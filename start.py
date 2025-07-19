#!/usr/bin/env python3
"""
Spotify Remote Control - Startup Script
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if environment variables are properly set"""
    load_dotenv()
    
    required_vars = [
        'SPOTIFY_CLIENT_ID',
        'SPOTIFY_CLIENT_SECRET',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Setup instructions:")
        print("1. Copy env_example.txt to .env:")
        print("   cp env_example.txt .env")
        print("2. Edit .env and add your Spotify API credentials")
        print("3. Get credentials from: https://developer.spotify.com/dashboard")
        print("4. Run this script again")
        return False
    
    print("✅ Environment variables are properly configured")
    return True

def main():
    """Main startup function"""
    print("🎵 Spotify Remote Control")
    print("=" * 30)
    
    if not check_environment():
        sys.exit(1)
    
    print("\n🚀 Starting Spotify Remote Control...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🌐 To access from other devices, use your computer's IP address")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting the app: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 