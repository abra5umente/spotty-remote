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
- 🔒 **HTTPS Support** - Secure connections with Let's Encrypt or Tailscale

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
   - **Redirect URI**: Choose based on your setup (see HTTPS options below)
5. Click "Save"
6. Copy your **Client ID** and **Client Secret**

#### 2. Choose Your HTTPS Setup

**Option A: Let's Encrypt (Recommended for Production)**
- ✅ Free, trusted certificates
- ✅ Works with any domain
- ✅ Automatic renewal
- ❌ Requires domain name and port 80 access

**Option B: Tailscale (Easy Setup)**
- ✅ No domain required
- ✅ Automatic HTTPS
- ✅ Works across networks
- ❌ Requires Tailscale account

**Option C: HTTP Only (Development)**
- ✅ Simple setup
- ❌ Not secure
- ❌ Spotify may reject in production

#### 3. Configure Environment Variables

1. Copy `env_example.txt` to `.env`:
   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` based on your chosen setup:

   **For Let's Encrypt (Option A):**
   ```
   SPOTIFY_CLIENT_ID=your_actual_client_id_here
   SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
   SECRET_KEY=any_random_string_here
   USE_HTTPS=true
   DOMAIN_NAME=your-domain.com
   REDIRECT_URI=https://your-domain.com:5000/callback
   ```

   **For Tailscale (Option B):**
   ```
   SPOTIFY_CLIENT_ID=your_actual_client_id_here
   SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
   SECRET_KEY=any_random_string_here
   USE_HTTPS=true
   DOMAIN_NAME=your-tailscale-endpoint.ts.net
   REDIRECT_URI=https://your-tailscale-endpoint.ts.net:5000/callback
   ```

   **For HTTP Development (Option C):**
   ```
   SPOTIFY_CLIENT_ID=your_actual_client_id_here
   SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
   SECRET_KEY=any_random_string_here
   USE_HTTPS=false
   REDIRECT_URI=http://localhost:5000/callback
   ```

#### 4. Set Up HTTPS (If Using Let's Encrypt)

If you chose Option A (Let's Encrypt), run the setup script:

```bash
python setup_letsencrypt.py
```

This will:
- Install certbot (if needed)
- Generate certificates for your domain
- Set up automatic renewal
- Update your `.env` file

**Requirements for Let's Encrypt:**
- Domain name pointing to your server
- Port 80 accessible from the internet
- Root/sudo access on your server

#### 5. Build and Run with Docker

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

#### 3. Set Up HTTPS (If Using Let's Encrypt)

If you chose Option A (Let's Encrypt), run the setup script:

```bash
python setup_letsencrypt.py
```

#### 4. Run the Application

```bash
python app.py
```

The app will start on:
- **HTTP**: `http://localhost:5000`
- **HTTPS**: `https://localhost:5000` or `https://your-domain.com:5000`

## Usage

### First Time Setup

1. Open your browser and go to your app URL:
   - **HTTP**: `http://localhost:5000`
   - **HTTPS**: `https://localhost:5000` or `https://your-domain.com:5000`
2. Click "Connect with Spotify"
3. Authorize the app with your Spotify account
4. You'll be redirected back to the control interface

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

## HTTPS Setup Options

### Option A: Let's Encrypt (Production)

**Best for:** Production servers with domain names

**Setup:**
1. Have a domain name pointing to your server
2. Ensure port 80 is accessible from the internet
3. Run: `python setup_letsencrypt.py`
4. Follow the prompts to generate certificates

**Benefits:**
- Free, trusted certificates
- Automatic renewal
- Industry standard
- Works with any domain

### Option B: Tailscale (Easy)

**Best for:** Personal use, quick setup

**Setup:**
1. Install Tailscale on your server
2. Get your Tailscale endpoint URL
3. Use that URL in your `.env` file
4. Update your Spotify app's redirect URI

**Benefits:**
- No domain required
- Automatic HTTPS
- Works across networks
- Simple setup

### Option C: HTTP Only (Development)

**Best for:** Local development only

**Setup:**
1. Use `USE_HTTPS=false` in your `.env`
2. Use `http://localhost:5000/callback` as redirect URI

**Limitations:**
- Not secure
- May not work with Spotify in production
- Only for development/testing

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
- Go back to your app URL and re-authenticate

### Can't access from other devices
- Make sure your firewall allows connections on port 5000
- Check that both devices are on the same network
- Try using your computer's local IP address instead of localhost

### Volume control not working
- Some Spotify clients may not support remote volume control
- Try controlling volume directly on your desktop Spotify client

### Docker issues
- Make sure Docker and Docker Compose are installed and running
- Check that the `.env` file exists and contains all required variables
- View logs with `docker-compose logs -f` for error details

### HTTPS/SSL issues
- **Let's Encrypt**: Make sure port 80 is open and domain points to your server
- **Tailscale**: Check that Tailscale is running and connected
- **Self-signed certs**: Accept the security warning in your browser
- Check certificate renewal: `./renew_cert.sh`

### Certificate renewal issues
- Check if certbot is installed: `certbot --version`
- Manually renew: `certbot renew`
- Check cron job: `crontab -l`
- View renewal logs: `journalctl -u certbot.timer`

## Security Notes

- This app runs locally on your network
- Spotify credentials are stored locally and not shared
- The app only requests the minimum permissions needed for playback control
- HTTPS is recommended for production use
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