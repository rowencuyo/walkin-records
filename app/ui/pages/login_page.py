"""
Login page — shown on app startup before granting access.
Handles both first-time password setup and regular login.
"""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy,
)

from app.services.auth_service import AuthService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage(QWidget):
    """Login / first-time setup page."""

    login_successful = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth = AuthService()
        self._is_setup = self._auth.is_setup_complete()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        # Centered card
        card = QWidget()
        card.setFixedWidth(380)
        card.setStyleSheet(
            "QWidget { background-color: #FFFFFF; border-radius: 12px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 40, 32, 32)
        card_layout.setSpacing(16)

        # Title
        title = QLabel("Archivium")
        title.setStyleSheet(
            "font-size: 24px; font-weight: 700; color: #1D1D1F; "
            "background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle_text = (
            "Set up your account" if not self._is_setup
            else "Sign in to continue"
        )
        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet(
            "font-size: 14px; color: #6E6E73; background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        card_layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Username
        username_label = QLabel("Username")
        username_label.setStyleSheet(
            "font-size: 13px; font-weight: 500; color: #1D1D1F; background: transparent;"
        )
        card_layout.addWidget(username_label)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Enter username")
        self._username_input.setFixedHeight(38)
        if self._is_setup:
            self._username_input.setText(self._auth.get_username())
        card_layout.addWidget(self._username_input)

        # Password
        pw_label = QLabel("Password")
        pw_label.setStyleSheet(
            "font-size: 13px; font-weight: 500; color: #1D1D1F; background: transparent;"
        )
        card_layout.addWidget(pw_label)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Enter password")
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.setFixedHeight(38)
        self._password_input.returnPressed.connect(self._on_submit)
        card_layout.addWidget(self._password_input)

        # Confirm password (setup only)
        if not self._is_setup:
            confirm_label = QLabel("Confirm Password")
            confirm_label.setStyleSheet(
                "font-size: 13px; font-weight: 500; color: #1D1D1F; background: transparent;"
            )
            card_layout.addWidget(confirm_label)

            self._confirm_input = QLineEdit()
            self._confirm_input.setPlaceholderText("Confirm password")
            self._confirm_input.setEchoMode(QLineEdit.Password)
            self._confirm_input.setFixedHeight(38)
            self._confirm_input.returnPressed.connect(self._on_submit)
            card_layout.addWidget(self._confirm_input)
        else:
            self._confirm_input = None

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet(
            "color: #FF3B30; font-size: 13px; background: transparent;"
        )
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        card_layout.addWidget(self._error_label)

        card_layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Submit button
        btn_text = "Create Account" if not self._is_setup else "Sign In"
        self._submit_btn = QPushButton(btn_text)
        self._submit_btn.setObjectName("primaryButton")
        self._submit_btn.setFixedHeight(40)
        self._submit_btn.clicked.connect(self._on_submit)
        card_layout.addWidget(self._submit_btn)

        outer.addWidget(card)

    def _show_error(self, msg: str):
        self._error_label.setText(msg)
        self._error_label.setVisible(True)

    def _on_submit(self):
        username = self._username_input.text().strip()
        password = self._password_input.text()

        if not username:
            self._show_error("Username is required")
            return
        if not password:
            self._show_error("Password is required")
            return

        if not self._is_setup:
            # First-time setup
            confirm = self._confirm_input.text() if self._confirm_input else ""
            if password != confirm:
                self._show_error("Passwords do not match")
                return
            if len(password) < 4:
                self._show_error("Password must be at least 4 characters")
                return

            try:
                self._auth.setup_password(username, password)
                logger.info("Account created for '%s'", username)
                self.login_successful.emit()
            except Exception as e:
                self._show_error(f"Setup failed: {e}")
        else:
            # Login
            success, error = self._auth.authenticate(username, password)
            if success:
                logger.info("Login successful for '%s'", username)
                self.login_successful.emit()
            else:
                self._show_error(error)
