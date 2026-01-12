"""
Backtest Engine for the Scalping Strategy
Simulates trades on historical data and saves results to database.
"""
import pandas as pd
from datetime import datetime, timedelta
from ..utils.indicators import calculate_indicators
from ..database.models import db, Trade

class BacktestEngine:
    def __init__(self, exchange_client, config):
        self.exchange = exchange_client
        self.config = config
        self.sl_multiplier = config.STOP_LOSS_ATR_MULTIPLIER
        self.tp_rr = config.TAKE_PROFIT_RR
        self.risk_per_trade = config.RISK_PER_TRADE
        self.initial_balance = 10000  # Simulated starting balance
        
    def fetch_historical_data(self, symbol, interval, days=30):
        """Fetch historical klines for backtesting."""
        # Calculate limit based on days and interval
        interval_minutes = {
            '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '1d': 1440
        }
        minutes_per_day = 1440
        candles_per_day = minutes_per_day // interval_minutes.get(interval, 1)
        limit = min(candles_per_day * days, 1500)  # Binance max is 1500
        
        df = self.exchange.get_historical_klines(symbol, interval, limit=limit)
        return df
    
    def run_backtest(self, symbol, interval='1m', days=30):
        """
        Run backtest on historical data.
        Returns list of simulated trades.
        """
        print(f"Starting backtest for {symbol} on {interval} for {days} days...")
        
        # Fetch data
        df = self.fetch_historical_data(symbol, interval, days)
        if df.empty or len(df) < 205:
            print(f"Not enough data for backtest. Got {len(df)} candles.")
            return []
        
        # Calculate indicators for full dataset
        df = calculate_indicators(df)
        
        trades = []
        balance = self.initial_balance
        position = None  # Current open position
        
        # Iterate through candles (start after indicator warmup)
        for i in range(205, len(df)):
            current_candle = df.iloc[i]
            prev_candle = df.iloc[i-1]
            current_price = current_candle['close']
            current_time = current_candle.name if isinstance(df.index, pd.DatetimeIndex) else df.iloc[i].get('timestamp', datetime.now())
            
            # Check if we have open position - manage exits first
            if position:
                should_close = False
                exit_reason = ""
                
                if position['side'] == 'LONG':
                    if current_candle['low'] <= position['stop_loss']:
                        should_close = True
                        exit_reason = "SL Hit"
                        exit_price = position['stop_loss']
                    elif current_candle['high'] >= position['take_profit']:
                        should_close = True
                        exit_reason = "TP Hit"
                        exit_price = position['take_profit']
                else:  # SHORT
                    if current_candle['high'] >= position['stop_loss']:
                        should_close = True
                        exit_reason = "SL Hit"
                        exit_price = position['stop_loss']
                    elif current_candle['low'] <= position['take_profit']:
                        should_close = True
                        exit_reason = "TP Hit"
                        exit_price = position['take_profit']
                
                if should_close:
                    # Calculate PnL
                    if position['side'] == 'LONG':
                        pnl = (exit_price - position['entry_price']) * position['quantity']
                    else:
                        pnl = (position['entry_price'] - exit_price) * position['quantity']
                    
                    balance += pnl
                    
                    # Record trade
                    trade = {
                        'symbol': symbol,
                        'side': position['side'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'stop_loss': position['stop_loss'],
                        'take_profit': position['take_profit'],
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'entry_time': position['entry_time'],
                        'exit_time': current_time,
                        'exit_reason': exit_reason,
                        'strategy': 'Backtest-Scalping'
                    }
                    trades.append(trade)
                    position = None
                    continue
            
            # Check for new entry signals (only if no position)
            if position is None:
                signal = self._check_signal(current_candle, prev_candle)
                
                if signal != 'NONE':
                    entry_price = current_price
                    atr = current_candle['atr']
                    sl_dist = atr * self.sl_multiplier
                    
                    if signal == 'LONG':
                        stop_loss = entry_price - sl_dist
                        take_profit = entry_price + (sl_dist * self.tp_rr)
                    else:
                        stop_loss = entry_price + sl_dist
                        take_profit = entry_price - (sl_dist * self.tp_rr)
                    
                    # Calculate position size
                    risk_amount = balance * self.risk_per_trade
                    price_diff = abs(entry_price - stop_loss)
                    quantity = risk_amount / price_diff if price_diff > 0 else 0
                    
                    if quantity > 0:
                        position = {
                            'side': signal,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'quantity': quantity,
                            'entry_time': current_time
                        }
        
        # Close any remaining open position at last price
        if position:
            last_price = df.iloc[-1]['close']
            last_time = df.iloc[-1].name if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
            
            if position['side'] == 'LONG':
                pnl = (last_price - position['entry_price']) * position['quantity']
            else:
                pnl = (position['entry_price'] - last_price) * position['quantity']
            
            balance += pnl
            trades.append({
                'symbol': symbol,
                'side': position['side'],
                'entry_price': position['entry_price'],
                'exit_price': last_price,
                'stop_loss': position['stop_loss'],
                'take_profit': position['take_profit'],
                'quantity': position['quantity'],
                'pnl': pnl,
                'entry_time': position['entry_time'],
                'exit_time': last_time,
                'exit_reason': 'End of Backtest',
                'strategy': 'Backtest-Scalping'
            })
        
        print(f"Backtest complete. {len(trades)} trades executed.")
        return trades, balance
    
    def _check_signal(self, current, prev):
        """Check for entry signals based on strategy."""
        # LONG Condition
        if (
            current['close'] > current['ema_trend'] and
            current['close'] > current['vwap'] and
            current['ema_fast'] > current['ema_slow'] and
            current['rsi'] > 50 and
            current['volume'] > current['vol_ma']
        ):
            cross_up = (prev['ema_fast'] <= prev['ema_slow']) and (current['ema_fast'] > current['ema_slow'])
            price_cross_up = (prev['close'] <= prev['ema_fast']) and (current['close'] > current['ema_fast'])
            if cross_up or price_cross_up:
                return 'LONG'
        
        # SHORT Condition
        elif (
            current['close'] < current['ema_trend'] and
            current['close'] < current['vwap'] and
            current['ema_fast'] < current['ema_slow'] and
            current['rsi'] < 50 and
            current['volume'] > current['vol_ma']
        ):
            cross_down = (prev['ema_fast'] >= prev['ema_slow']) and (current['ema_fast'] < current['ema_slow'])
            price_cross_down = (prev['close'] >= prev['ema_fast']) and (current['close'] < current['ema_fast'])
            if cross_down or price_cross_down:
                return 'SHORT'
        
        return 'NONE'
    
    def save_to_database(self, trades):
        """Save backtest trades to database."""
        saved_count = 0
        for t in trades:
            trade = Trade(
                symbol=t['symbol'],
                side=t['side'],
                entry_price=t['entry_price'],
                exit_price=t['exit_price'],
                stop_loss=t['stop_loss'],
                take_profit=t['take_profit'],
                quantity=t['quantity'],
                pnl=t['pnl'],
                status='CLOSED',
                entry_time=t['entry_time'] if isinstance(t['entry_time'], datetime) else datetime.now(),
                exit_time=t['exit_time'] if isinstance(t['exit_time'], datetime) else datetime.now(),
                strategy=t['strategy']
            )
            db.session.add(trade)
            saved_count += 1
        
        db.session.commit()
        print(f"Saved {saved_count} trades to database.")
        return saved_count
