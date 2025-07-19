# Spotify Remote Control

A simple web app to control your desktop Spotify client remotely. Works exclusively over Tailscale for secure access from anywhere.

## Features

- 🎵 **Play/Pause** - Control playback on your desktop Spotify
- ⏭️ **Next/Previous** - Skip tracks or go back
- 🔊 **Volume Control** - Adjust volume remotely
- ⏱️ **Seek Control** - Click progress bar to jump to any position
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔒 **Secure Access** - Uses Tailscale for HTTPS and network access
- 🤖 **Auto Setup** - Automatically generates unique hostname and connects to Tailscale

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
TAILSCALE_AUTH_KEY=tskey-auth-xxxxxxxxx
TAILSCALE_HOSTNAME=spotify-remote
```

### 4. Run with Docker

```bash
docker-compose up -d
```

The app will:
- Generate a unique hostname (e.g., `spotify-remote-a1b2c3d4`)
- Connect to Tailscale automatically
- Set up the correct Spotify redirect URI
- Run the web interface on HTTPS

Access your app at: `https://your-generated-hostname.ts.net:5000`

## How It Works

- **Tailscale-only**: The app connects directly to Tailscale and uses only the Tailscale network
- **Auto hostname**: Generates unique hostname to avoid conflicts
- **Dynamic redirect URI**: Automatically sets correct Spotify callback URL
- **No manual configuration**: Everything is handled automatically

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

## Usage

1. Open your app URL in a browser (shown in startup logs)
2. Click "Connect with Spotify"
3. Authorize the app
4. Control your desktop Spotify remotely

## Troubleshooting

**"TAILSCALE_AUTH_KEY is required"**
- Make sure you've set the auth key in your `.env` file

**"Failed to connect to Tailscale"**
- Check your auth key is correct
- Verify Tailscale network is accessible

**"No active playback found"**
- Make sure Spotify desktop client is running
- Make sure music is playing or paused

**"Not authenticated"**
- Re-authenticate with Spotify

## License

MIT License 