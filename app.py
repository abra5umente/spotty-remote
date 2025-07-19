from flask import Flask, render_template, request, jsonify, redirect, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import requests
import time
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
PORT = int(os.getenv('PORT', 5000))
NGROK_AUTHTOKEN = os.getenv('NGROK_AUTHTOKEN')
USE_NGROK = os.getenv('USE_NGROK', 'true').lower() == 'true'
FORCE_SETUP = os.getenv('FORCE_SETUP', 'false').lower() == 'true'

# Spotify OAuth scope
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

# Create cache directory once at startup
CACHE_DIR = os.path.join(os.getcwd(), '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

FIRST_RUN_FILE = os.path.join(CACHE_DIR, 'first_run_done')
LAST_NGROK_URL_FILE = os.path.join(CACHE_DIR, 'last_ngrok_url')

# Global variable to store ngrok URL
ngrok_url = None
ngrok_error = None

def save_last_ngrok_url(url):
    try:
        with open(LAST_NGROK_URL_FILE, 'w') as f:
            f.write(url)
    except Exception as e:
        print(f"[WARN] Could not save last ngrok URL: {e}")

def load_last_ngrok_url():
    try:
        with open(LAST_NGROK_URL_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        return None

def mark_first_run_done():
    try:
        with open(FIRST_RUN_FILE, 'w') as f:
            f.write('done')
    except Exception as e:
        print(f"[WARN] Could not mark first run done: {e}")

def is_first_run():
    return not os.path.exists(FIRST_RUN_FILE)

def start_ngrok():
    """Start ngrok tunnel"""
    global ngrok_url, ngrok_error
    ngrok_error = None
    
    if not USE_NGROK or not NGROK_AUTHTOKEN:
        print("⚠️  Ngrok disabled or no authtoken provided")
        ngrok_error = "Ngrok disabled or no authtoken provided"
        return None
    
    try:
        # Set ngrok authtoken
        os.system(f'ngrok config add-authtoken {NGROK_AUTHTOKEN}')
        
        # Start ngrok in background
        print("🚀 Starting ngrok tunnel...")
        os.system(f'ngrok http {PORT} --log=stdout > /dev/null 2>&1 &')
        
        # Wait for ngrok API to be available
        for i in range(10):
            try:
                response = requests.get('http://localhost:4040/api/tunnels')
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    for tunnel in tunnels:
                        if tunnel['proto'] == 'https':
                            ngrok_url = tunnel['public_url']
                            last_url = load_last_ngrok_url()
                            if last_url and last_url != ngrok_url:
                                print(f"[WARNING] OAuth callback URI has changed. If you need to reauthenticate, please run the configure-app command and update your Spotify app settings.")
                            save_last_ngrok_url(ngrok_url)
                            return ngrok_url
                time.sleep(1)
            except Exception as e:
                print(f"[ngrok wait] {e}")
                time.sleep(1)
        ngrok_error = "Ngrok API not reachable in container. Is ngrok running?"
        print(f"❌ {ngrok_error}")
    except Exception as e:
        ngrok_error = str(e)
        print(f"❌ Error starting ngrok: {e}")
    
    return None

def get_redirect_uri():
    """Get the appropriate redirect URI based on configuration"""
    if ngrok_url:
        return f"{ngrok_url}/callback"
    else:
        return f"http://localhost:{PORT}/callback"

def create_spotify_oauth():
    """Create Spotify OAuth object with configured redirect URI"""
    redirect_uri = get_redirect_uri()
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_path=os.path.join(CACHE_DIR, 'spotify_token_cache')
    )

def get_spotify_client():
    """Get authenticated Spotify client or None if not authenticated"""
    sp_oauth = create_spotify_oauth()
    token_info = sp_oauth.get_cached_token()
    return spotipy.Spotify(auth=token_info['access_token']) if token_info else None

@app.route('/')
def index():
    """Main page - shows setup instructions or control interface"""
    # Show setup page if first run, or if FORCE_SETUP is set, or if ngrok is enabled and not started
    if (USE_NGROK and NGROK_AUTHTOKEN and not ngrok_url and (is_first_run() or FORCE_SETUP)):
        return render_template('setup.html', port=PORT, ngrok_error=ngrok_error)
    
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

@app.route('/api/ngrok-url')
def get_ngrok_url():
    """Get the current ngrok URL"""
    if ngrok_url:
        return jsonify({
            'url': ngrok_url,
            'callback_url': f"{ngrok_url}/callback"
        })
    elif ngrok_error:
        return jsonify({'error': ngrok_error}), 500
    else:
        return jsonify({'error': 'Ngrok not started'}), 404

@app.route('/api/start-ngrok', methods=['POST'])
def start_ngrok_api():
    """Start ngrok via API call"""
    global ngrok_url
    if ngrok_url:
        return jsonify({'url': ngrok_url, 'callback_url': f"{ngrok_url}/callback"})
    
    url = start_ngrok()
    if url:
        mark_first_run_done()
        return jsonify({'url': url, 'callback_url': f"{url}/callback"})
    else:
        return jsonify({'error': ngrok_error or 'Failed to start ngrok'}), 500

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


def configure_app():
    """Manual setup: start ngrok, print URLs, and instructions."""
    print("\n=== Spotify Remote: Manual Setup ===\n")
    url = start_ngrok()
    if url:
        print(f"\n[ngrok] Public URL: {url}")
        print(f"[ngrok] Callback URL for Spotify: {url}/callback\n")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Select your app > Edit Settings")
        print(f"3. Add the callback URL above to Redirect URIs and Save.")
        print("4. Visit the app in your browser to continue authentication.")
        mark_first_run_done()
    else:
        print(f"[ERROR] Could not start ngrok: {ngrok_error or 'Unknown error'}")
    print()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'configure-app':
        configure_app()
        sys.exit(0)

    print("🚀 Starting Spotify Remote...")
    
    # Don't auto-start ngrok - let user start it via web interface or configure-app
    if USE_NGROK and NGROK_AUTHTOKEN:
        print("📋 Ngrok is configured but not started automatically")
        print("💡 Visit http://localhost:5000 to start ngrok and get your public URL")
        print("💡 Or run: docker exec -it spotify-remote python app.py configure-app")
    else:
        print("⚠️  Ngrok not configured - using localhost only")
    
    print(f"📱 Access your app at: http://localhost:{PORT}")
    
    app.run(debug=True, host='0.0.0.0', port=PORT) 