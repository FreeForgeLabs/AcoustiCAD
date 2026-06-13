import math
import logging


class AcousticGridManager:
    """
    Calculates acoustically-correct speaker spacing for grid snapping.

    Uses zone properties and speaker profiles to determine ideal spacing
    that ensures proper coverage and avoids phase issues.
    """

    def __init__(self, scale_manager):
        """Initialize the acoustic grid manager

        Args:
            scale_manager: The ScaleManager instance for unit conversions
        """
        self.scale_manager = scale_manager
        self.logger = logging.getLogger(__name__)

        # Current configuration
        self.current_zone = None
        self.current_profile = None
        self.calculated_spacing = None  # In feet

        # Constants
        self.MIN_SPACING_FT = 6.0  # Minimum 6 feet to avoid phase issues
        self.MAX_SPACING_FT = 50.0  # Maximum reasonable spacing

    def set_zone(self, zone):
        """Set the current zone for calculations

        Args:
            zone (dict): Zone data containing ceiling_height, listener_height, target_overlap
        """
        if zone:
            self.logger.info(
                f"Setting zone: {zone.get('name', 'unknown')} (has ceiling_height: {'ceiling_height' in zone})")
        else:
            self.logger.info("Clearing zone")

        self.current_zone = zone
        self._recalculate_spacing()

    def set_speaker_profile(self, profile):
        """Set the current speaker profile for calculations

        Args:
            profile: SpeakerProfile object with dispersion_angle_h, model_type, etc.
        """
        if profile:
            self.logger.info(f"Setting speaker profile: {profile.name}")
        else:
            self.logger.info("Clearing speaker profile")

        self.current_profile = profile
        self._recalculate_spacing()

    def get_ideal_spacing(self):
        """Get the ideal speaker spacing in feet

        Returns:
            float: Ideal spacing in feet, or None if not calculated
        """
        return self.calculated_spacing

    def get_ideal_spacing_pixels(self):
        """Get the ideal speaker spacing in pixels

        Returns:
            float: Ideal spacing in pixels, or None if not calculated
        """
        if self.calculated_spacing is None:
            return None
        return self.scale_manager.feet_to_pixels(self.calculated_spacing)

    def _recalculate_spacing(self):
        """Recalculate ideal speaker spacing based on current zone and profile"""
        # Need both zone and profile to calculate
        if not self.current_zone:
            self.calculated_spacing = None
            self.logger.info("Cannot calculate spacing: No zone set")
            return

        if not self.current_profile:
            self.calculated_spacing = None
            self.logger.info("Cannot calculate spacing: No speaker profile set")
            return

        try:
            spacing = self.calculate_ideal_speaker_spacing(
                self.current_profile,
                self.current_zone
            )

            self.calculated_spacing = spacing
            self.logger.info(
                f"Calculated ideal spacing: {spacing:.2f} ft "
                f"(zone: {self.current_zone.get('name', 'unknown')}, "
                f"profile: {self.current_profile.name})"
            )

        except Exception as e:
            self.logger.error(f"Error calculating spacing: {e}", exc_info=True)
            self.calculated_spacing = None

    def calculate_ideal_speaker_spacing(self, speaker_profile, zone):
        """
        Calculate acoustically-correct speaker spacing

        Args:
            speaker_profile: SpeakerProfile object
            zone (dict): Zone data dictionary

        Returns:
            float: Ideal spacing in feet
        """
        # 1. Determine speaker height based on type
        if speaker_profile.model_type == "In-Ceiling":
            speaker_height = zone.get('ceiling_height', 10.0)
        elif speaker_profile.model_type == "Pendant":
            # Use default mounting height from profile, or fall back to 8ft
            speaker_height = getattr(speaker_profile, 'default_mounting_height', 8.0)
        else:  # Surface Mount
            speaker_height = zone.get('ceiling_height', 10.0)

        # 2. Get listener height from zone (default 5.5 ft if not set)
        listener_height = zone.get('listener_height', 5.5)

        # 3. Calculate coverage height (distance from speaker to listener plane)
        coverage_height = speaker_height - listener_height

        # Validate coverage height
        if coverage_height <= 0:
            self.logger.warning(
                f"Invalid coverage height: {coverage_height:.2f} ft "
                f"(speaker: {speaker_height:.2f}, listener: {listener_height:.2f})"
            )
            coverage_height = 1.0  # Fallback to prevent math errors

        # 4. Get dispersion angle from profile
        dispersion_angle = speaker_profile.dispersion_angle_h

        # Validate dispersion angle
        if dispersion_angle <= 0 or dispersion_angle > 180:
            self.logger.warning(f"Invalid dispersion angle: {dispersion_angle}°, using 90°")
            dispersion_angle = 90.0

        # 5. Calculate coverage radius using trigonometry
        # radius = height × tan(angle/2)
        dispersion_radians = math.radians(dispersion_angle / 2)
        coverage_radius = coverage_height * math.tan(dispersion_radians)

        self.logger.debug(
            f"Coverage calculation: height={coverage_height:.2f}ft, "
            f"angle={dispersion_angle}°, radius={coverage_radius:.2f}ft"
        )

        # 6. Get target overlap from zone (default 15% if not set)
        target_overlap = zone.get('target_overlap', 15.0) / 100.0  # Convert percentage to decimal

        # Validate overlap
        if target_overlap < 0 or target_overlap > 0.5:
            self.logger.warning(f"Invalid overlap: {target_overlap * 100}%, using 15%")
            target_overlap = 0.15

        # 7. Calculate ideal spacing with overlap
        # spacing = 2 × radius × (1 - overlap)
        # Example: 10ft radius, 15% overlap = 2 × 10 × 0.85 = 17ft spacing
        ideal_spacing = 2 * coverage_radius * (1 - target_overlap)

        self.logger.debug(
            f"Spacing calculation: radius={coverage_radius:.2f}ft, "
            f"overlap={target_overlap * 100:.1f}%, spacing={ideal_spacing:.2f}ft"
        )

        # 8. Apply minimum spacing constraint (prevent phase issues)
        if ideal_spacing < self.MIN_SPACING_FT:
            self.logger.info(
                f"Calculated spacing {ideal_spacing:.2f}ft below minimum, "
                f"using {self.MIN_SPACING_FT}ft"
            )
            ideal_spacing = self.MIN_SPACING_FT

        # 9. Apply maximum spacing constraint (sanity check)
        if ideal_spacing > self.MAX_SPACING_FT:
            self.logger.warning(
                f"Calculated spacing {ideal_spacing:.2f}ft above maximum, "
                f"capping at {self.MAX_SPACING_FT}ft"
            )
            ideal_spacing = self.MAX_SPACING_FT

        return ideal_spacing

    def calculate_coverage_radius(self, speaker_profile, zone):
        """
        Calculate the coverage radius for a speaker

        Args:
            speaker_profile: SpeakerProfile object
            zone (dict): Zone data dictionary

        Returns:
            float: Coverage radius in feet
        """
        # Determine speaker height
        if speaker_profile.model_type == "In-Ceiling":
            speaker_height = zone.get('ceiling_height', 10.0)
        elif speaker_profile.model_type == "Pendant":
            speaker_height = getattr(speaker_profile, 'default_mounting_height', 8.0)
        else:
            speaker_height = zone.get('ceiling_height', 10.0)

        # Get listener height
        listener_height = zone.get('listener_height', 5.5)

        # Calculate coverage height
        coverage_height = max(speaker_height - listener_height, 1.0)

        # Get dispersion angle
        dispersion_angle = min(max(speaker_profile.dispersion_angle_h, 30), 180)

        # Calculate radius
        dispersion_radians = math.radians(dispersion_angle / 2)
        coverage_radius = coverage_height * math.tan(dispersion_radians)

        return coverage_radius

    def get_grid_info(self):
        """Get information about the current grid configuration

        Returns:
            dict: Grid configuration info including spacing, zone, profile
        """
        info = {
            'spacing_feet': self.calculated_spacing,
            'spacing_pixels': self.get_ideal_spacing_pixels() if self.calculated_spacing else None,
            'has_zone': self.current_zone is not None,
            'has_profile': self.current_profile is not None,
            'zone_name': self.current_zone.get('name') if self.current_zone else None,
            'profile_name': self.current_profile.name if self.current_profile else None,
        }

        if self.calculated_spacing and self.current_zone and self.current_profile:
            # Add calculation details
            coverage_radius = self.calculate_coverage_radius(
                self.current_profile,
                self.current_zone
            )

            info.update({
                'coverage_radius_feet': coverage_radius,
                'listener_height': self.current_zone.get('listener_height', 5.5),
                'target_overlap': self.current_zone.get('target_overlap', 15.0),
                'dispersion_angle': self.current_profile.dispersion_angle_h,
                'speaker_type': self.current_profile.model_type,
            })

        return info

    def validate_spacing(self, distance_feet):
        """
        Validate if a spacing distance is acoustically acceptable

        Args:
            distance_feet (float): Distance between speakers in feet

        Returns:
            tuple: (is_valid, status, message)
                is_valid (bool): True if spacing is acceptable
                status (str): 'good', 'acceptable', 'warning', or 'error'
                message (str): Description of the status
        """
        if distance_feet < self.MIN_SPACING_FT:
            return (
                False,
                'error',
                f"Too close ({distance_feet:.1f}ft) - minimum {self.MIN_SPACING_FT}ft to avoid phase issues"
            )

        if not self.calculated_spacing:
            # No ideal spacing calculated, just check minimum
            if distance_feet >= self.MIN_SPACING_FT:
                return (True, 'acceptable', f"Spacing: {distance_feet:.1f}ft")
            else:
                return (False, 'error', f"Below minimum spacing")

        # Compare to ideal spacing
        deviation = abs(distance_feet - self.calculated_spacing)
        percent_deviation = (deviation / self.calculated_spacing) * 100

        if percent_deviation < 10:
            return (True, 'good', f"Ideal spacing ({distance_feet:.1f}ft)")
        elif percent_deviation < 25:
            return (True, 'acceptable', f"Close to ideal ({distance_feet:.1f}ft, {percent_deviation:.0f}% deviation)")
        else:
            return (True, 'warning', f"Far from ideal ({distance_feet:.1f}ft vs {self.calculated_spacing:.1f}ft ideal)")

    def is_configured(self):
        """Check if manager has everything needed to calculate spacing

        Returns:
            bool: True if zone and profile are set
        """
        return self.current_zone is not None and self.current_profile is not None

    def clear(self):
        """Clear current configuration"""
        self.current_zone = None
        self.current_profile = None
        self.calculated_spacing = None
        self.logger.debug("Acoustic grid manager cleared")