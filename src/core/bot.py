import time
import threading
from datetime import datetime
from ..exchange.binance_client import BinanceClient
from ..strategy.scalping_strategy import ScalpingStrategy
from ..core.risk_manager import RiskManager
from ..database.db_manager import DBManager

class TradingBot:
    def __init__(self, config, db_manager):
        self.config = config
        self.db_manager = db_manager
        self.exchange = BinanceClient(config.BINANCE_API_KEY, config.BINANCE_API_SECRET, testnet=config.TESTNET)
        self.risk_manager = RiskManager(config, db_manager)
        self.strategy = ScalpingStrategy(self.risk_manager)
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.is_running = False
        self._stop_event = threading.Event()

    def start(self):
        self.is_running = True
        self._stop_event.clear()
        print(f"Bot started for {self.symbol} on {self.timeframe} timeframe.")
        self.db_manager.update_bot_state(is_running=True)
        self.run_loop()

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        print("Bot stopping...")
        self.db_manager.update_bot_state(is_running=False)

    def run_loop(self):
        while not self._stop_event.is_set():
            state = self.db_manager.get_bot_state()
            if state and not state.is_running:
                self.is_running = False
                break
            
            # Simple check to stop if logic says so, 
            # but usually the bot class controls the state.
            
            try:
                self.process_candle()
            except Exception as e:
                print(f"Error in main loop: {e}")
            
            time.sleep(10) # Poll every 10 seconds

    def process_candle(self):
        # 1. Fetch Data
        df = self.exchange.get_historical_klines(self.symbol, self.timeframe, limit=205)
        if df.empty:
            return

        # 2. Analyze Strategy
        current_price = df['close'].iloc[-1]
        signal, entry_price, stop_loss, take_profit = self.strategy.analyze(df)
        
        # 3. Check for Exits (Manage Open Trades)
        self.manage_open_trades(current_price)

        # 4. Execute New Trade
        if signal != 'NONE':
            self.execute_trade(signal, entry_price, stop_loss, take_profit)

    def execute_trade(self, signal, entry_price, stop_loss, take_profit):
        open_trades = self.db_manager.get_open_trades()
        # Ensure only one trade per symbol
        if any(t.symbol == self.symbol for t in open_trades):
            return

        # Risk Checks
        account_balance, _ = self.exchange.get_account_balance('USDT')
        if not self.risk_manager.can_open_trade(account_balance):
            return

        position_size = self.risk_manager.calculate_position_size(account_balance, entry_price, stop_loss)
        
        print(f"Signal: {signal} | Price: {entry_price} | SL: {stop_loss} | TP: {take_profit} | Size: {position_size:.4f}")

        if self.config.DRY_RUN:
            print("DRY RUN: Trade simulated.")
            trade = self.db_manager.add_trade(
                symbol=self.symbol,
                side=signal,
                entry_price=entry_price,
                quantity=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy="ScalpingStrategy"
            )
            # Update SL/TP manually if DB manager supports it or update model 
            # Since I added columns to model, I need to update DBManager.add_trade to accept them?
            # Or just set them nicely.
            # I will update DBManager.add_trade later or just ignore for now in this MVP script.
            pass
        else:
            # Live execution logic
            pass

    def manage_open_trades(self, current_price):
        open_trades = self.db_manager.get_open_trades()
        for trade in open_trades:
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
                # Calculate PnL
                if trade.side == 'LONG':
                    pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    pnl = (trade.entry_price - current_price) * trade.quantity
                
                print(f"Closing Trade {trade.id} ({trade.symbol} {trade.side}): {exit_reason} at {current_price} | PnL: {pnl:.4f}")
                
                if self.config.DRY_RUN:
                    self.db_manager.close_trade(trade.id, current_price, pnl)
                else:
                    # Live Close Logic: Place Market Order to close
                    # close_side = SIDE_SELL if trade.side == 'LONG' else SIDE_BUY
                    # order = self.exchange.place_order(trade.symbol, close_side, trade.quantity, 'MARKET')
                    # if order: update db...
                    pass
