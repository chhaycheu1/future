"""
Range + Liquidity Sweep Strategy
=================================
Timeframe: 5m

Rules:
1. Range Detection: Equal highs/lows (2+ touches)
2. Range Size: > 2x ATR
3. Liquidity Sweep: Price breaks and quickly reverses (fake breakout)
4. Entry: On reversal candle after sweep
5. Stop Loss: Beyond sweep extreme
6. Take Profit: 2R
"""
import pandas as pd
import numpy as np
from ..utils.indicators import calculate_indicators

class RangeSweepStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        
        # Configuration
        self.RANGE_LOOKBACK = 50
        self.EQUAL_LEVEL_TOLERANCE = 0.001  # 0.1% tolerance for equal highs/lows
        self.MIN_TOUCHES = 2
        self.MIN_RANGE_ATR = 2.0
        self.SWEEP_THRESHOLD_ATR = 0.3
        self.TP_RR_RATIO = 2.0
    
    def _find_range_levels(self, df, atr):
        """Find range highs and lows with multiple touches."""
        highs = df['high'].iloc[-self.RANGE_LOOKBACK:].values
        lows = df['low'].iloc[-self.RANGE_LOOKBACK:].values
        
        tolerance = df['close'].iloc[-1] * self.EQUAL_LEVEL_TOLERANCE
        
        # Find resistance (equal highs)
        resistance_level = None
        resistance_touches = 0
        sorted_highs = np.sort(highs)[::-1]  # Descending
        
        for level in sorted_highs[:10]:  # Check top 10 highs
            touches = np.sum(np.abs(highs - level) < tolerance)
            if touches >= self.MIN_TOUCHES:
                resistance_level = level
                resistance_touches = touches
                break
        
        # Find support (equal lows)
        support_level = None
        support_touches = 0
        sorted_lows = np.sort(lows)
        
        for level in sorted_lows[:10]:  # Check bottom 10 lows
            touches = np.sum(np.abs(lows - level) < tolerance)
            if touches >= self.MIN_TOUCHES:
                support_level = level
                support_touches = touches
                break
        
        return resistance_level, resistance_touches, support_level, support_touches
    
    def _is_valid_range(self, resistance, support, atr):
        """Check if range is large enough."""
        if resistance is None or support is None:
            return False
        range_size = resistance - support
        return range_size >= self.MIN_RANGE_ATR * atr
    
    def _detect_sweep(self, curr, prev, level, is_high_sweep, atr):
        """Detect a liquidity sweep (fake breakout)."""
        sweep_threshold = atr * self.SWEEP_THRESHOLD_ATR
        
        if is_high_sweep:  # Break above resistance and reverse
            broke_above = curr['high'] > level + sweep_threshold
            closed_below = curr['close'] < level
            reversal = curr['close'] < curr['open']  # Bearish candle
            return broke_above and closed_below and reversal
        else:  # Break below support and reverse
            broke_below = curr['low'] < level - sweep_threshold
            closed_above = curr['close'] > level
            reversal = curr['close'] > curr['open']  # Bullish candle
            return broke_below and closed_above and reversal
    
    def analyze(self, df: pd.DataFrame):
        """Analyze for Range Sweep entry signals."""
        if len(df) < 200:
            return 'NONE', 0, 0, 0
        
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        atr = curr['atr']
        
        # Find range levels
        resistance, res_touches, support, sup_touches = self._find_range_levels(df, atr)
        
        # Check if valid range exists
        if not self._is_valid_range(resistance, support, atr):
            return 'NONE', 0, 0, 0
        
        signal = 'NONE'
        
        # ===== SHORT: Sweep of resistance (fake breakout up) =====
        if self._detect_sweep(curr, prev, resistance, is_high_sweep=True, atr=atr):
            signal = 'SHORT'
            entry_price = curr['close']
            stop_loss = curr['high'] + (atr * 0.2)
            sl_distance = stop_loss - entry_price
            take_profit = entry_price - (sl_distance * self.TP_RR_RATIO)
            return signal, entry_price, stop_loss, take_profit
        
        # ===== LONG: Sweep of support (fake breakout down) =====
        if self._detect_sweep(curr, prev, support, is_high_sweep=False, atr=atr):
            signal = 'LONG'
            entry_price = curr['close']
            stop_loss = curr['low'] - (atr * 0.2)
            sl_distance = entry_price - stop_loss
            take_profit = entry_price + (sl_distance * self.TP_RR_RATIO)
            return signal, entry_price, stop_loss, take_profit
        
        return 'NONE', 0, 0, 0
