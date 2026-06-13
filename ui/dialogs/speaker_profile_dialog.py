import logging
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QDialogButtonBox, QWidget, QCheckBox, QScrollArea,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from core.speaker_profiles import SpeakerProfile
from ui.styles.base_styles import Colors, Typography
from ui.styles.component_styles import ButtonStyles

_ARROW_SVG = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "resources", "arrow_down.svg")
).replace("\\", "/")

# ── Shared style blocks ────────────────────────────────────────────────────

_LABEL_STYLE = f"""
    QLabel {{
        color: {Colors.TEXT_SECONDARY};
        font-size: {Typography.FONT_SIZE_SM};
        font-weight: {Typography.FONT_WEIGHT_MEDIUM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        background: transparent;
        border: none;
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

_CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: {Colors.TEXT_PRIMARY};
        font-size: {Typography.FONT_SIZE_SM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        spacing: 6px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 15px;
        height: 15px;
        border: 1px solid {Colors.BORDER_MEDIUM};
        border-radius: 3px;
        background: {Colors.WHITE};
    }}
    QCheckBox::indicator:checked {{
        background: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
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
        min-width: 20px;
    }}
"""

_REMOVE_BTN_STYLE = f"""
    QPushButton {{
        background: transparent;
        border: 1px solid {Colors.BORDER_MEDIUM};
        border-radius: 4px;
        color: {Colors.TEXT_MUTED};
        font-size: 14px;
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        min-width: 24px;
        max-width: 24px;
        min-height: 24px;
        max-height: 24px;
        padding: 0;
    }}
    QPushButton:hover {{
        background: #fdecea;
        border-color: #e57373;
        color: #c0392b;
    }}
"""

_ADD_TAP_BTN_STYLE = f"""
    QPushButton {{
        background: transparent;
        border: 1px dashed {Colors.PRIMARY};
        border-radius: 6px;
        color: {Colors.PRIMARY};
        font-size: {Typography.FONT_SIZE_SM};
        font-family: {Typography.FONT_FAMILY_PRIMARY};
        padding: 5px 12px;
        min-height: 28px;
    }}
    QPushButton:hover {{
        background: {Colors.PRIMARY_LIGHT};
    }}
"""

_TAPS_CONTAINER_STYLE = f"""
    QWidget#taps_container {{
        background: {Colors.GRAY_100};
        border: 1px solid {Colors.BORDER_LIGHT};
        border-radius: 6px;
    }}
"""


def _make_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_LABEL_STYLE)
    return lbl


def _make_input(default: str = "", placeholder: str = "") -> QLineEdit:
    edit = QLineEdit(default)
    edit.setPlaceholderText(placeholder)
    edit.setStyleSheet(_INPUT_STYLE)
    validator = QDoubleValidator()
    validator.setDecimals(2)
    validator.setBottom(0.0)
    edit.setValidator(validator)
    return edit


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
    return line


class SpeakerProfileDialog(QDialog):
    """Dialog for creating or editing a speaker profile."""

    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        self.profile = profile
        self.logger = logging.getLogger(__name__)
        self._tap_rows = []  # list of QLineEdit widgets (one per tap)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Speaker Profile")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setSizeGripEnabled(False)
        self.setStyleSheet(f"QDialog {{ background-color: {Colors.WHITE}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        # Title
        title_text = "Edit Speaker Profile" if self.profile else "New Speaker Profile"
        title = QLabel(title_text)
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
        root.addWidget(title)
        root.addSpacing(14)
        root.addWidget(_divider())
        root.addSpacing(20)

        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Name
        self._name_edit = QLineEdit(self.profile.name if self.profile else "")
        self._name_edit.setStyleSheet(_INPUT_STYLE)
        form.addRow(_make_label("Name"), self._name_edit)

        # Manufacturer
        self._mfr_edit = QLineEdit(self.profile.manufacturer if self.profile else "Generic")
        self._mfr_edit.setStyleSheet(_INPUT_STYLE)
        form.addRow(_make_label("Manufacturer"), self._mfr_edit)

        # Type
        self._type_combo = QComboBox()
        self._type_combo.setStyleSheet(_COMBO_STYLE)
        self._type_combo.addItems(["In-Ceiling", "Pendant"])
        if self.profile:
            self._type_combo.setCurrentText(self.profile.model_type)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow(_make_label("Type"), self._type_combo)

        # Diameter (In-Ceiling / Pendant only)
        diameter_val = str(self.profile.diameter) if self.profile else "6.0"
        self._diameter_edit = _make_input(diameter_val)
        self._diameter_row_label = _make_label("Diameter")
        self._diameter_unit = QLabel("in")
        self._diameter_unit.setStyleSheet(_UNIT_STYLE)
        diameter_row = QWidget()
        diameter_row.setStyleSheet("background: transparent; border: none;")
        drl = QHBoxLayout(diameter_row)
        drl.setContentsMargins(0, 0, 0, 0)
        drl.setSpacing(0)
        drl.addWidget(self._diameter_edit)
        drl.addWidget(self._diameter_unit)
        form.addRow(self._diameter_row_label, diameter_row)

        # Sensitivity
        sens_val = str(self.profile.sensitivity) if self.profile else "89.0"
        self._sensitivity_edit = _make_input(sens_val)
        sens_unit = QLabel("dB")
        sens_unit.setStyleSheet(_UNIT_STYLE)
        sens_row = QWidget()
        sens_row.setStyleSheet("background: transparent; border: none;")
        srl = QHBoxLayout(sens_row)
        srl.setContentsMargins(0, 0, 0, 0)
        srl.setSpacing(0)
        srl.addWidget(self._sensitivity_edit)
        srl.addWidget(sens_unit)
        form.addRow(_make_label("Sensitivity"), sens_row)

        # Impedance
        imp_val = str(self.profile.impedance) if self.profile else "8.0"
        self._impedance_edit = _make_input(imp_val)
        imp_unit = QLabel("Ω")
        imp_unit.setStyleSheet(_UNIT_STYLE)
        imp_row = QWidget()
        imp_row.setStyleSheet("background: transparent; border: none;")
        irl = QHBoxLayout(imp_row)
        irl.setContentsMargins(0, 0, 0, 0)
        irl.setSpacing(0)
        irl.addWidget(self._impedance_edit)
        irl.addWidget(imp_unit)
        form.addRow(_make_label("Impedance"), imp_row)

        # Frequency range
        low_val = str(self.profile.frequency_range[0]) if self.profile else "80"
        high_val = str(self.profile.frequency_range[1]) if self.profile else "20000"
        self._freq_low_edit = QLineEdit(low_val)
        self._freq_low_edit.setStyleSheet(_INPUT_STYLE)
        self._freq_high_edit = QLineEdit(high_val)
        self._freq_high_edit.setStyleSheet(_INPUT_STYLE)
        freq_sep = QLabel("–")
        freq_sep.setStyleSheet(_UNIT_STYLE)
        freq_unit = QLabel("Hz")
        freq_unit.setStyleSheet(_UNIT_STYLE)
        freq_row = QWidget()
        freq_row.setStyleSheet("background: transparent; border: none;")
        frl = QHBoxLayout(freq_row)
        frl.setContentsMargins(0, 0, 0, 0)
        frl.setSpacing(6)
        frl.addWidget(self._freq_low_edit)
        frl.addWidget(freq_sep)
        frl.addWidget(self._freq_high_edit)
        frl.addWidget(freq_unit)
        form.addRow(_make_label("Freq. Range"), freq_row)

        # Dispersion H
        disp_h_val = str(self.profile.dispersion_angle_h) if self.profile else "90.0"
        self._disp_h_edit = _make_input(disp_h_val)
        disp_h_unit = QLabel("°")
        disp_h_unit.setStyleSheet(_UNIT_STYLE)
        disp_h_row = QWidget()
        disp_h_row.setStyleSheet("background: transparent; border: none;")
        dhl = QHBoxLayout(disp_h_row)
        dhl.setContentsMargins(0, 0, 0, 0)
        dhl.setSpacing(0)
        dhl.addWidget(self._disp_h_edit)
        dhl.addWidget(disp_h_unit)
        form.addRow(_make_label("H Dispersion"), disp_h_row)

        # Dispersion V
        disp_v_val = str(self.profile.dispersion_angle_v) if self.profile else "90.0"
        self._disp_v_edit = _make_input(disp_v_val)
        disp_v_unit = QLabel("°")
        disp_v_unit.setStyleSheet(_UNIT_STYLE)
        disp_v_row = QWidget()
        disp_v_row.setStyleSheet("background: transparent; border: none;")
        dvl = QHBoxLayout(disp_v_row)
        dvl.setContentsMargins(0, 0, 0, 0)
        dvl.setSpacing(0)
        dvl.addWidget(self._disp_v_edit)
        dvl.addWidget(disp_v_unit)
        form.addRow(_make_label("V Dispersion"), disp_v_row)

        root.addLayout(form)
        root.addSpacing(18)
        root.addWidget(_divider())
        root.addSpacing(14)

        # ── Power section ──────────────────────────────────────────────────
        power_header = QLabel("Power")
        power_header.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        root.addWidget(power_header)
        root.addSpacing(8)

        # Single power row (shown when multi-tap is off)
        self._single_power_row = QWidget()
        self._single_power_row.setStyleSheet("background: transparent; border: none;")
        spl = QHBoxLayout(self._single_power_row)
        spl.setContentsMargins(0, 0, 0, 0)
        spl.setSpacing(0)
        single_lbl = _make_label("Power")
        single_lbl.setFixedWidth(110)
        # Determine initial value
        if self.profile and self.profile.power_taps:
            init_power = str(self.profile.power_taps[0])
        else:
            init_power = "30.0"
        self._single_power_edit = _make_input(init_power)
        single_unit = QLabel("W")
        single_unit.setStyleSheet(_UNIT_STYLE)
        spl.addWidget(single_lbl)
        spl.addWidget(self._single_power_edit)
        spl.addWidget(single_unit)
        root.addWidget(self._single_power_row)
        root.addSpacing(8)

        # 70V / multi-tap checkbox
        self._multi_tap_check = QCheckBox("70V Distribution / Multiple Taps")
        self._multi_tap_check.setStyleSheet(_CHECKBOX_STYLE)
        root.addWidget(self._multi_tap_check)

        # Multi-tap container (hidden until checkbox checked)
        self._taps_outer = QWidget()
        self._taps_outer.setVisible(False)
        self._taps_outer.setStyleSheet("background: transparent; border: none;")
        taps_outer_layout = QVBoxLayout(self._taps_outer)
        taps_outer_layout.setContentsMargins(0, 8, 0, 0)
        taps_outer_layout.setSpacing(6)

        # Scrollable container for tap rows
        self._taps_container = QWidget()
        self._taps_container.setObjectName("taps_container")
        self._taps_container.setStyleSheet(_TAPS_CONTAINER_STYLE)
        self._taps_layout = QVBoxLayout(self._taps_container)
        self._taps_layout.setContentsMargins(10, 10, 10, 10)
        self._taps_layout.setSpacing(6)

        taps_outer_layout.addWidget(self._taps_container)

        # "+ Add Tap" button
        self._add_tap_btn = QPushButton("+ Add Tap")
        self._add_tap_btn.setStyleSheet(_ADD_TAP_BTN_STYLE)
        self._add_tap_btn.clicked.connect(self._add_tap_row)
        taps_outer_layout.addWidget(self._add_tap_btn, alignment=Qt.AlignLeft)

        root.addWidget(self._taps_outer)
        root.addSpacing(18)

        # ── OK / Cancel ────────────────────────────────────────────────────
        root.addWidget(_divider())
        root.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(ButtonStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Save Profile")
        ok_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

        # Connect checkbox toggle
        self._multi_tap_check.toggled.connect(self._on_multi_tap_toggled)

        # Populate initial state
        self._populate_power_from_profile()
        self._on_type_changed(self._type_combo.currentText())

    def _populate_power_from_profile(self):
        """Set up power fields based on the loaded profile."""
        if not self.profile:
            return
        taps = self.profile.power_taps or []
        if len(taps) > 1:
            # Enable multi-tap mode and populate rows
            self._multi_tap_check.setChecked(True)  # triggers _on_multi_tap_toggled
            # Clear the default row that was added by the toggle, then add from profile
            self._clear_tap_rows()
            for val in taps:
                self._add_tap_row(value=val)
        elif taps:
            self._single_power_edit.setText(str(taps[0]))

    def _on_multi_tap_toggled(self, checked: bool):
        self._single_power_row.setVisible(not checked)
        self._taps_outer.setVisible(checked)
        if checked and not self._tap_rows:
            # Seed with the current single-power value
            try:
                seed = float(self._single_power_edit.text())
            except ValueError:
                seed = 30.0
            self._add_tap_row(value=seed)
        self.adjustSize()

    def _clear_tap_rows(self):
        """Remove all tap rows without adding a seed."""
        for edit in list(self._tap_rows):
            self._remove_tap_row(edit, adjust=False)

    def _add_tap_row(self, value: float = None):
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)

        edit = QLineEdit(str(value) if value is not None else "")
        edit.setPlaceholderText("e.g. 7.5")
        edit.setStyleSheet(_INPUT_STYLE)
        validator = QDoubleValidator(0.1, 9999.0, 2)
        edit.setValidator(validator)

        unit = QLabel("W")
        unit.setStyleSheet(_UNIT_STYLE)
        unit.setFixedWidth(20)

        remove_btn = QPushButton("×")
        remove_btn.setStyleSheet(_REMOVE_BTN_STYLE)
        remove_btn.setToolTip("Remove this tap")
        remove_btn.clicked.connect(lambda _, e=edit: self._remove_tap_row(e))

        rl.addWidget(edit)
        rl.addWidget(unit)
        rl.addWidget(remove_btn)

        self._tap_rows.append(edit)
        self._taps_layout.addWidget(row)
        edit.setFocus()
        self.adjustSize()

    def _remove_tap_row(self, edit: QLineEdit, adjust: bool = True):
        if edit not in self._tap_rows:
            return
        self._tap_rows.remove(edit)
        # The row widget is edit's parent
        row_widget = edit.parent()
        self._taps_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        if adjust:
            self.adjustSize()

    def _on_type_changed(self, speaker_type: str):
        # Both In-Ceiling and Pendant use circular diameter — always visible
        self._diameter_edit.setVisible(True)
        self._diameter_unit.setVisible(True)
        self._diameter_row_label.setVisible(True)

    def validate(self):
        if not self._name_edit.text().strip():
            return False, "Speaker name is required"
        if not self._mfr_edit.text().strip():
            return False, "Manufacturer is required"
        try:
            sens = float(self._sensitivity_edit.text())
            if not (70 <= sens <= 110):
                return False, "Sensitivity must be between 70 and 110 dB"
        except ValueError:
            return False, "Sensitivity must be a number"
        try:
            freq_low = float(self._freq_low_edit.text())
            freq_high = float(self._freq_high_edit.text())
            if freq_low >= freq_high:
                return False, "Low frequency must be less than high frequency"
        except ValueError:
            return False, "Frequency range values must be numbers"
        # Validate power
        if self._multi_tap_check.isChecked():
            if not self._tap_rows:
                return False, "Add at least one power tap"
            for edit in self._tap_rows:
                try:
                    val = float(edit.text())
                    if val <= 0:
                        return False, "Power tap values must be greater than 0"
                except ValueError:
                    return False, "All power tap values must be numbers"
        else:
            try:
                val = float(self._single_power_edit.text())
                if val <= 0:
                    return False, "Power must be greater than 0"
            except ValueError:
                return False, "Power must be a number"
        return True, ""

    def accept(self):
        is_valid, error_message = self.validate()
        if not is_valid:
            from ui.dialogs.alert_dialog import AlertDialog
            AlertDialog.show_warning(self, "Validation Error", error_message)
            return
        super().accept()

    def get_profile(self):
        """Build and return a SpeakerProfile from the dialog's current values."""
        # Power taps
        if self._multi_tap_check.isChecked():
            power_taps = []
            for edit in self._tap_rows:
                try:
                    power_taps.append(float(edit.text()))
                except ValueError:
                    pass
            power_taps = sorted(power_taps) if power_taps else [30.0]
        else:
            try:
                power_taps = [float(self._single_power_edit.text())]
            except ValueError:
                power_taps = [30.0]

        model_type = self._type_combo.currentText()

        try:
            diameter = float(self._diameter_edit.text())
        except ValueError:
            diameter = 6.0

        try:
            sensitivity = float(self._sensitivity_edit.text())
        except ValueError:
            sensitivity = 89.0

        try:
            impedance = float(self._impedance_edit.text())
        except ValueError:
            impedance = 8.0

        try:
            freq_low = int(float(self._freq_low_edit.text()))
            freq_high = int(float(self._freq_high_edit.text()))
        except ValueError:
            freq_low, freq_high = 80, 20000

        try:
            disp_h = float(self._disp_h_edit.text())
        except ValueError:
            disp_h = 90.0

        try:
            disp_v = float(self._disp_v_edit.text())
        except ValueError:
            disp_v = 90.0

        return SpeakerProfile(
            name=self._name_edit.text().strip(),
            manufacturer=self._mfr_edit.text().strip(),
            model_type=model_type,
            sensitivity=sensitivity,
            power_taps=power_taps,
            impedance=impedance,
            frequency_range=(freq_low, freq_high),
            dispersion_angle_h=disp_h,
            dispersion_angle_v=disp_v,
            diameter=diameter,
        )

    # Keep old attribute names alive so any external code accessing them doesn't crash
    @property
    def name_edit(self):
        return self._name_edit

    @property
    def manufacturer_edit(self):
        return self._mfr_edit

    @property
    def type_combo(self):
        return self._type_combo
