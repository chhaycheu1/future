import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Binance API
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    TESTNET = os.getenv("TESTNET", "True").lower() in ("true", "1", "t")
    
    # Trading Settings
    SYMBOL = os.getenv("SYMBOL", "BTCUSDT")  # Primary pair (legacy)
    
    # Multiple Trading Pairs (20+ pairs)
    SYMBOLS = [
        "BTCUSDT",   # Bitcoin
        "ETHUSDT",   # Ethereum
        "BNBUSDT",   # Binance Coin
        "SOLUSDT",   # Solana
        "XRPUSDT",   # Ripple
        "DOGEUSDT",  # Dogecoin
        "ADAUSDT",   # Cardano
        "AVAXUSDT",  # Avalanche
        "DOTUSDT",   # Polkadot
        "LINKUSDT",  # Chainlink
        "MATICUSDT", # Polygon
        "LTCUSDT",   # Litecoin
        "ATOMUSDT",  # Cosmos
        "UNIUSDT",   # Uniswap
        "ETCUSDT",   # Ethereum Classic
        "XLMUSDT",   # Stellar
        "APTUSDT",   # Aptos
        "NEARUSDT",  # Near Protocol
        "ARBUSDT",   # Arbitrum
        "OPUSDT",    # Optimism
        "FILUSDT",   # Filecoin
    ]
    
    TIMEFRAME = os.getenv("TIMEFRAME", "5m") # Increased to 5m to overcome fees
    LEVERAGE = int(os.getenv("LEVERAGE", "5"))
    
    # Risk Management
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.01")) # 1% (used if POSITION_SIZE_USDT is 0)
    POSITION_SIZE_USDT = float(os.getenv("POSITION_SIZE_USDT", "0")) # Fixed USDT amount per trade (0 = use percentage)
    STOP_LOSS_ATR_MULTIPLIER = float(os.getenv("STOP_LOSS_ATR_MULTIPLIER", "2.0"))
    TAKE_PROFIT_RR = float(os.getenv("TAKE_PROFIT_RR", "1.5"))
    TRADING_FEE_RATE = float(os.getenv("TRADING_FEE_RATE", "0.0005")) # 0.05% per side (Maker/Taker avg)
    
    # Bot State
    DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("true", "1", "t")
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
