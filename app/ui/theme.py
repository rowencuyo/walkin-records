"""
Application theme: colors, fonts, and stylesheet.
Professional, calm, desktop-native design.
"""
import sys


def _is_macos():
    return sys.platform == "darwin"


# ── Color Palette ──
class Colors:
    # Backgrounds
    BG_PRIMARY = "#FFFFFF"     # White
    BG_SECONDARY = "#F5F5F5"   # Light Gray 1
    BG_SIDEBAR = "#F5F5F5"
    BG_CARD = "#FFFFFF"
    BG_HEADER = "#FFFFFF"

    # Text
    TEXT_PRIMARY = "#212121"   # Dark Gray
    TEXT_SECONDARY = "#757575" # Mid Gray
    TEXT_TERTIARY = "#9E9E9E"  # Lighter Mid Gray
    TEXT_ON_ACCENT = "#FFFFFF" # White

    # Accent (Light Blue)
    ACCENT = "#4A90E2"         # Soft Light Blue
    ACCENT_HOVER = "#357ABD"   # Slightly darker blue
    ACCENT_PRESSED = "#2A6496" # Dark blue

    # Status (Converted to Grayscale)
    SUCCESS = "#757575"        # Mid Gray
    WARNING = "#616161"        # Mid-Dark Gray
    DANGER = "#424242"         # Dark Gray
    DANGER_HOVER = "#212121"

    # Borders
    BORDER = "#E0E0E0"         # Light Gray 2
    BORDER_LIGHT = "#EEEEEE"   # Light Gray 3
    BORDER_FOCUS = "#4A90E2"   # Light Blue Focus

    # Selection
    SELECTION = "#EBF4FA"      # Very Light Blue
    SELECTION_ACTIVE = "#D6EAF8" # Light Blue Tint

    # Sidebar
    SIDEBAR_ITEM_HOVER = "#EEEEEE" # Light Gray 3
    SIDEBAR_ITEM_ACTIVE = "#EBF4FA" # Very Light Blue
    SIDEBAR_ITEM_ACTIVE_TEXT = "#4A90E2" # Light Blue


# ── Spacing ──
class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


# ── Font ──
def get_font_family():
    if _is_macos():
        return "-apple-system, 'SF Pro Text', 'Helvetica Neue', sans-serif"
    return "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


FONT_FAMILY = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
if _is_macos():
    FONT_FAMILY = "-apple-system, 'SF Pro Text', 'Helvetica Neue', sans-serif"


def get_stylesheet() -> str:
    """Return the application-wide stylesheet."""
    return f"""
    /* ── Global ── */
    QMainWindow, QWidget {{
        background-color: {Colors.BG_PRIMARY};
        color: {Colors.TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: 16px;
    }}

    /* ── Sidebar ── */
    #sidebar {{
        background-color: {Colors.BG_SIDEBAR};
        border-right: 1px solid {Colors.BORDER_LIGHT};
    }}

    #sidebar QPushButton {{
        text-align: left;
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        margin: 2px 8px;
        font-size: 15px;
        color: {Colors.TEXT_PRIMARY};
        background: transparent;
    }}

    #sidebar QPushButton:hover {{
        background-color: {Colors.SIDEBAR_ITEM_HOVER};
    }}

    #sidebar QPushButton[active="true"] {{
        background-color: {Colors.SIDEBAR_ITEM_ACTIVE};
        color: {Colors.SIDEBAR_ITEM_ACTIVE_TEXT};
        font-weight: 600;
    }}

    /* ── Headers ── */
    #pageTitle {{
        font-size: 26px;
        font-weight: 700;
        color: {Colors.TEXT_PRIMARY};
        padding: 0px;
        margin: 0px;
    }}

    #sectionTitle {{
        font-size: 18px;
        font-weight: 600;
        color: {Colors.TEXT_PRIMARY};
        padding: 4px 0;
    }}

    /* ── Buttons ── */
    QPushButton {{
        padding: 8px 20px;
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        background-color: {Colors.BG_CARD};
        color: {Colors.TEXT_PRIMARY};
        font-size: 15px;
    }}

    QPushButton:hover {{
        background-color: {Colors.BG_SECONDARY};
        border-color: {Colors.BORDER};
    }}

    QPushButton:pressed {{
        background-color: {Colors.BORDER_LIGHT};
    }}

    QPushButton#primaryButton {{
        background-color: {Colors.ACCENT};
        border: none;
        color: {Colors.TEXT_ON_ACCENT};
        font-weight: 600;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {Colors.ACCENT_HOVER};
    }}

    QPushButton#primaryButton:pressed {{
        background-color: {Colors.ACCENT_PRESSED};
    }}

    QPushButton#dangerButton {{
        background-color: {Colors.DANGER};
        border: none;
        color: {Colors.TEXT_ON_ACCENT};
        font-weight: 600;
    }}

    QPushButton#dangerButton:hover {{
        background-color: {Colors.DANGER_HOVER};
    }}

    /* ── Inputs ── */
    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {{
        padding: 8px 12px;
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        background-color: {Colors.BG_CARD};
        color: {Colors.TEXT_PRIMARY};
        font-size: 15px;
        selection-background-color: {Colors.SELECTION_ACTIVE};
    }}

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {Colors.BORDER_FOCUS};
    }}

    QLineEdit:disabled, QComboBox:disabled {{
        background-color: {Colors.BG_SECONDARY};
        color: {Colors.TEXT_TERTIARY};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox::down-arrow {{
        width: 10px;
        height: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        selection-background-color: {Colors.SELECTION};
    }}

    /* ── Table View ── */
    QTableView {{
        background-color: {Colors.BG_CARD};
        alternate-background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 8px;
        gridline-color: {Colors.BORDER_LIGHT};
        selection-background-color: {Colors.SELECTION_ACTIVE};
        selection-color: {Colors.TEXT_PRIMARY};
        font-size: 15px;
    }}

    QTableView::item {{
        padding: 8px 10px;
        border: none;
    }}

    QTableView::item:selected {{
        background-color: {Colors.SELECTION_ACTIVE};
        color: {Colors.TEXT_PRIMARY};
    }}

    QHeaderView::section {{
        background-color: {Colors.BG_SECONDARY};
        color: {Colors.TEXT_SECONDARY};
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {Colors.BORDER_LIGHT};
        font-weight: 600;
        font-size: 14px;
    }}

    /* ── ScrollBar ── */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {Colors.BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {Colors.TEXT_TERTIARY};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
        height: 0;
        border: none;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {Colors.BORDER};
        border-radius: 4px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {Colors.TEXT_TERTIARY};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
        width: 0;
        border: none;
    }}

    /* ── Labels ── */
    QLabel {{
        color: {Colors.TEXT_PRIMARY};
    }}

    QLabel#fieldLabel {{
        color: {Colors.TEXT_SECONDARY};
        font-size: 14px;
        font-weight: 500;
    }}

    QLabel#errorLabel {{
        color: {Colors.DANGER};
        font-size: 14px;
    }}

    QLabel#subtitleLabel {{
        color: {Colors.TEXT_SECONDARY};
        font-size: 15px;
    }}

    /* ── Status Bar ── */
    QStatusBar {{
        background-color: {Colors.BG_SECONDARY};
        border-top: 1px solid {Colors.BORDER_LIGHT};
        color: {Colors.TEXT_SECONDARY};
        font-size: 14px;
    }}

    /* ── Tab Bar ── */
    QTabWidget::pane {{
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 8px;
        background-color: {Colors.BG_CARD};
    }}

    QTabBar::tab {{
        padding: 8px 16px;
        border: none;
        color: {Colors.TEXT_SECONDARY};
        font-size: 15px;
    }}

    QTabBar::tab:selected {{
        color: {Colors.ACCENT};
        border-bottom: 2px solid {Colors.ACCENT};
        font-weight: 600;
    }}

    /* ── Message Box ── */
    QMessageBox {{
        background-color: {Colors.BG_PRIMARY};
    }}

    /* ── Tooltip ── */
    QToolTip {{
        background-color: {Colors.TEXT_PRIMARY};
        color: {Colors.TEXT_ON_ACCENT};
        border: none;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 14px;
    }}

    /* ── Group Box ── */
    QGroupBox {{
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 8px;
        margin-top: 16px;
        padding: 16px 12px 12px 12px;
        font-weight: 600;
        color: {Colors.TEXT_PRIMARY};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {Colors.TEXT_PRIMARY};
    }}
    """
