from flask import Flask, render_template, request, jsonify, redirect, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://localhost:5000/callback')
DOMAIN_NAME = os.getenv('DOMAIN_NAME', '')
PORT = int(os.getenv('PORT', 5000))
IS_TAILSCALE = '.ts.net' in DOMAIN_NAME if DOMAIN_NAME else False

# Spotify OAuth scope
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

# Create cache directory once at startup
CACHE_DIR = os.path.join(os.getcwd(), '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def create_spotify_oauth():
    """Create Spotify OAuth object"""
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=os.path.join(CACHE_DIR, 'spotify_token_cache')
    )

def get_spotify_client():
    """Get authenticated Spotify client or None if not authenticated"""
    sp_oauth = create_spotify_oauth()
    token_info = sp_oauth.get_cached_token()
    return spotipy.Spotify(auth=token_info['access_token']) if token_info else None

def get_container_tailscale_hostname():
    """Get the current Tailscale hostname from the container's Tailscale installation"""
    try:
        result = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        
        for peer in data.get('Peer', {}).values():
            if peer.get('IsSelf', False):
                hostname = peer.get('DNSName', '')
                if hostname:
                    print(f"✅ Found Tailscale hostname: {hostname}")
                    return hostname
        
        print("⚠️ Could not get Tailscale hostname")
        return None
        
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"❌ Error getting Tailscale status: {e}")
        return None

@app.route('/')
def index():
    """Main page - shows login or control interface"""
    sp = get_spotify_client()
    
    if not sp:
        sp_oauth = create_spotify_oauth()
        return render_template('login.html', auth_url=sp_oauth.get_authorize_url())
    
    try:
        current_playback = sp.current_playback()
        return render_template('control.html', playback=current_playback)
    except Exception:
        # Token might be expired, redirect to login
        sp_oauth = create_spotify_oauth()
        return render_template('login.html', auth_url=sp_oauth.get_authorize_url())

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
    sp = get_spotify_client()
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
    sp = get_spotify_client()
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
    
    def set_vol(sp):
        sp.volume(volume)
    
    sp = get_spotify_client()
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
    if IS_TAILSCALE:
        print("🔍 Detecting Tailscale hostname...")
        tailscale_hostname = get_container_tailscale_hostname()
        if tailscale_hostname:
            print(f"🔒 Tailscale mode: HTTP server")
            print(f"📱 Access your app at: https://{tailscale_hostname}:{PORT}")
            print(f"🔗 Spotify redirect URI: https://{tailscale_hostname}:{PORT}/callback")
        else:
            print("❌ Tailscale not running or hostname not found.")
            print("💡 Please check Tailscale configuration in container.")
            exit(1)
    else:
        print("🔒 Local development mode: HTTP server")
        print(f"📱 Access your app at: http://localhost:{PORT}")
        if DOMAIN_NAME:
            print(f"🌐 Or at: http://{DOMAIN_NAME}:{PORT}")
    
    app.run(debug=True, host='0.0.0.0', port=PORT) 