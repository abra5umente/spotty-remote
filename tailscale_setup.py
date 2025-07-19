#!/usr/bin/env python3
"""
Simple Tailscale setup for Spotify Remote Control
"""

import subprocess
import os
from dotenv import load_dotenv

def main():
    print("🔒 Setting up Tailscale Serve for secure access...")
    print("=" * 55)
    
    # Your Tailscale hostname (from your status output)
    hostname = "abra5dt-win.skink-broadnose.ts.net"
    https_url = f"https://{hostname}:5000"
    callback_url = f"{https_url}/callback"
    
    print(f"✅ Using Tailscale hostname: {hostname}")
    
    # Start Tailscale Serve
    print("\n🌐 Starting Tailscale Serve...")
    try:
        subprocess.run(['tailscale', 'serve', '--https=5000', '--bg'], check=True)
        print("✅ Tailscale Serve started in background")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Tailscale Serve: {e}")
        return
    
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
        print(f"\n💡 Updating your .env file...")
        
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