#!/bin/bash

# MarketResearcher Web Interface Startup Script

echo "🚀 Starting MarketResearcher Web Interface..."

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
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Set environment variables
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")}

echo "🌐 Starting services..."

# Start API server in background
echo "🔧 Starting FastAPI server on port 8000..."
python api.py &
API_PID=$!

# Wait for API to start
sleep 3

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend on port 8501..."
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

echo ""
echo "✅ MarketResearcher Web Interface is running!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend (Local):  http://localhost:8501"
echo "   Frontend (Network): http://your-server-ip:8501"
echo "   API (Local):       http://localhost:8000"
echo "   API (Network):     http://your-server-ip:8000"
echo "   API Docs:          http://your-server-ip:8000/docs"
echo ""
echo "🔐 Default Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📋 Process IDs:"
echo "   API Server:  $API_PID"
echo "   Streamlit:   $STREAMLIT_PID"
echo ""
echo "🛑 To stop services:"
echo "   kill $API_PID $STREAMLIT_PID"
echo "   or press Ctrl+C"

# Wait for user interrupt
trap "echo '🛑 Stopping services...'; kill $API_PID $STREAMLIT_PID 2>/dev/null; exit 0" INT

# Keep script running
wait
