#!/bin/bash
# Check Flask application logs for errors

echo "📋 Checking last 100 lines of bot logs for errors..."
sudo journalctl -u tradingbot -n 100 --no-pager | grep -i "error\|exception\|traceback" -A 10

echo ""
echo "📋 Full recent logs:"
sudo journalctl -u tradingbot -n 50 --no-pager

echo ""
echo "💡 Try accessing the dashboard and then run this again to see the error."
