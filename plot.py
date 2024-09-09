import matplotlib.pyplot as plt

def plot_cumulative_returns(returns_df, benchmark_df):
    # Calculate cumulative returns for both strategy and benchmark
    returns_df["Cumulative Returns"] = (1 + returns_df["Daily Return"]).cumprod()
    benchmark_df["Cumulative Returns"] = (1 + benchmark_df["Daily Return"]).cumprod()

    plt.figure(figsize=(10, 6))

    # Plot the cumulative returns using blue and orange
    plt.plot(returns_df['Date'], returns_df["Cumulative Returns"], label="Strategy", color='blue')
    plt.plot(benchmark_df['Date'], benchmark_df["Cumulative Returns"], label="Benchmark", color='orange')

    # Use log scale for y-axis
    plt.yscale('log')

    yticks = [1, 1.5, 2, 3, 6, 11, 21, 51, 101]  # Y-ticks for large percentage gains
    plt.yticks(yticks, [f'{(y - 1) * 100:.0f}%' for y in yticks])  # Convert y-ticks to percentages

    # Add horizontal lines with percentage labels on the right
    for y in yticks:
        plt.axhline(y=y, color='gray', linestyle='--', linewidth=0.5)

    # Calculate final return percentages
    final_strategy_return = (returns_df["Cumulative Returns"].iloc[-1] - 1) * 100
    final_benchmark_return = (benchmark_df["Cumulative Returns"].iloc[-1] - 1) * 100

    # Annotate final returns on the right end of the plot
    plt.text(returns_df['Date'].iloc[-1], returns_df["Cumulative Returns"].iloc[-1], 
             f'{final_strategy_return:.2f}%', va='center', ha='left', color='blue', fontweight='bold')
    plt.text(benchmark_df['Date'].iloc[-1], benchmark_df["Cumulative Returns"].iloc[-1], 
             f'{final_benchmark_return:.2f}%', va='center', ha='left', color='orange', fontweight='bold')

    # Set plot title and labels
    plt.title('Cumulative Returns: Strategy vs Benchmark')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Return (Log-scale)')

    # Add legend and grid
    plt.legend(loc='upper left', fontsize='small')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.show()
