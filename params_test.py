from backtest import config_to_dict, run_backtest
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import warnings 

def run_param_test(param1, param2, range1, range2, optimization_metric="Calmar Ratio"):
    warnings.filterwarnings("ignore")
    results = []
    params = config_to_dict()

    for val1 in range1:
        for val2 in range2:
            val1 = round(val1, 1)
            val2 = round(val2, 3)
            
            print(f"testing {param1}: {val1} and {param2}: {val2}...")
            params[param1] = val1
            params[param2] = val2
            params["plotting"] = False
            
            returns, stats = run_backtest(**params)
            results.append({param1: val1, param2: val2, optimization_metric: stats[optimization_metric]})

    results_df = pd.DataFrame(results)
    results_pivot = results_df.pivot(index=param1, columns=param2, values=optimization_metric)
    print(results_pivot)
    plot_heatmap(results_pivot, param1, param2, optimization_metric)

def plot_heatmap(results_df, param1, param2, optimization_metric="Calmar Ratio"):
    plt.figure(figsize=(10, 6))
    sns.heatmap(results_df, annot=True, fmt=".4f", cmap="YlGnBu", cbar_kws={'label': optimization_metric})
    plt.title(f'{optimization_metric} Heatmap: {param1} vs {param2}')
    plt.xlabel(param2)
    plt.ylabel(param1)
    plt.show()

if __name__ == "__main__":
    param1_range = np.linspace(1, 50, 10) 
    param2_range = np.linspace(0.001, 0.01, 5) 
    param1 = "top_n_signals" # top_n_signals, long_sentiment_threshold, short_sentiment_threshold, long_leverage, short_leverage
    param2 = "long_sentiment_threshold"
    run_param_test(param1, param2, param1_range, param2_range)