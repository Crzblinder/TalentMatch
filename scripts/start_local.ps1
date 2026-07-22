$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$VenvPython = Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"
$VenvPip = Join-Path $ProjectRoot "backend\.venv\Scripts\pip.exe"

# --- Use HuggingFace mirror for China (avoids slow model downloads) ---
if (-not $env:HF_ENDPOINT) {
    $env:HF_ENDPOINT = "https://hf-mirror.com"
    Write-Host "Set HF_ENDPOINT=https://hf-mirror.com (set env var to override)" -ForegroundColor DarkGray
}

Write-Host "Starting TalentMatch Engine locally..." -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor DarkGray

# --- Resolve Python launcher ---
$pyLauncher = $null
foreach ($cmd in @("py", "python", "python3")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) { $pyLauncher = $found.Source; break }
}
if (-not $pyLauncher) {
    Write-Error "Python not found. Install Python 3.11+ and add it to PATH."
    exit 1
}
Write-Host "Python launcher: $pyLauncher" -ForegroundColor DarkGray

# --- Resolve npm (Windows: npm is a .cmd, not a direct exe) ---
$npmCmd = $null
foreach ($cmd in @("npm.cmd", "npm")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) { $npmCmd = $found.Source; break }
}
if (-not $npmCmd) {
    Write-Error "npm not found. Install Node.js 18+ and add it to PATH."
    exit 1
}
Write-Host "npm: $npmCmd" -ForegroundColor DarkGray

# --- Create venv if needed ---
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating backend virtual environment..." -ForegroundColor Yellow
    & $pyLauncher -m venv (Join-Path $ProjectRoot "backend\.venv")

    if (-not (Test-Path $VenvPython)) {
        Write-Error "Failed to create venv. Try manually: py -m venv backend\.venv"
        exit 1
    }
}
Write-Host "Venv Python: $VenvPython" -ForegroundColor DarkGray

# --- Install backend dependencies ---
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
& $VenvPip install -r (Join-Path $BackendDir "requirements.txt")

# --- Init DB and seed ---
Write-Host "Initializing database..." -ForegroundColor Yellow
Push-Location $BackendDir
try {
    & $VenvPython scripts\init_db.py
    & $VenvPython scripts\seed_data.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: seed_data.py exited with code $LASTEXITCODE" -ForegroundColor Red
        Write-Host "The app will still start, but the database may be empty." -ForegroundColor Red
        Write-Host "Fix: set HF_ENDPOINT or use a proxy, then re-run." -ForegroundColor Red
    }
} finally {
    Pop-Location
}

# --- Frontend dependencies ---
Push-Location $FrontendDir
try {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    & $npmCmd install
} finally {
    Pop-Location
}

# --- Start backend ---
Write-Host "Starting backend (port 8000)..." -ForegroundColor Green
$backend = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $BackendDir `
    -PassThru -NoNewWindow

# --- Start frontend ---
Write-Host "Starting frontend (port 5173)..." -ForegroundColor Green
$frontend = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", $npmCmd, "run", "dev" `
    -WorkingDirectory $FrontendDir `
    -PassThru -NoNewWindow

Write-Host ""
Write-Host "  Backend  PID: $($backend.Id)  ->  http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  Frontend PID: $($frontend.Id)  ->  http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open http://localhost:5173 in your browser" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to stop all services"

Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
Write-Host "Services stopped." -ForegroundColor Yellow
