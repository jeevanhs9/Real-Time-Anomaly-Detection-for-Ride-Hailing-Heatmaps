# ============================================================
# start-dev.ps1  —  Development launcher
# Real-Time Anomaly Detection for Ride-Hailing Heatmaps
#
# Usage:  .\start-dev.ps1
# Stops:  Ctrl+C  (kills both backend and frontend)
# ============================================================

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Real-Time Anomaly Detection for Ride-Hailing Heatmaps  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# ── Verify Python and Node are available ─────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: python not found in PATH." -ForegroundColor Red; exit 1
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: node not found in PATH." -ForegroundColor Red; exit 1
}

# ── Check required data artefacts exist ──────────────────────────────────────
$missingArtifacts = @(
    "$Root\data\models\zscore_baseline.joblib",
    "$Root\data\models\lightgbm_demand.joblib",
    "$Root\data\models\isoforest_market.joblib",
    "$Root\data\geo\bengaluru_h3_res8.json"
) | Where-Object { -not (Test-Path $_) }

if ($missingArtifacts.Count -gt 0) {
    Write-Host "MISSING DATA ARTEFACTS:" -ForegroundColor Yellow
    $missingArtifacts | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Run the training pipeline first:" -ForegroundColor Yellow
    Write-Host "  `$env:PYTHONPATH = 'backend'" -ForegroundColor White
    Write-Host "  python backend/scripts/train_eval_clean.py" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? [y/N]"
    if ($continue -ne "y") { exit 1 }
}

# ── Clear stale Vite cache ────────────────────────────────────────────────────
$viteCache = "$Root\frontend\node_modules\.vite"
if (Test-Path $viteCache) {
    Remove-Item -Recurse -Force $viteCache -ErrorAction SilentlyContinue
    Write-Host "  Cleared stale Vite cache." -ForegroundColor DarkGray
}

# ── Start backend in a new PowerShell window ─────────────────────────────────
Write-Host "  Starting backend  →  http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs           →  http://localhost:8000/docs" -ForegroundColor DarkGray
$backendCmd = "& { `$env:PYTHONPATH = '$Root\backend'; " +
              "Write-Host 'Backend starting...' -ForegroundColor Green; " +
              "uvicorn app.main:app --reload --port 8000 --host 127.0.0.1 }"
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru

# ── Wait for backend to become ready ─────────────────────────────────────────
Write-Host "  Waiting for backend to be ready..." -ForegroundColor DarkGray
$maxWait = 30
$waited  = 0
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" `
                                  -TimeoutSec 2 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { break }
    } catch { }
}
if ($waited -ge $maxWait) {
    Write-Host "  WARNING: Backend did not respond within ${maxWait}s — check the backend window for errors." -ForegroundColor Yellow
} else {
    Write-Host "  Backend ready. (${waited}s)" -ForegroundColor Green
}

# ── Start frontend in a new PowerShell window ────────────────────────────────
Write-Host "  Starting frontend →  http://localhost:5173" -ForegroundColor Green
$frontendCmd = "& { Set-Location '$Root\frontend'; " +
               "Write-Host 'Frontend starting...' -ForegroundColor Green; " +
               "npm run dev }"
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  BOTH SERVERS RUNNING" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend : http://localhost:5173" -ForegroundColor White
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health   : http://localhost:8000/api/v1/health" -ForegroundColor White
Write-Host ""
Write-Host "  Close the backend/frontend windows to stop them." -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
