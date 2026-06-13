import math
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QGridLayout, QHBoxLayout)
from PySide6.QtCore import Qt

from ui.styles.base_styles import Colors, Typography


class SpeakerRecommendation(QWidget):
    """Widget for calculating and displaying speaker recommendations — compact grid layout"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.current_zone = None
        self.auto_mode = True
        self.init_ui()

    # ── Shared label styles ───────────────────────────────────────────
    _FIELD_LABEL_STYLE = (
        f"QLabel {{ color: {Colors.TEXT_SECONDARY}; font-weight: 600; "
        f"font-size: 10px; background: transparent; border: none; }}"
    )
    _VALUE_LABEL_STYLE = (
        f"QLabel {{ color: {Colors.TEXT_PRIMARY}; font-weight: 500; "
        f"font-size: 11px; background: transparent; border: none; }}"
    )

    def _field(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(self._FIELD_LABEL_STYLE)
        return lbl

    def _value(self, text="—"):
        lbl = QLabel(text)
        lbl.setStyleSheet(self._VALUE_LABEL_STYLE)
        lbl.setWordWrap(True)
        return lbl

    def init_ui(self):
        """Initialize the UI components with compact grid layout"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-size: {Typography.FONT_SIZE_SM};
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_ACTIVE};
            }}
            QPushButton:disabled {{
                background-color: {Colors.TEXT_SECONDARY};
                color: {Colors.TEXT_MUTED};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Compact 2-column grid of all data points
        self.data_widget = QWidget()
        grid = QGridLayout(self.data_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(3)
        grid.setHorizontalSpacing(8)

        row = 0

        # ── Recommended Setup ──
        grid.addWidget(self._field("TYPE"), row, 0)
        self.rec_type = self._value("—")
        grid.addWidget(self.rec_type, row, 1)
        row += 1

        grid.addWidget(self._field("COUNT"), row, 0)
        self.rec_count = self._value("—")
        grid.addWidget(self.rec_count, row, 1)
        row += 1

        grid.addWidget(self._field("POWER"), row, 0)
        self.rec_power = self._value("—")
        grid.addWidget(self.rec_power, row, 1)
        row += 1

        grid.addWidget(self._field("SPACING"), row, 0)
        self.rec_spacing = self._value("—")
        grid.addWidget(self.rec_spacing, row, 1)
        row += 1

        grid.addWidget(self._field("COVERAGE"), row, 0)
        self.rec_coverage = self._value("—")
        grid.addWidget(self.rec_coverage, row, 1)
        row += 1

        # ── Zone Analysis ──
        grid.addWidget(self._field("CEILING"), row, 0)
        self.ceiling_height = self._value("—")
        grid.addWidget(self.ceiling_height, row, 1)
        row += 1

        grid.addWidget(self._field("RECOMMEND"), row, 0)
        self.height_recommendation = self._value("—")
        grid.addWidget(self.height_recommendation, row, 1)
        row += 1

        grid.addWidget(self._field("PENDANT HT"), row, 0)
        self.pendant_height = self._value("—")
        grid.addWidget(self.pendant_height, row, 1)
        row += 1

        grid.addWidget(self._field("TARGET SPL"), row, 0)
        self.target_spl = self._value("—")
        grid.addWidget(self.target_spl, row, 1)
        row += 1

        grid.addWidget(self._field("EST. AMBIENT"), row, 0)
        self.ambient_noise = self._value("—")
        grid.addWidget(self.ambient_noise, row, 1)
        row += 1

        grid.addWidget(self._field("HEADROOM"), row, 0)
        self.headroom = self._value("—")
        grid.addWidget(self.headroom, row, 1)

        grid.setColumnStretch(1, 1)

        main_layout.addWidget(self.data_widget)

        # Calculate button
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 4, 0, 0)
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self.on_calculate)
        btn_layout.addStretch()
        btn_layout.addWidget(self.calculate_button)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        main_layout.addStretch(1)

        # "No zone selected" message
        self.no_zone_label = QLabel("Select a zone to view recommendations")
        self.no_zone_label.setAlignment(Qt.AlignCenter)
        self.no_zone_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_BASE};
                font-style: italic;
                padding: 12px;
                background-color: {Colors.GRAY_100};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
            }}
        """)
        main_layout.addWidget(self.no_zone_label)

        # Initially hide data grid
        self.data_widget.setVisible(False)
        self.calculate_button.setVisible(False)

    def generate_recommendations(self, zone):
        """Generate speaker recommendations for the selected zone"""
        if not zone:
            self.current_zone = None
            self.data_widget.setVisible(False)
            self.calculate_button.setVisible(False)
            self.no_zone_label.setVisible(True)
            return

        self.current_zone = zone

        self.data_widget.setVisible(True)
        self.calculate_button.setVisible(True)
        self.no_zone_label.setVisible(False)

        self._analyze_ceiling_height(zone)
        self._analyze_spl_requirements(zone)

        if self.auto_mode:
            self.on_calculate()

    def _analyze_ceiling_height(self, zone):
        """Analyze ceiling height to determine speaker type"""
        ceiling_height = zone.get('ceiling_height', 10)
        self.ceiling_height.setText(f"{ceiling_height} ft")

        if ceiling_height < 8:
            recommendation = "In-Ceiling recommended"
            pendant_height = "N/A"
        elif 8 <= ceiling_height <= 12:
            recommendation = "In-Ceiling recommended"
            pendant_height = f"{ceiling_height - 4} ft"
        elif 12 < ceiling_height <= 20:
            recommendation = "Pendants recommended"
            pendant_height = "8 ft"
        else:
            recommendation = "Pendants recommended"
            pendant_height = "8-10 ft"

        self.height_recommendation.setText(recommendation)
        self.pendant_height.setText(pendant_height)

    def _analyze_spl_requirements(self, zone):
        """Analyze SPL requirements for the zone"""
        target_spl = zone.get('target_spl', 85)
        environment_type = zone.get('environment_type', 'enclosed')
        if environment_type == 'enclosed':
            ambient_noise = 45
        else:
            ambient_noise = 55

        headroom = max(15, target_spl - ambient_noise)

        self.target_spl.setText(f"{target_spl} dB")
        self.ambient_noise.setText(f"{ambient_noise} dB")
        self.headroom.setText(f"{headroom} dB")

    def on_calculate(self):
        """Calculate optimal speaker setup"""
        if not self.current_zone:
            return

        if 'points' in self.current_zone and self.current_zone['points']:
            points = self.current_zone['points']
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)

            ceiling_height = self.current_zone.get('ceiling_height', 10)
            target_spl = self.current_zone.get('target_spl', 85)

            zone_width = self.current_zone.get('length', (max_x - min_x) / 12)
            zone_length = self.current_zone.get('width', (max_y - min_y) / 12)
            zone_area = zone_width * zone_length

            if ceiling_height < 8:
                speaker_type = "In-Ceiling"
                mounting_height = ceiling_height
            elif 8 <= ceiling_height <= 12:
                speaker_type = "In-Ceiling"
                mounting_height = ceiling_height
            else:  # ceiling > 12 ft
                speaker_type = "Pendant"
                mounting_height = min(ceiling_height - 2, 10)

            listener_height = 4
            dispersion_angle = 90

            coverage_height = mounting_height - listener_height
            if coverage_height <= 0:
                coverage_radius = 0
            else:
                angle_rad = math.radians(dispersion_angle / 2)
                coverage_radius = coverage_height * math.tan(angle_rad)

            speaker_coverage = math.pi * coverage_radius * coverage_radius
            effective_coverage = speaker_coverage * 0.85

            speaker_count = math.ceil(zone_area / effective_coverage) if effective_coverage > 0 else 2
            speaker_count = max(2, speaker_count)

            speaker_spacing = math.sqrt(zone_area / speaker_count) if speaker_count > 0 else 0

            ambient_noise = 45
            required_spl = target_spl
            sensitivity = 89
            max_distance = speaker_spacing if speaker_spacing > 0 else 1
            distance_attenuation = 20 * math.log10(max_distance) if max_distance > 0 else 0

            power_db = required_spl - sensitivity + distance_attenuation
            power_watts = 10 ** (power_db / 10)

            standard_watts = [5, 10, 15, 30, 60, 100]
            for std_power in standard_watts:
                if std_power >= power_watts:
                    power_watts = std_power
                    break

            if power_watts > 100:
                power_watts = 100

            coverage_percent = min(100, (speaker_count * effective_coverage / zone_area) * 100) if zone_area > 0 else 0

            self.rec_type.setText(speaker_type)
            self.rec_count.setText(f"{speaker_count}")
            self.rec_power.setText(f"{power_watts} W")
            self.rec_spacing.setText(f"{speaker_spacing:.1f} ft")
            self.rec_coverage.setText(f"{coverage_percent:.1f}%")

            self.logger.info(f"Generated speaker recommendation for zone: {self.current_zone.get('name')}")
            self.logger.debug(
                f"Recommended setup: {speaker_count} x {speaker_type} @ {power_watts}W, {speaker_spacing:.1f}ft spacing")

    def set_auto_mode(self, enabled):
        """Set automatic recommendation mode"""
        self.auto_mode = enabled
        if enabled and self.current_zone:
            self.on_calculate()
