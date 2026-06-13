import math
import logging


class ScaleManager:
    """Manages scale conversion for the project - centralized and project-manager friendly"""

    # Sentinel value meaning "not yet calibrated by the user"
    DEFAULT_SCALE = 12.0  # 12 pixels = 1 foot (1 pixel = 1 inch)

    def __init__(self, on_scale_changed_callback=None):
        self.scale_factor = ScaleManager.DEFAULT_SCALE
        self.calibration_points = []
        self.calibration_mode = False
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"ScaleManager initialized with default scale factor: {ScaleManager.DEFAULT_SCALE}")

        # Store the callback instead of project manager reference
        self.on_scale_changed_callback = on_scale_changed_callback

    def _notify_scale_changed(self):
        """Notify callback that scale has changed due to USER action"""
        if self.on_scale_changed_callback:
            try:
                self.on_scale_changed_callback()
            except Exception as e:
                self.logger.error(f"Error in scale change callback: {e}")

    def set_scale_factor(self, factor):
        """Set scale factor due to USER action - triggers modification callback"""
        try:
            if factor <= 0:
                self.logger.warning(f"Invalid scale factor: {factor}, must be positive")
                return False

            old_factor = self.scale_factor
            self.scale_factor = factor
            self.logger.info(f"Scale factor changed by user: {old_factor} → {factor} pixels per foot")

            # Notify callback of USER-initiated scale change
            self._notify_scale_changed()
            return True

        except Exception as e:
            self.logger.error(f"Error setting scale factor: {e}", exc_info=True)
            return False

    def _set_scale_factor_internal(self, factor):
        """Set scale factor for internal/system use - does NOT trigger modification callback"""
        try:
            if factor <= 0:
                self.logger.warning(f"Invalid scale factor: {factor}, must be positive")
                return False

            self.scale_factor = factor
            self.logger.debug(f"Scale factor set internally: {factor} pixels per foot")
            return True

        except Exception as e:
            self.logger.error(f"Error setting scale factor internally: {e}", exc_info=True)
            return False

    def get_scale_factor(self):
        return self.scale_factor

    def start_calibration(self):
        try:
            self.calibration_mode = True
            self.calibration_points = []
            self.logger.info("Scale calibration started")
            return True

        except Exception as e:
            self.logger.error(f"Error starting calibration: {e}", exc_info=True)
            return False

    def add_calibration_point(self, x, y):
        try:
            # Validate coordinates
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                self.logger.warning(f"Invalid calibration point coordinates: ({x}, {y})")
                return False

            self.calibration_points.append((x, y))
            self.logger.debug(f"Added calibration point: ({x}, {y}), total points: {len(self.calibration_points)}")

            # If we have two points, we're ready to calculate
            if len(self.calibration_points) == 2:
                self.logger.info("Two calibration points collected, ready for real-world measurement")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error adding calibration point: {e}", exc_info=True)
            return False

    def calculate_scale_from_calibration(self, real_length):
        """
        Calculate scale factor from calibration points and real-world length - USER action

        Args:
            real_length (float): The real-world length between the calibration points in feet

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if len(self.calibration_points) != 2:
                self.logger.warning("Need exactly 2 calibration points")
                return False

            if real_length <= 0:
                self.logger.warning(f"Invalid real length: {real_length}, must be positive")
                return False

            # Calculate distance in pixels
            p1, p2 = self.calibration_points
            pixel_distance = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

            if pixel_distance <= 0:
                self.logger.warning("Calibration points are too close together")
                return False

            # Calculate scale factor (pixels per foot)
            old_factor = self.scale_factor
            self.scale_factor = pixel_distance / real_length
            self.logger.info(f"Calibration complete: {pixel_distance:.2f} pixels = {real_length:.2f} feet")
            self.logger.info(f"New scale factor: {self.scale_factor:.2f} pixels per foot (was {old_factor:.2f})")

            # Reset calibration
            self.calibration_mode = False
            self.calibration_points = []

            # Notify callback that scale has changed due to USER calibration
            self._notify_scale_changed()
            return True

        except Exception as e:
            self.logger.error(f"Error calculating scale from calibration: {e}", exc_info=True)
            # Reset calibration even on error
            self.calibration_mode = False
            self.calibration_points = []
            return False

    def is_calibrated(self):
        """Return True if the scale has been calibrated (not using the default sentinel)."""
        return self.scale_factor != ScaleManager.DEFAULT_SCALE

    def reset_to_default(self):
        """Reset scale to the uncalibrated default — system operation, no modification callback."""
        self._set_scale_factor_internal(ScaleManager.DEFAULT_SCALE)

    def is_calibrating(self):
        return self.calibration_mode

    def cancel_calibration(self):
        try:
            was_calibrating = self.calibration_mode
            self.calibration_mode = False
            self.calibration_points = []

            if was_calibrating:
                self.logger.info("Calibration cancelled")

            return True

        except Exception as e:
            self.logger.error(f"Error cancelling calibration: {e}", exc_info=True)
            # Try to reset state even on error
            self.calibration_mode = False
            self.calibration_points = []
            return False

    def pixels_to_feet(self, pixels):
        try:
            if self.scale_factor <= 0:
                self.logger.warning("Invalid scale factor for conversion")
                return 0

            feet = pixels / self.scale_factor
            self.logger.debug(f"Converted: {pixels:.2f} pixels → {feet:.2f} feet")
            return feet

        except Exception as e:
            self.logger.error(f"Error converting pixels to feet: {e}", exc_info=True)
            return 0

    def feet_to_pixels(self, feet):
        try:
            pixels = feet * self.scale_factor
            self.logger.debug(f"Converted: {feet:.2f} feet → {pixels:.2f} pixels")
            return pixels

        except Exception as e:
            self.logger.error(f"Error converting feet to pixels: {e}", exc_info=True)
            return 0

    def square_pixels_to_square_feet(self, square_pixels):
        try:
            if self.scale_factor <= 0:
                self.logger.warning("Invalid scale factor for area conversion")
                return 0

            square_feet = square_pixels / (self.scale_factor * self.scale_factor)
            self.logger.debug(f"Converted area: {square_pixels:.2f} sq.px → {square_feet:.2f} sq.ft")
            return square_feet

        except Exception as e:
            self.logger.error(f"Error converting square pixels to square feet: {e}", exc_info=True)
            return 0

    def square_feet_to_square_pixels(self, square_feet):
        try:
            square_pixels = square_feet * (self.scale_factor * self.scale_factor)
            self.logger.debug(f"Converted area: {square_feet:.2f} sq.ft → {square_pixels:.2f} sq.px")
            return square_pixels

        except Exception as e:
            self.logger.error(f"Error converting square feet to square pixels: {e}", exc_info=True)
            return 0

    def get_calibration_distance_pixels(self):
        try:
            if len(self.calibration_points) != 2:
                return 0

            p1, p2 = self.calibration_points
            return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

        except Exception as e:
            self.logger.error(f"Error getting calibration distance: {e}", exc_info=True)
            return 0

    def load_scale_data(self, scale_data):
        """Load scale data from project data - SYSTEM operation, does not trigger callbacks"""
        if not scale_data:
            return False

        try:
            # Use internal method that doesn't trigger callbacks
            scale_factor = scale_data.get('scale_factor', ScaleManager.DEFAULT_SCALE)
            success = self._set_scale_factor_internal(scale_factor)

            if success:
                self.logger.debug(f"Loaded scale factor from project data: {scale_factor}")

            return success
        except Exception as e:
            self.logger.error(f"Error loading scale data: {e}")
            return False

    def get_scale_data(self):
        """Get scale data for saving to project"""
        return {
            'scale_factor': self.scale_factor
        }

    def inches_to_pixels(self, inches):
        """Convert inches to pixels using the scale manager"""
        if inches <= 0:
            self.logger.warning(f"Invalid inches value: {inches}")
            return 1  # Return minimum value

        # Convert inches to feet and then to pixels
        feet = inches / 12.0
        pixels = feet * self.scale_factor

        self.logger.debug(f"Converting {inches} inches to {pixels:.2f} pixels (scale factor: {self.scale_factor})")
        return pixels