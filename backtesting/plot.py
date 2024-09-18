import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt

def calculate_statistics(cumulative_returns, daily_returns):
    # Calculate annualized return
    annualized_return = (cumulative_returns.iloc[-1] ** (252 / len(daily_returns)) - 1)

    # Calculate Sharpe Ratio
    risk_free_rate = 0.0
    excess_daily_returns = daily_returns - risk_free_rate / 252
    sharpe_ratio = np.sqrt(252) * excess_daily_returns.mean() / excess_daily_returns.std()

    # Calculate Max Drawdown
    cumulative_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()

    # Calculate Calmar Ratio
    calmar_ratio = annualized_return / abs(max_drawdown)

    return {
        "Annualized Return": annualized_return,
        "Sharpe Ratio": sharpe_ratio,
        "Max Drawdown": max_drawdown,
        "Calmar Ratio": calmar_ratio
    }


# Function to plot cumulative returns with statistics and additional details
def plot_cumulative_returns(cumulative_returns, benchmark_cumulative_returns, strategy_stats, benchmark_stats):
    plt.figure(figsize=(10, 6))
    
    strategy_label = (
        f"Strategy Annualized Return: {strategy_stats['Annualized Return']:.2%}\n"
        f"Sharpe Ratio: {strategy_stats['Sharpe Ratio']:.2f}, "
        f"Calmar Ratio: {strategy_stats['Calmar Ratio']:.2f}, "
        f"Max Drawdown: {strategy_stats['Max Drawdown']:.2%}"
    )
    
    benchmark_label = (
        f"Benchmark Annualized Return: {benchmark_stats['Annualized Return']:.2%}\n"
        f"Sharpe Ratio: {benchmark_stats['Sharpe Ratio']:.2f}, "
        f"Calmar Ratio: {benchmark_stats['Calmar Ratio']:.2f}, "
        f"Max Drawdown: {benchmark_stats['Max Drawdown']:.2%}"
    )
    
    plt.plot(cumulative_returns.index, cumulative_returns, label=strategy_label, color='blue')
    plt.plot(benchmark_cumulative_returns.index, benchmark_cumulative_returns, label=benchmark_label, color='orange')
    
    plt.title('Sentiment Strategy vs SPX')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Return (Log-scale)')
    
    # Use log scale for y-axis
    plt.yscale('log')
    
    # Customize y-ticks to show percentage gains
    yticks = [1, 1.1, 1.5, 2, 3, 5, 10]  # Example y-ticks for percentage gains
    plt.yticks(yticks, [f'{(y - 1) * 100:.0f}%' for y in yticks])
    
    # Add horizontal lines with percentage labels on the right
    for y in yticks:
        plt.axhline(y=y, color='gray', linestyle='--', linewidth=0.5)
    
    # Display final return percentages
    final_strategy_return = (cumulative_returns.iloc[-1] - 1) * 100
    final_benchmark_return = (benchmark_cumulative_returns.iloc[-1] - 1) * 100
    
    # Annotate final returns on the right end of the plot
    plt.text(cumulative_returns.index[-1], cumulative_returns.iloc[-1], 
             f'{final_strategy_return:.2f}%', va='center', ha='left', color='blue', fontweight='bold')
    plt.text(benchmark_cumulative_returns.index[-1], benchmark_cumulative_returns.iloc[-1], 
             f'{final_benchmark_return:.2f}%', va='center', ha='left', color='orange', fontweight='bold')
    
    # Add legend and grid
    plt.legend(loc='upper left', fontsize='small')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.show()
