#!/bin/bash

# Start Scanner Service - Isolated IB scanner process
echo "🔍 Starting Scanner Service..."

# Check if already running
if pgrep -f "scanner_service.py" > /dev/null; then
    echo "⚠️  Scanner service already running"
    exit 1
fi

# Navigate to web directory
cd "$(dirname "$0")"

# Activate conda environment if it exists
if [[ -n "$CONDA_PREFIX" ]]; then
    echo "🐍 Using active conda environment: $CONDA_DEFAULT_ENV"
else
    echo "🐍 Activating marketresearcher conda environment..."
    # Try to activate conda environment
    if command -v conda &> /dev/null; then
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate marketresearcher
    else
        echo "⚠️  Conda not found. Using system Python."
    fi
fi

# Install Flask if not already installed
if ! python -c "import flask" &> /dev/null; then
    echo "💾 Installing Flask dependency..."
    pip install flask
fi

# Start scanner service
echo "🚀 Starting scanner service on port 5000..."
python scanner_service.py &
SCANNER_PID=$!

echo "✅ Scanner service started with PID: $SCANNER_PID"
echo "📡 Service available at: http://localhost:5000"
echo "🔍 Health check: curl http://localhost:5000/health"
echo ""
echo "To stop: kill $SCANNER_PID"

# Wait for service to start
sleep 2

# Test health check
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Scanner service is healthy"
else
    echo "❌ Scanner service health check failed"
fi
