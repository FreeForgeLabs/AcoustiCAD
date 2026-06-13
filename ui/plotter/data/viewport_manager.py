import logging
from PySide6.QtCore import QObject, Signal


class ViewportManager(QObject):
    """Manages viewport transformations, scaling, and positioning"""

    # Signals
    viewport_changed = Signal()  # Emitted when viewport changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Viewport state
        self.scale_factor = 1.0  # pixels per foot
        self.offset_x = 50  # X offset in pixels
        self.offset_y = 50  # Y offset in pixels

        # View dimensions (will be updated by the parent view)
        self.view_width = 800
        self.view_height = 600

        # Current zone data for calculations
        self.current_zone_bounds = None  # (min_x, min_y, max_x, max_y)
        self.current_zone_center = None  # (center_x, center_y)

    def set_view_size(self, width, height):
        """Update the view dimensions

        Args:
            width (int): View width in pixels
            height (int): View height in pixels
        """
        if self.view_width != width or self.view_height != height:
            self.view_width = width
            self.view_height = height
            self.logger.debug(f"View size updated to {width}x{height}")

            # If we have a zone loaded, recenter it
            if self.current_zone_bounds:
                self._recenter_current_zone()

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates

        Args:
            screen_x (float): Screen X coordinate in pixels
            screen_y (float): Screen Y coordinate in pixels

        Returns:
            tuple: (world_x, world_y) in world units
        """
        world_x = (screen_x - self.offset_x) / self.scale_factor
        world_y = (screen_y - self.offset_y) / self.scale_factor
        return (world_x, world_y)

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates

        Args:
            world_x (float): World X coordinate
            world_y (float): World Y coordinate

        Returns:
            tuple: (screen_x, screen_y) in pixels
        """
        screen_x = (world_x * self.scale_factor) + self.offset_x
        screen_y = (world_y * self.scale_factor) + self.offset_y
        return (screen_x, screen_y)

    def set_zone(self, zone_data):
        """Set the current zone and calculate optimal viewport

        Args:
            zone_data (dict): Zone data containing 'points' list

        Returns:
            bool: True if viewport was updated, False if no valid zone
        """
        if not zone_data or 'points' not in zone_data or not zone_data['points']:
            self.current_zone_bounds = None
            self.current_zone_center = None
            return False

        # Calculate zone bounds
        points = zone_data['points']
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        self.current_zone_bounds = (min_x, min_y, max_x, max_y)

        # Calculate zone center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.current_zone_center = (center_x, center_y)

        # Calculate zone dimensions
        zone_width = max_x - min_x
        zone_height = max_y - min_y

        self.logger.debug(f"Zone bounds: {self.current_zone_bounds}")
        self.logger.debug(f"Zone center: {self.current_zone_center}")
        self.logger.debug(f"Zone dimensions: {zone_width} x {zone_height}")

        # Calculate optimal scale and offset
        self._calculate_optimal_viewport(zone_width, zone_height, center_x, center_y)

        # Emit change signal
        self.viewport_changed.emit()

        return True

    def _calculate_optimal_viewport(self, zone_width, zone_height, center_x, center_y):
        """Calculate optimal scale and offset for the zone

        Args:
            zone_width (float): Zone width in world units
            zone_height (float): Zone height in world units
            center_x (float): Zone center X in world units
            center_y (float): Zone center Y in world units
        """
        if zone_width <= 0 or zone_height <= 0:
            return

        # Calculate scale to make zone take up about 70% of the viewable area
        scale_x = (self.view_width * 0.7) / zone_width
        scale_y = (self.view_height * 0.7) / zone_height

        # Use the smaller scale to ensure the entire zone fits
        self.scale_factor = min(scale_x, scale_y)

        # Calculate offset to center the zone in the view
        self.offset_x = (self.view_width / 2) - (center_x * self.scale_factor)
        self.offset_y = (self.view_height / 2) - (center_y * self.scale_factor)

        self.logger.debug(f"Calculated scale factor: {self.scale_factor}")
        self.logger.debug(f"Calculated offset: ({self.offset_x}, {self.offset_y})")

    def _recenter_current_zone(self):
        """Recenter the current zone after view size change"""
        if not self.current_zone_center:
            return

        center_x, center_y = self.current_zone_center

        # Update offset to center the zone in the new view size
        self.offset_x = (self.view_width / 2) - (center_x * self.scale_factor)
        self.offset_y = (self.view_height / 2) - (center_y * self.scale_factor)

        self.logger.debug(f"Recentered zone to offset: ({self.offset_x}, {self.offset_y})")

        # Emit change signal
        self.viewport_changed.emit()

    def fit_zone_to_view(self, margin_pixels=50):
        """Fit the current zone to the view with optional margin

        Args:
            margin_pixels (int): Margin around the zone in pixels

        Returns:
            bool: True if successful, False if no zone loaded
        """
        if not self.current_zone_bounds:
            return False

        min_x, min_y, max_x, max_y = self.current_zone_bounds

        # Add margin to bounds
        margin_world = margin_pixels / self.scale_factor
        min_x_margin = min_x - margin_world
        max_x_margin = max_x + margin_world
        min_y_margin = min_y - margin_world
        max_y_margin = max_y + margin_world

        # Calculate dimensions with margin
        width_with_margin = max_x_margin - min_x_margin
        height_with_margin = max_y_margin - min_y_margin

        # Calculate scale to fit with margin
        if width_with_margin > 0 and height_with_margin > 0:
            scale_x = self.view_width / width_with_margin
            scale_y = self.view_height / height_with_margin

            # Use the smaller scale and limit to reasonable values
            fit_scale = min(scale_x, scale_y) * 0.9  # 90% to add some buffer
            fit_scale = min(fit_scale, 2.0)  # Don't scale up too much

            # Only scale down, not up
            if fit_scale < self.scale_factor:
                self.scale_factor = fit_scale

                # Recalculate center and offset
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2

                self.offset_x = (self.view_width / 2) - (center_x * self.scale_factor)
                self.offset_y = (self.view_height / 2) - (center_y * self.scale_factor)

                self.logger.debug(f"Fitted zone with scale: {self.scale_factor}")
                self.viewport_changed.emit()

        return True

    def zoom_in(self, factor=1.2):
        """Zoom in by the specified factor

        Args:
            factor (float): Zoom factor (> 1.0 to zoom in)
        """
        old_scale = self.scale_factor
        self.scale_factor *= factor

        # Limit maximum zoom
        self.scale_factor = min(self.scale_factor, 10.0)

        if self.scale_factor != old_scale:
            # Adjust offset to maintain center point
            if self.current_zone_center:
                center_x, center_y = self.current_zone_center
                self.offset_x = (self.view_width / 2) - (center_x * self.scale_factor)
                self.offset_y = (self.view_height / 2) - (center_y * self.scale_factor)

            self.logger.debug(f"Zoomed in to scale: {self.scale_factor}")
            self.viewport_changed.emit()

    def zoom_out(self, factor=1.2):
        """Zoom out by the specified factor

        Args:
            factor (float): Zoom factor (> 1.0 to zoom out more)
        """
        old_scale = self.scale_factor
        self.scale_factor /= factor

        # Limit minimum zoom
        self.scale_factor = max(self.scale_factor, 0.1)

        if self.scale_factor != old_scale:
            # Adjust offset to maintain center point
            if self.current_zone_center:
                center_x, center_y = self.current_zone_center
                self.offset_x = (self.view_width / 2) - (center_x * self.scale_factor)
                self.offset_y = (self.view_height / 2) - (center_y * self.scale_factor)

            self.logger.debug(f"Zoomed out to scale: {self.scale_factor}")
            self.viewport_changed.emit()

    def pan(self, delta_x, delta_y):
        """Pan the viewport by the specified pixel amounts

        Args:
            delta_x (float): X offset change in pixels
            delta_y (float): Y offset change in pixels
        """
        self.offset_x += delta_x
        self.offset_y += delta_y

        self.logger.debug(f"Panned to offset: ({self.offset_x}, {self.offset_y})")
        self.viewport_changed.emit()

    def reset_viewport(self):
        """Reset viewport to default values"""
        self.scale_factor = 1.0
        self.offset_x = 50
        self.offset_y = 50
        self.current_zone_bounds = None
        self.current_zone_center = None

        self.logger.debug("Viewport reset to defaults")
        self.viewport_changed.emit()

    def get_viewport_info(self):
        """Get current viewport information

        Returns:
            dict: Viewport state information
        """
        return {
            'scale_factor': self.scale_factor,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'view_width': self.view_width,
            'view_height': self.view_height,
            'zone_bounds': self.current_zone_bounds,
            'zone_center': self.current_zone_center
        }

    def calculate_zone_bounds(self, zone_data):
        """Calculate bounds for a zone without setting it as current

        Args:
            zone_data (dict): Zone data containing 'points' list

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

    def calculate_zone_center(self, zone_data):
        """Calculate center point for a zone

        Args:
            zone_data (dict): Zone data containing 'points' list

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

    def is_point_visible(self, world_x, world_y, margin=0):
        """Check if a world point is visible in the current viewport

        Args:
            world_x (float): World X coordinate
            world_y (float): World Y coordinate
            margin (int): Additional margin in pixels

        Returns:
            bool: True if point is visible
        """
        screen_x, screen_y = self.world_to_screen(world_x, world_y)

        return ((-margin <= screen_x <= self.view_width + margin) and
                (-margin <= screen_y <= self.view_height + margin))

    def get_visible_world_bounds(self):
        """Get the world coordinate bounds of the current viewport

        Returns:
            tuple: (min_world_x, min_world_y, max_world_x, max_world_y)
        """
        # Convert viewport corners to world coordinates
        top_left = self.screen_to_world(0, 0)
        bottom_right = self.screen_to_world(self.view_width, self.view_height)

        return (top_left[0], top_left[1], bottom_right[0], bottom_right[1])