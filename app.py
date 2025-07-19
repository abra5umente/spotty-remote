from flask import Flask, render_template, request, jsonify, redirect, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import subprocess
import socket
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
TAILSCALE_AUTH_KEY = os.getenv('TAILSCALE_AUTH_KEY')
TAILSCALE_HOSTNAME = os.getenv('TAILSCALE_HOSTNAME', 'spotify-remote')
PORT = int(os.getenv('PORT', 5000))

# Spotify OAuth scope
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

# Create cache directory once at startup
CACHE_DIR = os.path.join(os.getcwd(), '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def generate_unique_hostname():
    """Generate a unique hostname for the container"""
    # Use container hostname or generate unique one
    hostname = socket.gethostname()
    if hostname == 'localhost' or hostname.startswith('spotify-remote'):
        # Generate unique hostname
        unique_id = str(uuid.uuid4())[:8]
        return f"{TAILSCALE_HOSTNAME}-{unique_id}"
    return hostname

def setup_tailscale():
    """Setup Tailscale connection"""
    if not TAILSCALE_AUTH_KEY:
        print("❌ TAILSCALE_AUTH_KEY is required")
        exit(1)
    
    print("🔗 Setting up Tailscale...")
    
    # Generate unique hostname
    hostname = generate_unique_hostname()
    print(f"📱 Using hostname: {hostname}")
    
    # Start Tailscale daemon
    try:
        subprocess.run(['tailscaled', '--tun=userspace-networking', '--socks5-server=localhost:1055'], 
                      check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        print("⚠️ Tailscaled already running or failed to start")
    
    # Wait for daemon to be ready
    import time
    time.sleep(3)
    
    # Connect to Tailscale
    try:
        result = subprocess.run([
            'tailscale', 'up', 
            '--authkey', TAILSCALE_AUTH_KEY,
            '--hostname', hostname,
            '--advertise-tags', 'tag:spotify-remote'
        ], capture_output=True, text=True, check=True)
        
        print("✅ Tailscale connected successfully")
        return hostname
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to connect to Tailscale: {e}")
        print(f"Error output: {e.stderr}")
        exit(1)

def get_tailscale_hostname():
    """Get the current Tailscale hostname"""
    try:
        result = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        
        for peer in data.get('Peer', {}).values():
            if peer.get('IsSelf', False):
                hostname = peer.get('DNSName', '')
                if hostname:
                    return hostname
        
        return None
        
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"❌ Error getting Tailscale status: {e}")
        return None

def create_spotify_oauth(hostname):
    """Create Spotify OAuth object with dynamic redirect URI"""
    redirect_uri = f"https://{hostname}.ts.net:{PORT}/callback"
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_path=os.path.join(CACHE_DIR, 'spotify_token_cache')
    )

def get_spotify_client(hostname):
    """Get authenticated Spotify client or None if not authenticated"""
    sp_oauth = create_spotify_oauth(hostname)
    token_info = sp_oauth.get_cached_token()
    return spotipy.Spotify(auth=token_info['access_token']) if token_info else None

@app.route('/')
def index():
    """Main page - shows login or control interface"""
    hostname = get_tailscale_hostname()
    if not hostname:
        return "❌ Tailscale not connected", 500
    
    sp = get_spotify_client(hostname)
    
    if not sp:
        sp_oauth = create_spotify_oauth(hostname)
        return render_template('login.html', auth_url=sp_oauth.get_authorize_url())
    
    try:
        current_playback = sp.current_playback()
        return render_template('control.html', playback=current_playback)
    except Exception:
        # Token might be expired, redirect to login
        sp_oauth = create_spotify_oauth(hostname)
        return render_template('login.html', auth_url=sp_oauth.get_authorize_url())

@app.route('/callback')
def callback():
    """Handle Spotify OAuth callback"""
    hostname = get_tailscale_hostname()
    if not hostname:
        return "❌ Tailscale not connected", 500
    
    try:
        sp_oauth = create_spotify_oauth(hostname)
        session.clear()
        code = request.args.get('code')
        
        if not code:
            print("❌ No authorization code received from Spotify")
            return redirect('/')
        
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
    hostname = get_tailscale_hostname()
    if not hostname:
        return jsonify({'error': 'Tailscale not connected'}), 500
    
    sp = get_spotify_client(hostname)
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        current_playback = sp.current_playback()
        
        if not current_playback:
            return jsonify({'error': 'No active playback'})
        
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def spotify_action(action_func, *args, **kwargs):
    """Generic function to handle Spotify actions with authentication"""
    hostname = get_tailscale_hostname()
    if not hostname:
        return jsonify({'error': 'Tailscale not connected'}), 500
    
    sp = get_spotify_client(hostname)
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        action_func(sp, *args, **kwargs)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/play', methods=['POST'])
def play():
    """Start playback"""
    return spotify_action(lambda sp: sp.start_playback())

@app.route('/api/pause', methods=['POST'])
def pause():
    """Pause playback"""
    return spotify_action(lambda sp: sp.pause_playback())

@app.route('/api/next', methods=['POST'])
def next_track():
    """Skip to next track"""
    return spotify_action(lambda sp: sp.next_track())

@app.route('/api/previous', methods=['POST'])
def previous_track():
    """Go to previous track"""
    return spotify_action(lambda sp: sp.previous_track())

@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Set volume (0-100)"""
    if not request.is_json or request.json is None:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    volume = max(0, min(100, request.json.get('volume', 50)))
    
    hostname = get_tailscale_hostname()
    if not hostname:
        return jsonify({'error': 'Tailscale not connected'}), 500
    
    sp = get_spotify_client(hostname)
    if not sp:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        sp.volume(volume)
        return jsonify({'success': True, 'volume': volume})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/seek', methods=['POST'])
def seek():
    """Seek to position in track (in milliseconds)"""
    if not request.is_json or request.json is None:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    position_ms = request.json.get('position_ms', 0)
    return spotify_action(lambda sp: sp.seek_track(position_ms))

if __name__ == '__main__':
    print("🚀 Starting Spotify Remote...")
    
    # Setup Tailscale first
    hostname = setup_tailscale()
    
    print(f"🔒 Tailscale mode: HTTP server")
    print(f"📱 Access your app at: https://{hostname}.ts.net:{PORT}")
    print(f"🔗 Spotify redirect URI: https://{hostname}.ts.net:{PORT}/callback")
    
    app.run(debug=True, host='0.0.0.0', port=PORT) 