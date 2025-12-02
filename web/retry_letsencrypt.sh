#!/bin/bash

# Retry Let's Encrypt after DNS fix

echo "🔐 Retrying Let's Encrypt for your-domain.com..."

# Check DNS first
echo "🔍 Checking DNS resolution..."
RESOLVED_IP=$(dig your-domain.com A +short)
echo "Domain resolves to: $RESOLVED_IP"

if [ "$RESOLVED_IP" != "YOUR_SERVER_IP" ]; then
    echo "❌ DNS still points to wrong IP. Update DNS first!"
    echo "Current: $RESOLVED_IP"
    echo "Required: YOUR_SERVER_IP"
    exit 1
fi

# Ensure port 80 is open in router for Let's Encrypt validation
echo "⚠️  Make sure port 80 is forwarded in your router!"
echo "Router config needed:"
echo "- Port 80 → YOUR_LOCAL_IP:80"
echo "- Port 443 → YOUR_LOCAL_IP:443"
echo ""
read -p "Press Enter when DNS and router are configured..."

# Stop nginx temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com --email your-email@example.com --agree-tos --no-eff-email

if [ $? -eq 0 ]; then
    echo "✅ Let's Encrypt certificate obtained!"
    
    # Update nginx config
    sudo sed -i "s|#ssl_certificate /path/to/your/ssl/cert.pem;|ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;|g" /etc/nginx/sites-available/marketresearcher
    sudo sed -i "s|#ssl_certificate_key /path/to/your/ssl/key.pem;|ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;|g" /etc/nginx/sites-available/marketresearcher
    
    # Update server_name
    sudo sed -i "s|server_name YOUR_LOCAL_IP localhost;|server_name your-domain.com;|g" /etc/nginx/sites-available/marketresearcher
    
    # Test and start nginx
    sudo nginx -t && sudo systemctl start nginx
    
    # Setup auto-renewal
    sudo systemctl enable certbot.timer
    
    echo "🎉 SSL certificate installed!"
    echo "Access: https://your-domain.com"
else
    echo "❌ Certificate failed again"
    sudo systemctl start nginx
fi
