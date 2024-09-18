from model.fetch_signals import fetch_japanese_equities_file
from model.train_model import create_raw_signals 
from datetime import datetime 
import pandas as pd 
import warnings 
warnings.filterwarnings("ignore")

def create_daily_signal():
    news_file = fetch_japanese_equities_file()
    print(news_file) 
    raw_signals = create_raw_signals(folder_path="model/tse_stocks", news_dirs=news_file) 
    print("Raw Signals: ")
    print(raw_signals) 

    today = pd.to_datetime(datetime.today().date()) - pd.DateOffset(months=2)
    print("Testing Date (One month ago): ", today)
    longs = raw_signals.loc[(raw_signals['Date'] == today) & (raw_signals['quintiles'] == 1), "Ticker"]
    shorts = raw_signals.loc[(raw_signals['Date'] == today) & (raw_signals['quintiles'] == 5), "Ticker"]

    longs.to_csv(f"signals/longs.csv", index=False)
    shorts.to_csv(f"signals/shorts.csv", index=False)
    print(f"Saved long signals to longs.csv")
    print(f"Saved short signals to shorts.csv")

if __name__ == "__main__":
    create_daily_signal() 