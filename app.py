from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import json
import ssl
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
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

# Spotify OAuth scope - we need user-read-playback-state and user-modify-playback-state
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

def create_spotify_oauth():
    """Create Spotify OAuth object"""
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )

def generate_self_signed_cert():
    """Generate a self-signed certificate for development"""
    # Create certs directory if it doesn't exist
    os.makedirs(CERT_PATH, exist_ok=True)
    
    cert_file = os.path.join(CERT_PATH, 'cert.pem')
    key_file = os.path.join(CERT_PATH, 'key.pem')
    
    # Check if certificates already exist
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return cert_file, key_file
    
    print("🔐 Generating self-signed certificate for HTTPS...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Development"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Spotify Remote"),
        x509.NameAttribute(NameOID.COMMON_NAME, DOMAIN_NAME or "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(DOMAIN_NAME or "localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write certificate and private key to files
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print(f"✅ Certificate generated: {cert_file}")
    return cert_file, key_file

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
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
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
    if IS_TAILSCALE:
        # Tailscale handles HTTPS automatically
        print(f"🔒 Starting server on port {PORT} (Tailscale handles HTTPS)")
        print(f"📱 Access your app at: https://{DOMAIN_NAME}:{PORT}")
        
        app.run(debug=True, host='0.0.0.0', port=PORT)
    else:
        # Generate self-signed certificate for non-Tailscale HTTPS
        cert_file, key_file = generate_self_signed_cert()
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cert_file, key_file)
        
        print(f"🔒 Starting HTTPS server on port {PORT}")
        print(f"📱 Access your app at: https://localhost:{PORT}")
        if DOMAIN_NAME:
            print(f"🌐 Or at: https://{DOMAIN_NAME}:{PORT}")
        
        app.run(debug=True, host='0.0.0.0', port=PORT, ssl_context=ssl_context) 