import pandas as pd
import pandas_ta as ta

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates technical indicators for the strategy.
    
    Required Indicators:
    - EMA (Fast & Slow): Trend identification.
    - VWAP: Institutional entry level and trend confirmation.
    - RSI: Momentum (14 periods).
    - Volume MA: Volume confirmation.
    """
    if df.empty:
        return df

    # Ensure typical price is available for VWAP (H+L+C)/3 usually handled by pandas_ta but let's check
    # pandas-ta 'vwap' requires 'high', 'low', 'close', 'volume' columns which we have.
    
    # EMA
    df['ema_fast'] = ta.ema(df['close'], length=9)
    df['ema_slow'] = ta.ema(df['close'], length=21)
    df['ema_trend'] = ta.ema(df['close'], length=200) # Higher timeframe trend filter usually, but acceptable on 1m for major trend
    
    # VWAP
    # VWAP is intraday. pandas-ta vwap might accumulate indefinitely if not reset. 
    # For crypto custom vwap implementation or rolling vwap might be needed if using continuous streams.
    # However, 'ta.vwap' usually calculates based on the index (time) if provided or just cumulative.
    # We will use standard pandas-ta vwap. It expects a datetime index.
    if not isinstance(df.index, pd.DatetimeIndex):
         df.set_index('timestamp', inplace=True)
         
    df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
    
    # RSI
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    # Volume MA
    df['vol_ma'] = ta.sma(df['volume'], length=20)
    
    # ATR for stop loss
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    return df
