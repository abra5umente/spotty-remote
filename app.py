from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import json
import ssl
import ipaddress
import subprocess
import threading
import time
from datetime import datetime, timedelta
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://localhost:5000/callback')

# HTTPS configuration (required by Spotify)
USE_HTTPS = os.getenv('USE_HTTPS', 'true').lower() == 'true'
DOMAIN_NAME = os.getenv('DOMAIN_NAME', '')
CERT_PATH = os.getenv('CERT_PATH', './certs')
PORT = int(os.getenv('PORT', 5000))

# Check if using Tailscale (has .ts.net domain)
IS_TAILSCALE = '.ts.net' in DOMAIN_NAME if DOMAIN_NAME else False

# Check if using Let's Encrypt (has cert files)
LETSENCRYPT_CERT = os.path.join(CERT_PATH, 'fullchain.pem')
LETSENCRYPT_KEY = os.path.join(CERT_PATH, 'privkey.pem')
IS_LETSENCRYPT = os.path.exists(LETSENCRYPT_CERT) and os.path.exists(LETSENCRYPT_KEY)

# Spotify OAuth scope - we need user-read-playback-state and user-modify-playback-state
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

def create_spotify_oauth():
    """Create Spotify OAuth object"""
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(os.getcwd(), '.cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=os.path.join(cache_dir, 'spotify_token_cache')
    )

def get_tailscale_hostname():
    """Get the current Tailscale hostname if Tailscale is running"""
    try:
        # Check if Tailscale is running and get hostname
        # On Windows, Tailscale runs as a service, so we use the CLI
        result = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        
        # Find our hostname
        for peer in data.get('Peer', {}).values():
            if peer.get('IsSelf', False):
                hostname = peer.get('DNSName', '')
                if hostname:
                    print(f"✅ Found Tailscale hostname: {hostname}")
                    return hostname
        
        print("⚠️ Could not get Tailscale hostname")
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting Tailscale status: {e}")
        print("💡 Make sure Tailscale is running on your system")
        return None
    except FileNotFoundError:
        print("❌ Tailscale not installed. Please install it first.")
        print("💡 Download from: https://tailscale.com/download")
        return None

def check_letsencrypt_certs():
    """Check if Let's Encrypt certificates are available"""
    if os.path.exists(LETSENCRYPT_CERT) and os.path.exists(LETSENCRYPT_KEY):
        print(f"✅ Found Let's Encrypt certificates")
        return True
    else:
        print(f"⚠️ Let's Encrypt certificates not found at {CERT_PATH}")
        return False

@app.route('/')
def index():
    """Main page - shows login or control interface"""
    sp_oauth = create_spotify_oauth()
    
    # Check if we have a valid token
    token_info = sp_oauth.get_cached_token()
    
    if not token_info:
        # No valid token, redirect to login
        auth_url = sp_oauth.get_authorize_url()
        return render_template('login.html', auth_url=auth_url)
    
    # We have a valid token, show the control interface
    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_playback = sp.current_playback()
        return render_template('control.html', playback=current_playback)
    except Exception as e:
        # Token might be expired, redirect to login
        auth_url = sp_oauth.get_authorize_url()
        return render_template('login.html', auth_url=auth_url)

@app.route('/callback')
def callback():
    """Handle Spotify OAuth callback"""
    try:
        sp_oauth = create_spotify_oauth()
        session.clear()
        code = request.args.get('code')
        
        if not code:
            print("❌ No authorization code received from Spotify")
            return redirect('/')
        
        print(f"✅ Received authorization code from Spotify")
        token_info = sp_oauth.get_access_token(code)
        
        if token_info:
            session["token_info"] = token_info
            print("✅ Successfully obtained access token")
        else:
            print("❌ Failed to get access token")
            
        return redirect('/')
    except Exception as e:
        print(f"❌ Error in callback: {e}")
        return redirect('/')

@app.route('/api/playback')
def get_playback():
    """Get current playback status"""
    try:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            return jsonify({'error': 'Not authenticated'}), 401
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_playback = sp.current_playback()
        
        if current_playback:
            track = current_playback['item']
            return jsonify({
                'is_playing': current_playback['is_playing'],
                'track_name': track['name'] if track else 'Unknown',
                'artist_name': track['artists'][0]['name'] if track and track['artists'] else 'Unknown',
                'album_name': track['album']['name'] if track else 'Unknown',
                'progress_ms': current_playback.get('progress_ms', 0),
                'duration_ms': track['duration_ms'] if track else 0,
                'device_name': current_playback['device']['name'] if current_playback.get('device') else 'Unknown'
            })
        else:
            return jsonify({'error': 'No active playback'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/play', methods=['POST'])
def play():
    """Start playback"""
    try:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            return jsonify({'error': 'Not authenticated'}), 401
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.start_playback()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pause', methods=['POST'])
def pause():
    """Pause playback"""
    try:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            return jsonify({'error': 'Not authenticated'}), 401
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.pause_playback()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/next', methods=['POST'])
def next_track():
    """Skip to next track"""
    try:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            return jsonify({'error': 'Not authenticated'}), 401
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.next_track()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/previous', methods=['POST'])
def previous_track():
    """Go to previous track"""
    try:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            return jsonify({'error': 'Not authenticated'}), 401
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.previous_track()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Set volume (0-100)"""
    try:
        if not request.is_json or request.json is None:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        volume = request.json.get('volume', 50)
        volume = max(0, min(100, volume))  # Clamp between 0 and 100
        
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            return jsonify({'error': 'Not authenticated'}), 401
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.volume(volume)
        return jsonify({'success': True, 'volume': volume})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/seek', methods=['POST'])
def seek():
    """Seek to position in track (in milliseconds)"""
    try:
        if not request.is_json or request.json is None:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        position_ms = request.json.get('position_ms', 0)
        
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_cached_token()
        
        if not token_info:
            return jsonify({'error': 'Not authenticated'}), 401
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.seek_track(position_ms)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check if we're in a Docker container
    is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
    
    # Determine the correct setup based on configuration
    if IS_TAILSCALE:
        # Tailscale mode: HTTP server (Tailscale handles HTTPS)
        if is_docker:
            # In Docker, use the provided domain
            if DOMAIN_NAME and '.ts.net' in DOMAIN_NAME:
                print(f"🔒 Tailscale mode (Docker): HTTP server")
                print(f"📱 Access your app at: https://{DOMAIN_NAME}:{PORT}")
                print(f"🔗 Spotify redirect URI: https://{DOMAIN_NAME}:{PORT}/callback")
            else:
                print("❌ Tailscale domain not provided in Docker")
                exit(1)
        else:
            # Local Tailscale: detect hostname
            print("🔍 Detecting Tailscale hostname...")
            tailscale_hostname = get_tailscale_hostname()
            if tailscale_hostname:
                print(f"🔒 Tailscale mode (Local): HTTP server")
                print(f"📱 Access your app at: https://{tailscale_hostname}:{PORT}")
                print(f"🔗 Spotify redirect URI: https://{tailscale_hostname}:{PORT}/callback")
            else:
                print("❌ Tailscale not running or hostname not found.")
                print("💡 Please start Tailscale manually or use a different setup.")
                exit(1)
        
        # Start HTTP server for Tailscale
        app.run(debug=True, host='0.0.0.0', port=PORT)
        
    elif IS_LETSENCRYPT:
        # Let's Encrypt mode: HTTPS with Let's Encrypt certs
        print("🔒 Let's Encrypt mode: HTTPS server")
        print(f"📱 Access your app at: https://{DOMAIN_NAME}:{PORT}")
        print(f"🔗 Spotify redirect URI: https://{DOMAIN_NAME}:{PORT}/callback")
        
        # Use Let's Encrypt certificates
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(LETSENCRYPT_CERT, LETSENCRYPT_KEY)
        
        app.run(debug=True, host='0.0.0.0', port=PORT, ssl_context=ssl_context)
        
    else:
        # Local development mode: HTTP server
        print("🔒 Local development mode: HTTP server")
        print(f"📱 Access your app at: http://localhost:{PORT}")
        if DOMAIN_NAME:
            print(f"🌐 Or at: http://{DOMAIN_NAME}:{PORT}")
        
        # Start HTTP server for local development
        app.run(debug=True, host='0.0.0.0', port=PORT) 