import os
import pandas as pd
from datetime import datetime, timedelta
from src.exchange.binance_client import BinanceClient
from config.settings import Config
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def fetch_and_analyze():
    print("Connecting to Binance...")
    client = BinanceClient(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET'),
        testnet=os.getenv('TESTNET', 'True').lower() == 'true'
    )
    
    symbols = getattr(Config, 'SYMBOLS', ['ETHUSDT'])
    all_trades = []
    
    for symbol in symbols:
        print(f"Fetching trades for {symbol}...")
        try:
            # Fetch recent trades (last 30 days)
            trades = client.client.futures_account_trades(symbol=symbol, limit=1000)
            if trades:
                for t in trades:
                    t['symbol'] = symbol
                all_trades.extend(trades)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

    if not all_trades:
        print("No trades found on Binance.")
        return

    df = pd.DataFrame(all_trades)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df['realizedPnl'] = pd.to_numeric(df['realizedPnl'])
    df['qty'] = pd.to_numeric(df['qty'])
    df['price'] = pd.to_numeric(df['price'])
    df['commission'] = pd.to_numeric(df['commission'])
    
    # Filter only trades with PnL (closes) or commission?
    # realizedPnl is only non-zero on CLOSE or funding fee.
    # We want to identify closed trades.
    
    closed_trades = df[df['realizedPnl'] != 0].copy()
    
    # Filter out Funding Fees (usually small PnL with no qty or specific type?)
    # Binance futures trades include funding fees as realiziedPnl with commissionAsset usually?
    # Actually, Realized PnL is only for REDUCE_ONLY or CLOSE?
    # Let's simple filter by realizedPnl != 0
    
    print("\n--- PERFORMANCE SUMMARY ---")
    total_pnl = df['realizedPnl'].sum()
    total_commission = df['commission'].sum()
    net_pnl = total_pnl - total_commission
    
    print(f"Total Realized PnL: {total_pnl:.4f} USDT")
    print(f"Total Commission:   {total_commission:.4f} USDT")
    print(f"Net PnL:            {net_pnl:.4f} USDT")
    
    # Win Rate (approximate based on PnL > 0)
    # Note: A single 'trade' in Binance API is a fill. A position close might be multiple fills.
    # This is an approximation.
    winning_fills = len(closed_trades[closed_trades['realizedPnl'] > 0])
    losing_fills = len(closed_trades[closed_trades['realizedPnl'] < 0])
    total_fills = winning_fills + losing_fills
    
    if total_fills > 0:
        win_rate = (winning_fills / total_fills) * 100
        print(f"Win Rate (Fills):   {win_rate:.2f}% ({winning_fills}W / {losing_fills}L)")
    else:
        print("No PnL generating trades found.")
        
    print("\n--- CSV DATA (COPY BELOW) ---")
    print(df.to_csv(index=False))
    print("--- END CSV DATA ---")

if __name__ == "__main__":
    fetch_and_analyze()
