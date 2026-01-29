#!/bin/bash
# Quick Fix: Check logs and restart bot with database migration

echo "🔍 Checking bot logs for errors..."
sudo journalctl -u tradingbot -n 50 --no-pager

echo ""
echo "🔄 Restarting bot to trigger database migration..."
sudo systemctl restart tradingbot

echo ""
echo "⏳ Waiting 5 seconds..."
sleep 5

echo ""
echo "📊 Checking bot status..."
sudo systemctl status tradingbot --no-pager

echo ""
echo "✅ Done! Try refreshing the web page now."
