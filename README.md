# Spotify Remote Control

A simple web app to control any Spotify device remotely. Uses ngrok to expose your local server publicly for secure remote access.

## Features

- 🎵 **Play/Pause** - Control playback on any Spotify device
- ⏭️ **Next/Previous** - Skip tracks or go back
- 🔊 **Volume Control** - Adjust volume remotely
- ⏱️ **Seek Control** - Click progress bar to jump to any position
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔒 **Secure Access** - Uses ngrok for HTTPS and public access
- 🚀 **Ultra Simple** - No complex setup, automatic ngrok integration
- 🎯 **Real-time Updates** - Live playback status and progress

## Quick Start

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy your **Client ID** and **Client Secret**

### 2. Get ngrok Authtoken

1. Sign up at [ngrok.com](https://ngrok.com)
2. Get your authtoken from [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)

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
NGROK_AUTHTOKEN=your_ngrok_authtoken_here
USE_NGROK=true
```

### 4. Run with Docker

```bash
docker-compose up -d
```

### 5. Setup and Access

1. Visit `http://localhost:5000` in your browser (or `http://your-hostname:5000` from other devices on your network)
2. Click "Start ngrok tunnel" to get a public URL
3. Add the callback URL to your Spotify app settings
4. Click "Continue to Spotify Remote"
5. Authorize with Spotify
6. Start controlling any Spotify device remotely!

**Note**: The app may also be accessible via Tailscale or other VPN solutions at `http://your-tailscale-hostname:5000`, but YMMV depending on your network configuration.

## How It Works

- **ngrok Integration**: Automatically starts ngrok tunnel for public HTTPS access
- **Dynamic Setup**: Web-based setup process guides you through configuration
- **Automatic Redirect URI**: Sets correct Spotify callback URL based on ngrok URL
- **Token Caching**: Remembers your Spotify authentication
- **Real-time Control**: Live updates of playback status and progress

## Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# Manual setup (alternative to web interface)
docker exec -it spotify-remote python app.py configure-app
```

## Manual Setup Alternative

If you prefer command-line setup:

```bash
# Start the container
docker-compose up -d

# Run manual setup
docker exec -it spotify-remote python app.py configure-app

# Follow the printed instructions to configure your Spotify app
```

## Usage

1. Open your app URL (shown in setup or logs)
2. Click "Connect with Spotify" (first time only)
3. Authorize the app
4. Control any Spotify device remotely from any device

## Limitations & Caveats

### Free Software Limitations

This app uses ngrok's free tier, which has some limitations:

- **Dynamic URLs**: Each time ngrok restarts, you get a new public URL
- **Re-authentication Required**: When the URL changes, you may need to re-authenticate with Spotify
- **Callback URI Updates**: You'll need to update your Spotify app's redirect URIs with the new URL

These limitations are inherent to using free tunneling services. For a more permanent solution, consider:
- Using ngrok's paid plans with custom domains
- Setting up your own reverse proxy with a static domain
- Using other tunneling services with persistent URLs

## Troubleshooting

**"Ngrok not started"**
- Make sure `NGROK_AUTHTOKEN` is set in your `.env` file
- Check ngrok authtoken is valid at [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)

**"No active playback found"**
- Make sure a Spotify device is active and playing music
- Make sure music is playing or paused

**"Not authenticated"**
- Re-authenticate with Spotify by visiting the app URL

**"Callback URI mismatch"**
- Update your Spotify app's redirect URIs with the new ngrok URL
- The URL changes each time ngrok restarts

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SPOTIFY_CLIENT_ID` | Your Spotify app client ID | Required |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify app client secret | Required |
| `SECRET_KEY` | Flask secret key (any random string) | Required |
| `PORT` | Port to run the app on | `5000` |
| `NGROK_AUTHTOKEN` | Your ngrok authtoken | Required |
| `USE_NGROK` | Enable/disable ngrok | `true` |
| `FORCE_SETUP` | Force setup page to show | `false` |

## Architecture

This app follows the **KISS principle**:

- ✅ **Simple ngrok integration** - automatic tunnel creation
- ✅ **Web-based setup** - guided configuration process
- ✅ **Token persistence** - remembers authentication
- ✅ **Real-time updates** - live playback status
- ✅ **Responsive design** - works on all devices
- ✅ **Docker ready** - easy deployment

## Roadmap

### 🚀 Upcoming Features

1. **PWA Implementation**
   - Progressive Web App support
   - Install as native app
   - Push notifications for track changes

2. **Permanent HTTPS Solution**
   - Replace ngrok with more permanent solution (or you can just pay for ngrok, idk)
   - Custom domain support
   - SSL certificate management
   - Better persistence

### 🔮 Future Plans

- **Playlist Management** - Browse and control playlists
- **Device Selection** - Choose which Spotify device to control
- **Queue Management** - View and modify playback queue

---

🙏 **Dear Spotify:** This is a personal, non-commercial project. Please don't sue me, thanks! 💚

## License

MIT License 

## Known Bugs

- **ngrok tunnel status on setup page**: When you open the setup page, you may see a message that the ngrok tunnel has failed to start, even though it is actually running. This is a cosmetic issue and does not affect functionality. It is being worked on and will be fixed in a future update. 