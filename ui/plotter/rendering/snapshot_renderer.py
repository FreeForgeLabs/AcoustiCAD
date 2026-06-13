import logging
import base64
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QRectF, QBuffer, QIODevice


class SnapshotRenderer:
    """Handles high-quality snapshot generation for reports and documentation"""

    def __init__(self, parent_view):
        """Initialize the snapshot renderer

        Args:
            parent_view: The parent SpeakerView instance
        """
        self.view = parent_view
        self.logger = logging.getLogger(__name__)

    def capture_zone_snapshot(self, width=1200, height=900, include_legend=True):
        """
        Capture a high-quality snapshot of the current zone with speakers and obstructions

        Args:
            width (int): Output image width in pixels
            height (int): Output image height in pixels
            include_legend (bool): Whether to include a legend in the image

        Returns:
            QPixmap: High-quality rendered image of the zone
        """
        # Get speakers from data manager
        current_speakers = self.view.speaker_data_manager.get_all_speakers()
        self.logger.debug(f"capture_snapshot: zone={self.view.current_zone is not None}, speakers={len(current_speakers)}")

        if not self.view.current_zone:
            self.logger.info("No current zone - returning None")
            return None

        try:
            # Create high-resolution pixmap
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.white)
            self.logger.info(f"Created pixmap: {width}x{height}")

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Calculate zone bounds using viewport manager
            zone_bounds = self.view.viewport_manager.calculate_zone_bounds(self.view.current_zone)
            if not zone_bounds:
                self.logger.info("No valid zone bounds - returning pixmap")
                painter.end()
                return pixmap

            min_x, min_y, max_x, max_y = zone_bounds
            zone_width = max_x - min_x
            zone_height = max_y - min_y

            if zone_width <= 0 or zone_height <= 0:
                self.logger.info("Invalid zone dimensions - returning pixmap")
                painter.end()
                return pixmap

            # Calculate margins for legend space
            legend_height = 120 if include_legend else 0
            margin = 50
            available_width = width - (2 * margin)
            available_height = height - (2 * margin) - legend_height

            # Calculate scale to fit zone in available space
            scale_x = available_width / zone_width
            scale_y = available_height / zone_height
            render_scale = min(scale_x, scale_y) * 0.9  # 90% to add some buffer

            # Calculate center position
            center_x = width / 2
            center_y = (height - legend_height) / 2

            # Calculate offset to center the zone using viewport manager
            zone_center = self.view.viewport_manager.calculate_zone_center(self.view.current_zone)
            if not zone_center:
                painter.end()
                return pixmap

            zone_center_x, zone_center_y = zone_center
            offset_x = center_x - (zone_center_x * render_scale)
            offset_y = center_y - (zone_center_y * render_scale)

            # Apply transformations
            painter.translate(offset_x, offset_y)
            painter.scale(render_scale, render_scale)

            # Draw background if available
            if self.view.background_manager.has_background():
                self.view.background_manager.draw(painter)

            # Draw zone outline using zone renderer
            self.view.zone_renderer.draw_zone_for_snapshot(painter, self.view.current_zone)

            # Draw speakers using speaker renderer (get from data manager)
            self.logger.info(f"Drawing {len(current_speakers)} speakers")
            self.view.speaker_renderer.draw_speakers(painter, current_speakers, None, True, 1.0)

            # Draw obstructions
            if hasattr(self.view, 'obstruction_manager'):
                self.view.obstruction_manager.draw_obstructions(painter, False, 1.0)

            # Reset transformation for legend
            painter.resetTransform()

            # Draw legend if requested
            if include_legend:
                self._draw_snapshot_legend(painter, width, height)

            # Draw title
            self._draw_snapshot_title(painter, width)

            painter.end()

            self.logger.info(f"Snapshot generated successfully: {not pixmap.isNull()}")
            self.logger.info(f"Generated snapshot for zone: {self.view.current_zone.get('name', 'Unnamed')}")
            return pixmap

        except Exception as e:
            self.logger.error(f"Error capturing zone snapshot: {e}", exc_info=True)
            return None

    def capture_all_zones_thumbnails(self, zones, speaker_layout, obstruction_layout, thumbnail_size=300):
        """
        Capture thumbnail snapshots of all zones

        Args:
            zones (list): List of zone data
            speaker_layout (dict): Speaker layout data by zone_id
            obstruction_layout (dict): Obstruction layout data by zone_id
            thumbnail_size (int): Size of square thumbnails

        Returns:
            dict: Dictionary mapping zone_id to thumbnail QPixmap
        """
        thumbnails = {}

        # Store current state
        original_zone = self.view.current_zone
        original_zone_id = self.view.speaker_data_manager.current_zone_id
        original_obstructions = getattr(self.view.obstruction_manager, 'obstructions', {}).copy()

        try:
            for zone in zones:
                zone_id = str(zone.get('id', ''))
                if not zone_id:
                    continue

                # Set current zone
                self.view.current_zone = zone

                # Load speakers for this zone via data manager
                self.view.speaker_data_manager.set_current_zone(zone_id)

                # Load obstructions for this zone
                if hasattr(self.view, 'obstruction_manager'):
                    self.view.obstruction_manager.set_current_zone(zone_id)
                    if zone_id in obstruction_layout:
                        self.view.obstruction_manager.obstructions = obstruction_layout[zone_id]
                    else:
                        self.view.obstruction_manager.obstructions = {}

                # Capture thumbnail
                thumbnail = self.capture_zone_snapshot(
                    width=thumbnail_size,
                    height=thumbnail_size,
                    include_legend=False
                )

                if thumbnail:
                    thumbnails[zone_id] = thumbnail

        except Exception as e:
            self.logger.error(f"Error capturing thumbnails: {e}", exc_info=True)

        finally:
            # Restore original state
            self.view.current_zone = original_zone
            self.view.speaker_data_manager.set_current_zone(original_zone_id)
            if hasattr(self.view, 'obstruction_manager'):
                self.view.obstruction_manager.obstructions = original_obstructions

        return thumbnails

    def pixmap_to_base64(self, pixmap):
        """Convert QPixmap to base64 string for HTML embedding

        Args:
            pixmap (QPixmap): The pixmap to convert

        Returns:
            str: Base64 encoded image string with data URI prefix
        """
        if not pixmap or pixmap.isNull():
            return ""

        try:
            # Convert to bytes
            byte_array = QBuffer()
            byte_array.open(QIODevice.WriteOnly)
            pixmap.save(byte_array, "PNG", quality=100)

            # Encode to base64
            image_data = byte_array.data().data()
            base64_string = base64.b64encode(image_data).decode('utf-8')

            return f"data:image/png;base64,{base64_string}"

        except Exception as e:
            self.logger.error(f"Error converting pixmap to base64: {e}")
            return ""

    def _draw_snapshot_legend(self, painter, image_width, image_height):
        """Draw legend for the snapshot

        Args:
            painter (QPainter): The painter to draw with
            image_width (int): Total image width
            image_height (int): Total image height
        """
        legend_height = 100
        legend_y = image_height - legend_height - 10

        # Legend background
        legend_rect = QRectF(10, legend_y, image_width - 20, legend_height)
        painter.fillRect(legend_rect, QColor(248, 248, 248, 220))
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRect(legend_rect)

        # Legend title
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        painter.setPen(Qt.black)
        painter.drawText(int(legend_rect.left() + 10), int(legend_rect.top() + 20), "Legend")

        # Speaker types legend
        y_offset = legend_rect.top() + 40
        x_offset = legend_rect.left() + 20

        font = QFont("Arial", 10)
        painter.setFont(font)

        # Speaker types
        speaker_types = [
            ("In-Ceiling", QColor(0, 120, 215), "●"),
            ("Pendant", QColor(0, 180, 120), "▲"),
        ]

        for i, (type_name, color, symbol) in enumerate(speaker_types):
            x = x_offset + (i * 140)

            # Draw symbol
            painter.setPen(QPen(color, 3))
            font_symbol = QFont("Arial", 16, QFont.Bold)
            painter.setFont(font_symbol)
            painter.drawText(int(x), int(y_offset), symbol)

            # Draw label
            painter.setPen(Qt.black)
            painter.setFont(font)
            painter.drawText(int(x + 20), int(y_offset), type_name)

        # Obstruction types legend
        y_offset += 25
        obstruction_types = [
            ("Column", QColor(150, 150, 150)),
            ("Light", QColor(255, 255, 0)),
            ("HVAC", QColor(100, 100, 255)),
            ("Other", QColor(255, 0, 0))
        ]

        for i, (type_name, color) in enumerate(obstruction_types):
            x = x_offset + (i * 120)

            # Draw circle
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(x), int(y_offset - 8), 12, 12)

            # Draw label
            painter.setPen(Qt.black)
            painter.drawText(int(x + 20), int(y_offset), type_name)

    def _draw_snapshot_title(self, painter, image_width):
        """Draw title at the top of the snapshot

        Args:
            painter (QPainter): The painter to draw with
            image_width (int): Total image width
        """
        if not self.view.current_zone:
            return

        # Title background
        title_height = 40
        title_rect = QRectF(0, 0, image_width, title_height)
        painter.fillRect(title_rect, QColor(52, 62, 80))

        # Title text
        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)
        painter.setPen(Qt.white)

        zone_name = self.view.current_zone.get('name', 'Unnamed Zone')
        speaker_count = self.view.speaker_data_manager.get_speaker_count()
        obstruction_count = len(getattr(self.view.obstruction_manager, 'obstructions', {}))

        title_text = f"{zone_name} - {speaker_count} Speakers, {obstruction_count} Obstructions"
        painter.drawText(title_rect, Qt.AlignCenter, title_text)