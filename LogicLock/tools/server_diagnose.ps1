param(
    [int]$Port = 5000,
    [string]$StartCmd = "",
    [string]$LogPath = ""
)

Write-Host ("Diagnosing server on port {0}" -f $Port) -ForegroundColor Cyan

# Check if any process is listening on the port
try {
    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
} catch {
    $listeners = $null
}

if ($listeners) {
    Write-Host ("Processes listening on port {0}:" -f $Port) -ForegroundColor Green
    $listeners | Select-Object LocalAddress, LocalPort, OwningProcess | Format-Table -AutoSize
    foreach ($l in $listeners) {
        try {
            $p = Get-Process -Id $l.OwningProcess -ErrorAction Stop
            Write-Host " PID $($l.OwningProcess): $($p.ProcessName)" -ForegroundColor Yellow
        } catch {}
    }
} else {
    Write-Host ("No process currently listening on port {0}." -f $Port) -ForegroundColor Yellow
}

# TCP connectivity test
Write-Host "`nTesting TCP connection to localhost:{0}" -f $Port -ForegroundColor Cyan
Test-NetConnection -ComputerName localhost -Port $Port | Format-List

# Optional: show last lines of log if provided
if ($LogPath -and (Test-Path $LogPath)) {
    Write-Host ("`nShowing last 200 lines of log: {0}" -f $LogPath) -ForegroundColor Cyan
    Get-Content -Path $LogPath -Tail 200 | ForEach-Object { Write-Host $_ }
} elseif ($LogPath) {
    Write-Host ("`nLog file not found: {0}" -f $LogPath) -ForegroundColor Red
}

Write-Host "`nHelpful commands:" -ForegroundColor Cyan
Write-Host " - Run the game (foreground) to see server errors directly; if you need elevation use 'Run as Administrator'." -ForegroundColor White
Write-Host (" - If port is in use, find process: Get-NetTCPConnection -LocalPort {0} -State Listen | Select-Object OwningProcess; then tasklist /FI \"PID eq <pid>\"" -f $Port) -ForegroundColor White
Write-Host (" - To open firewall (elevated): New-NetFirewallRule -DisplayName \"Pygame Stream (TCP {0})\" -Direction Inbound -LocalPort {0} -Protocol TCP -Action Allow -Profile Private,Public" -f $Port) -ForegroundColor White
Write-Host "`nRun this script like: .\tools\server_diagnose.ps1 -Port 5000" -ForegroundColor Cyan
