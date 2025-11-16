#!/bin/bash

echo "=========================================="
echo "   AURA - Intelligent Research Assistant"
echo "=========================================="
echo ""

# Set the port from Render's environment variable (defaults to 8501 if not set)
PORT=${PORT:-8501}

echo "Starting AURA on port $PORT..."
echo ""

# Run Streamlit with the correct configuration for Render
streamlit run ai-services/app_v2.py \
  --server.port=$PORT \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false