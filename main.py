"""
Walk-In Records Management System — Entry Point
"""
import sys

from PySide6.QtWidgets import QApplication

from app.database import initialize_database
from app.ui.main_window import MainWindow
from app.ui.theme import get_stylesheet
from app.utils.logger import setup_logging, get_logger


def main():
    setup_logging()
    logger = get_logger("main")
    logger.info("Starting Walk-In Records Management System")

    app = QApplication(sys.argv)
    app.setApplicationName("Walk-In Records")
    app.setOrganizationName("WalkInRecords")
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
