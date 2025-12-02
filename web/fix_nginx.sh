#!/bin/bash

# Fix nginx startup by handling Apache2 port conflict

echo "🔧 Fixing nginx startup issue..."

# Stop and disable Apache2 to free up port 80
echo "Stopping Apache2 service..."
sudo systemctl stop apache2
sudo systemctl disable apache2

# Verify port 80 is free
echo "Checking if port 80 is free..."
if sudo netstat -tlnp | grep :80; then
    echo "⚠️  Port 80 still in use, killing processes..."
    sudo fuser -k 80/tcp
    sleep 2
fi

# Start nginx
echo "Starting nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Check nginx status
if sudo systemctl is-active --quiet nginx; then
    echo "✅ nginx is running successfully"
    
    # Test HTTPS access
    echo "🔒 Testing HTTPS access..."
    if curl -k -s https://YOUR_LOCAL_IP > /dev/null; then
        echo "✅ HTTPS access working"
    else
        echo "⚠️  HTTPS access test failed - check if MarketResearcher services are running"
    fi
    
else
    echo "❌ nginx failed to start"
    sudo systemctl status nginx --no-pager
fi

echo ""
echo "🌐 Access URLs:"
echo "   HTTPS: https://YOUR_LOCAL_IP"
echo "   HTTP:  http://YOUR_LOCAL_IP (redirects to HTTPS)"
