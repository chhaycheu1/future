from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False) # LONG or SHORT
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=True)
    stop_loss = db.Column(db.Float, nullable=True)
    take_profit = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    pnl = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='OPEN') # OPEN, CLOSED
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)
    strategy = db.Column(db.String(50), nullable=True) # Name of strategy or logic used

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'pnl': self.pnl,
            'status': self.status,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None
        }

class BotState(db.Model):
    __tablename__ = 'bot_state'
    
    id = db.Column(db.Integer, primary_key=True)
    is_running = db.Column(db.Boolean, default=False)
    is_dry_run = db.Column(db.Boolean, default=True)
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active_pairs = db.Column(db.String(200), default="BTCUSDT")

    def to_dict(self):
        return {
            'is_running': self.is_running,
            'is_dry_run': self.is_dry_run,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'active_pairs': self.active_pairs
        }
