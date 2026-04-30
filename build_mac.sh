#!/bin/bash
# =============================================================
# build_mac.sh — Build International Student Services .app
# Run this from the project root on a macOS machine.
# =============================================================

set -e   # exit immediately on any error

echo ""
echo "============================================================"
echo " International Student Services — macOS Build"
echo "============================================================"
echo ""

# 0. Ensure Xcode Command Line Tools are installed (required for PyInstaller)
echo "[CHECK] Checking for Xcode Command Line Tools..."
if ! xcode-select -p &>/dev/null; then
    echo ""
    echo "  ✖  ERROR: Xcode Command Line Tools are not installed."
    echo "     PyInstaller requires 'lipo' and other tools to build the app."
    echo ""
    echo "     Please run:  xcode-select --install"
    echo "     Then re-run this script after the installation completes."
    echo ""
    exit 1
else
    echo "[CHECK] Xcode Command Line Tools found ✓"
fi

# 1. Create / activate a virtual environment
echo "[SETUP] Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "[SETUP] Virtual environment created at .venv/"
else
    echo "[SETUP] Virtual environment already exists — reusing it."
fi
source .venv/bin/activate

# 2. Ensure dependencies are installed
echo "[SETUP] Installing / upgrading required dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade PySide6 openpyxl pyinstaller

# 3. Check for macOS icon (warn if missing, build continues without it)
echo "[CHECK] Verifying macOS icon..."
if [ ! -f "assets/icons/iss.icns" ]; then
    echo ""
    echo "  ⚠  WARNING: assets/icons/iss.icns not found."
    echo "     The app will build successfully but will have no custom icon."
    echo "     To add an icon, convert assets/icons/iss.ico → iss.icns"
    echo "     (e.g. using https://cloudconvert.com/ico-to-icns)"
    echo "     and place the file at: assets/icons/iss.icns"
    echo ""
else
    echo "[CHECK] iss.icns found ✓"
fi

# 4. Clean previous build artifacts
echo "[CLEAN] Removing old build/ and dist/ folders..."
rm -rf build dist

# 5. Run PyInstaller
echo "[BUILD] Running PyInstaller..."
python3 -m PyInstaller iss.spec

echo ""
echo "============================================================"
echo " BUILD COMPLETE"
echo " Output: dist/International Student Services.app"
echo "============================================================"
echo ""

# 6. Optional: open the dist folder in Finder
open dist/
