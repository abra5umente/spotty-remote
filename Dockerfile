# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and ngrok
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install ngrok
RUN wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip \
    && unzip ngrok-v3-stable-linux-amd64.zip \
    && mv ngrok /usr/local/bin/ \
    && rm ngrok-v3-stable-linux-amd64.zip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create user and cache directory
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/.cache \
    && chown -R app:app /app

# Expose port and set health check
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Switch to app user and run the app directly
USER app
CMD ["python", "app.py"] 