import logging
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPen, QBrush, QColor, QFont


class ZonesRenderer:
    """Handles all rendering operations for the zones canvas"""

    def __init__(self, canvas):
        """
        Initialize the renderer with a reference to the canvas

        Args:
            canvas: The ZonesCanvas instance this renderer will draw for
        """
        self.canvas = canvas
        self.logger = logging.getLogger(__name__)

    def render_all(self, painter, visible_rect):
        """
        Render all canvas elements in the correct order

        Args:
            painter (QPainter): The painter to draw with (already scaled)
            visible_rect (QRectF): The visible viewport rectangle in scene coordinates
        """
        try:
            # Draw all elements in correct layering order
            self.draw_background(painter)
            self.draw_grid(painter, visible_rect)
            self.draw_zones(painter)
            self.draw_editable_points(painter)
            self.draw_current_drawing(painter)
            self.draw_calibration_elements(painter)

        except Exception as e:
            self.logger.error(f"Error during render_all: {e}", exc_info=True)

    def draw_background(self, painter):
        """Draw the background image"""
        try:
            self.canvas.background_manager.draw(painter)
        except Exception as e:
            self.logger.error(f"Error drawing background: {e}", exc_info=True)

    def draw_grid(self, painter, visible_rect):
        """Draw the grid"""
        try:
            self.canvas.grid_manager.draw(painter, visible_rect)
        except Exception as e:
            self.logger.error(f"Error drawing grid: {e}", exc_info=True)

    def draw_zones(self, painter):
        """Draw all zones with labels"""
        try:
            for i, zone in enumerate(self.canvas.zones):
                if not self._is_zone_drawable(zone):
                    continue

                # Set up drawing style
                pen, brush = self._get_zone_style(zone, i)
                painter.setPen(pen)
                painter.setBrush(brush)

                # Draw the polygon
                qt_points = [QPoint(int(p[0]), int(p[1])) for p in zone['points']]
                painter.drawPolygon(qt_points)

                # Draw zone label
                self.draw_zone_label(painter, zone, i)

        except Exception as e:
            self.logger.error(f"Error drawing zones: {e}", exc_info=True)

    def draw_zone_label(self, painter, zone, index):
        """
        Draw zone name and information at the center of the zone

        Args:
            painter (QPainter): The painter to draw with
            zone (dict): Zone data
            index (int): Zone index for fallback naming
        """
        try:
            points = zone['points']

            # Calculate center point for text
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)

            # Set font
            font = QFont()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)

            # Create text with zone details
            text = self._build_zone_label_text(zone, index)

            # Draw text with background for readability
            painter.save()

            # Draw semi-transparent background for text
            text_rect_x = int(center_x - 70)
            text_rect_y = int(center_y - 10)
            text_rect_width = 140
            text_rect_height = 20

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.drawRect(text_rect_x, text_rect_y, text_rect_width, text_rect_height)

            # Draw text
            painter.setPen(QPen(Qt.black))
            painter.drawText(text_rect_x, text_rect_y, text_rect_width, text_rect_height,
                             Qt.AlignCenter, text)

            painter.restore()

        except Exception as e:
            self.logger.error(f"Error drawing zone label: {e}", exc_info=True)

    def draw_editable_points(self, painter):
        """Draw editable points for existing zones"""
        try:
            self.canvas.drawing_manager.draw_editable_points(painter)
        except Exception as e:
            self.logger.error(f"Error drawing editable points: {e}", exc_info=True)

    def draw_current_drawing(self, painter):
        """Draw current drawing elements (lines being drawn)"""
        try:
            self.canvas.drawing_manager.draw(painter)
        except Exception as e:
            self.logger.error(f"Error drawing current drawing: {e}", exc_info=True)

    def draw_calibration_elements(self, painter):
        """Draw calibration elements if in calibration mode"""
        try:
            if not self.canvas.scale_manager.is_calibrating():
                return

            painter.save()
            painter.setPen(QPen(Qt.red, 2))

            # Draw calibration points
            for point in self.canvas.scale_manager.calibration_points:
                painter.drawEllipse(point[0] - 5, point[1] - 5, 10, 10)

            # Draw line between points if we have two
            if len(self.canvas.scale_manager.calibration_points) == 2:
                p1, p2 = self.canvas.scale_manager.calibration_points
                painter.drawLine(p1[0], p1[1], p2[0], p2[1])

                # Draw distance text
                self._draw_calibration_distance(painter, p1, p2)

            painter.restore()

        except Exception as e:
            self.logger.error(f"Error drawing calibration elements: {e}", exc_info=True)

    def _draw_calibration_distance(self, painter, p1, p2):
        """Draw distance text for calibration line"""
        try:
            distance_pixels = self.canvas.scale_manager.get_calibration_distance_pixels()
            if distance_pixels > 0:
                # Calculate midpoint
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2

                # Draw distance text with background
                font = QFont()
                font.setPointSize(9)
                painter.setFont(font)

                text = f"{distance_pixels:.1f} px"
                text_width = 60
                text_height = 20

                # Draw background
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 0, 200)))
                painter.drawRect(int(mid_x - text_width / 2), int(mid_y - text_height / 2 - 10),
                                 text_width, text_height)

                # Draw text
                painter.setPen(QPen(Qt.black))
                painter.drawText(int(mid_x - text_width / 2), int(mid_y - text_height / 2 - 10),
                                 text_width, text_height, Qt.AlignCenter, text)

        except Exception as e:
            self.logger.error(f"Error drawing calibration distance: {e}", exc_info=True)

    def _is_zone_drawable(self, zone):
        """Check if a zone has valid drawable data"""
        return ('points' in zone and
                zone['points'] and
                len(zone['points']) >= 3)

    def _get_zone_style(self, zone, index):
        """
        Get drawing style (pen and brush) for a zone

        Args:
            zone (dict): Zone data
            index (int): Zone index

        Returns:
            tuple: (QPen, QBrush) for drawing the zone
        """
        try:
            pen = QPen(QColor(0, 100, 0), 2)

            # Highlight selected zone
            if index == self.canvas.selected_zone_index:
                pen.setColor(QColor(0, 200, 0))
                pen.setWidth(3)

            # Get zone color from drawing manager
            zone_color = self.canvas.drawing_manager.get_zone_color(zone, index)
            brush = QBrush(zone_color)

            return pen, brush

        except Exception as e:
            self.logger.error(f"Error getting zone style: {e}", exc_info=True)
            # Return default style on error
            return QPen(QColor(0, 100, 0), 2), QBrush(QColor(200, 255, 200, 100))

    def _build_zone_label_text(self, zone, index):
        """
        Build the text label for a zone

        Args:
            zone (dict): Zone data
            index (int): Zone index for fallback naming

        Returns:
            str: Formatted label text
        """
        try:
            # Get basic zone info
            zone_name = zone.get('name', f'Zone {index + 1}')
            target_spl = zone.get('target_spl', 85)
            room_name = zone.get('room_name', '')

            # Build main text
            room_text = f" ({room_name})" if room_name else ""
            text = f"{zone_name} ({target_spl}dB){room_text}"

            # Add ceiling height if specified
            ceiling_height = zone.get('ceiling_height')
            if ceiling_height is not None:
                text += f" (H: {ceiling_height}ft)"

            return text

        except Exception as e:
            self.logger.error(f"Error building zone label text: {e}", exc_info=True)
            return f"Zone {index + 1}"

    def set_zone_highlight(self, zone_index, highlighted=True):
        """
        Set highlight state for a specific zone (for future use)

        Args:
            zone_index (int): Index of zone to highlight
            highlighted (bool): Whether to highlight the zone
        """
        # This method can be used for future features like hover highlighting
        # For now, highlighting is handled through the canvas's selected_zone_index
        pass

    def get_zone_at_point(self, point):
        """
        Get the zone index at a given point (for future use)

        Args:
            point (tuple): (x, y) coordinates

        Returns:
            int or None: Zone index if found, None otherwise
        """
        try:
            from core.zones.geometry_utils import point_inside_polygon

            for i, zone in enumerate(self.canvas.zones):
                if not self._is_zone_drawable(zone):
                    continue

                if point_inside_polygon(point, zone['points']):
                    return i

            return None

        except Exception as e:
            self.logger.error(f"Error getting zone at point: {e}", exc_info=True)
            return None

    def calculate_render_bounds(self):
        """
        Calculate the bounding rectangle of all renderable content

        Returns:
            tuple: (min_x, min_y, max_x, max_y) bounds
        """
        try:
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')

            # Consider background bounds
            if self.canvas.background_manager.has_background():
                bg_width, bg_height = self.canvas.background_manager.get_background_size()
                min_x = min(min_x, 0)
                min_y = min(min_y, 0)
                max_x = max(max_x, bg_width)
                max_y = max(max_y, bg_height)

            # Consider zone bounds
            for zone in self.canvas.zones:
                if not self._is_zone_drawable(zone):
                    continue

                for x, y in zone['points']:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

            # If no content found, return default bounds
            if min_x == float('inf'):
                return (0, 0, 800, 600)

            # Add some padding
            padding = 20
            return (min_x - padding, min_y - padding,
                    max_x + padding, max_y + padding)

        except Exception as e:
            self.logger.error(f"Error calculating render bounds: {e}", exc_info=True)
            return (0, 0, 800, 600)