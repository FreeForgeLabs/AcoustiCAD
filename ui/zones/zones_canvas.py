import logging
from PySide6.QtWidgets import QWidget, QInputDialog, QApplication
from PySide6.QtCore import Qt, Signal, QPoint, QPointF, QEvent, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QImage

from core.zones.background_manager import BackgroundManager
from core.zones.drawing_manager import DrawingManager
from core.zones.grid_manager import GridManager
from core.scale_manager import ScaleManager
from core.zones.geometry_utils import point_inside_polygon, calculate_polygon_area
from ui.zones.zones_renderer import ZonesRenderer
from ui.styles.base_styles import Colors


class ZonesCanvas(QWidget):
    """Widget for rendering zones on a canvas with interaction capabilities"""

    # Signals
    zones_modified = Signal()
    selection_changed = Signal()
    zoom_changed = Signal(float)   # Emitted whenever zoom_factor changes

    def __init__(self, scale_manager, parent=None):
        """Initialize the zones canvas"""
        super().__init__(parent)
        self.scale_manager = scale_manager  # Store the scale manager
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing ZonesCanvas")

        # Initialize managers
        self._init_managers()

        # Initialize zone data
        self.zones = []
        self.selected_zone_index = None

        # Initialize canvas properties
        self._init_canvas_properties()

        # Initialize interaction state
        self._init_interaction_state()

        # Initialize renderer
        self.renderer = ZonesRenderer(self)

        self.logger.debug("ZonesCanvas initialized")

    def _init_managers(self):
        """Initialize all manager components"""
        self.background_manager = BackgroundManager(self)
        self.drawing_manager = DrawingManager(
            self.scale_manager, self,
            on_zone_created=self._on_zone_created,
        )
        self.grid_manager = GridManager(self)

    def _on_zone_created(self):
        """Called by DrawingManager when a new zone is committed."""
        self.zones_modified.emit()

    def _init_canvas_properties(self):
        """Initialize canvas visual properties"""
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(palette)

        # Set minimum size
        self.setMinimumSize(800, 600)

        # Enable gesture support
        self.grabGesture(Qt.PinchGesture)

    def _init_interaction_state(self):
        """Initialize interaction and transformation state"""
        # Canvas transformations
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_increment = 0.1

        # Mouse interaction tracking
        self.last_mouse_pos = QPoint(0, 0)
        self.panning = False
        self.space_pressed = False
        self.pan_with_left_button = False

    # ==================== CORE DRAWING METHODS ====================

    def paintEvent(self, event):
        """Main paint event - now uses renderer for clean separation"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Apply zoom transformation
            painter.scale(self.zoom_factor, self.zoom_factor)

            # Get visible viewport in scene coordinates
            visible_rect = self.get_visible_rect()

            # Delegate all rendering to the renderer
            self.renderer.render_all(painter, visible_rect)

        except Exception as e:
            self.logger.error(f"Error during paint event: {e}", exc_info=True)

    # ==================== UTILITY METHODS ====================

    def get_visible_rect(self):
        """Get the visible viewport rectangle in scene coordinates"""
        try:
            scroll_area = self.parent().parent()
            if not scroll_area:
                return QRectF(0, 0, self.width(), self.height())

            viewport = scroll_area.viewport()
            viewport_width = viewport.width()
            viewport_height = viewport.height()

            h_scroll = scroll_area.horizontalScrollBar().value()
            v_scroll = scroll_area.verticalScrollBar().value()

            # Convert to scene coordinates (account for zoom)
            x = h_scroll / self.zoom_factor
            y = v_scroll / self.zoom_factor
            width = viewport_width / self.zoom_factor
            height = viewport_height / self.zoom_factor

            return QRectF(x, y, width, height)

        except Exception as e:
            self.logger.error(f"Error getting visible rect: {e}", exc_info=True)
            return QRectF(0, 0, self.width(), self.height())

    def transform_point(self, point):
        """Transform a point from view coordinates to canvas coordinates"""
        if not isinstance(point, (QPoint, QPointF)):
            self.logger.warning(f"Invalid point type for transform: {type(point)}")
            return (0, 0)

        x = point.x() / self.zoom_factor
        y = point.y() / self.zoom_factor
        return (x, y)

    def update_canvas_size(self):
        """Update the canvas size based on content and zoom level"""
        width, height = 800, 600

        # If background is loaded, use its dimensions
        if self.background_manager.has_background():
            bg_width, bg_height = self.background_manager.get_background_size()
            width = max(width, bg_width)
            height = max(height, bg_height)

        # Consider zone extents
        for zone in self.zones:
            if 'points' in zone and zone['points']:
                for x, y in zone['points']:
                    width = max(width, x + 50)
                    height = max(height, y + 50)

        # Apply zoom factor
        width = int(width * self.zoom_factor)
        height = int(height * self.zoom_factor)

        # Update widget size
        self.setMinimumSize(width, height)
        self.resize(width, height)
        self.logger.debug(f"Canvas size updated to {width}x{height} (zoom: {self.zoom_factor:.2f})")

    # ==================== INTERACTION STATE METHODS ====================

    def is_in_drawing_mode(self):
        """Check if we're in a drawing or calibration mode"""
        return (self.drawing_manager.is_drawing() or
                self.scale_manager.is_calibrating() or
                self.drawing_manager.is_dragging_point())

    def should_pan(self, event):
        """Determine if we should pan based on current state and event"""
        if event.buttons() & Qt.MiddleButton:
            return True
        if self.space_pressed and event.buttons() & Qt.LeftButton:
            return True
        return False

    # ==================== GRID AND VISUAL CONTROLS ====================

    def toggle_grid(self):
        """Toggle grid visibility"""
        try:
            is_visible = self.grid_manager.toggle_grid()
            self.update()
            self.logger.debug(f"Grid visibility toggled to: {is_visible}")
            return is_visible
        except Exception as e:
            self.logger.error(f"Error toggling grid: {e}", exc_info=True)
            return False

    def toggle_snap(self):
        """Toggle grid snapping"""
        try:
            is_snap_enabled = self.grid_manager.toggle_snap()
            self.logger.debug(f"Grid snapping toggled to: {is_snap_enabled}")
            return is_snap_enabled
        except Exception as e:
            self.logger.error(f"Error toggling snap: {e}", exc_info=True)
            return False

    def set_grid_size(self, size):
        """Set grid size"""
        try:
            result = self.grid_manager.set_grid_size(size)
            if result:
                self.update()
            return result
        except Exception as e:
            self.logger.error(f"Error setting grid size: {e}", exc_info=True)
            return False

    def set_line_color(self, color):
        """Set drawing line color"""
        try:
            result = self.drawing_manager.set_line_color(color)
            if result:
                self.update()
            return result
        except Exception as e:
            self.logger.error(f"Error setting line color: {e}", exc_info=True)
            return False

    # ==================== ZONE MANAGEMENT ====================

    def calculate_area(self, points):
        """Calculate area for a set of points"""
        try:
            area_pixels = calculate_polygon_area(points)
            area_sqft = self.scale_manager.square_pixels_to_square_feet(area_pixels)
            return round(area_sqft, 2)
        except Exception as e:
            self.logger.error(f"Error calculating area: {e}", exc_info=True)
            return 0.0

    def select_shape_at_point(self, pos):
        """Select a zone at the given point"""
        if not pos:
            return

        try:
            old_zone_index = self.selected_zone_index

            # Check zones for selection
            for i, zone in enumerate(self.zones):
                if 'points' not in zone or not zone['points'] or len(zone['points']) < 3:
                    continue

                if point_inside_polygon((pos.x(), pos.y()), zone['points']):
                    self.selected_zone_index = i
                    self.logger.debug(f"Selected zone at index {i}")
                    self._emit_selection_signals()
                    self._enable_delete_button()
                    return

            # No zone was selected
            self.selected_zone_index = None
            self.logger.debug("No zone selected at click position")

            if old_zone_index is not None:
                self._emit_selection_signals()
                self._disable_delete_button()

        except Exception as e:
            self.logger.error(f"Error selecting shape at point: {e}", exc_info=True)

    def delete_selected_zone(self):
        """Delete the currently selected zone"""
        try:
            if self.selected_zone_index is None:
                self.logger.warning("No zone selected for deletion")
                return False

            zone_name = self.zones[self.selected_zone_index].get('name', f"Zone {self.selected_zone_index + 1}")

            # Remove the zone
            self.zones.pop(self.selected_zone_index)
            self.logger.info(f"Deleted zone: {zone_name}")

            # Reset selection
            self.selected_zone_index = None

            # Update UI
            self.update()
            self.zones_modified.emit()
            self.selection_changed.emit()

            # Update properties panel
            self._update_properties_panel()

            return True

        except Exception as e:
            self.logger.error(f"Error deleting zone: {e}", exc_info=True)
            return False

    # ==================== SIGNAL AND UI HELPER METHODS ====================

    def _emit_selection_signals(self):
        """Emit selection changed signals"""
        self.selection_changed.emit()
        self.logger.debug("Emitted selection_changed signal")

    def _update_properties_panel(self, zone_index=None):
        """Update properties panel through parent hierarchy"""
        zones_tab = self._find_zones_tab()
        if zones_tab:
            if zone_index is not None:
                zones_tab.update_properties_panel(zone_index)
                self.logger.debug(f"Called update_properties_panel({zone_index})")
            else:
                zones_tab.update_properties_panel()
                self.logger.debug("Called update_properties_panel to clear selection")

    def _enable_delete_button(self):
        """Enable delete button in properties panel"""
        properties_panel = self._find_properties_panel()
        if properties_panel:
            properties_panel.delete_zone_btn.setEnabled(True)
            self.logger.debug("Enabled delete button in properties panel")

    def _disable_delete_button(self):
        """Disable delete button in properties panel"""
        properties_panel = self._find_properties_panel()
        if properties_panel:
            properties_panel.delete_zone_btn.setEnabled(False)
            self.logger.debug("Disabled delete button in properties panel")

    def _find_zones_tab(self):
        """Find zones tab in parent hierarchy"""
        parent = self
        while parent:
            if hasattr(parent, 'update_properties_panel'):
                return parent
            if hasattr(parent, 'parent') and callable(parent.parent):
                parent = parent.parent()
            else:
                break
        return None

    def _find_properties_panel(self):
        """Find properties panel in parent hierarchy"""
        parent = self
        while parent:
            if hasattr(parent, 'properties_panel'):
                return parent.properties_panel
            if hasattr(parent, 'zones_tab') and hasattr(parent.zones_tab, 'properties_panel'):
                return parent.zones_tab.properties_panel
            if hasattr(parent, 'parent') and callable(parent.parent):
                parent = parent.parent()
            else:
                break
        return None

    # ==================== EVENT HANDLING METHODS ====================

    def mousePressEvent(self, event):
        """Handle mouse press events - clean and focused"""
        try:
            event.accept()
            self.last_mouse_pos = event.pos()

            # Check for panning first
            if self._should_start_panning(event):
                self._start_panning()
                return

            # Transform to canvas coordinates
            canvas_point = self._get_canvas_point(event.pos())

            # Route based on current mode
            if self._handle_mode_specific_press(event, canvas_point):
                return

            # Handle general interaction
            self._handle_general_press(event, canvas_point)

        except Exception as e:
            self.logger.error(f"Error in mousePressEvent: {e}", exc_info=True)
            self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        try:
            if self._handle_panning_release():
                return

            if self._handle_point_drag_release(event):
                return

        except Exception as e:
            self.logger.error(f"Error in mouseReleaseEvent: {e}", exc_info=True)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        try:
            if self._handle_panning_move(event):
                return

            self._update_cursor_state(event)
            self._handle_interaction_move(event)

        except Exception as e:
            self.logger.error(f"Error in mouseMoveEvent: {e}", exc_info=True)

    def keyPressEvent(self, event):
        """Handle key press events"""
        try:
            # Handle space bar for pan mode
            if self._handle_pan_key_press(event):
                return

            # Handle zoom shortcuts
            if self._handle_zoom_shortcuts(event):
                return

            # Handle grid shortcuts
            if self._handle_grid_shortcuts(event):
                return

            # Handle mode cancellation
            if self._handle_mode_cancellation(event):
                return

            # Handle other shortcuts
            if self._handle_other_shortcuts(event):
                return

            super().keyPressEvent(event)

        except Exception as e:
            self.logger.error(f"Error in keyPressEvent: {e}", exc_info=True)
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release events"""
        try:
            if event.key() == Qt.Key_Space and not event.isAutoRepeat():
                self._handle_space_release()
                event.accept()
                return

            super().keyReleaseEvent(event)

        except Exception as e:
            self.logger.error(f"Error in keyReleaseEvent: {e}", exc_info=True)
            super().keyReleaseEvent(event)

    def wheelEvent(self, event):
        """Handle mouse wheel events"""
        try:
            if self._is_mouse_wheel_zoom(event):
                self._handle_zoom_wheel(event)
            else:
                self._handle_scroll_wheel(event)
            event.accept()

        except Exception as e:
            self.logger.error(f"Error in wheelEvent: {e}", exc_info=True)

    def event(self, event):
        """Handle various events including gestures"""
        if event.type() == QEvent.Gesture:
            return self.gestureEvent(event)
        return super().event(event)

    def gestureEvent(self, event):
        """Handle gesture events (trackpad pinch)"""
        try:
            gesture = event.gesture(Qt.PinchGesture)
            if gesture:
                center_point = gesture.centerPoint().toPoint()
                scene_center_x, scene_center_y = self.transform_point(center_point)

                scale_factor = gesture.totalScaleFactor()
                current_zoom = self.zoom_factor
                target_zoom = current_zoom * scale_factor

                # Clamp and smooth
                target_zoom = max(self.min_zoom, min(self.max_zoom, target_zoom))
                new_zoom = current_zoom + (target_zoom - current_zoom) * 0.3

                old_zoom = self.zoom_factor
                self.zoom_factor = new_zoom

                self.update_canvas_size()

                # Adjust scroll position
                new_view_center_x = scene_center_x * self.zoom_factor
                new_view_center_y = scene_center_y * self.zoom_factor

                scroll_area = self.parent().parent()
                delta_x = new_view_center_x - center_point.x()
                delta_y = new_view_center_y - center_point.y()

                scroll_area.horizontalScrollBar().setValue(
                    scroll_area.horizontalScrollBar().value() + int(delta_x)
                )
                scroll_area.verticalScrollBar().setValue(
                    scroll_area.verticalScrollBar().value() + int(delta_y)
                )

                self.update()
                self.logger.debug(f"Pinch zoom from {old_zoom:.2f} to {new_zoom:.2f}")
                return True

        except Exception as e:
            self.logger.error(f"Error in gestureEvent: {e}", exc_info=True)

        return False

    # ==================== MOUSE EVENT HELPER METHODS ====================

    def _should_start_panning(self, event):
        """Determine if we should start panning"""
        return (event.buttons() & Qt.MiddleButton or
                (self.space_pressed and event.buttons() & Qt.LeftButton))

    def _start_panning(self):
        """Start panning mode"""
        self.panning = True
        self.setCursor(Qt.ClosedHandCursor)

    def _get_canvas_point(self, view_pos):
        """Transform view position to canvas coordinates"""
        canvas_x, canvas_y = self.transform_point(view_pos)
        return QPoint(int(canvas_x), int(canvas_y))

    def _handle_mode_specific_press(self, event, canvas_point):
        """Handle clicks for specific modes (calibration, drawing, point editing)"""
        # Handle calibration mode
        if self.scale_manager.is_calibrating() and event.button() == Qt.LeftButton:
            self._handle_calibration_click(canvas_point)
            return True

        # Handle drawing mode
        if self.drawing_manager.is_drawing() and event.button() == Qt.LeftButton:
            self.drawing_manager.add_point(canvas_point.x(), canvas_point.y())
            self.update()
            return True

        # Handle point selection (when not drawing)
        if event.button() == Qt.LeftButton and not self.drawing_manager.is_drawing():
            if self.drawing_manager.select_point_at_position(canvas_point):
                self.update()
                return True

        # Handle drawing completion
        if event.button() == Qt.RightButton and self.drawing_manager.is_drawing():
            self._finish_or_cancel_drawing()
            return True

        return False

    def _handle_general_press(self, event, canvas_point):
        """Handle general interaction (zone selection)"""
        if event.button() == Qt.LeftButton and not self.pan_with_left_button:
            self.select_shape_at_point(canvas_point)
            self.update()

    def _handle_panning_release(self):
        """Handle mouse release for panning"""
        if self.panning:
            self.panning = False
            cursor = Qt.OpenHandCursor if self.space_pressed or self.pan_with_left_button else Qt.ArrowCursor
            self.setCursor(cursor)
            return True
        return False

    def _handle_point_drag_release(self, event):
        """Handle mouse release for point dragging"""
        if event.button() == Qt.LeftButton:
            canvas_point = self._get_canvas_point(event.pos())

            if self.drawing_manager.end_point_drag(canvas_point):
                self._update_zone_area_after_drag()
                self.zones_modified.emit()
                self.update()
                return True
        return False

    def _update_zone_area_after_drag(self):
        """Update zone area after point dragging"""
        zone_idx = self.drawing_manager.selected_point_zone
        if (zone_idx is not None and 0 <= zone_idx < len(self.zones) and
                'points' in self.zones[zone_idx]):
            area = self.calculate_area(self.zones[zone_idx]['points'])
            self.zones[zone_idx]['area'] = area
            self.logger.debug(f"Updated zone area after drag: {area:.2f} sq ft")

    def _handle_panning_move(self, event):
        """Handle mouse move for panning"""
        if self.panning:
            delta_x = event.pos().x() - self.last_mouse_pos.x()
            delta_y = event.pos().y() - self.last_mouse_pos.y()

            scroll_area = self.parent().parent()
            h_value = scroll_area.horizontalScrollBar().value() - delta_x
            v_value = scroll_area.verticalScrollBar().value() - delta_y

            scroll_area.horizontalScrollBar().setValue(h_value)
            scroll_area.verticalScrollBar().setValue(v_value)

            self.last_mouse_pos = event.pos()
            return True
        return False

    def _update_cursor_state(self, event):
        """Update cursor based on current state"""
        if self.space_pressed and not self.is_in_drawing_mode():
            self.setCursor(Qt.OpenHandCursor)

    def _handle_interaction_move(self, event):
        """Handle mouse move for drawing/dragging interactions"""
        canvas_point = self._get_canvas_point(event.pos())

        # Update drawing manager
        self.drawing_manager.set_mouse_position(canvas_point)

        # Handle point dragging
        if self.drawing_manager.is_dragging_point():
            self.drawing_manager.drag_point_to(canvas_point.x(), canvas_point.y())
            self.update()
            return

        # Update for drawing/calibration modes
        if self.drawing_manager.is_drawing() or self.scale_manager.is_calibrating():
            self.update()

    def _handle_calibration_click(self, point):
        """Handle calibration click events"""
        try:
            if self.scale_manager.add_calibration_point(point.x(), point.y()):
                # We have two points, prompt for real-world length
                dlg = QInputDialog(self)
                dlg.setWindowTitle("Enter Real Length")
                dlg.setLabelText("Enter the real-world length between your two points (in feet):")
                dlg.setInputMode(QInputDialog.DoubleInput)
                dlg.setDoubleMinimum(0.1)
                dlg.setDoubleMaximum(1000.0)
                dlg.setDoubleValue(3.0)
                dlg.setDoubleDecimals(2)
                dlg.setStyleSheet(f"""
                    QDialog {{ background-color: {Colors.WHITE}; color: {Colors.TEXT_PRIMARY}; }}
                    QLabel {{ color: {Colors.TEXT_PRIMARY}; }}
                    QLineEdit, QSpinBox, QDoubleSpinBox {{
                        color: {Colors.TEXT_PRIMARY}; background-color: {Colors.WHITE};
                        border: 1px solid {Colors.BORDER_MEDIUM}; border-radius: 3px; padding: 3px 6px;
                    }}
                    QPushButton {{
                        color: {Colors.GRAY_800}; background-color: {Colors.GRAY_200};
                        border: 1px solid {Colors.GRAY_300}; border-radius: 4px; padding: 4px 12px;
                    }}
                    QPushButton:hover {{ background-color: {Colors.GRAY_300}; }}
                """)
                ok = dlg.exec()
                real_length = dlg.doubleValue()

                if ok:
                    self.scale_manager.calculate_scale_from_calibration(real_length)
                    self._emit_calibration_signals()
                    self.update()
                else:
                    self.scale_manager.cancel_calibration()

                self.setCursor(Qt.ArrowCursor)
            else:
                self.update()

        except Exception as e:
            self.logger.error(f"Error handling calibration click: {e}", exc_info=True)
            self.scale_manager.cancel_calibration()
            self.setCursor(Qt.ArrowCursor)

    def _emit_calibration_signals(self):
        """Emit signals after calibration completion"""
        # Find parent that can emit zones_modified signal
        parent_view = self.parent()
        while parent_view and not hasattr(parent_view, 'zones_modified'):
            parent_view = parent_view.parent()

        if parent_view and hasattr(parent_view, 'zones_modified'):
            parent_view.zones_modified.emit()
            self.logger.debug("Emitted zones_modified signal after scale calibration")

        # Update properties panel
        zones_tab = self._find_zones_tab()
        if zones_tab and hasattr(zones_tab, 'update_properties_panel'):
            zones_tab.update_properties_panel()
            self.logger.debug("Updated properties panel after scale calibration")

    def _finish_or_cancel_drawing(self):
        """Finish or cancel the current drawing operation"""
        try:
            if len(self.drawing_manager.current_points) >= 3:
                # Finish the shape
                success, new_item_index = self.drawing_manager.finish_drawing()

                if success:
                    # Update selection
                    self.selected_zone_index = new_item_index
                    self.logger.info(f"Finished drawing zone: index {new_item_index}, zone count: {len(self.zones)}")

                    # Calculate area for the newly created zone
                    if 0 <= new_item_index < len(self.zones) and 'points' in self.zones[new_item_index]:
                        self._calculate_new_zone_area(new_item_index)

                    # Emit signals
                    self._emit_drawing_completion_signals(new_item_index)
                else:
                    self.logger.debug("Failed to finish drawing zone")
            else:
                # Cancel drawing if not enough points
                self.drawing_manager.cancel_drawing()
                self.logger.debug("Drawing canceled (not enough points)")

            # Reset cursor and update
            self.setCursor(Qt.ArrowCursor)
            self.update()

        except Exception as e:
            self.logger.error(f"Error finishing/canceling drawing: {e}", exc_info=True)
            self.drawing_manager.cancel_drawing()
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def _calculate_new_zone_area(self, zone_index):
        """Calculate area for a newly created zone"""
        try:
            points = self.zones[zone_index]['points']

            # Only calculate area if scale is calibrated
            if self.scale_manager.is_calibrated():
                area_pixels = calculate_polygon_area(points)
                area_sqft = self.scale_manager.square_pixels_to_square_feet(area_pixels)
                self.zones[zone_index]['area'] = round(area_sqft, 2)
                self.logger.info(f"Calculated area for zone {zone_index}: {area_sqft:.2f} sq ft")
            else:
                # Set area to None when scale is not calibrated
                self.zones[zone_index]['area'] = None
                self.logger.info(f"Scale not calibrated, area set to None for zone {zone_index}")

        except Exception as e:
            self.logger.error(f"Error calculating new zone area: {e}", exc_info=True)

    def _emit_drawing_completion_signals(self, new_item_index):
        """Emit signals after completing zone drawing"""
        try:
            # Find parent that has zones_modified signal
            signal_parent = self._find_signal_parent('zones_modified')
            if signal_parent:
                signal_parent.zones_modified.emit()
                self.logger.debug("Emitted zones_modified signal")

            # Find parent that has selection_changed signal
            signal_parent = self._find_signal_parent('selection_changed')
            if signal_parent:
                signal_parent.selection_changed.emit()
                self.logger.debug("Emitted selection_changed signal")

            # Update properties panel
            zones_tab = self._find_zones_tab()
            if zones_tab:
                zones_tab.update_properties_panel(new_item_index)
                self.logger.debug(f"Called zones_tab.update_properties_panel({new_item_index})")
            else:
                self.logger.warning("Could not find zones_tab to update properties panel")

        except Exception as e:
            self.logger.error(f"Error emitting drawing completion signals: {e}", exc_info=True)

    def _find_signal_parent(self, signal_name):
        """Find parent that has a specific signal"""
        current = self
        while current:
            if (hasattr(current, signal_name) and
                    callable(getattr(getattr(current, signal_name), 'emit', None))):
                return current
            if hasattr(current, 'parent') and callable(current.parent):
                current = current.parent()
            else:
                break
        return None

    # ==================== KEYBOARD EVENT HELPER METHODS ====================

    def _handle_pan_key_press(self, event):
        """Handle spacebar press for pan mode"""
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.space_pressed = True
            if not self.is_in_drawing_mode():
                self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return True
        return False

    def _handle_zoom_shortcuts(self, event):
        """Handle zoom keyboard shortcuts"""
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Plus:
                self.zoom_in()
                event.accept()
                return True
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
                event.accept()
                return True
            elif event.key() == Qt.Key_0:
                self.reset_zoom()
                event.accept()
                return True
            elif event.key() == Qt.Key_F:
                self.fit_to_view()
                event.accept()
                return True
        return False

    def _handle_grid_shortcuts(self, event):
        """Handle grid-related keyboard shortcuts"""
        if event.key() == Qt.Key_G:
            self.grid_manager.toggle_grid()
            self.update()
            self.logger.debug(f"Grid toggled with G key, now: {self.grid_manager.is_visible()}")
            event.accept()
            return True

        if event.key() == Qt.Key_S:
            if self.grid_manager.is_visible():
                self.grid_manager.toggle_snap()
                self.logger.debug(f"Snap toggled with S key, now: {self.grid_manager.is_snap_enabled()}")
            else:
                self.logger.debug("Cannot toggle snap: grid is not visible")
            event.accept()
            return True

        return False

    def _handle_mode_cancellation(self, event):
        """Handle Escape key for canceling modes"""
        if event.key() == Qt.Key_Escape:
            if self.drawing_manager.is_drawing():
                self.cancel_drawing()
                self.logger.debug("Drawing canceled with Escape key")
                event.accept()
                return True
            elif self.scale_manager.is_calibrating():
                self.scale_manager.cancel_calibration()
                self.setCursor(Qt.ArrowCursor)
                self.update()
                self.logger.debug("Calibration canceled with Escape key")
                event.accept()
                return True
        return False

    def _handle_other_shortcuts(self, event):
        """Handle other keyboard shortcuts"""
        # Delete key
        if event.key() == Qt.Key_Delete:
            if self.selected_zone_index is not None:
                self.delete_selected_zone()
                self.logger.debug("Zone deleted with Delete key")
                event.accept()
                return True

        # Undo: works both while drawing and while editing zone points
        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if self.drawing_manager.undo_last_action():
                self.update()
                event.accept()
                return True

        return False

    def _handle_space_release(self):
        """Handle spacebar release"""
        self.space_pressed = False
        if not self.is_in_drawing_mode() and not self.pan_with_left_button:
            self.setCursor(Qt.ArrowCursor)

    # ==================== WHEEL EVENT HELPER METHODS ====================

    def _is_mouse_wheel_zoom(self, event):
        """Determine if wheel event should be used for zooming"""
        is_mouse_wheel = (abs(event.angleDelta().y()) > 0 and
                          event.angleDelta().x() == 0 and
                          abs(event.angleDelta().y()) >= 120)
        return is_mouse_wheel or event.modifiers() & Qt.AltModifier

    def _handle_scroll_wheel(self, event):
        """Handle wheel event for scrolling (trackpad)"""
        scroll_area = self.parent().parent()
        h_delta = event.angleDelta().x()
        v_delta = event.angleDelta().y()

        if v_delta != 0:
            scroll_area.verticalScrollBar().setValue(
                scroll_area.verticalScrollBar().value() - v_delta
            )

        if h_delta != 0:
            scroll_area.horizontalScrollBar().setValue(
                scroll_area.horizontalScrollBar().value() - h_delta
            )

    def _handle_zoom_wheel(self, event):
        """Handle zooming with mouse wheel"""
        try:
            # Get mouse position before zoom
            mouse_pos = event.pos()
            view_center_x = mouse_pos.x()
            view_center_y = mouse_pos.y()

            # Calculate zoom center in scene coordinates
            scene_center_x, scene_center_y = self.transform_point(QPoint(view_center_x, view_center_y))

            # Calculate new zoom factor
            delta = event.angleDelta().y()
            zoom_change = self.zoom_increment * (1 if delta > 0 else -1)
            new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom_factor + zoom_change))

            # Apply zoom
            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom
            self.update_canvas_size()

            # Adjust scroll position to keep point under mouse
            new_view_center_x = scene_center_x * self.zoom_factor
            new_view_center_y = scene_center_y * self.zoom_factor

            scroll_area = self.parent().parent()
            delta_x = new_view_center_x - view_center_x
            delta_y = new_view_center_y - view_center_y

            scroll_area.horizontalScrollBar().setValue(
                scroll_area.horizontalScrollBar().value() + int(delta_x)
            )
            scroll_area.verticalScrollBar().setValue(
                scroll_area.verticalScrollBar().value() + int(delta_y)
            )

            self.update()
            self.logger.debug(f"Zoomed from {old_zoom:.2f} to {self.zoom_factor:.2f}")

        except Exception as e:
            self.logger.error(f"Error handling zoom wheel: {e}", exc_info=True)

    # ==================== ZOOM CONTROL METHODS ====================

    def zoom_in(self):
        """Zoom in by one step"""
        try:
            new_zoom = min(self.zoom_factor + self.zoom_increment, self.max_zoom)
            self._apply_zoom_with_center_lock(new_zoom)
            self.logger.debug(f"Zoomed in to {new_zoom:.2f}")
        except Exception as e:
            self.logger.error(f"Error in zoom_in: {e}", exc_info=True)

    def zoom_out(self):
        """Zoom out by one step"""
        try:
            new_zoom = max(self.zoom_factor - self.zoom_increment, self.min_zoom)
            self._apply_zoom_with_center_lock(new_zoom)
            self.logger.debug(f"Zoomed out to {new_zoom:.2f}")
        except Exception as e:
            self.logger.error(f"Error in zoom_out: {e}", exc_info=True)

    def reset_zoom(self):
        """Reset zoom to 100%"""
        try:
            self._apply_zoom_with_center_lock(1.0)
            self.logger.debug("Reset zoom to 1.00")
        except Exception as e:
            self.logger.error(f"Error in reset_zoom: {e}", exc_info=True)

    def fit_to_view(self):
        """Fit all content to the viewport.

        If there is no content (no floorplan, no zones) the zoom resets to
        100 % so the canvas doesn't jump to a nonsensical level.
        If content exists the zoom is chosen so that all of it is visible;
        it may go above or below 100 % depending on content size.
        """
        try:
            scroll_area = self.parent().parent()
            viewport_width = scroll_area.viewport().width()
            viewport_height = scroll_area.viewport().height()

            content_width, content_height = self._calculate_content_bounds()

            if content_width <= 0 or content_height <= 0:
                # No real content — reset to 100 %
                new_zoom = 1.0
            else:
                zoom_x = viewport_width / content_width
                zoom_y = viewport_height / content_height
                # Never zoom IN past 100 % — fit only zooms OUT to show large content.
                # A floorplan bigger than the viewport will zoom out below 100 %;
                # small zones on a big empty canvas stay at 100 %.
                new_zoom = max(self.min_zoom, min(1.0, min(zoom_x, zoom_y)))

            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom
            self.update_canvas_size()

            # Scroll to top-left so content is visible from the origin
            scroll_area.horizontalScrollBar().setValue(0)
            scroll_area.verticalScrollBar().setValue(0)

            self.update()
            self.zoom_changed.emit(self.zoom_factor)
            self.logger.debug(f"Fit to view: zoom {old_zoom:.2f} → {new_zoom:.2f}")

        except Exception as e:
            self.logger.error(f"Error in fit_to_view: {e}", exc_info=True)

    def _apply_zoom_with_center_lock(self, new_zoom):
        """Apply zoom while keeping viewport center locked"""
        try:
            scroll_area = self.parent().parent()
            viewport_width = scroll_area.viewport().width()
            viewport_height = scroll_area.viewport().height()
            viewport_center_x = viewport_width // 2
            viewport_center_y = viewport_height // 2

            # Get current scroll positions
            h_value = scroll_area.horizontalScrollBar().value()
            v_value = scroll_area.verticalScrollBar().value()

            # Calculate center point in canvas coordinates
            center_x = (h_value + viewport_center_x) / self.zoom_factor
            center_y = (v_value + viewport_center_y) / self.zoom_factor

            # Apply new zoom
            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom
            self.update_canvas_size()

            # Calculate new scroll positions to keep center
            new_h_value = center_x * new_zoom - viewport_center_x
            new_v_value = center_y * new_zoom - viewport_center_y

            scroll_area.horizontalScrollBar().setValue(int(new_h_value))
            scroll_area.verticalScrollBar().setValue(int(new_v_value))

            self.update()
            self.zoom_changed.emit(self.zoom_factor)

        except Exception as e:
            self.logger.error(f"Error applying zoom with center lock: {e}", exc_info=True)

    def _calculate_content_bounds(self):
        """Return the pixel extent of real content at 1× zoom.

        IMPORTANT: self.width()/self.height() must NOT be used here —
        the canvas widget is resized proportionally to the zoom factor, so
        at 200 % zoom self.width() is roughly twice the viewport width.
        Using it as a lower bound would make 'Fit' zoom way out after
        zooming in.  Instead we measure only the actual content pixels.

        Returns (0, 0) when there is no content so the caller can reset
        to 100 % rather than producing an undefined zoom.
        """
        content_width = 0
        content_height = 0

        # Floorplan image (dimensions are stored at 1× zoom)
        if self.background_manager.has_background():
            bg_width, bg_height = self.background_manager.get_background_size()
            content_width = max(content_width, bg_width)
            content_height = max(content_height, bg_height)

        # Zone extents (canvas coordinates = pixels at 1× zoom)
        for zone in self.zones:
            if 'points' in zone and zone['points']:
                for x, y in zone['points']:
                    content_width = max(content_width, x)
                    content_height = max(content_height, y)

        # Add comfortable padding only when there is real content
        if content_width > 0 or content_height > 0:
            content_width += 40
            content_height += 40

        return content_width, content_height

    def cancel_drawing(self):
        """Cancel current drawing operation"""
        try:
            self.drawing_manager.cancel_drawing()
            self.setCursor(Qt.ArrowCursor)
            self.update()
            self.logger.debug("Drawing operation canceled")
        except Exception as e:
            self.logger.error(f"Error canceling drawing: {e}", exc_info=True)