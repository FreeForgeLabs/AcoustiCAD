import math
import time
import logging
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QRadialGradient
from PySide6.QtCore import Qt, QPoint, QRectF


class SpeakerRenderer:
    """Handles speaker visualization and coverage patterns"""

    # Speaker types and their visual properties
    SPEAKER_TYPES = {
        "In-Ceiling": {"color": QColor(0, 120, 215), "icon": "ceiling"},
        "Pendant": {"color": QColor(0, 180, 120), "icon": "pendant"},
    }

    # Default icon size in pixels
    ICON_SIZE = 16

    def __init__(self, scale_manager):
        """Initialize the speaker renderer

        Args:
            scale_manager: The scale manager for conversions
        """
        self.scale_manager = scale_manager
        self.logger = logging.getLogger(__name__)

    def draw_speakers(self, painter, speakers_dict, selected_speaker_ids=None,
                      selected_speaker_id=None, show_coverage=True, scale_factor=1.0):
        """Draw all speakers and their coverage patterns

        Args:
            painter (QPainter): The painter to draw with
            speakers_dict (dict): Dictionary of speaker data by ID
            selected_speaker_ids (set): Set of currently selected speaker IDs
            selected_speaker_id (str): Backward-compat single ID (wrapped into a set)
            show_coverage (bool): Whether to show coverage patterns
            scale_factor (float): Current view scale factor
        """
        # Backward compat: if old single-id arg is passed, wrap it
        if selected_speaker_id is not None and not selected_speaker_ids:
            selected_speaker_ids = {selected_speaker_id}

        if not speakers_dict:
            return

        # Save painter state
        painter.save()

        try:
            # Draw coverage patterns first (behind speakers)
            if show_coverage:
                for speaker_id, speaker in speakers_dict.items():
                    self._draw_coverage_pattern(painter, speaker, scale_factor)

            # Draw speaker icons on top
            for speaker_id, speaker in speakers_dict.items():
                is_selected = bool(selected_speaker_ids and speaker_id in selected_speaker_ids)
                self._draw_speaker_icon(painter, speaker_id, speaker, is_selected, scale_factor)

        finally:
            # Restore painter state
            painter.restore()

    def _draw_speaker_icon(self, painter, speaker_id, speaker, is_selected=False, scale_factor=1.0):
        """Draw a single speaker icon

        Args:
            painter (QPainter): The painter to draw with
            speaker_id (str): Speaker ID
            speaker (dict): Speaker data
            is_selected (bool): Whether this speaker is selected
            scale_factor (float): Current view scale factor
        """
        # Extract position with validation
        position = speaker.get('position', (0, 0))
        if isinstance(position, list):
            x, y = tuple(position)
        else:
            x, y = position

        speaker_type = speaker.get('type', "In-Ceiling")

        # Set colors based on type and selection
        if is_selected:
            color = QColor(255, 140, 0)  # Orange highlight
            pen_width = 3
        else:
            color = self.SPEAKER_TYPES.get(speaker_type, {}).get('color', QColor(0, 0, 0))
            pen_width = 2

        # Calculate speaker size
        diameter_pixels = self._calculate_speaker_size(speaker, scale_factor)
        half_size = diameter_pixels / 2

        # Set up drawing
        pen = QPen(color)
        pen.setWidth(pen_width)
        painter.setPen(pen)

        # Fill color (lighter version of outline)
        fill_color = QColor(color)
        fill_color.setAlpha(180)
        painter.setBrush(QBrush(fill_color))

        # Convert to integers for drawing functions
        ix, iy = int(x), int(y)
        i_diameter = int(diameter_pixels)
        i_half = int(half_size)

        # Draw based on speaker type
        if speaker_type == "Pendant":
            self._draw_pendant_speaker(painter, ix, iy, i_diameter, i_half)
        else:  # In-Ceiling (default)
            self._draw_ceiling_speaker(painter, ix, iy, i_diameter, i_half)

        # Draw speaker info if selected
        if is_selected:
            self._draw_speaker_info(painter, speaker, x, y, diameter_pixels)

    def _draw_ceiling_speaker(self, painter, x, y, diameter, half_size):
        """Draw an in-ceiling speaker icon"""
        # Draw circle
        painter.drawEllipse(x - half_size, y - half_size, diameter, diameter)
        # Draw crosshairs
        painter.drawLine(x, y - half_size, x, y + half_size)
        painter.drawLine(x - half_size, y, x + half_size, y)

    def _draw_pendant_speaker(self, painter, x, y, diameter, half_size):
        """Draw a pendant speaker icon"""
        # Draw line from ceiling
        line_top = int(y - diameter)
        half_height = half_size // 2
        painter.drawLine(x, line_top, x, y - half_height)

        # Triangle pointing down
        points = [
            QPoint(x, y + half_size),
            QPoint(x - half_size, y - half_height),
            QPoint(x + half_size, y - half_height)
        ]
        painter.drawPolygon(points)

    def _draw_speaker_info(self, painter, speaker, x, y, diameter_pixels):
        """Draw information text for selected speaker"""
        power = speaker.get('power', 'N/A')
        sensitivity = speaker.get('sensitivity', 'N/A')
        info_text = f"{power}W, {sensitivity}dB"

        painter.setPen(Qt.black)
        text_rect = QRectF(x - 40, y + diameter_pixels / 2, 80, 20)
        painter.fillRect(text_rect, QColor(255, 255, 255, 200))
        painter.drawText(text_rect, Qt.AlignCenter, info_text)

    def _draw_coverage_pattern(self, painter, speaker, scale_factor=1.0):
        """Draw the coverage pattern for a speaker with crash protection

        Args:
            painter (QPainter): The painter to draw with
            speaker (dict): Speaker data
            scale_factor (float): Current view scale factor
        """
        # Set a timeout to prevent infinite processing
        start_time = time.time()
        MAX_PROCESSING_TIME = 0.1  # 100ms maximum

        try:
            # Extract and validate position
            position = speaker.get('position', (0, 0))
            if isinstance(position, list):
                position = tuple(position)

            if not isinstance(position, tuple) or len(position) != 2:
                return

            x, y = position
            if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                return

            # Validate position range
            if abs(x) > 10000 or abs(y) > 10000:
                return

            # Get and validate dispersion angle
            dispersion = float(speaker.get('dispersion_angle', 90))
            if dispersion <= 0 or dispersion > 360:
                dispersion = 90

            # Get speaker type
            speaker_type = speaker.get('type', "In-Ceiling")

            # Calculate coverage radius
            coverage_radius = self._calculate_coverage_radius(speaker, dispersion)
            if coverage_radius <= 0:
                return

            # Convert radius to pixels using scale manager
            radius_px = self.scale_manager.feet_to_pixels(coverage_radius)
            radius_px = max(5, min(radius_px, 500))  # Safety limits

            # Draw coverage pattern
            self._draw_coverage_circle(painter, x, y, radius_px, speaker_type)

        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed > 0.05:
                self.logger.warning(f"Coverage drawing took {elapsed:.3f}s")

    def _calculate_coverage_radius(self, speaker, dispersion_angle):
        """Calculate the coverage radius for a speaker

        Args:
            speaker (dict): Speaker data
            dispersion_angle (float): Dispersion angle in degrees

        Returns:
            float: Coverage radius in feet
        """
        try:
            # Get speaker height based on type
            speaker_type = speaker.get('type', "In-Ceiling")

            if speaker_type == "Pendant":
                height = float(speaker.get('mounting_height', 8))
            else:  # In-Ceiling (default)
                height = float(speaker.get('ceiling_height', 10))

            # Validate height
            if height <= 0:
                height = 8
            elif height > 100:
                height = 20

            # Calculate coverage height (distance from speaker to listener level)
            listening_height = float(speaker.get('listener_height', 4.0))
            coverage_height = height - listening_height

            if coverage_height <= 0:
                return 0

            # Calculate radius using dispersion angle
            angle_rad = min(math.radians(dispersion_angle / 2), math.pi / 2)

            if angle_rad >= 1.5:  # ~85 degrees
                coverage_radius = coverage_height * 10
            else:
                coverage_radius = coverage_height * math.tan(angle_rad)

            # Apply reasonable limits
            return max(1, min(coverage_radius, 50))

        except (ValueError, TypeError, OverflowError, ZeroDivisionError):
            return 10  # Fallback value

    def _draw_coverage_circle(self, painter, x, y, radius_px, speaker_type):
        """Draw the coverage circle with gradient

        Args:
            painter (QPainter): The painter to draw with
            x, y (float): Speaker position
            radius_px (float): Coverage radius in pixels
            speaker_type (str): Type of speaker for color selection
        """
        try:
            ix, iy = int(x), int(y)
            iradius = int(radius_px)

            # Create gradient
            gradient = QRadialGradient(x, y, radius_px)

            # Set colors based on speaker type
            if speaker_type == "Pendant":
                base_color = QColor(0, 180, 120, 120)  # Green
            else:  # In-Ceiling (default)
                base_color = QColor(0, 120, 215, 120)  # Blue

            # Create gradient stops
            gradient.setColorAt(0, base_color)
            edge_color = QColor(base_color)
            edge_color.setAlpha(40)
            gradient.setColorAt(0.8, edge_color)
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

            # Draw filled circle
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(ix - iradius, iy - iradius, iradius * 2, iradius * 2)

            # Draw outline
            pen = QPen(QColor(80, 80, 80, 180))
            pen.setStyle(Qt.DotLine)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(ix - iradius, iy - iradius, iradius * 2, iradius * 2)

        except Exception as e:
            self.logger.error(f"Error drawing coverage circle: {e}")

    def _calculate_speaker_size(self, speaker, scale_factor):
        """Calculate the display size of a speaker icon

        Args:
            speaker (dict): Speaker data
            scale_factor (float): Current view scale factor

        Returns:
            float: Speaker diameter in pixels
        """
        # Get speaker size in inches
        diameter_inches = speaker.get('diameter', 6.0)

        try:
            # Convert inches to pixels using scale manager
            diameter_pixels = self.scale_manager.inches_to_pixels(diameter_inches)

            # FIXED: Painter is already transformed - use base pixels directly
            # Ensure minimum display size
            return max(diameter_pixels, self.ICON_SIZE / 2)

        except Exception as e:
            self.logger.error(f"Error calculating speaker size: {e}")
            return self.ICON_SIZE

    def get_speaker_click_radius(self, speaker, scale_factor):
        """Get the click detection radius for a speaker

        Args:
            speaker (dict): Speaker data
            scale_factor (float): Current view scale factor

        Returns:
            float: Click radius in scaled coordinates
        """
        return self.ICON_SIZE / scale_factor