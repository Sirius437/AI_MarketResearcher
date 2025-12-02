# MarketResearcher Web Interface

A secure web interface for remote access to the MarketResearcher platform, built with FastAPI backend and Streamlit frontend.

## Features

- **Secure Authentication**: JWT-based authentication with user management
- **Stock Analysis**: Real-time stock market analysis with AI insights
- **Cryptocurrency Analysis**: Comprehensive crypto market research
- **Portfolio Management**: Track and manage investment portfolios
- **Responsive UI**: Modern, user-friendly Streamlit interface
- **Docker Support**: Easy deployment with Docker Compose
- **SSL/HTTPS**: Secure connections with Nginx reverse proxy

## Quick Start

### Option 1: Automated Startup Scripts

#### Standard Web Interface

```bash
./web/start_web.sh
```

This script:
- Activates/creates a virtual environment
- Installs dependencies
- Generates SSL certificates if needed
- Starts the FastAPI server (port 8000)
- Starts the Streamlit frontend (port 8501)
- Displays access URLs and credentials

#### Network-Optimized Web Interface

```bash
./web/start_web_network.sh
```

This script:
- Detects your local network IP address
- Configures services for network access
- Disables CORS and XSRF protection for easier local network access
- Starts Streamlit with network-friendly settings
- Displays network access URLs for mobile/tablet devices

#### Scanner Service

```bash
./web/start_scanner_service.sh
```

This script:
- Activates the marketresearcher conda environment
- Installs required dependencies (Flask) if needed
- Starts the isolated Interactive Brokers scanner service
- Runs on port 5000
- Performs a health check
- Displays the process ID for management

**Dependencies:**
- Flask: `pip install flask`
- Interactive Brokers API: Already included in main requirements

**Troubleshooting:**
If you encounter issues with the scanner service:
1. Ensure you're using the marketresearcher conda environment
2. Verify Flask is installed: `pip list | grep flask`
3. Check the IB Gateway connection status

### Option 2: Manual Development Mode

1. **Install dependencies:**
```bash
cd web
conda activate marketresearcher
pip install -r requirements_web.txt
```

2. **Start the API server:**
```bash
python api.py
```

3. **Start the Streamlit frontend (in another terminal):**
```bash
streamlit run streamlit_app.py
```

4. **Access the application:**
- Frontend: http://localhost:8501
- API: http://localhost:8000
- Default credentials: `admin` / `admin123`

### Option 3: Docker Deployment

1. **Build and start services:**
```bash
docker-compose up -d
```

2. **Access the application:**
- HTTPS: https://localhost (with SSL)
- HTTP: http://localhost (redirects to HTTPS)

## Architecture

### Complete System Architecture

```
                                 Internet
                                     |
                                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Domain Names                           │
│        your-domain.com / www.your-domain.com            │
│                      │                                  │
│                      ▼                                  │
│ ┌─────────────────────────────────────┐                 │
│ │         Router (Port Forwarding)    │                 │
│ │     External:80/443 → Internal:80/443                 │
│ └─────────────────────────────────────┘                 │
│                      │                                  │
│                      ▼                                  │
│ ┌─────────────────────────────────────┐                 │
│ │           Fail2Ban Protection       │                 │
│ │  (SSH, Nginx, API, UI protection)   │                 │
│ └─────────────────────────────────────┘                 │
│                      │                                  │
│                      ▼                                  │
│ ┌──────────── ─┐    ┌─────────────┐    ┌─────────────┐  │
│ │ Nginx Proxy  │    │ Streamlit UI│    │ FastAPI API │  │
│ │(Ports 80/443)│───→│ (Port 8501)│───→ │ (Port 8000) │  │ 
│ └────────── ───┘     └─────────────┘    └─────────────┘ │
│                                             │           │
│                                             ▼           │
│                                    ┌─────────────────┐  │
│                                    │MarketResearcher │  │
│                                    │    Engine       │  │
│                                    └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. External users access your-domain.com or www.your-domain.com
2. DNS resolves to server IP (YOUR_SERVER_IP)
3. Router forwards ports 80/443 to the server
4. Fail2Ban monitors for suspicious activity
5. Nginx proxy handles SSL termination and routes requests:
   - Web UI requests → Streamlit (port 8501)
   - API requests → FastAPI (port 8000)
6. Both frontend and backend interact with the MarketResearcher engine

### Security Layers

1. **DNS/Domain**: your-domain.com with Let's Encrypt SSL
2. **Network**: Router with port forwarding
3. **Host**: Fail2Ban IP blocking
4. **Application**: JWT authentication, CORS, security headers
```

## Shutdown Procedures

### Graceful Shutdown of Automated Scripts

For services started with the automated scripts, press `Ctrl+C` in the terminal where the script is running. The scripts include trap handlers that will properly terminate all child processes.

### Manual Process Termination

1. **Find running processes:**
```bash
ps aux | grep -E 'api.py|streamlit|scanner_service'
```

2. **Kill processes by PID:**
```bash
kill <API_PID> <STREAMLIT_PID> <SCANNER_PID>
```

3. **Force kill if necessary:**
```bash
kill -9 <PID>
```

### Docker Shutdown

1. **Stop containers:**
```bash
docker-compose down
```

2. **Remove containers and volumes (if needed):**
```bash
docker-compose down -v
```

### Nginx Service

1. **Reload configuration:**
```bash
sudo systemctl reload nginx
```

2. **Restart service:**
```bash
sudo systemctl restart nginx
```

3. **Stop service:**
```bash
sudo systemctl stop nginx
```

### Security Services

1. **Stop Fail2Ban protection:**
```bash
sudo systemctl stop fail2ban
```

2. **Disable Fail2Ban on boot:**
```bash
sudo systemctl disable fail2ban
```

3. **Check Fail2Ban status:**
```bash
sudo systemctl status fail2ban
```

4. **View currently banned IPs:**
```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo fail2ban-client status marketresearcher-ui
```

5. **Unban a specific IP:**
```bash
sudo fail2ban-client set sshd unbanip YOUR_LOCAL_IP
```

## Network Management

### Active User Monitoring

1. **Check current active connections to web interface:**
```bash
netstat -an | grep :8501 | grep ESTABLISHED | wc -l
```

2. **View active user sessions in real-time:**
```bash
watch -n 1 "netstat -an | grep :8501 | grep ESTABLISHED"
```

3. **Monitor API requests with access log:**
```bash
tail -f web/logs/api_access.log
```

4. **View active user details from API (requires admin authentication):**
```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -d '{"username":"admin","password":"admin123"}' -H "Content-Type: application/json" | jq -r .access_token)

# Use token to access active users endpoint
curl -s http://localhost:8000/admin/active-users -H "Authorization: Bearer $TOKEN" | jq
```

5. **Identify specific users and their activity:**
```bash
# Get detailed user information including IP addresses and session IDs
curl -s http://localhost:8000/admin/active-users -H "Authorization: Bearer $TOKEN" | jq '.recent_activity'

# Filter by specific username
curl -s http://localhost:8000/admin/active-users -H "Authorization: Bearer $TOKEN" | jq '.recent_activity[] | select(.username=="specific_user")'
```

6. **Match IP addresses with network connections:**
```bash
# Get IP addresses of all connections to the web interface
netstat -an | grep :8501 | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq -c
```

### Network Status Checks

1. **Check if web services are listening:**
```bash
ss -tulpn | grep -E ':(8000|8501|5000)'
```

2. **Verify Nginx proxy status:**
```bash
sudo systemctl status nginx
```

3. **Test API health endpoint:**
```bash
curl -s http://localhost:8000/health | jq
```

4. **Check scanner service health:**
```bash
curl -s http://localhost:5000/health
```

5. **Verify domain resolution:**
```bash
nslookup your-domain.com
```

### Network Troubleshooting

1. **Check for port conflicts:**
```bash
sudo lsof -i -P -n | grep -E ':(8000|8501|5000|80|443)'
```

2. **View Nginx error logs:**
```bash
sudo tail -f /var/log/nginx/error.log
```

3. **Test SSL certificate validity:**
```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

4. **Check firewall status for web ports:**
```bash
sudo ufw status | grep -E '(8000|8501|80|443)'
```

5. **Monitor network traffic on web ports:**
```bash
sudo tcpdump -i any port 8501 -n
```

### Performance Monitoring

1. **Check API response times:**
```bash
for i in {1..10}; do curl -s -w "\n%{time_total}s\n" -o /dev/null http://localhost:8000/health; done
```

2. **Monitor system resources:**
```bash
htop -p $(pgrep -f "api.py|streamlit|scanner_service" | tr '\n' ',')
```

3. **Check for slow database queries:**
```bash
tail -f web/logs/db_queries.log | grep "slow query"
```

### Firewall & Security Status

1. **Check UFW firewall status:**
```bash
sudo ufw status verbose
```

2. **Verify specific port rules:**
```bash
sudo ufw status | grep -E '(8000|8501|80|443)'
```

3. **List all listening ports and applications:**
```bash
sudo netstat -tulpn
```

4. **Check for unauthorized SSH login attempts:**
```bash
sudo grep "Failed password" /var/log/auth.log | tail -n 20
```

5. **Monitor real-time login attempts:**
```bash
sudo tail -f /var/log/auth.log | grep "authentication"
```

6. **Check SSL certificate expiration:**
```bash
openssl x509 -enddate -noout -in web/ssl/cert.pem
```

7. **Verify SSL certificate strength:**
```bash
openssl x509 -text -noout -in web/ssl/cert.pem | grep "Signature Algorithm"
```

8. **Scan for open ports from external perspective:**
```bash
nmap -sT -p 80,443,8000,8501 localhost
```

9. **Check Nginx security headers:**
```bash
curl -s -I https://your-domain.com | grep -E '(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)'
```

10. **Verify file permissions:**
```bash
ls -la web/ssl/ web/users.json
```

11. **Check for recent security events:**
```bash
sudo journalctl -p err..emerg -n 50 --no-pager
```

12. **Verify running processes:**
```bash
ps aux | grep -v grep | grep -E '(api.py|streamlit|scanner_service|nginx)'
```

## Security Features

### Authentication & Encryption
- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt password hashing
- **HTTPS/SSL**: Encrypted connections with Let's Encrypt certificates
- **CORS Protection**: Cross-origin request security
- **Security Headers**: XSS, CSRF, and clickjacking protection
- **Rate Limiting**: API request throttling (configurable)

### Fail2Ban Protection

The MarketResearcher web interface includes Fail2Ban protection to prevent brute force attacks and unauthorized access attempts.

#### Protection Features

- **SSH Protection**: Blocks IPs after 3 failed login attempts within 10 minutes (1-hour ban)
- **Nginx HTTP Auth**: Blocks IPs after 3 authentication failures (1-hour ban)
- **API Protection**: Blocks IPs after 5 failed login attempts to the API (1-hour ban)
- **UI Protection**: Blocks IPs after 5 suspicious requests to the Streamlit UI (1-hour ban)

#### Activating Fail2Ban Protection

```bash
# Simple SSH-only protection
# sudo ./web/setup_simple_fail2ban.sh

# Enhanced protection (recommended)
# sudo ./web/setup_enhanced_fail2ban.sh
```

#### Managing Fail2Ban

```bash
# Check Fail2Ban status
sudo fail2ban-client status

# Check specific jail status
sudo fail2ban-client status sshd

# Unban an IP address
sudo fail2ban-client set sshd unbanip YOUR_LOCAL_IP

# Stop Fail2Ban service
sudo systemctl stop fail2ban

# Start Fail2Ban service
sudo systemctl start fail2ban

# Reload Fail2Ban configuration
sudo fail2ban-client reload
```

#### Log Files

Fail2Ban monitors the following log files:
- SSH: `/var/log/auth.log`
- Nginx: `/var/log/nginx/error.log`
- API: `./web/logs/api_access.log`
- UI: `./web/logs/streamlit_access.log`

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/verify` - Verify token

### Analysis
- `POST /analysis/stock` - Analyze stock symbol
- `POST /analysis/crypto` - Analyze cryptocurrency
- `GET /analysis/status/{task_id}` - Get analysis status

### Portfolio
- `GET /portfolio` - Get user portfolio
- `POST /portfolio/position` - Add position
- `DELETE /portfolio/position/{symbol}` - Remove position

### System
- `GET /health` - Health check

### Nginx restart commands
- `sudo systemctl reload nginx`

or

- `sudo systemctl restart nginx`


## Configuration

### Environment Variables

Create a `.env` file in the web directory:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# API Configuration  
API_HOST=0.0.0.0
API_PORT=8000

# MarketResearcher Configuration
FINNHUB_API_KEY=your-finnhub-key
BINANCE_API_KEY=your-binance-key
BINANCE_SECRET_KEY=your-binance-secret
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
POLYGON_API_KEY=your-polygon-key

# LLM Configuration
LLM_ENDPOINT=http://localhost:11434
LLM_MODEL=llama2
```

### User Management

**IMPORTANT**: No users are pre-configured in this release for security reasons.

#### Initial Setup

1. **Start the web application**:
   ```bash
   ./web/start_web.sh
   ```

2. **Access the web interface** at http://localhost:8501

3. **Create your first user** - The system will guide you through:
   - Setting up the admin account
   - Creating additional users
   - Configuring permissions

#### Adding Users Programmatically

```python
from web.auth import UserManager
user_manager = UserManager()
user_manager.create_user("username", "secure_password", "email@example.com")
```

#### Security Best Practices

- **Change default credentials immediately** after first setup
- **Use strong passwords** (minimum 12 characters with mixed case, numbers, symbols)
- **Remove admin account** after initial setup if not needed
- **Regular user account audits** recommended

#### User Database Location

Users are stored in `web/users.json` (automatically created when first user is added).

## SSL Setup

For production deployment, place SSL certificates in `web/ssl/`:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

Generate self-signed certificates for testing:
```bash
mkdir -p web/ssl
openssl req -x509 -newkey rsa:4096 -keyout web/ssl/key.pem -out web/ssl/cert.pem -days 365 -nodes
```

## Customization

### Adding New Analysis Types

1. **Add API endpoint in `api.py`:**
```python
@app.post("/analysis/forex")
async def analyze_forex(request: AnalysisRequest, ...):
    # Implementation
```

2. **Add UI page in `streamlit_app.py`:**
```python
def forex_analysis_page(self):
    # Implementation
```

3. **Update navigation menu**

### Custom Authentication

Replace the `UserManager` class in `auth.py` with your preferred authentication system (LDAP, OAuth2, etc.).

## Monitoring

### Health Checks
- API health: `GET /health`
- Service status via Docker: `docker-compose ps`

### Logs
- API logs: `docker-compose logs api`
- Frontend logs: `docker-compose logs frontend`
- Nginx logs: `docker-compose logs nginx`

## Troubleshooting

### Common Issues

1. **Connection refused errors:**
   - Check if services are running: `docker-compose ps`
   - Verify port availability: `netstat -tulpn | grep :8000`

2. **Authentication failures:**
   - Check JWT secret key configuration
   - Verify user credentials in `users.json`

3. **SSL certificate errors:**
   - Ensure certificates exist in `web/ssl/`
   - Check certificate validity: `openssl x509 -in cert.pem -text -noout`

4. **MarketResearcher initialization errors:**
   - Check API keys in environment variables
   - Verify LLM endpoint accessibility
   - Review logs: `docker-compose logs api`

5. Nginx server issues
   - Restart,   sudo systemctl restart nginx

## Development

### Running Tests
```bash
pytest web/tests/
```

### Code Style
```bash
black web/
flake8 web/
```

### Adding Dependencies
Update `requirements_web.txt` and rebuild containers:
```bash
docker-compose build
docker-compose up -d
```

## Production Deployment

### Recommended Setup

1. **Use proper SSL certificates** (Let's Encrypt)
2. **Configure firewall** (UFW/iptables)
3. **Set up monitoring** (Prometheus/Grafana)
4. **Enable log rotation**
5. **Regular backups** of user data and configurations
6. **Update security headers** in Nginx configuration

### Scaling

For high-traffic deployments:
- Use multiple API worker processes
- Implement Redis for session storage
- Add load balancing with multiple API instances
- Use database instead of JSON file for user storage

## License

This web interface is part of the MarketResearcher project and follows the same licensing terms.
