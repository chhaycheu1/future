#!/usr/bin/env python3
"""
Export all trade data from the production database for analysis.
Run this on the server:
  cd /var/www/trading-bot
  source venv/bin/activate
  python export_trades.py > trades_export.json
"""

from src.database.models import Trade, db
from src.web.app import app
import json
from datetime import datetime

def export_trades():
    with app.app_context():
        # Get all closed trades
        trades = Trade.query.filter(Trade.status == 'CLOSED').order_by(Trade.entry_time).all()
        
        trade_data = []
        for t in trades:
            trade_data.append({
                'id': t.id,
                'symbol': t.symbol,
                'side': t.side,
                'strategy': t.strategy,
                'entry_price': float(t.entry_price) if t.entry_price else 0,
                'exit_price': float(t.exit_price) if t.exit_price else 0,
                'quantity': float(t.quantity) if t.quantity else 0,
                'pnl': float(t.pnl) if t.pnl else 0,
                'entry_time': t.entry_time.isoformat() if t.entry_time else None,
                'exit_time': t.exit_time.isoformat() if t.exit_time else None,
                'stop_loss': float(t.stop_loss) if t.stop_loss else 0,
                'take_profit': float(t.take_profit) if t.take_profit else 0
            })
        
        result = {
            'export_time': datetime.now().isoformat(),
            'total_trades': len(trades),
            'trades': trade_data
        }
        
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    export_trades()
