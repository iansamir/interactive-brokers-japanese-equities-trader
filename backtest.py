import pandas as pd
import yfinance as yf
import backtest_config
from plot import calculate_statistics, plot_cumulative_returns

def generate_returns(signals_file="japan_signals.csv"):
    result = pd.read_csv(signals_file)
    result = result[['Date', 'Ticker', 'Return', 'net_sentiment', 'rank', 'quintiles']]

    result['Date'] = pd.to_datetime(result['Date'])
    result.set_index('Date', inplace=True)
    result.sort_index(inplace=True)
    result['net_sentiment'] = result['net_sentiment'].shift(1)

    print('Raw Results')
    print(result.head())

    # Start and End Dates
    start_date = pd.to_datetime(backtest_config.start_date)
    end_date = pd.to_datetime(backtest_config.end_date)
    result = result[(result.index >= start_date) & (result.index <= end_date)]

    print('Date Filtered Results')
    print(result.head())

    # Get Q1 for longs and Q5 for shorts
    longs = result[result['quintiles'] == 1]
    shorts = result[result['quintiles'] == 5]
    
    longs.to_csv('unfiltered_longs.csv')
    shorts.to_csv('unfiltered_shorts.csv')
    
    # Correct ranking by 'Date'
    longs['sentiment_rank'] = longs.groupby(longs.index)['net_sentiment'].rank(method='first', ascending=False)
    shorts['sentiment_rank'] = shorts.groupby(shorts.index)['net_sentiment'].rank(method='first', ascending=True)

    print('Longs and Shorts')
    print(longs.head())
    print(shorts.head())

    longs.to_csv('ranked_longs.csv')
    shorts.to_csv('ranked_shorts.csv')

    # Filter by top N signals and sentiment thresholds
    N = backtest_config.top_n_signals  # Number of top signals to use for long/short

    filtered_longs = longs[
        (longs['sentiment_rank'] <= N) & 
        (longs['net_sentiment'] >= backtest_config.long_sentiment_threshold)
    ]

    filtered_shorts = shorts[
        (shorts['sentiment_rank'] <= N) & 
        (shorts['net_sentiment'] <= backtest_config.short_sentiment_threshold)
    ]

    filtered_longs_returns = filtered_longs.groupby(filtered_longs.index)['Return'].mean()
    filtered_shorts_returns = filtered_shorts.groupby(filtered_shorts.index)['Return'].mean()

    strategy_returns = pd.DataFrame(index=result.index.unique())
    strategy_returns = strategy_returns.join(filtered_longs_returns.rename('filtered_return_q1'), how='left')
    strategy_returns = strategy_returns.join(filtered_shorts_returns.rename('filtered_return_q5'), how='left')

    strategy_returns['Daily Return'] = (
        strategy_returns['filtered_return_q1'] * backtest_config.long_leverage - 
        strategy_returns['filtered_return_q5'] * backtest_config.short_leverage
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

if __name__ == "__main__":
    returns_df = generate_returns()
    returns_df.to_csv("returns_df_inspect.csv")
    # Remove reverse stock split error day 
    if pd.Timestamp("2024-07-29") in returns_df["Date"].values:
        print("Reverse stock split found!")
        returns_df.loc[returns_df["Date"] == pd.Timestamp("2024-07-29"), "Daily Return"] = 0
        returns_df["Cumulative Return"] = (1 + returns_df['Daily Return']).cumprod()
    benchmark_df = get_benchmark(start_date=returns_df.index.min(), end_date=returns_df.index.max()) 
    
    # Calculate statistics
    strategy_stats = calculate_statistics(returns_df['Cumulative Return'], returns_df['Daily Return'])
    benchmark_stats = calculate_statistics(benchmark_df['Cumulative Return'], benchmark_df['Daily Return'])

    # Plot cumulative returns with statistics and additional details
    plot_cumulative_returns(
        returns_df['Cumulative Return'], 
        benchmark_df['Cumulative Return'], 
        strategy_stats, 
        benchmark_stats
    )
