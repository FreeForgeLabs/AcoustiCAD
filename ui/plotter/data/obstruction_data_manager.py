import logging
import uuid
import math
from PySide6.QtGui import QPen, QBrush, QColor


class ObstructionDataManager:
    """Manager for ceiling obstructions"""

    # Obstruction types and their properties
    OBSTRUCTION_TYPES = {
        "Column": {"color": QColor(150, 150, 150), "radius": 12.0, "icon": "column"},
        "Light": {"color": QColor(255, 255, 0, 180), "radius": 6.0, "icon": "light"},
        "HVAC": {"color": QColor(100, 100, 255, 180), "radius": 16.0, "icon": "hvac"},
        "Beam": {"color": QColor(139, 69, 19, 180), "radius": 12.0, "icon": "beam"},
        "Fire Sprinkler": {"color": QColor(220, 20, 60, 180), "radius": 3.0, "icon": "sprinkler"},
        "Other": {"color": QColor(255, 0, 0, 180), "radius": 24.0, "icon": "other"}
    }

    def __init__(self, scale_manager, parent=None):
        """Initialize the obstruction manager"""
        self.scale_manager = scale_manager
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.obstructions = {}  # Dictionary of obstruction data by ID
        self.selected_obstruction_id = None
        self.placement_mode = False
        self.obstruction_type = "Column"  # Default type
        self.current_zone_id = None
        self.current_obstruction_radius = None

        # Initialize zone-specific data structure
        self.zone_obstructions = {}  # Dictionary keyed by zone_id

        self.logger.debug("ObstructionDataManager initialized")

    def set_current_zone(self, zone_id):
        """Set the current zone"""
        if zone_id != self.current_zone_id:
            self.current_zone_id = zone_id
            self.selected_obstruction_id = None
            self.logger.debug(f"Set current zone to {zone_id}")

            # Initialize zone data if doesn't exist
            if zone_id and zone_id not in self.zone_obstructions:
                self.zone_obstructions[zone_id] = {}

            # Update current obstructions to reflect this zone's obstructions
            if zone_id:
                self.obstructions = self.zone_obstructions.get(zone_id, {})
            else:
                self.obstructions = {}

            return True
        return False

    def start_obstruction_placement(self, obstruction_type, radius_override=None):
        """Start obstruction placement mode with the specified type"""
        if obstruction_type in self.OBSTRUCTION_TYPES:
            self.obstruction_type = obstruction_type
            self.current_obstruction_radius = radius_override
            self.placement_mode = True
            self.logger.debug(f"Placement mode started: {obstruction_type}")
            return True
        else:
            self.logger.error(f"Invalid obstruction type: {obstruction_type}")
            return False

    def cancel_placement(self):
        """Cancel obstruction placement mode"""
        self.placement_mode = False
        self.logger.debug("Cancelled placement mode")

    def is_in_placement_mode(self):
        """Check if in obstruction placement mode"""
        return self.placement_mode

    def add_obstruction(self, x, y, obstruction_type=None, radius_override=None):
        """Add a new obstruction at the specified position"""
        if not self.current_zone_id:
            self.logger.warning("Cannot add obstruction: No zone selected")
            return None

        # Use current type if none specified
        if obstruction_type is None:
            obstruction_type = self.obstruction_type

        # Validate type
        if obstruction_type not in self.OBSTRUCTION_TYPES:
            self.logger.warning(f"Invalid obstruction type: {obstruction_type}")
            return None

        # Create unique ID
        obstruction_id = str(uuid.uuid4())

        # Get radius from override, stored override, or type default
        if radius_override is not None and radius_override > 0:
            radius = float(radius_override)
        elif self.current_obstruction_radius is not None and self.current_obstruction_radius > 0:
            radius = float(self.current_obstruction_radius)
        else:
            radius = self.OBSTRUCTION_TYPES[obstruction_type]["radius"]
        self.logger.debug(f"Using radius {radius} for type {obstruction_type}")

        # Create obstruction data
        obstruction_data = {
            'id': obstruction_id,
            'position': (x, y),
            'type': obstruction_type,
            'radius': radius,
            'notes': ""  # Optional notes
        }

        self.logger.debug(f"Created obstruction_data: {obstruction_data}")

        # Initialize zone_obstructions if needed
        if not hasattr(self, 'zone_obstructions'):
            self.zone_obstructions = {}

        # Add to zone's obstructions
        if self.current_zone_id not in self.zone_obstructions:
            self.zone_obstructions[self.current_zone_id] = {}

        self.zone_obstructions[self.current_zone_id][obstruction_id] = obstruction_data

        # Also add to current obstructions for easier access
        self.obstructions[obstruction_id] = obstruction_data

        self.logger.debug(f"Added {obstruction_type} obstruction at ({x}, {y}) with ID {obstruction_id}")
        self.logger.debug(f"Total obstructions in current zone: {len(self.obstructions)}")
        return obstruction_id

    def remove_obstruction(self, obstruction_id):
        """Remove an obstruction by ID"""
        if not self.current_zone_id or obstruction_id not in self.obstructions:
            return False

        # Remove from current obstructions
        if obstruction_id in self.obstructions:
            del self.obstructions[obstruction_id]

        # Remove from zone obstructions
        if self.current_zone_id in self.zone_obstructions and obstruction_id in self.zone_obstructions[
            self.current_zone_id]:
            del self.zone_obstructions[self.current_zone_id][obstruction_id]

        # Reset selection if this was selected
        if obstruction_id == self.selected_obstruction_id:
            self.selected_obstruction_id = None

        self.logger.debug(f"Removed obstruction {obstruction_id}")
        return True

    def select_obstruction(self, obstruction_id):
        """Select an obstruction by ID"""
        if obstruction_id in self.obstructions or obstruction_id is None:
            self.selected_obstruction_id = obstruction_id
            self.logger.debug(f"Selected obstruction {obstruction_id}")
            return True
        return False

    def get_selected_obstruction(self):
        """Get the currently selected obstruction"""
        if self.selected_obstruction_id:
            return self.obstructions.get(self.selected_obstruction_id)
        return None

    def update_obstruction(self, obstruction_id, key, value):
        """Update an obstruction property"""
        if obstruction_id not in self.obstructions:
            return False

        self.obstructions[obstruction_id][key] = value

        # Also update in zone obstructions
        if self.current_zone_id in self.zone_obstructions and obstruction_id in self.zone_obstructions[
            self.current_zone_id]:
            self.zone_obstructions[self.current_zone_id][obstruction_id][key] = value

        self.logger.debug(f"Updated obstruction {obstruction_id} {key}={value}")
        return True

    def get_obstructions_for_zone(self, zone_id):
        """Get all obstructions for a specific zone"""
        return self.zone_obstructions.get(zone_id, {})

    def load_obstructions(self, obstruction_data):
        """Load obstruction data for all zones"""
        if not obstruction_data:
            return False

        self.zone_obstructions = obstruction_data

        # Load current zone's obstructions
        if self.current_zone_id and self.current_zone_id in self.zone_obstructions:
            self.obstructions = self.zone_obstructions[self.current_zone_id]
        else:
            self.obstructions = {}

        self.selected_obstruction_id = None
        self.logger.debug(f"Loaded obstructions for {len(self.zone_obstructions)} zones")
        return True

    def draw_obstructions(self, painter, selected_only=False, scale_factor=1.0):
        """Draw obstructions on the canvas"""
        if not self.obstructions:
            return

        # Save painter state
        painter.save()

        # Draw each obstruction
        for obstruction_id, obstruction in self.obstructions.items():
            # Skip if not the selected one when drawing selected only
            if selected_only and obstruction_id != self.selected_obstruction_id:
                continue

            self._draw_obstruction(painter, obstruction_id, obstruction, scale_factor)

        # Restore painter state
        painter.restore()

    def _draw_obstruction(self, painter, obstruction_id, obstruction, view_scale_factor=1.0):
        """Draw a single obstruction"""
        x, y = obstruction['position']
        obstruction_type = obstruction['type']

        # Get radius in inches from the obstruction or default
        radius_inches = obstruction.get('radius', self.OBSTRUCTION_TYPES[obstruction_type]['radius'])

        # Convert inches to feet (real-world scale)
        radius_feet = radius_inches / 12.0

        # Convert feet to pixels using scale manager
        base_pixels = radius_feet * self.scale_manager.get_scale_factor()

        # FIXED: Painter is already transformed by the viewport - use base pixels directly
        radius_pixels = base_pixels

        # Log for debugging
        self.logger.debug(f"Drawing obstruction {obstruction_id}: {radius_inches}in → {radius_pixels}px")
        self.logger.debug(f"Scale factor: {self.scale_manager.get_scale_factor()}")

        # Set colors based on type and selection
        if obstruction_id == self.selected_obstruction_id:
            # Selected obstruction
            color = QColor(255, 140, 0)  # Orange highlight
            pen_width = 1  # Thinner line when scaled
        else:
            # Normal obstruction
            color = self.OBSTRUCTION_TYPES.get(obstruction_type, {}).get('color', QColor(0, 0, 0))
            pen_width = 1  # Thinner line when scaled

        # Draw obstruction
        pen = QPen(color)
        pen.setWidth(pen_width)
        painter.setPen(pen)

        # Fill color
        fill_color = QColor(color)
        fill_color.setAlpha(180)
        painter.setBrush(QBrush(fill_color))

        # Convert x and y to integers for drawing functions
        ix, iy = int(x), int(y)
        iradius = int(radius_pixels)

        # Draw circle for the obstruction
        painter.drawEllipse(ix - iradius, iy - iradius, iradius * 2, iradius * 2)

        # Draw different icons based on type
        if obstruction_type == "Column":
            # Draw a plus inside
            painter.drawLine(int(ix - iradius / 2), int(iy), int(ix + iradius / 2), int(iy))
            painter.drawLine(int(ix), int(iy - iradius / 2), int(ix), int(iy + iradius / 2))
        elif obstruction_type == "Light":
            # Draw light rays
            painter.drawLine(int(ix - iradius / 2), int(iy - iradius / 2), int(ix + iradius / 2), int(iy + iradius / 2))
            painter.drawLine(int(ix - iradius / 2), int(iy + iradius / 2), int(ix + iradius / 2), int(iy - iradius / 2))
        elif obstruction_type == "HVAC":
            # Draw H
            painter.drawLine(int(ix - iradius / 2), int(iy - iradius / 3), int(ix - iradius / 2), int(iy + iradius / 3))
            painter.drawLine(int(ix - iradius / 2), int(iy), int(ix + iradius / 2), int(iy))
            painter.drawLine(int(ix + iradius / 2), int(iy - iradius / 3), int(ix + iradius / 2), int(iy + iradius / 3))
        elif obstruction_type == "Beam":
            # Draw a horizontal line
            painter.drawLine(int(ix - iradius), int(iy), int(ix + iradius), int(iy))
        else:  # Other or Fire Sprinkler
            # Draw X
            painter.drawLine(int(ix - iradius / 2), int(iy - iradius / 2), int(ix + iradius / 2), int(iy + iradius / 2))
            painter.drawLine(int(ix - iradius / 2), int(iy + iradius / 2), int(ix + iradius / 2), int(iy - iradius / 2))

    def check_collision(self, x, y, radius_inches=0):
        """Check if there's a collision between position (x,y) and any obstruction"""
        for obstruction_id, obstruction in self.obstructions.items():
            obs_x, obs_y = obstruction['position']

            # Get obstruction radius in inches
            obs_radius_inches = obstruction.get('radius',
                                                self.OBSTRUCTION_TYPES[obstruction['type']]['radius'])

            # Convert radii from inches to pixels using scale manager
            # Convert inches to feet
            radius_feet = radius_inches / 12.0
            obs_radius_feet = obs_radius_inches / 12.0

            # Convert feet to pixels using scale factor
            radius_pixels = radius_feet * self.scale_manager.get_scale_factor()
            obs_radius_pixels = obs_radius_feet * self.scale_manager.get_scale_factor()

            # Calculate distance and check for collision
            distance = math.sqrt((x - obs_x) ** 2 + (y - obs_y) ** 2)
            if distance < (radius_pixels + obs_radius_pixels):
                return True

        return False

    def check_speaker_placement(self, x, y, speaker_radius=1, min_speaker_distance=None):
        """
        Check if a speaker can be placed at a position

        Args:
            x (float): X position
            y (float): Y position
            speaker_radius (float): Radius of the speaker in inches
            min_speaker_distance (float): Minimum distance between speakers in inches (optional)

        Returns:
            tuple: (can_place, reason) - Boolean and reason string if can't place
        """
        # Debug logging
        self.logger.debug(f"Checking placement at ({x}, {y}) with radius {speaker_radius} in")

        # Check collision with obstructions
        if self.check_collision(x, y, speaker_radius):
            self.logger.debug("Failed: Collision with obstruction")
            return False, "Collision with obstruction"

        # Check distance to other speakers if enabled
        if min_speaker_distance is not None and self.parent and hasattr(self.parent, 'speakers'):
            # Convert min distance to pixels using scale manager
            min_distance_feet = min_speaker_distance / 12.0
            min_distance_px = min_distance_feet * self.scale_manager.get_scale_factor()

            for speaker_id, speaker in self.parent.speakers.items():
                speaker_x, speaker_y = speaker['position']

                # Calculate distance between points
                distance = math.sqrt((x - speaker_x) ** 2 + (y - speaker_y) ** 2)

                # Check if distance is less than minimum
                if distance < min_distance_px and distance > 0.1:  # Add small threshold
                    self.logger.debug(
                        f"Failed: Too close to speaker {speaker_id} ({distance} < {min_distance_px})")
                    return False, "Too close to another speaker"

        return True, ""

    def get_nearest_obstruction(self, x, y, max_distance=None):
        """
        Find the nearest obstruction to a point

        Args:
            x (float): X position
            y (float): Y position
            max_distance (float): Maximum distance to consider

        Returns:
            str: ID of nearest obstruction or None
        """
        nearest_id = None
        nearest_distance = float('inf')

        for obstruction_id, obstruction in self.obstructions.items():
            obs_x, obs_y = obstruction['position']

            # Calculate distance
            distance = math.sqrt((x - obs_x) ** 2 + (y - obs_y) ** 2)

            # Check if this is closer
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_id = obstruction_id

        # Return None if no obstruction within max_distance
        if max_distance is not None and nearest_distance > max_distance:
            return None

        return nearest_id