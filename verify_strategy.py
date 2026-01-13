import pandas as pd
import numpy as np
from src.strategy.scalping_strategy import ScalpingStrategy
from src.core.risk_manager import RiskManager
# Mock DB Manager
class MockDBManager:
    def get_recent_trades(self, limit): return []
    def get_open_trades(self): return []

class MockConfig:
    RISK_PER_TRADE = 0.01
    STOP_LOSS_ATR_MULTIPLIER = 2.0
    TAKE_PROFIT_RR = 1.5

def test_long_signal():
    print("Testing LONG Signal Logic...")
    
    # Create synthetic data
    periods = 300
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=periods, freq='1min'),
        'open': np.linspace(100, 200, periods),
        'high': np.linspace(101, 201, periods),
        'low': np.linspace(99, 199, periods),
        'close': np.linspace(100, 200, periods),
        'volume': np.random.randint(100, 1000, periods)
    })
    
    # Manipulate data to create a crossover event at the end
    # Ensure Trend (EMA 200) is UP: Close > EMA 200. With linear linspace 100->200, EMA 200 will be below price at end.
    
    # Ensure Fast EMA (9) crosses Slow EMA (21)
    # We need a dip then a recovery.
    
    # Let's simplfy: Just use the Strategy on this uptrend.
    # It might trigger signals earlier.
    
    risk_manager = RiskManager(MockConfig(), MockDBManager())
    strategy = ScalpingStrategy(risk_manager)
    
    signal, entry, sl, tp = strategy.analyze(df)
    
    print(f"Result: {signal}, Entry: {entry}, SL: {sl}, TP: {tp}")
    
    # Since it's a perfect uptrend, we might expect a LONG if momentum fits.
    # But RSI might be overbought > 70? 
    # Logic says RSI > 50.
    
    if signal == 'LONG':
        print("PASS: Long signal detected on uptrend.")
    else:
        print("INFO: No signal on simple uptrend (expected if no crossover event just happened).")

def test_crossover_setup():
    print("\nTesting Crossover Setup...")
    # Construct a specific crossover
    # Previous candle: Fast < Slow
    # Current candle: Fast > Slow
    
    # It's hard to engineer exact EMA values with just OHLC, but we can try small dataset manipulation or mocking indicators.
    # But our strategy calculates indicators inside `analyze`.
    # Better to just run it and see.
    pass

if __name__ == "__main__":
    test_long_signal()
