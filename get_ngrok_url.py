#!/usr/bin/env python3
"""
Get ngrok HTTPS URL for Spotify configuration
"""

import requests
import time
import json

def get_ngrok_url():
    """Get the public HTTPS URL from ngrok"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}/{max_attempts}: Checking ngrok...")
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                for tunnel in tunnels:
                    if tunnel['proto'] == 'https':
                        return tunnel['public_url']
                print("No HTTPS tunnel found")
            else:
                print(f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            print("ngrok not ready yet...")
        except Exception as e:
            print(f"Error: {e}")
        
        if attempt < max_attempts - 1:
            print("Waiting 3 seconds...")
            time.sleep(3)
    
    return None

def main():
    print("🔍 Looking for ngrok HTTPS URL...")
    print("Make sure ngrok is running with: ngrok http 5000")
    print("=" * 50)
    
    https_url = get_ngrok_url()
    
    if https_url:
        print(f"\n✅ Found ngrok HTTPS URL!")
        print(f"🌐 Public URL: {https_url}")
        print(f"🔗 Callback URL: {https_url}/callback")
        print("\n📝 Next steps:")
        print("1. Go to your Spotify Developer Dashboard")
        print("2. Add this redirect URI to your app:")
        print(f"   {https_url}/callback")
        print("3. Update your .env file with:")
        print(f"   REDIRECT_URI={https_url}/callback")
        print("4. Start your Flask app: python app.py")
        print("5. Access your app at:", https_url)
    else:
        print("\n❌ Could not find ngrok URL")
        print("Make sure:")
        print("1. ngrok is running: ngrok http 5000")
        print("2. Wait a few seconds for ngrok to start")
        print("3. Try running this script again")

if __name__ == '__main__':
    main() 