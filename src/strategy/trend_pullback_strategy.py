"""
Trend Pullback Strategy
========================
Timeframe: 5m

Rules:
1. Trend Detection: EMA 50 > EMA 200 = bullish, EMA 50 < EMA 200 = bearish
2. Pullback: Price pulls back to EMA 20 or EMA 50
3. RSI Confirmation: 40-50 (bullish) or 50-60 (bearish)
4. Candle Pattern: Bullish/bearish engulfing or strong rejection
5. Entry: On candle close
6. Stop Loss: Below pullback low (long) / Above pullback high (short)
7. Take Profit: 2R
"""
import pandas as pd
from ..utils.indicators import calculate_indicators

class TrendPullbackStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        
        # Configuration
        self.TP_RR_RATIO = 2.0
        self.PULLBACK_TOLERANCE_ATR = 0.5
        
    def _is_bullish_engulfing(self, prev, curr):
        """Check for bullish engulfing pattern."""
        return (
            prev['close'] < prev['open'] and
            curr['close'] > curr['open'] and
            curr['close'] > prev['open'] and
            curr['open'] < prev['close']
        )
    
    def _is_bearish_engulfing(self, prev, curr):
        """Check for bearish engulfing pattern."""
        return (
            prev['close'] > prev['open'] and
            curr['close'] < curr['open'] and
            curr['close'] < prev['open'] and
            curr['open'] > prev['close']
        )
    
    def _is_bullish_rejection(self, curr):
        """Check for bullish rejection (hammer-like)."""
        body = abs(curr['close'] - curr['open'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        total_range = curr['high'] - curr['low']
        
        if total_range == 0:
            return False
            
        return (
            curr['close'] > curr['open'] and
            lower_wick > body * 2 and
            upper_wick < body
        )
    
    def _is_bearish_rejection(self, curr):
        """Check for bearish rejection (shooting star-like)."""
        body = abs(curr['close'] - curr['open'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        total_range = curr['high'] - curr['low']
        
        if total_range == 0:
            return False
            
        return (
            curr['close'] < curr['open'] and
            upper_wick > body * 2 and
            lower_wick < body
        )
    
    def _price_near_ema(self, price, ema_value, atr):
        """Check if price is near EMA (within tolerance)."""
        return abs(price - ema_value) < atr * self.PULLBACK_TOLERANCE_ATR
    
    def _find_pullback_low(self, df, lookback=5):
        """Find the lowest low in recent candles."""
        return df['low'].iloc[-lookback:].min()
    
    def _find_pullback_high(self, df, lookback=5):
        """Find the highest high in recent candles."""
        return df['high'].iloc[-lookback:].max()
    
    def analyze(self, df: pd.DataFrame):
        """Analyze for Trend Pullback entry signals."""
        if len(df) < 200:
            return 'NONE', 0, 0, 0
        
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        atr = curr['atr']
        
        signal = 'NONE'
        
        # ===== BULLISH TREND PULLBACK =====
        is_bullish_trend = curr['ema_50'] > curr['ema_trend']
        
        if is_bullish_trend:
            price_near_ema20 = self._price_near_ema(curr['low'], curr['ema_20'], atr)
            price_near_ema50 = self._price_near_ema(curr['low'], curr['ema_50'], atr)
            
            if price_near_ema20 or price_near_ema50:
                rsi_ok = 40 <= curr['rsi'] <= 50
                has_bullish_pattern = (
                    self._is_bullish_engulfing(prev, curr) or
                    self._is_bullish_rejection(curr)
                )
                
                if rsi_ok and has_bullish_pattern:
                    signal = 'LONG'
        
        # ===== BEARISH TREND PULLBACK =====
        is_bearish_trend = curr['ema_50'] < curr['ema_trend']
        
        if is_bearish_trend and signal == 'NONE':
            price_near_ema20 = self._price_near_ema(curr['high'], curr['ema_20'], atr)
            price_near_ema50 = self._price_near_ema(curr['high'], curr['ema_50'], atr)
            
            if price_near_ema20 or price_near_ema50:
                rsi_ok = 50 <= curr['rsi'] <= 60
                has_bearish_pattern = (
                    self._is_bearish_engulfing(prev, curr) or
                    self._is_bearish_rejection(curr)
                )
                
                if rsi_ok and has_bearish_pattern:
                    signal = 'SHORT'
        
        # ===== CALCULATE RISK PARAMETERS =====
        if signal != 'NONE':
            entry_price = curr['close']
            
            if signal == 'LONG':
                pullback_low = self._find_pullback_low(df)
                stop_loss = pullback_low - (atr * 0.2)
                sl_distance = entry_price - stop_loss
                take_profit = entry_price + (sl_distance * self.TP_RR_RATIO)
            else:
                pullback_high = self._find_pullback_high(df)
                stop_loss = pullback_high + (atr * 0.2)
                sl_distance = stop_loss - entry_price
                take_profit = entry_price - (sl_distance * self.TP_RR_RATIO)
            
            return signal, entry_price, stop_loss, take_profit
        
        return 'NONE', 0, 0, 0
