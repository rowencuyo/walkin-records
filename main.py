"""
International Student Services — Walk-In Records Management System
"""
import atexit
import sys

from PySide6.QtCore import qInstallMessageHandler, QtMsgType
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont
from pathlib import Path

from app import __version__
from app.database import initialize_database, close_connection
from app.ui.main_window import MainWindow
from app.ui.theme import FONT_FAMILY
from app.utils.logger import setup_logging, get_logger
from app.utils.paths import get_bundle_dir


def qt_message_handler(mode, context, message):
    """Filter out harmless Qt internal warnings, particularly the QFont string glitch."""
    if "QFont::setPointSize: Point size <= 0" in message:
        return
    
    # Log other Qt messages as warnings
    logger = get_logger("qt")
    logger.warning("Qt Msg: %s", message)


def main():
    qInstallMessageHandler(qt_message_handler)
    setup_logging()
    logger = get_logger("main")
    logger.info("Starting International Student Services v%s", __version__)

    app = QApplication(sys.argv)
    app.setApplicationName("International Student Services")
    app.setOrganizationName("International Student Services")

    # Safely apply 13px font universally to prevent QFont <= 0 pixel CSS calculation errors
    base_font = app.font()
    preferred_family = FONT_FAMILY.split(",")[0].strip("'\"")
    base_font.setFamily(preferred_family)
    base_font.setPixelSize(13)
    app.setFont(base_font)

    # Load global stylesheet from QSS file
    qss_path = get_bundle_dir() / "styles" / "global.qss"
    if qss_path.exists():
        logger.info("Loaded stylesheet from %s", qss_path)
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read()
        # Replace relative asset paths with absolute paths so icons resolve
        # correctly inside PyInstaller bundles (where CWD != bundle dir)
        bundle_assets = str(get_bundle_dir() / "assets").replace("\\", "/")
        qss = qss.replace('url("assets/', f'url("{bundle_assets}/')
        app.setStyleSheet(qss)
    else:
        logger.warning("QSS file not found at %s, using fallback stylesheet", qss_path)
        from app.ui.theme import get_stylesheet
        app.setStyleSheet(get_stylesheet())

    # Initialize database
    initialize_database()

    # Ensure DB connection is closed cleanly when the process exits
    atexit.register(close_connection)

    # Create and show main window
    window = MainWindow()

    # Center the window on the primary screen
    screen = app.primaryScreen()
    if screen:
        screen_geo = screen.availableGeometry()
        x = (screen_geo.width() - window.width()) // 2 + screen_geo.x()
        y = (screen_geo.height() - window.height()) // 2 + screen_geo.y()
        window.move(x, y)

    window.show()

    logger.info("Application window shown")
    try:
        sys.exit(app.exec())
    except Exception as e:
        logger.critical("Unhandled exception caused application crash: %s", e, exc_info=True)
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"An unexpected error occurred and the application must close:\n\n{e}",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
