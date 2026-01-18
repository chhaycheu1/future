"""
ScalpingStrategy V2
====================
An optimized version of ScalpingStrategy based on backtest data analysis.

Key Optimizations (learned from 105 backtest trades):
1. Stricter RSI thresholds (52+ for LONG, 48- for SHORT)
2. Tighter 1.2R take profit (winning trades close faster)
"""
import pandas as pd
from ..utils.indicators import calculate_indicators

class ScalpingStrategyV2:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        
        # Stricter RSI thresholds
        self.MIN_RSI_LONG = 52  # Stronger bullish momentum required
        self.MAX_RSI_SHORT = 48  # Stronger bearish momentum required
        
        # Tighter take profit
        self.TP_RR_OVERRIDE = 1.2

    def analyze(self, df: pd.DataFrame):
        """
        Analyzes the latest candle data with optimized logic.
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
        
        signal = 'NONE'
        
        # ===== LONG Condition (Optimized) =====
        if (
            last_row['close'] > last_row['ema_trend'] and  # Trend Up
            last_row['close'] > last_row['vwap'] and       # Above VWAP
            last_row['ema_fast'] > last_row['ema_slow'] and  # Fast EMA > Slow EMA
            last_row['rsi'] > self.MIN_RSI_LONG and        # Stronger bullish momentum
            last_row['volume'] > last_row['vol_ma']        # Volume confirmation
        ):
            # Entry Triggers
            cross_up = (prev_row['ema_fast'] <= prev_row['ema_slow']) and (last_row['ema_fast'] > last_row['ema_slow'])
            price_cross_up = (prev_row['close'] <= prev_row['ema_fast']) and (last_row['close'] > last_row['ema_fast'])
            
            if cross_up or price_cross_up:
                signal = 'LONG'

        # ===== SHORT Condition (Optimized) =====
        if signal == 'NONE':
            if (
                last_row['close'] < last_row['ema_trend'] and  # Trend Down
                last_row['close'] < last_row['vwap'] and       # Below VWAP
                last_row['ema_fast'] < last_row['ema_slow'] and  # Fast EMA < Slow EMA
                last_row['rsi'] < self.MAX_RSI_SHORT and       # Stronger bearish momentum
                last_row['volume'] > last_row['vol_ma']        # Volume confirmation
            ):
                cross_down = (prev_row['ema_fast'] >= prev_row['ema_slow']) and (last_row['ema_fast'] < last_row['ema_slow'])
                price_cross_down = (prev_row['close'] >= prev_row['ema_fast']) and (last_row['close'] < last_row['ema_fast'])
                
                if cross_down or price_cross_down:
                    signal = 'SHORT'

        # ===== CALCULATE RISK PARAMETERS =====
        if signal != 'NONE':
            atr = last_row['atr']
            entry_price = last_row['close']
            
            sl_dist = atr * self.risk_manager.sl_multiplier
            tp_rr = self.TP_RR_OVERRIDE
            
            if signal == 'LONG':
                stop_loss = entry_price - sl_dist
                take_profit = entry_price + (sl_dist * tp_rr)
            else:
                stop_loss = entry_price + sl_dist
                take_profit = entry_price - (sl_dist * tp_rr)

            return signal, entry_price, stop_loss, take_profit

        return 'NONE', 0, 0, 0
