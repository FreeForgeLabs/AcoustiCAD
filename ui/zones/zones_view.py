import logging
import os
import time
from PySide6.QtWidgets import QScrollArea, QInputDialog
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QImage
from .zones_canvas import ZonesCanvas


class ZonesView(QScrollArea):
    """
    Scroll area container for the zones canvas with properly separated signals
    """

    # SEMANTIC SIGNAL SEPARATION
    selection_changed = Signal()  # Zone selection changed
    zones_modified = Signal()  # USER modifications (need saving)
    zones_refreshed = Signal()  # Data loaded/refreshed (UI update only)
    zones_structure_changed = Signal()  # Zone count/structure changed (for UI rebuilding)

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)

        # Loading context flags
        self._loading_project = False  # Flag to prevent modification signals during loading
        self._in_data_operation = False  # Flag for non-user data operations

        # Initialize canvas with scale manager
        self.canvas = ZonesCanvas(project_manager.get_scale_manager(), self)
        self.setWidget(self.canvas)

        # Configure scroll area
        self._configure_scroll_area()

        # Connect canvas signals to our signals
        self._connect_canvas_signals()


    def _configure_scroll_area(self):
        """Configure scroll area properties"""
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignCenter)
        self.setFrameShape(QScrollArea.NoFrame)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setMouseTracking(True)
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(Qt.WheelFocus)

        # Enable touch events
        self.viewport().setAttribute(Qt.WA_AcceptTouchEvents)
        self.setAttribute(Qt.WA_AcceptTouchEvents)

    def _connect_canvas_signals(self):
        """Connect canvas signals with proper semantic routing"""
        # Canvas selection changes always propagate
        self.canvas.selection_changed.connect(self.selection_changed.emit)

        # Canvas zone modifications - route based on context
        self.canvas.zones_modified.connect(self._handle_canvas_zones_modified)

    def _handle_canvas_zones_modified(self):
        """Route canvas modification signals based on loading context"""
        if self._loading_project or self._in_data_operation:
            # During project loading or data operations, this is a refresh, not a modification
            self.zones_refreshed.emit()
            self.logger.debug("Emitted zones_refreshed (data operation context)")
        else:
            # Normal user modification
            self.zones_modified.emit()
            self.logger.debug("Emitted zones_modified (user action)")

    # ==================== PROPERTY FORWARDING ====================

    @property
    def zones(self):
        """Get zones from canvas"""
        return self.canvas.zones

    @zones.setter
    def zones(self, value):
        """Set zones on canvas"""
        self.canvas.zones = value

    @property
    def selected_zone_index(self):
        """Get selected zone index from canvas"""
        return self.canvas.selected_zone_index

    @selected_zone_index.setter
    def selected_zone_index(self, value):
        """Set selected zone index on canvas"""
        self.canvas.selected_zone_index = value

    @property
    def background_manager(self):
        """Get background manager from canvas"""
        return self.canvas.background_manager

    @property
    def drawing_manager(self):
        """Get drawing manager from canvas"""
        return self.canvas.drawing_manager

    @property
    def scale_manager(self):
        """Get scale manager from project manager"""
        return self.project_manager.get_scale_manager()

    # ==================== BACKGROUND MANAGEMENT (NO AUTO-EMIT) ====================

    def load_background(self, image_path):
        """Load a background image - NO automatic signal emission"""
        try:
            if not image_path or not os.path.exists(image_path):
                self.logger.warning(f"Invalid background image path: {image_path}")
                return False

            result = self.canvas.background_manager.load_background(image_path)
            if not result:
                self.logger.warning(f"Failed to load background image: {image_path}")
                return False

            # Update UI but don't emit modification signals
            self.fit_to_view()
            self.canvas.update_canvas_size()
            self.canvas.update()

            self.logger.info(f"Background image loaded: {image_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading background: {e}", exc_info=True)
            return False

    def clear_background(self):
        """Clear the background image - NO automatic signal emission"""
        try:
            result = self.canvas.background_manager.clear_background()
            if result:
                self.canvas.zoom_factor = 1.0
                self.canvas.update_canvas_size()
                self.canvas.update()
                self.logger.info("Background cleared")
            return result
        except Exception as e:
            self.logger.error(f"Error clearing background: {e}", exc_info=True)
            return False

    def clear_all(self):
        """Clear all content (background, zones, scale) - NO automatic signal emission"""
        try:
            # Set flag to prevent modification signals during clearing
            self._in_data_operation = True

            self.canvas.background_manager.clear_background()
            self.canvas.zones = []
            self.canvas.selected_zone_index = None
            self.canvas.drawing_manager.cancel_drawing()

            # Reset scale to default
            self.canvas.scale_manager.reset_to_default()

            # Reset zoom
            self.canvas.zoom_factor = 1.0
            self.canvas.update_canvas_size()
            self.canvas.update()

            self.logger.info("All content cleared")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing all content: {e}", exc_info=True)
            return False
        finally:
            self._in_data_operation = False

    # ==================== SCALE CALIBRATION ====================

    def start_calibration(self):
        """Start scale calibration process"""
        try:
            if not self.canvas.background_manager.has_background():
                from ui.dialogs.alert_dialog import AlertDialog
                AlertDialog.show_warning(self, "No Floorplan",
                                         "Please load a floorplan image before calibrating the scale.")
                return False

            result = self.canvas.scale_manager.start_calibration()
            if result:
                self.canvas.setCursor(Qt.CrossCursor)
                self.logger.info("Started calibration mode")
                from ui.dialogs.alert_dialog import AlertDialog
                AlertDialog.show_info(self, "Calibrate Scale",
                                      "Click on two points of known distance on the image.\n\n"
                                      "You will then be prompted to enter the real-world distance between those points.")
            return result

        except Exception as e:
            self.logger.error(f"Error starting calibration: {e}", exc_info=True)
            return False

    # ==================== GRID AND VISUAL CONTROLS ====================

    def toggle_grid(self):
        """Toggle grid visibility"""
        return self.canvas.toggle_grid()

    def toggle_snap(self):
        """Toggle grid snapping"""
        return self.canvas.toggle_snap()

    def set_grid_size(self, size):
        """Set grid size"""
        return self.canvas.set_grid_size(size)

    def set_line_color(self, color):
        """Set drawing line color"""
        return self.canvas.set_line_color(color)

    def is_grid_visible(self):
        """Check if grid is visible"""
        if hasattr(self.canvas, 'grid_manager'):
            return self.canvas.grid_manager.is_visible()
        return False

    def is_snap_enabled(self):
        """Check if grid snapping is enabled"""
        if hasattr(self.canvas, 'grid_manager'):
            return self.canvas.grid_manager.is_snap_enabled()
        return False

    def get_grid_size(self):
        """Get current grid size"""
        if hasattr(self.canvas, 'grid_manager'):
            return self.canvas.grid_manager.get_grid_size()
        return 10

    # ==================== ZOOM CONTROLS ====================

    def zoom_in(self):
        """Zoom in by one step"""
        self.canvas.zoom_in()

    def zoom_out(self):
        """Zoom out by one step"""
        self.canvas.zoom_out()

    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.canvas.reset_zoom()

    def fit_to_view(self):
        """Fit content to view"""
        self.canvas.fit_to_view()

    # ==================== ZONE CREATION ====================

    def create_rectangle_zone(self, zone_data):
        """Create a rectangular zone from zone data - USER ACTION"""
        try:
            # Extract dimensions
            length_ft = float(zone_data.get('length', 10.0))
            width_ft = float(zone_data.get('width', 10.0))

            # Validate dimensions against scale
            scale_factor = self.canvas.scale_manager.get_scale_factor()
            if not self.canvas.scale_manager.is_calibrated():  # Default scale - warn user
                from ui.dialogs.confirm_dialog import ConfirmDialog
                proceed = ConfirmDialog.ask(
                    self, "Scale Not Calibrated",
                    "The scale has not been calibrated yet. Zone dimensions may not be accurate.\n\n"
                    "Continue adding the zone anyway?",
                    confirm_text="Add Zone",
                    cancel_text="Cancel",
                )
                if not proceed:
                    return -1

            # Convert to pixels using scale
            length_px = length_ft * scale_factor
            width_px = width_ft * scale_factor

            self.logger.debug(f"Creating zone: {length_ft}ft x {width_ft}ft = {length_px}px x {width_px}px")

            # Find position for new zone
            pos_x, pos_y = self._find_empty_space(length_px, width_px)

            # Create rectangle points (clockwise from top-left)
            points = [
                (pos_x, pos_y),
                (pos_x + length_px, pos_y),
                (pos_x + length_px, pos_y + width_px),
                (pos_x, pos_y + width_px)
            ]

            # Create zone data
            new_zone = self._build_zone_data(zone_data, points, length_ft, width_ft)

            # Add zone
            self.zones.append(new_zone)
            self.canvas.selected_zone_index = len(self.zones) - 1

            # Update UI
            self._finalize_zone_creation()

            # Emit USER modification signals
            self.zones_modified.emit()
            self.zones_structure_changed.emit()
            self.selection_changed.emit()

            self.logger.info(f"Created rectangle zone: {new_zone['name']} with ID {new_zone['id']}")
            return len(self.zones) - 1

        except Exception as e:
            self.logger.error(f"Error creating rectangle zone: {e}", exc_info=True)
            return -1

    def _build_zone_data(self, zone_data, points, length_ft, width_ft):
        """Build complete zone data structure"""
        zone_idx = len(self.zones)
        color_index = zone_idx % len(self.canvas.drawing_manager.ZONE_COLORS)

        new_zone = {
            'id': int(time.time()),  # Unique ID for plotter tab
            'name': zone_data.get('name', f"Zone {zone_idx + 1}"),
            'room_name': zone_data.get('room_name', ''),
            'environment_type': zone_data.get('environment_type', 'enclosed'),
            'target_spl': zone_data.get('target_spl', 85.0),
            'points': points,
            'color_index': color_index,
            'length': length_ft,
            'width': width_ft,
            'area': round(length_ft * width_ft, 2)
        }

        # Add ceiling height for enclosed zones
        if zone_data.get('environment_type') == 'enclosed':
            new_zone['ceiling_height'] = zone_data.get('ceiling_height', 9.0)

        return new_zone

    def _finalize_zone_creation(self):
        """Finalize zone creation with UI updates"""
        self.canvas.update_canvas_size()
        self.update()
        self.ensure_zone_visible(len(self.zones) - 1)

    def _find_empty_space(self, length_px, width_px):
        """Find empty space for a new zone"""
        try:
            margin = 30
            x_start = 50
            y_start = 50

            # Adjust for background
            if self.canvas.background_manager.has_background():
                bg_width, bg_height = self.canvas.background_manager.get_background_size()
                x_start = bg_width + margin

            # Get occupied areas
            occupied_areas = self._get_occupied_areas()

            # Find non-overlapping position
            pos_x, pos_y = self._find_non_overlapping_position(
                x_start, y_start, length_px, width_px, margin, occupied_areas
            )

            # Ensure canvas is large enough
            self._ensure_canvas_size(pos_x, pos_y, length_px, width_px, margin)

            self.logger.debug(f"Found position for new zone: ({pos_x}, {pos_y})")
            return pos_x, pos_y

        except Exception as e:
            self.logger.error(f"Error finding empty space: {e}", exc_info=True)
            return 50, 50

    def _get_occupied_areas(self):
        """Get list of occupied areas from existing zones"""
        occupied_areas = []
        for zone in self.zones:
            if 'points' not in zone or not zone['points']:
                continue

            # Find bounding box of existing zone
            min_x = min(p[0] for p in zone['points'])
            max_x = max(p[0] for p in zone['points'])
            min_y = min(p[1] for p in zone['points'])
            max_y = max(p[1] for p in zone['points'])

            occupied_areas.append((min_x, min_y, max_x, max_y))

        return occupied_areas

    def _find_non_overlapping_position(self, x_start, y_start, length_px, width_px, margin, occupied_areas):
        """Find a position that doesn't overlap with existing zones"""
        pos_x = x_start
        pos_y = y_start
        max_attempts = 100

        for attempt in range(max_attempts):
            # Calculate zone boundaries at current position
            zone_left = pos_x
            zone_top = pos_y
            zone_right = pos_x + length_px
            zone_bottom = pos_y + width_px

            # Check for overlap
            overlap = False
            for left, top, right, bottom in occupied_areas:
                if not (zone_right < left or zone_left > right or
                        zone_bottom < top or zone_top > bottom):
                    overlap = True
                    break

            if not overlap:
                return pos_x, pos_y

            # Try next position in grid pattern
            if attempt % 4 == 0:
                pos_x += length_px + margin
            elif attempt % 4 == 1:
                pos_x = x_start
                pos_y += width_px + margin
            elif attempt % 4 == 2:
                pos_x = x_start + (length_px + margin) / 2
            else:
                pos_y += (width_px + margin) / 2

        # Fallback to default position
        self.logger.warning("Could not find non-overlapping position, using default")
        return x_start, y_start

    def _ensure_canvas_size(self, pos_x, pos_y, length_px, width_px, margin):
        """Ensure canvas is large enough for the new zone"""
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()

        new_width = max(canvas_width, pos_x + length_px + margin * 2)
        new_height = max(canvas_height, pos_y + width_px + margin * 2)

        if new_width > canvas_width or new_height > canvas_height:
            self.logger.debug(f"Expanding canvas from {canvas_width}x{canvas_height} to {new_width}x{new_height}")
            self.canvas.setMinimumSize(int(new_width), int(new_height))
            self.canvas.resize(int(new_width), int(new_height))
            self.canvas.updateGeometry()

    def ensure_zone_visible(self, zone_index):
        """Ensure a zone is visible in the viewport"""
        try:
            if zone_index < 0 or zone_index >= len(self.zones):
                return

            zone = self.zones[zone_index]
            if 'points' not in zone or not zone['points']:
                return

            # Calculate zone center
            center_x = sum(p[0] for p in zone['points']) / len(zone['points'])
            center_y = sum(p[1] for p in zone['points']) / len(zone['points'])

            # Get viewport dimensions
            viewport_width = self.viewport().width()
            viewport_height = self.viewport().height()

            # Scroll to center zone in viewport
            h_value = int(max(0, center_x - viewport_width / 2))
            v_value = int(max(0, center_y - viewport_height / 2))

            self.horizontalScrollBar().setValue(h_value)
            self.verticalScrollBar().setValue(v_value)

        except Exception as e:
            self.logger.error(f"Error ensuring zone visibility: {e}", exc_info=True)

    # ==================== DRAWING ZONES ====================

    def start_zone_drawing(self):
        """Start interactive zone drawing mode - USER ACTION"""
        try:
            self.logger.info("Starting zone drawing mode")

            # Ensure canvas has focus
            self.canvas.setFocus()

            # Clear conflicting states
            self.canvas.panning = False
            self.canvas.space_pressed = False

            # Start drawing mode
            result = self.canvas.drawing_manager.start_zone_drawing()

            if result:
                self.canvas.setCursor(Qt.CrossCursor)
                self.canvas.setMouseTracking(True)
                self.canvas.update()
                self.logger.debug("Drawing mode started successfully")
                return True
            else:
                self.logger.warning("Failed to start drawing mode")
                return False

        except Exception as e:
            self.logger.error(f"Error starting zone drawing: {e}", exc_info=True)
            return False

    # ==================== ZONE MANAGEMENT ====================

    def delete_selected_zone(self):
        """Delete the currently selected zone - USER ACTION"""
        result = self.canvas.delete_selected_zone()
        if result:
            # Emit USER modification signals
            self.zones_modified.emit()
            self.zones_structure_changed.emit()
            self.selection_changed.emit()
        return result

    def get_selected_zone(self):
        """Get the currently selected zone"""
        if (self.selected_zone_index is not None and
                0 <= self.selected_zone_index < len(self.zones)):
            return self.zones[self.selected_zone_index]
        return None

    def update_zone(self, index, data):
        """Update zone data - USER ACTION"""
        try:
            if not isinstance(index, int) or index < 0 or index >= len(self.zones):
                self.logger.warning(f"Invalid zone index for update: {index}")
                return False

            self.zones[index].update(data)
            self.logger.debug(f"Updated zone at index {index}: {data}")

            # Emit USER modification signals
            self.zones_modified.emit()
            self.canvas.update()
            return True

        except Exception as e:
            self.logger.error(f"Error updating zone: {e}", exc_info=True)
            return False

    def recalculate_zone_areas(self):
        """Recalculate all zone areas based on current scale - CALCULATION OPERATION"""
        try:
            # Set flag to indicate this is a calculation, not user modification
            self._in_data_operation = True

            scale_manager = self.canvas.scale_manager

            # Only proceed if scale is calibrated
            if not scale_manager.is_calibrated():
                self.logger.debug("Scale not calibrated, skipping area recalculation")
                return

            from core.zones.geometry_utils import calculate_polygon_area

            # Recalculate all zone areas
            for zone in self.canvas.zones:
                if 'points' in zone and zone['points'] and len(zone['points']) >= 3:
                    area_pixels = calculate_polygon_area(zone['points'])
                    area_sqft = scale_manager.square_pixels_to_square_feet(area_pixels)
                    zone['area'] = area_sqft
                    self.logger.debug(f"Updated area for zone '{zone.get('name', 'unnamed')}': {area_sqft:.2f} sq ft")

            self.update()
            # Emit refresh signal since this is a calculation update
            self.zones_refreshed.emit()
            self.logger.info("Recalculated all zone areas")

        except Exception as e:
            self.logger.error(f"Error recalculating zone areas: {e}", exc_info=True)
        finally:
            self._in_data_operation = False

    # ==================== DATA MANAGEMENT ====================

    def get_zones_data(self):
        """Get all zone data for saving"""
        try:
            # Ensure zones have calculated areas
            valid_zones = []
            for zone in self.zones:
                zone_copy = zone.copy()

                # Calculate area if needed
                if 'points' in zone_copy and zone_copy['points']:
                    zone_copy['area'] = self.canvas.calculate_area(zone_copy['points'])

                # Ensure required fields
                if 'name' not in zone_copy:
                    zone_copy['name'] = f"Zone {len(valid_zones) + 1}"

                valid_zones.append(zone_copy)

            result = {
                'scale_factor': self.scale_manager.get_scale_factor(),
                'background_path': self.background_manager.get_background_path(),
                'zones': valid_zones
            }

            self.logger.debug(f"Returning zones data with {len(valid_zones)} zones")
            return result

        except Exception as e:
            self.logger.error(f"Error getting zones data: {e}", exc_info=True)
            return {
                'scale_factor': self.canvas.scale_manager.DEFAULT_SCALE,
                'background_path': None,
                'zones': []
            }

    def to_json(self):
        """Convert zones data to JSON format"""
        return self.get_zones_data()

    def from_json(self, data):
        """Load zones data from JSON format - DATA LOADING OPERATION"""
        try:
            if not isinstance(data, dict):
                self.logger.warning(f"Invalid data format for from_json: {type(data)}")
                return False

            # Set loading flag to prevent modification signals
            self._loading_project = True

            self.logger.debug(f"Loading zones data with {len(data.get('zones', []))} zones")

            # Load scale factor
            if 'scale_factor' in data and isinstance(data['scale_factor'], (int, float)) and data['scale_factor'] > 0:
                self.scale_manager.set_scale_factor(data['scale_factor'])
                self.logger.debug(f"Loaded scale factor: {data['scale_factor']}")

            # Load background — fall back to project assets copy if original is missing
            if 'background_path' in data and data['background_path']:
                bg_path = data['background_path']
                if not os.path.exists(bg_path):
                    bg_path = self._find_background_in_assets(bg_path)
                if bg_path:
                    self.load_background(bg_path)
                    self.logger.debug(f"Loaded background from: {bg_path}")
                else:
                    self.logger.warning(f"Background file not found (original deleted, no project copy): {data['background_path']}")

            # Load zones
            if 'zones' in data and isinstance(data['zones'], list):
                self.canvas.zones = data['zones'].copy()
                self.logger.debug(f"Loaded {len(self.zones)} zones")
            else:
                self.logger.warning("No valid zones list in data")
                self.canvas.zones = []

            # Reset selection and update
            self.canvas.selected_zone_index = None
            self.canvas.update_canvas_size()
            self.canvas.update()

            # Emit single refresh signal after all loading is complete
            self.zones_refreshed.emit()
            self.zones_structure_changed.emit()

            return True

        except Exception as e:
            self.logger.error(f"Error loading from JSON: {e}", exc_info=True)
            return False
        finally:
            self._loading_project = False

    def _find_background_in_assets(self, original_path):
        """Return the path to the project's assets copy of a background, or None."""
        try:
            pm = self.project_manager if hasattr(self, 'project_manager') else None
            if not pm or not pm.current_project_id:
                return None
            storage = pm.storage if hasattr(pm, 'storage') else None
            if not storage:
                return None
            assets_dir = os.path.join(storage.projects_dir, f"{pm.current_project_id}_assets")
            ext = os.path.splitext(original_path)[1].lower() or ".png"
            candidate = os.path.join(assets_dir, f"background{ext}")
            if os.path.exists(candidate):
                self.logger.info(f"Using project assets copy of background: {candidate}")
                return candidate
            return None
        except Exception:
            return None

    # ==================== EXPORT FUNCTIONALITY ====================

    def export_to_image(self, file_path, format=None):
        """Export the current view to an image file"""
        try:
            if not file_path:
                self.logger.warning("Invalid file path for export")
                return False

            # Determine format from extension if not specified
            if not format:
                ext = os.path.splitext(file_path)[1].lower()
                format_map = {
                    '.jpg': 'jpg', '.jpeg': 'jpg',
                    '.bmp': 'bmp',
                    '.tif': 'tiff', '.tiff': 'tiff'
                }
                format = format_map.get(ext, 'png')

            # Create image and render canvas
            image = QImage(self.canvas.size(), QImage.Format_ARGB32)
            image.fill(Qt.white)

            from PySide6.QtGui import QPainter
            painter = QPainter(image)
            try:
                self.canvas.render(painter)
            finally:
                painter.end()

            # Set quality for JPG
            quality = 95 if format.lower() in ['jpg', 'jpeg'] else -1

            result = image.save(file_path, format.upper(), quality)

            if result:
                self.logger.info(f"Image exported to: {file_path} in {format} format")
            else:
                self.logger.warning(f"Failed to save image to: {file_path}")

            return result

        except Exception as e:
            self.logger.error(f"Error exporting to image: {e}", exc_info=True)
            return False

    def export_to_pdf(self, file_path):
        """Export the current view to a PDF file"""
        try:
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QPainter

            # Create high-resolution printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setResolution(1200)

            # Set orientation based on content aspect ratio
            if self.canvas.width() > self.canvas.height():
                printer.setOrientation(QPrinter.Landscape)
            else:
                printer.setOrientation(QPrinter.Portrait)

            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(5, 5, 5, 5, QPrinter.Millimeter)

            # Get printer rectangle
            printer_rect = printer.pageRect(QPrinter.DevicePixel)

            # Create painter
            painter = QPainter()
            if not painter.begin(printer):
                self.logger.error("Failed to begin painting on printer")
                return False

            # Calculate scaling to fit content
            scale_x = printer_rect.width() / self.canvas.width()
            scale_y = printer_rect.height() / self.canvas.height()
            scale = min(scale_x, scale_y) * 0.95

            # Apply scaling and render
            painter.save()
            painter.scale(scale, scale)
            self.canvas.render(painter)
            painter.restore()
            painter.end()

            self.logger.info(f"PDF exported successfully to: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to PDF: {e}", exc_info=True)
            return False

    # ==================== EVENT FORWARDING ====================

    def keyPressEvent(self, event):
        """Forward key press events to canvas"""
        self.canvas.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Forward key release events to canvas"""
        self.canvas.keyReleaseEvent(event)

    def mousePressEvent(self, event):
        """Forward mouse press events to canvas"""
        self.canvas.mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        """Forward mouse release events to canvas"""
        self.canvas.mouseReleaseEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        """Forward mouse move events to canvas"""
        self.canvas.mouseMoveEvent(event)
        event.accept()