import logging
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QMainWindow, QLabel, QStatusBar, QApplication, QMessageBox)

from ui.dialogs.unsaved_changes_dialog import UnsavedChangesDialog
from ui.dialogs.alert_dialog import AlertDialog
from ui.dialogs.confirm_dialog import ConfirmDialog
from core.project_manager import ProjectManager

from ui.styles.main_window_styles import apply_professional_main_window_styling
from ui.managers.window_context_manager import WindowContextManager
from .constants import UIConstants, Messages, WindowSettings, AppInfo
from .error_decorator import handle_errors, handle_project_errors, handle_ui_errors, handle_save_errors
from .menu_manager import MenuManager
from .tab_manager import TabManager
from utils.report_generator import ReportGenerator


class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""

    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MainWindow initializing")

        try:
            # Initialize project manager first
            self.project_manager = ProjectManager(storage)

            # Initialize window context manager
            self.context_manager = WindowContextManager(self)

            # State tracking
            self.closing_application = False

            # Connect project manager signals to handle changes
            self.project_manager.project_changed.connect(self.on_project_changed)

            # Initialize managers
            self.menu_manager = MenuManager(self, storage, self.project_manager)
            self.tab_manager = TabManager(self, storage, self.project_manager)

            # Initialize UI
            self.init_ui()

            # Connect tab signals after tabs are created
            self.tab_manager.connect_tab_signals()

            # Create shared report generator AFTER tabs are created
            self.shared_report_generator = ReportGenerator(self, storage)

            # Configure with visual formatter using plotter tab's speaker view
            if (hasattr(self.tab_manager, 'plotter_tab') and
                    self.tab_manager.plotter_tab and
                    hasattr(self.tab_manager.plotter_tab, 'speaker_view')):
                self.shared_report_generator.add_visual_formatter(
                    self.tab_manager.plotter_tab.speaker_view
                )
                self.logger.info("Shared report generator configured with visual formatter")
            else:
                self.logger.warning("Could not configure visual formatter - plotter tab or speaker view not available")

            # Pass shared generator to menu manager
            self.menu_manager.set_report_generator(self.shared_report_generator)

            # Pass shared generator to plotter tab
            if (self.tab_manager and
                self.tab_manager.plotter_tab):
                self.tab_manager.plotter_tab.set_report_generator(self.shared_report_generator)

            # Connect application exit signal
            app = QApplication.instance()
            if app:
                app.aboutToQuit.connect(self.on_application_exit)

            self.logger.info("MainWindow initialized")

        except Exception as e:
            self.logger.critical(f"Critical error during MainWindow initialization: {e}", exc_info=True)
            raise  # Re-raise to crash the app instead of continuing with broken state

    @handle_ui_errors()
    def init_ui(self):
        """Initialize the UI components"""
        try:
            # Set window properties
            self.setWindowTitle(AppInfo.WINDOW_TITLE)
            self.setMinimumSize(UIConstants.MIN_WINDOW_WIDTH, UIConstants.MIN_WINDOW_HEIGHT)

            # Set window icon (shows in dock, taskbar, and title bar on Windows)
            icon_path = os.path.join(os.path.dirname(__file__),
                                     '..', 'resources', 'AppIcon_preview.png')
            icon_path = os.path.normpath(icon_path)
            if os.path.exists(icon_path):
                QApplication.instance().setWindowIcon(QIcon(icon_path))

            # Restore window settings AFTER setting minimum size
            self.restore_window_settings()

            # Enable touch and gesture support globally
            if UIConstants.TOUCH_SYNTHESIZE_MOUSE:
                QApplication.instance().setAttribute(Qt.AA_SynthesizeMouseForUnhandledTouchEvents)

            # Create tabs using tab manager
            self.tab_manager.create_tabs()

            # Set up status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)

            # Add status label
            self.status_label = QLabel(Messages.READY)
            self.status_bar.addWidget(self.status_label)

            # Set up menu bar using menu manager
            self.menu_manager.create_menu_bar()

            self.logger.debug("UI initialized")

            apply_professional_main_window_styling(self)

            self.logger.debug("UI initialized with modern styling")


        except Exception as e:
            self.logger.critical(f"Critical error during UI initialization: {e}", exc_info=True)
            raise  # Don't suppress critical UI initialization errors


    @handle_ui_errors()
    def on_project_changed(self):
        """Handle project changed signal"""
        try:
            # Update project manager's modification flag
            self.project_manager.project_modified = True

            # If we have a loaded zones_view, ensure it's connected for thumbnails
            self.connect_zones_view_to_project_manager()

            has_unsaved = self.project_manager and self.project_manager.has_unsaved_changes()

            # Update status bar
            self.status_label.setText(Messages.UNSAVED_CHANGES if has_unsaved else Messages.READY)

            # Update editor header bar modification dot (legacy, off-screen widget)
            if hasattr(self.tab_manager, 'editor_header') and self.tab_manager.editor_header:
                self.tab_manager.editor_header.set_modified(bool(has_unsaved))

            # Update the visible toolbar's modification indicator
            if hasattr(self.tab_manager, '_set_toolbar_modified'):
                self.tab_manager._set_toolbar_modified(bool(has_unsaved))

            # Keep plotter toolbar modified dot in sync
            if hasattr(self.tab_manager, '_set_plotter_toolbar_modified'):
                self.tab_manager._set_plotter_toolbar_modified(bool(has_unsaved))

            self.logger.debug("Project modified state updated via on_project_changed")
        except Exception as e:
            try:
                self.logger.error(f"Error in on_project_changed: {e}")
            except:
                print(f"Error in on_project_changed: {e}")

    def on_application_exit(self):
        """Handle application exit - called by aboutToQuit signal"""
        self.logger.debug("Application exit signal received")
        # All handling is done in closeEvent

    def closeEvent(self, event):
        """Handle window close event with unsaved changes check and comprehensive error handling"""
        self.logger.debug("Close event received")

        # Prevent handling the close event multiple times
        if self.closing_application:
            self.logger.debug("Close event already in progress, accepting")
            super().closeEvent(event)
            return

        self.closing_application = True

        try:
            # Check for unsaved changes with proper error handling
            try:
                has_unsaved = self.project_manager.has_unsaved_changes()
                self.logger.debug(f"Unsaved changes check result: {has_unsaved}")
            except Exception as e:
                self.logger.error(f"Error checking for unsaved changes: {e}")
                # Assume no unsaved changes if we can't check
                has_unsaved = False

            if has_unsaved:
                self.logger.debug("Unsaved changes detected during close")

                try:
                    dialog = UnsavedChangesDialog(Messages.UNSAVED_CHANGES_EXIT, self)
                    result = dialog.exec()
                    self.logger.debug(f"Unsaved changes dialog result: {result}")

                    if result == dialog.SAVE:
                        # Save the current project
                        self.logger.debug("Saving project before exit")

                        try:
                            saved = self.save_current_project()
                            self.logger.debug(f"Save result: {saved}")
                        except Exception as save_error:
                            self.logger.error(f"Error saving project during close: {save_error}")
                            saved = False

                        if not saved:
                            # If save failed, give the user a chance to cancel closing
                            try:
                                if not ConfirmDialog.ask(
                                    self, "Save Failed", Messages.SAVE_FAILED_EXIT,
                                    confirm_text="Exit Anyway", cancel_text="Stay"
                                ):
                                    self.logger.debug("User canceled exit after save failure")
                                    event.ignore()
                                    self.closing_application = False
                                    return
                            except Exception as dialog_error:
                                self.logger.error(f"Error showing save failed dialog: {dialog_error}")
                                # Continue with exit if dialog fails

                    elif result == dialog.CANCEL:
                        # Cancel exit
                        self.logger.debug("User canceled application exit")
                        event.ignore()
                        self.closing_application = False
                        return

                except Exception as dialog_error:
                    self.logger.error(f"Error handling unsaved changes dialog: {dialog_error}")
                    # Continue with exit if dialog handling fails

            # Save window position and size with error handling
            try:
                self.logger.debug("Saving window settings before exit")
                self.save_window_settings()
            except Exception as settings_error:
                self.logger.error(f"Error saving window settings: {settings_error}")
                # Continue with exit even if settings save fails

            # Perform cleanup operations
            try:
                self._perform_cleanup()
            except Exception as cleanup_error:
                self.logger.error(f"Error during cleanup: {cleanup_error}")
                # Continue with exit even if cleanup fails

            # Accept the close event
            self.logger.info("Application closing gracefully")
            event.accept()

        except Exception as e:
            self.logger.critical(f"Critical error during close event: {e}", exc_info=True)

            # Show critical error dialog to user
            try:
                AlertDialog.show_error(
                    self,
                    "Critical Error",
                    f"A critical error occurred while closing the application:\n\n{str(e)}\n\n"
                    "The application will still attempt to close."
                )
            except Exception:
                # If we can't even show an error dialog, just log it
                self.logger.critical("Could not show critical error dialog")

            # In case of critical error, still allow closing
            event.accept()

        finally:
            # Reset flag based on whether closing was successful
            if event.isAccepted():
                self.closing_application = True
                self.logger.debug("Close event accepted")
            else:
                self.closing_application = False
                self.logger.debug("Close event rejected")

    @handle_ui_errors()
    def save_window_settings(self):
        """Save the window position and state"""
        settings = self.storage.load_settings()

        # Convert QByteArray to hex string properly
        geometry = self.saveGeometry()
        geometry_hex = geometry.toHex().data().decode('utf-8')
        settings[WindowSettings.WINDOW_GEOMETRY] = geometry_hex

        state = self.saveState()
        state_hex = state.toHex().data().decode('utf-8')
        settings[WindowSettings.WINDOW_STATE] = state_hex

        self.storage.save_settings(settings)
        self.logger.debug("Window settings saved")

    @handle_ui_errors()
    def restore_window_settings(self):
        """Restore window position and size from settings"""
        settings = self.storage.load_settings()

        # Restore geometry
        geometry = settings.get(WindowSettings.WINDOW_GEOMETRY)
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
                self.logger.debug("Restored window geometry")
            except Exception as e:
                self.logger.error(f"Error restoring geometry: {e}")

        # Restore window state
        window_state = settings.get(WindowSettings.WINDOW_STATE)
        if window_state:
            try:
                self.restoreState(bytes.fromhex(window_state))
                self.logger.debug("Restored window state")
            except Exception as e:
                self.logger.error(f"Error restoring state: {e}")

    @handle_project_errors()
    def on_new_project(self):
        """Handle new project action"""
        # Check for unsaved changes first
        if self.project_manager.has_unsaved_changes():
            dialog = UnsavedChangesDialog(Messages.UNSAVED_CHANGES_NEW_PROJECT, self)
            result = dialog.exec()

            if result == dialog.SAVE:
                # Save current project
                if not self.save_current_project():
                    return  # Don't proceed if save failed
            elif result == dialog.CANCEL:
                return  # Cancel the operation

        # Create new project in project tab
        self.tab_manager.project_tab.on_new_project()

        # Connect zones_view to project_manager for thumbnail generation
        self.connect_zones_view_to_project_manager()

        # Navigate to the editor with the newly created project
        project_data = self.project_manager.get_current_project_data()
        if project_data:
            self.open_project_editor(project_data.get('name', 'New Project'))

    @handle_project_errors()
    def on_open_project(self):
        """Handle open project action"""
        # Check for unsaved changes first
        if self.project_manager.has_unsaved_changes():
            dialog = UnsavedChangesDialog(Messages.UNSAVED_CHANGES_OPEN_PROJECT, self)
            result = dialog.exec()

            if result == dialog.SAVE:
                # Save current project
                if not self.save_current_project():
                    return  # Don't proceed if save failed
            elif result == dialog.CANCEL:
                return  # Cancel the operation

        # Open project in project tab
        self.tab_manager.project_tab.on_open_project()

    @handle_save_errors()
    def on_save(self, checked=None):
        """Handle save action"""
        saved = self.save_current_project()

        if saved:
            self.status_label.setText(Messages.PROJECT_SAVED)
            self.logger.info("Project saved successfully")
        else:
            self.status_label.setText(Messages.SAVE_FAILED)
            self.logger.warning("Failed to save project")

        return saved

    @handle_save_errors()
    def save_current_project(self):
        """Save the current project with data from all tabs"""
        project_id = self.project_manager.get_current_project_id()
        if not project_id:
            self.logger.warning("No project selected to save")
            return False

        project_data = self.project_manager.get_current_project_data()
        if not project_data:
            self.logger.error("No project data available")
            return False

        # Create a copy of project data
        updated_project_data = project_data.copy()

        # Flag to track if zones were modified
        zones_were_modified = False

        # Save zones data if zones tab exists
        if (self.tab_manager and
                hasattr(self.tab_manager, 'zones_tab') and
                self.tab_manager.zones_tab and
                hasattr(self.tab_manager.zones_tab, 'save_data')):

            if self.tab_manager.zones_tab.save_data(updated_project_data):
                zones_were_modified = True
            else:
                self.logger.warning("Failed to save zones data")
                if hasattr(self, 'status_label') and self.status_label:
                    self.status_label.setText(Messages.SAVE_FAILED)
                return False

        # Save plotter data if plotter tab exists
        if (self.tab_manager and
                hasattr(self.tab_manager, 'plotter_tab') and
                self.tab_manager.plotter_tab):

            # Get speaker layout data
            if hasattr(self.tab_manager.plotter_tab,
                       'speaker_view') and self.tab_manager.plotter_tab.speaker_view:
                if hasattr(self.tab_manager.plotter_tab.speaker_view, 'layout_data'):
                    speaker_layout = {}
                    layout_data = self.tab_manager.plotter_tab.speaker_view.layout_data
                    if layout_data:
                        for zone_id, speakers in layout_data.items():
                            if speakers:  # Only include zones with speakers
                                speaker_layout[zone_id] = speakers

                    updated_project_data['speaker_layout'] = speaker_layout

                # Get obstruction layout data
                if hasattr(self.tab_manager.plotter_tab.speaker_view, 'obstruction_manager'):
                    obstruction_manager = self.tab_manager.plotter_tab.speaker_view.obstruction_manager
                    if obstruction_manager and hasattr(obstruction_manager, 'zone_obstructions'):
                        updated_project_data['obstruction_layout'] = obstruction_manager.zone_obstructions

        # Update the project manager's data
        self.project_manager.current_project_data = updated_project_data

        self.project_manager.zones_modified = zones_were_modified

        # Save project
        save_result = self.project_manager.save_project()

        if save_result:
            self.logger.info(f"Project {project_id} saved successfully")

            # Reset modification flags in project manager
            self.project_manager.project_modified = False
            self.project_manager.zones_modified = False

            # Update window context with saved project data
            self.context_manager.set_project_context(updated_project_data)

            # Refresh the project list to show updated thumbnail
            if (self.tab_manager and
                    hasattr(self.tab_manager, 'project_tab') and
                    self.tab_manager.project_tab and
                    hasattr(self.tab_manager.project_tab, 'load_projects')):
                self.tab_manager.project_tab.load_projects()

            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(Messages.PROJECT_SAVED)
            return True
        else:
            self.logger.error(f"Failed to save project {project_id}")
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(Messages.SAVE_FAILED)
            AlertDialog.show_error(self, "Save Error", "Failed to save project.")
            return False

    @handle_project_errors()
    def load_project(self, project_id):
        """
        Load a project by ID

        Args:
            project_id: The ID of the project to load
        Returns:
            bool: True if project was successfully loaded, False otherwise
        """
        if project_id is None:
            self.logger.error("Cannot load project: project_id is None")
            return False

        # First, check for unsaved changes
        if self.project_manager and self.project_manager.has_unsaved_changes():
            dialog = UnsavedChangesDialog(Messages.UNSAVED_CHANGES_LOAD_PROJECT, self)
            result = dialog.exec()

            if result == dialog.SAVE:
                # Save current project
                if not self.save_current_project():
                    # If save failed, ask if they want to continue anyway
                    if not ConfirmDialog.ask(
                        self, "Save Failed", Messages.SAVE_FAILED_LOAD,
                        confirm_text="Load Anyway", cancel_text="Cancel"
                    ):
                        return False
            elif result == dialog.CANCEL:
                # Cancel loading
                return False

        # Load the project in project manager
        success = self.project_manager.load_project(project_id)

        if success:
            # Connect zones_view to project_manager for thumbnail generation
            self.connect_zones_view_to_project_manager()

            # Update window context with loaded project
            project_data = self.project_manager.get_current_project_data()
            if project_data:
                self.context_manager.set_project_context(project_data)

            # Load the project in project tab
            result = self.tab_manager.project_tab.load_project(project_id)

            if result:
                # Navigate to the editor view
                project_name = project_data.get('name', 'Project') if project_data else 'Project'
                self.open_project_editor(project_name)
                self.status_label.setText(Messages.PROJECT_LOADED)
                self.logger.info(f"Project loaded: {project_id}")
                return True
            else:
                self.status_label.setText(Messages.LOAD_FAILED)
                self.logger.warning(f"Failed to load project: {project_id}")
                # Clear context on failure
                self.context_manager.clear_project_context()
                return False
        else:
            self.status_label.setText(Messages.LOAD_FAILED)
            self.logger.warning(f"Failed to load project in project manager: {project_id}")
            # Clear context on failure
            self.context_manager.clear_project_context()
            return False

    @handle_ui_errors()
    def connect_zones_view_to_project_manager(self):
        """Ensure zones_view is connected to project_manager for thumbnail generation"""
        try:
            # Find the zones_view component
            if (hasattr(self.tab_manager, 'zones_tab') and
                    self.tab_manager.zones_tab and
                    hasattr(self.tab_manager.zones_tab, 'zones_view') and
                    self.tab_manager.zones_tab.zones_view):

                # Set it in the project manager
                self.project_manager.set_zones_view(self.tab_manager.zones_tab.zones_view)
                self.logger.debug("Connected zones_view to project_manager for thumbnails")
            else:
                self.logger.warning("Could not find zones_view to connect to project_manager")
        except Exception as e:
            # Safe error handling
            try:
                self.logger.error(f"Error connecting zones_view: {e}")
            except:
                print(f"Error connecting zones_view: {e}")


    def open_project_editor(self, project_name: str):
        """Switch to the editor view for the currently loaded project."""
        self.tab_manager.show_editor(project_name)

    def back_to_projects(self):
        """Navigate back to the project browser, prompting for unsaved changes."""
        if self.project_manager and self.project_manager.has_unsaved_changes():
            dialog = UnsavedChangesDialog(Messages.UNSAVED_CHANGES_LOAD_PROJECT, self)
            result = dialog.exec()
            if result == dialog.SAVE:
                if not self.save_current_project():
                    return
            elif result == dialog.CANCEL:
                return
        self.tab_manager.show_home_screen()

    @handle_ui_errors()
    def on_about(self):
        """Handle about action"""
        version = QApplication.instance().applicationVersion()
        QMessageBox.about(self, Messages.ABOUT_TITLE,
                          Messages.ABOUT_TEXT.format(version=version))

    @handle_ui_errors()
    def change_status_message(self, message, timeout=UIConstants.STATUS_MESSAGE_TIMEOUT):
        """
        Show a temporary message in the status bar

        Args:
            message (str): The message to display
            timeout (int): Time in milliseconds to show the message, or 0 for permanent
        """
        self.status_bar.showMessage(message, timeout)

    # Properties to provide easy access to tab components
    @property
    def project_tab(self):
        """Get the project tab"""
        return self.tab_manager.project_tab if self.tab_manager else None

    @property
    def zones_tab(self):
        """Get the zones tab"""
        return self.tab_manager.zones_tab if self.tab_manager else None

    @property
    def plotter_tab(self):
        """Get the plotter tab"""
        return self.tab_manager.plotter_tab if self.tab_manager else None

    @property
    def tab_widget(self):
        """Get the tab widget"""
        return self.tab_manager.tab_widget if self.tab_manager else None

    def _perform_cleanup(self):
        """Perform cleanup operations before application exit"""
        self.logger.debug("Starting application cleanup")

        try:
            # Clean up context manager
            if hasattr(self, 'context_manager') and self.context_manager:
                self.context_manager.clear_project_context()

            # Disconnect tab manager signals to prevent memory leaks
            if hasattr(self, 'tab_manager') and self.tab_manager:
                self.logger.debug("Cleaning up tab manager")
                self._cleanup_tab_manager()

            # Disconnect main window signals
            try:
                app = QApplication.instance()
                if app and hasattr(app, 'aboutToQuit'):
                    app.aboutToQuit.disconnect()
            except Exception:
                pass  # Signal might not be connected

            # Clean up project manager signals
            if hasattr(self, 'project_manager') and self.project_manager:
                try:
                    self.project_manager.project_changed.disconnect()
                except Exception:
                    pass

            # Clean up report generator resources
            if hasattr(self, 'shared_report_generator') and self.shared_report_generator:
                self.logger.debug("Cleaning up report generator resources")
                if hasattr(self.shared_report_generator, 'clear_cache'):
                    self.shared_report_generator.clear_cache()

            self.logger.debug("Application cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup operations: {e}")

    def _cleanup_tab_manager(self):
        """Clean up tab manager resources and signal connections"""
        try:
            # Disconnect all signal connections
            for source, signal_name, target, slot_name, description in self.tab_manager.signal_connections:
                try:
                    signal = getattr(source, signal_name, None)
                    if signal and hasattr(signal, 'disconnect'):
                        signal.disconnect()
                except Exception:
                    pass  # Signal might already be disconnected

            # Clear connection lists
            self.tab_manager.signal_connections.clear()
            self.tab_manager.pending_connections.clear()

            # Disconnect tab widget signals
            if self.tab_manager.tab_widget:
                try:
                    self.tab_manager.tab_widget.currentChanged.disconnect()
                except Exception:
                    pass

            # Clear references to break circular dependencies
            self.tab_manager.project_tab = None
            self.tab_manager.zones_tab = None
            self.tab_manager.plotter_tab = None
            self.tab_manager.tab_widget = None
            self.tab_manager.stack_widget = None
            self.tab_manager.editor_header = None

            self.logger.debug("Tab manager cleanup completed")

        except Exception as e:
            self.logger.error(f"Error cleaning up tab manager: {e}")