import logging
from PySide6.QtCore import QObject, Signal, Qt


class PlacementManager(QObject):
    """Handles speaker and obstruction placement logic"""

    # Signals
    placement_mode_changed = Signal(bool, str)  # enabled, mode_type
    cursor_change_requested = Signal(object)  # Qt cursor
    status_message = Signal(str)  # Status message
    speaker_placed = Signal(str)  # speaker_id
    obstruction_placed = Signal(str)  # obstruction_id

    def __init__(self, parent_view):
        """Initialize the placement manager

        Args:
            parent_view: The parent SpeakerView instance
        """
        super().__init__(parent_view)
        self.view = parent_view
        self.logger = logging.getLogger(__name__)

        # Placement state
        self.speaker_placement_active = False
        self.obstruction_placement_active = False
        self.current_speaker_profile = None
        self.current_obstruction_type = "Column"
        self.current_obstruction_radius_override = None

        # Grid snapping state
        self.bypass_grid_snap = False  # Set to True when Shift key is held

    def set_bypass_grid_snap(self, bypass):
        """Set grid snap bypass state (e.g., when Shift key is held)

        Args:
            bypass (bool): Whether to bypass grid snapping
        """
        self.bypass_grid_snap = bypass

        # Update grid snapper if available
        if hasattr(self.view, 'grid_snapper') and self.view.grid_snapper:
            self.view.grid_snapper.set_bypass(bypass)

    def start_speaker_placement(self, profile):
        """Start speaker placement mode with the specified profile

        Args:
            profile: SpeakerProfile object containing speaker specifications
        """
        if not profile:
            self.logger.warning("Cannot start placement: No profile provided")
            return False

        # Validate zone availability
        if not self._validate_zone_for_placement():
            return False

        # Set the profile in data manager
        self.view.speaker_data_manager.set_speaker_profile(profile)

        # Update placement state
        self.current_speaker_profile = profile
        self.speaker_placement_active = True
        self.obstruction_placement_active = False

        # Update UI
        self.cursor_change_requested.emit(Qt.CrossCursor)
        self.status_message.emit("Click to place speaker")
        self.placement_mode_changed.emit(True, "speaker")

        self.logger.debug(f"Started speaker placement mode with profile: {profile.name}")
        return True

    def start_obstruction_placement(self, obstruction_type, radius_override=None):
        """Start obstruction placement mode with the specified type

        Args:
            obstruction_type (str): Type of obstruction to place
            radius_override (float, optional): Radius in inches to override the type default
        """
        # Validate zone availability
        if not self._validate_zone_for_placement():
            return False

        # Validate obstruction type
        if not self._validate_obstruction_type(obstruction_type):
            return False

        # Set zone in obstruction manager
        zone_id = str(self.view.current_zone['id'])
        self.view.obstruction_manager.set_current_zone(zone_id)

        # Update placement state
        self.current_obstruction_type = obstruction_type
        self.current_obstruction_radius_override = radius_override
        self.obstruction_placement_active = True
        self.speaker_placement_active = False

        # Update UI
        self.cursor_change_requested.emit(Qt.CrossCursor)
        self.status_message.emit(f"Click to place {obstruction_type}")
        self.placement_mode_changed.emit(True, "obstruction")

        self.logger.debug(f"Started obstruction placement mode: {obstruction_type}")
        return True

    def cancel_placement(self):
        """Cancel any active placement mode"""
        self.speaker_placement_active = False
        self.obstruction_placement_active = False

        # Reset UI
        self.cursor_change_requested.emit(Qt.ArrowCursor)
        self.status_message.emit("Placement cancelled")
        self.placement_mode_changed.emit(False, "none")

        self.logger.debug("Cancelled placement mode")

    def handle_placement_click(self, world_x, world_y):
        """Handle a placement click at world coordinates

        Args:
            world_x, world_y: World coordinates of the click (in feet)

        Returns:
            bool: True if placement was handled, False otherwise
        """
        # APPLY GRID SNAPPING HERE
        snapped_x, snapped_y = self._apply_grid_snapping(world_x, world_y)

        if self.speaker_placement_active:
            return self._handle_speaker_placement_click(snapped_x, snapped_y)
        elif self.obstruction_placement_active:
            return self._handle_obstruction_placement_click(snapped_x, snapped_y)
        return False

    def _apply_grid_snapping(self, x_feet, y_feet):
        """Apply grid snapping to coordinates if enabled

        Args:
            x_feet, y_feet: Coordinates in feet (world coordinates)

        Returns:
            tuple: (snapped_x, snapped_y) in feet
        """
        # Check if grid snapper is available
        if not hasattr(self.view, 'grid_snapper') or not self.view.grid_snapper:
            return (x_feet, y_feet)

        # Apply snapping (grid snapper handles enabled/bypass state internally)
        snapped_x, snapped_y = self.view.grid_snapper.snap_to_grid(x_feet, y_feet)

        # Log if snapping occurred
        if abs(snapped_x - x_feet) > 0.01 or abs(snapped_y - y_feet) > 0.01:
            self.logger.debug(
                f"Grid snap: ({x_feet:.2f}, {y_feet:.2f}) → "
                f"({snapped_x:.2f}, {snapped_y:.2f})"
            )

        return (snapped_x, snapped_y)

    def _handle_speaker_placement_click(self, world_x, world_y):
        """Handle speaker placement click"""
        # Validate position within zone
        if not self._validate_position_in_zone(world_x, world_y):
            self.status_message.emit("Cannot place speaker outside zone")
            return False

        # Check for collision with obstructions
        if not self._validate_speaker_position(world_x, world_y):
            return False

        # Add speaker via data manager (snapshot first so placement is undoable)
        zone_id = str(self.view.current_zone['id'])
        self.view.speaker_data_manager.push_undo_snapshot()
        speaker_id = self.view.speaker_data_manager.add_speaker(world_x, world_y, zone_id)

        if speaker_id:
            self.speaker_placed.emit(speaker_id)
            self.status_message.emit("Speaker placed successfully")

            # Exit placement mode
            self.cancel_placement()

            self.logger.debug(f"Placed speaker {speaker_id} at ({world_x}, {world_y})")
            return True
        else:
            self.status_message.emit("Failed to place speaker")
            return False

    def _handle_obstruction_placement_click(self, world_x, world_y):
        """Handle obstruction placement click"""
        # Validate position within zone
        if not self._validate_position_in_zone(world_x, world_y):
            self.status_message.emit("Cannot place obstruction outside zone")
            return False

        # Add obstruction via obstruction manager
        obstruction_id = self.view.obstruction_manager.add_obstruction(
            world_x, world_y, self.current_obstruction_type,
            radius_override=self.current_obstruction_radius_override)

        if obstruction_id:
            self.obstruction_placed.emit(obstruction_id)
            self.status_message.emit("Obstruction placed successfully")

            # Exit placement mode
            self.cancel_placement()

            self.logger.debug(f"Placed {self.current_obstruction_type} at ({world_x}, {world_y})")
            return True
        else:
            self.status_message.emit("Failed to place obstruction")
            return False

    def _validate_zone_for_placement(self):
        """Validate that a zone is available for placement"""
        if not self.view.current_zone:
            self.status_message.emit("No zone selected")
            self.logger.warning("Cannot place: No zone selected")
            return False

        if 'id' not in self.view.current_zone:
            self.status_message.emit("Invalid zone selected")
            self.logger.warning("Cannot place: Zone has no ID")
            return False

        return True

    def _validate_obstruction_type(self, obstruction_type):
        """Validate obstruction type"""
        valid_types = self.view.obstruction_manager.OBSTRUCTION_TYPES
        if obstruction_type not in valid_types:
            self.status_message.emit(f"Invalid obstruction type: {obstruction_type}")
            self.logger.warning(f"Invalid obstruction type: {obstruction_type}")
            return False
        return True

    def _validate_position_in_zone(self, x, y):
        """Validate that position is within current zone"""
        if not self.view.current_zone or 'points' not in self.view.current_zone:
            return False

        points = self.view.current_zone['points']
        if not points:
            return False

        from core.zones.geometry_utils import point_inside_polygon
        return point_inside_polygon((x, y), points)

    def _validate_speaker_position(self, x, y):
        """Validate speaker position against obstructions and spacing"""
        # Check collision with obstructions
        speaker_radius = 1.0  # Default speaker radius in inches
        min_distance = getattr(self.view, 'min_speaker_distance', None)

        can_place, reason = self.view.obstruction_manager.check_speaker_placement(
            x, y, speaker_radius, min_distance)

        if not can_place:
            self.status_message.emit(f"Cannot place speaker: {reason}")
            self.logger.debug(f"Speaker placement blocked: {reason}")
            return False

        return True

    def is_placement_active(self):
        """Check if any placement mode is active"""
        return self.speaker_placement_active or self.obstruction_placement_active

    def get_placement_mode(self):
        """Get current placement mode"""
        if self.speaker_placement_active:
            return "speaker"
        elif self.obstruction_placement_active:
            return "obstruction"
        return "none"

    def get_current_profile(self):
        """Get current speaker profile"""
        return self.current_speaker_profile

    def get_current_obstruction_type(self):
        """Get current obstruction type"""
        return self.current_obstruction_type

    def set_obstruction_type(self, obstruction_type):
        """Set the obstruction type for placement"""
        if self._validate_obstruction_type(obstruction_type):
            self.current_obstruction_type = obstruction_type
            return True
        return False