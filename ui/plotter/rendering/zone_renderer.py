import logging
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QPoint, QRectF


class ZoneRenderer:
    """Handles zone visualization and rendering"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def draw_zone(self, painter, zone_data):
        """Draw the zone outline and information

        Args:
            painter (QPainter): The painter to draw with
            zone_data (dict): Zone data containing points and properties
        """
        if not zone_data:
            return

        # Draw zone outline
        self._draw_zone_outline(painter, zone_data)

        # Draw zone information overlay
        self._draw_zone_info(painter, zone_data)

    def draw_zone_for_snapshot(self, painter, zone_data):
        """Draw zone outline optimized for high-quality snapshots

        Args:
            painter (QPainter): The painter to draw with
            zone_data (dict): Zone data containing points and properties
        """
        if not zone_data or 'points' not in zone_data or not zone_data['points']:
            return

        # Draw zone with thicker lines for better visibility in reports
        pen = QPen(QColor(0, 100, 0))
        pen.setWidth(4)  # Thicker for high-res output
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Draw zone polygon
        points = zone_data['points']
        qt_points = [QPoint(int(p[0]), int(p[1])) for p in points]
        painter.drawPolygon(qt_points)

    def _draw_zone_outline(self, painter, zone_data):
        """Draw the zone boundary outline

        Args:
            painter (QPainter): The painter to draw with
            zone_data (dict): Zone data containing points
        """
        if 'points' not in zone_data or not zone_data['points']:
            return

        # Draw zone outline with a thicker, more visible pen
        pen = QPen(QColor(0, 100, 0))  # Dark green color
        pen.setWidth(3)  # Thick line for visibility
        painter.setPen(pen)

        # Remove the fill by setting no brush
        painter.setBrush(Qt.NoBrush)

        # Draw zone polygon
        points = zone_data['points']
        qt_points = [QPoint(int(p[0]), int(p[1])) for p in points]
        painter.drawPolygon(qt_points)

    def _draw_zone_info(self, painter, zone_data):
        """Draw zone information overlay in the center

        Args:
            painter (QPainter): The painter to draw with
            zone_data (dict): Zone data containing properties
        """
        if 'points' not in zone_data or not zone_data['points']:
            return

        points = zone_data['points']

        # Set up text drawing
        painter.setPen(Qt.black)
        font = QFont()
        font.setBold(True)
        painter.setFont(font)

        # Calculate center of the zone
        center_x = sum(p[0] for p in points) / len(points)
        center_y = sum(p[1] for p in points) / len(points)

        # Create zone info text
        zone_name = zone_data.get('name', 'Unnamed Zone')
        ceiling_height = zone_data.get('ceiling_height', 'unknown')
        target_spl = zone_data.get('target_spl', 'unknown')

        info_text = f"{zone_name}\nCeiling: {ceiling_height} ft\nTarget SPL: {target_spl} dB"

        # Draw text with background
        text_rect = QRectF(center_x - 100, center_y - 40, 200, 80)
        painter.fillRect(text_rect, QColor(255, 255, 255, 180))
        painter.drawText(text_rect, Qt.AlignCenter, info_text)

    def draw_no_zone_message(self, painter, widget_rect):
        """Draw a message when no zone is selected

        Args:
            painter (QPainter): The painter to draw with
            widget_rect (QRect): The widget's rectangle for centering
        """
        painter.setPen(Qt.gray)
        painter.drawText(widget_rect, Qt.AlignCenter, "No zone selected")

    def calculate_zone_bounds(self, zone_data):
        """Calculate the bounding box of a zone

        Args:
            zone_data (dict): Zone data containing points

        Returns:
            tuple: (min_x, min_y, max_x, max_y) or None if invalid
        """
        if not zone_data or 'points' not in zone_data or not zone_data['points']:
            return None

        points = zone_data['points']

        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        return (min_x, min_y, max_x, max_y)

    def get_zone_center(self, zone_data):
        """Get the center point of a zone

        Args:
            zone_data (dict): Zone data containing points

        Returns:
            tuple: (center_x, center_y) or None if invalid
        """
        bounds = self.calculate_zone_bounds(zone_data)
        if not bounds:
            return None

        min_x, min_y, max_x, max_y = bounds
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        return (center_x, center_y)

    def get_zone_dimensions(self, zone_data):
        """Get the width and height of a zone

        Args:
            zone_data (dict): Zone data containing points

        Returns:
            tuple: (width, height) or None if invalid
        """
        bounds = self.calculate_zone_bounds(zone_data)
        if not bounds:
            return None

        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x
        height = max_y - min_y

        return (width, height)