"""
Momentum Breakout Strategy
===========================
Rides strong momentum after market structure breaks and liquidity sweeps.

Entry Logic:
- Market structure break (higher high in uptrend / lower low in downtrend)
- Volume surge (2x average)
- RSI confirmation (>60 for LONG, <40 for SHORT)
- Enter on pullback to breakout level

Exit Logic:
- 3:1 minimum R:R
- Partial profits at 1.5R (50% position)
- Trailing stop to breakeven at 1R
"""
import pandas as pd
from ..utils.indicators import calculate_indicators

class MomentumBreakoutStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.name = "MomentumBreakout"
        
        # Configuration
        self.VOLUME_SURGE_MULTIPLIER = 2.0
        self.RSI_LONG_MIN = 60
        self.RSI_SHORT_MAX = 40
        self.PULLBACK_TOLERANCE_ATR = 0.5
        self.MIN_RR_RATIO = 3.0
        self.STRUCTURE_LOOKBACK = 20
        
    def _find_recent_high(self, df, lookback=20):
        """Find the most recent swing high."""
        return df['high'].iloc[-lookback:-1].max()
    
    def _find_recent_low(self, df, lookback=20):
        """Find the most recent swing low."""
        return df['low'].iloc[-lookback:-1].max()
    
    def _is_higher_high(self, curr_high, recent_high):
        """Check if current high breaks above recent high."""
        return curr_high > recent_high
    
    def _is_lower_low(self, curr_low, recent_low):
        """Check if current low breaks below recent low."""
        return curr_low < recent_low
    
    def _has_volume_surge(self, curr_volume, avg_volume):
        """Check for volume surge."""
        return curr_volume > avg_volume * self.VOLUME_SURGE_MULTIPLIER
    
    def _is_pullback_to_breakout(self, close, breakout_level, atr):
        """Check if price pulled back near breakout level."""
        tolerance = atr * self.PULLBACK_TOLERANCE_ATR
        return abs(close - breakout_level) <= tolerance
    
    def analyze(self, df: pd.DataFrame):
        """
        Analyze for momentum breakout signals.
        
        Returns:
            signal (str): 'LONG', 'SHORT', or 'NONE'
            entry_price (float)
            stop_loss (float)
            take_profit (float)
        """
        if len(df) < 200:
            return 'NONE', 0, 0, 0
        
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Find recent swing points
        recent_high = self._find_recent_high(df, self.STRUCTURE_LOOKBACK)
        recent_low = self._find_recent_low(df, self.STRUCTURE_LOOKBACK)
        
        signal = 'NONE'
        
        # ===== LONG: Higher High Breakout =====
        if self._is_higher_high(curr['high'], recent_high):
            # Confirm with volume and RSI
            has_volume = self._has_volume_surge(curr['volume'], curr['vol_ma'])
            rsi_ok = curr['rsi'] > self.RSI_LONG_MIN
            
            # Check if price pulled back to breakout level
            is_pullback = self._is_pullback_to_breakout(
                curr['close'], recent_high, curr['atr']
            )
            
            if has_volume and rsi_ok and is_pullback:
                signal = 'LONG'
                entry_price = curr['close']
                
                # Stop below recent swing low
                stop_loss = recent_low - (curr['atr'] * 0.5)
                
                # Target: 3R minimum
                sl_distance = entry_price - stop_loss
                take_profit = entry_price + (sl_distance * self.MIN_RR_RATIO)
                
                return signal, entry_price, stop_loss, take_profit
        
        # ===== SHORT: Lower Low Breakout =====
        if self._is_lower_low(curr['low'], recent_low):
            # Confirm with volume and RSI
            has_volume = self._has_volume_surge(curr['volume'], curr['vol_ma'])
            rsi_ok = curr['rsi'] < self.RSI_SHORT_MAX
            
            # Check if price pulled back to breakout level
            is_pullback = self._is_pullback_to_breakout(
                curr['close'], recent_low, curr['atr']
            )
            
            if has_volume and rsi_ok and is_pullback:
                signal = 'SHORT'
                entry_price = curr['close']
                
                # Stop above recent swing high
                stop_loss = recent_high + (curr['atr'] * 0.5)
                
                # Target: 3R minimum
                sl_distance = stop_loss - entry_price
                take_profit = entry_price - (sl_distance * self.MIN_RR_RATIO)
                
                return signal, entry_price, stop_loss, take_profit
        
        return 'NONE', 0, 0, 0
