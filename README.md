# Spotify Remote Control

A simple web app to control your desktop Spotify client remotely. Works over your host's Tailscale network for secure access from anywhere.

## Features

- 🎵 **Play/Pause** - Control playback on your desktop Spotify
- ⏭️ **Next/Previous** - Skip tracks or go back
- 🔊 **Volume Control** - Adjust volume remotely
- ⏱️ **Seek Control** - Click progress bar to jump to any position
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔒 **Secure Access** - Uses your host's Tailscale for HTTPS and network access
- 🚀 **Ultra Simple** - No complex setup, uses what's already working

## Quick Start

### 1. Setup Tailscale on Your Host

Make sure Tailscale is running on your host machine:

```bash
# Install Tailscale (if not already installed)
# Then connect:
tailscale up --authkey=your-auth-key
```

### 2. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy your **Client ID** and **Client Secret**

### 3. Configure Environment

```bash
cp env_example.txt .env
```

Edit `.env`:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=any_random_string_here
PORT=5000
```

### 4. Run with Docker

```bash
docker-compose up -d
```

The app will:
- Automatically detect your Tailscale hostname
- Set up the correct Spotify redirect URI
- Run the web interface on HTTPS

Access your app at: `https://your-tailscale-hostname:5000`

## How It Works

- **Host-based Tailscale**: Uses your host's existing Tailscale installation
- **Automatic detection**: Discovers your Tailscale hostname automatically
- **Dynamic redirect URI**: Sets correct Spotify callback URL based on your hostname
- **Zero complexity**: No container Tailscale, no daemon management, no auth keys

## Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart
```

## Usage

1. Open your app URL in a browser (shown in startup logs)
2. Click "Connect with Spotify"
3. Authorize the app
4. Control your desktop Spotify remotely

## Troubleshooting

**"Tailscale not connected"**
- Make sure Tailscale is running on your host: `tailscale status`
- Connect to Tailscale: `tailscale up --authkey=your-auth-key`

**"No active playback found"**
- Make sure Spotify desktop client is running
- Make sure music is playing or paused

**"Not authenticated"**
- Re-authenticate with Spotify

**"Failed to get Tailscale status"**
- Ensure Tailscale CLI is available on your host
- Check Tailscale is properly installed and running

## Architecture

This app follows the **KISS principle**:

- ✅ **No container Tailscale** - uses host's working installation
- ✅ **No daemon management** - host handles everything
- ✅ **No privileged containers** - standard security
- ✅ **No auth key management** - host manages authentication
- ✅ **Automatic hostname** - uses whatever hostname you have
- ✅ **Works immediately** - no setup, no waiting

## License

MIT License 