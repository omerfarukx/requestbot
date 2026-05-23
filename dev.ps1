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
#   .\dev.ps1 deploy   -> Sunucuya deploy et (build + scp + ssh restart)

param(
  [ValidateSet("start", "stop", "status", "reset", "server", "client", "logs", "deploy")]
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

  "deploy" {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  RequestBot Tam Deploy Basladi"             -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""

    # 1. Client frontend build (exe icin)
    Write-Host "-> [1/5] Client frontend build..." -ForegroundColor Yellow
    & $NPM --prefix (Join-Path $ROOT "client\frontend") run build
    if ($LASTEXITCODE -ne 0) { Write-Host "HATA: client frontend build basarisiz!" -ForegroundColor Red; exit 1 }
    Write-Host "   OK" -ForegroundColor Green

    # 2. PyInstaller ile RequestBot.exe
    Write-Host "-> [2/5] PyInstaller - RequestBot.exe olusturuluyor..." -ForegroundColor Yellow
    & $PYTHON -m PyInstaller RequestBot.spec --noconfirm 2>&1 | ForEach-Object {
      if ($_ -match "ERROR|error") { Write-Host "   $_" -ForegroundColor Red }
    }
    if ($LASTEXITCODE -ne 0) { Write-Host "HATA: PyInstaller basarisiz!" -ForegroundColor Red; exit 1 }
    $exeSrc = Join-Path $ROOT "dist\RequestBot.exe"
    if (-not (Test-Path $exeSrc)) { Write-Host "HATA: dist\RequestBot.exe bulunamadi!" -ForegroundColor Red; exit 1 }
    $downloadsDir = Join-Path $ROOT "server\downloads"
    if (-not (Test-Path $downloadsDir)) { New-Item -ItemType Directory -Path $downloadsDir | Out-Null }
    Copy-Item $exeSrc (Join-Path $downloadsDir "RequestBot.exe") -Force
    Write-Host "   RequestBot.exe -> server\downloads\  OK" -ForegroundColor Green

    # 3. Server frontend build
    Write-Host "-> [3/5] Server frontend build..." -ForegroundColor Yellow
    & $NPM --prefix (Join-Path $ROOT "server\frontend") run build
    if ($LASTEXITCODE -ne 0) { Write-Host "HATA: server frontend build basarisiz!" -ForegroundColor Red; exit 1 }
    Write-Host "   OK" -ForegroundColor Green

    # 4. SCP: frontend dist + backend Python
    Write-Host "-> [4/5] Kod dosyalari sunucuya aktariliyor..." -ForegroundColor Yellow
    $scpDist    = "requestbot:/tmp/requestbot_dist"
    $scpBackend = "requestbot:/tmp/requestbot_backend"
    scp -o ServerAliveInterval=30 -o ServerAliveCountMax=5 -r (Join-Path $ROOT "server\frontend\dist") $scpDist
    if ($LASTEXITCODE -ne 0) { Write-Host "HATA: SCP dist basarisiz!" -ForegroundColor Red; exit 1 }
    scp -o ServerAliveInterval=30 -o ServerAliveCountMax=5 -r (Join-Path $ROOT "server\backend") $scpBackend
    if ($LASTEXITCODE -ne 0) { Write-Host "HATA: SCP backend basarisiz!" -ForegroundColor Red; exit 1 }
    Write-Host "   OK" -ForegroundColor Green

    # 5. SSH: dosyalari yerles + servisi yeniden baslat
    Write-Host "-> [5/5] SSH: servis guncelleniyor..." -ForegroundColor Yellow
    ssh requestbot @'
set -e
cd /opt/requestbot
git pull
rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='*.db' /tmp/requestbot_backend/ server/backend/
rm -rf /tmp/requestbot_backend
/opt/requestbot/server/backend/.venv/bin/pip install -r server/backend/requirements.txt -q
rm -rf server/frontend/dist
mv /tmp/requestbot_dist server/frontend/dist
systemctl restart requestbot 2>/dev/null || supervisorctl restart requestbot 2>/dev/null || true
echo "[Deploy] Tamamlandi!"
'@
    if ($LASTEXITCODE -ne 0) { Write-Host "HATA: SSH komutu basarisiz!" -ForegroundColor Red; exit 1 }

    # 6. SCP: RequestBot.exe (buyuk dosya, son adim)
    Write-Host "-> [6/6] RequestBot.exe yukleniyor (buyuk dosya, bekleyiniz)..." -ForegroundColor Yellow
    $scpExeDest = "requestbot:/opt/requestbot/server/downloads/RequestBot.exe"
    scp -o ServerAliveInterval=60 -o ServerAliveCountMax=20 -C (Join-Path $downloadsDir "RequestBot.exe") $scpExeDest
    if ($LASTEXITCODE -ne 0) {
      Write-Host "UYARI: Exe yuklemesi basarisiz - kod degisiklikleri deploy edildi, exe eski kaldi." -ForegroundColor Yellow
    } else {
      Write-Host "   OK" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  Deploy tamamlandi!  https://requesthitbot.com" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
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
