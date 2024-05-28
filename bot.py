import ccxt
import pandas as pd
import ta
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(filename='trading_bot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

api_key = 'api_key'
api_secret = 'api_secret'

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True  
    }
})

symbols = ['BTC/USDT', 'ETH/USDT']

def fetch_ohlcv(symbol, timeframe='1h', limit=100):
    ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_atr(df, period=14):
    df['atr'] = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=period).average_true_range()
    return df['atr'].iloc[-1]

def calculate_bollinger_bands(df, period=20, std_dev=2):
    indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=period, window_dev=std_dev)
    df['bb_middle'] = indicator_bb.bollinger_mavg()
    df['bb_upper'] = indicator_bb.bollinger_hband()
    df['bb_lower'] = indicator_bb.bollinger_lband()

def calculate_ema(df, period=14):
    df['ema'] = ta.trend.EMAIndicator(close=df['close'], window=period).ema_indicator()

def decide_strategy(df):
    if df['close'].iloc[-1] < df['bb_lower'].iloc[-1]:
        return 'mean_reversion'
    elif df['close'].iloc[-1] > df['ema'].iloc[-1]:
        return 'momentum'
    else:
        return 'none'

def fetch_market_data(symbols):
    market_data = {}
    for symbol in symbols:
        market_data[symbol] = binance.fetch_ticker(symbol)
    return market_data

def place_order(symbol, order_type, side, amount, price=None):
    try:
        if order_type == 'limit':
            order = binance.create_limit_order(symbol, side, amount, price)
        elif order_type == 'market':
            order = binance.create_market_order(symbol, side, amount)
        logging.info(f"Placed {side} order for {amount} {symbol} at {price}")
        return order
    except ccxt.InsufficientFunds as e:
        logging.error(f"Insufficient funds for placing order: {e}")
        return None
    except ccxt.InvalidOrder as e:
        logging.error(f"Invalid order parameters: {e}")
        return None
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        return None

def manage_orders(symbols):
    try:
        for symbol in symbols:
            open_orders = binance.fetch_open_orders(symbol)
            for order in open_orders:
                current_price = binance.fetch_ticker(symbol)['last']
                if order['side'] == 'buy' and order['price'] < current_price * 0.98:  
                    binance.cancel_order(order['id'], symbol)
                    logging.info(f"Cancelled order {order['id']} for {symbol} due to significant price deviation")
    except Exception as e:
        logging.error(f"Error managing orders: {e}")

def calculate_position_size(symbol, balance, risk_percentage=0.01):
    try:
        df = fetch_ohlcv(symbol)
        atr = calculate_atr(df)
        price = df['close'].iloc[-1]
        position_size = (balance * risk_percentage) / atr
        amount = position_size / price
        logging.info(f"Calculated position size for {symbol}: {amount} based on ATR and risk percentage")
        return amount
    except Exception as e:
        logging.error(f"Error calculating position size: {e}")
        return 0

def adjust_order_size(symbol, amount, price):
    try:
        markets = binance.load_markets()
        market = markets[symbol]
        
        quote_asset = symbol.split('/')[1]
        balance = get_balance(quote_asset)
        max_amount_based_on_balance = balance / price
        
        amount = min(amount, max_amount_based_on_balance, market['limits']['amount']['max'])
        amount = max(amount, market['limits']['amount']['min'])
        
        return amount
    except Exception as e:
        logging.error(f"Error adjusting order size: {e}")
        return 0

def smart_order_routing(symbol, side, amount, price):
    try:
        chunk_size = amount / 5  
        orders = []
        for i in range(5):
            if side == 'buy':
                price_chunk = price * (1 - i * 0.001)  
            else:
                price_chunk = price * (1 + i * 0.001)  
            adjusted_chunk_size = adjust_order_size(symbol, chunk_size, price_chunk)
            if adjusted_chunk_size > 0:
                placed_order = place_order(symbol, 'limit', side, adjusted_chunk_size, price_chunk)
                if placed_order:
                    orders.append(placed_order)
                    logging.info(f"Successfully placed {side} order chunk: {adjusted_chunk_size} {symbol} at {price_chunk}")
            time.sleep(1)  
        logging.info(f"Executed smart order routing for {side} order of {amount} {symbol} at {price}")
        return orders
    except Exception as e:
        logging.error(f"Error in smart order routing: {e}")
        return []

def get_balance(asset):
    try:
        balance = binance.fetch_balance()
        available_balance = balance['free'][asset]
        logging.info(f"Available balance for {asset}: {available_balance}")
        return available_balance
    except Exception as e:
        logging.error(f"Error fetching balance: {e}")
        return 0

def apply_risk_management(symbol, entry_orders, stop_loss_pct=0.01, take_profit_pct=0.02):
    try:
        for entry_order in entry_orders:
            if entry_order:
                entry_price = entry_order['price']
                amount = entry_order['amount']
                if entry_order['side'] == 'buy':
                    stop_loss_price = entry_price * (1 - stop_loss_pct)
                    take_profit_price = entry_price * (1 + take_profit_pct)
                    place_order(symbol, 'limit', 'sell', amount, take_profit_price)
                    place_order(symbol, 'stop_loss_limit', 'sell', amount, stop_loss_price)
                elif entry_order['side'] == 'sell':
                    stop_loss_price = entry_price * (1 + stop_loss_pct)
                    take_profit_price = entry_price * (1 - take_profit_pct)
                    place_order(symbol, 'limit', 'buy', amount, take_profit_price)
                    place_order(symbol, 'stop_loss_limit', 'buy', amount, stop_loss_price)
                logging.info(f"Applied risk management for {symbol}: Stop Loss at {stop_loss_price}, Take Profit at {take_profit_price}")
    except Exception as e:
        logging.error(f"Error applying risk management: {e}")

def trading_loop():
    while True:
        try:
            market_data = fetch_market_data(symbols)
            manage_orders(symbols)  
            for symbol in symbols:
                base_asset, quote_asset = symbol.split('/')
                df = fetch_ohlcv(symbol)
                calculate_bollinger_bands(df)
                calculate_ema(df)
                
                strategy = decide_strategy(df)
                logging.info(f"Selected strategy for {symbol}: {strategy}")
                
                base_price = market_data[symbol]['last']
                quote_balance = get_balance(quote_asset)
                
                if quote_balance > 1 and strategy != 'none':  
                    amount = calculate_position_size(symbol, quote_balance)
                    if amount > 0:
                        if strategy == 'mean_reversion':
                            buy_price = df['bb_lower'].iloc[-1]
                            sell_price = df['bb_upper'].iloc[-1]
                        elif strategy == 'momentum':
                            buy_price = base_price * 0.995
                            sell_price = base_price * 1.005
                        
                        entry_orders = smart_order_routing(symbol, 'buy', amount, buy_price)  
                        if entry_orders:
                            apply_risk_management(symbol, entry_orders)
                        smart_order_routing(symbol, 'sell', amount, sell_price)  
                    
            logging.info("Completed trading loop iteration")
        except Exception as e:
            logging.error(f"Error in trading loop: {e}")
        time.sleep(60)  

if __name__ == "__main__":
    trading_loop()
