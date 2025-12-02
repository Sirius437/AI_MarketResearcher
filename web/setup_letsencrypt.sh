#!/bin/bash

# Setup Let's Encrypt SSL certificate for MarketResearcher
# Requires a domain name pointing to your public IP

echo "🔐 Setting up Let's Encrypt SSL certificate..."

# Install certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

echo "⚠️  IMPORTANT: You need a domain name for Let's Encrypt!"
echo "Examples: marketresearcher.yourdomain.com"
echo ""
read -p "Enter your domain name (or press Enter to skip): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Domain required for Let's Encrypt. Exiting."
    exit 1
fi

# Stop nginx temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d "$DOMAIN" --email your-email@example.com --agree-tos --no-eff-email

if [ $? -eq 0 ]; then
    echo "✅ Let's Encrypt certificate obtained!"
    
    # Update nginx config to use Let's Encrypt certificate
    sudo sed -i "s|#ssl_certificate /path/to/your/ssl/cert.pem;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|g" /etc/nginx/sites-available/marketresearcher
    sudo sed -i "s|#ssl_certificate_key /path/to/your/ssl/key.pem;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|g" /etc/nginx/sites-available/marketresearcher
    
    # Update server_name
    sudo sed -i "s|server_name YOUR_LOCAL_IP localhost;|server_name $DOMAIN;|g" /etc/nginx/sites-available/marketresearcher
    
    # Test and reload nginx
    sudo nginx -t && sudo systemctl start nginx
    
    # Setup auto-renewal
    sudo systemctl enable certbot.timer
    
    echo "🎉 Let's Encrypt SSL certificate installed!"
    echo "Access your site at: https://$DOMAIN"
else
    echo "❌ Failed to get Let's Encrypt certificate"
    sudo systemctl start nginx
fi
