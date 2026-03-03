"""
Logging setup for the application.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_initialized = False


def setup_logging():
    """Configure application-wide logging."""
    global _initialized
    if _initialized:
        return

    log_dir = Path(__file__).resolve().parent.parent.parent / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    root = logging.getLogger("walkin")
    root.setLevel(logging.DEBUG)

    # File handler with rotation
    fh = RotatingFileHandler(
        str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(fh)

    # Console handler (INFO and above)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(ch)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance under the 'walkin' namespace."""
    setup_logging()
    return logging.getLogger(f"walkin.{name}")
