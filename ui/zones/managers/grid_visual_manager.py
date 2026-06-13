import logging

from PySide6.QtCore import Signal, QObject

from ui.dialogs.confirm_dialog import ConfirmDialog
from ui.dialogs.alert_dialog import AlertDialog


class GridVisualManager(QObject):
    """Manages grid and visual control operations for ZonesTab"""

    # Signals for grid state changes
    grid_toggled = Signal(bool)  # is_visible
    snap_toggled = Signal(bool)  # is_enabled
    grid_size_changed = Signal(int)  # size
    line_color_changed = Signal(object)  # QColor

    def __init__(self, parent_tab):
        super().__init__(parent_tab)  # Initialize QObject
        self.parent_tab = parent_tab
        self.logger = logging.getLogger(__name__)

    def toggle_grid(self):
        """Toggle grid visibility"""
        try:
            zones_view = self.parent_tab.zones_view
            if zones_view:
                is_visible = zones_view.toggle_grid()
                self.grid_toggled.emit(is_visible)

                # Update toolbar state
                if hasattr(self.parent_tab, 'toolbar_manager'):
                    self.parent_tab.toolbar_manager.set_grid_action_state(is_visible)

                # Enable snap toggle only if grid is visible
                if hasattr(self.parent_tab, 'toolbar_manager'):
                    self.parent_tab.toolbar_manager.enable_snap_action(is_visible)

                # If grid is turned off, also disable snapping
                if not is_visible and zones_view.is_snap_enabled():
                    zones_view.toggle_snap()
                    if hasattr(self.parent_tab, 'toolbar_manager'):
                        self.parent_tab.toolbar_manager.set_snap_action_state(False)

                self.logger.debug(f"Grid visibility set to {is_visible}")
                return is_visible
        except Exception as e:
            self.logger.error(f"Error toggling grid: {e}")
            return False

    def toggle_snap(self):
        """Toggle grid snapping"""
        try:
            zones_view = self.parent_tab.zones_view
            if zones_view:
                is_enabled = zones_view.toggle_snap()
                self.snap_toggled.emit(is_enabled)

                # Update toolbar state
                if hasattr(self.parent_tab, 'toolbar_manager'):
                    self.parent_tab.toolbar_manager.set_snap_action_state(is_enabled)

                self.logger.debug(f"Grid snapping set to {is_enabled}")
                return is_enabled
        except Exception as e:
            self.logger.error(f"Error toggling snap: {e}")
            return False

    def set_grid_size(self, size):
        """Set grid size"""
        try:
            zones_view = self.parent_tab.zones_view
            if zones_view and hasattr(zones_view, 'set_grid_size'):
                result = zones_view.set_grid_size(size)
                if result:
                    self.grid_size_changed.emit(size)
                    self.logger.debug(f"Grid size set to {size}")
                return result
        except Exception as e:
            self.logger.error(f"Error setting grid size: {e}")
            return False

    def set_line_color(self, color):
        """Set drawing line color"""
        try:
            zones_view = self.parent_tab.zones_view
            if zones_view and hasattr(zones_view, 'set_line_color'):
                result = zones_view.set_line_color(color)
                if result:
                    self.line_color_changed.emit(color)
                    self.logger.debug(f"Line color set to {color.name()}")
                return result
        except Exception as e:
            self.logger.error(f"Error setting line color: {e}")
            return False

    def initialize_default_grid_settings(self):
        """Initialize default grid settings (grid and snap enabled)"""
        try:
            zones_view = self.parent_tab.zones_view

            # Enable grid by default if not already visible
            if not zones_view.is_grid_visible():
                zones_view.toggle_grid()
                self.logger.debug("Grid enabled by default")

            # Enable snap to grid by default if not already enabled
            if not zones_view.is_snap_enabled():
                zones_view.toggle_snap()
                self.logger.debug("Snap to grid enabled by default")

            return True

        except Exception as e:
            self.logger.error(f"Error enabling default grid settings: {e}")
            return False

    def handle_grid_resolution_request(self, new_size):
        """Handle grid resolution change request"""
        try:
            zones_view = self.parent_tab.zones_view

            # Set the new grid size
            if self.set_grid_size(new_size):
                # If grid is not visible, ask if user wants to enable it
                if not zones_view.is_grid_visible():
                    if ConfirmDialog.ask(
                        self.parent_tab,
                        "Enable Grid",
                        "Grid is currently hidden. Would you like to show it?",
                        confirm_text="Show Grid",
                        cancel_text="Keep Hidden",
                    ):
                        self.toggle_grid()

                return True
            return False

        except Exception as e:
            self.logger.error(f"Error handling grid resolution request: {e}")
            AlertDialog.show_error(
                self.parent_tab, "Grid Error", f"Failed to set grid resolution: {str(e)}"
            )
            return False

    def get_current_grid_state(self):
        """Get current grid and snap state"""
        try:
            zones_view = self.parent_tab.zones_view
            return {
                'grid_visible': zones_view.is_grid_visible() if zones_view else False,
                'snap_enabled': zones_view.is_snap_enabled() if zones_view else False,
                'grid_size': zones_view.get_grid_size() if zones_view else 10
            }
        except Exception as e:
            self.logger.error(f"Error getting grid state: {e}")
            return {
                'grid_visible': False,
                'snap_enabled': False,
                'grid_size': 10
            }

    def sync_toolbar_with_grid_state(self):
        """Synchronize toolbar button states with actual grid state"""
        try:
            if not hasattr(self.parent_tab, 'toolbar_manager'):
                return

            state = self.get_current_grid_state()
            toolbar = self.parent_tab.toolbar_manager

            # Update toolbar button states
            toolbar.set_grid_action_state(state['grid_visible'])
            toolbar.set_snap_action_state(state['snap_enabled'])
            toolbar.enable_snap_action(state['grid_visible'])

        except Exception as e:
            self.logger.error(f"Error syncing toolbar with grid state: {e}")

    def reset_grid_to_defaults(self):
        """Reset grid settings to default values"""
        try:
            # Default settings
            default_size = 10
            default_grid_visible = True
            default_snap_enabled = True

            zones_view = self.parent_tab.zones_view

            # Set grid size
            self.set_grid_size(default_size)

            # Set grid visibility
            if zones_view.is_grid_visible() != default_grid_visible:
                self.toggle_grid()

            # Set snap state
            if zones_view.is_snap_enabled() != default_snap_enabled:
                self.toggle_snap()

            # Sync toolbar
            self.sync_toolbar_with_grid_state()

            self.logger.debug("Grid settings reset to defaults")
            return True

        except Exception as e:
            self.logger.error(f"Error resetting grid to defaults: {e}")
            return False

    def validate_grid_size(self, size):
        """Validate grid size is within acceptable range"""
        min_size = 4
        max_size = 48

        if not isinstance(size, int):
            return False, "Grid size must be an integer"

        if size < min_size:
            return False, f"Grid size must be at least {min_size} pixels"

        if size > max_size:
            return False, f"Grid size must be no more than {max_size} pixels"

        return True, "Grid size is valid"

    def get_grid_info(self):
        """Get comprehensive grid information for display or debugging"""
        try:
            zones_view = self.parent_tab.zones_view
            state = self.get_current_grid_state()

            info = {
                'state': state,
                'zones_view_available': zones_view is not None,
                'grid_manager_available': (zones_view and
                                           hasattr(zones_view, 'canvas') and
                                           hasattr(zones_view.canvas, 'grid_manager')),
                'capabilities': {
                    'can_toggle_grid': hasattr(zones_view, 'toggle_grid') if zones_view else False,
                    'can_toggle_snap': hasattr(zones_view, 'toggle_snap') if zones_view else False,
                    'can_set_size': hasattr(zones_view, 'set_grid_size') if zones_view else False,
                    'can_get_size': hasattr(zones_view, 'get_grid_size') if zones_view else False
                }
            }

            return info

        except Exception as e:
            self.logger.error(f"Error getting grid info: {e}")
            return {
                'state': {'grid_visible': False, 'snap_enabled': False, 'grid_size': 10},
                'zones_view_available': False,
                'grid_manager_available': False,
                'capabilities': {
                    'can_toggle_grid': False,
                    'can_toggle_snap': False,
                    'can_set_size': False,
                    'can_get_size': False
                },
                'error': str(e)
            }