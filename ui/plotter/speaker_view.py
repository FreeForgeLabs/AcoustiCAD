import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush

from core.zones.background_manager import BackgroundManager
from ui.plotter.data.obstruction_data_manager import ObstructionDataManager
from ui.plotter.data.acoustic_grid_manager import AcousticGridManager
from ui.plotter.rendering.zone_renderer import ZoneRenderer
from ui.plotter.rendering.speaker_renderer import SpeakerRenderer
from ui.plotter.rendering.snapshot_renderer import SnapshotRenderer
from ui.plotter.rendering.coverage_manager import CoverageManager
from ui.plotter.rendering.grid_renderer import GridRenderer
from ui.plotter.rendering.measurement_renderer import MeasurementRenderer
from ui.plotter.rendering.heatmap_renderer import HeatmapRenderer
from ui.plotter.interactions.mouse_handler import MouseHandler
from ui.plotter.interactions.placement_manager import PlacementManager
from ui.plotter.interactions.grid_snapper import GridSnapper
from ui.plotter.data.viewport_manager import ViewportManager
from ui.plotter.data.speaker_data_manager import SpeakerDataManager


class SpeakerView(QWidget):
    """Widget for displaying and manipulating speaker placement - Fully Refactored with Grid/Measurements"""

    # Signals
    speaker_selected = Signal(str)  # Emitted when a speaker is selected (backward compat)
    speakers_selection_changed = Signal(list)   # list of selected speaker IDs
    obstruction_selected = Signal(str)  # Emitted when an obstruction is selected

    # Speaker types (kept for compatibility)
    SPEAKER_TYPES = {
        "In-Ceiling": {"color": (0, 120, 215), "icon": "ceiling"},
        "Pendant": {"color": (0, 180, 120), "icon": "pendant"},
        "Surface Mount": {"color": (200, 60, 0), "icon": "surface"}
    }

    def __init__(self, scale_manager, parent=None):
        super().__init__(parent)
        self.scale_manager = scale_manager
        self.logger = logging.getLogger(__name__)

        # Set widget properties
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(palette)

        # Initialize all component managers
        self._initialize_managers()
        self._connect_all_signals()

        # Current state
        self.current_zone = None
        self.selected_speaker_ids = set()   # multi-select set
        self.selected_obstruction_id = None

        # Legacy properties for backward compatibility
        self.speaker_type = "Auto Select"
        self.dispersion_angle = 90
        self.min_speaker_distance = None

        self.logger.debug("SpeakerView initialized with full component architecture + grid/measurements")

    def _initialize_managers(self):
        """Initialize all component managers"""
        # Core managers
        self.background_manager = BackgroundManager(self)
        self.obstruction_manager = ObstructionDataManager(self.scale_manager, self)

        # Rendering components
        self.zone_renderer = ZoneRenderer()
        self.speaker_renderer = SpeakerRenderer(self.scale_manager)
        self.snapshot_renderer = SnapshotRenderer(self)
        self.coverage_manager = CoverageManager(self)

        # Data management
        self.viewport_manager = ViewportManager(self)
        self.viewport_manager.set_view_size(self.width(), self.height())
        self.speaker_data_manager = SpeakerDataManager(self)

        # Grid and measurement systems (NEW)
        self.acoustic_grid_manager = AcousticGridManager(self.scale_manager)
        self.grid_snapper = GridSnapper(self.acoustic_grid_manager)
        self.grid_renderer = GridRenderer(self.scale_manager, self.grid_snapper)
        self.measurement_renderer = MeasurementRenderer(self.scale_manager)

        # Interaction management
        self.placement_manager = PlacementManager(self)
        self.mouse_handler = MouseHandler(self)
        self.mouse_handler.set_view(self)

        # Heatmap and auto-layout (NEW)
        self.heatmap_renderer = HeatmapRenderer()
        self._grid_type = 'rect'
        self._auto_layout_manager = None

    def _connect_all_signals(self):
        """Connect signals from all component managers"""
        # Viewport signals
        self.viewport_manager.viewport_changed.connect(self.update)

        # Speaker data signals
        self.speaker_data_manager.speaker_added.connect(self._on_speaker_data_added)
        self.speaker_data_manager.speaker_removed.connect(self._on_speaker_data_removed)
        self.speaker_data_manager.speaker_updated.connect(self._on_speaker_data_updated)
        self.speaker_data_manager.speakers_cleared.connect(self._on_speakers_data_cleared)
        self.speaker_data_manager.layout_loaded.connect(self._on_layout_data_loaded)

        # Coverage signals
        self.coverage_manager.coverage_changed.connect(self._on_coverage_changed)
        self.coverage_manager.update_requested.connect(self._on_update_requested)
        self.coverage_manager.forced_update_requested.connect(self._on_forced_update_requested)

        # Placement signals
        self.placement_manager.placement_mode_changed.connect(self._on_placement_mode_changed)
        self.placement_manager.cursor_change_requested.connect(self.setCursor)
        self.placement_manager.status_message.connect(self._on_status_message)
        self.placement_manager.speaker_placed.connect(self._on_speaker_placed)
        self.placement_manager.obstruction_placed.connect(self._on_obstruction_placed)

        # Mouse signals
        self.mouse_handler.speaker_selected.connect(self._on_mouse_speaker_selected)
        self.mouse_handler.obstruction_selected.connect(self._on_mouse_obstruction_selected)
        self.mouse_handler.speaker_added.connect(self._on_mouse_speaker_added)
        self.mouse_handler.obstruction_added.connect(self._on_mouse_obstruction_added)
        self.mouse_handler.speaker_layout_changed.connect(self._on_speaker_layout_changed)
        self.mouse_handler.speaker_layout_changed.connect(self._on_heatmap_invalidate)
        self.mouse_handler.obstruction_layout_changed.connect(self._on_obstruction_layout_changed)
        self.mouse_handler.status_message.connect(self._on_status_message)
        self.mouse_handler.cursor_change.connect(self.setCursor)

    ### SIGNAL HANDLERS ###
    def _on_speaker_data_added(self, speaker_id, speaker_data):
        """Handle speaker added from data manager"""
        self.selected_speaker_ids = {speaker_id}
        self.speakers_selection_changed.emit([speaker_id])
        self.speaker_selected.emit(speaker_id)
        self.update()
        self._notify_parent_speaker_change()

    def _on_speaker_data_removed(self, speaker_id):
        """Handle speaker removed from data manager"""
        self.selected_speaker_ids.discard(speaker_id)
        self.speakers_selection_changed.emit(list(self.selected_speaker_ids))
        # Keep backward-compat speaker_selected signal
        self.speaker_selected.emit(self.selected_speaker_id or "")
        self.update()

    def _on_speaker_data_updated(self, speaker_id, property_name, value):
        """Handle speaker updated from data manager"""
        self.update()

    def _on_speakers_data_cleared(self):
        """Handle speakers cleared from data manager"""
        self.selected_speaker_ids.clear()
        self.speakers_selection_changed.emit([])
        self.speaker_selected.emit("")
        self.update()

    def _on_layout_data_loaded(self, layout_data):
        """Handle layout loaded from data manager"""
        self.coverage_manager.handle_layout_loaded()
        self.update()

    def _on_coverage_changed(self, show_coverage):
        """Handle coverage display state change"""
        # Force update when coverage changes
        self.update()

    def _on_update_requested(self):
        """Handle standard update request from coverage manager"""
        super().update()

    def _on_forced_update_requested(self):
        """Handle forced update request from coverage manager"""
        super().update()

    def _on_placement_mode_changed(self, enabled, mode_type):
        """Handle placement mode changes"""
        self.update()

    def _on_speaker_placed(self, speaker_id):
        """Handle speaker placed from placement manager"""
        self.selected_speaker_ids = {speaker_id}
        self.speakers_selection_changed.emit([speaker_id])
        self.speaker_selected.emit(speaker_id)
        self.update()
        self._notify_parent_speaker_change()

    def _on_obstruction_placed(self, obstruction_id):
        """Handle obstruction placed from placement manager"""
        self.selected_obstruction_id = obstruction_id
        self.obstruction_selected.emit(obstruction_id)
        self.update()
        self._notify_parent_obstruction_change()

    def _on_mouse_speaker_selected(self, speaker_id, multi=False):
        """Handle speaker selection from mouse. multi=True for Ctrl+click."""
        if not speaker_id:
            self.selected_speaker_ids.clear()
        elif multi:
            if speaker_id in self.selected_speaker_ids:
                self.selected_speaker_ids.discard(speaker_id)
            else:
                self.selected_speaker_ids.add(speaker_id)
        else:
            self.selected_speaker_ids = {speaker_id}
        self.speakers_selection_changed.emit(list(self.selected_speaker_ids))
        self.speaker_selected.emit(self.selected_speaker_id or "")
        self.update()

    def _on_mouse_obstruction_selected(self, obstruction_id):
        """Handle obstruction selection from mouse"""
        self.selected_obstruction_id = obstruction_id
        self.obstruction_selected.emit(obstruction_id)

    def _on_mouse_speaker_added(self, x, y):
        """Handle speaker addition from mouse"""
        if self.placement_manager.is_placement_active():
            self.placement_manager.handle_placement_click(x, y)
        else:
            self._add_speaker_at_position(x, y)

    def _on_mouse_obstruction_added(self, x, y, obstruction_type):
        """Handle obstruction addition from mouse"""
        if self.placement_manager.is_placement_active():
            self.placement_manager.handle_placement_click(x, y)

    def _on_speaker_layout_changed(self):
        """Handle speaker layout changes"""
        self._notify_parent_speaker_change()

    def _on_heatmap_invalidate(self):
        """Invalidate heatmap cache when speakers change"""
        if hasattr(self, 'heatmap_renderer'):
            self.heatmap_renderer.invalidate_cache()

    def _on_obstruction_layout_changed(self):
        """Handle obstruction layout changes"""
        self._notify_parent_obstruction_change()

    def _on_status_message(self, message):
        """Handle status messages"""
        parent = self.parent()
        if parent and hasattr(parent, 'status_label'):
            parent.status_label.setText(message)

    def _notify_parent_speaker_change(self):
        """Notify parent of speaker changes"""
        parent = self.parent()
        if parent and hasattr(parent, 'speaker_layout_changed'):
            if hasattr(parent.speaker_layout_changed, 'emit'):
                parent.speaker_layout_changed.emit()
        if parent and hasattr(parent, 'project_manager'):
            parent.project_manager.project_modified = True

    def _notify_parent_obstruction_change(self):
        """Notify parent of obstruction changes"""
        parent = self.parent()
        if parent and hasattr(parent, 'obstruction_layout_changed'):
            if hasattr(parent.obstruction_layout_changed, 'emit'):
                parent.obstruction_layout_changed.emit()
        if parent and hasattr(parent, 'project_manager'):
            parent.project_manager.project_modified = True

    ### PROPERTIES FOR BACKWARD COMPATIBILITY ###

    @property
    def selected_speaker_id(self):
        """Return first selected speaker ID for backward compat, or None."""
        return next(iter(self.selected_speaker_ids), None)

    @selected_speaker_id.setter
    def selected_speaker_id(self, value):
        """Backward-compat setter — replaces selection with single ID (or clears)."""
        if value:
            self.selected_speaker_ids = {value}
        else:
            self.selected_speaker_ids = set()

    @property
    def scale_factor(self):
        """Get current scale factor"""
        return self.viewport_manager.scale_factor

    @scale_factor.setter
    def scale_factor(self, value):
        """Set scale factor"""
        self.viewport_manager.scale_factor = value

    @property
    def offset_x(self):
        """Get current X offset"""
        return self.viewport_manager.offset_x

    @offset_x.setter
    def offset_x(self, value):
        """Set X offset"""
        self.viewport_manager.offset_x = value

    @property
    def offset_y(self):
        """Get current Y offset"""
        return self.viewport_manager.offset_y

    @offset_y.setter
    def offset_y(self, value):
        """Set Y offset"""
        self.viewport_manager.offset_y = value

    @property
    def speakers(self):
        """Get current speakers dictionary"""
        return self.speaker_data_manager.get_all_speakers()

    @property
    def layout_data(self):
        """Get layout data"""
        return self.speaker_data_manager.get_layout_data()

    @layout_data.setter
    def layout_data(self, value):
        """Set layout data"""
        self.speaker_data_manager.load_speaker_layout(value)

    @property
    def show_coverage(self):
        """Get coverage display state"""
        return self.coverage_manager.show_coverage

    @show_coverage.setter
    def show_coverage(self, value):
        """Set coverage display state"""
        self.coverage_manager.show_coverage = value

    @property
    def placement_mode(self):
        """Get speaker placement mode"""
        return self.placement_manager.get_placement_mode() == "speaker"

    @placement_mode.setter
    def placement_mode(self, value):
        """Set speaker placement mode"""
        if value and not self.placement_manager.is_placement_active():
            profile = self.placement_manager.get_current_profile()
            if profile:
                self.placement_manager.start_speaker_placement(profile)
        elif not value:
            self.placement_manager.cancel_placement()

    @property
    def placing_obstruction(self):
        """Get obstruction placement mode"""
        return self.placement_manager.get_placement_mode() == "obstruction"

    @placing_obstruction.setter
    def placing_obstruction(self, value):
        """Set obstruction placement mode"""
        if value and not self.placement_manager.is_placement_active():
            obstruction_type = self.placement_manager.get_current_obstruction_type()
            self.placement_manager.start_obstruction_placement(obstruction_type)
        elif not value:
            self.placement_manager.cancel_placement()

    ### MOUSE EVENTS ###
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        self.mouse_handler.handle_mouse_press(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        self.mouse_handler.handle_mouse_move(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        self.mouse_handler.handle_mouse_release(event)

    def keyPressEvent(self, event):
        """Handle key press events — Delete/Backspace removes selected speakers"""
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            if self.selected_speaker_ids:
                self.delete_selected_speakers()
        else:
            super().keyPressEvent(event)

    ### PAINTING ###
    def paintEvent(self, event):
        """Draw the speakers, obstructions, grid, and measurements"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Save painter state
        painter.save()

        # Apply viewport transformations
        painter.translate(self.viewport_manager.offset_x, self.viewport_manager.offset_y)
        painter.scale(self.viewport_manager.scale_factor, self.viewport_manager.scale_factor)

        # Draw background
        if self.background_manager.has_background():
            self.background_manager.draw(painter)

        # Draw zone content
        if self.current_zone:
            self.zone_renderer.draw_zone(painter, self.current_zone)

            # Draw grid overlay (NEW)
            if self.grid_renderer.is_visible():
                zone_bounds = self.viewport_manager.calculate_zone_bounds(self.current_zone)
                self.grid_renderer.draw_grid(painter, self.viewport_manager, zone_bounds)

            # Draw speakers with coverage
            current_speakers = self.speaker_data_manager.get_all_speakers()
            self.speaker_renderer.draw_speakers(
                painter, current_speakers,
                selected_speaker_ids=self.selected_speaker_ids,
                show_coverage=self.coverage_manager.show_coverage,
                scale_factor=self.viewport_manager.scale_factor
            )

            # Draw obstructions
            self.obstruction_manager.draw_obstructions(
                painter, False, self.viewport_manager.scale_factor
            )

            # Draw measurements (NEW)
            if self.measurement_renderer.is_visible():
                self.logger.debug(f"Drawing measurements with {len(current_speakers)} speakers")
                self.measurement_renderer.draw_measurements(
                    painter, current_speakers, self.current_zone
                )
            else:
                self.logger.debug("Measurements not visible, skipping")

        # Restore painter state
        painter.restore()

        # Draw heatmap in screen space (after transform reset) if enabled
        if (self.heatmap_renderer.is_enabled() and self.current_zone
                and self.speaker_data_manager):
            current_speakers = self.speaker_data_manager.get_all_speakers()
            self.heatmap_renderer.draw_heatmap(
                painter, self.current_zone, current_speakers,
                self.viewport_manager, self.viewport_manager.scale_factor
            )

        # Draw rubber-band selection rectangle (screen space, after transform reset)
        mh = self.mouse_handler
        if (mh.rubber_band_active
                and mh.rubber_band_start_screen
                and mh.rubber_band_end_screen):
            sx1, sy1 = mh.rubber_band_start_screen
            sx2, sy2 = mh.rubber_band_end_screen
            rb_rect = QRect(
                int(min(sx1, sx2)), int(min(sy1, sy2)),
                int(abs(sx2 - sx1)), int(abs(sy2 - sy1))
            )
            rb_pen = QPen(QColor(0, 120, 215))
            rb_pen.setStyle(Qt.DashLine)
            rb_pen.setWidth(1)
            painter.setPen(rb_pen)
            painter.setBrush(QBrush(QColor(0, 120, 215, 30)))
            painter.drawRect(rb_rect)

        # Draw "No zone selected" message if needed
        if not self.current_zone:
            self.zone_renderer.draw_no_zone_message(painter, self.rect())

    def update(self):
        """Override update method to use coverage manager throttling"""
        if self.coverage_manager.should_throttle_update():
            return
        super().update()

    ### RESIZE HANDLING ###
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.viewport_manager.set_view_size(self.width(), self.height())

    ### PUBLIC API METHODS ###
    def set_current_zone(self, zone):
        """Set the current zone and update display"""
        if hasattr(self, '_setting_zone') and self._setting_zone:
            return

        if (self.current_zone and zone and
                'id' in self.current_zone and 'id' in zone and
                self.current_zone['id'] == zone['id']):
            # Same zone, just update the reference (zone data may have changed)
            self.current_zone = zone
            # Update acoustic grid with potentially new zone data
            if hasattr(self, 'acoustic_grid_manager'):
                self.acoustic_grid_manager.set_zone(zone)
            return

        self._setting_zone = True
        try:
            self.current_zone = zone
            self.selected_speaker_id = None
            self.selected_obstruction_id = None
            self.speaker_selected.emit("")

            if zone and 'id' in zone:
                zone_id = str(zone['id'])
                self.obstruction_manager.set_current_zone(zone_id)
                self.speaker_data_manager.set_current_zone(zone_id)
                # Pass zone's pendant height default so new pendant speakers inherit it
                self.speaker_data_manager.set_zone_pendant_height(
                    zone.get('pendant_height', 9.0)
                )

                # Update acoustic grid for this zone (NEW)
                if hasattr(self, 'acoustic_grid_manager'):
                    self.acoustic_grid_manager.set_zone(zone)
            else:
                self.obstruction_manager.set_current_zone(None)
                self.speaker_data_manager.set_current_zone(None)
                if hasattr(self, 'acoustic_grid_manager'):
                    self.acoustic_grid_manager.set_zone(None)

            self.viewport_manager.set_zone(zone)
        finally:
            self._setting_zone = False

    def get_current_zone(self):
        """Get the current zone data"""
        return self.current_zone

    def clear_zone(self):
        """Clear current zone and all data"""
        self.current_zone = None
        self.selected_speaker_id = None
        self.selected_obstruction_id = None
        self.speaker_data_manager.set_current_zone(None)
        self.obstruction_manager.set_current_zone(None)
        self.viewport_manager.reset_viewport()
        self.placement_manager.cancel_placement()
        self.acoustic_grid_manager.clear()
        self.update()

    def fit_zone_to_view(self):
        """Fit current zone to view"""
        return self.viewport_manager.fit_zone_to_view()

    ### COVERAGE METHODS ###
    def set_show_coverage(self, show):
        """Set whether to show coverage patterns"""
        self.coverage_manager.set_show_coverage(show)

    def force_coverage_display(self):
        """Force coverage patterns to be displayed"""
        self.coverage_manager.force_coverage_display()

    def toggle_coverage_visualization(self):
        """Toggle coverage visualization"""
        self.coverage_manager.toggle_coverage_visualization()

    ### PLACEMENT METHODS ###
    def start_speaker_placement(self, profile):
        """Start speaker placement mode"""
        return self.placement_manager.start_speaker_placement(profile)

    def start_obstruction_placement(self, obstruction_type):
        """Start obstruction placement mode"""
        return self.placement_manager.start_obstruction_placement(obstruction_type)

    def set_placement_mode(self, enabled):
        """Enable or disable speaker placement mode"""
        if enabled:
            profile = self.placement_manager.get_current_profile()
            if profile:
                self.placement_manager.start_speaker_placement(profile)
        else:
            self.placement_manager.cancel_placement()

    def set_speaker_profile(self, profile):
        """Set the current speaker profile"""
        if not profile:
            return
        self.speaker_data_manager.set_speaker_profile(profile)
        self.placement_manager.current_speaker_profile = profile
        self.speaker_type = profile.model_type
        self.dispersion_angle = profile.dispersion_angle_h

        # Update acoustic grid for this profile (NEW)
        self.acoustic_grid_manager.set_speaker_profile(profile)

        self.update()

    def set_min_speaker_distance(self, distance):
        """Set minimum speaker distance"""
        self.min_speaker_distance = distance

    ### DATA METHODS ###
    def load_speaker_layout(self, layout_data):
        """Load speaker layout data"""
        return self.speaker_data_manager.load_speaker_layout(layout_data)

    def load_obstruction_layout(self, obstruction_data):
        """Load obstruction layout data"""
        if not obstruction_data:
            return False
        success = self.obstruction_manager.load_obstructions(obstruction_data)
        if success and self.current_zone and 'id' in self.current_zone:
            zone_id = str(self.current_zone['id'])
            self.obstruction_manager.set_current_zone(zone_id)
        self.update()
        return success

    def get_obstruction_layout(self):
        """Get obstruction layout data"""
        return self.obstruction_manager.zone_obstructions

    def delete_selected_speaker(self):
        """Delete the currently selected speaker (single, backward compat)"""
        if self.selected_speaker_id:
            return self.speaker_data_manager.remove_speaker(self.selected_speaker_id)
        return False

    def delete_selected_speakers(self):
        """Delete all currently selected speakers."""
        if self.selected_speaker_ids:
            self.speaker_data_manager.push_undo_snapshot()
        for sid in list(self.selected_speaker_ids):
            self.speaker_data_manager.remove_speaker(sid)
        # selection cleared by _on_speaker_data_removed signals

    def clear_all_speakers(self):
        """Remove all speakers from the current zone."""
        self.speaker_data_manager.push_undo_snapshot()
        self.speaker_data_manager.clear_speakers()

    def delete_selected_obstruction(self):
        """Delete the currently selected obstruction"""
        if self.selected_obstruction_id:
            success = self.obstruction_manager.remove_obstruction(self.selected_obstruction_id)
            if success:
                self.selected_obstruction_id = None
                self.obstruction_selected.emit("")
                self.update()
            return success
        return False

    def clear_speakers(self):
        """Clear all speakers from current zone"""
        return self.speaker_data_manager.clear_speakers() > 0

    def export_speaker_data(self):
        """Export speaker data for reports"""
        return self.speaker_data_manager.export_speaker_data(self.current_zone)

    def set_dispersion_angle(self, angle):
        """Set dispersion angle for speakers"""
        self.dispersion_angle = angle
        self.speaker_data_manager.update_all_speaker_dispersion(angle, self.selected_speaker_id)
        self.update()

    def set_speaker_type(self, speaker_type):
        """Set current speaker type"""
        self.speaker_type = speaker_type
        self.speaker_data_manager.default_speaker_type = speaker_type

    ### BACKGROUND METHODS ###
    def has_background(self):
        """Check if background is loaded"""
        return self.background_manager.has_background()

    def get_background_size(self):
        """Get background image size"""
        if self.background_manager.has_background():
            return self.background_manager.get_background_size()
        return (0, 0)

    def load_background(self, image_path):
        """Load background image"""
        if not image_path:
            return False
        success = self.background_manager.load_background(image_path)
        if success:
            self.update()
        return success

    ### SNAPSHOT METHODS ###
    def capture_zone_snapshot(self, width=1200, height=900, include_legend=True):
        """Capture high-quality zone snapshot"""
        return self.snapshot_renderer.capture_zone_snapshot(width, height, include_legend)

    def capture_all_zones_thumbnails(self, zones, speaker_layout, obstruction_layout, thumbnail_size=300):
        """Capture thumbnails for all zones"""
        return self.snapshot_renderer.capture_all_zones_thumbnails(
            zones, speaker_layout, obstruction_layout, thumbnail_size
        )

    def pixmap_to_base64(self, pixmap):
        """Convert QPixmap to base64 string"""
        return self.snapshot_renderer.pixmap_to_base64(pixmap)

    ### GRID AND MEASUREMENT METHODS (NEW) ###
    def set_acoustic_grid_visible(self, visible):
        """Set acoustic grid visibility"""
        self.grid_renderer.set_visible(visible)
        self.update()

    def set_measurements_visible(self, visible):
        """Set measurement annotations visibility"""
        self.logger.info(f"Setting measurements visible: {visible}")
        self.measurement_renderer.set_visible(visible)
        self.logger.info(f"Measurement renderer visible state: {self.measurement_renderer.is_visible()}")
        self.update()

    def set_grid_snapping_enabled(self, enabled):
        """Enable or disable grid snapping"""
        self.grid_snapper.set_enabled(enabled)
        self.logger.info(f"Grid snapping {'enabled' if enabled else 'disabled'}")

    def get_grid_info(self):
        """Get information about current grid configuration"""
        return self.acoustic_grid_manager.get_grid_info()

    def get_grid_spacing_formatted(self):
        """Get formatted grid spacing string"""
        return self.grid_snapper.format_grid_size()

    ### VIZ MODE AND AUTO-LAYOUT METHODS (NEW) ###
    def set_viz_mode(self, mode):
        """Switch between 'circles' and 'heatmap' visualization."""
        self.heatmap_renderer.set_enabled(mode == 'heatmap')
        self.set_show_coverage(mode == 'circles')
        self.update()

    def set_grid_type(self, grid_type):
        """Set the grid type for auto-layout ('rect' or 'hex')."""
        self._grid_type = grid_type

    def run_auto_layout(self, zone, profile, overlap_pct=None, layout_method=None):
        """Run auto-layout algorithm for the current zone."""
        if not self._auto_layout_manager:
            return
        if profile:
            self.set_speaker_profile(profile)
        positions = self._auto_layout_manager.generate_layout(
            zone, profile, self._grid_type, overlap_pct=overlap_pct, layout_method=layout_method)
        if not positions:
            return
        zone_id = zone.get('id')
        if zone_id is not None:
            zone_id = str(zone_id)
        # Clear existing speakers in this zone
        for spk_id in list(self.speaker_data_manager.get_all_speakers().keys()):
            self.speaker_data_manager.remove_speaker(spk_id)
        # Place new speakers
        for x, y in positions:
            self.speaker_data_manager.add_speaker(x, y, zone_id)
        self.heatmap_renderer.invalidate_cache()
        self.update()

    def set_auto_layout_manager(self, manager):
        """Set the auto-layout manager instance."""
        self._auto_layout_manager = manager

    ### UTILITY METHODS ###
    def _add_speaker_at_position(self, x, y):
        """Add speaker at position (backward compatibility)"""
        if not self.current_zone or 'id' not in self.current_zone:
            return None
        zone_id = str(self.current_zone['id'])
        return self.speaker_data_manager.add_speaker(x, y, zone_id)