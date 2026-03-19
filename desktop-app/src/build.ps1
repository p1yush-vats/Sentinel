# build.ps1
# Place this in: desktop-app\src\
# Run: powershell -ExecutionPolicy Bypass -File build.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SENTINEL Desktop App Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will take 10-15 minutes." -ForegroundColor Yellow
Write-Host "If asked about MinGW64 - type yes and press Enter." -ForegroundColor Yellow
Write-Host ""

python -m nuitka `
    --standalone `
    --windows-console-mode=disable `
    --windows-icon-from-ico="..\assets\iso\sentinel.ico" `
    --enable-plugin=tk-inter `
    --include-package=customtkinter `
    --include-package=pynput `
    --include-package=httpx `
    --include-package=cryptography `
    --include-package=pytz `
    --include-package=core `
    --include-package=ui `
    --include-package=auth `
    --include-package=detection `
    --include-package=storage `
    --include-package=sync `
    --include-package=utils `
    --include-data-files="..\\.env=.env" `
    --include-data-dir="..\venv\Lib\site-packages\customtkinter=customtkinter" `
    --output-filename=SENTINEL.exe `
    --output-dir="..\dist" `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   Build Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Output: desktop-app\dist\main.dist\SENTINEL.exe" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "   Build Failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Paste the error above and we will fix it." -ForegroundColor Yellow
}