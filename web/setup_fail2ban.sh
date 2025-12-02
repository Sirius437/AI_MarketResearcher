#!/bin/bash

# MarketResearcher Fail2Ban Setup Script
echo "🔒 Setting up Fail2Ban protection for MarketResearcher..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

# Create log directories if they don't exist
echo "📁 Creating log directories..."
mkdir -p ./web/logs

# Create log files if they don't exist
touch ./web/logs/api_access.log
touch ./web/logs/streamlit_access.log

# Set proper permissions
# chown -R your-username:your-username ./web/logs  # Update with your username
chmod 755 ./web/logs
chmod 644 ./web/logs/*.log

# Copy configuration files
echo "📝 Installing Fail2Ban configurations..."
cp ./web/marketresearcher-fail2ban.conf /etc/fail2ban/jail.d/marketresearcher.conf
cp ./web/marketresearcher-api.conf /etc/fail2ban/filter.d/marketresearcher-api.conf
cp ./web/marketresearcher-ui.conf /etc/fail2ban/filter.d/marketresearcher-ui.conf
cp ./web/nginx-badbots.conf /etc/fail2ban/filter.d/nginx-badbots.conf

# Ensure filter directory has correct permissions
chmod 755 /etc/fail2ban/filter.d
chmod 644 /etc/fail2ban/filter.d/*.conf

# Ensure Fail2Ban service is properly configured and running
echo "🔄 Starting Fail2Ban service..."

# Make sure the service is enabled
systemctl enable fail2ban

# Stop the service if it's running with issues
systemctl stop fail2ban

# Make sure the socket directory exists
mkdir -p /var/run/fail2ban

# Start the service
systemctl start fail2ban

# Give it a moment to initialize
sleep 2

# Check status
echo "✅ Checking Fail2Ban status..."
systemctl status fail2ban

echo ""
echo "🛡️ Fail2Ban protection for MarketResearcher has been set up!"
echo "🔒 Protection includes:"
echo "  - SSH brute force protection (3 failed attempts = 1 hour ban)"
echo "  - Nginx authentication failures (3 failed attempts = 1 hour ban)"
echo "  - Bad bots and scanners (2 detections = 24 hour ban)"
echo "  - MarketResearcher API protection (5 failed attempts = 1 hour ban)"
echo "  - MarketResearcher UI protection (5 suspicious requests = 1 hour ban)"
echo ""
echo "📊 To check current bans: sudo fail2ban-client status"
echo "🔓 To unban an IP: sudo fail2ban-client set JAIL unbanip IP"
echo "   Example: sudo fail2ban-client set sshd unbanip YOUR_LOCAL_IP"
echo ""
