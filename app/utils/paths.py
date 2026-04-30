"""
Path utilities for PyInstaller compatibility.

When the app is bundled via PyInstaller, `Path(__file__)` points inside a
temporary extraction directory. This module provides helpers that resolve
paths correctly in both development and frozen (bundled) modes.
"""
import sys
from pathlib import Path


def get_project_root() -> Path:
    """
    Return the project root directory.

    - In development: the directory containing main.py (repo root).
    - When frozen (PyInstaller): the directory containing the .exe.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller sets sys.executable to the .exe path
        return Path(sys.executable).resolve().parent
    # Development: utils → app → project root
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir() -> Path:
    """
    Return the writable data directory for user data, logs, and database.

    - In development: <project_root>/data
    - When frozen (PyInstaller): ~/.iss_records/data
      (avoids PermissionError in C:\\Program Files)
    """
    if getattr(sys, "frozen", False):
        return Path.home() / ".iss_records" / "data"
    return Path(__file__).resolve().parent.parent.parent / "data"


def get_bundle_dir() -> Path:
    """
    Return the directory where bundled *read-only* assets live.

    - In development: same as project root.
    - When frozen: PyInstaller's internal _MEIPASS temp directory,
      where --add-data files are extracted.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent.parent
