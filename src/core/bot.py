import time
import threading
from datetime import datetime
from ..exchange.binance_client import BinanceClient
from ..exchange.websocket_manager import BinanceWebSocket, WebSocketDataProvider
from ..strategy.momentum_breakout_strategy import MomentumBreakoutStrategy
from ..strategy.mean_reversion_strategy import MeanReversionStrategy
from ..strategy.liquidity_grab_strategy import LiquidityGrabStrategy
from ..core.risk_manager import RiskManager
from ..database.db_manager import DBManager

class TradingBot:
    def __init__(self, config, db_manager):
        self.config = config
        self.db_manager = db_manager
        self.exchange = BinanceClient(config.BINANCE_API_KEY, config.BINANCE_API_SECRET, testnet=config.TESTNET)
        self.risk_manager = RiskManager(config, db_manager)
        
        # Initialize NEW profitable strategies
        self.strategies = [
            # ("MomentumBreakout", MomentumBreakoutStrategy(self.risk_manager)),  # DISABLED - losing money
            # ("MeanReversion", MeanReversionStrategy(self.risk_manager)),  # DISABLED - losing money
            ("LiquidityGrab", LiquidityGrabStrategy(self.risk_manager))
        ]
        
        self.symbols = getattr(config, 'SYMBOLS', [config.SYMBOL])
        self.timeframe = config.TIMEFRAME
        self.is_running = False
        self._stop_event = threading.Event()
        
        # WebSocket for real-time data
        self.ws_manager = None
        self.data_provider = None
        self.use_websocket = getattr(config, 'USE_WEBSOCKET', True)

    def _on_candle_close(self, symbol, df):
        """Callback when a candle closes - run strategy analysis immediately."""
        if not self.is_running or df.empty:
            return
        
        try:
            current_price = df['close'].iloc[-1]
            
            # Check for exits
            self.manage_open_trades_for_symbol(symbol, current_price)
            
            # Run strategies
            for strategy_name, strategy in self.strategies:
                signal, entry_price, stop_loss, take_profit = strategy.analyze(df, symbol=symbol)
                if signal != 'NONE':
                    self.execute_trade(symbol, signal, entry_price, stop_loss, take_profit, strategy_name)
        except Exception as e:
            print(f"Error processing {symbol} on candle close: {e}")

    def start(self):
        self.is_running = True
        self._stop_event.clear()
        print(f"Bot started for {len(self.symbols)} pairs on {self.timeframe} timeframe.")
        print(f"Pairs: {', '.join(self.symbols)}")
        self.db_manager.update_bot_state(is_running=True)
        
        # Initialize WebSocket
        if self.use_websocket:
            try:
                self.ws_manager = BinanceWebSocket(
                    symbols=self.symbols,
                    timeframe=self.timeframe,
                    testnet=self.config.TESTNET,
                    on_candle_close=self._on_candle_close
                )
                self.ws_manager.start()
                self.data_provider = WebSocketDataProvider(self.exchange, self.ws_manager)
                print("🚀 WebSocket mode enabled - real-time data streaming")
            except Exception as e:
                print(f"⚠️ WebSocket init failed: {e}, falling back to HTTP polling")
                self.use_websocket = False
        
        self.run_loop()

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        print("Bot stopping...")
        
        # Stop WebSocket
        if self.ws_manager:
            self.ws_manager.stop()
        
        self.db_manager.update_bot_state(is_running=False)

    def run_loop(self):
        """Main loop - with WebSocket, this mainly handles exits and health checks."""
        while not self._stop_event.is_set():
            state = self.db_manager.get_bot_state()
            if state and not state.is_running:
                self.is_running = False
                break
            
            try:
                # In WebSocket mode: strategies are triggered by candle close callback
                # This loop just handles periodic tasks and fallback
                for symbol in self.symbols:
                    if self._stop_event.is_set():
                        break
                    
                    # Always check for exits with current price
                    if self.ws_manager and self.ws_manager.is_ready(symbol):
                        current_price = self.ws_manager.get_current_price(symbol)
                        if current_price:
                            self.manage_open_trades_for_symbol(symbol, current_price)
                    else:
                        # Fallback to HTTP if WebSocket data not ready
                        self.process_symbol(symbol)
                        
            except Exception as e:
                print(f"Error in main loop: {e}")
            
            # Sleep less in WebSocket mode since callbacks handle most work
            time.sleep(5 if self.use_websocket else 10)

    def process_symbol(self, symbol):
        """Process a single symbol (HTTP fallback mode)."""
        try:
            # Get data from provider (WebSocket cache or HTTP)
            if self.data_provider:
                df = self.data_provider.get_candles(symbol, self.timeframe, limit=205)
            else:
                df = self.exchange.get_historical_klines(symbol, self.timeframe, limit=205)
            if df.empty:
                return

            current_price = df['close'].iloc[-1]
            
            # 2. Check for Exits (Manage Open Trades for this symbol)
            self.manage_open_trades_for_symbol(symbol, current_price)

            # 3. Run EACH strategy
            for strategy_name, strategy in self.strategies:
                signal, entry_price, stop_loss, take_profit = strategy.analyze(df)
                
                # 4. Execute New Trade
                if signal != 'NONE':
                    self.execute_trade(symbol, signal, entry_price, stop_loss, take_profit, strategy_name)
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    def execute_trade(self, symbol, signal, entry_price, stop_loss, take_profit, strategy_name):
        open_trades = self.db_manager.get_open_trades()
        # Ensure only one trade per symbol PER STRATEGY
        if any(t.symbol == symbol and t.strategy == strategy_name for t in open_trades):
            return

        # Risk Checks
        account_balance, _ = self.exchange.get_account_balance('USDT')
        if not self.risk_manager.can_open_trade(account_balance):
            return

        position_size = self.risk_manager.calculate_position_size(account_balance, entry_price, stop_loss)
        
        # Round position size based on asset price (precision adjustment)
        if entry_price > 1000:  # BTC, etc.
            position_size = round(position_size, 3)
        elif entry_price > 10:  # ETH, BNB, etc.
            position_size = round(position_size, 2)
        elif entry_price > 1:   # SOL, LINK, etc.
            position_size = round(position_size, 1)
        else:                   # DOGE, XRP, etc.
            position_size = round(position_size, 0)
        
        if position_size <= 0:
            return
        
        print(f"📈 [{strategy_name}] {symbol} {signal} | Entry: {entry_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f} | Size: {position_size}")

        if self.config.DRY_RUN:
            print("DRY RUN: Trade simulated.")
            trade = self.db_manager.add_trade(
                symbol=symbol,
                side=signal,
                entry_price=entry_price,
                quantity=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=strategy_name
            )
        else:
            # Live execution logic
            try:
                side = 'BUY' if signal == 'LONG' else 'SELL'
                order = self.exchange.place_order(symbol, side, position_size, 'MARKET')
                if order:
                    self.db_manager.add_trade(
                        symbol=symbol,
                        side=signal,
                        entry_price=entry_price,
                        quantity=position_size,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        strategy=strategy_name
                    )
            except Exception as e:
                print(f"Error placing order for {symbol}: {e}")

    def manage_open_trades_for_symbol(self, symbol, current_price):
        """Manage open trades for a specific symbol."""
        open_trades = self.db_manager.get_open_trades()
        for trade in open_trades:
            if trade.symbol != symbol:
                continue
            if not trade.stop_loss or not trade.take_profit:
                continue

            should_close = False
            exit_reason = ""
            
            if trade.side == 'LONG':
                if current_price <= trade.stop_loss:
                    should_close = True
                    exit_reason = "SL Hit"
                elif current_price >= trade.take_profit:
                    should_close = True
                    exit_reason = "TP Hit"
            elif trade.side == 'SHORT':
                if current_price >= trade.stop_loss:
                    should_close = True
                    exit_reason = "SL Hit"
                elif current_price <= trade.take_profit:
                    should_close = True
                    exit_reason = "TP Hit"
            
            if should_close:
                # Calculate Gross PnL
                if trade.side == 'LONG':
                    gross_pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    gross_pnl = (trade.entry_price - current_price) * trade.quantity
                
                # Calculate Fees (Entry + Exit)
                # Fee = (Entry Value + Exit Value) * Fee Rate
                entry_value = trade.entry_price * trade.quantity
                exit_value = current_price * trade.quantity
                fee = (entry_value + exit_value) * self.config.TRADING_FEE_RATE
                
                net_pnl = gross_pnl - fee
                
                print(f"📉 Closing {trade.symbol} {trade.side}: {exit_reason} at {current_price:.2f} | Gross PnL: {gross_pnl:.4f} | Fee: {fee:.4f} | Net PnL: {net_pnl:.4f}")
                
                if self.config.DRY_RUN:
                    self.db_manager.close_trade(trade.id, current_price, net_pnl)
                else:
                    # Live Close Logic
                    try:
                        close_side = 'SELL' if trade.side == 'LONG' else 'BUY'
                        order = self.exchange.place_order(trade.symbol, close_side, trade.quantity, 'MARKET')
                        if order:
                            self.db_manager.close_trade(trade.id, current_price, net_pnl)
                    except Exception as e:
                        print(f"Error closing trade {trade.id}: {e}")
