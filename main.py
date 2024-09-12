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
    Read CSV file and return a list of tuples (ticker, limit_price, amount).
    """
    df = pd.read_csv(file_path)
    return [(str(row['ticker']), float(row['limit_price']), float(row['amount'])) for _, row in df.iterrows()]

def close_equity_positions(exchange_filter=None):
    """
    Fetch and close equity positions based on an optional exchange filter.
    If `exchange_filter` is provided, only positions from that exchange will be closed.
    """
    positions = ib.positions()
    
    if not positions:
        print(Fore.YELLOW + "No positions found.")
    
    for position in positions:
        contract = position.contract
        print(f"{Fore.BLUE}Checking position: {contract.symbol} (Type: {contract.secType}, Exchange: {contract.exchange}), Size: {position.position}")
        
        # If an exchange filter is provided, check if the position matches
        if exchange_filter:
            if contract.secType == 'STK' and contract.exchange == exchange_filter:
                action = 'SELL' if position.position > 0 else 'BUY'
                order = MarketOrder(action, abs(position.position))
                trade = ib.placeOrder(contract, order)
                trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Closed position for {fill.contract.symbol} of {fill.shares} shares.")
                print(f"{Fore.GREEN}Closing {action} order placed for {contract.symbol}, {abs(position.position)} shares.")
                ib.sleep(1)  # Sleep to avoid rate limit
            else:
                print(f"{Fore.YELLOW}Skipping position: {contract.symbol} on {contract.exchange} (does not match filter)")
        else:
            # If no filter is provided, close all equity positions
            if contract.secType == 'STK':
                action = 'SELL' if position.position > 0 else 'BUY'
                order = MarketOrder(action, abs(position.position))
                trade = ib.placeOrder(contract, order)
                trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Closed position for {fill.contract.symbol} of {fill.shares} shares.")
                print(f"{Fore.GREEN}Closing {action} order placed for {contract.symbol}, {abs(position.position)} shares.")
                ib.sleep(1)  # Sleep to avoid rate limit
            else:
                print(f"{Fore.YELLOW}Skipping non-equity position: {contract.symbol} on {contract.exchange}")

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

def confirm_and_place_orders(trades, action):
    """
    Print and confirm limit orders before placing them.
    :param trades: List of tuples (ticker, limit_price, amount)
    :param action: 'BUY' or 'SELL'
    """
    # Print the proposed trades
    print(f"Proposed {action} orders:")
    df = pd.DataFrame(trades, columns=['Ticker', 'Limit Price', 'Amount'])
    print(df)
    
    # Ask for confirmation
    confirm = input(f"Do you want to place these {action} orders? (yes/no): ").strip().lower()
    if confirm == 'yes':
        place_limit_orders(trades, action)
    else:
        print(f"{action.capitalize()} orders have been canceled.")

def place_limit_orders(trades, action):
    """
    Place limit orders for the given trades.
    :param trades: List of tuples (ticker, limit_price, amount)
    :param action: 'BUY' or 'SELL'
    """
    for ticker, limit_price, amount in trades:
        # Assuming we are placing a limit order based on the amount in USD
        # Calculate the quantity to buy/sell based on the amount and limit price
        quantity = int(amount / limit_price)

        # Create contract and order
        contract = Stock(ticker, 'SMART', 'USD')  # Modify contract as per your requirements
        order = LimitOrder(action, quantity, limit_price)

        # Place the order
        trade = ib.placeOrder(contract, order)
        print(f"Placing {action} limit order for {ticker}: {quantity} shares at {limit_price} limit price.")

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

def confirm_and_close_positions(exchange_filter=None):
    """
    Display positions and ask for confirmation before closing.
    """
    positions = ib.positions()
    
    if not positions:
        print(Fore.YELLOW + "No positions found.")
        return

    # Display positions as a DataFrame
    df = display_positions_as_dataframe(positions)

    if df is not None:
        confirm = input(Fore.CYAN + f"Do you want to proceed with closing the {exchange_filter if exchange_filter else ''} positions? (yes/no): ").lower()

        if confirm == 'yes':
            for position in positions:
                contract = position.contract
                if exchange_filter:
                    if contract.secType == 'STK' and contract.exchange == exchange_filter:
                        action = 'SELL' if position.position > 0 else 'BUY'
                        order = MarketOrder(action, abs(position.position))
                        trade = ib.placeOrder(contract, order)
                        trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Closed position for {fill.contract.symbol} of {fill.shares} shares.")
                        print(f"{Fore.GREEN}Closing {action} order placed for {contract.symbol}, {abs(position.position)} shares.")
                        ib.sleep(1)  # Sleep to avoid rate limit
                    else:
                        print(f"{Fore.YELLOW}Skipping position: {contract.symbol} on {contract.exchange} (does not match filter)")
                else:
                    if contract.secType == 'STK':
                        action = 'SELL' if position.position > 0 else 'BUY'
                        order = MarketOrder(action, abs(position.position))
                        trade = ib.placeOrder(contract, order)
                        trade.filledEvent += lambda trade, fill: print(f"{Fore.GREEN}Closed position for {fill.contract.symbol} of {fill.shares} shares.")
                        print(f"{Fore.GREEN}Closing {action} order placed for {contract.symbol}, {abs(position.position)} shares.")
                        ib.sleep(1)  # Sleep to avoid rate limit
        else:
            print(Fore.RED + "Aborting position closure.")
    else:
        print(Fore.RED + "No positions to close.")

if __name__ == "__main__":
    try:
        if not ib.isConnected():
            print(Fore.RED + "Failed to connect to Interactive Brokers. Please check your connection settings.")
            exit()

        confirm_and_close_positions(exchange_filter="TSEJ")

        longs = read_csv('signals/longs.csv')
        shorts = read_csv('signals/shorts.csv')

        if longs:
            print(Fore.CYAN + "Placing long limit orders...")
            confirm_and_place_orders(longs, 'BUY')

        if shorts:
            print(Fore.CYAN + "Placing short limit orders...")
            confirm_and_place_orders(shorts, 'SELL')

    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}")
    
    finally:
        ib.disconnect()