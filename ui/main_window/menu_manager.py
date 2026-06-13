"""
Menu management for the main window.
"""

import logging
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from utils.report_menu_helper import ReportMenuHelper
from ui.main_window.constants import Messages
from ui.main_window.error_decorator import handle_ui_errors


class MenuManager:
    """Manages menu creation and updates for the main window"""

    def __init__(self, main_window, storage, project_manager):
        self.main_window = main_window
        self.storage = storage
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)

        # Keep references to menus that need updating
        self.recent_projects_menu = None
        self.report_helper = None
        self._reports_menu = None

    @handle_ui_errors()
    def create_menu_bar(self):
        """Create the complete menu bar"""
        self._create_file_menu()
        self._create_reports_menu()
        self._create_help_menu()
        self.logger.debug("Menu bar created")

    def _create_file_menu(self):
        """Create the File menu"""
        file_menu = self.main_window.menuBar().addMenu("&File")

        # New Project
        new_action = QAction("&New Project", self.main_window)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new project")
        new_action.triggered.connect(self.main_window.on_new_project)
        file_menu.addAction(new_action)

        # Open Project
        open_action = QAction("&Open Project", self.main_window)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing project")
        open_action.triggered.connect(self.main_window.on_open_project)
        file_menu.addAction(open_action)

        # Recent Projects submenu
        self.recent_projects_menu = QMenu("Recent Projects", self.main_window)
        file_menu.addMenu(self.recent_projects_menu)
        self.update_recent_projects_menu()

        file_menu.addSeparator()

        # Save
        save_action = QAction("&Save", self.main_window)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current project")
        save_action.triggered.connect(self.main_window.on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("E&xit", self.main_window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)

    def _create_reports_menu(self):
        """Create the Reports menu placeholder; populated later via set_report_generator()."""
        self._reports_menu = self.main_window.menuBar().addMenu("&Reports")

    def set_report_generator(self, shared_report_generator):
        """Set the shared report generator and create the report menu helper"""
        if hasattr(self.main_window, 'zones_tab'):
            # Get speaker view from plotter tab for the report helper
            speaker_view = None
            if (hasattr(self.main_window, 'tab_manager') and
                    hasattr(self.main_window.tab_manager, 'plotter_tab') and
                    self.main_window.tab_manager.plotter_tab and
                    hasattr(self.main_window.tab_manager.plotter_tab, 'speaker_view')):
                speaker_view = self.main_window.tab_manager.plotter_tab.speaker_view

            # Create ReportMenuHelper with shared generator
            self.report_helper = ReportMenuHelper(
                self.main_window,
                self.main_window.zones_tab,
                self.project_manager,
                speaker_view=speaker_view
            )

            # Override the report generator with our shared one
            self.report_helper.report_generator = shared_report_generator

            # Populate the pre-created Reports menu
            if self._reports_menu:
                self.report_helper.create_report_menu(menu_bar=self._reports_menu)
                self.logger.info("Report menu helper configured with shared report generator")
            else:
                self.logger.error("Could not find Reports menu to populate")
        else:
            self.logger.error("zones_tab not available for report menu helper")

    def _create_help_menu(self):
        """Create the Help menu"""
        help_menu = self.main_window.menuBar().addMenu("&Help")

        # About
        about_action = QAction("&About", self.main_window)
        about_action.setStatusTip(Messages.ABOUT_TITLE)
        about_action.triggered.connect(self.main_window.on_about)
        help_menu.addAction(about_action)

    @handle_ui_errors()
    def update_recent_projects_menu(self):
        """Update the recent projects menu"""
        if not self.recent_projects_menu:
            return

        self.recent_projects_menu.clear()

        # Get recent projects from storage
        settings = self.storage.load_settings()
        recent_projects = settings.get("recent_projects", [])

        if not recent_projects:
            no_recent = QAction(Messages.NO_RECENT_PROJECTS, self.main_window)
            no_recent.setEnabled(False)
            self.recent_projects_menu.addAction(no_recent)
            return

        # Add recent projects
        for project in recent_projects:
            project_id = project.get("id")
            project_name = project.get("name", "Unnamed Project")

            if project_id is not None:
                action = QAction(project_name, self.main_window)
                action.setData(project_id)
                action.triggered.connect(self._open_recent_project)
                self.recent_projects_menu.addAction(action)

        # Add separator and clear option
        self.recent_projects_menu.addSeparator()
        clear_action = QAction(Messages.CLEAR_RECENT_PROJECTS, self.main_window)
        clear_action.triggered.connect(self._clear_recent_projects)
        self.recent_projects_menu.addAction(clear_action)


    @handle_ui_errors()
    def _open_recent_project(self):
        """Open a project from the recent projects menu"""
        action = self.main_window.sender()
        if action:
            project_id = action.data()
            if project_id is not None:
                self.main_window.load_project(project_id)

    @handle_ui_errors()
    def _clear_recent_projects(self):
        """Clear the recent projects list"""
        settings = self.storage.load_settings()
        settings["recent_projects"] = []
        self.storage.save_settings(settings)
        self.update_recent_projects_menu()
        self.logger.info("Recent projects list cleared")