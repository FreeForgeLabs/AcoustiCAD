import logging
from PySide6.QtGui import QPen, QColor, QFont
from PySide6.QtCore import Qt


class GridRenderer:
    """Renders visual grid overlay at acoustic spacing intervals"""

    def __init__(self, scale_manager, grid_snapper):
        """Initialize the grid renderer

        Args:
            scale_manager: ScaleManager for unit conversions
            grid_snapper: GridSnapper for grid line calculations
        """
        self.scale_manager = scale_manager
        self.grid_snapper = grid_snapper
        self.logger = logging.getLogger(__name__)

        # Rendering state
        self.visible = False

        # Visual styling
        self.grid_color = QColor(180, 180, 180, 100)  # Light gray, semi-transparent
        self.grid_line_width = 1
        self.label_color = QColor(100, 100, 100, 180)
        self.label_font_size = 9

    def set_visible(self, visible):
        """Set grid visibility

        Args:
            visible (bool): Whether grid should be visible
        """
        self.visible = visible
        self.logger.debug(f"Grid visibility: {visible}")

    def is_visible(self):
        """Check if grid is visible

        Returns:
            bool: True if grid should be rendered
        """
        return self.visible

    def draw_grid(self, painter, viewport_manager, zone_bounds=None):
        """
        Draw the grid overlay

        Args:
            painter (QPainter): The painter to draw with (already transformed to world coords)
            viewport_manager: ViewportManager for getting visible bounds
            zone_bounds (tuple): Optional (min_x, min_y, max_x, max_y) to constrain grid
        """
        if not self.visible:
            return

        # Get visible bounds from viewport in world coordinates
        visible_bounds = viewport_manager.get_visible_world_bounds()
        if not visible_bounds:
            return

        min_x, min_y, max_x, max_y = visible_bounds

        # Constrain to zone bounds if provided
        if zone_bounds:
            zone_min_x, zone_min_y, zone_max_x, zone_max_y = zone_bounds
            min_x = max(min_x, zone_min_x)
            min_y = max(min_y, zone_min_y)
            max_x = min(max_x, zone_max_x)
            max_y = min(max_y, zone_max_y)

        # Get grid lines from snapper (in world coordinates - feet)
        grid_data = self.grid_snapper.get_grid_lines_in_bounds(min_x, min_y, max_x, max_y)

        if not grid_data:
            # No grid configured
            return

        # Save painter state
        painter.save()

        try:
            # Set up pen for grid lines
            pen = QPen(self.grid_color)
            pen.setWidth(self.grid_line_width)
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)

            # Draw vertical grid lines (constant X)
            for x in grid_data['vertical']:
                # Lines are in world coordinates, painter is already transformed
                painter.drawLine(int(x), int(min_y), int(x), int(max_y))

            # Draw horizontal grid lines (constant Y)
            for y in grid_data['horizontal']:
                painter.drawLine(int(min_x), int(y), int(max_x), int(y))

            # Draw grid spacing labels at intersections
            self._draw_grid_labels(painter, grid_data, min_x, min_y, max_x, max_y)

        finally:
            # Restore painter state
            painter.restore()

    def _draw_grid_labels(self, painter, grid_data, min_x, min_y, max_x, max_y):
        """
        Draw spacing labels on the grid

        Args:
            painter (QPainter): The painter to draw with
            grid_data (dict): Grid line data from snapper
            min_x, min_y, max_x, max_y: Visible bounds in world coordinates
        """
        grid_size = grid_data.get('grid_size')
        if not grid_size:
            return

        # Format grid size for display
        formatted_size = self.grid_snapper.format_grid_size()

        # Set up font for labels
        font = QFont("Arial", self.label_font_size)
        painter.setFont(font)
        painter.setPen(self.label_color)

        # Draw label at first visible intersection
        vertical_lines = grid_data.get('vertical', [])
        horizontal_lines = grid_data.get('horizontal', [])

        if vertical_lines and horizontal_lines:
            # Place label at top-left grid intersection
            label_x = vertical_lines[0]
            label_y = horizontal_lines[0]

            # Offset label slightly from intersection
            label_text = f"Grid: {formatted_size}"
            painter.drawText(int(label_x + 0.2), int(label_y + 0.5), label_text)

    def draw_snap_preview(self, painter, current_x, current_y):
        """
        Draw a preview of where a point will snap to

        Args:
            painter (QPainter): The painter to draw with
            current_x, current_y: Current cursor position in world coordinates (feet)
        """
        if not self.visible:
            return

        # Get snap point
        snap_point = self.grid_snapper.get_nearest_grid_point(current_x, current_y)

        if not snap_point:
            return

        snap_x, snap_y = snap_point

        # Save painter state
        painter.save()

        try:
            # Draw crosshair at snap point
            pen = QPen(QColor(255, 140, 0, 200))  # Orange
            pen.setWidth(2)
            painter.setPen(pen)

            # Draw small crosshair (in world coordinates)
            cross_size = 1.0  # 1 foot radius
            painter.drawLine(
                int(snap_x - cross_size), int(snap_y),
                int(snap_x + cross_size), int(snap_y)
            )
            painter.drawLine(
                int(snap_x), int(snap_y - cross_size),
                int(snap_x), int(snap_y + cross_size)
            )

            # Draw circle at snap point
            painter.drawEllipse(
                int(snap_x - 0.3), int(snap_y - 0.3),
                int(0.6), int(0.6)
            )

        finally:
            painter.restore()

    def set_grid_color(self, color):
        """Set the grid line color

        Args:
            color (QColor): Grid line color
        """
        self.grid_color = color

    def set_label_color(self, color):
        """Set the label text color

        Args:
            color (QColor): Label color
        """
        self.label_color = color

    def clear(self):
        """Clear renderer state"""
        self.visible = False
        self.logger.debug("Grid renderer cleared")