import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Binance API
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    TESTNET = os.getenv("TESTNET", "True").lower() in ("true", "1", "t")
    
    # Trading Settings
    SYMBOL = os.getenv("SYMBOL", "BTCUSDT")  # Default Pair
    TIMEFRAME = os.getenv("TIMEFRAME", "1m") # 1m, 3m, 5m etc.
    LEVERAGE = int(os.getenv("LEVERAGE", "5"))
    
    # Risk Management
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.01")) # 1%
    STOP_LOSS_ATR_MULTIPLIER = float(os.getenv("STOP_LOSS_ATR_MULTIPLIER", "2.0"))
    TAKE_PROFIT_RR = float(os.getenv("TAKE_PROFIT_RR", "1.5"))
    
    # Bot State
    DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("true", "1", "t")
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
