"""
Binance WebSocket Manager
=========================
Handles real-time kline (candlestick) streams from Binance Futures.
Uses websocket-client library for reliable connections.
"""
import json
import threading
import time
from collections import defaultdict
from datetime import datetime
import pandas as pd

    USE_BINANCE_WS = True
except ImportError:
    USE_BINANCE_WS = False
    try:
        import websocket
    except ImportError:
        websocket = None
        print("Warning: websocket-client not installed. WebSocket features will be disabled.")

# WebSocket endpoints
TESTNET_WS_URL = "wss://stream.binancefuture.com/ws"
MAINNET_WS_URL = "wss://fstream.binance.com/ws"


class BinanceWebSocket:
    """
    Manages WebSocket connections to Binance Futures for real-time kline data.
    Maintains a local cache of candle data that gets updated in real-time.
    """
    
    def __init__(self, symbols, timeframe="1m", testnet=False, on_candle_close=None):
        """
        Args:
            symbols: List of trading pairs (e.g., ["BTCUSDT", "ETHUSDT"])
            timeframe: Candle interval (e.g., "1m", "5m", "15m")
            testnet: If True, connects to testnet WebSocket
            on_candle_close: Callback function called when a candle closes
        """
        self.symbols = [s.lower() for s in symbols]
        self.timeframe = timeframe
        self.testnet = testnet
        self.on_candle_close = on_candle_close
        
        # Local candle cache: {symbol: DataFrame}
        self.candle_cache = defaultdict(lambda: pd.DataFrame())
        self.cache_lock = threading.Lock()
        
        # Current (incomplete) candle data
        self.current_candles = {}
        
        # Connection state
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.connected = False
        self.reconnect_count = 0
        self.max_reconnects = 10
        
        # Use appropriate endpoint
        self.ws_url = TESTNET_WS_URL if testnet else MAINNET_WS_URL
        
    def _build_stream_url(self):
        """Build the combined stream URL for multiple symbols."""
        streams = [f"{symbol}@kline_{self.timeframe}" for symbol in self.symbols]
        stream_param = "/".join(streams)
        return f"{self.ws_url}/{stream_param}"
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            
            # Handle combined stream format
            if 'data' in data:
                data = data['data']
            
            if 'e' not in data or data['e'] != 'kline':
                return
                
            kline = data['k']
            symbol = kline['s'].upper()
            is_closed = kline['x']
            
            # Update current candle
            candle_data = {
                'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v']),
            }
            
            self.current_candles[symbol] = candle_data
            
            # If candle is closed, add to cache and trigger callback
            if is_closed:
                with self.cache_lock:
                    df = self.candle_cache[symbol]
                    new_row = pd.DataFrame([candle_data])
                    
                    if df.empty:
                        self.candle_cache[symbol] = new_row
                    else:
                        # Append and keep only last 250 candles
                        self.candle_cache[symbol] = pd.concat([df, new_row], ignore_index=True).tail(250)
                
                # Trigger callback for strategy analysis
                if self.on_candle_close:
                    self.on_candle_close(symbol, self.get_candles(symbol))
                    
        except Exception as e:
            print(f"WebSocket message error: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket error."""
        print(f"WebSocket error: {error}")
        self.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connected = False
        
        # Auto-reconnect if still running
        if self.running and self.reconnect_count < self.max_reconnects:
            self.reconnect_count += 1
            print(f"Reconnecting... (attempt {self.reconnect_count}/{self.max_reconnects})")
            time.sleep(5)  # Wait before reconnecting
            self._connect()
    
    def _on_open(self, ws):
        """Handle WebSocket open."""
        print(f"✅ WebSocket connected to Binance {'Testnet' if self.testnet else 'Mainnet'}")
        print(f"📡 Streaming {len(self.symbols)} symbols on {self.timeframe} timeframe")
        self.connected = True
        self.reconnect_count = 0
    
    def _connect(self):
        """Establish WebSocket connection."""
        if not websocket:
            print("Cannot connect: websocket-client library is not installed.")
            self.running = False
            return

        url = self._build_stream_url()
        
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        self.ws.run_forever()
    
    def start(self):
        """Start WebSocket connection in background thread."""
        if self.running:
            return
            
        self.running = True
        self.ws_thread = threading.Thread(target=self._connect, daemon=True)
        self.ws_thread.start()
        
        # Wait for connection
        timeout = 10
        start = time.time()
        while not self.connected and time.time() - start < timeout:
            time.sleep(0.1)
        
        if not self.connected:
            print("⚠️ WebSocket connection timeout - will retry in background")
    
    def stop(self):
        """Stop WebSocket connection."""
        self.running = False
        if self.ws:
            self.ws.close()
    
    def get_candles(self, symbol, limit=205):
        """
        Get cached candles for a symbol.
        Returns DataFrame similar to HTTP API response.
        """
        symbol = symbol.upper()
        
        with self.cache_lock:
            df = self.candle_cache.get(symbol, pd.DataFrame())
            
            if df.empty:
                return pd.DataFrame()
            
            # Include current (incomplete) candle if available
            if symbol in self.current_candles:
                current = pd.DataFrame([self.current_candles[symbol]])
                df = pd.concat([df, current], ignore_index=True)
            
            return df.tail(limit).copy()
    
    def is_ready(self, symbol):
        """Check if we have enough cached data for a symbol."""
        symbol = symbol.upper()
        with self.cache_lock:
            df = self.candle_cache.get(symbol, pd.DataFrame())
            return len(df) >= 200
    
    def get_current_price(self, symbol):
        """Get the latest price for a symbol."""
        symbol = symbol.upper()
        if symbol in self.current_candles:
            return self.current_candles[symbol]['close']
        return None


class WebSocketDataProvider:
    """
    Provides a unified interface for getting candle data.
    Falls back to HTTP if WebSocket data is not ready.
    """
    
    def __init__(self, http_client, ws_manager):
        self.http_client = http_client
        self.ws_manager = ws_manager
    
    def get_candles(self, symbol, timeframe, limit=205):
        """
        Get candles, preferring WebSocket cache but falling back to HTTP.
        """
        # Try WebSocket first
        if self.ws_manager and self.ws_manager.is_ready(symbol):
            df = self.ws_manager.get_candles(symbol, limit)
            if not df.empty:
                return df
        
        # Fallback to HTTP
        return self.http_client.get_historical_klines(symbol, timeframe, limit)
    
    def get_current_price(self, symbol):
        """Get current price, preferring WebSocket."""
        if self.ws_manager:
            price = self.ws_manager.get_current_price(symbol)
            if price:
                return price
        
        # Fallback to HTTP
        return self.http_client.get_market_price(symbol)
