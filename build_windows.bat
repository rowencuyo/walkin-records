@echo off
:: ============================================================
:: build_windows.bat — Build International Student Services .exe
:: Run this from the project root on a Windows machine.
:: ============================================================

echo.
echo ============================================================
echo  International Student Services — Windows Build
echo ============================================================
echo.

:: 1. Ensure PyInstaller is installed
py -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing PyInstaller...
    py -m pip install pyinstaller
)

:: 2. Clean previous build artifacts
echo [CLEAN] Removing old build/ and dist/ folders...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

:: 3. Run PyInstaller
echo [BUILD] Running PyInstaller...
py -m PyInstaller iss.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  BUILD COMPLETE
echo  Output: dist\ISS\ISS.exe
echo ============================================================
echo.
pause
