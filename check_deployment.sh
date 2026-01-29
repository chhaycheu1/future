#!/bin/bash
# Check deployment status on production server

echo "=== Checking Production Server Status ==="
echo ""

# Update with your server details
SERVER_IP="YOUR_SERVER_IP"
SERVER_USER="deployer"

ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
    echo "1. Current Git Commit:"
    cd /var/www/trading-bot
    git log --oneline -1
    
    echo ""
    echo "2. Bot Service Status:"
    sudo systemctl status tradingbot --no-pager | head -15
    
    echo ""
    echo "3. Active Strategies in bot.py:"
    grep -A 5 "self.strategies = \[" src/core/bot.py
    
    echo ""
    echo "4. Recent bot logs (last 20 lines):"
    sudo journalctl -u tradingbot -n 20 --no-pager
EOF
