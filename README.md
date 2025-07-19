# Spotify Remote Control

A simple web app to control your desktop Spotify client remotely. Works over Tailscale for secure access from anywhere.

## Features

- 🎵 **Play/Pause** - Control playback on your desktop Spotify
- ⏭️ **Next/Previous** - Skip tracks or go back
- 🔊 **Volume Control** - Adjust volume remotely
- ⏱️ **Seek Control** - Click progress bar to jump to any position
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔒 **Secure Access** - Uses Tailscale for HTTPS and network access

## Quick Start

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy your **Client ID** and **Client Secret**

### 2. Get Tailscale Auth Key

1. Go to [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
2. Generate a new auth key
3. Copy the key

### 3. Configure Environment

```bash
cp env_example.txt .env
```

Edit `.env`:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=any_random_string_here
DOMAIN_NAME=your-hostname.ts.net
TAILSCALE_AUTH_KEY=tskey-auth-xxxxxxxxx
TAILSCALE_HOSTNAME=spotify-remote
```

### 4. Run with Docker

```bash
docker-compose up -d
```

The app will:
- Start Tailscale in the container
- Connect to your Tailscale network
- Run the web interface on HTTPS

Access your app at: `https://your-hostname.ts.net:5000`

## Local Development

For local testing (no Tailscale needed):

```env
# Leave DOMAIN_NAME empty for local mode
DOMAIN_NAME=
REDIRECT_URI=http://localhost:5000/callback
```

```bash
pip install -r requirements.txt
python app.py
```

Access at: `http://localhost:5000`

## Usage

1. Open your app URL in a browser
2. Click "Connect with Spotify"
3. Authorize the app
4. Control your desktop Spotify remotely

## Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# Production mode
docker-compose -f docker-compose.prod.yml up -d
```

## How It Works

- Uses Spotify Web API to control your desktop client
- Tailscale provides secure HTTPS access from anywhere
- No music is played by the app - it only controls your existing Spotify
- Container includes its own Tailscale installation

## Troubleshooting

**"No active playback found"**
- Make sure Spotify desktop client is running
- Make sure music is playing or paused

**"Not authenticated"**
- Re-authenticate with Spotify

**Tailscale connection issues**
- Check your auth key is correct
- Verify Tailscale hostname is available

## License

MIT License 