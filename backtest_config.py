# params for japan equities backtesting 
# need signals file saved as japan_signals.csv from https://drive.google.com/file/d/1r26Kxg9fQoWyx6Rb9nCY1EhWjC75BRSH/view?usp=drive_link

start_date = "2020-01-01"
end_date = "2024-09-01"

top_n_signals = 100 # n longs and n shorts each day

long_sentiment_threshold = 0.0029
short_sentiment_threshold = 100

long_leverage = 1.75
short_leverage = 1.0 

return_threshold_window = 20 # trading days 
long_return_threshold = -100
short_return_threshold = 100
