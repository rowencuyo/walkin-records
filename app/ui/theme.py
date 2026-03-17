"""
Application theme: colors, fonts, spacing, and component styling.
Professional, modern, desktop-native design (macOS-inspired).
"""
import sys


def _is_macos():
    return sys.platform == "darwin"


# ────────────────────────────────────────────────────────────
# COLOR PALETTE (macOS-inspired, calm, professional)
# ────────────────────────────────────────────────────────────

class Colors:
    """Complete color palette for consistent theming."""
    
    # === Backgrounds ===
    BG_PRIMARY = "#F5F6F8"      # Main app background
    BG_SECONDARY = "#F0F1F5"    # Secondary surfaces, subtle sections
    BG_SIDEBAR = "#F0F1F5"      # Sidebar background
    BG_CARD = "#FFFFFF"         # Cards, panels, modal backgrounds
    BG_HEADER = "#FFFFFF"       # Header/toolbar background
    BG_HOVER = "#FFFFFF"        # Hover state for inactive items
    BG_SELECTED = "#EDF2FF"     # Selected/highlighted background
    
    # === Text ===
    TEXT_PRIMARY = "#1F2933"    # Body text, primary labels
    TEXT_SECONDARY = "#6B7280"  # Secondary labels, helper text
    TEXT_TERTIARY = "#9CA3AF"   # Disabled text, metadata
    TEXT_ON_ACCENT = "#FFFFFF"  # Text on colored backgrounds
    TEXT_ON_DARK = "#F3F4F6"    # Text on dark backgrounds
    
    # === Accent (Primary Action Color) ===
    ACCENT = "#4F8EF7"          # Primary actions
    ACCENT_HOVER = "#3B7BE0"    # Hover state
    ACCENT_PRESSED = "#2D6AD0"  # Pressed state
    ACCENT_LIGHT = "#EDF2FF"    # Light accent background
    
    # === Status Colors ===
    SUCCESS = "#10B981"         # Success/positive
    SUCCESS_LIGHT = "#D1FAE5"
    WARNING = "#F59E0B"         # Warning/caution
    WARNING_LIGHT = "#FEF3C7"
    DANGER = "#EF4444"          # Error/destructive
    DANGER_HOVER = "#DC2626"
    DANGER_LIGHT = "#FEE2E2"
    INFO = "#06B6D4"            # Informational
    
    # === Borders ===
    BORDER = "#D1D5DB"          # Standard border
    BORDER_LIGHT = "#E5E7EB"    # Subtle border
    BORDER_FOCUS = "#4F8EF7"    # Focus border (accent color)
    BORDER_ERROR = "#EF4444"    # Error state border
    
    # === Interactive ===
    SELECTION = "#EDF2FF"       # Selection/highlight
    SELECTION_ACTIVE = "#DBEAFE"
    
    # === Sidebar Specific ===
    SIDEBAR_ITEM_HOVER = "#E8EAF0"
    SIDEBAR_ITEM_ACTIVE = "#EDF2FF"
    SIDEBAR_ITEM_ACTIVE_TEXT = "#4F8EF7"
    
    # === Semantic (optional, for future use) ===
    BACKGROUND = BG_PRIMARY
    FOREGROUND = TEXT_PRIMARY
    MUTED = TEXT_SECONDARY


# ────────────────────────────────────────────────────────────
# SPACING & SIZE SYSTEM (8px base, scaling up)
# ────────────────────────────────────────────────────────────

class Spacing:
    """Consistent spacing system for margins, padding, gaps."""
    # Base unit: 4px (0.5 rem)
    XS = 4       # Extra small: 4px
    SM = 8       # Small: 8px (1 rem)
    MD = 12      # Medium: 12px (1.5 rem)
    LG = 16      # Large: 16px (2 rem) — default
    XL = 24      # Extra large: 24px (3 rem)
    XXL = 32     # 2x large: 32px (4 rem)
    XXXL = 48    # 3x large: 48px (6 rem)
    
    @staticmethod
    def all_values():
        """Helper to get all spacing values."""
        return [
            Spacing.XS, Spacing.SM, Spacing.MD, Spacing.LG,
            Spacing.XL, Spacing.XXL, Spacing.XXXL
        ]


# ────────────────────────────────────────────────────────────
# COMPONENT SIZES (standardized for consistency)
# ────────────────────────────────────────────────────────────

class ComponentSize:
    """Standardized sizes for common UI components."""
    # Button heights
    BUTTON_SMALL = 32      # Small buttons (compact mode)
    BUTTON_MEDIUM = 40     # Standard button (default, forms)
    BUTTON_LARGE = 48      # Large button (primary CTA)
    
    # Input heights
    INPUT_SMALL = 32
    INPUT_MEDIUM = 40      # Standard input field
    INPUT_LARGE = 48
    
    # Icon sizes
    ICON_TINY = 16
    ICON_SMALL = 20
    ICON_MEDIUM = 24
    ICON_LARGE = 32
    ICON_XLARGE = 48
    
    # Sidebar
    SIDEBAR_WIDTH = 200
    SIDEBAR_COLLAPSED_WIDTH = 60
    
    # Header/Toolbar
    TOOLBAR_HEIGHT = 56
    
    # Spacing for list items
    LIST_ITEM_HEIGHT = 44
    LIST_ITEM_PADDING = 12
    
    # Card/panel
    CARD_PADDING = 16
    CARD_RADIUS = 8
    
    # Modal
    MODAL_MIN_WIDTH = 400
    MODAL_MIN_HEIGHT = 300
    
    # Avatar/profile pics
    AVATAR_SMALL = 32
    AVATAR_MEDIUM = 40
    AVATAR_LARGE = 64
    AVATAR_XLARGE = 96


# ────────────────────────────────────────────────────────────
# TYPOGRAPHY (Font Family & Default System)
# ────────────────────────────────────────────────────────────

class Typography:
    """Font families and text styles."""
    
    # System font families
    SYSTEM_FONT = (
        "-apple-system, 'SF Pro Display', 'SF Pro Text', "
        "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
        if _is_macos() else
        "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
    )
    
    MONOSPACE_FONT = "'Monaco', 'Courier New', monospace"
    
    # Font sizes (px)
    SIZE_XS = 11    # Tiny: captions, badges
    SIZE_SM = 13    # Small: helper text, secondary content
    SIZE_BASE = 15  # Base: body text, standard size
    SIZE_LG = 16    # Large: form labels, secondary headings
    SIZE_XL = 18    # Extra large: primary heading
    SIZE_XXL = 24   # 2xl: page title
    SIZE_XXXL = 32  # 3xl: hero title
    
    # Font weights
    WEIGHT_THIN = 300
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    
    # Line heights (ratio)
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75


FONT_FAMILY = Typography.SYSTEM_FONT


def get_stylesheet() -> str:
    """Return the application-wide stylesheet with improved styling."""
    return f"""
    /* ════════════════════════════════════════════════════════════
       GLOBAL DEFAULTS
       ════════════════════════════════════════════════════════════ */
    
    QMainWindow, QWidget {{
        background-color: {Colors.BG_PRIMARY};
        color: {Colors.TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {Typography.SIZE_BASE}px;
        line-height: {Typography.LINE_HEIGHT_NORMAL};
    }}

    QLabel, QCheckBox, QRadioButton {{
        background: transparent;
        color: {Colors.TEXT_PRIMARY};
    }}

    QLabel:disabled {{
        color: {Colors.TEXT_TERTIARY};
    }}

    /* ── Card & Panels ── */
    #card {{
        background-color: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 8px;
    }}
    
    QFrame {{
        background: transparent;
    }}

    /* ── Form Groups ── */
    QGroupBox {{
        background: transparent;
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 8px;
        margin-top: 8px;
        padding-top: 8px;
        color: {Colors.TEXT_PRIMARY};
        font-weight: 600;
        font-size: {Typography.SIZE_LG}px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
    }}


    /* ════════════════════════════════════════════════════════════
       TOOLBAR & HEADER
       ════════════════════════════════════════════════════════════ */
    
    QToolBar, #mainToolbar {{
        background-color: {Colors.BG_HEADER};
        border-bottom: 1px solid {Colors.BORDER_LIGHT};
        padding: {Spacing.SM}px {Spacing.LG}px;
        spacing: {Spacing.SM}px;
        height: {ComponentSize.TOOLBAR_HEIGHT}px;
    }}

    #toolbarTitle {{
        font-size: {Typography.SIZE_XL}px;
        font-weight: {Typography.WEIGHT_BOLD};
        color: {Colors.TEXT_PRIMARY};
        padding: 0 {Spacing.SM}px;
        background: transparent;
    }}


    /* ════════════════════════════════════════════════════════════
       SIDEBAR NAVIGATION
       ════════════════════════════════════════════════════════════ */
    
    #sidebar {{
        background-color: {Colors.BG_SIDEBAR};
        border-right: 1px solid {Colors.BORDER_LIGHT};
        min-width: {ComponentSize.SIDEBAR_WIDTH}px;
        max-width: {ComponentSize.SIDEBAR_WIDTH}px;
    }}

    #sidebar > QLabel {{
        font-size: {Typography.SIZE_SM}px;
        font-weight: {Typography.WEIGHT_BOLD};
        color: {Colors.TEXT_PRIMARY};
        padding: {Spacing.LG}px {Spacing.LG}px {Spacing.SM}px {Spacing.LG}px;
        letter-spacing: 0.5px;
    }}

    #sidebar QPushButton {{
        text-align: left;
        padding: {Spacing.MD}px {Spacing.LG}px;
        border: none;
        border-radius: 6px;
        margin: {Spacing.XS}px {Spacing.MD}px;
        font-size: {Typography.SIZE_BASE}px;
        font-weight: {Typography.WEIGHT_NORMAL};
        color: {Colors.TEXT_PRIMARY};
        background: transparent;
        height: auto;
    }}

    #sidebar QPushButton:hover {{
        background-color: {Colors.SIDEBAR_ITEM_HOVER};
    }}

    #sidebar QPushButton[active="true"] {{
        background-color: {Colors.SIDEBAR_ITEM_ACTIVE};
        color: {Colors.SIDEBAR_ITEM_ACTIVE_TEXT};
        font-weight: {Typography.WEIGHT_SEMIBOLD};
    }}

    #sidebar QPushButton:focus {{
        outline: none;
        border: 1px solid {Colors.BORDER_FOCUS};
    }}


    /* ════════════════════════════════════════════════════════════
       TYPOGRAPHY & TEXT
       ════════════════════════════════════════════════════════════ */
    
    #pageTitle {{
        font-size: {Typography.SIZE_XXL}px;
        font-weight: {Typography.WEIGHT_BOLD};
        color: {Colors.TEXT_PRIMARY};
        padding: 0px;
        margin: 0px;
        letter-spacing: -0.5px;
    }}

    #sectionTitle {{
        font-size: {Typography.SIZE_XL}px;
        font-weight: {Typography.WEIGHT_SEMIBOLD};
        color: {Colors.TEXT_PRIMARY};
        padding: {Spacing.SM}px 0;
        margin: 0;
    }}

    #subtitleLabel {{
        font-size: {Typography.SIZE_BASE}px;
        color: {Colors.TEXT_SECONDARY};
        font-weight: {Typography.WEIGHT_NORMAL};
    }}

    #fieldLabel {{
        font-size: {Typography.SIZE_LG}px;
        font-weight: {Typography.WEIGHT_MEDIUM};
        color: {Colors.TEXT_PRIMARY};
    }}

    #helperText {{
        font-size: {Typography.SIZE_SM}px;
        color: {Colors.TEXT_SECONDARY};
        font-weight: {Typography.WEIGHT_NORMAL};
    }}

    #errorLabel {{
        font-size: {Typography.SIZE_SM}px;
        color: {Colors.DANGER};
        font-weight: {Typography.WEIGHT_MEDIUM};
    }}


    /* ════════════════════════════════════════════════════════════
       BUTTONS (Standardized sizing & states)
       ════════════════════════════════════════════════════════════ */
    
    QPushButton {{
        padding: {Spacing.MD}px {Spacing.LG}px;
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        background-color: {Colors.BG_CARD};
        color: {Colors.TEXT_PRIMARY};
        font-size: {Typography.SIZE_BASE}px;
        font-weight: {Typography.WEIGHT_MEDIUM};
        min-height: {ComponentSize.BUTTON_MEDIUM}px;
        outline: none;
    }}

    QPushButton:hover {{
        background-color: {Colors.BG_SECONDARY};
        border-color: {Colors.BORDER};
    }}

    QPushButton:pressed {{
        background-color: {Colors.BG_SECONDARY};
        border-color: {Colors.ACCENT};
    }}

    QPushButton:focus {{
        border-color: {Colors.BORDER_FOCUS};
        outline: none;
    }}

    QPushButton:disabled {{
        background-color: {Colors.BG_SECONDARY};
        color: {Colors.TEXT_TERTIARY};
        border-color: {Colors.BORDER_LIGHT};
    }}

    /* === Primary Button (Main CTA) === */
    QPushButton#primaryButton {{
        background-color: {Colors.ACCENT};
        border: none;
        color: {Colors.TEXT_ON_ACCENT};
        font-weight: {Typography.WEIGHT_SEMIBOLD};
        min-height: {ComponentSize.BUTTON_MEDIUM}px;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {Colors.ACCENT_HOVER};
    }}

    QPushButton#primaryButton:pressed {{
        background-color: {Colors.ACCENT_PRESSED};
    }}

    QPushButton#primaryButton:focus {{
        border: 2px solid {Colors.BORDER_FOCUS};
        padding: calc({Spacing.MD}px - 1px) calc({Spacing.LG}px - 1px);
    }}

    QPushButton#primaryButton:disabled {{
        background-color: {Colors.BORDER_LIGHT};
        color: {Colors.TEXT_TERTIARY};
    }}

    /* === Danger Button (Destructive Actions) === */
    QPushButton#dangerButton {{
        background-color: {Colors.DANGER};
        border: none;
        color: {Colors.TEXT_ON_ACCENT};
        font-weight: {Typography.WEIGHT_SEMIBOLD};
    }}

    QPushButton#dangerButton:hover {{
        background-color: {Colors.DANGER_HOVER};
    }}

    QPushButton#dangerButton:pressed {{
        background-color: #991B1B;
    }}

    QPushButton#dangerButton:disabled {{
        background-color: {Colors.BORDER_LIGHT};
        color: {Colors.TEXT_TERTIARY};
    }}

    /* === Secondary Button === */
    QPushButton#secondaryButton {{
        background-color: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        color: {Colors.TEXT_PRIMARY};
        font-weight: {Typography.WEIGHT_MEDIUM};
    }}

    QPushButton#secondaryButton:hover {{
        background-color: {Colors.BG_SECONDARY};
    }}


    /* ════════════════════════════════════════════════════════════
       FORM INPUTS
       ════════════════════════════════════════════════════════════ */
    
    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
        padding: {Spacing.MD}px {Spacing.MD}px;
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        background-color: {Colors.BG_CARD};
        color: {Colors.TEXT_PRIMARY};
        font-size: {Typography.SIZE_BASE}px;
        selection-background-color: {Colors.SELECTION_ACTIVE};
        min-height: {ComponentSize.INPUT_MEDIUM}px;
    }}

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus, 
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {Colors.BORDER_FOCUS};
        padding: calc({Spacing.MD}px - 1px) calc({Spacing.MD}px - 1px);
        background-color: {Colors.BG_CARD};
    }}

    QLineEdit:disabled, QComboBox:disabled {{
        background-color: {Colors.BG_SECONDARY};
        color: {Colors.TEXT_TERTIARY};
        border-color: {Colors.BORDER_LIGHT};
    }}

    /* === Combobox Dropdown === */
    QComboBox::drop-down {{
        border: none;
        width: {ComponentSize.ICON_MEDIUM}px;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        width: {ComponentSize.ICON_SMALL}px;
        height: {ComponentSize.ICON_SMALL}px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        selection-background-color: {Colors.SELECTION_ACTIVE};
        padding: {Spacing.SM}px 0;
    }}


    /* ════════════════════════════════════════════════════════════
       CALENDAR WIDGET
       ════════════════════════════════════════════════════════════ */
    
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background-color: {Colors.BG_SECONDARY};
        border-bottom: 1px solid {Colors.BORDER_LIGHT};
    }}
    
    QCalendarWidget QToolButton {{
        color: {Colors.TEXT_PRIMARY};
        background-color: transparent;
        border: none;
        padding: {Spacing.SM}px;
        font-weight: {Typography.WEIGHT_SEMIBOLD};
        border-radius: 4px;
    }}
    
    QCalendarWidget QToolButton:hover {{
        background-color: {Colors.BORDER_LIGHT};
    }}
    
    QCalendarWidget QMenu {{
        background-color: {Colors.BG_CARD};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_LIGHT};
    }}
    
    QCalendarWidget QSpinBox {{
        background-color: {Colors.BG_CARD};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_LIGHT};
    }}
    
    QCalendarWidget QAbstractItemView:enabled {{
        color: {Colors.TEXT_PRIMARY};
        background-color: {Colors.BG_CARD};
        selection-background-color: {Colors.SELECTION_ACTIVE};
        selection-color: {Colors.TEXT_PRIMARY};
    }}


    /* ════════════════════════════════════════════════════════════
       TABLE VIEW
       ════════════════════════════════════════════════════════════ */
    
    QTableView {{
        background-color: {Colors.BG_CARD};
        alternate-background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 8px;
        gridline-color: {Colors.BORDER_LIGHT};
        selection-background-color: {Colors.SELECTION_ACTIVE};
        selection-color: {Colors.TEXT_PRIMARY};
        font-size: {Typography.SIZE_BASE}px;
    }}

    QTableView::item {{
        padding: {Spacing.MD}px {Spacing.MD}px;
        border: none;
    }}

    QTableView::item:selected {{
        background-color: {Colors.SELECTION_ACTIVE};
        color: {Colors.TEXT_PRIMARY};
    }}

    QTableView::item:hover {{
        background-color: {Colors.BG_SECONDARY};
    }}

    QHeaderView::section {{
        background-color: {Colors.BG_SECONDARY};
        color: {Colors.TEXT_SECONDARY};
        padding: {Spacing.MD}px {Spacing.MD}px;
        border: none;
        border-bottom: 1px solid {Colors.BORDER_LIGHT};
        font-weight: {Typography.WEIGHT_SEMIBOLD};
        font-size: {Typography.SIZE_SM}px;
    }}


    /* ════════════════════════════════════════════════════════════
       SCROLLBARS
       ════════════════════════════════════════════════════════════ */
    
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
        background: {Colors.TEXT_SECONDARY};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
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
        background: {Colors.TEXT_SECONDARY};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
        width: 0;
        border: none;
    }}


    /* ════════════════════════════════════════════════════════════
       STATUS BAR
       ════════════════════════════════════════════════════════════ */
    
    QStatusBar {{
        background-color: {Colors.BG_SECONDARY};
        border-top: 1px solid {Colors.BORDER_LIGHT};
        color: {Colors.TEXT_SECONDARY};
        font-size: {Typography.SIZE_SM}px;
        padding: {Spacing.SM}px {Spacing.LG}px;
    }}


    /* ════════════════════════════════════════════════════════════
       TAB WIDGET
       ════════════════════════════════════════════════════════════ */
    
    QTabWidget::pane {{
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 8px;
        background-color: {Colors.BG_CARD};
    }}

    QTabBar::tab {{
        padding: {Spacing.MD}px {Spacing.LG}px;
        border: none;
        color: {Colors.TEXT_SECONDARY};
        font-size: {Typography.SIZE_BASE}px;
        border-bottom: 2px solid transparent;
    }}

    QTabBar::tab:selected {{
        color: {Colors.ACCENT};
        border-bottom-color: {Colors.ACCENT};
        font-weight: {Typography.WEIGHT_SEMIBOLD};
    }}

    QTabBar::tab:hover {{
        color: {Colors.TEXT_PRIMARY};
    }}


    /* ════════════════════════════════════════════════════════════
       TOOLTIPS
       ════════════════════════════════════════════════════════════ */
    
    QToolTip {{
        background-color: {Colors.TEXT_PRIMARY};
        color: {Colors.TEXT_ON_DARK};
        border: none;
        padding: {Spacing.SM}px {Spacing.MD}px;
        border-radius: 6px;
        font-size: {Typography.SIZE_SM}px;
    }}

    """
    return stylesheet

