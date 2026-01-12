import pandas as pd
from ..utils.indicators import calculate_indicators

class ScalpingStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager

    def analyze(self, df: pd.DataFrame):
        """
        Analyzes the latest candle data and returns a signal.
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
        
        # --- Strategy Logic ---
        
        # 1. Trend Filter: Price > EMA 200 (Long) / Price < EMA 200 (Short)
        # 2. Volume Check: Current Volume > Volume MA * 1.5 (Strong move)
        # 3. Momentum: RSI between 40 and 60 is chop? 
        #    User said: "Avoid chop / low-volume markets". "RSI for momentum".
        #    - Long: RSI > 50 and rising.
        #    - Short: RSI < 50 and falling.
        # 4. Entry:
        #    - Long: Price crosses above EMA 9 and EMA 9 > EMA 21
        #    - Short: Price crosses below EMA 9 and EMA 9 < EMA 21
        #    - VWAP Confluence: Price > VWAP (Long), Price < VWAP (Short)

        signal = 'NONE'
        
        # LONG Condition
        if (
            last_row['close'] > last_row['ema_trend'] and # Trend Up
            last_row['close'] > last_row['vwap'] and      # Above VWAP
            last_row['ema_fast'] > last_row['ema_slow'] and # Fast EMA > Slow EMA
            last_row['rsi'] > 50 and                   # Bullish Momentum
            last_row['volume'] > last_row['vol_ma']    # Volume confirmation
        ):
            # Check for fresh cross or breakout
            # Example: previous close was below fast ema or fast ema was below slow ema?
            # Let's simple check: if we are in this state, is it a good entry?
            # To avoid spamming, we might want to check if prev candle wasn't meeting all conditions?
            # For scalping, simple "Crossover" check is better.
            
            # Refined Entry: fast EMA crossed above slow EMA recently OR close crossed above fast EMA
            cross_up = (prev_row['ema_fast'] <= prev_row['ema_slow']) and (last_row['ema_fast'] > last_row['ema_slow'])
            price_cross_up = (prev_row['close'] <= prev_row['ema_fast']) and (last_row['close'] > last_row['ema_fast'])
            
            if cross_up or price_cross_up:
                signal = 'LONG'

        # SHORT Condition
        elif (
            last_row['close'] < last_row['ema_trend'] and # Trend Down
            last_row['close'] < last_row['vwap'] and      # Below VWAP
            last_row['ema_fast'] < last_row['ema_slow'] and # Fast EMA < Slow EMA
            last_row['rsi'] < 50 and                   # Bearish Momentum
            last_row['volume'] > last_row['vol_ma']    # Volume confirmation
        ):
            cross_down = (prev_row['ema_fast'] >= prev_row['ema_slow']) and (last_row['ema_fast'] < last_row['ema_slow'])
            price_cross_down = (prev_row['close'] >= prev_row['ema_fast']) and (last_row['close'] < last_row['ema_fast'])
            
            if cross_down or price_cross_down:
                signal = 'SHORT'

        if signal != 'NONE':
            # Calculate Risk Parameters
            atr = last_row['atr']
            entry_price = last_row['close']
            
            # Stop Loss based on ATR (Volatility)
            # Long: Entry - (ATR * Multiplier)
            # Short: Entry + (ATR * Multiplier)
            sl_dist = atr * self.risk_manager.sl_multiplier
            
            if signal == 'LONG':
                stop_loss = entry_price - sl_dist
                take_profit = entry_price + (sl_dist * self.risk_manager.tp_rr)
            else:
                stop_loss = entry_price + sl_dist
                take_profit = entry_price - (sl_dist * self.risk_manager.tp_rr)

            return signal, entry_price, stop_loss, take_profit

        return 'NONE', 0, 0, 0
