from .models import db, Trade, BotState
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

class DBManager:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        db.init_app(app)
        with app.app_context():
            db.create_all()
            # Initialize bot state if not exists
            if not BotState.query.first():
                initial_state = BotState(is_running=False, is_dry_run=True)
                db.session.add(initial_state)
                db.session.commit()

    def add_trade(self, symbol, side, entry_price, quantity, stop_loss=None, take_profit=None, strategy="Scalping"):
        try:
            trade = Trade(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=strategy,
                entry_time=datetime.utcnow(),
                status='OPEN'
            )
            db.session.add(trade)
            db.session.commit()
            return trade
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error adding trade: {e}")
            return None

    def close_trade(self, trade_id, exit_price, pnl):
        try:
            trade = Trade.query.get(trade_id)
            if trade:
                trade.exit_price = exit_price
                trade.pnl = pnl
                trade.status = 'CLOSED'
                trade.exit_time = datetime.utcnow()
                db.session.commit()
                return trade
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error closing trade: {e}")
            return None

    def get_open_trades(self):
        return Trade.query.filter_by(status='OPEN').all()

    def get_recent_trades(self, limit=50):
        return Trade.query.order_by(Trade.entry_time.desc()).limit(limit).all()

    def get_bot_state(self):
        return BotState.query.first()

    def update_bot_state(self, is_running=None, is_dry_run=None):
        try:
            state = BotState.query.first()
            if state:
                if is_running is not None:
                    state.is_running = is_running
                if is_dry_run is not None:
                    state.is_dry_run = is_dry_run
                state.last_update = datetime.utcnow()
                db.session.commit()
                return state
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating bot state: {e}")
            return None
