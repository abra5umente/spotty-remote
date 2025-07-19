#!/usr/bin/env python3
"""
Let's Encrypt Certificate Setup Script for Spotify Remote

This script helps you set up Let's Encrypt certificates for HTTPS production use.
"""

import os
import subprocess
import sys
from pathlib import Path

def check_certbot():
    """Check if certbot is installed"""
    try:
        subprocess.run(['certbot', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_certbot():
    """Install certbot"""
    print("🔧 Installing certbot...")
    
    # Detect OS and install certbot
    if sys.platform.startswith('linux'):
        # Try different package managers
        package_managers = [
            ['apt-get', 'update', '&&', 'apt-get', 'install', '-y', 'certbot'],
            ['yum', 'install', '-y', 'certbot'],
            ['dnf', 'install', '-y', 'certbot'],
            ['pacman', '-S', '--noconfirm', 'certbot']
        ]
        
        for cmd in package_managers:
            try:
                if cmd[0] == 'apt-get':
                    subprocess.run(' '.join(cmd), shell=True, check=True)
                    return True
                else:
                    subprocess.run(cmd, check=True)
                    return True
            except subprocess.CalledProcessError:
                continue
                
    elif sys.platform.startswith('darwin'):  # macOS
        try:
            subprocess.run(['brew', 'install', 'certbot'], check=True)
            return True
        except subprocess.CalledProcessError:
            print("❌ Please install Homebrew first: https://brew.sh/")
            return False
            
    elif sys.platform.startswith('win'):
        print("❌ Certbot installation on Windows is complex.")
        print("💡 Consider using WSL or Docker for Let's Encrypt setup.")
        return False
    
    print("❌ Could not install certbot automatically.")
    print("💡 Please install certbot manually: https://certbot.eff.org/")
    return False

def get_domain_info():
    """Get domain information from user"""
    print("\n🌐 Domain Setup")
    print("==============")
    
    domain = input("Enter your domain name (e.g., spotify-remote.example.com): ").strip()
    if not domain:
        print("❌ Domain name is required for Let's Encrypt certificates.")
        return None
    
    email = input("Enter your email address (for Let's Encrypt notifications): ").strip()
    if not email:
        print("❌ Email address is required for Let's Encrypt certificates.")
        return None
    
    return domain, email

def generate_certificate(domain, email):
    """Generate Let's Encrypt certificate"""
    print(f"\n🔐 Generating certificate for {domain}...")
    
    # Create certs directory
    certs_dir = Path('./certs')
    certs_dir.mkdir(exist_ok=True)
    
    # Certbot command for standalone mode
    cmd = [
        'certbot', 'certonly',
        '--standalone',
        '--pre-hook', 'systemctl stop spotify-remote || true',
        '--post-hook', 'systemctl start spotify-remote || true',
        '--email', email,
        '--agree-tos',
        '--no-eff-email',
        '--domains', domain
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Certificate generated successfully!")
        
        # Copy certificates to our certs directory
        certbot_cert_path = f"/etc/letsencrypt/live/{domain}"
        if os.path.exists(f"{certbot_cert_path}/fullchain.pem"):
            subprocess.run(['cp', f"{certbot_cert_path}/fullchain.pem", './certs/cert.pem'], check=True)
            subprocess.run(['cp', f"{certbot_cert_path}/privkey.pem", './certs/key.pem'], check=True)
            subprocess.run(['chmod', '600', './certs/key.pem'], check=True)
            print("✅ Certificates copied to ./certs/")
        else:
            print("⚠️  Certificates not found in expected location.")
            print("💡 You may need to copy them manually from /etc/letsencrypt/live/")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Certificate generation failed: {e}")
        return False

def update_env_file(domain):
    """Update .env file with HTTPS settings"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found. Please create it first.")
        return False
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add HTTPS settings
    updated_lines = []
    https_updated = False
    domain_updated = False
    redirect_updated = False
    
    for line in lines:
        if line.startswith('USE_HTTPS='):
            updated_lines.append('USE_HTTPS=true\n')
            https_updated = True
        elif line.startswith('DOMAIN_NAME='):
            updated_lines.append(f'DOMAIN_NAME={domain}\n')
            domain_updated = True
        elif line.startswith('REDIRECT_URI='):
            updated_lines.append(f'REDIRECT_URI=https://{domain}:5000/callback\n')
            redirect_updated = True
        else:
            updated_lines.append(line)
    
    # Add missing settings
    if not https_updated:
        updated_lines.append('USE_HTTPS=true\n')
    if not domain_updated:
        updated_lines.append(f'DOMAIN_NAME={domain}\n')
    if not redirect_updated:
        updated_lines.append(f'REDIRECT_URI=https://{domain}:5000/callback\n')
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ .env file updated with HTTPS settings")
    return True

def setup_renewal_cron():
    """Set up automatic certificate renewal"""
    print("\n🔄 Setting up automatic renewal...")
    
    # Create renewal script
    renewal_script = '''#!/bin/bash
# Spotify Remote Certificate Renewal Script

# Stop the application
docker-compose down || systemctl stop spotify-remote || true

# Renew certificates
certbot renew --quiet

# Copy renewed certificates
DOMAIN=$(grep DOMAIN_NAME .env | cut -d'=' -f2)
if [ -n "$DOMAIN" ]; then
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./certs/cert.pem
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./certs/key.pem
    chmod 600 ./certs/key.pem
fi

# Restart the application
docker-compose up -d || systemctl start spotify-remote || true
'''
    
    with open('renew_cert.sh', 'w') as f:
        f.write(renewal_script)
    
    os.chmod('renew_cert.sh', 0o755)
    
    # Add to crontab (renew twice daily)
    cron_job = "0 6,18 * * * cd $(pwd) && ./renew_cert.sh"
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Add our job if not already present
        if cron_job not in current_cron:
            new_cron = current_cron + "\n" + cron_job + "\n"
            subprocess.run(['crontab', '-'], input=new_cron, text=True, check=True)
            print("✅ Automatic renewal scheduled (twice daily)")
        else:
            print("✅ Automatic renewal already scheduled")
            
    except subprocess.CalledProcessError:
        print("⚠️  Could not set up automatic renewal.")
        print("💡 You can manually run: ./renew_cert.sh")

def main():
    """Main setup function"""
    print("🔐 Let's Encrypt Certificate Setup for Spotify Remote")
    print("=====================================================")
    
    # Check if certbot is installed
    if not check_certbot():
        print("❌ Certbot is not installed.")
        install_choice = input("Would you like to install certbot? (y/n): ").strip().lower()
        if install_choice == 'y':
            if not install_certbot():
                return
        else:
            print("💡 Please install certbot manually and run this script again.")
            return
    
    # Get domain information
    domain_info = get_domain_info()
    if not domain_info:
        return
    
    domain, email = domain_info
    
    # Generate certificate
    if not generate_certificate(domain, email):
        return
    
    # Update .env file
    if not update_env_file(domain):
        return
    
    # Set up renewal
    setup_renewal_cron()
    
    print("\n🎉 Setup complete!")
    print("==================")
    print(f"📱 Your app will be available at: https://{domain}:5000")
    print("🔧 To start the app with HTTPS:")
    print("   docker-compose up -d")
    print("   or")
    print("   python app.py")
    print("\n⚠️  Important notes:")
    print("   - Make sure port 80 is open for certificate validation")
    print("   - Certificates will auto-renew twice daily")
    print("   - Update your Spotify app's redirect URI to: https://{domain}:5000/callback")

if __name__ == '__main__':
    main() 