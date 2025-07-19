# Spotify Remote Control - Docker Build Script (PowerShell)

Write-Host "🐳 Building Spotify Remote Control Docker container..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your Spotify credentials:" -ForegroundColor Yellow
    Write-Host "SPOTIFY_CLIENT_ID=your_client_id" -ForegroundColor Cyan
    Write-Host "SPOTIFY_CLIENT_SECRET=your_client_secret" -ForegroundColor Cyan
    Write-Host "SECRET_KEY=your_secret_key" -ForegroundColor Cyan
    Write-Host "REDIRECT_URI=https://abra5dt-win.skink-broadnose.ts.net:5000/callback" -ForegroundColor Cyan
    exit 1
}

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Check required environment variables
$requiredVars = @('SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SECRET_KEY')
$missingVars = @()

foreach ($var in $requiredVars) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing required environment variables!" -ForegroundColor Red
    Write-Host "Please check your .env file contains:" -ForegroundColor Yellow
    foreach ($var in $missingVars) {
        Write-Host "- $var" -ForegroundColor Cyan
    }
    exit 1
}

Write-Host "✅ Environment variables loaded" -ForegroundColor Green

# Build the Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker build -t spotify-remote:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker image built successfully!" -ForegroundColor Green

# Run with docker-compose
Write-Host "🚀 Starting container with docker-compose..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker-compose failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container started!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access your app at:" -ForegroundColor Cyan
Write-Host "   Local: http://localhost:5000" -ForegroundColor White
Write-Host "   Tailscale: https://abra5dt-win.skink-broadnose.ts.net:5000" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop: docker-compose down" -ForegroundColor White
Write-Host "   Restart: docker-compose restart" -ForegroundColor White
Write-Host "   Update: docker-compose pull && docker-compose up -d" -ForegroundColor White 