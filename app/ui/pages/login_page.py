"""
Login page — shown on app startup before granting access.
Handles both first-time password setup and regular login.
"""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit

from app.services.auth_service import AuthService
from app.utils.logger import get_logger
from app.ui.theme import Colors, Spacing, ComponentSize, Typography
from app.ui.ui_helpers import (
    create_text_input, create_primary_button, create_heading,
    create_error_label, create_form_field, create_label,
    create_card, create_spacer_vertical
)

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
        """Build the login/setup card UI using modern design system."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        # Centered card
        card, layout = create_card(parent=self)
        card.setFixedWidth(400)
        layout.setContentsMargins(ComponentSize.CARD_PADDING,
                                 ComponentSize.CARD_PADDING,
                                 ComponentSize.CARD_PADDING,
                                 ComponentSize.CARD_PADDING)
        
        # Title: "Archivium"
        title = create_heading("Archivium", level=1, parent=card)
        layout.addWidget(title)

        # Subtitle
        subtitle_text = (
            "Set up your account" if not self._is_setup
            else "Sign in to continue"
        )
        subtitle = create_heading(subtitle_text, level=4, parent=card)
        layout.addWidget(subtitle)

        layout.addWidget(create_spacer_vertical(Spacing.SM))

        # Username field
        self._username_input = create_text_input("Enter username", card)
        username_field = create_form_field("Username", self._username_input, parent=card)
        layout.addWidget(username_field)
        
        if self._is_setup:
            self._username_input.setText(self._auth.get_username())

        # Password field
        self._password_input = create_text_input("Enter password", card)
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.returnPressed.connect(self._on_submit)
        password_field = create_form_field("Password", self._password_input, parent=card)
        layout.addWidget(password_field)

        # Confirm password (only during setup)
        if not self._is_setup:
            self._confirm_input = create_text_input("Confirm password", card)
            self._confirm_input.setEchoMode(QLineEdit.Password)
            self._confirm_input.returnPressed.connect(self._on_submit)
            confirm_field = create_form_field("Confirm Password", self._confirm_input, parent=card)
            layout.addWidget(confirm_field)
        else:
            self._confirm_input = None

        # Error label
        self._error_label = create_error_label("", card)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        layout.addWidget(create_spacer_vertical(Spacing.SM))

        # Submit button
        btn_text = "Create Account" if not self._is_setup else "Sign In"
        self._submit_btn = create_primary_button(btn_text, card)
        self._submit_btn.clicked.connect(self._on_submit)
        layout.addWidget(self._submit_btn)

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
