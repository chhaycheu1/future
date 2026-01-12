from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime

class BinanceClient:
    def __init__(self, api_key, api_secret, testnet=False):
        self.client = Client(api_key, api_secret, testnet=testnet)
    
    def get_market_price(self, symbol):
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None

    def get_historical_klines(self, symbol, interval, limit=100):
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'quote_asset_volume', 'number_of_trades', 
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            return df
        except BinanceAPIException as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return pd.DataFrame()

    def get_account_balance(self, asset='USDT'):
        try:
            account = self.client.futures_account()
            for balance in account['assets']:
                if balance['asset'] == asset:
                    return float(balance['walletBalance']), float(balance['availableBalance'])
            return 0.0, 0.0
        except BinanceAPIException as e:
            print(f"Error fetching balance: {e}")
            return 0.0, 0.0

    def get_position(self, symbol):
        try:
            # positions = self.client.futures_position_information(symbol=symbol) # This often returns multiple entries
            # We want to be safe, so we iterate
            account = self.client.futures_account()
            for position in account['positions']:
                if position['symbol'] == symbol:
                    amt = float(position['positionAmt'])
                    entry_price = float(position['entryPrice'])
                    unrealized_profit = float(position['unrealizedProfit'])
                    return {
                        'symbol': symbol,
                        'amount': amt,
                        'entry_price': entry_price,
                        'unrealized_pnl': unrealized_profit,
                        'side': 'LONG' if amt > 0 else 'SHORT' if amt < 0 else 'NONE'
                    }
            return None
        except BinanceAPIException as e:
            print(f"Error fetching position for {symbol}: {e}")
            return None

    def place_order(self, symbol, side, quantity, order_type='MARKET', price=None):
        try:
            # Side: 'BUY' or 'SELL'
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            if order_type == 'LIMIT':
                params['timeInForce'] = TIME_IN_FORCE_GTC
                params['price'] = price
            
            order = self.client.futures_create_order(**params)
            return order
        except BinanceAPIException as e:
            print(f"Error placing order for {symbol}: {e}")
            return None
            
    def set_leverage(self, symbol, leverage):
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            print(f"Leverage for {symbol} set to {leverage}x")
        except BinanceAPIException as e:
            print(f"Error setting leverage: {e}")
