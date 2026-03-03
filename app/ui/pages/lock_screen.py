"""
Lock screen — shown on manual lock or idle auto-lock.
Password-only entry, username displayed but not editable.
"""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpacerItem, QSizePolicy,
)

from app.services.auth_service import AuthService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LockScreen(QWidget):
    """Session lock screen — password-only unlock."""

    unlock_successful = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth = AuthService()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        # Centered card
        card = QWidget()
        card.setFixedWidth(360)
        card.setStyleSheet(
            "QWidget { background-color: #FFFFFF; border-radius: 12px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 40, 32, 32)
        card_layout.setSpacing(16)

        # Lock icon / title
        title = QLabel("Locked")
        title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #1D1D1F; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        username = self._auth.get_username()
        user_label = QLabel(username)
        user_label.setStyleSheet(
            "font-size: 14px; color: #6E6E73; background: transparent;"
        )
        user_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(user_label)

        card_layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Password input
        pw_label = QLabel("Password")
        pw_label.setStyleSheet(
            "font-size: 13px; font-weight: 500; color: #1D1D1F; background: transparent;"
        )
        card_layout.addWidget(pw_label)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Enter password to unlock")
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.setFixedHeight(38)
        self._password_input.returnPressed.connect(self._on_unlock)
        card_layout.addWidget(self._password_input)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet(
            "color: #FF3B30; font-size: 13px; background: transparent;"
        )
        self._error_label.setVisible(False)
        card_layout.addWidget(self._error_label)

        card_layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Unlock button
        unlock_btn = QPushButton("Unlock")
        unlock_btn.setObjectName("primaryButton")
        unlock_btn.setFixedHeight(40)
        unlock_btn.clicked.connect(self._on_unlock)
        card_layout.addWidget(unlock_btn)

        outer.addWidget(card)

    def focus_password(self):
        """Focus the password field when shown."""
        self._password_input.clear()
        self._error_label.setVisible(False)
        self._password_input.setFocus()

    def _on_unlock(self):
        password = self._password_input.text()
        if not password:
            self._error_label.setText("Password is required")
            self._error_label.setVisible(True)
            return

        success, error = self._auth.authenticate_password_only(password)
        if success:
            logger.info("Session unlocked")
            self.unlock_successful.emit()
        else:
            self._error_label.setText(error)
            self._error_label.setVisible(True)
            self._password_input.clear()
            self._password_input.setFocus()
