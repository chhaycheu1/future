#!/bin/bash
# Manual deployment script to force update server to commit 81aea44

echo "=== Forcing server update to commit 81aea44 ==="
echo ""
echo "This script will:"
echo "1. SSH into your production server"
echo "2. Force reset to commit 81aea44"
echo "3. Restart the trading bot"
echo ""

# You need to update these values:
SERVER_IP="YOUR_SERVER_IP"
SERVER_USER="deployer"

ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
    cd /var/www/trading-bot
    
    echo "Current commit:"
    git log --oneline -1
    
    echo ""
    echo "Fetching latest from origin..."
    git fetch origin
    
    echo ""
    echo "Force resetting to origin/main (81aea44)..."
    git reset --hard origin/main
    
    echo ""
    echo "New commit:"
    git log --oneline -1
    
    echo ""
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    echo ""
    echo "Restarting trading bot..."
    sudo systemctl restart tradingbot
    
    echo ""
    echo "Checking bot status..."
    sudo systemctl status tradingbot --no-pager -l
    
    echo ""
    echo "Done! Server should now be running commit 81aea44"
EOF
