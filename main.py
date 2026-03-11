"""
Archivium — Offline Walk-In Records Management System
"""
import sys

from PySide6.QtCore import qInstallMessageHandler, QtMsgType
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.database import initialize_database
from app.ui.main_window import MainWindow
from app.ui.theme import get_stylesheet, FONT_FAMILY
from app.utils.logger import setup_logging, get_logger


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
    logger.info("Starting Archivium")

    app = QApplication(sys.argv)
    app.setApplicationName("Archivium")
    app.setOrganizationName("Archivium")

    # Safely apply 13px font universally to prevent QFont <= 0 pixel CSS calculation errors
    base_font = app.font()
    preferred_family = FONT_FAMILY.split(",")[0].strip("'\"")
    base_font.setFamily(preferred_family)
    base_font.setPixelSize(13)
    app.setFont(base_font)

    app.setStyleSheet(get_stylesheet())

    # Initialize database
    initialize_database()

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("Application window shown")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
