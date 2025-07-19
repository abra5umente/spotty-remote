# Spotify Remote - Tailscale Setup for Windows
# This script helps set up Tailscale on Windows for the Spotify Remote app

Write-Host "🔗 Setting up Tailscale for Spotify Remote on Windows" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

# Check if Tailscale is installed
try {
    $tailscaleVersion = & tailscale version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Tailscale is installed: $tailscaleVersion" -ForegroundColor Green
    } else {
        throw "Tailscale not found"
    }
} catch {
    Write-Host "❌ Tailscale not found!" -ForegroundColor Red
    Write-Host "📥 Please download and install Tailscale from:" -ForegroundColor Yellow
    Write-Host "   https://tailscale.com/download" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 After installation, restart this script." -ForegroundColor Yellow
    exit 1
}

# Check if Tailscale is running
try {
    $status = & tailscale status --json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $statusData = $status | ConvertFrom-Json
        $selfPeer = $statusData.Peer.PSObject.Properties | Where-Object { $_.Value.IsSelf -eq $true }
        
        if ($selfPeer) {
            $hostname = $selfPeer.Value.DNSName
            Write-Host "✅ Tailscale is running and connected!" -ForegroundColor Green
            Write-Host "🌐 Your Tailscale hostname: $hostname" -ForegroundColor Cyan
            
            # Get the redirect URI
            $redirectUri = "https://$hostname`:5000/callback"
            Write-Host "🔗 Spotify redirect URI: $redirectUri" -ForegroundColor Cyan
            
            Write-Host ""
            Write-Host "📝 Next steps:" -ForegroundColor Yellow
            Write-Host "1. Go to your Spotify Developer Dashboard" -ForegroundColor White
            Write-Host "2. Add this redirect URI to your app:" -ForegroundColor White
            Write-Host "   $redirectUri" -ForegroundColor Cyan
            Write-Host "3. Update your .env file with:" -ForegroundColor White
            Write-Host "   USE_HTTPS=true" -ForegroundColor Cyan
            Write-Host "   DOMAIN_NAME=$hostname" -ForegroundColor Cyan
            Write-Host "4. Start your Spotify Remote app" -ForegroundColor White
            
        } else {
            Write-Host "⚠️ Tailscale is running but not connected to a network" -ForegroundColor Yellow
            Write-Host "💡 Run: tailscale up" -ForegroundColor Cyan
        }
    } else {
        Write-Host "⚠️ Tailscale is not running" -ForegroundColor Yellow
        Write-Host "💡 Starting Tailscale..." -ForegroundColor Cyan
        
        try {
            & tailscale up
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Tailscale started successfully!" -ForegroundColor Green
                Write-Host "💡 Run this script again to get your hostname." -ForegroundColor Yellow
            } else {
                Write-Host "❌ Failed to start Tailscale" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Error starting Tailscale: $_" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "❌ Error checking Tailscale status: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
Write-Host "- Make sure Tailscale is running as a Windows service" -ForegroundColor White
Write-Host "- Check that the tailscale command is in your PATH" -ForegroundColor White
Write-Host "- Try running PowerShell as Administrator" -ForegroundColor White
Write-Host "- Restart Tailscale service if needed" -ForegroundColor White 