import logging
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt


class GridManager:
    """Manages grid display and snap functionality for the zones view"""

    def __init__(self, parent_view):
        """
        Initialize the grid manager

        Args:
            parent_view: The parent canvas view
        """
        self.parent_view = parent_view
        self.logger = logging.getLogger(__name__)
        self.logger.debug("GridManager initialized")

        # Grid properties - Default to visible and snap-enabled
        self.enabled = True
        self.visible = True
        self.snap_enabled = True
        self.grid_size = 10  # Default grid size in pixels
        self.major_grid_lines = 5  # Draw darker line every X grid lines
        self.grid_color = QColor(100, 100, 100, 100)  # Semi-transparent gray
        self.major_grid_color = QColor(80, 80, 80, 150)  # Darker gray

    def set_visible(self, visible):
        """
        Set grid visibility

        Args:
            visible (bool): Whether to show the grid

        Returns:
            bool: True if state changed, False otherwise
        """
        if self.visible != visible:
            self.visible = visible
            self.logger.debug(f"Grid visibility set to {visible}")
            if self.parent_view:
                self.parent_view.update()
            return True
        return False

    def is_visible(self):
        """
        Check if grid is visible

        Returns:
            bool: True if grid is visible, False otherwise
        """
        return self.visible

    def set_snap_enabled(self, enabled):
        """
        Enable or disable grid snapping

        Args:
            enabled (bool): Whether to enable snapping

        Returns:
            bool: True if state changed, False otherwise
        """
        if self.snap_enabled != enabled:
            self.snap_enabled = enabled
            self.logger.debug(f"Grid snapping set to {enabled}")
            return True
        return False

    def is_snap_enabled(self):
        """
        Check if grid snapping is enabled

        Returns:
            bool: True if snapping is enabled, False otherwise
        """
        return self.snap_enabled

    def set_grid_size(self, size):
        """
        Set the grid size in pixels

        Args:
            size (int): The grid size (must be positive)

        Returns:
            bool: True if successful, False otherwise
        """
        if size <= 0:
            self.logger.warning(f"Invalid grid size: {size}")
            return False

        if self.grid_size != size:
            self.grid_size = size
            self.logger.debug(f"Grid size set to {size}")
            if self.parent_view:
                self.parent_view.update()
            return True
        return False

    def get_grid_size(self):
        """
        Get the current grid size

        Returns:
            int: The grid size in pixels
        """
        return self.grid_size

    def snap_to_grid(self, x, y):
        """
        Snap a point to the nearest grid intersection

        Args:
            x (float): X coordinate
            y (float): Y coordinate

        Returns:
            tuple: (snapped_x, snapped_y) coordinates
        """
        if not self.snap_enabled:
            return (x, y)

        try:
            # Calculate nearest grid intersection
            snapped_x = round(x / self.grid_size) * self.grid_size
            snapped_y = round(y / self.grid_size) * self.grid_size
            self.logger.debug(f"Snapped point ({x}, {y}) to ({snapped_x}, {snapped_y})")
            return (snapped_x, snapped_y)
        except Exception as e:
            self.logger.error(f"Error in snap_to_grid: {e}", exc_info=True)
            return (x, y)

    # In GridManager.draw method:
    def draw(self, painter, viewport_rect=None):
        """Draw the grid on the specified painter"""
        if not self.visible or not painter:
            return

        try:
            # Save painter state
            painter.save()

            # Get canvas size
            if viewport_rect:
                width = viewport_rect.width()
                height = viewport_rect.height()
                origin_x = viewport_rect.x()
                origin_y = viewport_rect.y()
            else:
                width = self.parent_view.width()
                height = self.parent_view.height()
                origin_x = 0
                origin_y = 0

            # Calculate grid lines
            h_lines = int(height / self.grid_size) + 1
            v_lines = int(width / self.grid_size) + 1

            # Calculate starting positions
            start_x = int(origin_x / self.grid_size) * self.grid_size
            start_y = int(origin_y / self.grid_size) * self.grid_size

            # Draw vertical lines
            for i in range(v_lines + 1):
                x = start_x + (i * self.grid_size)

                # Skip if outside viewport
                if x < origin_x or x > origin_x + width:
                    continue

                # Check if major grid line
                if i % self.major_grid_lines == 0:
                    painter.setPen(QPen(self.major_grid_color, 1, Qt.SolidLine))
                else:
                    painter.setPen(QPen(self.grid_color, 1, Qt.DotLine))

                # Simply convert all coordinates to integers
                painter.drawLine(int(x), int(origin_y), int(x), int(origin_y + height))

            # Draw horizontal lines
            for i in range(h_lines + 1):
                y = start_y + (i * self.grid_size)

                # Skip if outside viewport
                if y < origin_y or y > origin_y + height:
                    continue

                # Check if major grid line
                if i % self.major_grid_lines == 0:
                    painter.setPen(QPen(self.major_grid_color, 1, Qt.SolidLine))
                else:
                    painter.setPen(QPen(self.grid_color, 1, Qt.DotLine))

                # Simply convert all coordinates to integers
                painter.drawLine(int(origin_x), int(y), int(origin_x + width), int(y))

            # Restore painter state
            painter.restore()

        except Exception as e:
            self.logger.error(f"Error drawing grid: {e}", exc_info=True)
            # Restore painter state even on error
            try:
                painter.restore()
            except:
                pass

    def toggle_grid(self):
        """
        Toggle grid visibility

        Returns:
            bool: The new visibility state
        """
        self.set_visible(not self.visible)
        return self.visible

    def toggle_snap(self):
        """
        Toggle grid snapping

        Returns:
            bool: The new snap state
        """
        self.set_snap_enabled(not self.snap_enabled)
        return self.snap_enabled