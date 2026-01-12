import pandas as pd
import numpy as np

def ema(series: pd.Series, length: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=length, adjust=False).mean()

def sma(series: pd.Series, length: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=length).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate Volume Weighted Average Price."""
    typical_price = (high + low + close) / 3
    cumulative_tp_vol = (typical_price * volume).cumsum()
    cumulative_vol = volume.cumsum()
    return cumulative_tp_vol / cumulative_vol

def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.ewm(span=length, adjust=False).mean()

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

    # EMA
    df['ema_fast'] = ema(df['close'], length=9)
    df['ema_slow'] = ema(df['close'], length=21)
    df['ema_trend'] = ema(df['close'], length=200)
    
    # VWAP - Set datetime index if needed
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
         
    df['vwap'] = vwap(df['high'], df['low'], df['close'], df['volume'])
    
    # RSI
    df['rsi'] = rsi(df['close'], length=14)
    
    # Volume MA
    df['vol_ma'] = sma(df['volume'], length=20)
    
    # ATR for stop loss
    df['atr'] = atr(df['high'], df['low'], df['close'], length=14)

    return df
