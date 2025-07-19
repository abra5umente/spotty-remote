# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Tailscale in one layer
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
    gnupg \
    && curl -fsSL https://pkgs.tailscale.com/stable/debian/bullseye.noarmor.gpg | tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null \
    && curl -fsSL https://pkgs.tailscale.com/stable/debian/bullseye.tailscale-keyring.list | tee /etc/apt/sources.list.d/tailscale.list \
    && apt-get update \
    && apt-get install -y tailscale \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create startup script and user in one layer
RUN echo '#!/bin/bash\n\
echo "🚀 Starting Spotify Remote..."\n\
if [[ "$DOMAIN_NAME" == *".ts.net"* ]]; then\n\
    echo "🔍 Tailscale mode detected"\n\
    if [ -n "$TAILSCALE_AUTH_KEY" ]; then\n\
        echo "🔗 Setting up Tailscale..."\n\
        tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &\n\
        sleep 2\n\
        tailscale up --authkey="$TAILSCALE_AUTH_KEY" --hostname="$TAILSCALE_HOSTNAME" --advertise-tags=tag:spotify-remote\n\
        if [ $? -eq 0 ]; then\n\
            echo "✅ Tailscale connected successfully"\n\
        else\n\
            echo "❌ Failed to connect to Tailscale"\n\
            exit 1\n\
        fi\n\
    else\n\
        echo "❌ Tailscale mode enabled but no auth key provided"\n\
        exit 1\n\
    fi\n\
else\n\
    echo "🌐 Standard mode (no Tailscale needed)"\n\
fi\n\
echo "🎵 Starting Spotify Remote app..."\n\
exec python app.py' > /app/start.sh \
    && chmod +x /app/start.sh \
    && useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/.cache \
    && chown -R app:app /app

# Expose port and set health check
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Switch to app user and run the startup script
USER app
CMD ["./start.sh"] 