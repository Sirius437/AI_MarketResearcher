#!/bin/bash

# Simple Fail2Ban Setup Script for SSH Protection
echo "🔒 Setting up basic Fail2Ban SSH protection..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

# Copy configuration file
echo "📝 Installing simple Fail2Ban configuration..."
cp ./web/simple-jail.conf /etc/fail2ban/jail.d/simple.conf

# Make sure there are no conflicting configurations
echo "🧹 Cleaning up any conflicting configurations..."
rm -f /etc/fail2ban/jail.d/marketresearcher.conf

# Ensure proper permissions
chmod 644 /etc/fail2ban/jail.d/simple.conf

# Restart Fail2Ban with debugging
echo "🔄 Starting Fail2Ban service with debugging..."
systemctl stop fail2ban
sleep 2
fail2ban-client -x start

# Check status
echo "✅ Checking Fail2Ban status..."
fail2ban-client status

echo ""
echo "🛡️ Basic Fail2Ban SSH protection has been set up!"
echo "📊 To check current bans: sudo fail2ban-client status"
echo "🔓 To unban an IP: sudo fail2ban-client set sshd unbanip IP"
echo ""
