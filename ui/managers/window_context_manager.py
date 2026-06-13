"""
Window Context Manager for AcoustiCAD.
Manages window title and project context across all tabs.
"""

from PySide6.QtWidgets import QMainWindow
from typing import Optional, Dict, Any


class WindowContextManager:
    """Manages window title based on current project"""

    def __init__(self, main_window: QMainWindow):
        """
        Initialize the window context manager.

        Args:
            main_window: The main QMainWindow instance
        """
        self.main_window = main_window
        self.current_project = None
        self.base_title = "AcoustiCAD"

        # Set initial title
        self.main_window.setWindowTitle(self.base_title)

    def set_project_context(self, project_data: Dict[str, Any]) -> None:
        """
        Update window title with project info.

        Args:
            project_data: Dictionary containing project information
        """
        self.current_project = project_data

        if project_data and project_data.get('name'):
            # Create window title with project name
            project_name = project_data['name'].strip()
            title = f"{self.base_title} - {project_name}"
            self.main_window.setWindowTitle(title)
        else:
            # Fallback to base title if no valid project name
            self.main_window.setWindowTitle(self.base_title)

    def clear_project_context(self) -> None:
        """Clear project from window title"""
        self.current_project = None
        self.main_window.setWindowTitle(self.base_title)

    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently loaded project data.

        Returns:
            Current project data or None if no project loaded
        """
        return self.current_project

    def get_current_project_name(self) -> Optional[str]:
        """
        Get the name of the currently loaded project.

        Returns:
            Project name or None if no project loaded
        """
        if self.current_project:
            return self.current_project.get('name')
        return None

    def is_project_loaded(self) -> bool:
        """
        Check if a project is currently loaded.

        Returns:
            True if project is loaded, False otherwise
        """
        return self.current_project is not None

    def update_project_name(self, new_name: str) -> None:
        """
        Update the project name in the current context (useful for project edits).

        Args:
            new_name: The new project name
        """
        if self.current_project:
            self.current_project['name'] = new_name
            self.set_project_context(self.current_project)