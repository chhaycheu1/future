"""
Liquidity Grab Strategy
========================
Trades reversals after stop hunts (liquidity sweeps).

Entry Logic:
- Identify key support/resistance levels
- Wait for sweep: wick beyond level, close back inside
- Volume spike confirmation
- Enter on next candle in reversal direction

Exit Logic:
- Target: Previous swing high/low (2:1+ R:R)
- Stop: Beyond sweep wick
- Max 1 trade per sweep event
"""
import pandas as pd
import numpy as np
from ..utils.indicators import calculate_indicators

class LiquidityGrabStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.name = "LiquidityGrab"
        
        # Configuration
        self.LEVEL_LOOKBACK = 50
        self.LEVEL_TOLERANCE_PERCENT = 0.002  # 0.2% tolerance
        self.MIN_TOUCHES = 2
        self.SWEEP_THRESHOLD_ATR = 0.3
        self.VOLUME_SURGE_MULTIPLIER = 1.5
        self.MIN_RR_RATIO = 2.0
        
        # State tracking
        self.last_sweep_candle = {}  # {symbol: candle_index}
        
    def _find_key_levels(self, df):
        """
        Find significant support/resistance levels.
        Returns levels that have been tested multiple times.
        """
        highs = df['high'].iloc[-self.LEVEL_LOOKBACK:].values
        lows = df['low'].iloc[-self.LEVEL_LOOKBACK:].values
        closes = df['close'].iloc[-self.LEVEL_LOOKBACK:].values
        
        avg_price = np.mean(closes)
        tolerance = avg_price * self.LEVEL_TOLERANCE_PERCENT
        
        # Find resistance levels (clustered highs)
        resistance_levels = []
        sorted_highs = np.unique(np.round(highs, 2))
        
        for level in sorted_highs:
            touches = np.sum(np.abs(highs - level) <= tolerance)
            if touches >= self.MIN_TOUCHES:
                resistance_levels.append(level)
        
        # Find support levels (clustered lows)
        support_levels = []
        sorted_lows = np.unique(np.round(lows, 2))
        
        for level in sorted_lows:
            touches = np.sum(np.abs(lows - level) <= tolerance)
            if touches >= self.MIN_TOUCHES:
                support_levels.append(level)
        
        return support_levels, resistance_levels
    
    def _detect_liquidity_sweep_bullish(self, curr, prev, support_level, atr):
        """
        Detect bullish liquidity sweep.
        - Wick breaks below support
        - Candle closes back above support
        - Bearish to bullish reversal
        """
        sweep_threshold = atr * self.SWEEP_THRESHOLD_ATR
        
        # Check if wick swept below support
        wick_swept = curr['low'] < (support_level - sweep_threshold)
        
        # Check if closed back above support
        closed_above = curr['close'] > support_level
        
        # Reversal pattern (engulfing or strong bounce)
        is_bullish_close = curr['close'] > curr['open']
        strong_recovery = (curr['close'] - curr['low']) > (curr['high'] - curr['low']) * 0.7
        
        return wick_swept and closed_above and is_bullish_close and strong_recovery
    
    def _detect_liquidity_sweep_bearish(self, curr, prev, resistance_level, atr):
        """
        Detect bearish liquidity sweep.
        - Wick breaks above resistance
        - Candle closes back below resistance
        - Bullish to bearish reversal
        """
        sweep_threshold = atr * self.SWEEP_THRESHOLD_ATR
        
        # Check if wick swept above resistance
        wick_swept = curr['high'] > (resistance_level + sweep_threshold)
        
        # Check if closed back below resistance
        closed_below = curr['close'] < resistance_level
        
        # Reversal pattern
        is_bearish_close = curr['close'] < curr['open']
        strong_rejection = (curr['high'] - curr['close']) > (curr['high'] - curr['low']) * 0.7
        
        return wick_swept and closed_below and is_bearish_close and strong_rejection
    
    def _find_nearest_level(self, price, levels):
        """Find the nearest level to current price."""
        if not levels:
            return None
        
        levels_array = np.array(levels)
        distances = np.abs(levels_array - price)
        nearest_idx = np.argmin(distances)
        
        return levels_array[nearest_idx]
    
    def analyze(self, df: pd.DataFrame, symbol='UNKNOWN'):
        """
        Analyze for liquidity grab signals.
        
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
        
        # Find key support/resistance levels
        support_levels, resistance_levels = self._find_key_levels(df)
        
        if not support_levels and not resistance_levels:
            return 'NONE', 0, 0, 0
        
        # Find nearest levels to current price
        nearest_support = self._find_nearest_level(curr['close'], support_levels)
        nearest_resistance = self._find_nearest_level(curr['close'], resistance_levels)
        
        signal = 'NONE'
        
        # ===== LONG: Bullish Liquidity Sweep =====
        if nearest_support is not None:
            is_sweep = self._detect_liquidity_sweep_bullish(
                curr, prev, nearest_support, curr['atr']
            )
            
            # Volume confirmation
            has_volume_spike = curr['volume'] > curr['vol_ma'] * self.VOLUME_SURGE_MULTIPLIER
            
            if is_sweep and has_volume_spike:
                signal = 'LONG'
                entry_price = curr['close']
                
                # Stop beyond sweep wick
                stop_loss = curr['low'] - (curr['atr'] * 0.3)
                
                # Target: Previous high (opposite side of range)
                if resistance_levels:
                    take_profit = min(resistance_levels)
                else:
                    # Fallback: 2R minimum
                    sl_distance = entry_price - stop_loss
                    take_profit = entry_price + (sl_distance * self.MIN_RR_RATIO)
                
                # Ensure minimum R:R
                sl_distance = entry_price - stop_loss
                min_tp = entry_price + (sl_distance * self.MIN_RR_RATIO)
                take_profit = max(take_profit, min_tp)
                
                return signal, entry_price, stop_loss, take_profit
        
        # ===== SHORT: Bearish Liquidity Sweep =====
        if nearest_resistance is not None:
            is_sweep = self._detect_liquidity_sweep_bearish(
                curr, prev, nearest_resistance, curr['atr']
            )
            
            # Volume confirmation
            has_volume_spike = curr['volume'] > curr['vol_ma'] * self.VOLUME_SURGE_MULTIPLIER
            
            if is_sweep and has_volume_spike:
                signal = 'SHORT'
                entry_price = curr['close']
                
                # Stop beyond sweep wick
                stop_loss = curr['high'] + (curr['atr'] * 0.3)
                
                # Target: Previous low (opposite side of range)
                if support_levels:
                    take_profit = max(support_levels)
                else:
                    # Fallback: 2R minimum
                    sl_distance = stop_loss - entry_price
                    take_profit = entry_price - (sl_distance * self.MIN_RR_RATIO)
                
                # Ensure minimum R:R
                sl_distance = stop_loss - entry_price
                min_tp = entry_price - (sl_distance * self.MIN_RR_RATIO)
                take_profit = min(take_profit, min_tp)
                
                return signal, entry_price, stop_loss, take_profit
        
        return 'NONE', 0, 0, 0
