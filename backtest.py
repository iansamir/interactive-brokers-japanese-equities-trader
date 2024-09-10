import pandas as pd
import yfinance as yf
import backtest_config
from plot import calculate_statistics, plot_cumulative_returns

def config_to_dict():
    config_params = {
        "start_date": backtest_config.start_date,
        "end_date": backtest_config.end_date,
        "top_n_signals": backtest_config.top_n_signals,
        "long_sentiment_threshold": backtest_config.long_sentiment_threshold,
        "short_sentiment_threshold": backtest_config.short_sentiment_threshold,
        "long_leverage": backtest_config.long_leverage,
        "short_leverage": backtest_config.short_leverage,
        "return_threshold_window": backtest_config.return_threshold_window, 
        "long_return_threshold": backtest_config.long_return_threshold, 
        "short_return_threshold": backtest_config.short_return_threshold,
    }
    return config_params 

def generate_returns(signals_file="japan_signals.csv", returns_file="all-japan-ticker-returns-2010-01-01.csv", start_date=None, end_date=None, top_n_signals=50,
                     long_sentiment_threshold=-100, short_sentiment_threshold=100, 
                     return_threshold_window=20, long_return_threshold=-100, short_return_threshold=-100, 
                     long_leverage=1, short_leverage=1):
    
    
    print(long_return_threshold)
    print(short_return_threshold)
    result = pd.read_csv(signals_file)
    result = result[['Date', 'Ticker', 'Return', 'net_sentiment', 'rank', 'quintiles']]

    result['Date'] = pd.to_datetime(result['Date'])
    result.set_index('Date', inplace=True)
    result.sort_index(inplace=True)
    result['net_sentiment'] = result['net_sentiment'].shift(1)

    # Start and End Dates
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    result = result[(result.index >= start_date) & (result.index <= end_date)]

    # Get Q1 for longs and Q5 for shorts
    longs = result[result['quintiles'] == 1]
    shorts = result[result['quintiles'] == 5]

    # Correct ranking by 'Date'
    longs['sentiment_rank'] = longs.groupby(longs.index)['net_sentiment'].rank(method='first', ascending=False)
    shorts['sentiment_rank'] = shorts.groupby(shorts.index)['net_sentiment'].rank(method='first', ascending=True)

    # Filter by top N signals and sentiment thresholds
    filtered_longs = longs[
        (longs['sentiment_rank'] <= top_n_signals) & 
        (longs['net_sentiment'] >= long_sentiment_threshold)
    ]

    filtered_shorts = shorts[
        (shorts['sentiment_rank'] <= top_n_signals) & 
        (shorts['net_sentiment'] <= short_sentiment_threshold)
    ]

    print('Filtered longs by sentiment:', len(filtered_longs))
    print('Filtered shorts by sentiment:', len(filtered_shorts))

    # Load the combined returns data
    combined_returns = pd.read_csv(returns_file, index_col='Date', parse_dates=True)

    # Calculate the rolling X-day returns up to the day before the current day
    rolling_returns = combined_returns.shift(1).rolling(window=return_threshold_window).sum()

    # Print the first few rows of rolling returns to inspect
    print("Rolling returns (first few rows):")
    print(rolling_returns.head())

    filtered_longs['Ticker'] = filtered_longs['Ticker'].astype(str)
    filtered_shorts['Ticker'] = filtered_shorts['Ticker'].astype(str)
    combined_returns.columns = combined_returns.columns.astype(str)  # Ensure ticker columns in combined_returns are strings

    # Adjust filter function to use previous day's rolling return value
    def filter_by_rolling_return(row, direction='long'):
        try:
            # Use rolling return from the previous trading day
            ticker = row['Ticker']
            rolling_return = rolling_returns.at[row.name, ticker]
            
            if direction == 'long':
                return (rolling_return >= long_return_threshold) or pd.isna(rolling_return)
            else:  # direction == 'short'
                return (rolling_return <= short_return_threshold) or pd.isna(rolling_return)
        except KeyError:
            # If rolling return data is missing for the date or ticker, include it by default
            print(f"Missing rolling return for Date: {row.name}, Ticker: {ticker}")
            return True

    # Filter the long and short positions based on rolling returns
    filtered_longs_with_returns = filtered_longs[filtered_longs.apply(filter_by_rolling_return, axis=1, direction='long')]
    filtered_shorts_with_returns = filtered_shorts[filtered_shorts.apply(filter_by_rolling_return, axis=1, direction='short')]

    # Print the number of rows after filtering
    print('Filtered longs by returns:', len(filtered_longs_with_returns))
    print('Filtered shorts by returns:', len(filtered_shorts_with_returns))

    filtered_longs_returns = filtered_longs_with_returns.groupby(filtered_longs_with_returns.index)['Return'].mean()
    filtered_shorts_returns = filtered_shorts_with_returns.groupby(filtered_shorts_with_returns.index)['Return'].mean()

    strategy_returns = pd.DataFrame(index=result.index.unique())
    strategy_returns = strategy_returns.join(filtered_longs_returns.rename('filtered_return_q1'), how='left')
    strategy_returns = strategy_returns.join(filtered_shorts_returns.rename('filtered_return_q5'), how='left')

    # Calculate daily returns
    strategy_returns['Daily Return'] = (
        strategy_returns['filtered_return_q1'] * long_leverage - 
        strategy_returns['filtered_return_q5'] * short_leverage
    )

    # Fill NaN values with 0 for daily returns
    strategy_returns['Daily Return'].fillna(0, inplace=True)
    strategy_returns.sort_index(inplace=True)
    strategy_returns['Cumulative Return'] = (1 + strategy_returns['Daily Return']).cumprod()

    strategy_returns["Date"] = strategy_returns.index 

    return strategy_returns 

def get_benchmark(start_date, end_date):
    benchmark_data = yf.download("^N225", start=start_date, end=end_date)
    # Compute daily returns from the benchmark's 'Adj Close' prices
    benchmark_data['Daily Return'] = benchmark_data['Adj Close'].pct_change()
    benchmark_data['Cumulative Return'] = (1 + benchmark_data['Daily Return']).cumprod()
    return benchmark_data


def run_backtest(start_date, end_date, top_n_signals, long_sentiment_threshold, short_sentiment_threshold, long_leverage, short_leverage, return_threshold_window, long_return_threshold, short_return_threshold, 
signals_file="japan_signals.csv", plotting=True):
    returns_df = generate_returns(
        signals_file=signals_file, 
        start_date=start_date, 
        end_date=end_date, 
        top_n_signals=top_n_signals,
        long_sentiment_threshold=long_sentiment_threshold, 
        short_sentiment_threshold=short_sentiment_threshold, 
        long_leverage=long_leverage, 
        short_leverage=short_leverage, 
        return_threshold_window=return_threshold_window, 
        long_return_threshold=long_return_threshold, 
        short_return_threshold=short_return_threshold
    )
    
    returns_df.to_csv("returns_df_inspect.csv")

    # Remove reverse stock split error day 
    if pd.Timestamp("2024-07-29") in returns_df["Date"].values:
        returns_df.loc[returns_df["Date"] == pd.Timestamp("2024-07-29"), "Daily Return"] = 0
        returns_df["Cumulative Return"] = (1 + returns_df['Daily Return']).cumprod()

    benchmark_df = get_benchmark(start_date=returns_df.index.min(), end_date=returns_df.index.max()) 
    
    # Calculate statistics
    strategy_stats = calculate_statistics(returns_df['Cumulative Return'], returns_df['Daily Return'])
    benchmark_stats = calculate_statistics(benchmark_df['Cumulative Return'], benchmark_df['Daily Return'])

    if plotting: 
        plot_cumulative_returns(
            returns_df['Cumulative Return'], 
            benchmark_df['Cumulative Return'], 
            strategy_stats, 
            benchmark_stats
        )

    return returns_df, strategy_stats 

if __name__ == "__main__":
    params = config_to_dict()
    run_backtest(**params)