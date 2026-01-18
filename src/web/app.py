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

# Custom Filters
from datetime import timedelta

@app.template_filter('gmt7')
def gmt7_filter(dt):
    if not dt:
        return ""
    # Add 7 hours to UTC time
    return (dt + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')

@app.template_filter('money')
def money_filter(value):
    if value is None:
        return "-"
    return f"{float(value):.2f}"

@app.route('/')
def dashboard():
    state = db_manager.get_bot_state()
    
    # Fetch LIVE positions from Binance instead of database
    live_positions = []
    try:
        exchange = BinanceClient(
            Config.BINANCE_API_KEY, 
            Config.BINANCE_API_SECRET, 
            testnet=getattr(Config, 'TESTNET', False)
        )
        live_positions = exchange.get_all_positions()
    except Exception as e:
        print(f"Error fetching live positions: {e}")
    
    recent_trades = db_manager.get_recent_trades(limit=10)
    
    # Calculate some stats
    total_trades = Trade.query.filter(Trade.status == 'CLOSED').count()
    winning_trades = Trade.query.filter(Trade.pnl > 0).count()
    win_rate = (winning_trades / total_trades *100) if total_trades > 0 else 0
    total_pnl = sum([t.pnl for t in Trade.query.filter(Trade.status == 'CLOSED').all() if t.pnl])
    
    # PER-STRATEGY STATS
    strategy_stats = {}
    for strategy_name in ["ScalpingStrategy", "SmartScalpingStrategy", "TrendPullbackStrategy", "RangeSweepStrategy"]:
        strategy_trades = Trade.query.filter(Trade.status == 'CLOSED', Trade.strategy == strategy_name).all()
        if strategy_trades:
            strategy_total = len(strategy_trades)
            strategy_wins = sum(1 for t in strategy_trades if t.pnl and t.pnl > 0)
            strategy_pnl = sum([t.pnl for t in strategy_trades if t.pnl])
            strategy_win_rate = (strategy_wins / strategy_total * 100) if strategy_total > 0 else 0
            strategy_stats[strategy_name] = {
                'total_trades': strategy_total,
                'win_rate': f"{strategy_win_rate:.2f}",
                'net_pnl': f"{strategy_pnl:.2f}"
            }
        else:
            strategy_stats[strategy_name] = {
                'total_trades': 0,
                'win_rate': "0.00",
                'net_pnl': "0.00"
            }
    
    # Fetch wallet balance
    wallet_balance = 0.0
    try:
        wallet_balance, _ = exchange.get_account_balance('USDT')
    except Exception as e:
        print(f"Error fetching wallet balance: {e}")
    
    # Current settings
    current_leverage = getattr(Config, 'LEVERAGE', 5)
    position_size_usdt = getattr(Config, 'POSITION_SIZE_USDT', 100)
    
    # Configuration data
    strategy_name = "Scalping Strategy"  # This could be dynamic if you have multiple strategies
    timeframe = getattr(Config, 'TIMEFRAME', '1m')
    trading_symbols = getattr(Config, 'SYMBOLS', [Config.SYMBOL])

    return render_template('dashboard.html', 
                           state=state, 
                           active_trades=live_positions,  # Now using live Binance positions
                           recent_trades=recent_trades,
                           win_rate=f"{win_rate:.2f}",
                           total_pnl=f"{total_pnl:.2f}",
                           total_trades=total_trades,
                           wallet_balance=f"{wallet_balance:.2f}",
                           current_leverage=current_leverage,
                           position_size_usdt=position_size_usdt,
                           strategy_name=strategy_name,
                           timeframe=timeframe,
                           trading_symbols=trading_symbols,
                           strategy_stats=strategy_stats)

@app.route('/history')
def history():
    trades = db_manager.get_recent_trades(limit=500)
    return render_template('history.html', trades=trades)

@app.route('/api/status', methods=['GET'])
def get_status():
    state = db_manager.get_bot_state()
    return jsonify(state.to_dict() if state else {})

@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    """Get real-time dashboard data for auto-refresh."""
    try:
        # Initialize exchange client
        exchange = BinanceClient(
            Config.BINANCE_API_KEY, 
            Config.BINANCE_API_SECRET, 
            testnet=getattr(Config, 'TESTNET', False)
        )
        
        # Fetch LIVE positions from Binance (not from database)
        live_positions = exchange.get_all_positions()
        
        # Fetch recent closed trades from database
        recent_trades = db_manager.get_recent_trades(limit=10)
        
        # Calculate stats
        total_trades = Trade.query.filter(Trade.status == 'CLOSED').count()
        winning_trades = Trade.query.filter(Trade.pnl > 0).count()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum([t.pnl for t in Trade.query.filter(Trade.status == 'CLOSED').all() if t.pnl])
        
        # Fetch wallet balance
        wallet_balance = 0.0
        try:
            wallet_balance, _ = exchange.get_account_balance('USDT')
        except Exception as e:
            print(f"Error fetching wallet balance: {e}")
        
        # Format trades for JSON
        from datetime import timedelta
        
        # Format live positions from Binance
        active_trades_data = [{
            'symbol': p['symbol'],
            'side': p['side'],
            'entry_price': p['entry_price'],
            'quantity': p['amount'],
            'leverage': p['leverage'],
            'notional': p['notional'],  # Position size in USDT
            'unrealized_pnl': p['unrealized_pnl'],
            'liquidation_price': p['liquidation_price']
        } for p in live_positions]
        
        recent_trades_data = [{
            'symbol': t.symbol,
            'side': t.side,
            'status': t.status,
            'position_size': float(t.entry_price * t.quantity) if (t.entry_price and t.quantity) else 0,
            'pnl': float(t.pnl) if t.pnl else 0,
            'entry_time': (t.entry_time + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') if t.entry_time else '',
            'exit_time': (t.exit_time + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S') if t.exit_time else '-'
        } for t in recent_trades]
        
        return jsonify({
            'status': 'success',
            'data': {
                'wallet_balance': f"{wallet_balance:.2f}",
                'total_pnl': f"{total_pnl:.2f}",
                'win_rate': f"{win_rate:.2f}",
                'total_trades': total_trades,
                'active_trades': active_trades_data,
                'recent_trades': recent_trades_data
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


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

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/api/reports_data')
def get_reports_data():
    try:
        strategy_filter = request.args.get('strategy', 'all')
        
        # Base query
        query = Trade.query
        
        # Apply filter
        if strategy_filter != 'all':
            query = query.filter(Trade.strategy == strategy_filter)
            
        trades = query.all()
        
        if not trades:
            return jsonify({
                'status': 'success',
                'data': {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'by_side': [],
                    'by_symbol': [],
                    'by_strategy': []
                }
            })

        # --- Aggregations ---
        
        # Overall
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl and t.pnl > 0)
        total_pnl = sum(t.pnl for t in trades if t.pnl)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Helper for grouping
        def get_stats(group_key_func):
            stats = {}
            for t in trades:
                key = group_key_func(t)
                if key not in stats:
                    stats[key] = {'count': 0, 'pnl': 0.0, 'wins': 0}
                
                stats[key]['count'] += 1
                if t.pnl:
                    stats[key]['pnl'] += t.pnl
                    if t.pnl > 0:
                        stats[key]['wins'] += 1
            
            result = []
            for key, val in stats.items():
                wr = (val['wins'] / val['count'] * 100) if val['count'] > 0 else 0
                result.append({
                    'symbol': key if group_key_func == lambda x: x.symbol else None,
                    'side': key if group_key_func == lambda x: x.side else None,
                    'strategy': key if group_key_func == lambda x: x.strategy else None,
                    'count': val['count'],
                    'pnl': val['pnl'],
                    'win_rate': round(wr, 2)
                })
            return result

        # By Side
        by_side = get_stats(lambda t: t.side)
        
        # By Symbol
        by_symbol = get_stats(lambda t: t.symbol)
        
        # By Strategy
        by_strategy = get_stats(lambda t: t.strategy)
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'by_side': by_side,
                'by_symbol': by_symbol,
                'by_strategy': by_strategy
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    run_server()
