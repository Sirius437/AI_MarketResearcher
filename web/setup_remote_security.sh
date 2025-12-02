#!/bin/bash

# MarketResearcher Remote Access Security Setup Script
# This script configures firewall, SSL, and security measures for remote access

echo "🔒 Setting up MarketResearcher Remote Access Security..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get local IP
LOCAL_IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -1)
echo "📍 Local IP Address: $LOCAL_IP"

# 1. Configure UFW Firewall
echo -e "\n${YELLOW}1. Configuring UFW Firewall...${NC}"

# Enable UFW
sudo ufw --force enable

# Default policies - deny incoming, allow outgoing
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (important - don't lock yourself out!)
sudo ufw allow ssh
sudo ufw allow 22

# Allow MarketResearcher ports from specific networks only
echo "🌐 Allowing MarketResearcher ports (8000, 8501) for local network..."
sudo ufw allow from YOUR_LOCAL_NETWORK to any port 8000
sudo ufw allow from YOUR_LOCAL_NETWORK to any port 8501

# Allow HTTPS (443) for secure remote access
sudo ufw allow 443

# Allow HTTP (80) for redirect to HTTPS
sudo ufw allow 80

echo -e "${GREEN}✅ Firewall configured${NC}"

# 2. Generate SSL Certificates
echo -e "\n${YELLOW}2. Generating SSL Certificates...${NC}"

# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate for development
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo "🔐 Generating self-signed SSL certificate..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
        -subj "/C=US/ST=State/L=City/O=MarketResearcher/CN=$LOCAL_IP" \
        -addext "subjectAltName=IP:$LOCAL_IP,DNS:localhost"
    
    # Set proper permissions
    chmod 600 ssl/key.pem
    chmod 644 ssl/cert.pem
    
    echo -e "${GREEN}✅ SSL certificates generated${NC}"
else
    echo -e "${GREEN}✅ SSL certificates already exist${NC}"
fi

# 3. Install nginx for reverse proxy and SSL termination
echo -e "\n${YELLOW}3. Setting up Nginx reverse proxy...${NC}"

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Create nginx configuration for MarketResearcher
sudo tee /etc/nginx/sites-available/marketresearcher > /dev/null <<EOF
# Rate limiting
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/m;

server {
    listen 80;
    server_name $LOCAL_IP localhost;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $LOCAL_IP localhost;
    
    # SSL Configuration
    ssl_certificate $(pwd)/ssl/cert.pem;
    ssl_certificate_key $(pwd)/ssl/key.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Main application (Streamlit)
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
        
        # Rate limiting for general access
        limit_req zone=api burst=10 nodelay;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Rate limiting for API
        limit_req zone=api burst=20 nodelay;
    }
    
    # Stricter rate limiting for login endpoint
    location /api/auth/login {
        proxy_pass http://127.0.0.1:8000/auth/login;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Very strict rate limiting for login attempts
        limit_req zone=login burst=3 nodelay;
    }
    
    # Block access to sensitive files
    location ~ /\\.ht {
        deny all;
    }
    
    location ~ /\\.env {
        deny all;
    }
    
    location ~ /users\\.json {
        deny all;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/marketresearcher /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if sudo nginx -t; then
    echo -e "${GREEN}✅ Nginx configuration valid${NC}"
    sudo systemctl restart nginx
    sudo systemctl enable nginx
else
    echo -e "${RED}❌ Nginx configuration error${NC}"
    exit 1
fi

# 4. Configure fail2ban for additional protection
echo -e "\n${YELLOW}4. Setting up fail2ban protection...${NC}"

if ! command -v fail2ban-server &> /dev/null; then
    echo "📦 Installing fail2ban..."
    sudo apt install -y fail2ban
fi

# Create fail2ban configuration for MarketResearcher
sudo tee /etc/fail2ban/jail.d/marketresearcher.conf > /dev/null <<EOF
[nginx-login]
enabled = true
port = http,https
filter = nginx-login
logpath = /var/log/nginx/access.log
maxretry = 3
bantime = 3600
findtime = 600

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 86400
findtime = 600
EOF

# Create custom filter for login attempts
sudo tee /etc/fail2ban/filter.d/nginx-login.conf > /dev/null <<EOF
[Definition]
failregex = ^<HOST>.*POST.*/auth/login.*HTTP/1.* 401
ignoreregex =
EOF

sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

echo -e "${GREEN}✅ fail2ban configured${NC}"

# 5. Display firewall status
echo -e "\n${YELLOW}5. Current Firewall Status:${NC}"
sudo ufw status numbered

# 6. Show final configuration
echo -e "\n${GREEN}🎉 Remote Access Security Setup Complete!${NC}"
echo ""
echo "🔒 Security Features Enabled:"
echo "   ✅ UFW Firewall with restrictive rules"
echo "   ✅ SSL/HTTPS encryption"
echo "   ✅ Nginx reverse proxy with security headers"
echo "   ✅ Rate limiting (5 login attempts/min, 30 API calls/min)"
echo "   ✅ fail2ban protection against brute force"
echo "   ✅ Security headers (XSS, CSRF, etc.)"
echo ""
echo "🌐 Access URLs:"
echo "   Local:  https://$LOCAL_IP"
echo "   Remote: https://YOUR_PUBLIC_IP (after port forwarding)"
echo ""
echo "⚠️  Next Steps for Remote Access:"
echo "   1. Configure port forwarding on your router:"
echo "      - Forward external port 443 → $LOCAL_IP:443"
echo "      - Forward external port 80 → $LOCAL_IP:80 (optional, for redirects)"
echo "   2. Find your public IP: curl ifconfig.me"
echo "   3. Consider using a dynamic DNS service"
echo "   4. Test access from external network"
echo ""
echo "🔧 Management Commands:"
echo "   - View firewall: sudo ufw status"
echo "   - View fail2ban: sudo fail2ban-client status"
echo "   - Nginx logs: sudo tail -f /var/log/nginx/access.log"
echo "   - SSL cert info: openssl x509 -in ssl/cert.pem -text -noout"
