#!/bin/bash

# Start script for Spotify Remote with Tailscale support

echo "🚀 Starting Spotify Remote..."

# Check if we're in Tailscale mode (domain contains .ts.net)
if [[ "$DOMAIN_NAME" == *".ts.net"* ]]; then
    echo "🔍 Tailscale mode detected"
    
    # Check if Tailscale auth key is provided
    if [ -n "$TAILSCALE_AUTH_KEY" ]; then
        echo "🔗 Setting up Tailscale..."
        
        # Start Tailscale daemon
        tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
        TAILSCALED_PID=$!
        
        # Wait for daemon to start
        sleep 2
        
        # Authenticate with Tailscale
        tailscale up --authkey="$TAILSCALE_AUTH_KEY" --hostname="$TAILSCALE_HOSTNAME" --advertise-tags=tag:spotify-remote
        
        if [ $? -eq 0 ]; then
            echo "✅ Tailscale connected successfully"
        else
            echo "❌ Failed to connect to Tailscale"
            exit 1
        fi
    else
        echo "❌ Tailscale mode enabled but no auth key provided"
        echo "💡 Set TAILSCALE_AUTH_KEY environment variable"
        exit 1
    fi
else
    echo "🌐 Standard mode (no Tailscale needed)"
fi

# Start the Flask application
echo "🎵 Starting Spotify Remote app..."
exec python app.py 