"""
UI Helper Functions — Standardized, reusable component builders.
Ensures consistency across all UI pages without duplicating code.
Eliminates inline styles and promotes design system usage.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QPushButton, QLineEdit, QComboBox, QLabel, QVBoxLayout,
    QHBoxLayout, QFrame, QWidget, QDateEdit, QTextEdit, QPlainTextEdit,
)
from PySide6.QtGui import QFont

from app.ui.theme import Colors, Spacing, ComponentSize, Typography


# ────────────────────────────────────────────────────────────
# BUTTONS (Standardized, reusable button builders)
# ────────────────────────────────────────────────────────────

def create_primary_button(text: str, parent=None) -> QPushButton:
    """Create a primary action button (blue, filled, high emphasis)."""
    btn = QPushButton(text, parent)
    btn.setObjectName("primaryButton")
    btn.setMinimumHeight(ComponentSize.BUTTON_MEDIUM)
    return btn


def create_secondary_button(text: str, parent=None) -> QPushButton:
    """Create a secondary button (outline, medium emphasis)."""
    btn = QPushButton(text, parent)
    btn.setObjectName("secondaryButton")
    btn.setMinimumHeight(ComponentSize.BUTTON_MEDIUM)
    return btn


def create_danger_button(text: str, parent=None) -> QPushButton:
    """Create a destructive action button (red, filled, for delete/discard)."""
    btn = QPushButton(text, parent)
    btn.setObjectName("dangerButton")
    btn.setMinimumHeight(ComponentSize.BUTTON_MEDIUM)
    return btn


def create_small_button(text: str, parent=None) -> QPushButton:
    """Create a small action button (compact, secondary actions)."""
    btn = QPushButton(text, parent)
    btn.setMinimumHeight(ComponentSize.BUTTON_SMALL)
    return btn


# ────────────────────────────────────────────────────────────
# FORM INPUTS (Standardized input fields)
# ────────────────────────────────────────────────────────────

def create_text_input(placeholder: str = "", parent=None) -> QLineEdit:
    """Create a standard text input field."""
    field = QLineEdit(parent)
    field.setPlaceholderText(placeholder)
    field.setMinimumHeight(ComponentSize.INPUT_MEDIUM)
    return field


def create_combobox(items: list[str] | None = None, parent=None) -> QComboBox:
    """Create a standard dropdown/combobox."""
    combo = QComboBox(parent)
    combo.setMinimumHeight(ComponentSize.INPUT_MEDIUM)
    if items:
        combo.addItems(items)
    return combo


def create_multiline_input(placeholder: str = "", parent=None) -> QPlainTextEdit:
    """Create a multiline text input (remarks, notes, etc.)."""
    field = QPlainTextEdit(parent)
    field.setPlaceholderText(placeholder)
    field.setMinimumHeight(ComponentSize.INPUT_LARGE * 1.5)
    return field


def create_date_input(parent=None) -> QDateEdit:
    """Create a date picker field."""
    field = QDateEdit(parent)
    field.setMinimumHeight(ComponentSize.INPUT_MEDIUM)
    field.setCalendarPopup(True)
    field.setDisplayFormat("yyyy-MM-dd")
    return field


# ────────────────────────────────────────────────────────────
# LABELS & TEXT (Semantic typography helpers)
# ────────────────────────────────────────────────────────────

def create_heading(text: str, level: int = 1, parent=None) -> QLabel:
    """Create a heading with semantic sizing (level 1=largest, 4=smallest)."""
    label = QLabel(text, parent)
    
    if level == 1:
        label.setObjectName("pageTitle")
        label.setFont(QFont(Typography.SYSTEM_FONT, Typography.SIZE_XXL,
                           QFont.Bold))
    elif level == 2:
        label.setObjectName("sectionTitle")
        label.setFont(QFont(Typography.SYSTEM_FONT, Typography.SIZE_XL,
                           QFont.SemiBold))
    elif level == 3:
        label.setFont(QFont(Typography.SYSTEM_FONT, Typography.SIZE_LG,
                           QFont.SemiBold))
    else:  # level 4+
        label.setObjectName("fieldLabel")
        label.setFont(QFont(Typography.SYSTEM_FONT, Typography.SIZE_BASE,
                           QFont.Medium))
    
    label.setWordWrap(True)
    return label


def create_label(text: str, parent=None) -> QLabel:
    """Create a standard label (form labels, annotations)."""
    label = QLabel(text, parent)
    label.setObjectName("fieldLabel")
    return label


def create_helper_text(text: str, parent=None) -> QLabel:
    """Create helper/secondary text (smaller, lighter color)."""
    label = QLabel(text, parent)
    label.setObjectName("helperText")
    label.setWordWrap(True)
    return label


def create_error_label(text: str, parent=None) -> QLabel:
    """Create error message label (red, prominent)."""
    label = QLabel(text, parent)
    label.setObjectName("errorLabel")
    label.setWordWrap(True)
    return label


# ────────────────────────────────────────────────────────────
# FORM SECTIONS & CONTAINERS (Layout helpers)
# ────────────────────────────────────────────────────────────

def create_form_section(title: str, parent=None) -> tuple[QWidget, QVBoxLayout]:
    """Create a labeled form section with consistent spacing.
    
    Returns (container_widget, content_layout) for adding fields.
    """
    container = QWidget(parent)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(Spacing.MD)
    
    if title:
        title_label = create_heading(title, level=3)
        layout.addWidget(title_label)
    
    return container, layout


def create_form_field(label_text: str, widget: QWidget, 
                      helper_text: str = "",
                      error_text: str = "",
                      parent=None) -> QWidget:
    """Create a complete form field with label, input, and optional helper/error text.
    
    Args:
        label_text: Label above the field
        widget: Input widget (QLineEdit, QComboBox, etc.)
        helper_text: Optional helper/secondary text
        error_text: Optional error message
        parent: Parent widget
    
    Returns:
        Container widget with all elements
    """
    container = QWidget(parent)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(Spacing.SM)
    
    # Label
    label = create_label(label_text)
    layout.addWidget(label)
    
    # Input widget
    layout.addWidget(widget)
    
    # Helper text (below field, lighter)
    if helper_text:
        helper = create_helper_text(helper_text)
        layout.addWidget(helper)
    
    # Error text (red, if present)
    if error_text:
        error = create_error_label(error_text)
        layout.addWidget(error)
    
    return container


def create_button_group(buttons: list[tuple[str, str]],
                       parent=None) -> tuple[QWidget, dict[str, QPushButton]]:
    """Create a horizontal group of buttons.
    
    Args:
        buttons: List of (button_label, button_type) tuples
                 button_type: "primary", "secondary", "danger", "small"
        parent: Parent widget
    
    Returns:
        (container_widget, button_dict) where button_dict maps labels to buttons
    """
    container = QWidget(parent)
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(Spacing.MD)
    
    button_dict = {}
    for label, btn_type in buttons:
        if btn_type == "primary":
            btn = create_primary_button(label)
        elif btn_type == "danger":
            btn = create_danger_button(label)
        elif btn_type == "small":
            btn = create_small_button(label)
        else:  # "secondary" or default
            btn = create_secondary_button(label)
        
        layout.addWidget(btn)
        button_dict[label] = btn
    
    layout.addStretch()  # Push buttons to the left
    return container, button_dict


def create_card(title: str = "", parent=None) -> tuple[QFrame, QVBoxLayout]:
    """Create a card/panel container with consistent styling.
    
    Returns (card_widget, content_layout) for adding child elements.
    """
    card = QFrame(parent)
    card.setObjectName("card")
    
    layout = QVBoxLayout(card)
    layout.setContentsMargins(ComponentSize.CARD_PADDING, ComponentSize.CARD_PADDING,
                             ComponentSize.CARD_PADDING, ComponentSize.CARD_PADDING)
    layout.setSpacing(Spacing.LG)
    
    if title:
        title_label = create_heading(title, level=3)
        layout.addWidget(title_label)
    
    return card, layout


def create_spacer_vertical(size: int = Spacing.LG) -> QWidget:
    """Create a vertical spacing widget."""
    spacer = QWidget()
    spacer.setFixedHeight(size)
    return spacer


def create_spacer_horizontal(size: int = Spacing.LG) -> QWidget:
    """Create a horizontal spacing widget."""
    spacer = QWidget()
    spacer.setFixedWidth(size)
    return spacer


# ────────────────────────────────────────────────────────────
# DIVIDERS & VISUAL SEPARATORS
# ────────────────────────────────────────────────────────────

def create_horizontal_line(parent=None) -> QFrame:
    """Create a horizontal divider line."""
    line = QFrame(parent)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")
    line.setFixedHeight(1)
    return line


def create_vertical_line(parent=None) -> QFrame:
    """Create a vertical divider line."""
    line = QFrame(parent)
    line.setFrameShape(QFrame.VLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")
    line.setFixedWidth(1)
    return line


# ────────────────────────────────────────────────────────────
# BATCH HELPERS (Create multiple consistent elements)
# ────────────────────────────────────────────────────────────

def create_form_fields_from_spec(spec: list[dict], parent=None) -> dict[str, QWidget]:
    """Create multiple form fields from specification.
    
    Args:
        spec: List of dicts with keys: "name", "label", "type", "items" (for combo),
              "helper", "placeholder"
        parent: Parent widget
    
    Returns:
        Dict mapping field names to their widget containers
    """
    fields = {}
    
    for field_spec in spec:
        name = field_spec.get("name", "")
        label = field_spec.get("label", name)
        field_type = field_spec.get("type", "text")  # text, combo, multiline, date
        helper = field_spec.get("helper", "")
        placeholder = field_spec.get("placeholder", "")
        items = field_spec.get("items", [])
        
        # Create the appropriate input widget
        if field_type == "combo":
            widget = create_combobox(items, parent)
        elif field_type == "multiline":
            widget = create_multiline_input(placeholder, parent)
        elif field_type == "date":
            widget = create_date_input(parent)
        else:  # "text" or default
            widget = create_text_input(placeholder, parent)
        
        # Wrap in form field container
        field_container = create_form_field(label, widget, helper, "", parent)
        fields[name] = field_container
    
    return fields
