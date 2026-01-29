#!/bin/bash
# Server Restart Script
# Run this on the production server to pull latest changes and restart

echo "🔄 Pulling latest changes from GitHub..."
cd ~/future
git pull origin main

echo "🔄 Restarting trading bot service..."
sudo systemctl restart tradingbot

echo "⏳ Waiting for service to start..."
sleep 3

echo "📊 Checking service status..."
sudo systemctl status tradingbot --no-pager

echo ""
echo "✅ Deployment complete!"
echo "🌐 Web should be updated now"
echo ""
echo "If statistics reset is needed on server, run:"
echo "  cd ~/future && python3 reset_statistics.py"
