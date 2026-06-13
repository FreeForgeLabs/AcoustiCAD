from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel,
                             QLineEdit, QDoubleSpinBox, QComboBox, QPushButton,
                             QCheckBox, QTextEdit, QFrame)
from PySide6.QtCore import Qt, Signal

from ui.styles.base_styles import Colors, Typography


class ObstructionPropertiesPanel(QWidget):
    """Panel for editing obstruction properties"""

    # Signal when property is changed
    property_changed = Signal(str, str, object)  # obstruction_id, property_name, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_obstruction_id = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Properties section title (flat, no QGroupBox)
        self.properties_title = QLabel("Obstruction Properties")
        self.properties_title.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background-color: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(self.properties_title)

        # Properties form
        self.properties_form = QWidget()
        form_layout = QFormLayout(self.properties_form)
        form_layout.setContentsMargins(0, 0, 0, 0)

        # Obstruction type - Read-only label
        self.type_label = QLabel("Column")  # Default value
        self.type_label.setStyleSheet(f"QLabel {{ border: 1px solid {Colors.BORDER_DARK}; padding: 5px; background-color: {Colors.GRAY_200}; }}")
        form_layout.addRow("Type:", self.type_label)

        # Diameter in inches (user-facing)
        self.diameter_spinner = QDoubleSpinBox()
        self.diameter_spinner.setRange(2.0, 72.0)  # Range in inches (min 2", max 72")
        self.diameter_spinner.setValue(12.0)  # Default (6" radius = 12" diameter)
        self.diameter_spinner.setSingleStep(1.0)  # 1 inch increments
        self.diameter_spinner.setSuffix(" in")  # Indicate inches
        self.diameter_spinner.valueChanged.connect(self.on_diameter_changed)
        form_layout.addRow("Diameter:", self.diameter_spinner)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.textChanged.connect(self.on_notes_changed)
        form_layout.addRow("Notes:", self.notes_edit)

        main_layout.addWidget(self.properties_form)

        # Delete button
        self.delete_button = QPushButton("Delete Obstruction")
        self.delete_button.clicked.connect(self.on_delete_obstruction)
        main_layout.addWidget(self.delete_button)

        # Add stretch to bottom
        main_layout.addStretch(1)

        # Initially hide until obstruction is selected
        self.properties_title.setVisible(False)
        self.properties_form.setVisible(False)
        self.delete_button.setVisible(False)

        # No selection message
        self.no_selection = QLabel("Select an obstruction to edit properties")
        self.no_selection.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.no_selection)

    def show_obstruction_properties(self, obstruction):
        """Display properties for the selected obstruction"""
        if not obstruction:
            self.clear()
            return

        # Store obstruction ID
        self.current_obstruction_id = obstruction['id']

        # Show property panels
        self.properties_title.setVisible(True)
        self.properties_form.setVisible(True)
        self.delete_button.setVisible(True)
        self.no_selection.setVisible(False)

        # Update values (block signals to prevent unintended updates)
        self.diameter_spinner.blockSignals(True)
        self.notes_edit.blockSignals(True)

        # Set values from obstruction data
        # Set the type label (read-only)
        obstruction_type = obstruction.get('type', 'Column')
        self.type_label.setText(obstruction_type)

        # Get radius value in inches and convert to diameter for display
        radius_inches = obstruction.get('radius', 12.0)  # Default to 12 inches if not specified
        diameter_inches = radius_inches * 2.0  # Convert radius to diameter
        self.diameter_spinner.setValue(diameter_inches)

        self.notes_edit.setText(obstruction.get('notes', ""))

        # Unblock signals
        self.diameter_spinner.blockSignals(False)
        self.notes_edit.blockSignals(False)

    def clear(self):
        """Clear properties when no obstruction is selected"""
        self.current_obstruction_id = None
        self.properties_title.setVisible(False)
        self.properties_form.setVisible(False)
        self.delete_button.setVisible(False)
        self.no_selection.setVisible(True)

    # Event handlers
    def on_diameter_changed(self, value):
        """Handle diameter change"""
        if not self.current_obstruction_id:
            return

        # Convert diameter to radius for internal storage
        radius = value / 2.0

        # Emit property changed signal with the radius in inches
        self.property_changed.emit(self.current_obstruction_id, 'radius', radius)

    def on_notes_changed(self):
        """Handle notes change"""
        if not self.current_obstruction_id:
            return

        self.property_changed.emit(self.current_obstruction_id, 'notes', self.notes_edit.toPlainText())

    def on_delete_obstruction(self):
        """Handle delete obstruction button"""
        if not self.current_obstruction_id:
            return

        # Emit delete signal using the property_changed mechanism
        self.property_changed.emit(self.current_obstruction_id, 'delete', True)

        # Clear selection
        self.clear()
