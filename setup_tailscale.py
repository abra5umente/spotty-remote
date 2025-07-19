#!/usr/bin/env python3
"""
Setup script for Tailscale Serve (secure alternative to ngrok)
"""

import subprocess
import os
from dotenv import load_dotenv

def get_tailscale_hostname():
    """Get the Tailscale hostname for this machine"""
    try:
        result = subprocess.run(['tailscale', 'status', '--json'], 
                              capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        
        # Find the current machine
        for peer in data.get('Peer', {}).values():
            if peer.get('IsSelf', False):
                return peer.get('DNSName', '')
    except Exception as e:
        print(f"Error getting Tailscale hostname: {e}")
    
    return None

def main():
    print("🔒 Setting up Tailscale Serve for secure access...")
    print("=" * 55)
    
    # Check if Tailscale is installed
    try:
        subprocess.run(['tailscale', 'version'], check=True, capture_output=True)
        print("✅ Tailscale is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Tailscale not found. Please install it first:")
        print("   https://tailscale.com/download")
        return
    
    # Get Tailscale hostname
    hostname = get_tailscale_hostname()
    if not hostname:
        print("❌ Could not get Tailscale hostname")
        print("Make sure Tailscale is running and you're logged in")
        return
    
    print(f"✅ Found Tailscale hostname: {hostname}")
    
    # Start Tailscale Serve with HTTP backend
    print("\n🌐 Starting Tailscale Serve...")
    try:
        # Use --http flag to tell Tailscale the backend is HTTP
        subprocess.run(['tailscale', 'serve', '--http=5000', '--bg'], check=True)
        print("✅ Tailscale Serve started in background (HTTP backend)")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Tailscale Serve: {e}")
        return
    
    # Create the HTTPS URL
    https_url = f"https://{hostname}:5000"
    callback_url = f"{https_url}/callback"
    
    print(f"\n✅ Tailscale Serve is ready!")
    print(f"🌐 Secure URL: {https_url}")
    print(f"🔗 Callback URL: {callback_url}")
    print("\n📝 Next steps:")
    print("1. Go to your Spotify Developer Dashboard")
    print("2. Add this redirect URI to your app:")
    print(f"   {callback_url}")
    print("3. Update your .env file with:")
    print(f"   REDIRECT_URI={callback_url}")
    print("4. Start your Flask app: python app.py")
    print("5. Access your app at:", https_url)
    print("\n🔒 Security benefits:")
    print("   ✅ Only accessible within your Tailscale network")
    print("   ✅ No public internet exposure")
    print("   ✅ Encrypted end-to-end")
    print("   ✅ No need for ngrok")
    
    # Update .env file if it exists
    load_dotenv()
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"\n💡 Would you like me to update your .env file?")
        print(f"   This will change REDIRECT_URI to: {callback_url}")
        
        # Read current .env content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update the redirect URI
        if 'REDIRECT_URI=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('REDIRECT_URI='):
                    lines[i] = f'REDIRECT_URI={callback_url}'
                    break
            
            # Write back to file
            with open(env_file, 'w') as f:
                f.write('\n'.join(lines))
            
            print("✅ Updated .env file with Tailscale redirect URI")
        else:
            print("⚠️  Could not find REDIRECT_URI in .env file")

if __name__ == '__main__':
    main() 