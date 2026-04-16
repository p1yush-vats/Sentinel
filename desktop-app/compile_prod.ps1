# compile_prod.ps1
# Place this in the root of the 'sentinel' project or 'desktop-app' folder.
# Run by right-clicking and 'Run with PowerShell' or typing .\compile_prod.ps1 in your terminal.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SENTINEL Desktop Prod Compiler" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Ensure we are in the correct directory
$DesktopPath = Join-Path $PSScriptRoot "desktop-app"
if (-not (Test-Path $DesktopPath)) {
    $DesktopPath = $PSScriptRoot
}
Set-Location $DesktopPath

# 2. Activate Virtual Environment
Write-Host "[1/3] Activating Virtual Environment..." -ForegroundColor Yellow
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "ERROR: venv not found! Please make sure you created the venv in desktop-app." -ForegroundColor Red
    exit
}

# 3. Navigate to Source
Set-Location "src"

# 4. Run Nuitka Build
Write-Host "[2/3] Starting Nuitka Compilation (10-15 mins)..." -ForegroundColor Cyan
Write-Host "This will convert Python to C++ for production performance." -ForegroundColor Gray

python -m nuitka `
    --standalone `
    --windows-console-mode=disable `
    --windows-icon-from-ico="..\assets\iso\sentinel.ico" `
    --assume-yes-for-downloads `
    --enable-plugin=tk-inter `
    --include-package=customtkinter `
    --include-package=pynput `
    --include-package=httpx `
    --include-package=cryptography `
    --include-package=pytz `
    --include-package=winotify `
    --include-package=pystray `
    --include-package=core `
    --include-package=ui `
    --include-package=auth `
    --include-package=detection `
    --include-package=storage `
    --include-package=sync `
    --include-package=utils `
    --include-data-files="..\\.env=.env" `
    --include-data-dir="..\assets=assets" `
    --include-data-dir="..\venv\Lib\site-packages\customtkinter=customtkinter" `
    --output-filename=SENTINEL_PROD.exe `
    --output-dir="..\dist" `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[3/3] BUILD COMPLETE!" -ForegroundColor Green
    Write-Host "Location: desktop-app\dist\main.dist\SENTINEL_PROD.exe" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "BUILD FAILED. Please check the error above." -ForegroundColor Red
}

Write-Host "Press any key to close..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
