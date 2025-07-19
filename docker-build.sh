#!/bin/bash

# Spotify Remote Control - Docker Build Script

set -e

echo "🐳 Building Spotify Remote Control Docker container..."
echo "=================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your Spotify credentials:"
    echo "SPOTIFY_CLIENT_ID=your_client_id"
    echo "SPOTIFY_CLIENT_SECRET=your_client_secret"
    echo "SECRET_KEY=your_secret_key"
    echo "REDIRECT_URI=https://abra5dt-win.skink-broadnose.ts.net:5000/callback"
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
if [ -z "$SPOTIFY_CLIENT_ID" ] || [ -z "$SPOTIFY_CLIENT_SECRET" ] || [ -z "$SECRET_KEY" ]; then
    echo "❌ Missing required environment variables!"
    echo "Please check your .env file contains:"
    echo "- SPOTIFY_CLIENT_ID"
    echo "- SPOTIFY_CLIENT_SECRET"
    echo "- SECRET_KEY"
    exit 1
fi

echo "✅ Environment variables loaded"

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t spotify-remote:latest .

echo "✅ Docker image built successfully!"

# Run with docker-compose
echo "🚀 Starting container with docker-compose..."
docker-compose up -d

echo "✅ Container started!"
echo ""
echo "📱 Access your app at:"
echo "   Local: https://localhost:5000"
echo "   Tailscale: https://abra5dt-win.skink-broadnose.ts.net:5000"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Update: docker-compose pull && docker-compose up -d" 