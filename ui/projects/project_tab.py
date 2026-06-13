import os
import json
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem,
                             QFileDialog, QFrame)
from PySide6.QtCore import Qt, Signal

from ui.projects.project_item_widget import ProjectItemWidget
from ui.projects.project_details_widget import ProjectDetailsWidget
from ui.dialogs.project_dialog import ProjectDialog
from ui.dialogs.confirm_dialog import ConfirmDialog
from ui.dialogs.alert_dialog import AlertDialog
from ui.styles.component_styles import ButtonStyles
from ui.styles.base_styles import Colors, Typography, Spacing, BorderRadius


# Trust-boundary caps for imported project files. Generous enough that real
# projects won't trip them; tight enough that absurd inputs (10MB strings,
# million-item arrays) get rejected before reaching storage.
_MAX_STRING_LEN = 50_000
_MAX_LIST_ITEMS = 1_000
_MAX_TOTAL_FIELDS = 200


def _validate_imported_project(data):
    """Validate an externally-loaded project dict before it touches storage.

    External files (user-picked JSON) are untrusted input. We verify shape,
    required fields, types, and bounds — rejecting early with a clear message
    rather than letting bad data poison the project store.

    Returns (True, None) on success, (False, error_message) on rejection.
    """
    if not isinstance(data, dict):
        return False, "File is not a valid project (expected a JSON object)."

    if len(data) > _MAX_TOTAL_FIELDS:
        return False, f"Project has too many fields ({len(data)})."

    name = data.get('name')
    if not isinstance(name, str) or not name.strip():
        return False, "Project file is missing a valid 'name' field."

    if 'id' in data and not isinstance(data['id'], (int, str)):
        return False, "Project 'id' must be a number or string."

    for key, value in data.items():
        if isinstance(value, str) and len(value) > _MAX_STRING_LEN:
            return False, f"Field '{key}' exceeds maximum length."
        if isinstance(value, list) and len(value) > _MAX_LIST_ITEMS:
            return False, f"Field '{key}' has too many items."

    return True, None


class ProjectTab(QWidget):
    """Tab for managing projects"""

    project_selected = Signal(object, str)  # project_id, project_name

    def __init__(self, storage, project_manager, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)
        self.current_project_id = None

        self.init_ui()
        self._apply_shared_styling()
        self.load_projects()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        main_layout.addWidget(self._create_project_list_panel(), 1)
        main_layout.addWidget(self._create_project_details_panel(), 1)

    def _create_card_frame(self):
        """Create a styled card frame"""
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                margin: {Spacing.SM};
            }}
        """)
        return frame

    def _create_card_title(self, text):
        """Create a styled card title with a solid color separator"""
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(6)

        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_MD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(label)

        # QWidget instead of QFrame.HLine — HLine ignores stylesheet on macOS
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet(f"background-color: {Colors.PRIMARY}; border: none;")
        layout.addWidget(line)

        return container

    def _create_project_list_panel(self):
        panel = self._create_card_frame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._create_card_title("Projects"))

        self.project_list = QListWidget()
        self.project_list.setSelectionMode(QListWidget.SingleSelection)
        self.project_list.itemSelectionChanged.connect(self.on_project_selected)
        self.project_list.itemDoubleClicked.connect(self._on_list_double_clicked)
        self.project_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                padding: {Spacing.SM};
            }}
            QListWidget::item {{
                padding: 0px;
                border-bottom: 1px solid {Colors.GRAY_100};
                border-radius: {BorderRadius.SM};
                margin: 1px;
            }}
            QListWidget::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {Colors.GRAY_50};
            }}
        """)
        layout.addWidget(self.project_list)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.new_btn = QPushButton("New Project")
        self.new_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        self.new_btn.clicked.connect(self.on_new_project)

        self.import_btn = QPushButton("Import Project")
        self.import_btn.setStyleSheet(ButtonStyles.get_secondary_button_style())
        self.import_btn.clicked.connect(self.on_open_project)

        self.delete_btn = QPushButton("Delete Project")
        self.delete_btn.setStyleSheet(ButtonStyles.get_danger_button_style())
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.on_delete_project)

        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.delete_btn)
        layout.addLayout(button_layout)

        return panel

    def _create_project_details_panel(self):
        panel = self._create_card_frame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        layout.addWidget(self._create_card_title("Project Details"))

        self.project_details = ProjectDetailsWidget()
        layout.addWidget(self.project_details)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self.open_editor_btn = QPushButton("Open in Editor")
        self.open_editor_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        self.open_editor_btn.clicked.connect(self._open_in_editor)
        self.open_editor_btn.setEnabled(False)

        self.edit_btn = QPushButton("Edit Details")
        self.edit_btn.setStyleSheet(ButtonStyles.get_secondary_button_style())
        self.edit_btn.clicked.connect(self.on_edit_project)
        self.edit_btn.setEnabled(False)

        self.export_btn = QPushButton("Export")
        self.export_btn.setStyleSheet(ButtonStyles.get_secondary_button_style())
        self.export_btn.clicked.connect(self.on_export_project)
        self.export_btn.setEnabled(False)

        action_layout.addWidget(self.open_editor_btn)
        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.export_btn)
        action_layout.addStretch()

        layout.addLayout(action_layout)

        self.details_panel = panel
        return panel

    def _apply_shared_styling(self):
        self.setStyleSheet(f"""
            ProjectTab {{
                background-color: {Colors.BG_SECONDARY};
                border: none;
            }}
        """)

    def _set_detail_buttons_enabled(self, enabled):
        self.delete_btn.setEnabled(enabled)
        self.open_editor_btn.setEnabled(enabled)
        self.edit_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)

    def load_projects(self):
        self.project_list.clear()
        for project in self.storage.get_all_projects():
            project_id = project.get('id')
            if project_id is None:
                self.logger.warning(f"Skipping project with missing ID: {project.get('name', 'Unnamed')}")
                continue

            item = QListWidgetItem()
            project_widget = ProjectItemWidget(project)
            item.setData(Qt.UserRole, project_id)
            item.setSizeHint(project_widget.sizeHint())
            self.project_list.addItem(item)
            self.project_list.setItemWidget(item, project_widget)

    def load_project_data(self, project_id):
        project_data = self.storage.load_project(project_id)
        if not project_data:
            AlertDialog.show_error(self, "Error", f"Failed to load project {project_id}")
            return False

        self.project_details.load_project_data(project_data)
        self._set_detail_buttons_enabled(True)
        self.current_project_id = project_id
        self.project_selected.emit(project_id, project_data.get('name', 'Unnamed Project'))
        return True

    def select_project_by_id(self, project_id):
        if project_id is None:
            self.logger.warning("Attempted to select a project with None ID")
            return False

        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            widget = self.project_list.itemWidget(item)
            if widget and hasattr(widget, 'project_id') and widget.project_id == project_id:
                self.project_list.setCurrentItem(item)
                return True

        self.logger.warning(f"Project with ID {project_id} not found in list")
        return False

    def on_project_selected(self):
        """Single-click: show project metadata preview without full load."""
        selected_items = self.project_list.selectedItems()
        if not selected_items:
            self._set_detail_buttons_enabled(False)
            self.current_project_id = None
            self.project_details.clear_project_details()
            return

        item = selected_items[0]
        project_id = item.data(Qt.UserRole)
        if project_id is None:
            widget = self.project_list.itemWidget(item)
            if widget and hasattr(widget, 'project_id'):
                project_id = widget.project_id

        if project_id is None:
            self.logger.warning("Failed to get project ID from selected item")
            return

        self._show_project_preview(project_id)

    def _show_project_preview(self, project_id):
        """Load and display project metadata in the details panel (no signal emission)."""
        project_data = self.storage.load_project(project_id)
        if not project_data:
            return
        self.project_details.load_project_data(project_data)
        self._set_detail_buttons_enabled(True)
        self.current_project_id = project_id

    def _open_in_editor(self):
        """Full project load + navigate to editor. Called by button or double-click."""
        if not self.current_project_id:
            return
        top = self.window()
        if hasattr(top, 'load_project') and callable(top.load_project):
            top.load_project(self.current_project_id)
        else:
            self.logger.warning("MainWindow not found, loading project directly")
            self.load_project_data(self.current_project_id)

    def _on_list_double_clicked(self, item):
        """Double-click on a project list item opens it in the editor."""
        project_id = item.data(Qt.UserRole)
        if project_id is None:
            widget = self.project_list.itemWidget(item)
            if widget and hasattr(widget, 'project_id'):
                project_id = widget.project_id
        if project_id:
            self.current_project_id = project_id
            self._open_in_editor()

    def on_new_project(self):
        dialog = ProjectDialog(self)
        if dialog.exec() != dialog.Accepted:
            return

        project_data = dialog.get_project_data()
        name = project_data.pop('name')
        description = project_data.pop('description', '')
        result = self.project_manager.create_new_project(name, description, **project_data)
        if not result:
            AlertDialog.show_error(self, "Error", "Failed to save new project")
            return

        project_id = result.get('id')
        self.logger.info(f"New project created with ID: {project_id}")
        self.load_projects()
        self.select_project_by_id(project_id)
        self.current_project_id = project_id
        self.export_btn.setEnabled(True)
        self.project_selected.emit(project_id, result.get('name', ''))

    def on_edit_project(self):
        if not self.current_project_id:
            return

        project_data = self.storage.load_project(self.current_project_id)
        if not project_data:
            AlertDialog.show_error(self, "Error", f"Failed to load project {self.current_project_id}")
            return

        dialog = ProjectDialog(self, existing_project=project_data)
        if dialog.exec() != dialog.Accepted:
            return

        updated_data = dialog.get_project_data()
        saved_project = self.storage.save_project(updated_data)
        if not saved_project:
            AlertDialog.show_error(self, "Error", "Failed to save project changes")
            return

        self.load_projects()
        self.select_project_by_id(saved_project.get('id'))
        self.load_project_data(saved_project.get('id'))

        self.project_manager.project_modified = False
        self.project_manager.zones_modified = False

    def on_open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project",
            os.path.expanduser("~"),
            "Project Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except json.JSONDecodeError as e:
            AlertDialog.show_error(self, "Invalid Project File",
                                   f"This file is not valid JSON:\n{e}")
            return
        except Exception as e:
            AlertDialog.show_error(self, "Error", f"Failed to open project: {str(e)}")
            return

        is_valid, error_msg = _validate_imported_project(project_data)
        if not is_valid:
            self.logger.warning(f"Rejected import of {file_path}: {error_msg}")
            AlertDialog.show_error(self, "Invalid Project File", error_msg)
            return

        saved_project = self.storage.save_project(project_data)
        if not saved_project:
            AlertDialog.show_error(self, "Error", "Failed to import project")
            return

        self.load_projects()
        self.select_project_by_id(saved_project.get('id'))

    def on_delete_project(self):
        if not self.current_project_id:
            return

        if not ConfirmDialog.ask(
            self, "Delete Project",
            "Are you sure you want to delete this project? This cannot be undone.",
            confirm_text="Delete Project",
            cancel_text="Cancel",
            danger=True
        ):
            return

        if self.storage.delete_project(self.current_project_id):
            self.load_projects()
            self.project_list.clearSelection()
            self.current_project_id = None
            self._set_detail_buttons_enabled(False)
            self.project_details.clear_project_details()
        else:
            AlertDialog.show_error(self, "Error", "Failed to delete project")

    def on_export_project(self):
        if not self.current_project_id:
            return

        project_data = self.storage.load_project(self.current_project_id)
        if not project_data:
            AlertDialog.show_error(self, "Error", "Failed to load project for export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Project",
            os.path.join(os.path.expanduser("~"), f"{project_data.get('name', 'Project')}.json"),
            "Project Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            AlertDialog.show_info(self, "Success", f"Project exported to:\n{file_path}")
        except Exception as e:
            AlertDialog.show_error(self, "Error", f"Failed to export project: {str(e)}")

    def load_project(self, project_id):
        """Load a project by ID (called from external components)"""
        if project_id is None:
            self.logger.error("Attempted to load project with None ID")
            return False

        if not self.storage.load_project(project_id):
            self.logger.error(f"Project with ID {project_id} not found in storage")
            return False

        if not self.select_project_by_id(project_id):
            self.logger.info(f"Project {project_id} not in list, refreshing")
            self.load_projects()
            if not self.select_project_by_id(project_id):
                self.logger.warning(f"Project {project_id} still not found after refresh")
                return False

        self.load_project_data(project_id)

        self.project_manager.project_modified = False
        self.project_manager.zones_modified = False

        return True
