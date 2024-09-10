import pandas as pd
import yfinance as yf
import backtest_config
from plot import plot_cumulative_returns

def generate_returns(signals_file="japan_signals.csv"):
    result = pd.read_csv(signals_file)
    result = result[['Date', 'Ticker', 'Return', 'net_sentiment', 'rank', 'quintiles']]

    result['Date'] = pd.to_datetime(result['Date'])
    result.set_index('Date', inplace=True)
    result.sort_index(inplace=True)
    result['net_sentiment'] = result['net_sentiment'].shift(1)

    print('Raw Results')
    print(result.head())

    # Define start and end dates from strategy configuration
    start_date = pd.to_datetime(backtest_config.start_date)
    end_date = pd.to_datetime(backtest_config.end_date)

    # Filter results to the specified date range
    result = result[(result.index >= start_date) & (result.index <= end_date)]

    print('Date Filtered Results')
    print(result.head())

    # Get Q1 for longs and Q5 for shorts
    longs = result[result['quintiles'] == 1]
    shorts = result[result['quintiles'] == 5]

    print(longs)
    print(shorts)
    
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

    strategy_returns["Date"] = strategy_returns.index 

    return strategy_returns 


def get_benchmark(start_date, end_date):
    benchmark_data = yf.download("^N225", start=start_date, end=end_date)
    # Compute daily returns from the benchmark's 'Adj Close' prices
    benchmark_data['Daily Return'] = benchmark_data['Adj Close'].pct_change()
    benchmark_data = benchmark_data.reset_index()[['Date', 'Daily Return']] 
    return benchmark_data

if __name__ == "__main__":
    returns_df = generate_returns()
    if pd.Timestamp("2024-07-29") in returns_df.index:
        returns_df.loc["2024-07-29", "Daily Return"] = 0    
    
    benchmark_df = get_benchmark(start_date=returns_df.index.min(), end_date=returns_df.index.max()) 
    plot_cumulative_returns(returns_df, benchmark_df)