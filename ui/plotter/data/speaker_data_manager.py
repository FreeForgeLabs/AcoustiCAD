import copy
import logging
import uuid
from PySide6.QtCore import QObject, Signal


class SpeakerDataManager(QObject):
    """Manages speaker data operations, layout loading/saving, and persistence"""

    # Signals
    speaker_added = Signal(str, dict)  # speaker_id, speaker_data
    speaker_removed = Signal(str)  # speaker_id
    speaker_updated = Signal(str, str, object)  # speaker_id, property, value
    speakers_cleared = Signal()
    layout_loaded = Signal(dict)  # layout_data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Speaker data storage
        self.layout_data = {}  # Dictionary by zone_id containing speaker dictionaries
        self.current_zone_id = None
        self.current_speakers = {}  # Active speakers for current zone

        # Speaker profile and properties for new speakers
        self.current_profile = None
        self.speaker_properties = {}
        self.default_speaker_type = "In-Ceiling"
        self.default_dispersion_angle = 90

        # Zone-level pendant height default (set when zone is selected)
        self.zone_pendant_height = 9.0

        # Undo / redo stacks — each entry is a deepcopy of current_speakers
        self._undo_stack = []
        self._redo_stack = []
        self._MAX_UNDO = 30

    # ── Undo / Redo ──────────────────────────────────────────────────────

    def push_undo_snapshot(self):
        """Save the current speaker state so it can be restored with undo().
        Call this BEFORE any mutating operation (place, delete, clear).
        """
        self._undo_stack.append(copy.deepcopy(self.current_speakers))
        if len(self._undo_stack) > self._MAX_UNDO:
            self._undo_stack.pop(0)
        self._redo_stack.clear()   # new action invalidates the redo history

    def undo(self):
        """Restore the previous speaker state. Returns True if successful."""
        if not self._undo_stack:
            return False
        self._redo_stack.append(copy.deepcopy(self.current_speakers))
        self._restore_snapshot(self._undo_stack.pop())
        return True

    def redo(self):
        """Re-apply the most recently undone action. Returns True if successful."""
        if not self._redo_stack:
            return False
        self._undo_stack.append(copy.deepcopy(self.current_speakers))
        self._restore_snapshot(self._redo_stack.pop())
        return True

    def _restore_snapshot(self, snapshot):
        """Replace current speakers with snapshot and refresh the view via signals."""
        self.current_speakers = snapshot
        if self.current_zone_id:
            self.layout_data[self.current_zone_id] = copy.deepcopy(snapshot)
        # Notify view: clear first, then re-add each restored speaker
        self.speakers_cleared.emit()
        for speaker_id, speaker_data in snapshot.items():
            self.speaker_added.emit(speaker_id, speaker_data)

    def clear_undo_history(self):
        """Discard all undo/redo history (e.g. when switching zones)."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    def can_undo(self):
        return bool(self._undo_stack)

    def can_redo(self):
        return bool(self._redo_stack)

    # ─────────────────────────────────────────────────────────────────────

    def set_current_zone(self, zone_id):
        """Set the current active zone

        Args:
            zone_id (str): Zone ID to set as current

        Returns:
            bool: True if zone changed, False if same zone
        """
        if zone_id == self.current_zone_id:
            return False

        # Store current speakers back to layout data
        if self.current_zone_id and self.current_speakers:
            self.layout_data[self.current_zone_id] = self.current_speakers.copy()

        # Update current zone — undo history is zone-specific, clear it
        self.current_zone_id = zone_id
        self.clear_undo_history()

        # Load speakers for new zone
        if zone_id and zone_id in self.layout_data:
            self.current_speakers = self.layout_data[zone_id].copy()
        else:
            self.current_speakers = {}
            # Initialize empty zone data
            if zone_id:
                self.layout_data[zone_id] = {}

        self.logger.debug(f"Set current zone to {zone_id}, loaded {len(self.current_speakers)} speakers")
        return True

    def set_zone_pendant_height(self, height: float):
        """Update the pendant height default for the current zone.

        Called whenever a zone is selected so that newly placed pendant speakers
        inherit the correct mounting height instead of a hardcoded fallback.
        """
        self.zone_pendant_height = max(4.0, float(height))

    def add_speaker(self, x, y, zone_id=None):
        """Add a new speaker at the specified position

        Args:
            x (float): X coordinate in world units
            y (float): Y coordinate in world units
            zone_id (str, optional): Zone ID, uses current zone if not specified

        Returns:
            str: Speaker ID if successful, None if failed
        """
        # Use current zone if not specified
        if zone_id is None:
            zone_id = self.current_zone_id

        if not zone_id:
            self.logger.warning("Cannot add speaker: No zone specified or current")
            return None

        # Generate unique speaker ID
        speaker_id = str(uuid.uuid4())

        # Create speaker data with current profile/settings
        speaker_data = {
            'id': speaker_id,
            'position': (x, y),
            'type': self.default_speaker_type,
            'dispersion_angle': self.default_dispersion_angle
        }

        # Add properties from current profile if available
        if self.speaker_properties:
            for key, value in self.speaker_properties.items():
                if key not in speaker_data:
                    speaker_data[key] = value

        # Stamp zone pendant height onto pendant speakers that don't have a mounting_height yet
        if speaker_data.get('type') == 'Pendant' and 'mounting_height' not in speaker_data:
            speaker_data['mounting_height'] = self.zone_pendant_height

        # Add speaker diameter from profile if available
        if self.current_profile:
            speaker_data['diameter'] = getattr(self.current_profile, 'diameter', 6.0)

        # Add to current speakers
        self.current_speakers[speaker_id] = speaker_data

        # Update layout data
        if zone_id not in self.layout_data:
            self.layout_data[zone_id] = {}
        self.layout_data[zone_id][speaker_id] = speaker_data

        self.logger.debug(f"Added speaker {speaker_id} at ({x}, {y}) in zone {zone_id}")

        # Emit signal
        self.speaker_added.emit(speaker_id, speaker_data)

        return speaker_id

    def remove_speaker(self, speaker_id):
        """Remove a speaker by ID

        Args:
            speaker_id (str): Speaker ID to remove

        Returns:
            bool: True if removed, False if not found
        """
        if speaker_id not in self.current_speakers:
            return False

        # Remove from current speakers
        del self.current_speakers[speaker_id]

        # Remove from layout data
        if self.current_zone_id and self.current_zone_id in self.layout_data:
            if speaker_id in self.layout_data[self.current_zone_id]:
                del self.layout_data[self.current_zone_id][speaker_id]

        self.logger.debug(f"Removed speaker {speaker_id}")

        # Emit signal
        self.speaker_removed.emit(speaker_id)

        return True

    def update_speaker(self, speaker_id, property_name, value):
        """Update a speaker property

        Args:
            speaker_id (str): Speaker ID
            property_name (str): Property name to update
            value: New property value

        Returns:
            bool: True if updated, False if speaker not found
        """
        if speaker_id not in self.current_speakers:
            return False

        # Update in current speakers
        self.current_speakers[speaker_id][property_name] = value

        # Update in layout data
        if (self.current_zone_id and
                self.current_zone_id in self.layout_data and
                speaker_id in self.layout_data[self.current_zone_id]):
            self.layout_data[self.current_zone_id][speaker_id][property_name] = value

        self.logger.debug(f"Updated speaker {speaker_id}: {property_name} = {value}")

        # Emit signal
        self.speaker_updated.emit(speaker_id, property_name, value)

        return True

    def get_speaker(self, speaker_id):
        """Get speaker data by ID

        Args:
            speaker_id (str): Speaker ID

        Returns:
            dict: Speaker data or None if not found
        """
        return self.current_speakers.get(speaker_id)

    def get_all_speakers(self):
        """Get all speakers in current zone

        Returns:
            dict: Dictionary of speaker data by speaker_id
        """
        return self.current_speakers.copy()

    def clear_speakers(self, zone_id=None):
        """Clear all speakers from specified zone or current zone

        Args:
            zone_id (str, optional): Zone to clear, uses current if not specified

        Returns:
            int: Number of speakers cleared
        """
        if zone_id is None:
            zone_id = self.current_zone_id

        if not zone_id:
            return 0

        # Count speakers being cleared
        if zone_id == self.current_zone_id:
            count = len(self.current_speakers)
            self.current_speakers.clear()
        else:
            count = len(self.layout_data.get(zone_id, {}))

        # Clear from layout data
        if zone_id in self.layout_data:
            self.layout_data[zone_id].clear()

        self.logger.debug(f"Cleared {count} speakers from zone {zone_id}")

        # Emit signal
        self.speakers_cleared.emit()

        return count

    def load_speaker_layout(self, layout_data):
        """Load complete speaker layout data

        Args:
            layout_data (dict): Layout data dictionary by zone_id

        Returns:
            bool: True if loaded successfully
        """
        if not layout_data:
            self.logger.debug("No layout data to load")
            return False

        # Store layout data
        self.layout_data = layout_data.copy()

        # Reload current zone's speakers if we have a current zone
        if self.current_zone_id and self.current_zone_id in self.layout_data:
            self.current_speakers = self.layout_data[self.current_zone_id].copy()
        else:
            self.current_speakers = {}

        self.logger.debug(f"Loaded speaker layout for {len(self.layout_data)} zones")

        # Emit signal
        self.layout_loaded.emit(layout_data)

        return True

    def get_layout_data(self):
        """Get complete layout data for all zones

        Returns:
            dict: Complete layout data by zone_id
        """
        # Make sure current zone data is saved
        if self.current_zone_id and self.current_speakers:
            self.layout_data[self.current_zone_id] = self.current_speakers.copy()

        return self.layout_data.copy()

    def get_zone_speakers(self, zone_id):
        """Get speakers for a specific zone

        Args:
            zone_id (str): Zone ID

        Returns:
            dict: Speaker data for the zone
        """
        if zone_id == self.current_zone_id:
            return self.current_speakers.copy()
        else:
            return self.layout_data.get(zone_id, {}).copy()

    def set_speaker_profile(self, profile):
        """Set the current speaker profile for new speakers

        Args:
            profile: SpeakerProfile object
        """
        if not profile:
            return

        self.logger.debug(f"Setting speaker profile: {profile.name}")

        # Store profile
        self.current_profile = profile

        # Update default settings
        self.default_speaker_type = profile.model_type
        self.default_dispersion_angle = profile.dispersion_angle_h

        # Store properties for new speakers
        self.speaker_properties = {
            'type': profile.model_type,
            'dispersion_angle_h': profile.dispersion_angle_h,
            'dispersion_angle_v': profile.dispersion_angle_v,
            'sensitivity': profile.sensitivity,
            'power': profile.power_taps[0] if profile.power_taps else 15,
            'power_taps': profile.power_taps,
            'manufacturer': profile.manufacturer,
            'name': profile.name
        }

        # Add diameter (both In-Ceiling and Pendant use circular drivers)
        self.speaker_properties['diameter'] = profile.diameter

    def update_all_speaker_dispersion(self, angle, exclude_speaker_id=None):
        """Update dispersion angle for all speakers except specified one

        Args:
            angle (float): New dispersion angle
            exclude_speaker_id (str, optional): Speaker ID to exclude from update
        """
        updated_count = 0

        for speaker_id in self.current_speakers:
            if speaker_id != exclude_speaker_id:
                self.update_speaker(speaker_id, 'dispersion_angle', angle)
                updated_count += 1

        self.logger.debug(f"Updated dispersion angle to {angle} for {updated_count} speakers")

    def export_speaker_data(self, zone_data=None):
        """Export speaker data in a format suitable for reports

        Args:
            zone_data (dict, optional): Zone information

        Returns:
            dict: Formatted speaker data or None if no current zone
        """
        if not self.current_zone_id:
            return None

        # Create result structure
        result = {
            "zone_id": self.current_zone_id,
            "zone_name": zone_data.get('name', 'Unnamed Zone') if zone_data else 'Unnamed Zone',
            "speakers": []
        }

        # Add speakers with formatted positions
        for speaker_id, speaker in self.current_speakers.items():
            speaker_data = speaker.copy()

            # Convert position to readable format
            if 'position' in speaker_data:
                x, y = speaker_data['position']
                speaker_data['position_x'] = x
                speaker_data['position_y'] = y

            result["speakers"].append(speaker_data)

        return result

    def get_speaker_count(self, zone_id=None):
        """Get count of speakers in specified zone or current zone

        Args:
            zone_id (str, optional): Zone ID, uses current if not specified

        Returns:
            int: Number of speakers
        """
        if zone_id is None:
            zone_id = self.current_zone_id

        if zone_id == self.current_zone_id:
            return len(self.current_speakers)
        else:
            return len(self.layout_data.get(zone_id, {}))

    def has_speakers(self, zone_id=None):
        """Check if zone has any speakers

        Args:
            zone_id (str, optional): Zone ID, uses current if not specified

        Returns:
            bool: True if zone has speakers
        """
        return self.get_speaker_count(zone_id) > 0

    def get_speaker_statistics(self):
        """Get statistics about current speakers

        Returns:
            dict: Statistics including counts by type, power, etc.
        """
        if not self.current_speakers:
            return {}

        stats = {
            'total_count': len(self.current_speakers),
            'by_type': {},
            'by_power': {},
            'total_power': 0,
            'avg_dispersion': 0
        }

        total_dispersion = 0

        for speaker in self.current_speakers.values():
            # Count by type
            speaker_type = speaker.get('type', 'Unknown')
            stats['by_type'][speaker_type] = stats['by_type'].get(speaker_type, 0) + 1

            # Count by power
            power = speaker.get('power', 0)
            stats['by_power'][power] = stats['by_power'].get(power, 0) + 1
            stats['total_power'] += power

            # Sum dispersion for average
            dispersion = speaker.get('dispersion_angle', 90)
            total_dispersion += dispersion

        # Calculate average dispersion
        if stats['total_count'] > 0:
            stats['avg_dispersion'] = total_dispersion / stats['total_count']

        return stats

    def validate_speaker_data(self, speaker_data):
        """Validate speaker data structure

        Args:
            speaker_data (dict): Speaker data to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = ['id', 'position', 'type']

        for field in required_fields:
            if field not in speaker_data:
                return False, f"Missing required field: {field}"

        # Validate position
        position = speaker_data['position']
        if not isinstance(position, (list, tuple)) or len(position) != 2:
            return False, "Position must be a list/tuple of 2 coordinates"

        try:
            x, y = position
            float(x)
            float(y)
        except (ValueError, TypeError):
            return False, "Position coordinates must be numeric"

        # Validate type
        valid_types = ["In-Ceiling", "Pendant"]
        if speaker_data['type'] not in valid_types:
            return False, f"Invalid speaker type: {speaker_data['type']}"

        return True, ""

    def get_debug_info(self):
        """Get debug information about current state

        Returns:
            dict: Debug information
        """
        return {
            'current_zone_id': self.current_zone_id,
            'current_speakers_count': len(self.current_speakers),
            'total_zones': len(self.layout_data),
            'layout_data_zones': list(self.layout_data.keys()),
            'has_profile': self.current_profile is not None,
            'profile_name': self.current_profile.name if self.current_profile else None,
            'default_type': self.default_speaker_type,
            'default_dispersion': self.default_dispersion_angle
        }