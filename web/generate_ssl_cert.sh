#!/bin/bash

# Generate proper SSL certificates using Let's Encrypt

DOMAIN="your-domain.com"  # Replace with your domain
EMAIL="your-email@example.com"  # Replace with your email

echo "🔐 Generating proper SSL certificates using Let's Encrypt..."

# Backup existing certificates if they exist
if [ -f "ssl/cert.pem" ]; then
    echo "📦 Backing up existing certificates..."
    mv ssl/cert.pem ssl/cert_backup.pem
    mv ssl/key.pem ssl/key_backup.pem
fi

# Create directory for Let's Encrypt certificates if it doesn't exist
mkdir -p ssl

# Use certbot to obtain certificates for both domain and www subdomain
echo "🔑 Requesting certificates from Let's Encrypt..."
sudo certbot certonly --nginx \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --expand \
    --redirect

# Copy Let's Encrypt certificates to our ssl directory
echo "📋 Copying certificates to project directory..."
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem

# Fix permissions
sudo chown $(whoami):$(whoami) ssl/cert.pem ssl/key.pem

echo "✅ Proper SSL certificates generated"
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

echo "🎉 Certificate updated! Now using trusted Let's Encrypt certificates for $DOMAIN and www.$DOMAIN."
echo "⏰ Certificates will auto-renew before they expire."

