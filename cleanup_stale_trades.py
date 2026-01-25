"""
Cleanup Script: Close stale OPEN trades in database
This script marks all OPEN trades as CLOSED if they don't exist on Binance
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import db, Trade
from src.exchange.binance_client import BinanceClient
from src.web.app import app
from config.settings import Config

def cleanup_stale_trades():
    """Close all OPEN trades in database that don't exist on Binance"""
    
    with app.app_context():
        # Get all open trades from database
        open_trades = Trade.query.filter(Trade.status == 'OPEN').all()
        
        if not open_trades:
            print("No open trades found in database.")
            return
        
        print(f"Found {len(open_trades)} OPEN trades in database.")
        
        # Initialize Binance client
        try:
            exchange = BinanceClient(
                Config.BINANCE_API_KEY,
                Config.BINANCE_API_SECRET,
                testnet=getattr(Config, 'TESTNET', False)
            )
            
            # Get actual positions from Binance
            live_positions = exchange.get_all_positions()
            live_symbols = {p['symbol'] for p in live_positions if p['amount'] != 0}
            
            print(f"Found {len(live_symbols)} actual open positions on Binance: {live_symbols}")
            
        except Exception as e:
            print(f"Error connecting to Binance: {e}")
            print("Proceeding with manual cleanup...")
            live_symbols = set()
        
        # Close stale trades
        closed_count = 0
        for trade in open_trades:
            if trade.symbol not in live_symbols:
                print(f"Closing stale trade: {trade.symbol} {trade.side} (Entry: {trade.entry_price})")
                
                # Mark as closed with current time and 0 PnL (unknown actual result)
                trade.status = 'CLOSED'
                trade.exit_time = datetime.utcnow()
                
                # Set exit price to entry price (assume breakeven for unknown trades)
                trade.exit_price = trade.entry_price
                
                # Set PnL to 0 if not already set
                if trade.pnl is None:
                    trade.pnl = 0.0
                
                closed_count += 1
        
        # Commit changes
        db.session.commit()
        print(f"\n✅ Closed {closed_count} stale trades.")
        
        # Show remaining open trades
        remaining = Trade.query.filter(Trade.status == 'OPEN').count()
        if remaining > 0:
            print(f"⚠️  {remaining} trades remain OPEN (matching Binance positions)")
        else:
            print("✅ All stale trades cleaned up!")

if __name__ == "__main__":
    cleanup_stale_trades()
