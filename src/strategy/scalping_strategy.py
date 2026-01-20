import pandas as pd
from ..utils.indicators import calculate_indicators

class ScalpingStrategy:
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        
        # DATA-DRIVEN FIXES based on 169 real trades
        # Symbol Blacklist: These 5 symbols lost $116.71 (67% of all losses)
        self.SYMBOL_BLACKLIST = [
            'FILUSDT',   # Lost -$32.35
            'OPUSDT',    # Lost -$28.48
            'XRPUSDT',   # Lost -$20.61
            'DOGEUSDT',  # Lost -$19.27
            'ETHUSDT'    # Lost -$16.00
        ]
        
        # Regime Filters
        self.MIN_ATR_PERCENTILE = 40  # Skip low volatility (bottom 40%)
        self.MIN_VOLUME_STRENGTH = 1.2  # Require strong volume

    def analyze(self, df: pd.DataFrame, symbol=None):
        """
        FIXED ScalpingStrategy based on real trading data analysis.
        
        Key Improvements:
        - Symbol blacklist (removed -$116 loss sources)
        - LONG pullback entries (was 19.61% WR, targeting 35%+)
        - 2.0x R:R (was 1.5x)
        - ATR regime filter
        - Stricter LONG requirements
        """
        if len(df) < 200:
            return 'NONE', 0, 0, 0
        
        # FIX 1: Symbol Blacklist
        if symbol and symbol in self.SYMBOL_BLACKLIST:
            return 'NONE', 0, 0, 0

        df = calculate_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # FIX 2: Market Regime Filter (ATR)
        if last_row['atr_percentile'] < self.MIN_ATR_PERCENTILE:
            return 'NONE', 0, 0, 0  # Skip low volatility
        
        # FIX 3: Volume Strength Filter
        if last_row['volume_strength'] < self.MIN_VOLUME_STRENGTH:
            return 'NONE', 0, 0, 0  # Skip weak volume
        
        signal = 'NONE'
        
        # FIX 4: IMPROVED LONG LOGIC (was 19.61% WR)
        if (
            # Basic trend filter
            last_row['close'] > last_row['ema_trend'] and
            last_row['close'] > last_row['vwap'] and
            last_row['ema_fast'] > last_row['ema_slow'] and
            last_row['volume'] > last_row['vol_ma']
        ):
            # STRICTER LONG REQUIREMENTS (data showed LONGs fail)
            # Require RSI > 55 (not just > 50)
            if last_row['rsi'] < 55:
                return 'NONE', 0, 0, 0
            
            # Require stronger EMA separation (0.2% minimum gap)
            ema_gap_pct = (last_row['ema_fast'] - last_row['ema_slow']) / last_row['ema_slow']
            if ema_gap_pct < 0.002:
                return 'NONE', 0, 0, 0
            
            # PULLBACK ENTRY LOGIC (don't chase breakouts)
            recent_high = df['high'].tail(10).max()
            pullback_pct = (recent_high - last_row['close']) / recent_high
            
            # Must have pulled back at least 0.3% from recent high
            if pullback_pct >= 0.003:
                # Check if bouncing from EMA_fast support
                price_near_ema = abs(last_row['close'] - last_row['ema_fast']) / last_row['close']
                
                if price_near_ema < 0.004:  # Within 0.4% of EMA
                    # Require volume surge on bounce
                    if last_row['volume'] > last_row['vol_ma'] * 1.3:
                        signal = 'LONG'

        # SHORT Condition (performs better - 36.44% WR vs 19.61% LONG)
        # Keep existing logic but slightly stricter
        elif (
            last_row['close'] < last_row['ema_trend'] and
            last_row['close'] < last_row['vwap'] and
            last_row['ema_fast'] < last_row['ema_slow'] and
            last_row['rsi'] < 50 and
            last_row['volume'] > last_row['vol_ma']
        ):
            # SHORT entries can be more lenient (they performed better)
            cross_down = (prev_row['ema_fast'] >= prev_row['ema_slow']) and (last_row['ema_fast'] < last_row['ema_slow'])
            price_cross_down = (prev_row['close'] >= prev_row['ema_fast']) and (last_row['close'] < last_row['ema_fast'])
            
            if cross_down or price_cross_down:
                signal = 'SHORT'

        if signal != 'NONE':
            # FIX 5: IMPROVED RISK MANAGEMENT
            atr = last_row['atr']
            entry_price = last_row['close']
            
            # Stop Loss based on ATR
            sl_dist = atr * self.risk_manager.sl_multiplier
            
            # FIX 6: INCREASE R:R TO 2.0x (was 1.5x)
            # Data showed avg loss ($3.00) > avg win ($2.88)
            tp_rr = 2.0  # Force 2:1 reward-to-risk
            
            if signal == 'LONG':
                stop_loss = entry_price - sl_dist
                take_profit = entry_price + (sl_dist * tp_rr)
            else:
                stop_loss = entry_price + sl_dist
                take_profit = entry_price - (sl_dist * tp_rr)

            return signal, entry_price, stop_loss, take_profit

        return 'NONE', 0, 0, 0
