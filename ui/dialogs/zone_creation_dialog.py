"""
Styled dialog for creating a new zone by entering dimensions.
Matches the app's design system (same look as ConfirmDialog).

Uses plain QLineEdit widgets for all numeric fields so macOS native
spin-box stepper buttons never appear.
"""

import os

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox,
                             QPushButton, QWidget, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from ui.styles.base_styles import Colors, Typography
from ui.styles.component_styles import ButtonStyles

# Path to the shared chevron SVG that already exists in ui/resources/
_ARROW_SVG = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "resources", "arrow_down.svg")
).replace("\\", "/")   # Qt stylesheet url() requires forward slashes


# ── Shared style blocks ────────────────────────────────────────────────────

_LABEL_STYLE = f"""
    QLabel {{
        color: {Colors.TEXT_SECONDARY};
        font-size: {Typography.FONT_SIZE_SM};
        font-weight: {Typography.FONT_WEIGHT_MEDIUM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        background: transparent;
        border: none;
        padding-right: 8px;
    }}
"""

_INPUT_STYLE = f"""
    QLineEdit {{
        border: 1px solid {Colors.BORDER_MEDIUM};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: {Typography.FONT_SIZE_SM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        color: {Colors.TEXT_PRIMARY};
        background-color: {Colors.WHITE};
        min-height: 32px;
        max-height: 32px;
    }}
    QLineEdit:focus {{
        border-color: {Colors.PRIMARY};
        outline: none;
    }}
    QLineEdit::placeholder {{
        color: {Colors.TEXT_MUTED};
    }}
"""

_UNIT_STYLE = f"""
    QLabel {{
        color: {Colors.TEXT_MUTED};
        font-size: {Typography.FONT_SIZE_SM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        background: transparent;
        border: none;
        padding-left: 6px;
        min-width: 24px;
    }}
"""

_COMBO_STYLE = f"""
    QComboBox {{
        border: 1px solid {Colors.BORDER_MEDIUM};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: {Typography.FONT_SIZE_SM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        color: {Colors.TEXT_PRIMARY};
        background-color: {Colors.WHITE};
        min-height: 32px;
        max-height: 32px;
    }}
    QComboBox:focus {{
        border-color: {Colors.PRIMARY};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
        subcontrol-origin: padding;
        subcontrol-position: center right;
    }}
    QComboBox::down-arrow {{
        image: url({_ARROW_SVG});
        width: 10px;
        height: 6px;
    }}
    QComboBox QAbstractItemView {{
        border: 1px solid {Colors.BORDER_MEDIUM};
        border-radius: 4px;
        background-color: {Colors.WHITE};
        selection-background-color: {Colors.PRIMARY_LIGHT};
        selection-color: {Colors.PRIMARY};
        padding: 4px 0;
        font-size: {Typography.FONT_SIZE_SM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
    }}
"""


def _make_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_LABEL_STYLE)
    return lbl


def _make_number_row(unit: str, default: str) -> tuple:
    """Return (container_widget, line_edit) for a numeric + unit label row."""
    row = QWidget()
    row.setStyleSheet("background: transparent; border: none;")
    hl = QHBoxLayout(row)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.setSpacing(0)

    edit = QLineEdit(default)
    edit.setStyleSheet(_INPUT_STYLE)
    edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    validator = QDoubleValidator()
    validator.setDecimals(2)
    validator.setBottom(0.0)
    edit.setValidator(validator)

    unit_lbl = QLabel(unit)
    unit_lbl.setStyleSheet(_UNIT_STYLE)
    unit_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    hl.addWidget(edit)
    hl.addWidget(unit_lbl)
    return row, edit


class ZoneCreationDialog(QDialog):
    """Styled dialog for creating a new zone by entering its dimensions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Zone")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setSizeGripEnabled(False)
        self._init_ui()

    # ── Build UI ──────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.WHITE}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(0)

        # Title
        title = QLabel("Add Zone")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_LG};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)
        layout.addSpacing(14)
        layout.addWidget(self._divider())
        layout.addSpacing(20)

        # Form
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setContentsMargins(0, 0, 0, 0)

        # Zone Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Main Hall")
        self.name_edit.setStyleSheet(_INPUT_STYLE)
        form.addRow(_make_label("Zone Name"), self.name_edit)

        # Environment: Indoor keeps ceiling height; Outdoor hides it
        self.environment_combo = QComboBox()
        self.environment_combo.addItems(["Indoor", "Outdoor"])
        self.environment_combo.setStyleSheet(_COMBO_STYLE)
        form.addRow(_make_label("Environment"), self.environment_combo)

        # Dimensions
        length_row, self.length_edit = _make_number_row("ft", "10.00")
        self._length_label = _make_label("Length")
        form.addRow(self._length_label, length_row)

        width_row, self.width_edit = _make_number_row("ft", "10.00")
        self._width_label = _make_label("Width")
        form.addRow(self._width_label, width_row)

        # Ceiling Height (Indoor only)
        ceiling_row, self.ceiling_edit = _make_number_row("ft", "9.00")
        self._ceiling_label = _make_label("Ceiling Height")
        self._ceiling_row = ceiling_row
        form.addRow(self._ceiling_label, ceiling_row)

        # Target SPL
        spl_row, self.spl_edit = _make_number_row("dB", "85.00")
        form.addRow(_make_label("Target SPL"), spl_row)

        layout.addLayout(form)
        layout.addSpacing(24)
        layout.addWidget(self._divider())
        layout.addSpacing(16)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(ButtonStyles.get_secondary_button_style())
        cancel_btn.setDefault(False)
        cancel_btn.setAutoDefault(False)
        cancel_btn.clicked.connect(self.reject)

        self.create_btn = QPushButton("Add Zone")
        self.create_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._validate_and_accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self.create_btn)
        layout.addLayout(btn_row)

        # Wire environment → ceiling visibility
        self.environment_combo.currentIndexChanged.connect(self._update_ceiling_visibility)
        self._update_ceiling_visibility(0)

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _divider() -> QWidget:
        d = QWidget()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
        return d

    def _update_ceiling_visibility(self, index: int):
        is_indoor = (index == 0)
        self._ceiling_label.setVisible(is_indoor)
        self._ceiling_row.setVisible(is_indoor)

    def _parse_float(self, edit: QLineEdit, default: float) -> float:
        try:
            return float(edit.text().strip())
        except (ValueError, AttributeError):
            return default

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            from ui.dialogs.alert_dialog import AlertDialog
            AlertDialog.show_warning(self, "Missing Name", "Please enter a zone name.")
            self.name_edit.setFocus()
            return

        length = self._parse_float(self.length_edit, 0.0)
        width  = self._parse_float(self.width_edit,  0.0)
        if length <= 0 or width <= 0:
            from ui.dialogs.alert_dialog import AlertDialog
            AlertDialog.show_warning(self, "Invalid Dimensions",
                                     "Length and Width must be greater than zero.")
            return

        self.accept()

    # ── Legacy aliases ─────────────────────────────────────────────────

    def update_ceiling_visibility(self, index: int):
        self._update_ceiling_visibility(index)

    def validate_and_accept(self):
        self._validate_and_accept()

    # ── Public API ────────────────────────────────────────────────────

    def get_zone_data(self) -> dict:
        """Return the entered zone data as a dictionary."""
        is_indoor = (self.environment_combo.currentIndex() == 0)
        length = self._parse_float(self.length_edit, 10.0)
        width  = self._parse_float(self.width_edit,  10.0)
        data = {
            'name':             self.name_edit.text().strip(),
            'room_name':        '',   # Room field removed; kept in dict for compatibility
            'environment_type': 'enclosed' if is_indoor else 'outdoor',
            'target_spl':       self._parse_float(self.spl_edit, 85.0),
            'length':           length,
            'width':            width,
            'area':             length * width,
        }
        if is_indoor:
            data['ceiling_height'] = self._parse_float(self.ceiling_edit, 9.0)
        return data

    def set_room_names(self, room_names):
        """No-op — Room field removed; kept so callers don't crash."""
        pass

    # ── Legacy spinbox-style accessors ────────────────────────────────

    class _EditProxy:
        """Makes a QLineEdit look like a QDoubleSpinBox to legacy callers."""
        def __init__(self, edit: "QLineEdit", default: float = 0.0):
            self._edit = edit
            self._default = default

        def value(self) -> float:
            try:
                return float(self._edit.text().strip())
            except (ValueError, AttributeError):
                return self._default

        def setValue(self, v):
            self._edit.setText(f"{float(v):.2f}")

    def __getattr__(self, name):
        _map = {
            'length_spin':  ('length_edit', 10.0),
            'width_spin':   ('width_edit',  10.0),
            'ceiling_spin': ('ceiling_edit', 9.0),
            'spl_spin':     ('spl_edit',    85.0),
        }
        if name in _map:
            attr, default = _map[name]
            return self._EditProxy(object.__getattribute__(self, attr), default)
        raise AttributeError(name)
