import logging

from PySide6.QtWidgets import (QFileDialog, QInputDialog, QColorDialog)
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor

from ui.dialogs.confirm_dialog import ConfirmDialog
from ui.dialogs.alert_dialog import AlertDialog
from ui.styles.base_styles import Colors


class ToolbarActionHandler(QObject):
    """Handles all toolbar action logic and coordination between managers"""

    def __init__(self, parent_tab):
        super().__init__(parent_tab)
        self.parent_tab = parent_tab
        self.logger = logging.getLogger(__name__)

    def handle_load_background(self, placeholder_path=""):
        """Handle load background action with full dialog and validation logic"""
        # Check if background already exists
        if self.parent_tab.zones_view.background_manager.has_background():
            confirmed = ConfirmDialog.ask(
                self.parent_tab,
                "Replace Floorplan",
                "This will replace the current floorplan image. "
                "All zone information will be kept.\n\n"
                "Continue?",
                confirm_text="Replace",
            )
            if not confirmed:
                return

        # Open file dialog
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(
            self.parent_tab, "Open Floorplan Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.pdf);;PDF Files (*.pdf);;All Files (*)"
        )

        if image_path:
            self._handle_background_loaded(image_path)

    def _handle_background_loaded(self, image_path):
        """Handle successful background loading then optionally start calibration."""
        # Load background first
        success = self.parent_tab.zones_view.load_background(image_path)
        if not success:
            AlertDialog.show_error(
                self.parent_tab,
                "Load Failed",
                "The floorplan image could not be loaded. Please check the file and try again."
            )
            return

        self.parent_tab.toolbar_manager.update_draw_zone_button()
        # Background loading is a user action that should trigger modification
        self.parent_tab.on_zones_modified()

        # Copy background into project assets so it's preserved if the original is deleted
        try:
            pm = self.parent_tab.project_manager
            if pm.current_project_id and hasattr(pm, 'storage'):
                copy_path = pm.storage.copy_background_for_project(pm.current_project_id, image_path)
                if copy_path:
                    self.parent_tab.zones_view.background_manager.background_path = copy_path
        except Exception:
            pass  # Non-critical: original path remains if copy fails

        # Ask whether to calibrate scale now
        should_calibrate = ConfirmDialog.ask(
            self.parent_tab,
            "Calibrate Scale",
            "For accurate area measurements you should calibrate the scale for this image.\n\n"
            "Would you like to calibrate now? (You can also do this later via the Calibrate button.)",
            confirm_text="Calibrate Now",
            cancel_text="Skip for Now",
        )
        if should_calibrate:
            self.parent_tab.zones_view.start_calibration()

    def handle_draw_zone(self):
        """Handle draw zone action — no floorplan required."""
        # Show drawing hint in status bar and start immediately
        if hasattr(self.parent_tab, 'status_label'):
            self.parent_tab.status_label.setText(
                "Drawing mode — left-click to add points · right-click to finish · Esc to cancel"
            )

        # Start drawing through zones view
        self.parent_tab.zones_view.start_zone_drawing()

    def handle_line_color_change(self, placeholder_color=None):
        """Handle line color change with color dialog"""
        try:
            # Get current color or default
            current_color = QColor(0, 128, 255)  # Default blue

            # Open color dialog
            color = QColorDialog.getColor(
                current_color,
                self.parent_tab,
                "Select Drawing Line Color",
                QColorDialog.ShowAlphaChannel
            )

            # Apply if valid
            if color.isValid():
                self.parent_tab.grid_visual_manager.set_line_color(color)
                # Update color swatch in toolbar
                if hasattr(self.parent_tab, 'toolbar_manager'):
                    self.parent_tab.toolbar_manager.update_color_swatch(color)

        except Exception as e:
            self.logger.error(f"Error changing line color: {e}")

    def handle_grid_resolution_change(self, placeholder_size=0):
        """Handle grid resolution change with input dialog"""
        try:
            # Get current grid size from zones_view
            current_size = self.parent_tab.zones_view.get_grid_size()

            dlg = QInputDialog(self.parent_tab)
            dlg.setWindowTitle("Grid Resolution")
            dlg.setLabelText("Set grid size in pixels (4–48):")
            dlg.setInputMode(QInputDialog.IntInput)
            dlg.setIntMinimum(4)
            dlg.setIntMaximum(48)
            dlg.setIntValue(current_size)
            dlg.setStyleSheet(f"""
                QDialog {{ background-color: {Colors.WHITE}; color: {Colors.TEXT_PRIMARY}; }}
                QLabel {{ color: {Colors.TEXT_PRIMARY}; }}
                QLineEdit, QSpinBox {{
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
            grid_size = dlg.intValue()

            if ok and grid_size >= 4:
                # Handle through grid visual manager
                self.parent_tab.grid_visual_manager.handle_grid_resolution_request(grid_size)

        except Exception as e:
            self.logger.error(f"Error in grid resolution dialog: {e}")
            AlertDialog.show_error(self.parent_tab, "Grid Error", f"Failed to set grid resolution: {str(e)}")

    def validate_action_prerequisites(self, action_name):
        """Validate prerequisites for specific actions"""
        if action_name == "draw_zone":
            return True   # No floorplan required — draw on grid
        elif action_name == "calibrate_scale":
            return self.parent_tab.zones_view.background_manager.has_background()
        elif action_name == "export":
            zones_view = self.parent_tab.zones_view
            return (zones_view.background_manager.has_background() or len(zones_view.zones) > 0)
        return True

    def get_action_error_message(self, action_name):
        """Get appropriate error message for failed action prerequisites"""
        if action_name == "draw_zone":
            return ""   # draw_zone is always available
        elif action_name == "calibrate_scale":
            return "Please load a floorplan image before calibrating scale."
        elif action_name == "export":
            return "Nothing to export. Please add a floorplan or draw some zones first."
        return "Action cannot be performed at this time."
