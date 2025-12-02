#!/bin/bash

# MarketResearcher Web Interface Network Startup Script
# Optimized for local network access

echo "🚀 Starting MarketResearcher Web Interface for Local Network..."

# Get local IP address
LOCAL_IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -1)
echo "🌐 Local IP Address: $LOCAL_IP"

# Check if in web directory
if [ ! -f "requirements_web.txt" ]; then
    echo "📂 Changing to web directory..."
    cd web
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_web.txt
pip install -r ../requirements.txt

# Create necessary directories
mkdir -p ssl logs

# Generate self-signed SSL certificates if they don't exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo "🔐 Generating SSL certificates..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=$LOCAL_IP"
fi

# Set environment variables
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")}

echo "🌐 Starting services for network access..."

# Start API server in background
#echo "🔧 Starting FastAPI server on $LOCAL_IP:8000..."
#python api.py &
#API_PID=$!

# Wait for API to start
#sleep 3

# Start Streamlit frontend with network configuration
echo "🎨 Starting Streamlit frontend on $LOCAL_IP:8501..."
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --server.enableCORS false --server.enableXsrfProtection false &
STREAMLIT_PID=$!

echo ""
echo "✅ MarketResearcher Web Interface is running on your local network!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend (Local):   http://localhost:8501"
echo "   Frontend (Network): http://$LOCAL_IP:8501"
echo "   API (Local):        http://localhost:8000"
echo "   API (Network):      http://$LOCAL_IP:8000"
echo "   API Docs:           http://$LOCAL_IP:8000/docs"
echo ""
echo "📱 Mobile/Tablet Access:"
echo "   Use: http://$LOCAL_IP:8501"
echo ""
echo "🔐 Default Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🔧 Network Configuration:"
echo "   - CORS disabled for local network access"
echo "   - XSRF protection disabled for easier access"
echo "   - Server listening on all interfaces (0.0.0.0)"
echo ""
echo "📋 Process IDs:"
echo "   API Server:  $API_PID"
echo "   Streamlit:   $STREAMLIT_PID"
echo ""
echo "🛑 To stop services:"
echo "   kill $API_PID $STREAMLIT_PID"
echo "   or press Ctrl+C"
echo ""
echo "🔥 Share this URL with devices on your network:"
echo "   http://$LOCAL_IP:8501"

# Wait for user interrupt
trap "echo '🛑 Stopping services...'; kill $API_PID $STREAMLIT_PID 2>/dev/null; exit 0" INT

# Keep script running
wait
