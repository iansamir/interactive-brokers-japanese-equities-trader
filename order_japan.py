from ib_insync import *
import pandas as pd
from colorama import Fore, init
import math

# Initialize colorama
init(autoreset=True)

# Initialize IB connection
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Adjust port and clientId as needed

def read_csv(file_path):
    """
    Read CSV file and return a list of tickers.
    """
    try:
        df = pd.read_csv(file_path)
        return df['Ticker'].tolist()  # Ensure CSV has only the 'Ticker' column
    except KeyError as e:
        print(Fore.RED + f"Error: {e} column is missing from the CSV file. Check the file format.")
        raise

def fetch_account_cash_value():
    """
    Fetch the total available cash balance from the IB account.
    """
    account_values = ib.accountSummary()
    cash_value = None
    for item in account_values:
        if item.tag == 'AvailableFunds' and item.currency == 'USD':  # Adjust to your currency if needed
            cash_value = float(item.value)
            break
    if cash_value is None:
        raise ValueError("Failed to fetch available cash value.")
    return cash_value

def close_japanese_positions():
    """
    Close all open positions on the Tokyo Stock Exchange (TSEJ).
    """
    positions = ib.positions()
    japanese_positions = [pos for pos in positions if pos.contract.exchange == 'TSEJ']

    if not japanese_positions:
        print(Fore.YELLOW + "No Japanese positions found.")
        return

    print(f"Closing all Japanese positions...")
    for position in japanese_positions:
        contract = position.contract
        action = 'SELL' if position.position > 0 else 'BUY'
        order = MarketOrder(action, abs(position.position))
        trade = ib.placeOrder(contract, order)
        trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Closed {fill.contract.symbol} of {fill.shares} shares.")
        print(f"{Fore.GREEN}Closing {action} order placed for {contract.symbol}, {abs(position.position)} shares.")
        ib.sleep(1)  # Sleep to avoid rate limit

def place_fixed_share_orders(tickers, action):
    """
    Place market orders for a fixed number of shares (100) for each ticker.
    """
    fixed_shares = 100  # Fixed quantity for each ticker

    for symbol in tickers:
        contract = Stock(symbol, 'TSEJ', 'JPY')  # Tokyo Stock Exchange Japan
        
        try:
            # Qualify the contract
            ib.qualifyContracts(contract)
            print(f"{Fore.CYAN}Contract qualified for {symbol} on exchange TSEJ.")
        except Exception as e:
            print(f"{Fore.RED}Failed to qualify contract for {symbol}. Error: {e}")
            continue

        try:
            # Place the market order
            order = MarketOrder(action, fixed_shares)
            trade = ib.placeOrder(contract, order)
            trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Executed {action} market order for {fill.contract.symbol}, {fill.shares} shares at {fill.price}.")
            print(f"{Fore.GREEN}{action} market order placed for {symbol}, {fixed_shares} shares.")
            ib.sleep(1)  # Sleep to avoid rate limit
        except Exception as e:
            print(Fore.RED + f"Failed to place order for {symbol}. Error: {e}")

def display_and_confirm_orders(tickers, action):
    """
    Display the proposed orders and ask for confirmation before placing them.
    """
    print(f"Proposed {action} orders:")
    df = pd.DataFrame(tickers, columns=['Ticker'])
    df['Shares'] = 100  # Fixed 100 shares for each order
    print(df)

    confirm = input(f"Do you want to place these {action} orders? (yes/no): ").strip().lower()
    if confirm == 'yes':
        place_fixed_share_orders(tickers, action)
    else:
        print(f"{action.capitalize()} orders have been canceled.")

def display_positions_as_dataframe(positions):
    """
    Convert the positions to a pandas DataFrame and display it.
    """
    if positions:
        positions_data = []
        for position in positions:
            contract = position.contract
            positions_data.append({
                "Symbol": contract.symbol,
                "SecType": contract.secType,
                "Exchange": contract.exchange,
                "Position": position.position,
                "Average Cost": position.avgCost
            })

        df = pd.DataFrame(positions_data)
        print(df)
        return df
    else:
        print(Fore.YELLOW + "No positions found.")
        return None

def display_and_confirm_positions():
    """
    Display all positions first, then ask for confirmation before closing Japanese positions.
    """
    positions = ib.positions()

    if not positions:
        print(Fore.YELLOW + "No positions found.")
        return

    # Display all positions as a DataFrame
    print(Fore.CYAN + "Displaying all current positions:")
    df_all_positions = display_positions_as_dataframe(positions)
    print(df_all_positions)

    # Ask user for confirmation to close Japanese positions
    confirm = input(Fore.CYAN + "Do you want to close all Japanese positions? (yes/no): ").lower()

    if confirm == 'yes':
        close_japanese_positions()
    else:
        print(Fore.RED + "Aborting position closure.")

if __name__ == "__main__":
    try:
        if not ib.isConnected():
            print(Fore.RED + "Failed to connect to Interactive Brokers. Please check your connection settings.")
            exit()

        # Display positions, confirm and close Japanese positions
        display_and_confirm_positions()

        # Step 1: Fetch the total available cash value in the account
        total_cash = fetch_account_cash_value()
        print(f"Total available cash: {total_cash} USD")

        # Step 2: Read CSV files for long and short tickers
        longs = read_csv('signals/longs.csv')
        shorts = read_csv('signals/shorts.csv')

        # Step 3: Confirm and place long orders
        if longs:
            print(f"Placing long orders for tickers: {longs}")
            display_and_confirm_orders(longs, 'BUY')

        # Step 4: Confirm and place short orders
        if shorts:
            print(f"Placing short orders for tickers: {shorts}")
            display_and_confirm_orders(shorts, 'SELL')

    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}")
    
    finally:
        ib.disconnect()