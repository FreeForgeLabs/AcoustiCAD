from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize, QByteArray, QBuffer, QRect
import logging
import os


class ThumbnailGenerator:
    """Utility class for generating thumbnails of zone layouts"""

    def __init__(self):
        """Initialize the ThumbnailGenerator"""
        self.logger = logging.getLogger(__name__)

    def generate_from_zones_view(self, zones_view, width=300, height=200):
        """
        Generate a thumbnail from a ZonesView widget
        Args:
            zones_view: The ZonesView widget to generate a thumbnail from
            width (int): The desired width of the thumbnail
            height (int): The desired height of the thumbnail
        Returns:
            str or None: Base64-encoded image string if successful, None otherwise
        """
        if not zones_view:
            self.logger.warning("Cannot generate thumbnail: zones_view is None")
            return self.generate_placeholder(width, height)

        image = None
        painter = None

        try:
            # Create a new image with the specified dimensions
            image = QImage(width, height, QImage.Format_ARGB32)
            image.fill(Qt.white)

            # Get the original size of the zones view
            original_size = zones_view.size()
            if original_size.width() <= 0 or original_size.height() <= 0:
                self.logger.warning("Invalid zones view size for thumbnail generation")
                return self.generate_placeholder(width, height)

            # Calculate scaling factors
            scale_x = width / original_size.width()
            scale_y = height / original_size.height()

            # Use the smaller scale to maintain aspect ratio
            scale = min(scale_x, scale_y)

            # Create a painter for the image
            painter = QPainter(image)

            # Check if painter is valid before proceeding
            if not painter.isActive():
                self.logger.error("Failed to create active painter for thumbnail")
                return self.generate_placeholder(width, height)

            # Enable anti-aliasing
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # Scale the painter
            painter.scale(scale, scale)

            # Center the content
            scaled_width = original_size.width() * scale
            scaled_height = original_size.height() * scale
            offset_x = (width - scaled_width) / 2 / scale
            offset_y = (height - scaled_height) / 2 / scale
            painter.translate(offset_x, offset_y)

            # Have the zones view render itself to our painter
            zones_view.render(painter)

            # Ensure painter is properly finished before converting
            painter.end()
            painter = None  # Mark as cleaned up

            # Convert to base64 string
            result = self.image_to_base64(image)
            self.logger.debug(f"Generated thumbnail from zones view - size: {width}x{height}")
            return result

        except Exception as e:
            self.logger.error(f"Error generating thumbnail from zones view: {e}", exc_info=True)
            return self.generate_placeholder(width, height)

        finally:
            # Ensure painter is properly closed even in error cases
            if painter is not None and painter.isActive():
                try:
                    painter.end()
                except Exception as cleanup_error:
                    self.logger.warning(f"Error during painter cleanup: {cleanup_error}")

            # Explicitly release image memory
            image = None

    def generate_placeholder(self, width=300, height=200):
        """
        Generate a placeholder thumbnail if real generation fails

        Args:
            width (int): The desired width of the placeholder
            height (int): The desired height of the placeholder

        Returns:
            str or None: Base64-encoded image string if successful, None otherwise
        """
        image = None
        painter = None

        try:
            # Create a placeholder image
            image = QImage(width, height, QImage.Format_ARGB32)
            image.fill(QColor(240, 240, 240))

            painter = QPainter(image)

            # Check if painter is valid before proceeding
            if not painter.isActive():
                self.logger.error("Failed to create active painter for placeholder")
                return None

            # Draw border
            painter.setPen(QColor(200, 200, 200))
            painter.drawRect(5, 5, width - 10, height - 10)

            # Draw text
            font = QFont("Arial", 10)
            painter.setFont(font)
            painter.setPen(Qt.black)

            text_rect = QRect(10, height // 2 - 20, width - 20, 40)
            painter.drawText(text_rect, Qt.AlignCenter, "Preview Not Available")

            # Ensure painter is properly finished before converting
            painter.end()
            painter = None  # Mark as cleaned up

            # Convert to base64 string
            result = self.image_to_base64(image)
            self.logger.debug(f"Generated placeholder thumbnail - size: {width}x{height}")
            return result

        except Exception as e:
            self.logger.error(f"Error generating placeholder thumbnail: {e}", exc_info=True)
            return None

        finally:
            # Ensure painter is properly closed even in error cases
            if painter is not None and painter.isActive():
                try:
                    painter.end()
                except Exception as cleanup_error:
                    self.logger.warning(f"Error during painter cleanup: {cleanup_error}")

            # Explicitly release image memory
            image = None

    def image_to_base64(self, image):
        """
        Convert a QImage to a base64 encoded string

        Args:
            image (QImage): The image to convert

        Returns:
            str or None: Base64-encoded image string if successful, None otherwise
        """
        if not image or image.isNull():
            self.logger.warning("Cannot convert to base64: image is None or null")
            return None

        buffer = None

        try:
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)

            if not buffer.open(QBuffer.WriteOnly):
                self.logger.error("Failed to open buffer for writing")
                return None

            # Save image as PNG format
            success = image.save(buffer, "PNG")
            if not success:
                self.logger.error("Failed to save image to buffer")
                return None

            image_data = byte_array.toBase64().data().decode()
            return image_data

        except Exception as e:
            self.logger.error(f"Error converting image to base64: {e}", exc_info=True)
            return None

        finally:
            # Close the buffer if it was opened
            if buffer is not None and buffer.isOpen():
                buffer.close()

    def base64_to_image(self, base64_string):
        """
        Convert a base64 encoded string back to a QImage

        Args:
            base64_string (str): The base64 string to convert

        Returns:
            QImage or None: The converted image if successful, None otherwise
        """
        if not base64_string:
            self.logger.warning("Cannot convert to image: base64_string is empty")
            return None

        try:
            byte_array = QByteArray.fromBase64(base64_string.encode())

            if byte_array.isEmpty():
                self.logger.warning("Empty byte array after base64 decoding")
                return None

            image = QImage()
            if not image.loadFromData(byte_array):
                self.logger.error("Failed to load image from byte array")
                return None

            if image.isNull():
                self.logger.error("Loaded image is null")
                return None

            self.logger.debug(f"Successfully converted base64 to image - size: {image.width()}x{image.height()}")
            return image

        except Exception as e:
            self.logger.error(f"Error converting base64 to image: {e}", exc_info=True)
            return None

    def save_thumbnail_to_file(self, base64_string, file_path):
        """
        Save a base64 encoded thumbnail to a file

        Args:
            base64_string (str): The base64 string to save
            file_path (str): The path to save the file to

        Returns:
            bool: True if successful, False otherwise
        """
        if not base64_string:
            self.logger.warning("Cannot save thumbnail: base64_string is empty")
            return False

        try:
            # Convert base64 to image
            image = self.base64_to_image(base64_string)
            if not image or image.isNull():
                return False

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save image to file
            success = image.save(file_path, "PNG")
            if success:
                self.logger.info(f"Saved thumbnail to file: {file_path}")
            else:
                self.logger.error(f"Failed to save thumbnail to file: {file_path}")

            return success

        except Exception as e:
            self.logger.error(f"Error saving thumbnail to file: {e}", exc_info=True)
            return False