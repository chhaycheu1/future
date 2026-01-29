import sqlite3
import sys

def analyze_liquidity_grab():
    try:
        conn = sqlite3.connect('instance/trading_bot.db')
        cursor = conn.cursor()
        
        # First check what columns exist
        cursor.execute('PRAGMA table_info(trades)')
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Available columns: {', '.join(columns)}\n")
        
        # Get LiquidityGrab performance
        query = """
            SELECT COUNT(*), 
                   ROUND(SUM(pnl), 2), 
                   ROUND(AVG(pnl), 2),
                   COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                   COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses
            FROM trades 
            WHERE strategy = 'LiquidityGrab' AND status = 'closed'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            total, total_pnl, avg_pnl, wins, losses = result
            win_rate = (wins / total * 100) if total > 0 else 0
            
            print("=" * 60)
            print("LIQUIDITYGRAB STRATEGY PERFORMANCE")
            print("=" * 60)
            print(f"Total Trades: {total}")
            print(f"Total PnL: ${total_pnl if total_pnl else 0:.2f} USDT")
            print(f"Avg PnL: ${avg_pnl if avg_pnl else 0:.2f}")
            print(f"Wins: {wins} | Losses: {losses}")
            print(f"Win Rate: {win_rate:.2f}%")
            print("=" * 60)
            print()
            
            # Get recent trades
            cursor.execute("""
                SELECT id, symbol, side, entry_price, ROUND(pnl, 2) as pnl, 
                       entry_time, close_time
                FROM trades 
                WHERE strategy = 'LiquidityGrab' AND status = 'closed'
                ORDER BY close_time DESC
                LIMIT 20
            """)
            
            print("Recent 20 LiquidityGrab Trades:")
            print("-" * 100)
            print(f"{'ID':<5} | {'Symbol':<12} | {'Side':<6} | {'Entry':<10} | {'PnL':<10} | {'Entry Time':<19} -> {'Close Time':<19}")
            print("-" * 100)
            
            for row in cursor.fetchall():
                trade_id, symbol, side, entry_price, pnl, entry_time, close_time = row
                entry_time_str = entry_time[:19] if entry_time else 'N/A'
                close_time_str = close_time[:19] if close_time else 'N/A'
                pnl_str = f"${pnl:+7.2f}"
                
                print(f"{trade_id:<5} | {symbol:<12} | {side:<6} | ${entry_price:8.4f} | {pnl_str:<10} | {entry_time_str:<19} -> {close_time_str:<19}")
            
            # Breakdown by symbol
            cursor.execute("""
                SELECT symbol, 
                       COUNT(*) as trades,
                       ROUND(SUM(pnl), 2) as total_pnl,
                       COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins
                FROM trades 
                WHERE strategy = 'LiquidityGrab' AND status = 'closed'
                GROUP BY symbol
                ORDER BY total_pnl ASC
            """)
            
            print("\n" + "=" * 60)
            print("BREAKDOWN BY SYMBOL (Worst to Best)")
            print("=" * 60)
            print(f"{'Symbol':<12} | {'Trades':<8} | {'Total PnL':<12} | {'Win Rate':<10}")
            print("-" * 60)
            
            for symbol, trades, total_pnl, wins in cursor.fetchall():
                wr = (wins / trades * 100) if trades > 0 else 0
                print(f"{symbol:<12} | {trades:<8} | ${total_pnl:+9.2f} | {wr:5.1f}%")
            
            # Breakdown by LONG/SHORT
            cursor.execute("""
                SELECT side,
                       COUNT(*) as trades,
                       ROUND(SUM(pnl), 2) as total_pnl,
                       COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins
                FROM trades 
                WHERE strategy = 'LiquidityGrab' AND status = 'closed'
                GROUP BY side
            """)
            
            print("\n" + "=" * 60)
            print("BREAKDOWN BY SIDE")
            print("=" * 60)
            print(f"{'Side':<10} | {'Trades':<8} | {'Total PnL':<12} | {'Win Rate':<10}")
            print("-" * 60)
            
            for side, trades, total_pnl, wins in cursor.fetchall():
                wr = (wins / trades * 100) if trades > 0 else 0
                print(f"{side:<10} | {trades:<8} | ${total_pnl:+9.2f} | {wr:5.1f}%")
            
        else:
            print("No LiquidityGrab trades found in the database.")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    analyze_liquidity_grab()
