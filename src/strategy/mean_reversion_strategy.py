"""
Mean Reversion Strategy
=======================
Fades extreme price deviations back to VWAP/mean in ranging markets.

Entry Logic:
- Price deviates 2+ standard deviations from VWAP
- RSI divergence (price makes lower low, RSI makes higher low)
- Volume drying up (exhaustion signal)
- Only trade in low-trend environments (ADX < 25)

Exit Logic:
- Target: VWAP or middle Bollinger Band
- 2:1 minimum R:R
- Stop beyond recent extreme wick
"""
import pandas as pd
import numpy as np
from ..utils.indicators import calculate_indicators

class MeanReversionStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.name = "MeanReversion"
        
        # Configuration
        self.STD_DEV_THRESHOLD = 2.0
        self.MAX_ADX = 25  # Only trade in ranging markets
        self.VOLUME_DECLINE_RATIO = 0.7
        self.MIN_RR_RATIO = 2.0
        self.DIVERGENCE_LOOKBACK = 5
        
    def _calculate_vwap_distance(self, price, vwap, atr):
        """Calculate price distance from VWAP in ATR units."""
        return (price - vwap) / atr
    
    def _check_rsi_divergence_bullish(self, df, lookback=5):
        """
        Check for bullish RSI divergence.
        Price makes lower low, RSI makes higher low.
        """
        recent_df = df.iloc[-lookback:]
        
        # Find price lows
        price_lows = recent_df['low'].values
        rsi_values = recent_df['rsi'].values
        
        if len(price_lows) < 2:
            return False
        
        # Check if price made lower low
        price_lower_low = price_lows[-1] < price_lows[-2]
        
        # Check if RSI made higher low
        rsi_higher_low = rsi_values[-1] > rsi_values[-2]
        
        return price_lower_low and rsi_higher_low
    
    def _check_rsi_divergence_bearish(self, df, lookback=5):
        """
        Check for bearish RSI divergence.
        Price makes higher high, RSI makes lower high.
        """
        recent_df = df.iloc[-lookback:]
        
        # Find price highs
        price_highs = recent_df['high'].values
        rsi_values = recent_df['rsi'].values
        
        if len(price_highs) < 2:
            return False
        
        # Check if price made higher high
        price_higher_high = price_highs[-1] > price_highs[-2]
        
        # Check if RSI made lower high
        rsi_lower_high = rsi_values[-1] < rsi_values[-2]
        
        return price_higher_high and rsi_lower_high
    
    def _is_volume_declining(self, curr_volume, avg_volume):
        """Check if volume is drying up (exhaustion)."""
        return curr_volume < avg_volume * self.VOLUME_DECLINE_RATIO
    
    def _calculate_adx(self, df, period=14):
        """
        Calculate Average Directional Index (ADX).
        ADX < 25 indicates ranging market.
        """
        # Simplified ADX calculation
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / atr
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.iloc[-1] if len(adx) > 0 else 50
    
    def analyze(self, df: pd.DataFrame):
        """
        Analyze for mean reversion signals.
        
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
        
        # Only trade in ranging markets
        adx = self._calculate_adx(df)
        if adx > self.MAX_ADX:
            return 'NONE', 0, 0, 0
        
        # Calculate deviation from VWAP
        vwap_distance = self._calculate_vwap_distance(
            curr['close'], curr['vwap'], curr['atr']
        )
        
        signal = 'NONE'
        
        # ===== LONG: Oversold Mean Reversion =====
        if vwap_distance < -self.STD_DEV_THRESHOLD:
            # Check for bullish divergence
            has_divergence = self._check_rsi_divergence_bullish(df, self.DIVERGENCE_LOOKBACK)
            
            # Check for volume exhaustion
            volume_declining = self._is_volume_declining(curr['volume'], curr['vol_ma'])
            
            # RSI oversold
            rsi_oversold = curr['rsi'] < 30
            
            if has_divergence and volume_declining and rsi_oversold:
                signal = 'LONG'
                entry_price = curr['close']
                
                # Stop beyond recent low
                recent_low = df['low'].iloc[-10:].min()
                stop_loss = recent_low - (curr['atr'] * 0.5)
                
                # Target: VWAP (mean reversion target)
                take_profit = curr['vwap']
                
                # Ensure minimum 2R
                sl_distance = entry_price - stop_loss
                min_tp = entry_price + (sl_distance * self.MIN_RR_RATIO)
                take_profit = max(take_profit, min_tp)
                
                return signal, entry_price, stop_loss, take_profit
        
        # ===== SHORT: Overbought Mean Reversion =====
        elif vwap_distance > self.STD_DEV_THRESHOLD:
            # Check for bearish divergence
            has_divergence = self._check_rsi_divergence_bearish(df, self.DIVERGENCE_LOOKBACK)
            
            # Check for volume exhaustion
            volume_declining = self._is_volume_declining(curr['volume'], curr['vol_ma'])
            
            # RSI overbought
            rsi_overbought = curr['rsi'] > 70
            
            if has_divergence and volume_declining and rsi_overbought:
                signal = 'SHORT'
                entry_price = curr['close']
                
                # Stop beyond recent high
                recent_high = df['high'].iloc[-10:].max()
                stop_loss = recent_high + (curr['atr'] * 0.5)
                
                # Target: VWAP (mean reversion target)
                take_profit = curr['vwap']
                
                # Ensure minimum 2R
                sl_distance = stop_loss - entry_price
                min_tp = entry_price - (sl_distance * self.MIN_RR_RATIO)
                take_profit = min(take_profit, min_tp)
                
                return signal, entry_price, stop_loss, take_profit
        
        return 'NONE', 0, 0, 0
