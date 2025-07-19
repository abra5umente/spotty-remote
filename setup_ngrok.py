#!/usr/bin/env python3
"""
Setup script for ngrok HTTPS tunnel
"""

import subprocess
import time
import requests
import json
import os
from dotenv import load_dotenv

def get_ngrok_url():
    """Get the public HTTPS URL from ngrok"""
    try:
        # Wait a moment for ngrok to start
        time.sleep(2)
        
        # Get ngrok tunnel info
        response = requests.get("http://localhost:4040/api/tunnels")
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            for tunnel in tunnels:
                if tunnel['proto'] == 'https':
                    return tunnel['public_url']
    except Exception as e:
        print(f"Error getting ngrok URL: {e}")
    
    return None

def main():
    print("🚀 Setting up ngrok for HTTPS access...")
    print("=" * 50)
    
    # Check if ngrok is installed
    try:
        subprocess.run(["ngrok", "version"], check=True, capture_output=True)
        print("✅ ngrok is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ngrok not found. Please install it first:")
        print("   winget install Ngrok.Ngrok")
        return
    
    # Start ngrok tunnel
    print("\n🌐 Starting ngrok tunnel...")
    print("This will create a public HTTPS URL for your local app.")
    print("Press Ctrl+C to stop ngrok when you're done.")
    print("-" * 50)
    
    try:
        # Start ngrok in background
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", "5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for ngrok to start
        time.sleep(3)
        
        # Get the HTTPS URL
        https_url = get_ngrok_url()
        
        if https_url:
            print(f"✅ ngrok tunnel created!")
            print(f"🌐 Public HTTPS URL: {https_url}")
            print(f"🔗 Callback URL: {https_url}/callback")
            print("\n📝 Next steps:")
            print("1. Go to your Spotify Developer Dashboard")
            print("2. Add this redirect URI to your app:")
            print(f"   {https_url}/callback")
            print("3. Update your .env file with:")
            print(f"   REDIRECT_URI={https_url}/callback")
            print("4. Start your Flask app: python app.py")
            print("5. Access your app at:", https_url)
            
            # Update .env file if it exists
            load_dotenv()
            env_file = '.env'
            if os.path.exists(env_file):
                print(f"\n💡 Would you like me to update your .env file with the new redirect URI?")
                print(f"   This will change REDIRECT_URI to: {https_url}/callback")
                
                # Read current .env content
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Update the redirect URI
                if 'REDIRECT_URI=' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('REDIRECT_URI='):
                            lines[i] = f'REDIRECT_URI={https_url}/callback'
                            break
                    
                    # Write back to file
                    with open(env_file, 'w') as f:
                        f.write('\n'.join(lines))
                    
                    print("✅ Updated .env file with new redirect URI")
                else:
                    print("⚠️  Could not find REDIRECT_URI in .env file")
        else:
            print("❌ Could not get ngrok URL. Make sure ngrok is running.")
        
        # Keep ngrok running
        print("\n⏳ ngrok is running. Press Ctrl+C to stop...")
        ngrok_process.wait()
        
    except KeyboardInterrupt:
        print("\n👋 Stopping ngrok...")
        if 'ngrok_process' in locals():
            ngrok_process.terminate()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main() 