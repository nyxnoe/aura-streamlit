#!/bin/bash

echo "=========================================="
echo "   AURA Backend API Server"
echo "=========================================="
echo ""

# Set the port from Render's environment variable (defaults to 5000 if not set)
PORT=${PORT:-5000}

echo "Starting Flask API server on port $PORT..."
echo ""

# Change to backend directory
cd backend || {
    echo "❌ Error: backend directory not found"
    echo "Current directory: $(pwd)"
    echo "Contents: $(ls -la)"
    exit 1
}

echo "✅ Changed to backend directory"
echo "Contents: $(ls -la)"
echo ""

# Check if api_server.py exists
if [ ! -f "api_server.py" ]; then
    echo "❌ Error: api_server.py not found in backend directory"
    exit 1
fi

echo "✅ Found api_server.py"
echo ""

# Create outputs directory if it doesn't exist
mkdir -p outputs
echo "✅ Created/verified outputs directory"
echo ""

# Run the Flask API server with Gunicorn (production server)
echo "🚀 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT \
         --workers 2 \
         --threads 4 \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         --log-level info \
         api_server:app