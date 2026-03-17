"""
Global keyboard shortcuts handler for the application.
Handles common shortcuts like Cmd+N (new record), Cmd+F (search), etc.
"""
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QWidget

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ShortcutsManager(QObject):
    """Manages global keyboard shortcuts for the application."""
    
    # Signals for shortcut actions
    new_record = Signal()
    search_focused = Signal()
    export_records = Signal()
    close_dialog = Signal()
    open_settings = Signal()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent_widget = parent
        self._shortcuts = {}
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        """Register all keyboard shortcuts."""
        # New Record: Cmd+N (macOS) / Ctrl+N (Windows/Linux)
        self._register_shortcut(
            QKeySequence.New,
            lambda: self.new_record.emit(),
            "New Record"
        )
        
        # Search: Cmd+F / Ctrl+F
        self._register_shortcut(
            QKeySequence.Find,
            lambda: self.search_focused.emit(),
            "Focus Search"
        )
        
        # Export: Cmd+Shift+E / Ctrl+Shift+E
        self._register_shortcut(
            QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_E),
            lambda: self.export_records.emit(),
            "Export Records",
            is_cross_platform=False
        )
        
        # Close: Escape
        self._register_shortcut(
            QKeySequence.Close,
            lambda: self.close_dialog.emit(),
            "Close Dialog"
        )
        
        # Settings: Cmd+, / Ctrl+,
        self._register_shortcut(
            QKeySequence(Qt.CTRL | Qt.Key_Comma),
            lambda: self.open_settings.emit(),
            "Open Settings",
            is_cross_platform=False
        )
        
        logger.info("Keyboard shortcuts initialized")
    
    def _register_shortcut(
        self,
        key_sequence: QKeySequence,
        callback,
        name: str,
        is_cross_platform: bool = True
    ):
        """Register a single keyboard shortcut."""
        try:
            shortcut = QShortcut(key_sequence, self.parent_widget)
            shortcut.activated.connect(callback)
            self._shortcuts[name] = shortcut
            # Try to get string representation, fallback to name if not available
            try:
                key_str = key_sequence.toString()
            except Exception:
                key_str = name
            logger.debug(f"Registered shortcut: {name} ({key_str})")
        except Exception as e:
            logger.warning(f"Failed to register shortcut {name}: {e}")
    
    def get_shortcut_keys(self) -> dict[str, str]:
        """Return human-readable shortcut keys for help display."""
        return {
            "New Record": "⌘N" if self._is_macos() else "Ctrl+N",
            "Search": "⌘F" if self._is_macos() else "Ctrl+F",
            "Export": "⌘⇧E" if self._is_macos() else "Ctrl+Shift+E",
            "Close": "Esc",
            "Settings": "⌘," if self._is_macos() else "Ctrl+,",
        }
    
    @staticmethod
    def _is_macos() -> bool:
        """Check if running on macOS."""
        import sys
        return sys.platform == "darwin"
