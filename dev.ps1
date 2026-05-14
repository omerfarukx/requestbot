# RequestBot Dev Orchestrator
#
# Kullanim:
#   .\dev.ps1          -> Tumunu baslat
#   .\dev.ps1 stop     -> Tumunu durdur
#   .\dev.ps1 status   -> Port saglik kontrolu
#   .\dev.ps1 reset    -> DB sifirla + session temizle
#   .\dev.ps1 server   -> Sadece server tarafi
#   .\dev.ps1 client   -> Sadece client tarafi (launcher dahil)
#   .\dev.ps1 logs     -> Son loglari goster

param(
  [ValidateSet("start", "stop", "status", "reset", "server", "client", "logs")]
  [string]$Command = "start"
)

$ROOT = $PSScriptRoot
$LOG_DIR = Join-Path $ROOT ".devlogs"
if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR | Out-Null }

$PYTHON = "C:\Python313\python.exe"
$NPM = "npm.cmd"

# ----- helpers -----

function Stop-AllProcs {
  Write-Host "-> Python / Node surecleri durduruluyor..." -ForegroundColor Yellow
  Get-Process python, pythonw, node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep 2
}

function Test-Endpoint {
  param([int]$port, [string]$path = "/")
  try {
    $r = Invoke-WebRequest "http://localhost:$port$path" -UseBasicParsing -TimeoutSec 2
    return @{ ok = $true; status = $r.StatusCode }
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    if ($code) { return @{ ok = $true; status = $code } }
    return @{ ok = $false; status = 0 }
  }
}

function Start-ServerBackend {
  Write-Host "-> Server Backend (FastAPI) port 8001" -ForegroundColor Cyan
  Start-Process $PYTHON `
    -ArgumentList "-m", "uvicorn", "main:app", "--port", "8001", "--reload" `
    -WorkingDirectory (Join-Path $ROOT "server\backend") `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $LOG_DIR "server-backend.log") `
    -RedirectStandardError  (Join-Path $LOG_DIR "server-backend.err.log")
}

function Start-ServerFrontend {
  Write-Host "-> Server Frontend (Vite) port 3001" -ForegroundColor Cyan
  Start-Process $NPM `
    -ArgumentList "run", "dev" `
    -WorkingDirectory (Join-Path $ROOT "server\frontend") `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $LOG_DIR "server-frontend.log") `
    -RedirectStandardError  (Join-Path $LOG_DIR "server-frontend.err.log")
}

function Start-ClientBackend {
  Write-Host "-> Client Backend (FastAPI) port 8000" -ForegroundColor Magenta
  Start-Process $PYTHON `
    -ArgumentList "-m", "uvicorn", "main:app", "--port", "8000", "--reload" `
    -WorkingDirectory (Join-Path $ROOT "client\backend") `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $LOG_DIR "client-backend.log") `
    -RedirectStandardError  (Join-Path $LOG_DIR "client-backend.err.log")
}

function Start-ClientFrontend {
  Write-Host "-> Client Frontend (Vite) port 3000" -ForegroundColor Magenta
  Start-Process $NPM `
    -ArgumentList "run", "dev" `
    -WorkingDirectory (Join-Path $ROOT "client\frontend") `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $LOG_DIR "client-frontend.log") `
    -RedirectStandardError  (Join-Path $LOG_DIR "client-frontend.err.log")
}

function Start-Launcher {
  Write-Host "-> Client Launcher (GUI)" -ForegroundColor Green
  Start-Process $PYTHON `
    -ArgumentList (Join-Path $ROOT "client\launcher.pyw") `
    -WorkingDirectory (Join-Path $ROOT "client") `
    -WindowStyle Normal
}

function Show-Status {
  Write-Host ""
  Write-Host "=== Servis Durumu ===" -ForegroundColor Cyan
  $targets = @(
    @{ name = "Server Backend";  port = 8001; path = "/docs" }
    @{ name = "Server Frontend"; port = 3001; path = "/" }
    @{ name = "Client Backend";  port = 8000; path = "/docs" }
    @{ name = "Client Frontend"; port = 3000; path = "/" }
  )
  foreach ($t in $targets) {
    $r = Test-Endpoint -port $t.port -path $t.path
    if ($r.ok) {
      $line = "  [OK]   {0,-20} :{1}  [{2}]" -f $t.name, $t.port, $r.status
      Write-Host $line -ForegroundColor Green
    } else {
      $line = "  [DOWN] {0,-20} :{1}" -f $t.name, $t.port
      Write-Host $line -ForegroundColor Red
    }
  }
  Write-Host ""
}

# ----- commands -----

switch ($Command) {

  "stop" {
    Stop-AllProcs
    Write-Host "OK - Tum servisler durduruldu" -ForegroundColor Green
  }

  "status" {
    Show-Status
  }

  "reset" {
    Stop-AllProcs
    Write-Host "-> Server DB siliniyor..." -ForegroundColor Yellow
    Remove-Item (Join-Path $ROOT "server\backend\server.db") -ErrorAction SilentlyContinue
    Write-Host "-> Client DB siliniyor..." -ForegroundColor Yellow
    Remove-Item (Join-Path $ROOT "client\backend\bot.db") -ErrorAction SilentlyContinue
    Write-Host "-> Launcher session temizleniyor..." -ForegroundColor Yellow
    Remove-Item "$env:APPDATA\RequestBot\session.json" -ErrorAction SilentlyContinue
    Write-Host "OK - Reset tamam - '.\dev.ps1 start' ile baslat" -ForegroundColor Green
  }

  "server" {
    Stop-AllProcs
    Start-ServerBackend
    Start-Sleep 2
    Start-ServerFrontend
    Start-Sleep 5
    Show-Status
    Write-Host "Server Frontend: http://localhost:3001" -ForegroundColor Green
    Write-Host "Server API Docs: http://localhost:8001/docs" -ForegroundColor Green
  }

  "client" {
    Start-ClientBackend
    Start-Sleep 2
    Start-ClientFrontend
    Start-Sleep 2
    Start-Launcher
    Write-Host "Client Dashboard: http://localhost:3000" -ForegroundColor Green
  }

  "logs" {
    Write-Host "Log dosyalari: $LOG_DIR" -ForegroundColor Cyan
    Get-ChildItem $LOG_DIR -Filter "*.log" | ForEach-Object {
      Write-Host ""
      Write-Host "--- $($_.Name) ---" -ForegroundColor Yellow
      Get-Content $_.FullName -Tail 10
    }
  }

  default {
    Stop-AllProcs
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "  RequestBot Dev - Tum servisler basliyor"   -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""

    Start-ServerBackend
    Start-Sleep 2
    Start-ServerFrontend
    Start-Sleep 2
    Start-ClientBackend
    Start-Sleep 2
    Start-ClientFrontend
    Start-Sleep 5

    Show-Status

    Write-Host "URLs:" -ForegroundColor Cyan
    Write-Host "  Server (pazaryeri) : http://localhost:3001" -ForegroundColor White
    Write-Host "  Server API Docs    : http://localhost:8001/docs" -ForegroundColor Gray
    Write-Host "  Client (dashboard) : http://localhost:3000" -ForegroundColor White
    Write-Host "  Client API Docs    : http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Launcher GUI: .\dev.ps1 client" -ForegroundColor Yellow
    Write-Host "Loglar      : .\dev.ps1 logs" -ForegroundColor Gray
    Write-Host "Durdur      : .\dev.ps1 stop" -ForegroundColor Gray
  }
}
