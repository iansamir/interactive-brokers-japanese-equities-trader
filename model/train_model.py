import pandas as pd
import numpy as np
import os
import pytz
import pandas_datareader.data as web
import logging
import yfinance as yf 
from pathlib import Path
from tqdm.auto import tqdm
from datetime import datetime, timedelta
from sklearn.linear_model import ElasticNet

# Function to concatenate CSV files in folder
def concatenate_csv_files_in_folder(folder_path):
    print(f"Starting to concatenate files from: {folder_path}")
    df_list = []
    for file_path in Path(folder_path).rglob('*.txt'):
        try:
            df = pd.read_csv(file_path)
            df = transform(df, symbol=file_path.stem.split('.')[0])
            df_list.append(df)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    concatenated_df = pd.concat(df_list, ignore_index=True)
    print("Finished concatenating files.")
    return concatenated_df

# Transform each dataframe
def transform(df, symbol):
    result = pd.DataFrame(index=df.index)
    result['Date'] = pd.to_datetime(df['<DATE>'], format='%Y%m%d')
    result['Ticker'] = symbol
    result['Close'] = df['<CLOSE>']
    result['Volume'] = df['<VOL>']
    result['Return'] = result['Close'].pct_change().shift(-1)
    turnover = result['Volume'] * result['Close']
    result['Turnover_p3m_JPY'] = turnover.rolling(window=63, min_periods=1).mean()
    return result.dropna()

# Standardize returns
def standardize(returns_series):
    if len(returns_series) == 1:
        return returns_series
    else:
        return (returns_series - returns_series.mean()) / returns_series.std()

# Compute log returns and standardize
def compute_log_and_standardize(prices):
    prices['Return_adj'] = np.log(prices['Return'] + 1)
    groups_of_returns_by_date = prices.groupby(['Date'], group_keys=False)['Return_adj']
    prices['Return_adj'] = groups_of_returns_by_date.apply(standardize)
    return prices

# Fetch USD/JPY exchange rate using yfinance
def fetch_usdjpy(start_date, end_date):
    print(f"Fetching USD/JPY exchange rate from {start_date} to {end_date}...")
    fx_data = yf.download('JPY=X', start=start_date, end=end_date)
    fx = fx_data[['Close']].reset_index().rename(columns={'Close': 'USDJPY'})
    return fx

# Merge exchange rate and convert turnover
def convert_and_merge(prices, fx):
    prices = prices.merge(fx, on='Date', how='left')
    prices['Turnover_p3m_USD'] = prices['Turnover_p3m_JPY'] / prices['USDJPY']
    return prices[['Date', 'Ticker', 'Turnover_p3m_USD', 'Return', 'Return_adj']]

# Process news data
def process_news_data(news_dirs):
    print(f"Loading news data from {news_dirs}...")
    news = pd.read_csv(news_dirs, sep='\t', encoding="ISO-8859-1", low_memory=False, usecols=[
        'Time_Stamp_Original(JST)', 'News_Source', 'News_ID_ND_Original', 'Company_Relevance',
        'Company_IDs(TSE)', 'Categories', 'Evaluation_Events', 'Keyword_Headline', 
        'QuantitativeScore_Market', 'QualitativeScore_Rule', 'SentimentScore_Expert', 'QualitativeScore_Rule_New'
    ])
    news = fill_na_and_compute_scores(news)
    return news

# Fill NaNs and compute scores
def fill_na_and_compute_scores(news):
    cols_to_fill_na = ['Categories', 'Evaluation_Events', 'Keyword_Headline']
    news[cols_to_fill_na] = news[cols_to_fill_na].fillna('Alex')
    news['Ticker'] = news['Company_IDs(TSE)'].astype(str)
    score_cols = ['QuantitativeScore_Market', 'QualitativeScore_Rule', 'SentimentScore_Expert', 'QualitativeScore_Rule_New']
    news['score'] = news[score_cols].mean(axis=1) / 50 - 1
    news['average_score'] = news['score'] * news['Company_Relevance']
    news = news[news['Company_Relevance'] >= 100]
    return news

# Process timestamp to date
def process_timestamps(news):
    timestamp = pd.to_datetime(news['Time_Stamp_Original(JST)'])
    news['Date'] = timestamp.apply(lambda d: d.date() if d.time() <= pd.Timestamp('15:00:00').time() else d.date() + timedelta(days=1))
    news['Date'] = pd.to_datetime(news['Date'])
    return news

# Create sentiment features
def create_sentiment_features(news, score_cols):
    df_grouped_list = []

    for score_col in score_cols:
        temp_news = news[~news[score_col].isna()].copy()

        # Define sentiment score as:
        # => 1 if the score is above 60
        # => 0 if the score is between 40 and 60
        # => -1 if the score is below 40
        temp_news['sentiment'] = temp_news[score_col].apply(lambda x: 1 if x >= 60 else (0 if x > 40 else -1))
        temp_news['sentiment_positive'] = (temp_news['sentiment'] > 0).astype(int)
        temp_news['sentiment_negative'] = (temp_news['sentiment'] < 0).astype(int)

        # Group by Date and Ticker and aggregate sentiment
        df_grouped = temp_news.groupby(['Date', 'Ticker']).agg({
            'sentiment_positive': 'sum',
            'sentiment_negative': 'sum'
        }).reset_index()

        # Create a column for the specific sentiment score LS feature
        feature_col = f'{score_col}_LS'
        df_grouped[feature_col] = np.log10((df_grouped['sentiment_positive'] + 1) / (df_grouped['sentiment_negative'] + 1))

        # Append the new grouped DataFrame to the list
        df_grouped_list.append(df_grouped[['Date', 'Ticker', feature_col]])

    # Merge all the grouped DataFrames on 'Date' and 'Ticker'
    df_merged = df_grouped_list[0]
    for df in df_grouped_list[1:]:
        df_merged = df_merged.merge(df, on=['Date', 'Ticker'], how='outer')

    return df_merged

# Train-test split generator
def train_test_split(data, look_back_years, start_date=None):
    print(f"Generating train-test splits starting from {start_date}, with a lookback of {look_back_years} years.")
    end_date = data['Date'].max()
    start_date = data['Date'].min() if start_date is None else pd.Timestamp(start_date)
    date_tuples = []
    current_start_date = start_date
    while True:
        start_training = current_start_date
        start_testing = (start_training + pd.DateOffset(years=look_back_years)).replace(month=1, day=1)
        end_testing = start_testing + pd.DateOffset(years=1)

        if end_testing > end_date:
            end_testing = end_date
        print(f"Train period: {start_training} to {start_testing}, Test period: {start_testing} to {end_testing}")
        train_data = data[(data['Date'] >= start_training) & (data['Date'] < start_testing)]
        test_data = data[(data['Date'] >= start_testing) & (data['Date'] <= end_testing)]  # Use <= for end date inclusion
        print(f"Test data range: {test_data['Date'].min()} to {test_data['Date'].max()}")

        yield train_data, test_data
        current_start_date = (start_training + pd.DateOffset(years=1)).replace(month=1, day=1)
        if current_start_date + pd.DateOffset(years=look_back_years) > end_date:
            break

# Model training and backtesting
def train_model(df_regression, lookback_years, start_date, alpha, l1_ratio, target_col, topic_ls, num_quantiles):
    betas = pd.DataFrame(columns=['intercept'] + topic_ls)
    used_features = pd.Series()
    result = []
    
    for train_data, test_data in train_test_split(df_regression, lookback_years, start_date=start_date):
        x_train = train_data[topic_ls].values
        y_train = train_data[target_col].values
        x_test = test_data[topic_ls].values
        model = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=0, max_iter=10000, tol=1e-5)
        model.fit(x_train, y_train)
        
        year = test_data['Date'].iloc[0].year
        betas.loc[year] = np.insert(model.coef_, 0, model.intercept_, axis=0)
        predictions = model.predict(x_test)
        used_features[year] = len([beta for beta in model.coef_ if beta != 0])
        
        batch = test_data[['Date', 'Ticker', 'Turnover_p3m_USD', 'Return']].copy()
        batch['net_sentiment'] = predictions
        batch['rank'] = batch.groupby('Date')['net_sentiment'].rank(pct=True)
        batch['quintiles'] = pd.cut(batch['rank'], num_quantiles, labels=np.arange(1, num_quantiles + 1)[::-1])
        result.append(batch)
    
    return pd.concat(result).reset_index(drop=True), betas

# Main function to run the entire model
def create_raw_signals(folder_path, news_dirs, lookback_years=3, start_date='2011-01-01', alpha=1e-05, l1_ratio=0.5, target_col='Return', num_quantiles=5):
    prices = concatenate_csv_files_in_folder(folder_path)
    prices = compute_log_and_standardize(prices[prices['Date'] >= '2010-01-01'].sort_values(['Date', 'Ticker']).reset_index(drop=True))
    
    fx = fetch_usdjpy(prices['Date'].min(), prices['Date'].max())
    prices = convert_and_merge(prices, fx)
    print("Prices: ")
    print(prices) 
    
    news = process_news_data(news_dirs)
    news = process_timestamps(news)
    print("Raw News: ")
    print(news)
    
    score_cols = ['QuantitativeScore_Market', 'QualitativeScore_Rule', 'SentimentScore_Expert', 'QualitativeScore_Rule_New']
    df_grouped = create_sentiment_features(news, score_cols)
    df_regression = prices.merge(df_grouped, on=['Date', 'Ticker'], how='inner')
    df_regression = df_regression.fillna(0) 
    print(f"Min Date in df_regression: {df_regression['Date'].min()}")
    print(f"Max Date in df_regression: {df_regression['Date'].max()}")
    
    result, betas = train_model(df_regression, lookback_years, start_date, alpha, l1_ratio, target_col, [f'{col}_LS' for col in score_cols], num_quantiles)
    result.to_csv('result.csv')
    print("Result saved to result.csv")
    return result 

if __name__ == "__main__":
    create_raw_signals('tse_stocks', 'alexandria.FTRI.japanese_equities.merged.csv')