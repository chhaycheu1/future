import pandas as pd
import numpy as np
from src.utils.indicators import calculate_indicators

def test_indicators():
    print("Verifying Indicators Calculation...")
    
    periods = 100
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=periods, freq='1min'),
        'high': np.random.rand(periods) * 10 + 100,
        'low': np.random.rand(periods) * 10 + 90,
        'close': np.random.rand(periods) * 10 + 95,
        'volume': np.random.randint(100, 1000, periods)
    })
    
    df = calculate_indicators(df)
    
    required_columns = ['ema_fast', 'ema_slow', 'ema_trend', 'vwap', 'rsi', 'vol_ma', 'atr']
    missing = [col for col in required_columns if col not in df.columns]
    
    if not missing:
        print("PASS: All indicators present.")
    else:
        print(f"FAIL: Missing columns: {missing}")

    # Check for NaNs (normal at start, but should be filled later)
    if df.iloc[-1][required_columns].isnull().any():
        print("WARN: Last row has NaNs in indicators.")
    else:
        print("PASS: Latest indicators are valid.")

if __name__ == "__main__":
    test_indicators()
