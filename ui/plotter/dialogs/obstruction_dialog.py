"""ObstructionDialog — pick obstruction type and size before placing."""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QDoubleSpinBox, QPushButton, QFrame)
from PySide6.QtCore import Qt
from ui.styles.base_styles import Colors, Typography, BorderRadius, Spacing

# Default radii in inches per type (mirrors obstruction_data_manager.OBSTRUCTION_TYPES)
_TYPE_DEFAULTS = {
    "Column":         {"radius_in": 12.0, "desc": "Structural column or pillar"},
    "Light":          {"radius_in":  6.0, "desc": "Ceiling light fixture"},
    "HVAC":           {"radius_in": 16.0, "desc": "HVAC diffuser or vent"},
    "Beam":           {"radius_in": 12.0, "desc": "Overhead structural beam"},
    "Fire Sprinkler": {"radius_in":  3.0, "desc": "Fire sprinkler head"},
    "Other":          {"radius_in": 24.0, "desc": "Custom ceiling obstruction"},
}

class ObstructionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Place Obstruction")
        self.setMinimumWidth(360)
        self.setModal(True)
        self._result = None
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {Colors.WHITE}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        def section_lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_SECONDARY};
                    font-size: {Typography.FONT_SIZE_XS};
                    font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                    font-family: {Typography.FONT_FAMILY_PRIMARY};
                    background: transparent; border: none;
                    letter-spacing: 0.5px;
                }}
            """)
            return l

        input_style = f"""
            QComboBox, QDoubleSpinBox {{
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                padding: 6px 10px;
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                background: {Colors.WHITE};
            }}
            QComboBox:focus, QDoubleSpinBox:focus {{ border-color: {Colors.PRIMARY}; }}
            QComboBox::drop-down {{ border: none; padding-right: 8px; }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                selection-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER_MEDIUM};
            }}
        """

        # TYPE
        layout.addWidget(section_lbl("OBSTRUCTION TYPE"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(list(_TYPE_DEFAULTS.keys()))
        self._type_combo.setStyleSheet(input_style)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(self._type_combo)

        self._desc_lbl = QLabel("")
        self._desc_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Typography.FONT_SIZE_XS}; font-family: {Typography.FONT_FAMILY_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(self._desc_lbl)

        # SIZE
        layout.addWidget(section_lbl("SIZE (radius in feet)"))
        size_row = QHBoxLayout()
        self._radius_spin = QDoubleSpinBox()
        self._radius_spin.setRange(0.1, 20.0)
        self._radius_spin.setSingleStep(0.5)
        self._radius_spin.setDecimals(1)
        self._radius_spin.setSuffix(" ft")
        self._radius_spin.setStyleSheet(input_style)
        size_row.addWidget(self._radius_spin)
        size_row.addStretch()
        layout.addLayout(size_row)

        # Instruction note
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Colors.BORDER_LIGHT}; border: none;")
        layout.addWidget(sep)

        note = QLabel("Click on the floor plan to stamp-place. Press Escape or click Place again to stop.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Typography.FONT_SIZE_XS}; font-family: {Typography.FONT_FAMILY_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(note)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine); sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {Colors.BORDER_LIGHT}; border: none;")
        layout.addWidget(sep2)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD}; padding: 7px 16px;
                font-size: {Typography.FONT_SIZE_SM}; font-family: {Typography.FONT_FAMILY_PRIMARY};
                color: {Colors.TEXT_SECONDARY};
            }}
            QPushButton:hover {{ background: {Colors.GRAY_50}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        place_btn = QPushButton("Start Placing")
        place_btn.setDefault(True)
        place_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.PRIMARY}; color: white; border: none;
                border-radius: {BorderRadius.MD}; padding: 7px 20px;
                font-size: {Typography.FONT_SIZE_SM}; font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QPushButton:hover {{ background: {Colors.PRIMARY_HOVER}; }}
        """)
        place_btn.clicked.connect(self._on_place)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(place_btn)
        layout.addLayout(btn_row)

        # Initialise with first type
        self._on_type_changed(self._type_combo.currentText())

    def _on_type_changed(self, text):
        info = _TYPE_DEFAULTS.get(text, {})
        self._desc_lbl.setText(info.get("desc", ""))
        radius_in = info.get("radius_in", 12.0)
        radius_ft = round(radius_in / 12.0, 1)
        self._radius_spin.setValue(radius_ft)

    def _on_place(self):
        self._result = {
            "type": self._type_combo.currentText(),
            "radius_inches": self._radius_spin.value() * 12.0,  # convert ft -> inches
        }
        self.accept()

    def get_result(self):
        """Returns dict with 'type' and 'radius_inches', or None if cancelled."""
        return self._result
