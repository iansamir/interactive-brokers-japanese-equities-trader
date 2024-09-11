# params for japan equities backtesting 
# need signals file saved as japan_signals.csv from https://drive.google.com/file/d/1r26Kxg9fQoWyx6Rb9nCY1EhWjC75BRSH/view?usp=drive_link
# need all returns file saved as all-japan-ticker-returns-2010-01-01.csv from https://drive.google.com/file/d/1tXFGWVzIElex-CrZW3VjEJf7ThL3_C_5/view?usp=sharing

start_date = "2018-01-01"
end_date = "2024-08-01"

top_n_signals = 1000 # n longs and n shorts each day

long_sentiment_threshold = -100
short_sentiment_threshold = 100

long_leverage = 1.0
short_leverage = 1.0 
max_alloc = 0.05 # most allocation in a single asset per day 

return_threshold_window = 20 # trading days 
long_return_threshold = 0.00
short_return_threshold = 100
