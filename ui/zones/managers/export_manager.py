import logging
import os
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Signal, QObject

from ui.dialogs.alert_dialog import AlertDialog


class ExportManager(QObject):
    """Manages export functionality for ZonesTab"""

    # Signals
    export_started = Signal(str)  # message
    export_completed = Signal(str, bool)  # file_path, success

    def __init__(self, parent_tab):
        super().__init__(parent_tab)  # Initialize QObject
        self.parent_tab = parent_tab
        self.logger = logging.getLogger(__name__)

    def export_image(self):
        """Handle export image action with smart defaults"""
        if not self._has_content_to_export():
            AlertDialog.show_warning(
                self.parent_tab, "Nothing to Export",
                "There is no background image or zones to export. Please add content first."
            )
            return

        # Get export parameters
        file_path, default_format = self._get_export_parameters()

        if not file_path:
            return  # User canceled

        # Show processing message
        self.export_started.emit("Exporting... Please wait")

        try:
            # Determine export method based on file extension
            if file_path.lower().endswith('.pdf'):
                success = self._export_to_pdf(file_path)
            else:
                success = self._export_to_image(file_path)

            # Emit completion signal
            self.export_completed.emit(file_path, success)

            # Show result message
            if success:
                AlertDialog.show_info(self.parent_tab, "Export Complete", f"File exported to:\n{file_path}")
            else:
                AlertDialog.show_error(self.parent_tab, "Export Failed", f"Failed to export to {file_path}")

        except Exception as e:
            self.export_completed.emit(file_path, False)
            AlertDialog.show_error(self.parent_tab, "Export Failed", f"Failed to export: {str(e)}")

    def _has_content_to_export(self):
        """Check if there's content to export"""
        zones_view = self.parent_tab.zones_view
        return (zones_view.background_manager.has_background() or
                len(zones_view.zones) > 0)

    def _get_export_parameters(self):
        """Get export file path and determine format"""
        # Determine default format and path based on background
        default_format = "PNG Files (*.png)"
        default_path = ""

        zones_view = self.parent_tab.zones_view
        if zones_view.background_manager.has_background():
            bg_path = zones_view.background_manager.get_background_path()
            if bg_path:
                # Get directory and filename from background path
                bg_dir = os.path.dirname(bg_path)
                bg_name = os.path.splitext(os.path.basename(bg_path))[0]
                default_path = os.path.join(bg_dir, f"{bg_name}_export")

                # Use background format as default if supported
                bg_ext = os.path.splitext(bg_path)[1].lower()
                format_map = {
                    '.jpg': "JPEG Files (*.jpg)",
                    '.jpeg': "JPEG Files (*.jpg)",
                    '.png': "PNG Files (*.png)",
                    '.bmp': "BMP Files (*.bmp)",
                    '.tif': "TIFF Files (*.tiff)",
                    '.tiff': "TIFF Files (*.tiff)",
                    '.pdf': "PDF Files (*.pdf)"
                }
                default_format = format_map.get(bg_ext, "PNG Files (*.png)")

        # Set up file dialog filters
        filters = ("PDF Files (*.pdf);;PNG Files (*.png);;JPEG Files (*.jpg);;"
                   "BMP Files (*.bmp);;TIFF Files (*.tiff);;All Files (*)")

        # Show file dialog
        file_dialog = QFileDialog()
        file_path, selected_filter = file_dialog.getSaveFileName(
            self.parent_tab, "Export Drawing", default_path, filters, default_format
        )

        if not file_path:
            return None, None

        # Add appropriate extension if missing
        file_path = self._ensure_file_extension(file_path, selected_filter)

        return file_path, selected_filter

    def _ensure_file_extension(self, file_path, selected_filter):
        """Ensure the file has the correct extension"""
        extension_map = {
            "PDF Files (*.pdf)": ".pdf",
            "PNG Files (*.png)": ".png",
            "JPEG Files (*.jpg)": ".jpg",
            "BMP Files (*.bmp)": ".bmp",
            "TIFF Files (*.tiff)": ".tiff"
        }

        if selected_filter in extension_map:
            expected_ext = extension_map[selected_filter]
            if not file_path.lower().endswith(expected_ext.lower()):
                # Handle special cases
                if expected_ext == ".jpg" and file_path.lower().endswith('.jpeg'):
                    return file_path  # .jpeg is acceptable for JPEG files
                elif expected_ext == ".tiff" and file_path.lower().endswith('.tif'):
                    return file_path  # .tif is acceptable for TIFF files
                else:
                    file_path += expected_ext

        return file_path

    def _export_to_image(self, file_path):
        """Export to image format"""
        try:
            # Get format from file extension
            ext = os.path.splitext(file_path)[1].lower()
            format_map = {
                '.jpg': 'jpg', '.jpeg': 'jpg',
                '.png': 'png',
                '.bmp': 'bmp',
                '.tif': 'tiff', '.tiff': 'tiff'
            }

            format_name = format_map.get(ext, 'png')

            # Export using zones view
            return self.parent_tab.zones_view.export_to_image(file_path, format_name)

        except Exception as e:
            self.logger.error(f"Error in _export_to_image: {e}")
            return False

    def _export_to_pdf(self, file_path):
        """Export to PDF format"""
        try:
            return self.parent_tab.zones_view.export_to_pdf(file_path)
        except Exception as e:
            self.logger.error(f"Error in _export_to_pdf: {e}")
            return False

    def get_suggested_export_path(self, extension=".png"):
        """Get a suggested export path based on current project or background"""
        try:
            zones_view = self.parent_tab.zones_view

            # Try to base on background image path
            if zones_view.background_manager.has_background():
                bg_path = zones_view.background_manager.get_background_path()
                if bg_path:
                    bg_dir = os.path.dirname(bg_path)
                    bg_name = os.path.splitext(os.path.basename(bg_path))[0]
                    return os.path.join(bg_dir, f"{bg_name}_export{extension}")

            # Try to base on project
            if hasattr(self.parent_tab, 'project_manager') and self.parent_tab.project_manager:
                project_data = self.parent_tab.project_manager.get_current_project_data()
                if project_data and 'name' in project_data:
                    project_name = project_data['name']
                    return f"{project_name}_zones{extension}"

            # Default fallback
            return f"zones_export{extension}"

        except Exception as e:
            self.logger.error(f"Error getting suggested export path: {e}")
            return f"zones_export{extension}"

    def get_export_info(self):
        """Get information about what will be exported"""
        zones_view = self.parent_tab.zones_view
        info = {
            'has_background': zones_view.background_manager.has_background(),
            'zone_count': len(zones_view.zones),
            'has_content': self._has_content_to_export()
        }

        if info['has_background']:
            bg_path = zones_view.background_manager.get_background_path()
            if bg_path:
                info['background_name'] = os.path.basename(bg_path)
                info['background_dir'] = os.path.dirname(bg_path)

        return info

    def validate_export_path(self, file_path):
        """Validate that the export path is writable"""
        try:
            # Check if directory exists and is writable
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                return False, f"Directory does not exist: {directory}"

            if not os.access(directory, os.W_OK):
                return False, f"Directory is not writable: {directory}"

            # Check if file already exists
            if os.path.exists(file_path):
                return True, f"File already exists and will be overwritten: {file_path}"

            return True, "Export path is valid"

        except Exception as e:
            return False, f"Error validating export path: {str(e)}"