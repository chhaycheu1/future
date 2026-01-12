from flask import Flask, render_template, jsonify, request
from ..database.db_manager import DBManager
from ..database.models import Trade, BotState, db
from ..core.backtest import BacktestEngine
from ..exchange.binance_client import BinanceClient
from config.settings import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize DB
db_manager = DBManager(app)

@app.route('/')
def dashboard():
    state = db_manager.get_bot_state()
    active_trades = db_manager.get_open_trades()
    recent_trades = db_manager.get_recent_trades(limit=10)
    
    # Calculate some stats
    total_trades = Trade.query.filter(Trade.status == 'CLOSED').count()
    winning_trades = Trade.query.filter(Trade.pnl > 0).count()
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum([t.pnl for t in Trade.query.filter(Trade.status == 'CLOSED').all() if t.pnl])

    return render_template('dashboard.html', 
                           state=state, 
                           active_trades=active_trades, 
                           recent_trades=recent_trades,
                           win_rate=f"{win_rate:.2f}",
                           total_pnl=f"{total_pnl:.2f}",
                           total_trades=total_trades)

@app.route('/history')
def history():
    trades = db_manager.get_recent_trades(limit=500)
    return render_template('history.html', trades=trades)

@app.route('/api/status', methods=['GET'])
def get_status():
    state = db_manager.get_bot_state()
    return jsonify(state.to_dict() if state else {})

@app.route('/api/toggle_bot', methods=['POST'])
def toggle_bot():
    state = db_manager.get_bot_state()
    if state:
        new_status = not state.is_running
        db_manager.update_bot_state(is_running=new_status)
        return jsonify({'status': 'success', 'is_running': new_status})
    return jsonify({'status': 'error', 'message': 'Bot state not found'}), 404

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run a backtest on historical data."""
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol', Config.SYMBOL)
        interval = data.get('interval', Config.TIMEFRAME)
        days = data.get('days', 30)
        
        # Initialize exchange client for testnet
        exchange = BinanceClient(
            Config.BINANCE_API_KEY, 
            Config.BINANCE_API_SECRET, 
            testnet=Config.TESTNET
        )
        
        # Run backtest
        engine = BacktestEngine(exchange, Config)
        trades, final_balance = engine.run_backtest(symbol, interval, days)
        
        if not trades:
            return jsonify({
                'status': 'error',
                'message': 'No trades generated. Not enough data or no signals found.'
            }), 400
        
        # Save to database
        saved = engine.save_to_database(trades)
        
        # Calculate stats
        winning = sum(1 for t in trades if t['pnl'] > 0)
        losing = sum(1 for t in trades if t['pnl'] <= 0)
        total_pnl = sum(t['pnl'] for t in trades)
        win_rate = (winning / len(trades) * 100) if trades else 0
        
        return jsonify({
            'status': 'success',
            'message': f'Backtest completed. {saved} trades saved.',
            'stats': {
                'total_trades': len(trades),
                'winning_trades': winning,
                'losing_trades': losing,
                'win_rate': f"{win_rate:.2f}%",
                'total_pnl': f"${total_pnl:.2f}",
                'initial_balance': 10000,
                'final_balance': f"${final_balance:.2f}",
                'return_pct': f"{((final_balance - 10000) / 10000 * 100):.2f}%"
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """Clear all trade history from database."""
    try:
        Trade.query.delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Trade history cleared.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    run_server()
