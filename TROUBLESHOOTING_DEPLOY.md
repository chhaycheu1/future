# Troubleshooting: Web Not Updating After GitHub Deploy

## Issue
Code pushed to GitHub but web interface not showing changes.

## Possible Causes & Solutions

### 1. **Browser Cache** (Most Common)
**Try this first:**
- **Hard Refresh**: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- **Clear Browser Cache**: Settings → Clear browsing data → Cached images and files
- **Incognito/Private Window**: Open web in private browsing mode

---

### 2. **Check GitHub Actions Status**
1. Go to: https://github.com/chhaycheu1/future/actions
2. Check if latest deployment succeeded (green ✅) or failed (red ❌)
3. If failed, click on it to see error logs

---

### 3. **Manual Server Restart** (If Auto-Deploy Failed)

**Option A: Using the restart script**
```bash
# SSH into your server
ssh root@103.82.23.153

# Navigate to project directory
cd /var/www/trading-bot

# Run restart script
bash deploy_restart.sh
```

**Option B: Manual commands**
```bash
# SSH into server
ssh root@103.82.23.153

# 1. Pull latest code
cd /var/www/trading-bot
git pull origin main

# 2. Restart service
sudo systemctl restart tradingbot

# 3. Check status
sudo systemctl status tradingbot

# 4. Check logs (if errors)
sudo journalctl -u tradingbot -n 50
```

---

### 4. **Reset Statistics on Server** (If Database Not Reset)

The statistics reset (`reset_statistics.py`) only ran **locally**, not on the server.

**To reset on production server:**
```bash
# SSH into server
ssh root@103.82.23.153

# Navigate to project
cd /var/www/trading-bot

# Activate virtual environment
source venv/bin/activate

# Run reset script
python3 reset_statistics.py
# Type "yes" when prompted

# Restart service
sudo systemctl restart tradingbot
```

---

### 5. **Check Nginx Status**
```bash
# Check Nginx is running
sudo systemctl status nginx

# Reload Nginx config (if changed)
sudo nginx -t
sudo systemctl reload nginx
```

---

### 6. **Verify Code on Server**

Check if latest code is actually on the server:
```bash
ssh root@103.82.23.153
cd /var/www/trading-bot

# Check current commit
git log -1 --oneline

# Should match latest commit on GitHub
```

Compare with GitHub: https://github.com/chhaycheu1/future/commits/main

---

## Quick Diagnosis Steps

1. **Hard refresh browser** (`Ctrl+Shift+R`)
2. **Check GitHub Actions**: https://github.com/chhaycheu1/future/actions
3. **SSH and restart**: `sudo systemctl restart tradingbot`
4. **Check service logs**: `sudo journalctl -u tradingbot -n 50`

---

## Expected Changes

After successful deployment, you should see:

### Trade History Page (`/history`)
- **MeanReversion** option removed from strategy filter dropdown
- Only showing:
  - ScalpingStrategy
  - SmartScalpingStrategy
  - TrendPullbackStrategy
  - RangeSweepStrategy
  - MomentumBreakout
  - LiquidityGrab

### Reports Page (`/reports`)
- Same filter changes as History page

### Dashboard Statistics
- **Will still show old data** until you run `reset_statistics.py` **on the server**
- Local reset only affected your local database, not production

---

## Still Not Working?

If none of the above work:

1. **Check server IP**: Make sure you're visiting the correct server (103.82.23.153)
2. **Check DNS/Port**: Verify you're accessing the right port
3. **Check deployment logs**: 
   ```bash
   sudo journalctl -u tradingbot -n 100 --no-pager
   ```
4. **Force restart everything**:
   ```bash
   sudo systemctl stop tradingbot
   sudo systemctl start tradingbot
   sudo systemctl restart nginx
   ```

---

## Contact Info

If deployment is broken, check:
- GitHub Actions logs
- Server logs: `journalctl -u tradingbot`
- Nginx logs: `/var/log/nginx/error.log`
