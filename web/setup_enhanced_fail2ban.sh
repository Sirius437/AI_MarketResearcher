#!/bin/bash

# Enhanced Fail2Ban Setup Script for MarketResearcher
echo "🔒 Setting up enhanced Fail2Ban protection for MarketResearcher..."

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
# Set proper permissions - update with your username
# chown -R your-username:your-username ./web/logs
chmod 755 ./web/logs
chmod 644 ./web/logs/*.log

# Copy configuration files
echo "📝 Installing enhanced Fail2Ban configurations..."
cp ./web/enhanced-jail.conf /etc/fail2ban/jail.d/marketresearcher.conf
cp ./web/marketresearcher-api.conf /etc/fail2ban/filter.d/marketresearcher-api.conf
cp ./web/marketresearcher-ui.conf /etc/fail2ban/filter.d/marketresearcher-ui.conf

# Ensure proper permissions
chmod 644 /etc/fail2ban/jail.d/marketresearcher.conf
chmod 644 /etc/fail2ban/filter.d/marketresearcher-api.conf
chmod 644 /etc/fail2ban/filter.d/marketresearcher-ui.conf

# Reload Fail2Ban configuration
echo "🔄 Reloading Fail2Ban configuration..."
fail2ban-client reload

# Check status
echo "✅ Checking Fail2Ban status..."
fail2ban-client status

echo ""
echo "🛡️ Enhanced Fail2Ban protection for MarketResearcher has been set up!"
echo "🔒 Protection includes:"
echo "  - SSH brute force protection (3 failed attempts = 1 hour ban)"
echo "  - Nginx authentication failures (3 failed attempts = 1 hour ban)"
echo "  - MarketResearcher API protection (5 failed attempts = 1 hour ban)"
echo "  - MarketResearcher UI protection (5 suspicious requests = 1 hour ban)"
echo ""
echo "📊 To check current bans: sudo fail2ban-client status"
echo "🔓 To unban an IP: sudo fail2ban-client set JAIL unbanip IP"
echo "   Example: sudo fail2ban-client set sshd unbanip YOUR_LOCAL_IP"
echo ""

# Add configuration to log rotation
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/marketresearcher << EOF
./web/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 your-username your-username  # Update with your username
    sharedscripts
    postrotate
        fail2ban-client reload > /dev/null
    endscript
}
EOF

echo "✅ Log rotation configured for MarketResearcher logs"
echo ""
