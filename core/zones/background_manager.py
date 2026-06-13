import os
import logging
from PySide6.QtGui import QPixmap, QImage


class BackgroundManager:
    """Manages background images for the zones view"""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        self.background_pixmap = None
        self.background_path = None
        self.background_scale = 1.0
        self.background_offset = (0, 0)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("BackgroundManager initialized")

    def load_background(self, image_path):
        if not image_path:
            self.logger.error("Cannot load background: image_path is empty")
            return False

        try:
            if not os.path.exists(image_path):
                self.logger.error(f"Background image not found: {image_path}")
                return False

            # Check if file is a PDF
            if image_path.lower().endswith('.pdf'):
                try:
                    import fitz  # PyMuPDF

                    # Open PDF document
                    pdf_document = fitz.open(image_path)

                    # Get first page
                    page = pdf_document[0]

                    # Render page to a pixmap (adjust zoom factor as needed)
                    zoom_factor = 2.0  # Higher for better quality
                    matrix = fitz.Matrix(zoom_factor, zoom_factor)
                    pixmap = page.get_pixmap(matrix=matrix)

                    # Convert to QImage then QPixmap
                    img_data = pixmap.samples
                    qimage = QImage(img_data, pixmap.width, pixmap.height,
                                    pixmap.stride, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)

                    pdf_document.close()
                except ImportError:
                    self.logger.error("PyMuPDF not installed. Cannot load PDF files.")
                    return False
            else:
                # Load directly as QPixmap for other image types
                pixmap = QPixmap(image_path)

            if pixmap.isNull():
                self.logger.error(f"Failed to load background image: {image_path}")
                return False

            # Store background
            self.background_pixmap = pixmap
            self.background_path = image_path
            self.logger.info(f"Background loaded successfully: {image_path} ({pixmap.width()}x{pixmap.height()})")

            # Trigger redraw
            if self.parent_view:
                self.parent_view.update()

            return True

        except Exception as e:
            self.logger.error(f"Error loading background: {e}", exc_info=True)
            return False

    def has_background(self):
        return self.background_pixmap is not None and not self.background_pixmap.isNull()

    def clear_background(self):
        try:
            old_path = self.background_path
            self.background_pixmap = None
            self.background_path = None

            if self.parent_view:
                self.parent_view.update()

            self.logger.info(f"Background cleared: {old_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing background: {e}", exc_info=True)
            return False

    def get_background_path(self):
        self.logger.debug(f"Getting background path: {self.background_path}")
        return self.background_path

    def draw(self, painter):
        if not painter:
            self.logger.warning("Cannot draw background: painter is None")
            return

        try:
            if self.background_pixmap and not self.background_pixmap.isNull():
                painter.save()

                # Apply scaling and offset if needed
                painter.translate(self.background_offset[0], self.background_offset[1])
                painter.scale(self.background_scale, self.background_scale)

                # Draw the background
                painter.drawPixmap(0, 0, self.background_pixmap)

                painter.restore()

        except Exception as e:
            self.logger.error(f"Error drawing background: {e}", exc_info=True)

    def set_background_scale(self, scale):
        """
        Set the background scaling factor

        Args:
            scale (float): The scaling factor to apply

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if scale <= 0:
                self.logger.warning(f"Invalid background scale: {scale}, must be positive")
                return False

            self.background_scale = scale

            if self.parent_view:
                self.parent_view.update()

            self.logger.debug(f"Background scale set to: {scale}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting background scale: {e}", exc_info=True)
            return False

    def set_background_offset(self, offset_x, offset_y):
        """
        Set the background offset

        Args:
            offset_x (float): Horizontal offset
            offset_y (float): Vertical offset

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.background_offset = (offset_x, offset_y)

            if self.parent_view:
                self.parent_view.update()

            self.logger.debug(f"Background offset set to: ({offset_x}, {offset_y})")
            return True

        except Exception as e:
            self.logger.error(f"Error setting background offset: {e}", exc_info=True)
            return False

    def get_background_size(self):
        """
        Get the size of the current background image

        Returns:
            tuple: Width and height of the background image or (0, 0) if no background
        """
        if self.background_pixmap and not self.background_pixmap.isNull():
            width = self.background_pixmap.width()
            height = self.background_pixmap.height()
            return (width, height)
        return (0, 0)