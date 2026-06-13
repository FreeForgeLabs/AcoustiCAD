from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel,
                             QDoubleSpinBox, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal

from ui.styles.base_styles import Colors, Typography


class SpeakerPropertiesPanel(QWidget):
    """Panel for editing speaker properties"""

    # Signal when property is changed
    property_changed = Signal(str, str, object)  # speaker_id, property_name, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_speaker_id = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Properties section title (flat, no QGroupBox)
        self.properties_title = QLabel("Speaker Properties")
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

        # Power/Wattage
        self.power_spinner = QDoubleSpinBox()
        self.power_spinner.setRange(1, 100)
        self.power_spinner.setValue(15)
        self.power_spinner.setSingleStep(5)
        self.power_spinner.setSuffix(" W")
        self.power_spinner.valueChanged.connect(self.on_power_changed)
        form_layout.addRow("Power:", self.power_spinner)

        # Mounting height (for pendant speakers)
        self.mounting_spinner = QDoubleSpinBox()
        self.mounting_spinner.setRange(4, 20)
        self.mounting_spinner.setValue(8)
        self.mounting_spinner.setSingleStep(0.5)
        self.mounting_spinner.setSuffix(" ft")
        self.mounting_spinner.valueChanged.connect(self.on_mounting_changed)
        self.mounting_label = QLabel("Mounting Height:")
        form_layout.addRow(self.mounting_label, self.mounting_spinner)

        main_layout.addWidget(self.properties_form)

        # Separator between editable and read-only sections
        self.coverage_sep = QFrame()
        self.coverage_sep.setFrameShape(QFrame.HLine)
        self.coverage_sep.setFrameShadow(QFrame.Plain)
        self.coverage_sep.setFixedHeight(1)
        self.coverage_sep.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
        main_layout.addWidget(self.coverage_sep)

        # Coverage analysis section title (flat)
        self.coverage_title = QLabel("Coverage Analysis")
        self.coverage_title.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background-color: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(self.coverage_title)

        # Coverage form
        self.coverage_form = QWidget()
        coverage_layout = QFormLayout(self.coverage_form)
        coverage_layout.setContentsMargins(0, 0, 0, 0)

        # Coverage radius
        self.coverage_radius = QLabel("0 ft")
        coverage_layout.addRow("Coverage Radius:", self.coverage_radius)

        # Coverage area
        self.coverage_area = QLabel("0 ft²")
        coverage_layout.addRow("Coverage Area:", self.coverage_area)

        # Estimated SPL
        self.estimated_spl = QLabel("0 dB")
        coverage_layout.addRow("Estimated SPL:", self.estimated_spl)

        main_layout.addWidget(self.coverage_form)

        # Delete button
        self.delete_button = QPushButton("Delete Speaker")
        self.delete_button.clicked.connect(self.on_delete_speaker)
        main_layout.addWidget(self.delete_button)

        # Add stretch to bottom
        main_layout.addStretch(1)

        # Initially hide until speaker is selected
        self.properties_title.setVisible(False)
        self.properties_form.setVisible(False)
        self.coverage_sep.setVisible(False)
        self.coverage_title.setVisible(False)
        self.coverage_form.setVisible(False)
        self.delete_button.setVisible(False)

        # No selection message
        self.no_selection = QLabel("Select a speaker to edit properties")
        self.no_selection.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.no_selection)

    def show_speaker_properties(self, speaker):
        """Display properties for the selected speaker"""
        if not speaker:
            self.clear()
            return

        # Store speaker ID
        self.current_speaker_id = speaker['id']

        # Show property panels
        self.properties_title.setVisible(True)
        self.properties_form.setVisible(True)
        self.coverage_sep.setVisible(True)
        self.coverage_title.setVisible(True)
        self.coverage_form.setVisible(True)
        self.delete_button.setVisible(True)
        self.no_selection.setVisible(False)

        # Update values (block signals to prevent unintended updates)
        self.power_spinner.blockSignals(True)
        self.mounting_spinner.blockSignals(True)

        # Set values from speaker data
        self.power_spinner.setValue(speaker.get('power', 15))

        # Show/hide mounting height based on type
        speaker_type = speaker.get('type', 'In-Ceiling')
        if speaker_type == "Pendant":
            self.mounting_label.setVisible(True)
            self.mounting_spinner.setVisible(True)
            self.mounting_spinner.setValue(speaker.get('mounting_height', 9))
        else:
            self.mounting_label.setVisible(False)
            self.mounting_spinner.setVisible(False)

        # Calculate coverage details
        self._update_coverage_details(speaker)

        # Unblock signals
        self.power_spinner.blockSignals(False)
        self.mounting_spinner.blockSignals(False)

    def clear(self):
        """Clear properties when no speaker is selected"""
        self.current_speaker_id = None
        self.properties_title.setText("Speaker Properties")  # reset title
        self.delete_button.setText("Delete Speaker")          # reset button
        self.properties_title.setVisible(False)
        self.properties_form.setVisible(False)
        self.coverage_sep.setVisible(False)
        self.coverage_title.setVisible(False)
        self.coverage_form.setVisible(False)
        self.delete_button.setVisible(False)
        self.no_selection.setVisible(True)

    def show_multi_selection(self, count):
        """Show a summary view when multiple speakers are selected."""
        self.current_speaker_id = None
        self.properties_title.setVisible(True)
        self.properties_form.setVisible(False)
        self.coverage_sep.setVisible(False)
        self.coverage_title.setVisible(False)
        self.coverage_form.setVisible(False)
        self.delete_button.setVisible(True)
        self.no_selection.setVisible(False)
        self.properties_title.setText(f"{count} speakers selected")
        self.delete_button.setText("Delete Selected")

    def _update_coverage_details(self, speaker):
        """Calculate and display coverage details"""
        # Get properties
        speaker_type = speaker.get('type', 'In-Ceiling')
        dispersion = speaker.get('dispersion_angle', 90)
        power = speaker.get('power', 15)
        sensitivity = speaker.get('sensitivity', 89)

        # Get zone and listener info
        parent = self.parent()
        ceiling_height = 10  # default
        while parent:
            # Try to find speaker view with zone data
            if hasattr(parent, 'speaker_view') and hasattr(parent.speaker_view, 'get_current_zone'):
                zone = parent.speaker_view.get_current_zone()
                if zone:
                    ceiling_height = zone.get('ceiling_height', 10)
                break

            # Move up parent hierarchy
            if hasattr(parent, 'parent'):
                parent = parent.parent()
            else:
                break

        # Calculate coverage radius
        listener_height = 4  # feet (average ear height)

        if speaker_type == "Pendant":
            speaker_height = speaker.get('mounting_height', 8)
        else:  # In-Ceiling (default)
            speaker_height = ceiling_height

        # Calculate coverage
        coverage_height = speaker_height - listener_height
        if coverage_height <= 0:
            radius_ft = 0
        else:
            import math
            angle_rad = math.radians(dispersion / 2)
            radius_ft = coverage_height * math.tan(angle_rad)

        # Calculate coverage area
        area_ft2 = math.pi * radius_ft * radius_ft

        # Calculate SPL at center of coverage area
        center_spl = sensitivity + 10 * math.log10(power) - 20 * math.log10(1)  # At 1m

        # Update labels
        self.coverage_radius.setText(f"{radius_ft:.1f} ft")
        self.coverage_area.setText(f"{area_ft2:.1f} ft²")
        self.estimated_spl.setText(f"{center_spl:.1f} dB")

    # Event handlers

    def on_power_changed(self, value):
        """Handle power/wattage change"""
        if not self.current_speaker_id:
            return

        self.property_changed.emit(self.current_speaker_id, 'power', value)

    def on_mounting_changed(self, value):
        """Handle mounting height change"""
        if not self.current_speaker_id:
            return

        self.property_changed.emit(self.current_speaker_id, 'mounting_height', value)

    def on_delete_speaker(self):
        """Handle delete speaker button"""
        if not self.current_speaker_id:
            return

        # Emit delete signal using the property_changed mechanism
        self.property_changed.emit(self.current_speaker_id, 'delete', True)

        # Clear selection
        self.clear()
