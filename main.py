from ib_insync import *
import pandas as pd
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Initialize IB connection
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Adjust port and clientId as needed

def read_csv(file_path):
    """
    Read CSV file and return a list of tuples (ticker, quantity).
    """
    df = pd.read_csv(file_path)
    return [(str(row['ticker']), int(row['quantity'])) for _, row in df.iterrows()]

def close_japanese_equity_positions():
    """
    Fetch and close all Japanese equity positions from the previous day.
    """
    positions = ib.positions()
    
    if not positions:
        print(Fore.YELLOW + "No positions found.")
    
    for position in positions:
        contract = position.contract
        print(f"{Fore.BLUE}Checking position: {contract.symbol} (Type: {contract.secType}, Exchange: {contract.exchange}), Size: {position.position}")
        
        # Check if the position is a Japanese stock (equity) on the Tokyo Stock Exchange
        if contract.secType == 'STK' and contract.exchange == 'TSEJ':
            action = 'SELL' if position.position > 0 else 'BUY'
            order = MarketOrder(action, abs(position.position))
            trade = ib.placeOrder(contract, order)
            trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Closed position for {fill.contract.symbol} of {fill.shares} shares.")
            print(f"{Fore.GREEN}Closing {action} order placed for {contract.symbol}, {abs(position.position)} shares.")
            ib.sleep(1)  # Sleep to avoid rate limit
        else:
            print(f"{Fore.YELLOW}Skipping non-Japanese equity position: {contract.symbol} on {contract.exchange}")

def place_market_orders(equities_list, action):
    """
    Place market orders for a list of equities.
    """
    for symbol, quantity in equities_list:
        # Specify exchange 'TSEJ' for Tokyo Stock Exchange Japan
        contract = Stock(symbol, 'TSEJ', 'JPY')  # Correct exchange for Japanese stocks
        
        # Try to qualify the contract
        try:
            ib.qualifyContracts(contract)
            print(f"{Fore.CYAN}Contract qualified for {symbol} on exchange TSEJ.")
        except Exception as e:
            print(f"{Fore.RED}Failed to qualify contract for {symbol}. Error: {e}")
            continue

        # Adjust quantity to meet minimum order size and round lot requirements
        min_order_size = 100
        if quantity < min_order_size:
            print(f"{Fore.YELLOW}Order size for {symbol} is less than the minimum required size of {min_order_size}. Skipping order.")
            continue

        # Ensure the order quantity is a multiple of 100
        if quantity % 100 != 0:
            print(f"{Fore.YELLOW}Order size for {symbol} is not a multiple of 100. Adjusting to nearest multiple.")
            quantity = (quantity // 100) * 100

        # Try to place the order
        try:
            order = MarketOrder(action, quantity)
            trade = ib.placeOrder(contract, order)
            trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Executed {action} order for {fill.contract.symbol}, {fill.shares} shares.")
            print(f"{Fore.GREEN}{action} order placed for {symbol}, {quantity} shares.")
            ib.sleep(1)  # Sleep to avoid rate limit
        except Exception as e:
            print(f"{Fore.RED}Failed to place order for {symbol}. Error: {e}")

if __name__ == "__main__":
    try:
        # Check if IB connection is established
        if not ib.isConnected():
            print(Fore.RED + "Failed to connect to Interactive Brokers. Please check your connection settings.")
            exit()

        # Close previous day Japanese equity positions only
        close_japanese_equity_positions()

        # Read CSV files for long and short trades
        longs = read_csv('signals/longs.csv')
        shorts = read_csv('signals/shorts.csv')

        # Ensure new positions are placed regardless of closing positions
        if longs:
            print(Fore.CYAN + "Placing long market orders...")
            place_market_orders(longs, 'BUY')

        if shorts:
            print(Fore.CYAN + "Placing short market orders...")
            place_market_orders(shorts, 'SELL')

    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}")
    
    finally:
        # Disconnect from IB
        ib.disconnect()