import math
import logging
from PySide6.QtCore import Qt, QObject, Signal


class MouseHandler(QObject):
    """Handles all mouse interactions for the speaker view"""

    # Signals for communicating with the parent view
    speaker_selected = Signal(str)  # speaker_id
    obstruction_selected = Signal(str)  # obstruction_id
    speaker_added = Signal(float, float)  # x, y position
    obstruction_added = Signal(float, float, str)  # x, y, obstruction_type
    speaker_layout_changed = Signal()
    obstruction_layout_changed = Signal()
    status_message = Signal(str)  # status message to display
    cursor_change = Signal(object)  # Qt cursor to set

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Reference to the parent view (will be set by parent)
        self.view = None

        # Mouse interaction state
        self.dragging_speaker = False
        self.dragging_obstruction = False
        self.drag_start_pos = None

        # Rubber-band (drag-to-select) state — stored in screen pixels
        self.rubber_band_active = False
        self.rubber_band_start_screen = None   # (sx, sy) on press
        self.rubber_band_end_screen = None     # (sx, sy) current cursor position
        self.rubber_band_additive = False      # True when Shift/Ctrl held on press

    def set_view(self, view):
        """Set the parent view reference

        Args:
            view: The SpeakerView instance
        """
        self.view = view

    def handle_mouse_press(self, event):
        """Handle mouse press events

        Args:
            event: QMouseEvent

        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self.view:
            return False

        # Convert screen coordinates to world coordinates
        x, y = self._screen_to_world(event.x(), event.y())

        # Handle obstruction placement mode
        if self._handle_obstruction_placement(event, x, y):
            return True

        # Handle speaker placement mode
        if self._handle_speaker_placement(event, x, y):
            return True

        # Handle selection and dragging
        if event.button() == Qt.LeftButton:
            return self._handle_selection_and_dragging(x, y, event)

        return False

    def handle_mouse_move(self, event):
        """Handle mouse move events

        Args:
            event: QMouseEvent

        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self.view:
            return False

        # Convert screen coordinates to world coordinates
        x, y = self._screen_to_world(event.x(), event.y())

        # Handle obstruction dragging
        if self._handle_obstruction_dragging(x, y):
            return True

        # Handle speaker dragging
        if self._handle_speaker_dragging(x, y):
            return True

        # Update rubber-band end position
        if self.rubber_band_active:
            self.rubber_band_end_screen = (event.x(), event.y())
            self.view.update()
            return True

        return False

    def handle_mouse_release(self, event):
        """Handle mouse release events

        Args:
            event: QMouseEvent

        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self.view:
            return False

        if event.button() == Qt.LeftButton:
            # Finish rubber-band selection before anything else
            if self.rubber_band_active:
                self._end_rubber_band_selection(event)
                return True

            was_dragging = self.dragging_obstruction or self.dragging_speaker

            # Handle obstruction drag end
            if self.dragging_obstruction:
                self._end_obstruction_drag()

            # Handle speaker drag end
            if self.dragging_speaker:
                self._end_speaker_drag()

            return was_dragging

        return False

    def _screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates

        Args:
            screen_x, screen_y: Screen pixel coordinates

        Returns:
            tuple: (world_x, world_y) coordinates
        """
        if not self.view:
            return (0, 0)

        x = (screen_x - self.view.offset_x) / self.view.scale_factor
        y = (screen_y - self.view.offset_y) / self.view.scale_factor
        return (x, y)

    def _handle_obstruction_placement(self, event, x, y):

        if not (hasattr(self.view, 'placing_obstruction') and self.view.placing_obstruction):
            return False

        if event.button() != Qt.LeftButton:
            return False

        if not self.view.current_zone:
            return False

        # Check if clicked inside the zone
        if 'points' in self.view.current_zone and self.view.current_zone['points']:
            from core.zones.geometry_utils import point_inside_polygon
            if not point_inside_polygon((x, y), self.view.current_zone['points']):
                return False  # Click outside zone

        # Create a new obstruction

        # Get obstruction type from placement manager
        if hasattr(self.view, 'placement_manager'):
            obstruction_type = self.view.placement_manager.get_current_obstruction_type()
        else:
            obstruction_type = getattr(self.view, 'obstruction_type', 'Column')
        obstruction_id = self.view.obstruction_manager.add_obstruction(x, y, obstruction_type)

        if obstruction_id:
            # Select the new obstruction
            self.view.selected_obstruction_id = obstruction_id
            self.view.obstruction_manager.select_obstruction(obstruction_id)

            # Emit signals
            self.obstruction_selected.emit(obstruction_id)

        # Exit placement mode
        self.view.placing_obstruction = False
        self.cursor_change.emit(Qt.ArrowCursor)
        self.status_message.emit("Obstruction placed")

        # Update display
        self.view.update()
        return True

    def _handle_speaker_placement(self, event, x, y):
        """Handle speaker placement mode

        Args:
            event: QMouseEvent
            x, y: World coordinates

        Returns:
            bool: True if placement was handled
        """
        if not (hasattr(self.view, 'placement_mode') and self.view.placement_mode):
            return False

        if event.button() != Qt.LeftButton:
            return False

        if not self.view.current_zone:
            return False

        # Check if clicked inside the zone
        if 'points' in self.view.current_zone and self.view.current_zone['points']:
            from core.zones.geometry_utils import point_inside_polygon
            if not point_inside_polygon((x, y), self.view.current_zone['points']):
                return False  # Click outside zone

        # Check for collision with obstructions
        speaker_radius = 1.0  # Default speaker radius in inches
        min_distance = getattr(self.view, 'min_speaker_distance', None)
        can_place, reason = self.view.obstruction_manager.check_speaker_placement(
            x, y, speaker_radius, min_distance)

        if not can_place:
            self.status_message.emit(f"Cannot place speaker: {reason}")
            return False

        # Signal to add speaker
        self.speaker_added.emit(x, y)

        # Exit placement mode
        self.view.placement_mode = False
        self.cursor_change.emit(Qt.ArrowCursor)
        self.status_message.emit("Speaker placed")

        # Update display
        self.view.update()
        return True

    def _handle_selection_and_dragging(self, x, y, event=None):
        """Handle selection and start of dragging

        Args:
            x, y: World coordinates
            event: QMouseEvent (used for modifier key detection)

        Returns:
            bool: True if selection was handled
        """
        # Check for obstruction selection first (they're on top layer)
        obstruction_id = self.view.obstruction_manager.get_nearest_obstruction(
            x, y, 20 / self.view.scale_factor)

        if obstruction_id:
            # Select this obstruction
            self.view.obstruction_manager.select_obstruction(obstruction_id)
            self.view.selected_obstruction_id = obstruction_id
            self.obstruction_selected.emit(obstruction_id)

            # Deselect any selected speaker
            if hasattr(self.view, 'selected_speaker_ids') and self.view.selected_speaker_ids:
                self.view._on_mouse_speaker_selected("", multi=False)
                self.speaker_selected.emit("")

            # Start dragging
            self.dragging_obstruction = True
            self.drag_start_pos = (x, y)
            self.cursor_change.emit(Qt.ClosedHandCursor)

            self.view.update()
            return True

        # Check for speaker selection
        for speaker_id, speaker in self.view.speakers.items():
            sx, sy = speaker['position']
            distance = math.sqrt((x - sx) ** 2 + (y - sy) ** 2)

            # Use speaker renderer for click detection
            click_radius = self.view.speaker_renderer.get_speaker_click_radius(
                speaker, self.view.scale_factor)

            if distance <= click_radius:
                # Multi-select: Ctrl, Cmd (macOS), or Shift all work
                modifiers = event.modifiers() if event else Qt.NoModifier
                multi = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier | Qt.ShiftModifier))
                self._select_speaker(speaker_id, multi=multi)

                # Deselect any selected obstruction
                if hasattr(self.view, 'selected_obstruction_id') and self.view.selected_obstruction_id:
                    self.view.obstruction_manager.select_obstruction(None)
                    self.view.selected_obstruction_id = None
                    self.obstruction_selected.emit("")

                # Start dragging
                self.dragging_speaker = True
                self.drag_start_pos = (x, y)
                self.cursor_change.emit(Qt.ClosedHandCursor)

                self.view.update()
                return True

        # Nothing was hit — deselect obstructions and start rubber-band selection
        if hasattr(self.view, 'selected_obstruction_id') and self.view.selected_obstruction_id:
            self.view.obstruction_manager.select_obstruction(None)
            self.view.selected_obstruction_id = None
            self.obstruction_selected.emit("")

        modifiers = event.modifiers() if event else Qt.NoModifier
        additive = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier | Qt.ShiftModifier))

        if not additive:
            # Clear existing selection immediately (non-additive drag replaces)
            self.view._on_mouse_speaker_selected("", multi=False)
            self.speaker_selected.emit("")

        # Begin rubber-band drag
        self.rubber_band_active = True
        self.rubber_band_start_screen = (event.x(), event.y())
        self.rubber_band_end_screen = (event.x(), event.y())
        self.rubber_band_additive = additive

        self.view.update()
        return True

    def _select_speaker(self, speaker_id, multi=False):
        """Update speaker selection on the view, respecting multi-select."""
        self.view._on_mouse_speaker_selected(speaker_id, multi=multi)
        self.speaker_selected.emit(self.view.selected_speaker_id or "")

    def _handle_obstruction_dragging(self, x, y):
        """Handle obstruction dragging

        Args:
            x, y: World coordinates

        Returns:
            bool: True if dragging was handled
        """
        if not (self.dragging_obstruction and
                hasattr(self.view, 'selected_obstruction_id') and
                self.view.selected_obstruction_id):
            return False

        # Update obstruction position
        selected_obstruction = self.view.obstruction_manager.get_selected_obstruction()
        if selected_obstruction:
            self.view.obstruction_manager.update_obstruction(
                self.view.selected_obstruction_id, 'position', (x, y))

            # Update display
            self.view.update()

        return True

    def _handle_speaker_dragging(self, x, y):
        """Handle speaker dragging with grid snapping support

        Args:
            x, y: World coordinates

        Returns:
            bool: True if dragging was handled
        """
        if not (self.dragging_speaker and
                hasattr(self.view, 'selected_speaker_id') and
                self.view.selected_speaker_id):
            return False

        # Make sure we have current zone
        if not self.view.current_zone:
            return False

        # APPLY GRID SNAPPING TO DRAG COORDINATES
        if hasattr(self.view, 'grid_snapper') and self.view.grid_snapper:
            snapped_x, snapped_y = self.view.grid_snapper.snap_to_grid(x, y)
            if abs(snapped_x - x) > 0.01 or abs(snapped_y - y) > 0.01:
                self.logger.debug(f"Grid snap during drag: ({x:.2f}, {y:.2f}) → ({snapped_x:.2f}, {snapped_y:.2f})")
                x, y = snapped_x, snapped_y

        # Check if inside the zone
        if 'points' in self.view.current_zone and self.view.current_zone['points']:
            from core.zones.geometry_utils import point_inside_polygon
            if not point_inside_polygon((x, y), self.view.current_zone['points']):
                return False  # Don't allow dropping outside zone

        # Get speaker data from data manager
        speaker_data = self.view.speaker_data_manager.get_speaker(self.view.selected_speaker_id)
        if not speaker_data:
            return False

        # Get current position for backup
        current_pos = speaker_data['position']
        if isinstance(current_pos, list):
            current_pos = tuple(current_pos)

        # Temporarily update speaker position in data manager for collision check
        self.view.speaker_data_manager.update_speaker(
            self.view.selected_speaker_id, 'position', (-9999, -9999))

        # Check for collision with obstructions
        speaker_radius = 12  # Default speaker radius in pixels
        min_distance = getattr(self.view, 'min_speaker_distance', None)
        can_place, reason = self.view.obstruction_manager.check_speaker_placement(
            x, y, speaker_radius, min_distance)

        if not can_place:
            # Restore original position in data manager
            self.view.speaker_data_manager.update_speaker(
                self.view.selected_speaker_id, 'position', current_pos)
            # Log the reason for debugging
            self.logger.debug(f"Cannot move speaker: {reason}")
            return False

        # Update position in data manager (this will trigger signals and update display)
        self.view.speaker_data_manager.update_speaker(
            self.view.selected_speaker_id, 'position', (x, y))

        # Force coverage display to update
        self.view.show_coverage = True

        return True

    def _end_rubber_band_selection(self, event):
        """Finish a rubber-band drag and select all speakers inside the rect."""
        self.rubber_band_end_screen = (event.x(), event.y())

        sx1, sy1 = self.rubber_band_start_screen
        sx2, sy2 = self.rubber_band_end_screen

        # Treat very small drag (< 6 px in both dims) as a plain deselect click
        if abs(sx2 - sx1) < 6 and abs(sy2 - sy1) < 6:
            if not self.rubber_band_additive:
                self.view._on_mouse_speaker_selected("", multi=False)
                self.speaker_selected.emit("")
        else:
            # Convert rubber-band corners to world coordinates
            wx1, wy1 = self._screen_to_world(sx1, sy1)
            wx2, wy2 = self._screen_to_world(sx2, sy2)
            min_x, max_x = min(wx1, wx2), max(wx1, wx2)
            min_y, max_y = min(wy1, wy2), max(wy1, wy2)

            # Collect all speakers whose centre falls inside the rect
            captured = {
                sid for sid, spk in self.view.speakers.items()
                if min_x <= spk['position'][0] <= max_x
                and min_y <= spk['position'][1] <= max_y
            }

            if self.rubber_band_additive:
                self.view.selected_speaker_ids |= captured
            else:
                self.view.selected_speaker_ids = captured

            self.view.speakers_selection_changed.emit(list(self.view.selected_speaker_ids))
            self.view.speaker_selected.emit(self.view.selected_speaker_id or "")

        # Reset rubber-band state
        self.rubber_band_active = False
        self.rubber_band_start_screen = None
        self.rubber_band_end_screen = None
        self.rubber_band_additive = False
        self.view.update()

    def _end_obstruction_drag(self):
        """End obstruction dragging"""
        self.dragging_obstruction = False
        self.drag_start_pos = None
        self.cursor_change.emit(Qt.ArrowCursor)

        # Emit signal when obstruction dragging ends
        self.obstruction_layout_changed.emit()

    def _end_speaker_drag(self):
        """End speaker dragging"""
        self.dragging_speaker = False
        self.drag_start_pos = None
        self.cursor_change.emit(Qt.ArrowCursor)

        # Emit signal when speaker dragging ends
        self.speaker_layout_changed.emit()

    def cancel_placement_mode(self):
        """Cancel any active placement mode"""
        if hasattr(self.view, 'placement_mode'):
            self.view.placement_mode = False
        if hasattr(self.view, 'placing_obstruction'):
            self.view.placing_obstruction = False
        self.cursor_change.emit(Qt.ArrowCursor)

    def is_dragging(self):
        """Check if currently dragging anything

        Returns:
            bool: True if dragging speakers or obstructions
        """
        return self.dragging_speaker or self.dragging_obstruction

    def get_drag_info(self):
        """Get information about current drag operation

        Returns:
            dict: Information about current drag state
        """
        return {
            'dragging_speaker': self.dragging_speaker,
            'dragging_obstruction': self.dragging_obstruction,
            'drag_start_pos': self.drag_start_pos
        }