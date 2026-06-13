from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QFormLayout, QDoubleSpinBox)
from PySide6.QtCore import Signal

# Import shared styling system instead of embedding styles
from ui.styles.component_styles import ButtonStyles, InputStyles
from ui.styles.base_styles import Colors, Typography, Spacing, BorderRadius


class ObstructionControlPanel(QWidget):
    """Panel for obstruction placement and speaker spacing controls using shared styling"""

    # Signals
    place_obstruction_requested = Signal(str)  # obstruction_type
    min_spacing_toggled = Signal(bool)  # enabled
    min_spacing_value_changed = Signal(float)  # value in inches

    def __init__(self, parent=None):
        """Initialize the obstruction control panel

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
        self._apply_shared_styling()

    def _init_ui(self):
        """Initialize the UI components with clean layout matching zones tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Ceiling Obstructions section
        self._create_obstruction_section(layout)

        # Speaker Spacing section
        self._create_spacing_section(layout)

        layout.addStretch(1)

    def _create_obstruction_section(self, main_layout):
        """Create clean obstruction section matching zones tab styling"""
        # Section header with blue underline (matching zones tab)
        header_label = QLabel("Ceiling Obstructions")
        header_label.setObjectName("section-header")  # Use object name for styling
        main_layout.addWidget(header_label)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)

        # Type selection row
        type_layout = QHBoxLayout()
        type_label = QLabel("TYPE")
        type_label.setObjectName("field-label")  # Use object name for styling
        type_layout.addWidget(type_label)

        self.obstruction_type_combo = QComboBox()
        self.obstruction_type_combo.addItems(["Column", "Light", "HVAC", "Beam", "Fire Sprinkler", "Other"])
        type_layout.addWidget(self.obstruction_type_combo)
        content_layout.addLayout(type_layout)

        # Place button
        self.place_obstruction_btn = QPushButton("Place Obstruction")
        self.place_obstruction_btn.setObjectName("primary-button")  # Use object name for styling
        content_layout.addWidget(self.place_obstruction_btn)

        # Description text
        info_label = QLabel(
            "Place obstructions to mark areas where speakers cannot be installed, such as columns, lights, or HVAC diffusers.")
        info_label.setWordWrap(True)
        info_label.setObjectName("description-text")  # Use object name for styling
        content_layout.addWidget(info_label)

        main_layout.addLayout(content_layout)

    def _create_spacing_section(self, main_layout):
        """Create clean speaker spacing section matching zones tab styling"""
        # Section header with blue underline (matching zones tab)
        header_label = QLabel("Speaker Spacing")
        header_label.setObjectName("section-header")  # Use object name for styling
        main_layout.addWidget(header_label)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)

        # Minimum distance row
        distance_layout = QHBoxLayout()
        distance_label = QLabel("MINIMUM DISTANCE")
        distance_label.setObjectName("field-label")  # Use object name for styling
        distance_layout.addWidget(distance_label)

        self.min_spacing_spinner = QDoubleSpinBox()
        self.min_spacing_spinner.setRange(12, 120)
        self.min_spacing_spinner.setValue(36)  # Default 3 feet (36 inches)
        self.min_spacing_spinner.setSingleStep(6)
        self.min_spacing_spinner.setSuffix(" in")
        self.min_spacing_spinner.setEnabled(False)  # Initially disabled
        distance_layout.addWidget(self.min_spacing_spinner)
        content_layout.addLayout(distance_layout)

        # Description for spacing
        spacing_info_label = QLabel("Enable minimum spacing to prevent speakers from being placed too close together.")
        spacing_info_label.setWordWrap(True)
        spacing_info_label.setObjectName("description-text")  # Use object name for styling
        content_layout.addWidget(spacing_info_label)

        main_layout.addLayout(content_layout)

    def _apply_shared_styling(self):
        """Apply shared styling system from ui/styles/"""
        # Use shared styling instead of custom embedded styles
        style = f"""
            ObstructionControlPanel {{
                background-color: transparent;
            }}

            /* Section headers with blue underline - matching zones tab */
            QLabel[objectName="section-header"] {{
                color: {Colors.TEXT_PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_SM};
                padding-bottom: 8px;
                border-bottom: 2px solid {Colors.PRIMARY};
                margin-bottom: 12px;
                margin-top: 8px;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}

            /* Field labels - uppercase with letter spacing */
            QLabel[objectName="field-label"] {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_XS};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                min-width: 100px;
            }}

            /* Description text */
            QLabel[objectName="description-text"] {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_XS};
                line-height: 1.4;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
        """

        self.setStyleSheet(style)

        # Apply shared component styles to individual widgets
        self._apply_shared_component_styles()

    def _apply_shared_component_styles(self):
        """Apply shared component styles to individual widgets"""
        # Apply shared input styling to combo box and spinner
        input_style = f"""
            QComboBox, QDoubleSpinBox {{
                padding: 8px 12px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QComboBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {Colors.PRIMARY};
                background-color: {Colors.GRAY_50};
            }}
            QComboBox:disabled, QDoubleSpinBox:disabled {{
                background-color: {Colors.GRAY_200};
                color: {Colors.TEXT_MUTED};
                border-color: {Colors.BORDER_LIGHT};
            }}
            QComboBox {{
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {Colors.TEXT_SECONDARY};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                selection-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER_MEDIUM};
            }}
        """

        self.obstruction_type_combo.setStyleSheet(input_style)
        self.min_spacing_spinner.setStyleSheet(input_style)

        # Apply shared button styling
        button_style = f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.MD};
                padding: 10px 16px;
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_ACTIVE};
            }}
            QPushButton:disabled {{
                background-color: {Colors.GRAY_400};
                color: {Colors.TEXT_MUTED};
            }}
        """

        self.place_obstruction_btn.setStyleSheet(button_style)

    def _connect_signals(self):
        """Connect internal widget signals"""
        self.place_obstruction_btn.clicked.connect(self._on_place_obstruction_clicked)
        self.min_spacing_spinner.valueChanged.connect(self._on_min_spacing_value_changed)

    def _on_place_obstruction_clicked(self):
        """Handle place obstruction button click"""
        obstruction_type = self.obstruction_type_combo.currentText()
        self.place_obstruction_requested.emit(obstruction_type)

    def _on_min_spacing_value_changed(self, value):
        """Handle minimum spacing value change"""
        self.min_spacing_value_changed.emit(value)

    def set_min_spacing_enabled(self, enabled):
        """Enable or disable minimum spacing controls

        Args:
            enabled (bool): Whether to enable spacing controls
        """
        self.min_spacing_spinner.setEnabled(enabled)
        if enabled:
            # Emit current value when enabling
            self.min_spacing_value_changed.emit(self.min_spacing_spinner.value())

    def get_obstruction_type_combo(self):
        """Get the obstruction type combo box for external control"""
        return self.obstruction_type_combo

    def get_place_obstruction_button(self):
        """Get the place obstruction button for external control"""
        return self.place_obstruction_btn

    def get_min_spacing_spinner(self):
        """Get the minimum spacing spinner for external control"""
        return self.min_spacing_spinner

    def get_current_obstruction_type(self):
        """Get the currently selected obstruction type"""
        return self.obstruction_type_combo.currentText()

    def get_min_spacing_value(self):
        """Get the current minimum spacing value"""
        return self.min_spacing_spinner.value()

    def set_enabled(self, enabled):
        """Enable or disable the entire panel"""
        self.setEnabled(enabled)