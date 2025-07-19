# Spotify Remote Control

A Python web application that allows you to control your desktop Spotify client remotely from any device on your network. This app acts as a remote control - it doesn't play music itself, but controls playback on your desktop Spotify client.

## Features

- 🎵 **Play/Pause** - Control playback on your desktop Spotify
- ⏭️ **Next/Previous** - Skip tracks or go back
- 🔊 **Volume Control** - Adjust volume remotely
- ⏱️ **Seek Control** - Click on progress bar to jump to any position
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔄 **Real-time Updates** - Live track information and playback status
- 🌐 **Network Access** - Control from any device on your network

## Prerequisites

- Python 3.7 or higher
- A Spotify account
- Spotify desktop client installed and running on your computer
- Spotify Developer account (free)

## Setup Instructions

### Option 1: Docker (Recommended)

#### Prerequisites
- Docker and Docker Compose installed
- Spotify Developer account

#### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in the app details:
   - **App name**: Spotify Remote Control (or any name you prefer)
   - **App description**: Remote control for Spotify desktop client
   - **Redirect URI**: `https://your-tailscale.endpoint.ts.net:5000/callback`
5. Click "Save"
6. Copy your **Client ID** and **Client Secret**

#### 2. Configure Environment Variables

1. Copy `env_example.txt` to `.env`:
   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` and add your Spotify credentials:
   ```
   SPOTIFY_CLIENT_ID=your_actual_client_id_here
   SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
   SECRET_KEY=any_random_string_here
   REDIRECT_URI=https://your-tailscale.endpoint.ts.net:5000/callback
   ```

#### 3. Build and Run with Docker

**Windows (PowerShell):**
```powershell
.\docker-run.ps1
```

**Linux/Mac:**
```bash
chmod +x docker-build.sh
./docker-build.sh
```

**Manual Docker commands:**
```bash
# Build the image
docker build -t spotify-remote:latest .

# Run with docker-compose
docker-compose up -d
```

### Option 2: Local Development

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Follow the same steps as Docker setup above.

#### 3. Run the Application

```bash
python app.py
```

The app will start on `http://localhost:5000`

## Usage

### First Time Setup

1. Open your browser and go to `http://localhost:5000` (or your Tailscale URL)
2. Click "Connect with Spotify"
3. Authorize the app with your Spotify account
4. You'll be redirected back to the control interface

## Docker Management

### Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Restart the container
docker-compose restart

# Update and restart
docker-compose pull && docker-compose up -d

# View container status
docker-compose ps

# Access container shell (for debugging)
docker-compose exec spotify-remote bash
```

### Production Deployment

For production use, use the production compose file:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This includes additional security settings:
- Read-only filesystem
- Dropped capabilities
- No new privileges
- Health checks

### Controlling Spotify

- **Play/Pause**: Click the large play/pause button
- **Next Track**: Click the forward button
- **Previous Track**: Click the backward button
- **Volume**: Use the volume slider
- **Seek**: Click anywhere on the progress bar to jump to that position

### Accessing from Other Devices

To control Spotify from your laptop or other devices:

1. Find your computer's IP address:
   - **Windows**: Run `ipconfig` in Command Prompt
   - **Mac/Linux**: Run `ifconfig` or `ip addr` in Terminal

2. On your laptop, open a browser and go to:
   ```
   http://YOUR_COMPUTER_IP:5000
   ```
   (Replace `YOUR_COMPUTER_IP` with your actual IP address)

3. You'll see the same control interface and can control Spotify remotely

## How It Works

This app uses the Spotify Web API to:
- Read the current playback state from your desktop Spotify client
- Send control commands (play, pause, skip, etc.) to your desktop client
- Display real-time track information and progress

The app doesn't play any music itself - it only controls your existing Spotify desktop client. This means:
- ✅ No duplicate playback
- ✅ Works with your existing playlists and library
- ✅ Maintains your current queue
- ✅ Uses your desktop's audio output

## Troubleshooting

### "No active playback found"
- Make sure Spotify desktop client is running
- Make sure music is playing or paused (not stopped)
- Try refreshing the page

### "Not authenticated" error
- Your session may have expired
- Go back to `http://localhost:5000` and re-authenticate

### Can't access from other devices
- Make sure your firewall allows connections on port 5000
- Check that both devices are on the same network
- Try using your computer's local IP address instead of localhost

### Volume control not working
- Some Spotify clients may not support remote volume control
- Try controlling volume directly on your desktop Spotify client

## Security Notes

- This app runs locally on your network
- Spotify credentials are stored locally and not shared
- The app only requests the minimum permissions needed for playback control
- For production use, consider adding authentication to the web interface

## Development

To modify or extend the app:

- **Backend**: Edit `app.py` to add new API endpoints
- **Frontend**: Edit templates in the `templates/` folder
- **Styling**: Modify the CSS in `templates/base.html`

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests! 