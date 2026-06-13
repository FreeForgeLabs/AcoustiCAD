import math
import logging


class GridSnapper:
    """
    Snaps coordinates to an acoustic grid in world coordinates (feet).

    Works entirely in real-world coordinates (feet) - no pixel conversions.
    The grid size is determined by the AcousticGridManager based on speaker
    profile and zone properties.
    """

    def __init__(self, acoustic_grid_manager):
        """Initialize the grid snapper

        Args:
            acoustic_grid_manager: AcousticGridManager instance for grid size
        """
        self.acoustic_grid_manager = acoustic_grid_manager
        self.logger = logging.getLogger(__name__)

        # Snapping state
        self.enabled = True
        self.bypass_snap = False  # Set to True when Shift key is held

    def set_enabled(self, enabled):
        """Enable or disable grid snapping

        Args:
            enabled (bool): Whether snapping is enabled
        """
        self.enabled = enabled
        self.logger.debug(f"Grid snapping {'enabled' if enabled else 'disabled'}")

    def set_bypass(self, bypass):
        """Set bypass state (e.g., when Shift key is held)

        Args:
            bypass (bool): Whether to bypass snapping temporarily
        """
        self.bypass_snap = bypass

    def is_active(self):
        """Check if snapping is currently active

        Returns:
            bool: True if snapping should be applied
        """
        return self.enabled and not self.bypass_snap

    def snap_to_grid(self, x_feet, y_feet):
        """
        Snap coordinates to the acoustic grid

        Args:
            x_feet (float): X coordinate in feet (world coordinates)
            y_feet (float): Y coordinate in feet (world coordinates)

        Returns:
            tuple: (snapped_x, snapped_y) in feet
        """
        # If snapping is disabled or bypassed, return original coordinates
        if not self.is_active():
            self.logger.debug(f"Snapping inactive (enabled={self.enabled}, bypass={self.bypass_snap})")
            return (x_feet, y_feet)

        # Get grid size from acoustic manager
        grid_size_feet = self.acoustic_grid_manager.get_ideal_spacing()

        # If no grid size calculated, return original coordinates
        if grid_size_feet is None or grid_size_feet <= 0:
            self.logger.warning(f"No grid size available (size={grid_size_feet}), returning original coordinates")
            return (x_feet, y_feet)

        # Snap to nearest grid intersection
        snapped_x = self._snap_value(x_feet, grid_size_feet)
        snapped_y = self._snap_value(y_feet, grid_size_feet)

        self.logger.info(
            f"Snapped ({x_feet:.2f}, {y_feet:.2f}) → "
            f"({snapped_x:.2f}, {snapped_y:.2f}) "
            f"[grid: {grid_size_feet:.2f}ft]"
        )

        return (snapped_x, snapped_y)

    def _snap_value(self, value, grid_size):
        """
        Snap a single coordinate value to the nearest grid line

        Args:
            value (float): Coordinate value in feet
            grid_size (float): Grid spacing in feet

        Returns:
            float: Snapped value in feet
        """
        # Round to nearest grid line
        # Example: value=7.3ft, grid=5ft → round(7.3/5) × 5 = round(1.46) × 5 = 1 × 5 = 5ft
        #          value=8.2ft, grid=5ft → round(8.2/5) × 5 = round(1.64) × 5 = 2 × 5 = 10ft
        return round(value / grid_size) * grid_size

    def get_nearest_grid_point(self, x_feet, y_feet):
        """
        Get the nearest grid intersection point (always snapped, regardless of enabled state)

        Args:
            x_feet (float): X coordinate in feet
            y_feet (float): Y coordinate in feet

        Returns:
            tuple: (grid_x, grid_y) in feet, or None if no grid configured
        """
        grid_size_feet = self.acoustic_grid_manager.get_ideal_spacing()

        if grid_size_feet is None or grid_size_feet <= 0:
            return None

        snapped_x = self._snap_value(x_feet, grid_size_feet)
        snapped_y = self._snap_value(y_feet, grid_size_feet)

        return (snapped_x, snapped_y)

    def get_snap_distance(self, x_feet, y_feet):
        """
        Calculate distance to nearest grid intersection

        Args:
            x_feet (float): X coordinate in feet
            y_feet (float): Y coordinate in feet

        Returns:
            float: Distance to nearest grid point in feet, or None if no grid
        """
        nearest = self.get_nearest_grid_point(x_feet, y_feet)

        if nearest is None:
            return None

        snap_x, snap_y = nearest
        distance = math.sqrt((x_feet - snap_x) ** 2 + (y_feet - snap_y) ** 2)

        return distance

    def get_grid_lines_in_bounds(self, min_x_feet, min_y_feet, max_x_feet, max_y_feet):
        """
        Get all grid lines within specified bounds (for rendering)

        Args:
            min_x_feet (float): Minimum X in feet
            min_y_feet (float): Minimum Y in feet
            max_x_feet (float): Maximum X in feet
            max_y_feet (float): Maximum Y in feet

        Returns:
            dict: Dictionary with 'vertical' and 'horizontal' lists of grid line positions in feet
                  Returns None if no grid configured
        """
        grid_size_feet = self.acoustic_grid_manager.get_ideal_spacing()

        if grid_size_feet is None or grid_size_feet <= 0:
            return None

        # Calculate vertical grid lines (constant X values)
        vertical_lines = []
        start_x = math.floor(min_x_feet / grid_size_feet) * grid_size_feet
        x = start_x
        while x <= max_x_feet:
            if x >= min_x_feet:
                vertical_lines.append(x)
            x += grid_size_feet

        # Calculate horizontal grid lines (constant Y values)
        horizontal_lines = []
        start_y = math.floor(min_y_feet / grid_size_feet) * grid_size_feet
        y = start_y
        while y <= max_y_feet:
            if y >= min_y_feet:
                horizontal_lines.append(y)
            y += grid_size_feet

        return {
            'vertical': vertical_lines,
            'horizontal': horizontal_lines,
            'grid_size': grid_size_feet
        }

    def get_snap_info(self):
        """Get information about current snap configuration

        Returns:
            dict: Snap configuration info
        """
        grid_size = self.acoustic_grid_manager.get_ideal_spacing()

        return {
            'enabled': self.enabled,
            'bypass': self.bypass_snap,
            'active': self.is_active(),
            'grid_size_feet': grid_size,
            'has_grid': grid_size is not None and grid_size > 0,
        }

    def format_grid_size(self):
        """
        Format the grid size as a readable string

        Returns:
            str: Formatted grid size (e.g., "8.5 ft" or "8'-6"")
        """
        grid_size = self.acoustic_grid_manager.get_ideal_spacing()

        if grid_size is None:
            return "Not configured"

        # Convert to feet and inches
        feet = int(grid_size)
        inches = (grid_size - feet) * 12

        if inches < 0.5:
            # No significant inches, just show feet
            return f"{feet}'-0\""
        elif abs(inches - 6) < 0.5:
            # Close to 6 inches
            return f"{feet}'-6\""
        else:
            # Show precise inches
            return f"{feet}'-{inches:.0f}\""

    def snap_if_close(self, x_feet, y_feet, threshold_feet=0.5):
        """
        Snap to grid only if the point is within threshold distance

        This provides "magnetic" snapping behavior - only snaps if you're
        close to a grid line.

        Args:
            x_feet (float): X coordinate in feet
            y_feet (float): Y coordinate in feet
            threshold_feet (float): Maximum distance for snapping in feet

        Returns:
            tuple: (snapped_x, snapped_y) in feet, or original if too far
        """
        if not self.is_active():
            return (x_feet, y_feet)

        # Get distance to nearest grid point
        snap_distance = self.get_snap_distance(x_feet, y_feet)

        if snap_distance is None or snap_distance > threshold_feet:
            # Too far from grid, don't snap
            return (x_feet, y_feet)

        # Close enough, snap to grid
        return self.snap_to_grid(x_feet, y_feet)

    def clear(self):
        """Clear snap state"""
        self.enabled = True
        self.bypass_snap = False
        self.logger.debug("Grid snapper cleared")