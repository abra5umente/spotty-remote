# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Tailscale
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
    gnupg \
    && curl -fsSL https://pkgs.tailscale.com/stable/debian/bullseye.noarmor.gpg | tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null \
    && curl -fsSL https://pkgs.tailscale.com/stable/debian/bullseye.tailscale-keyring.list | tee /etc/apt/sources.list.d/tailscale.list \
    && apt-get update \
    && apt-get install -y tailscale \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create startup script with proper line endings
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "🚀 Starting Spotify Remote..."' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'if [[ "$DOMAIN_NAME" == *".ts.net"* ]]; then' >> /app/start.sh && \
    echo '    echo "🔍 Tailscale mode detected"' >> /app/start.sh && \
    echo '    if [ -n "$TAILSCALE_AUTH_KEY" ]; then' >> /app/start.sh && \
    echo '        echo "🔗 Setting up Tailscale..."' >> /app/start.sh && \
    echo '        tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &' >> /app/start.sh && \
    echo '        sleep 2' >> /app/start.sh && \
    echo '        tailscale up --authkey="$TAILSCALE_AUTH_KEY" --hostname="$TAILSCALE_HOSTNAME" --advertise-tags=tag:spotify-remote' >> /app/start.sh && \
    echo '        if [ $? -eq 0 ]; then' >> /app/start.sh && \
    echo '            echo "✅ Tailscale connected successfully"' >> /app/start.sh && \
    echo '        else' >> /app/start.sh && \
    echo '            echo "❌ Failed to connect to Tailscale"' >> /app/start.sh && \
    echo '            exit 1' >> /app/start.sh && \
    echo '        fi' >> /app/start.sh && \
    echo '    else' >> /app/start.sh && \
    echo '        echo "❌ Tailscale mode enabled but no auth key provided"' >> /app/start.sh && \
    echo '        exit 1' >> /app/start.sh && \
    echo '    fi' >> /app/start.sh && \
    echo 'else' >> /app/start.sh && \
    echo '    echo "🌐 Standard mode (no Tailscale needed)"' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "🎵 Starting Spotify Remote app..."' >> /app/start.sh && \
    echo 'exec python app.py' >> /app/start.sh && \
    chmod +x /app/start.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/.cache \
    && chown -R app:app /app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Switch to app user and run the startup script
USER app
CMD ["./start.sh"] 