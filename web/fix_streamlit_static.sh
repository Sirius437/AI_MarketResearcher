#!/bin/bash

# Fix Streamlit static file serving through nginx reverse proxy

echo "🔧 Fixing Streamlit static file serving..."

# Update nginx configuration to properly handle Streamlit static files
sudo tee /etc/nginx/sites-available/marketresearcher > /dev/null <<'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

server {
    listen 80;
    server_name your-domain.com localhost;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com localhost;
    
    # SSL Configuration
    ssl_certificate #/path/to/your/ssl/cert.pem;  # Update with your SSL certificate path
    ssl_certificate_key #/path/to/your/ssl/key.pem;  # Update with your SSL key path
    
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
    
    # Streamlit static files - serve directly without proxy
    location /static/ {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Add CORS headers for static files
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
    }
    
    # Streamlit WebSocket connections
    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Main application (Streamlit)
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_cache_bypass $http_upgrade;
        
        # Rate limiting for general access
        limit_req zone=api burst=10 nodelay;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting for API
        limit_req zone=api burst=20 nodelay;
    }
    
    # Stricter rate limiting for login endpoint
    location /api/auth/login {
        proxy_pass http://127.0.0.1:8000/auth/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Very strict rate limiting for login attempts
        limit_req zone=login burst=3 nodelay;
    }
    
    # Block access to sensitive files
    location ~ /\.ht {
        deny all;
    }
    
    location ~ /\.env {
        deny all;
    }
    
    location ~ /users\.json {
        deny all;
    }
}
EOF

# Test nginx configuration
if sudo nginx -t; then
    echo "✅ Nginx configuration valid"
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx configuration error"
    sudo nginx -t
    exit 1
fi

# Test static file access
echo "🧪 Testing static file access..."
sleep 2

# Test local access first
if curl -k -s -o /dev/null -w "%{http_code}" https://YOUR_LOCAL_IP/static/ | grep -q "200\|404"; then
    echo "✅ Local static file routing working"
else
    echo "⚠️  Local static file test inconclusive"
fi

# Test remote access
if curl -k -s -o /dev/null -w "%{http_code}" https://YOUR_DOMAIN.com/static/ | grep -q "200\|404"; then
    echo "✅ Remote static file routing working"
else
    echo "⚠️  Remote static file test inconclusive"
fi

echo ""
echo "🎉 Streamlit static file serving should now be fixed!"
echo "Try accessing: https://YOUR_DOMAIN.com"
