from flask import Flask, render_template, jsonify, request
from ..database.db_manager import DBManager
from ..database.models import Trade, BotState
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

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    run_server()
