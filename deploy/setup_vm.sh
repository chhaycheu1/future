#!/bin/bash

# Exit on error
set -e

APP_DIR="/var/www/trading-bot"
USER_NAME="deployer"

echo "t--- Updating System ---"
sudo apt update && sudo apt upgrade -y

echo "t--- Installing Dependencies ---"
sudo apt install -y python3 python3-pip python3-venv nginx git ufw

echo "t--- Setting up Firewall ---"
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "t--- Creating User $USER_NAME ---"
if id "$USER_NAME" &>/dev/null; then
    echo "User $USER_NAME already exists"
else
    sudo adduser --disabled-password --gecos "" $USER_NAME
    sudo usermod -aG sudo $USER_NAME
fi

echo "t--- Setting up Application Directory ---"
sudo mkdir -p $APP_DIR
sudo chown -R $USER_NAME:$USER_NAME $APP_DIR

# Initial setup of venv (can be done during CI/CD too, but good to have prepared)
sudo -u $USER_NAME bash -c "cd $APP_DIR && python3 -m venv venv"

echo "t--- Nginx Setup ---"
# Remove default if exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi

# Copy config usually happens here, assuming this script runs from the repo or we copy the file manually.
# For now, we will assume strict separation or that the user copies the file content.
# Only linking if the file exists in the right place (e.g., if we cloned repo to $APP_DIR already)
# sudo ln -sf $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/tradingbot
# sudo ln -sf /etc/nginx/sites-available/tradingbot /etc/nginx/sites-enabled/

echo "t--- Setup Complete ---"
echo "Next steps:"
echo "1. Configure SSH keys for $USER_NAME"
echo "2. Clone/Upload your code to $APP_DIR"
echo "3. Copy deploy/nginx.conf to /etc/nginx/sites-available/tradingbot and enable it"
echo "4. Copy deploy/tradingbot.service to /etc/systemd/system/ and enable it"
