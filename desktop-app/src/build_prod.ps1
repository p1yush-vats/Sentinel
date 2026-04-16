# build_prod.ps1
# Place this in: desktop-app\src\
# Run: powershell -ExecutionPolicy Bypass -File build_prod.ps1

$VENV_PYTHON = "..\venv\Scripts\python.exe"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SENTINEL PROD BUILDER (ONE-FILE)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Compiling into a single standalone .exe..." -ForegroundColor Yellow
Write-Host "This will take 10-20 minutes." -ForegroundColor Yellow
Write-Host ""

& $VENV_PYTHON -m nuitka `
    --onefile `
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
    --include-data-dir="..\venv\Lib\site-packages\customtkinter=customtkinter" `
    --output-filename=SENTINEL_PROD.exe `
    --output-dir="..\dist" `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   Build Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Output: desktop-app\dist\SENTINEL_PROD.exe" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "   Build Failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
}
