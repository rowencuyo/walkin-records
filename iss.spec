# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file — International Student Services
Works for BOTH Windows (.exe) and macOS (.app).

Windows build:
    pyinstaller iss.spec

macOS build:
    pyinstaller iss.spec

Output (Windows):  dist/ISS/ISS.exe       (one-folder, recommended)
Output (macOS):    dist/ISS.app
"""

import sys
import os
from pathlib import Path

block_cipher = None

# ── Detect platform ────────────────────────────────────────────────────────────
IS_WINDOWS = sys.platform == "win32"
IS_MAC     = sys.platform == "darwin"

# ── Icon paths (place your icon files here, or leave None) ────────────────────
# Windows: supply a .ico file  →  assets/icons/iss.ico
# macOS  : supply a .icns file →  assets/icons/iss.icns
WIN_ICON  = "assets/icons/iss.ico"  if Path("assets/icons/iss.ico").exists()  else None
MAC_ICON  = "assets/icons/iss.icns" if Path("assets/icons/iss.icns").exists() else None
APP_ICON  = MAC_ICON if IS_MAC else WIN_ICON

# ── Bundled data files (source → destination inside bundle) ───────────────────
added_datas = [
    ("styles",                    "styles"),
    ("assets",                    "assets"),
    ("WalkIn_Records_Export.xlsx", "."),
]

# ── Hidden imports PySide6 requires ───────────────────────────────────────────
hidden = [
    # Charts module (used for the Record Trends line graph)
    "PySide6.QtCharts",
    # SVG support (icons in the sidebar and profile pic widget)
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    # Print support (used by export_profile_to_pdf)
    "PySide6.QtPrintSupport",
    # openpyxl — Excel export
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.styles.borders",
    # Core audit logging module (separate top-level package)
    "core",
    "core.audit_logger",
    # Core app modules PyInstaller may miss via static analysis
    "app.services.completeness",
    "app.services.draft_service",
    "app.services.image_service",
    "app.services.export_service",
    "app.services.document_service",
    "app.services.dashboard_service",
    "app.services.auth_service",
    "app.services.record_service",
    "app.services.notification_service",
    "app.services.preferences_service",
    "app.ui.components.audit_viewer_dialog",
    "app.utils.validators",
    "app.utils.paths",
]

# ── Excluded heavy packages we don't need ─────────────────────────────────────
excluded = [
    "tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "PIL",
    "IPython",
    "jupyter",
    "pytest",
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE (shared between Windows folder-mode and macOS) ────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,           # one-folder mode (more reliable than onefile)
    name="ISS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                   # no terminal window
    icon=APP_ICON,
)

# ── COLLECT (one-folder bundle) ───────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ISS",
)

# ── macOS .app bundle (ignored on Windows) ────────────────────────────────────
if IS_MAC:
    app_bundle = BUNDLE(
        coll,
        name="International Student Services.app",
        icon=MAC_ICON,
        bundle_identifier="com.iss.walkin-records",
        info_plist={
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion":            "1.0.0",
            "CFBundleName":               "International Student Services",
            "CFBundleDisplayName":        "International Student Services",
            "NSHighResolutionCapable":    True,
            "LSMinimumSystemVersion":     "11.0",
            "NSRequiresAquaSystemAppearance": False,  # supports dark mode
        },
    )
