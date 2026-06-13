import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QBrush


class DrawingManager:
    """Manages drawing operations for the zones view"""

    # Colors for zones
    ZONE_COLORS = [
        QColor(200, 255, 200, 100),  # Light green
        QColor(200, 200, 255, 100),  # Light blue
        QColor(255, 200, 200, 100),  # Light red
        QColor(255, 255, 200, 100),  # Light yellow
        QColor(255, 230, 200, 100),  # Light orange
        QColor(240, 200, 240, 100),  # Light purple
    ]

    def __init__(self, scale_manager, parent_view, on_zone_created=None):
        self.scale_manager = scale_manager
        self.parent_view = parent_view
        self.on_zone_created = on_zone_created  # callable(); called after a zone is committed
        self.drawing_zone = False
        self.current_points = []
        self.mouse_pos = None
        self.selected_point_index = None
        self.selected_point_zone = None
        self.is_dragging = False
        self._drag_origin = None  # Original position before a drag starts
        self.undo_stack = []
        self.logger = logging.getLogger(__name__)
        self.logger.debug("DrawingManager initialized")

        # Drawing line properties (new)
        self.line_color = QColor(0, 128, 255)  # Default to blue instead of black
        self.line_width = 2
        self.line_style = Qt.DashLine

        # Hover point tracking (new)
        self.hover_point_index = None
        self.hover_point_zone = None

    def is_drawing(self):
        try:
            return self.drawing_zone
        except Exception as e:
            self.logger.error(f"Error in is_drawing: {e}")
            return False

    def set_mouse_position(self, pos):
        if pos is None:
            self.logger.warning("Cannot set mouse position: pos is None")
            return

        self.mouse_pos = (pos.x(), pos.y())

        # Check for hover point when not dragging
        if not self.is_dragging and not self.drawing_zone:
            self._update_hover_point(pos)

    def _update_hover_point(self, pos):
        """
        Check if mouse is hovering over a point and update hover state

        Args:
            pos: Mouse position
        """
        try:
            x, y = pos.x(), pos.y()
            selection_radius = 8  # Larger selection radius for easier point selection

            # Reset hover state
            old_hover_index = self.hover_point_index
            old_hover_zone = self.hover_point_zone
            self.hover_point_index = None
            self.hover_point_zone = None

            # Look through all zone points
            for zone_idx, zone in enumerate(self.parent_view.zones):
                if 'points' not in zone or not zone['points']:
                    continue

                for point_idx, point in enumerate(zone['points']):
                    if abs(x - point[0]) <= selection_radius and abs(y - point[1]) <= selection_radius:
                        self.hover_point_index = point_idx
                        self.hover_point_zone = zone_idx
                        break

                if self.hover_point_index is not None:
                    break

            # Request update if hover state changed
            if (old_hover_index != self.hover_point_index or
                    old_hover_zone != self.hover_point_zone):
                if self.parent_view and hasattr(self.parent_view, 'update'):
                    self.parent_view.update()

        except Exception as e:
            self.logger.error(f"Error updating hover point: {e}")

    def start_zone_drawing(self, room_index=None):
        try:
            # Reset state
            self.drawing_zone = True  # This is the key flag that determines if we're in drawing mode
            self.current_points = []
            self.selected_point_index = None
            self.selected_point_zone = None
            self.is_dragging = False
            self.undo_stack = []

            # Add more logging to help debug
            self.logger.info("Started zone drawing mode")
            self.logger.debug(f"Drawing zone flag set to: {self.drawing_zone}")

            # Return success
            return True
        except Exception as e:
            self.logger.error(f"Error starting zone drawing: {e}")
            # Make sure drawing_zone is False on error
            self.drawing_zone = False
            return False

    def add_point(self, x, y):
        try:
            # Simple validation with detailed logging
            if not self.drawing_zone:
                self.logger.warning("Cannot add point: not in drawing mode")
                return

            if x is None or y is None:
                self.logger.warning(f"Cannot add point: invalid coordinates ({x}, {y})")
                return

            # Apply grid snapping if enabled
            if (hasattr(self.parent_view, 'grid_manager') and
                    self.parent_view.grid_manager.is_snap_enabled()):
                x, y = self.parent_view.grid_manager.snap_to_grid(x, y)
                self.logger.debug(f"Snapped point to grid: ({x}, {y})")

            # Add the point
            self.current_points.append((float(x), float(y)))
            self.logger.info(f"Added point at ({x}, {y}), total points: {len(self.current_points)}")

            # Save for undo
            self.undo_stack.append(("add_point", len(self.current_points) - 1))

            # Request a refresh of the parent view if available
            if self.parent_view and hasattr(self.parent_view, 'update'):
                self.parent_view.update()

        except Exception as e:
            self.logger.error(f"Error adding point: {e}", exc_info=True)

    def finish_drawing(self):
        """
        Finish the current drawing

        Returns:
            tuple: (success, index) - success is a boolean, index is the index of the new zone
        """
        # Need at least 3 points to make a polygon
        if len(self.current_points) < 3:
            self.logger.warning("Cannot finish drawing: need at least 3 points")
            return False, None

        try:
            if self.drawing_zone:
                # Create a new zone
                import uuid
                new_zone = {
                    'id': str(uuid.uuid4()),
                    'name': f"Zone {len(self.parent_view.zones) + 1}",
                    'room_name': '',  # Empty room name by default
                    'points': self.current_points.copy(),
                    'target_spl': 85.0,
                    'ceiling_height': 9.0,  # Default ceiling height
                    'color_index': len(self.parent_view.zones) % len(self.ZONE_COLORS)
                }

                # Calculate area using scale manager
                try:
                    from core.zones.geometry_utils import calculate_polygon_area

                    # Calculate pixel area
                    area_pixels = calculate_polygon_area(self.current_points)

                    # Check if scale has been calibrated (not using default)
                    if self.scale_manager.is_calibrated():
                        # Scale is calibrated, calculate real area
                        area_sqft = self.scale_manager.square_pixels_to_square_feet(area_pixels)
                        new_zone['area'] = area_sqft
                        self.logger.debug(f"Calculated area for new zone: {area_sqft:.2f} sq ft")
                    else:
                        # Using default scale, store None to indicate uncalibrated
                        new_zone['area'] = None
                        self.logger.debug("Scale not calibrated, area set to None")

                except Exception as e:
                    self.logger.error(f"Error calculating zone area: {e}", exc_info=True)

                # Add the zone
                self.parent_view.zones.append(new_zone)
                new_index = len(self.parent_view.zones) - 1
                self.logger.info(f"Finished drawing zone: index {new_index}, points: {len(self.current_points)}")

                # Reset drawing state
                self.drawing_zone = False
                self.current_points = []

                # Notify owner that a zone was committed
                if self.on_zone_created:
                    self.on_zone_created()

                # Return the index of the new zone
                return True, new_index

            self.logger.warning("Finish drawing called but not in drawing mode")
            return False, None

        except Exception as e:
            self.logger.error(f"Error finishing drawing: {e}")
            # Ensure we exit drawing mode even on error
            self.drawing_zone = False
            self.current_points = []
            return False, None

    def cancel_drawing(self):
        try:
            was_drawing = self.drawing_zone
            self.drawing_zone = False
            self.current_points = []
            self.undo_stack = []

            if was_drawing:
                self.logger.info("Drawing cancelled")

            return True

        except Exception as e:
            self.logger.error(f"Error cancelling drawing: {e}")
            return False

    def draw(self, painter):
        """
        Draw the current drawing elements

        Args:
            painter: The QPainter to draw on
        """
        if not painter:
            return

        if not self.current_points:
            return

        try:
            # Draw current points and lines
            pen = QPen(self.line_color, self.line_width, self.line_style)
            painter.setPen(pen)

            # Draw lines between points
            for i in range(len(self.current_points) - 1):
                p1 = self.current_points[i]
                p2 = self.current_points[i + 1]
                # Convert to int before drawing
                painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))

            # Draw line to mouse position if we have at least one point
            if self.mouse_pos and self.current_points:
                last_point = self.current_points[-1]
                # Convert to int before drawing
                painter.drawLine(int(last_point[0]), int(last_point[1]),
                                 int(self.mouse_pos[0]), int(self.mouse_pos[1]))

            # Draw points
            for i, point in enumerate(self.current_points):
                # Use a solid circle for points
                painter.setBrush(QBrush(self.line_color))
                painter.drawEllipse(int(point[0] - 4), int(point[1] - 4), 8, 8)

        except Exception as e:
            self.logger.error(f"Error drawing: {e}", exc_info=True)

    def draw_editable_points(self, painter):
        """
        Draw all editable points for existing zones

        Args:
            painter: The QPainter to draw on
        """
        if not painter:
            return

        try:
            # Only draw points if not in drawing mode
            if self.drawing_zone:
                return

            # Draw points for all zones
            for zone_idx, zone in enumerate(self.parent_view.zones):
                if 'points' not in zone or not zone['points']:
                    continue

                # Use zone color for points
                zone_color = self.get_zone_color(zone, zone_idx)

                # Draw each point
                for point_idx, point in enumerate(zone['points']):
                    # Determine point appearance
                    is_selected = (zone_idx == self.selected_point_zone and
                                   point_idx == self.selected_point_index)
                    is_hovered = (zone_idx == self.hover_point_zone and
                                  point_idx == self.hover_point_index)

                    # Set appearance based on state
                    if is_selected:
                        # Selected point - larger, opaque
                        painter.setBrush(QBrush(Qt.white))
                        painter.setPen(QPen(Qt.black, 1))
                        size = 10
                    elif is_hovered:
                        # Hovered point - highlight
                        painter.setBrush(QBrush(Qt.yellow))
                        painter.setPen(QPen(Qt.black, 1))
                        size = 8
                    else:
                        # Normal point
                        painter.setBrush(QBrush(zone_color.lighter(120)))
                        painter.setPen(QPen(Qt.black, 1))
                        size = 6

                    # Draw the point
                    half_size = size // 2
                    painter.drawEllipse(int(point[0] - half_size),
                                        int(point[1] - half_size),
                                        size, size)

        except Exception as e:
            self.logger.error(f"Error drawing editable points: {e}", exc_info=True)

    def select_point_at_position(self, pos):
        if not pos:
            return False

        try:
            x, y = pos.x(), pos.y()
            selection_radius = 8  # Slightly larger for easier selection

            # Look through all zone points
            for zone_idx, zone in enumerate(self.parent_view.zones):
                if 'points' not in zone or not zone['points']:
                    continue

                for point_idx, point in enumerate(zone['points']):
                    if abs(x - point[0]) <= selection_radius and abs(y - point[1]) <= selection_radius:
                        self.selected_point_index = point_idx
                        self.selected_point_zone = zone_idx
                        self._drag_origin = point  # Save original position for undo
                        self.is_dragging = True
                        return True

            # No point selected
            self.selected_point_index = None
            self.selected_point_zone = None
            self.is_dragging = False
            return False

        except Exception as e:
            self.logger.error(f"Error selecting point: {e}")
            self.selected_point_index = None
            self.selected_point_zone = None
            self.is_dragging = False
            return False

    def is_dragging_point(self):
        return self.is_dragging and self.selected_point_index is not None

    def drag_point_to(self, x, y):
        if self.selected_point_index is None:
            return False

        try:
            self.is_dragging = True

            # Apply grid snapping if enabled
            if (hasattr(self.parent_view, 'grid_manager') and
                    self.parent_view.grid_manager.is_snap_enabled()):
                x, y = self.parent_view.grid_manager.snap_to_grid(x, y)
                self.logger.debug(f"Snapped dragged point to grid: ({x}, {y})")

            # Update the point position
            if self.selected_point_zone is not None:
                self.parent_view.zones[self.selected_point_zone]['points'][self.selected_point_index] = (x, y)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error dragging point: {e}")
            return False

    def end_point_drag(self, pos):
        if not self.is_dragging:
            return False

        try:
            # Final update to position
            if self.selected_point_index is not None and pos is not None:
                x, y = pos.x(), pos.y()

                # Apply grid snapping if enabled
                if (hasattr(self.parent_view, 'grid_manager') and
                        self.parent_view.grid_manager.is_snap_enabled()):
                    x, y = self.parent_view.grid_manager.snap_to_grid(x, y)

                if self.selected_point_zone is not None:
                    self.parent_view.zones[self.selected_point_zone]['points'][self.selected_point_index] = (x, y)

            # Push to undo stack if the point actually moved
            if (self.selected_point_index is not None and
                    self._drag_origin is not None and
                    self.selected_point_zone is not None):
                self.undo_stack.append((
                    "move_point",
                    (self.selected_point_zone, self.selected_point_index, self._drag_origin)
                ))

            # Reset dragging state
            self._drag_origin = None
            self.is_dragging = False
            return True

        except Exception as e:
            self.logger.error(f"Error ending point drag: {e}")
            self._drag_origin = None
            self.is_dragging = False
            return False

    def undo_last_action(self):
        if not self.undo_stack:
            return False

        try:
            action, data = self.undo_stack.pop()

            if action == "add_point" and self.current_points:
                self.current_points.pop()
                return True

            if action == "move_point":
                zone_idx, point_idx, old_pos = data
                if (zone_idx is not None and
                        zone_idx < len(self.parent_view.zones) and
                        point_idx < len(self.parent_view.zones[zone_idx]['points'])):
                    self.parent_view.zones[zone_idx]['points'][point_idx] = old_pos
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error undoing last action: {e}")
            return False

    def get_zone_color(self, zone, index):
        try:
            color_index = zone.get('color_index', index % len(self.ZONE_COLORS))
            return self.ZONE_COLORS[color_index % len(self.ZONE_COLORS)]

        except Exception as e:
            self.logger.error(f"Error getting zone color: {e}")
            # Return a default color in case of error
            return self.ZONE_COLORS[0]

    def set_line_color(self, color):
        """
        Set the color for drawing lines

        Args:
            color (QColor): The color to use

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not isinstance(color, QColor):
                self.logger.warning(f"Invalid color type: {type(color)}")
                return False

            self.line_color = color
            self.logger.debug(f"Line color set to: {color.name()}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting line color: {e}")
            return False