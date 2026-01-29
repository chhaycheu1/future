import pandas as pd

# Parse the trade data
data = """ScalpingStrategy,ETHUSDT,SHORT,0.23
ScalpingStrategy,ETHUSDT,SHORT,-0.01
ScalpingStrategy,DOTUSDT,SHORT,-0.97
ScalpingStrategy,ADAUSDT,SHORT,1.80
ScalpingStrategy,ATOMUSDT,SHORT,1.73
ScalpingStrategy,LTCUSDT,SHORT,4.21
ScalpingStrategy,XRPUSDT,SHORT,-2.25
ScalpingStrategy,FILUSDT,LONG,-4.08
ScalpingStrategy,LTCUSDT,SHORT,-2.80
ScalpingStrategy,OPUSDT,SHORT,-1.97
ScalpingStrategy,ATOMUSDT,LONG,2.32
ScalpingStrategy,BTCUSDT,SHORT,-1.91
ScalpingStrategy,DOGEUSDT,SHORT,-1.61
ScalpingStrategy,OPUSDT,SHORT,-1.68
ScalpingStrategy,BNBUSDT,LONG,0.97
ScalpingStrategy,ADAUSDT,SHORT,1.41
ScalpingStrategy,BTCUSDT,LONG,-1.89
ScalpingStrategy,XRPUSDT,SHORT,1.60
ScalpingStrategy,OPUSDT,SHORT,-1.68
ScalpingStrategy,LINKUSDT,SHORT,3.36
ScalpingStrategy,DOGEUSDT,SHORT,1.99
ScalpingStrategy,OPUSDT,SHORT,-2.27
ScalpingStrategy,ETCUSDT,SHORT,1.34
ScalpingStrategy,ADAUSDT,SHORT,-2.16
ScalpingStrategy,ETHUSDT,SHORT,-1.76
ScalpingStrategy,XRPUSDT,SHORT,-1.62
ScalpingStrategy,OPUSDT,SHORT,2.60
ScalpingStrategy,UNIUSDT,LONG,-2.76
ScalpingStrategy,FILUSDT,LONG,-3.12
ScalpingStrategy,ATOMUSDT,LONG,-2.31
ScalpingStrategy,XLMUSDT,SHORT,4.12
ScalpingStrategy,DOGEUSDT,SHORT,3.68
ScalpingStrategy,XRPUSDT,SHORT,1.17
ScalpingStrategy,BTCUSDT,SHORT,-1.31
ScalpingStrategy,ETHUSDT,LONG,-1.61
ScalpingStrategy,APTUSDT,SHORT,3.29
ScalpingStrategy,ETHUSDT,SHORT,-1.73
ScalpingStrategy,ETHUSDT,LONG,-2.01
ScalpingStrategy,OPUSDT,SHORT,2.93
ScalpingStrategy,ADAUSDT,SHORT,3.61
ScalpingStrategy,XRPUSDT,SHORT,2.25
ScalpingStrategy,ARBUSDT,SHORT,3.82
ScalpingStrategy,DOTUSDT,SHORT,-2.40
SmartScalpingStrategy,DOTUSDT,SHORT,-3.11
ScalpingStrategy,BTCUSDT,LONG,-1.92
ScalpingStrategy,ETHUSDT,SHORT,3.90
ScalpingStrategy,BTCUSDT,SHORT,2.68
ScalpingStrategy,LTCUSDT,LONG,-5.44
ScalpingStrategy,ATOMUSDT,LONG,-2.51
ScalpingStrategy,FILUSDT,SHORT,-10.44
ScalpingStrategy,BNBUSDT,SHORT,2.71
ScalpingStrategy,ETCUSDT,SHORT,5.50
ScalpingStrategy,ATOMUSDT,SHORT,3.35
ScalpingStrategy,APTUSDT,SHORT,-1.22
ScalpingStrategy,LINKUSDT,LONG,0.05
ScalpingStrategyV2,LINKUSDT,LONG,-0.14
ScalpingStrategy,ARBUSDT,SHORT,-3.09
ScalpingStrategyV2,ARBUSDT,SHORT,-3.09
TrendPullbackStrategy,BNBUSDT,SHORT,-0.75
ScalpingStrategy,OPUSDT,SHORT,-2.42
ScalpingStrategy,XLMUSDT,SHORT,-2.40
ScalpingStrategy,BNBUSDT,SHORT,-1.33
TrendPullbackStrategy,ETCUSDT,SHORT,1.93
ScalpingStrategy,ATOMUSDT,SHORT,-2.70
ScalpingStrategy,XLMUSDT,SHORT,1.44
ScalpingStrategy,LINKUSDT,LONG,-2.10
ScalpingStrategy,ADAUSDT,SHORT,2.81
ScalpingStrategy,XRPUSDT,SHORT,0.89
TrendPullbackStrategy,ETHUSDT,LONG,-0.21
TrendPullbackStrategy,APTUSDT,SHORT,1.62
ScalpingStrategy,ETHUSDT,LONG,-6.74
ScalpingStrategy,OPUSDT,SHORT,-2.27
ScalpingStrategy,DOTUSDT,SHORT,-2.36
ScalpingStrategy,DOGEUSDT,SHORT,-2.80
ScalpingStrategy,XLMUSDT,SHORT,3.95
ScalpingStrategy,NEARUSDT,SHORT,-4.34
ScalpingStrategy,ARBUSDT,SHORT,-3.53
ScalpingStrategy,BNBUSDT,LONG,-1.54
ScalpingStrategy,BNBUSDT,LONG,-1.71
ScalpingStrategy,LINKUSDT,LONG,-3.55
TrendPullbackStrategy,XLMUSDT,SHORT,3.42
TrendPullbackStrategy,XRPUSDT,SHORT,0.04
ScalpingStrategy,XRPUSDT,SHORT,-2.65
ScalpingStrategy,DOGEUSDT,LONG,-2.61
ScalpingStrategy,XRPUSDT,LONG,-1.81
ScalpingStrategy,DOGEUSDT,LONG,-2.39
TrendPullbackStrategy,BTCUSDT,SHORT,-1.37
TrendPullbackStrategy,ETCUSDT,SHORT,1.23
ScalpingStrategy,BTCUSDT,LONG,-3.08
ScalpingStrategy,LTCUSDT,SHORT,-2.50
ScalpingStrategy,ETCUSDT,SHORT,-3.30
ScalpingStrategy,FILUSDT,SHORT,-4.44
ScalpingStrategy,XRPUSDT,SHORT,-1.72
ScalpingStrategy,ADAUSDT,SHORT,-4.47
ScalpingStrategy,ADAUSDT,SHORT,-3.83
ScalpingStrategy,DOGEUSDT,SHORT,-2.84
RangeSweepStrategy,NEARUSDT,LONG,2.45
ScalpingStrategy,XLMUSDT,SHORT,-3.45
SmartScalpingStrategy,XLMUSDT,SHORT,-3.45
RangeSweepStrategy,FILUSDT,SHORT,-2.76
TrendPullbackStrategy,XLMUSDT,SHORT,-1.90
ScalpingStrategy,OPUSDT,LONG,-2.69
SmartScalpingStrategy,OPUSDT,LONG,-3.28
ScalpingStrategy,XLMUSDT,SHORT,-1.95
ScalpingStrategy,BNBUSDT,LONG,0.87
ScalpingStrategy,DOTUSDT,LONG,-2.58
ScalpingStrategy,ATOMUSDT,SHORT,-2.90
ScalpingStrategy,XLMUSDT,SHORT,-2.19
TrendPullbackStrategy,ADAUSDT,SHORT,-1.27
ScalpingStrategy,DOTUSDT,LONG,3.66
ScalpingStrategy,ATOMUSDT,LONG,-2.88
ScalpingStrategy,DOGEUSDT,LONG,-2.14
ScalpingStrategy,XRPUSDT,LONG,-2.13
RangeSweepStrategy,XLMUSDT,SHORT,-2.57
RangeSweepStrategy,BTCUSDT,SHORT,4.10
TrendPullbackStrategy,BNBUSDT,LONG,-1.01
TrendPullbackStrategy,ETHUSDT,LONG,-1.03
TrendPullbackStrategy,BTCUSDT,LONG,0.07
ScalpingStrategy,OPUSDT,LONG,-5.30
ScalpingStrategy,DOGEUSDT,LONG,-2.14
ScalpingStrategy,ATOMUSDT,LONG,-2.28
ScalpingStrategy,XRPUSDT,LONG,-1.69
ScalpingStrategy,XLMUSDT,SHORT,-2.60
TrendPullbackStrategy,BTCUSDT,LONG,-0.69
ScalpingStrategy,ETCUSDT,LONG,-1.95
ScalpingStrategy,DOTUSDT,LONG,1.79
ScalpingStrategy,ARBUSDT,LONG,-5.28
ScalpingStrategy,FILUSDT,LONG,-3.73
ScalpingStrategy,DOGEUSDT,SHORT,-2.00
TrendPullbackStrategy,DOTUSDT,LONG,1.34
TrendPullbackStrategy,BNBUSDT,LONG,-1.01
ScalpingStrategy,ETCUSDT,SHORT,-2.51
TrendPullbackStrategy,LTCUSDT,LONG,-1.10
ScalpingStrategy,DOGEUSDT,LONG,-2.50
ScalpingStrategy,NEARUSDT,LONG,-3.68
ScalpingStrategy,XRPUSDT,SHORT,1.87
ScalpingStrategy,APTUSDT,SHORT,-4.06
ScalpingStrategy,APTUSDT,SHORT,4.60
ScalpingStrategy,ATOMUSDT,SHORT,4.11
ScalpingStrategy,DOTUSDT,SHORT,8.07
ScalpingStrategy,LTCUSDT,SHORT,6.62
RangeSweepStrategy,XLMUSDT,LONG,7.25
ScalpingStrategy,XRPUSDT,SHORT,-14.56
ScalpingStrategy,ETCUSDT,SHORT,-5.13
ScalpingStrategy,OPUSDT,SHORT,-6.40
ScalpingStrategy,ADAUSDT,SHORT,-5.89
ScalpingStrategy,DOTUSDT,SHORT,-5.11
ScalpingStrategy,ETHUSDT,SHORT,-2.40
ScalpingStrategy,APTUSDT,SHORT,6.67
ScalpingStrategy,ETHUSDT,SHORT,-1.99
TrendPullbackStrategy,BNBUSDT,SHORT,-1.74
ScalpingStrategy,OPUSDT,SHORT,-4.05
ScalpingStrategy,ETHUSDT,SHORT,1.32
ScalpingStrategy,ATOMUSDT,SHORT,-2.82
TrendPullbackStrategy,ADAUSDT,SHORT,3.34
TrendPullbackStrategy,BNBUSDT,SHORT,-1.90
ScalpingStrategy,FILUSDT,SHORT,-3.78
ScalpingStrategy,XLMUSDT,SHORT,-4.94
ScalpingStrategy,BNBUSDT,SHORT,-1.96
ScalpingStrategy,DOGEUSDT,SHORT,-2.23
TrendPullbackStrategy,APTUSDT,SHORT,2.86
ScalpingStrategy,ETCUSDT,SHORT,-2.82
ScalpingStrategy,ARBUSDT,SHORT,-3.12
ScalpingStrategy,ETHUSDT,SHORT,-1.96
ScalpingStrategy,LTCUSDT,SHORT,-4.36
TrendPullbackStrategy,BTCUSDT,SHORT,-0.80
TrendPullbackStrategy,ETCUSDT,SHORT,0.09
TrendPullbackStrategy,LTCUSDT,SHORT,-1.43
TrendPullbackStrategy,DOGEUSDT,SHORT,-1.68"""

lines = data.strip().split('\n')
trades = []
for line in lines:
    parts = line.split(',')
    trades.append({
        'strategy': parts[0],
        'symbol': parts[1],
        'side': parts[2],
        'pnl': float(parts[3])
    })

df = pd.DataFrame(trades)

# Overall Statistics
print("=" * 80)
print("PRODUCTION TRADING PERFORMANCE REPORT")
print("=" * 80)
print(f"\nTotal Trades: {len(df)}")
print(f"Total PnL: ${df['pnl'].sum():.2f} USDT")
print(f"Average Trade: ${df['pnl'].mean():.2f} USDT")
print(f"Win Rate: {(df['pnl'] > 0).sum() / len(df) * 100:.2f}%")
print(f"Winners: {(df['pnl'] > 0).sum()}")
print(f"Losers: {(df['pnl'] <= 0).sum()}")

# Per-Strategy Breakdown
print("\n" + "=" * 80)
print("PER-STRATEGY PERFORMANCE")
print("=" * 80)

for strategy in df['strategy'].unique():
    strategy_df = df[df['strategy'] == strategy]
    wins = (strategy_df['pnl'] > 0).sum()
    losses = (strategy_df['pnl'] <= 0).sum()
    total = len(strategy_df)
    win_rate = wins / total * 100
    total_pnl = strategy_df['pnl'].sum()
    avg_win = strategy_df[strategy_df['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
    avg_loss = strategy_df[strategy_df['pnl'] <= 0]['pnl'].mean() if losses > 0 else 0
    
    print(f"\n{strategy}:")
    print(f"  Trades: {total}")
    print(f"  Win Rate: {win_rate:.2f}% ({wins}W / {losses}L)")
    print(f"  Total PnL: ${total_pnl:.2f}")
    print(f"  Avg Trade: ${strategy_df['pnl'].mean():.2f}")
    print(f"  Avg Win: ${avg_win:.2f}")
    print(f"  Avg Loss: ${avg_loss:.2f}")
    print(f"  Risk-Reward: {abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "  Risk-Reward: N/A")

# Long vs Short Analysis
print("\n" + "=" * 80)
print("DIRECTIONAL BIAS")
print("=" * 80)

for side in ['LONG', 'SHORT']:
    side_df = df[df['side'] == side]
    if len(side_df) > 0:
        print(f"\n{side}:")
        print(f"  Trades: {len(side_df)}")
        print(f"  Win Rate: {(side_df['pnl'] > 0).sum() / len(side_df) * 100:.2f}%")
        print(f"  Total PnL: ${side_df['pnl'].sum():.2f}")
        print(f"  Avg Trade: ${side_df['pnl'].mean():.2f}")

# Symbol Performance
print("\n" + "=" * 80)
print("TOP 10 SYMBOLS BY PNL")
print("=" * 80)

symbol_stats = df.groupby('symbol').agg({
    'pnl': ['sum', 'count', 'mean']
}).round(2)
symbol_stats.columns = ['Total PnL', 'Trades', 'Avg PnL']
symbol_stats = symbol_stats.sort_values('Total PnL', ascending=False)

print(symbol_stats.head(10).to_string())

print("\n" + "=" * 80)
print("WORST 5 SYMBOLS BY PNL")
print("=" * 80)
print(symbol_stats.tail(5).to_string())

# Best and Worst Trades
print("\n" + "=" * 80)
print("EXTREMES")
print("=" * 80)

best_trade = df.loc[df['pnl'].idxmax()]
worst_trade = df.loc[df['pnl'].idxmin()]

print(f"\nBest Trade: {best_trade['strategy']} | {best_trade['symbol']} {best_trade['side']} | +${best_trade['pnl']:.2f}")
print(f"Worst Trade: {worst_trade['strategy']} | {worst_trade['symbol']} {worst_trade['side']} | ${worst_trade['pnl']:.2f}")
