"""
Profile picture display widget.
"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout


class ProfilePictureWidget(QWidget):
    """Displays a profile picture with upload/remove actions."""

    upload_requested = Signal()
    remove_requested = Signal()

    def __init__(self, size: int = 120, editable: bool = True, parent=None):
        super().__init__(parent)
        self._size = size
        self._editable = editable
        self._path: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        self._image_label = QLabel(self)
        self._image_label.setFixedSize(self._size, self._size)
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet(
            f"border-radius: {self._size // 2}px; "
            f"background-color: #E5E5EA; "
            f"border: 2px solid #D1D1D6;"
        )
        self.set_placeholder()
        layout.addWidget(self._image_label, alignment=Qt.AlignCenter)

        if self._editable:
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            btn_layout.setContentsMargins(0, 8, 0, 0)

            self._upload_btn = QPushButton("Upload", self)
            self._upload_btn.setFixedHeight(36)
            self._upload_btn.clicked.connect(self.upload_requested.emit)
            btn_layout.addWidget(self._upload_btn)

            self._remove_btn = QPushButton("Remove", self)
            self._remove_btn.setFixedHeight(36)
            self._remove_btn.setObjectName("dangerButton")
            self._remove_btn.clicked.connect(self.remove_requested.emit)
            self._remove_btn.setVisible(False)
            btn_layout.addWidget(self._remove_btn)

            layout.addLayout(btn_layout)

    def set_image(self, path: str | None):
        """Set the profile picture from a file path."""
        self._path = path
        if path and Path(path).exists():
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # Create circular crop
                scaled = pixmap.scaled(
                    self._size, self._size,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation,
                )
                # Center crop
                x = (scaled.width() - self._size) // 2
                y = (scaled.height() - self._size) // 2
                cropped = scaled.copy(x, y, self._size, self._size)

                # Apply circular mask
                result = QPixmap(self._size, self._size)
                result.fill(Qt.transparent)
                painter = QPainter(result)
                painter.setRenderHint(QPainter.Antialiasing)
                clip = QPainterPath()
                clip.addEllipse(0, 0, self._size, self._size)
                painter.setClipPath(clip)
                painter.drawPixmap(0, 0, cropped)
                painter.end()

                self._image_label.setPixmap(result)
                self._image_label.setStyleSheet(
                    f"border-radius: {self._size // 2}px; "
                    f"background-color: transparent; "
                    f"border: none;"
                )
                if self._editable:
                    self._remove_btn.setVisible(True)
                return

        self.set_placeholder()

    def set_placeholder(self):
        """Show the default placeholder."""
        self._image_label.setText("No\nPhoto")
        self._image_label.setStyleSheet(
            f"border-radius: {self._size // 2}px; "
            f"background-color: #E5E5EA; "
            f"border: 2px solid #D1D1D6; "
            f"color: #8E8E93; "
            f"font-size: 12px;"
        )
        if self._editable and hasattr(self, "_remove_btn"):
            self._remove_btn.setVisible(False)

    @property
    def current_path(self) -> str | None:
        return self._path
