import pandas as pd
from ..utils.indicators import calculate_indicators
from datetime import datetime, timedelta

class SmartScalpingStrategy:
    """
    Improved scalping strategy with market regime filtering and trade frequency controls.
    
    Key Improvements:
    1. Market Regime Filter - Avoids low ATR, low volume, and ranging markets
    2. Pullback Entries - Waits for retracements instead of breakouts
    3. Trade Frequency Controls - Max trades per symbol/day with cooldown
    """
    
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.trade_counts = {}  # {symbol: {date: count}}
        self.loss_streaks = {}  # {symbol: (count, last_time)}
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Configuration
        self.MAX_TRADES_PER_SYMBOL_DAY = 10
        self.MAX_TOTAL_TRADES_DAY = 50
        self.LOSS_STREAK_THRESHOLD = 2
        self.COOLDOWN_MINUTES = 30
        
        # Regime Filter Thresholds
        self.MIN_ATR_PERCENTILE = 30  # Skip if ATR < 30th percentile
        self.MIN_EMA_COMPRESSION = 0.5  # Skip if EMAs too compressed
        self.MIN_VOLUME_STRENGTH = 1.2  # Require strong volume

    def _reset_daily_counters_if_needed(self):
        """Reset counters at start of new trading day."""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trade_count = 0
            self.last_reset_date = current_date
            # Clean up old dates from trade_counts
            for symbol in list(self.trade_counts.keys()):
                self.trade_counts[symbol] = {
                    date: count for date, count in self.trade_counts[symbol].items()
                    if date == current_date
                }

    def _can_trade_symbol(self, symbol):
        """Check trade frequency limits for a symbol."""
        self._reset_daily_counters_if_needed()
        current_date = datetime.now().date()
        
        # Check daily total limit
        if self.daily_trade_count >= self.MAX_TOTAL_TRADES_DAY:
            return False
        
        # Check per-symbol limit
        symbol_trades_today = self.trade_counts.get(symbol, {}).get(current_date, 0)
        if symbol_trades_today >= self.MAX_TRADES_PER_SYMBOL_DAY:
            return False
        
        # Check cooldown after loss streak
        if symbol in self.loss_streaks:
            streak_count, last_time = self.loss_streaks[symbol]
            if streak_count >= self.LOSS_STREAK_THRESHOLD:
                time_since_loss = datetime.now() - last_time
                if time_since_loss < timedelta(minutes=self.COOLDOWN_MINUTES):
                    return False
        
        return True

    def _record_trade(self, symbol):
        """Increment trade counters."""
        current_date = datetime.now().date()
        if symbol not in self.trade_counts:
            self.trade_counts[symbol] = {}
        self.trade_counts[symbol][current_date] = self.trade_counts[symbol].get(current_date, 0) + 1
        self.daily_trade_count += 1

    def _check_market_regime(self, last_row):
        """
        Filter out unfavorable market conditions.
        Returns True if market regime is favorable for trading.
        """
        # 1. ATR Filter - Skip low volatility
        if last_row['atr_percentile'] < self.MIN_ATR_PERCENTILE:
            return False
        
        # 2. EMA Compression Filter - Skip ranging markets
        if last_row['ema_compression'] < self.MIN_EMA_COMPRESSION:
            return False
        
        # 3. Volume Filter - Require strong participation
        if last_row['volume_strength'] < self.MIN_VOLUME_STRENGTH:
            return False
        
        return True

    def analyze(self, df: pd.DataFrame):
        """
        Analyzes the latest candle data with improved logic.
        Returns:
            signal (str): 'LONG', 'SHORT', or 'NONE'
            entry_price (float)
            stop_loss (float)
            take_profit (float)
        """
        if len(df) < 200:
            return 'NONE', 0, 0, 0

        df = calculate_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # Market Regime Filter (MOST IMPORTANT)
        if not self._check_market_regime(last_row):
            return 'NONE', 0, 0, 0
        
        signal = 'NONE'
        
        # LONG Condition - Improved Entry Logic
        if (
            # Trend Filter
            last_row['close'] > last_row['ema_trend'] and
            last_row['ema_fast'] > last_row['ema_slow'] and
            
            # VWAP Confirmation (must be above for longs)
            last_row['close'] > last_row['vwap'] and
            
            # RSI Filter - Not overbought, bullish zone
            35 < last_row['rsi'] < 65 and
            last_row['rsi'] > 50 and
            
            # Volume Confirmation
            last_row['volume'] > last_row['vol_ma']
        ):
            # PULLBACK ENTRY LOGIC (instead of breakout)
            # Wait for price to pull back to EMA_fast and bounce
            price_near_ema = abs(last_row['close'] - last_row['ema_fast']) / last_row['atr'] < 0.3
            price_bouncing = prev_row['close'] < prev_row['ema_fast'] and last_row['close'] >= last_row['ema_fast']
            
            # Alternative: VWAP reclaim entry
            vwap_reclaim = prev_row['close'] < prev_row['vwap'] and last_row['close'] > last_row['vwap']
            
            if price_bouncing or (price_near_ema and vwap_reclaim):
                signal = 'LONG'

        # SHORT Condition - Improved Entry Logic
        elif (
            # Trend Filter
            last_row['close'] < last_row['ema_trend'] and
            last_row['ema_fast'] < last_row['ema_slow'] and
            
            #VWAP Confirmation (must be below for shorts)
            last_row['close'] < last_row['vwap'] and
            
            # RSI Filter - Not oversold, bearish zone
            35 < last_row['rsi'] < 65 and
            last_row['rsi'] < 50 and
            
            # Volume Confirmation
            last_row['volume'] > last_row['vol_ma']
        ):
            # PULLBACK ENTRY LOGIC
            price_near_ema = abs(last_row['close'] - last_row['ema_fast']) / last_row['atr'] < 0.3
            price_bouncing = prev_row['close'] > prev_row['ema_fast'] and last_row['close'] <= last_row['ema_fast']
            
            # Alternative: VWAP rejection entry
            vwap_rejection = prev_row['close'] > prev_row['vwap'] and last_row['close'] < last_row['vwap']
            
            if price_bouncing or (price_near_ema and vwap_rejection):
                signal = 'SHORT'

        if signal != 'NONE':
            # Calculate Risk Parameters
            atr = last_row['atr']
            entry_price = last_row['close']
            
            # Volatility-Based Stop Loss with minimum distance
            sl_dist = max(atr * self.risk_manager.sl_multiplier, entry_price * 0.005)  # Min 0.5%
            
            # Dynamic Risk-Reward based on volatility
            # Higher volatility = wider targets
            rr_multiplier = 1.5 if last_row['atr_percentile'] > 60 else 2.0
            
            if signal == 'LONG':
                stop_loss = entry_price - sl_dist
                take_profit = entry_price + (sl_dist * rr_multiplier)
            else:
                stop_loss = entry_price + sl_dist
                take_profit = entry_price - (sl_dist * rr_multiplier)

            return signal, entry_price, stop_loss, take_profit

        return 'NONE', 0, 0, 0
