@echo off
REM ============================================================
REM  build.bat — SENTINEL Desktop App build script
REM  Place in: desktop-app/
REM  Run from: desktop-app/  (cd desktop-app && build.bat)
REM ============================================================

echo.
echo ============================================================
echo   SENTINEL Desktop App — PyInstaller Build
echo ============================================================
echo.

REM ── Check we're in the right directory ──────────────────────
if not exist "src\main.py" (
    echo ERROR: Run this script from the desktop-app\ directory.
    echo        Example:  cd desktop-app ^&^& build.bat
    pause
    exit /b 1
)

REM ── Check PyInstaller is installed ──────────────────────────
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller not found. Installing...
    pip install pyinstaller pyinstaller-hooks-contrib
    if errorlevel 1 (
        echo Failed to install PyInstaller. Aborting.
        pause
        exit /b 1
    )
)

REM ── Clean previous build artifacts ──────────────────────────
echo [1/4] Cleaning previous build...
if exist "build"       rmdir /s /q build
if exist "dist\SENTINEL.exe" del /q "dist\SENTINEL.exe"
echo       Done.
echo.

REM ── Run PyInstaller ─────────────────────────────────────────
echo [2/4] Running PyInstaller...
echo       This takes 2-5 minutes. Please wait.
echo.
python -m PyInstaller sentinel.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed. See output above.
    pause
    exit /b 1
)
echo.

REM ── Verify output ───────────────────────────────────────────
echo [3/4] Verifying output...
if not exist "dist\SENTINEL.exe" (
    echo ERROR: dist\SENTINEL.exe was not created.
    pause
    exit /b 1
)

REM ── Get file size ────────────────────────────────────────────
for %%A in ("dist\SENTINEL.exe") do (
    set SIZE=%%~zA
)
REM Convert bytes to MB (rough)
set /a SIZE_MB=%SIZE% / 1048576

echo       dist\SENTINEL.exe created successfully.
echo       File size: ~%SIZE_MB% MB
echo.

REM ── Copy .env next to exe if it exists ──────────────────────
echo [4/4] Copying support files...
if exist ".env" (
    copy /y ".env" "dist\.env" >nul
    echo       .env copied to dist\.env
) else (
    echo       WARNING: .env not found - users must supply it.
)

REM ── Done ────────────────────────────────────────────────────
echo.
echo ============================================================
echo   BUILD COMPLETE
echo   Output: dist\SENTINEL.exe
echo.
echo   To distribute:
echo     - Copy dist\SENTINEL.exe to any Windows machine
echo     - Place a configured .env in the same folder
echo     - (Optional) Run installer via Inno Setup
echo ============================================================
echo.

REM ── Optional: open the dist folder ──────────────────────────
set /p OPEN="Open dist\ folder now? (y/n): "
if /i "%OPEN%"=="y" explorer dist

pause
