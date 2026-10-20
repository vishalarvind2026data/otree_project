# ==============================================================================
# Share Live Tunnel Script (Instant Public Internet Link - PowerShell)
# ==============================================================================
param (
    [int]$Port = 8000
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  oTree Instant Live Internet Exposer" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "This script creates a secure public HTTPS link to your local oTree"
Write-Host "server so participants across the internet can join."
Write-Host ""
Write-Host "[*] Connecting to secure public tunnel on port $Port..."
Write-Host "[*] Once the URL appears, send participants to:" -ForegroundColor Yellow
Write-Host "    https://<TUNNEL-DOMAIN>/room/online_open" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C at any time to stop sharing." -ForegroundColor Gray
Write-Host "----------------------------------------------------------------------"

npx --yes localtunnel --port $Port
