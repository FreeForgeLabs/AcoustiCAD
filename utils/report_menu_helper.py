import logging
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from utils.report_generator import ReportGenerator
from utils.report_validation import ReportValidator
from utils.report_data_models import BatchReportResult
from ui.dialogs.alert_dialog import AlertDialog
from ui.dialogs.confirm_dialog import ConfirmDialog


class ReportMenuHelper:
    """
    Helper class to add report functionality to the application
    Refactored to work with the new modular report generator
    """

    def __init__(self, parent, zones_tab, project_manager, speaker_view=None):
        """
        Initialize the report menu helper

        Args:
            parent: The parent widget (usually main window)
            zones_tab: The zones tab instance
            project_manager: The project manager instance
            speaker_view: Optional speaker view for visual reports
        """
        self.parent = parent
        self.zones_tab = zones_tab
        self.project_manager = project_manager
        self.speaker_view = speaker_view
        self.logger = logging.getLogger(__name__)

        # Get storage from project manager
        storage = getattr(project_manager, 'storage', None)

        # Create report generator and validator
        self.report_generator = ReportGenerator(parent, storage)
        self.validator = ReportValidator(self.logger)

        # Add visual formatter if speaker view is available
        if speaker_view:
            self.report_generator.add_visual_formatter(speaker_view)
            self.logger.info("Visual formatter added to report generator")
        else:
            self.logger.debug("No speaker view provided - visual reports will not be available")

    def create_report_menu(self, toolbar=None, menu_bar=None) -> QMenu:
        """
        Create a report menu and add to toolbar/menu bar

        Args:
            toolbar: The toolbar to add report actions to (optional)
            menu_bar: The menu bar to add report menu to (optional)

        Returns:
            QMenu: The created report menu
        """
        # Create report menu
        self.report_menu = QMenu("Reports", self.parent)

        # Add report actions
        self._add_project_report_action()
        self._add_speaker_report_action()
        self.report_menu.addSeparator()
        self._add_material_list_action()

        # Add submenu for batch operations
        self._add_batch_operations_submenu()

        # Add settings submenu
        self._add_settings_submenu()

        # Add menu to menu bar if provided
        if menu_bar:
            menu_bar.addMenu(self.report_menu)

        return self.report_menu

    def _add_project_report_action(self):
        """Add project report action to menu"""
        action = QAction("Generate Project Report", self.parent)
        action.triggered.connect(self.generate_project_report)
        action.setStatusTip("Generate a comprehensive project report")
        action.setToolTip("Create a detailed report of the current project including all zones")
        self.report_menu.addAction(action)

    def _add_speaker_report_action(self):
        """Add speaker report action to menu"""
        action = QAction("Generate Speaker Report", self.parent)
        action.triggered.connect(self.generate_speaker_report)
        action.setStatusTip("Generate a detailed speaker placement report")
        action.setToolTip("Create a visual report showing speaker placements and calculations")
        self.report_menu.addAction(action)

    def _add_material_list_action(self):
        """Add material list action to menu"""
        action = QAction("Generate Material List", self.parent)
        action.triggered.connect(self.generate_material_list)
        action.setStatusTip("Generate a consolidated list of materials")
        action.setToolTip("Create a CSV list of all materials for ordering and inventory")
        self.report_menu.addAction(action)

    def _add_batch_operations_submenu(self):
        """Add batch operations submenu"""
        batch_menu = QMenu("Batch Operations", self.parent)

        # All reports action
        all_reports_action = QAction("Generate All Reports", self.parent)
        all_reports_action.triggered.connect(self.generate_all_reports)
        all_reports_action.setStatusTip("Generate all available reports")
        all_reports_action.setToolTip("Create project report, speaker report, and material list")
        batch_menu.addAction(all_reports_action)

        # Custom batch action
        custom_batch_action = QAction("Custom Report Package", self.parent)
        custom_batch_action.triggered.connect(self.generate_custom_report_package)
        custom_batch_action.setStatusTip("Generate custom selection of reports")
        custom_batch_action.setToolTip("Choose which reports to generate in a batch")
        batch_menu.addAction(custom_batch_action)

        self.report_menu.addMenu(batch_menu)

    def _add_settings_submenu(self):
        """Add settings submenu"""
        settings_menu = QMenu("Settings", self.parent)

        # Set reports directory
        set_dir_action = QAction("Set Reports Directory", self.parent)
        set_dir_action.triggered.connect(self.set_reports_directory_dialog)
        set_dir_action.setStatusTip("Set default directory for saving reports")
        settings_menu.addAction(set_dir_action)

        # View current settings
        view_settings_action = QAction("View Current Settings", self.parent)
        view_settings_action.triggered.connect(self.show_current_settings)
        view_settings_action.setStatusTip("View current report generation settings")
        settings_menu.addAction(view_settings_action)

        self.report_menu.addMenu(settings_menu)

    def generate_project_report(self) -> bool:
        """
        Generate a comprehensive project report

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate project state
            if not self._validate_project_state():
                return False

            # Get and validate data
            project_data, zones_data = self._get_and_validate_basic_data()
            if not project_data or not zones_data:
                return False

            # Validate report-specific data
            validation = self.validator.validate_project_report_data(project_data, zones_data)
            if validation['errors']:
                self._show_validation_errors("Project Report", validation['errors'])
                return False

            # Show warnings if any
            if validation['warnings']:
                self._show_validation_warnings("Project Report", validation['warnings'])

            # Save unsaved changes if needed
            if not self._handle_unsaved_changes():
                return False

            # Generate report
            result = self.report_generator.generate_project_report(project_data, zones_data)

            if result.success:
                self._show_success("Project report generated successfully.", result.file_path)
                return True
            else:
                self._show_error(f"Failed to generate project report: {result.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"Error generating project report: {e}", exc_info=True)
            self._show_error(f"Failed to generate project report: {str(e)}")
            return False

    def generate_speaker_report(self) -> bool:
        """
        Generate a comprehensive speaker placement report

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate project state
            if not self._validate_project_state():
                return False

            # Get and validate data
            project_data, zones_data = self._get_and_validate_basic_data()
            if not project_data or not zones_data:
                return False

            # Get speaker layout
            speaker_layout = self._get_speaker_layout()
            if not speaker_layout:
                self._show_warning("No Speaker Data",
                                   "No speaker placement data found. Please place speakers before generating this report.")
                return False

            # Validate speaker report data
            validation = self.validator.validate_speaker_report_data(project_data, zones_data, speaker_layout)
            if validation['errors']:
                self._show_validation_errors("Speaker Report", validation['errors'])
                return False

            # Show warnings if any
            if validation['warnings']:
                self._show_validation_warnings("Speaker Report", validation['warnings'])

            # Save unsaved changes if needed
            if not self._handle_unsaved_changes():
                return False

            # Generate report — pass zones_data so the generator can match speakers to zones
            result = self.report_generator.generate_speaker_report(project_data, speaker_layout, zones_data)

            if result.success:
                self._show_success("Speaker report generated successfully.", result.file_path)
                return True
            else:
                self._show_error(f"Failed to generate speaker report: {result.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"Error generating speaker report: {e}", exc_info=True)
            self._show_error(f"Failed to generate speaker report: {str(e)}")
            return False

    def generate_material_list(self) -> bool:
        """
        Generate a consolidated list of materials for ordering/inventory

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate project state
            if not self._validate_project_state():
                return False

            # Get zones data
            zones_data = self._get_zones_data()
            if not zones_data:
                self._show_warning("No Data", "Unable to retrieve zones data.")
                return False

            # Validate material list data
            validation = self.validator.validate_material_list_data(zones_data)
            if validation['errors']:
                self._show_validation_errors("Material List", validation['errors'])
                return False

            # Show warnings if any
            if validation['warnings']:
                self._show_validation_warnings("Material List", validation['warnings'])

            # Generate material list
            result = self.report_generator.generate_material_list(zones_data)

            if result.success:
                self._show_success("Material list generated successfully.", result.file_path)
                return True
            else:
                self._show_error(f"Failed to generate material list: {result.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"Error generating material list: {e}", exc_info=True)
            self._show_error(f"Failed to generate material list: {str(e)}")
            return False

    def generate_all_reports(self) -> bool:
        """
        Generate all available reports in sequence

        Returns:
            bool: True if all reports generated successfully
        """
        try:
            if not self._validate_project_state():
                return False

            if not self._handle_unsaved_changes():
                return False

            # Determine which reports can be generated
            project_data, zones_data = self._get_and_validate_basic_data()
            if not project_data or not zones_data:
                return False

            report_types = ["project"]

            # Add speaker report if speaker data exists
            speaker_layout = self._get_speaker_layout()
            if speaker_layout and any(speakers for speakers in speaker_layout.values()):
                report_types.append("speaker")

            # Add material list if materials exist
            material_validation = self.validator.validate_material_list_data(zones_data)
            if not material_validation['errors']:
                report_types.append("material")

            if len(report_types) == 1:
                self._show_warning("Limited Reports",
                                   "Only project report can be generated. Add speakers and materials for more reports.")

            # Generate batch reports
            result = self.report_generator.generate_batch_reports(
                report_types, project_data, zones_data, speaker_layout
            )

            # Show results
            self._show_batch_results(result)
            return result.is_complete_success

        except Exception as e:
            self.logger.error(f"Error generating all reports: {e}", exc_info=True)
            self._show_error(f"Failed to generate reports: {str(e)}")
            return False

    def generate_custom_report_package(self) -> bool:
        """
        Generate a custom selection of reports

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._validate_project_state():
                return False

            # Create selection dialog
            selected_reports = self._show_report_selection_dialog()
            if not selected_reports:
                return False

            if not self._handle_unsaved_changes():
                return False

            # Get data
            project_data, zones_data = self._get_and_validate_basic_data()
            if not project_data or not zones_data:
                return False

            speaker_layout = self._get_speaker_layout() if "speaker" in selected_reports else None

            # Generate batch reports
            result = self.report_generator.generate_batch_reports(
                selected_reports, project_data, zones_data, speaker_layout
            )

            # Show results
            self._show_batch_results(result)
            return result.is_complete_success

        except Exception as e:
            self.logger.error(f"Error generating custom report package: {e}", exc_info=True)
            self._show_error(f"Failed to generate custom report package: {str(e)}")
            return False

    def set_reports_directory_dialog(self):
        """Show dialog to set reports directory"""
        from PySide6.QtWidgets import QFileDialog

        current_dir = self.report_generator.get_reports_directory()

        directory = QFileDialog.getExistingDirectory(
            self.parent,
            "Select Reports Directory",
            current_dir or ""
        )

        if directory:
            self.report_generator.set_reports_directory(directory)
            self._show_success(f"Reports directory set to: {directory}")

    def show_current_settings(self):
        """Show current report generation settings"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox

        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Report Settings")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        # Current settings
        reports_dir = self.report_generator.get_reports_directory() or "Not set"
        available_formats = ", ".join(self.report_generator.get_available_formats())
        speaker_view_status = "Available" if self.speaker_view else "Not available"

        settings_text = f"""
Current Report Settings:

Reports Directory: {reports_dir}

Available Formats: {available_formats}

Visual Reports: {speaker_view_status}

Report Types:
• Project Report - Comprehensive project overview
• Speaker Report - Detailed speaker placement analysis  
• Material List - CSV list for ordering/inventory
• Batch Operations - Generate multiple reports at once
"""

        label = QLabel(settings_text)
        label.setWordWrap(True)
        layout.addWidget(label)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

    def _show_report_selection_dialog(self) -> List[str]:
        """
        Show dialog for selecting which reports to generate

        Returns:
            list: List of selected report types
        """
        try:
            from PySide6.QtWidgets import (QCheckBox, QDialog, QVBoxLayout,
                                         QDialogButtonBox, QLabel, QGroupBox)

            dialog = QDialog(self.parent)
            dialog.setWindowTitle("Select Reports to Generate")
            dialog.setModal(True)
            dialog.resize(450, 350)

            layout = QVBoxLayout(dialog)

            # Add description
            description = QLabel("Select which reports you would like to generate:")
            layout.addWidget(description)

            # Create group box for report options
            group_box = QGroupBox("Available Reports")
            group_layout = QVBoxLayout(group_box)

            # Get data to check availability
            zones_data = self._get_zones_data()
            speaker_layout = self._get_speaker_layout()

            # Project report checkbox
            self.project_cb = QCheckBox("Project Report - Comprehensive project overview")
            self.project_cb.setChecked(True)  # Default checked
            group_layout.addWidget(self.project_cb)

            # Speaker report checkbox
            self.speaker_cb = QCheckBox("Speaker Report - Detailed speaker placement analysis")
            speaker_available = bool(speaker_layout and any(speakers for speakers in speaker_layout.values()))
            self.speaker_cb.setEnabled(speaker_available)
            self.speaker_cb.setChecked(speaker_available)
            if not speaker_available:
                self.speaker_cb.setText(self.speaker_cb.text() + " (No speaker data)")
            group_layout.addWidget(self.speaker_cb)

            # Material list checkbox
            self.material_cb = QCheckBox("Material List - CSV list for ordering/inventory")
            material_validation = self.validator.validate_material_list_data(zones_data or {})
            material_available = not material_validation['errors']
            self.material_cb.setEnabled(material_available)
            self.material_cb.setChecked(material_available)
            if not material_available:
                self.material_cb.setText(self.material_cb.text() + " (No materials)")
            group_layout.addWidget(self.material_cb)

            layout.addWidget(group_box)

            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            # Show dialog and get result
            if dialog.exec() == QDialog.Accepted:
                selected = []
                if self.project_cb.isChecked():
                    selected.append("project")
                if self.speaker_cb.isChecked() and self.speaker_cb.isEnabled():
                    selected.append("speaker")
                if self.material_cb.isChecked() and self.material_cb.isEnabled():
                    selected.append("material")
                return selected

            return []

        except Exception as e:
            self.logger.error(f"Error showing report selection dialog: {e}", exc_info=True)
            return []

    def _show_batch_results(self, result: BatchReportResult):
        """Show results of batch report generation"""
        if result.is_complete_success:
            message = f"All {result.total_requested} reports generated successfully!"
            self._show_success(message)
        elif result.is_partial_success:
            message = f"Generated {result.successful} out of {result.total_requested} reports successfully."
            details = []
            for report_type, report_result in result.results.items():
                if report_result.success:
                    details.append(f"✓ {report_type.title()} report: {report_result.file_path}")
                else:
                    details.append(f"✗ {report_type.title()} report: {report_result.error_message}")

            full_message = message + "\n\nDetails:\n" + "\n".join(details)
            self._show_warning("Partial Success", full_message)
        else:
            message = f"Failed to generate any reports ({result.failed} failures)."
            details = []
            for report_type, report_result in result.results.items():
                details.append(f"✗ {report_type.title()} report: {report_result.error_message}")

            full_message = message + "\n\nErrors:\n" + "\n".join(details)
            self._show_error(full_message)

    def _validate_project_state(self) -> bool:
        """
        Validate that a project is loaded and ready for report generation

        Returns:
            bool: True if project state is valid
        """
        current_project_id = self.project_manager.get_current_project_id()
        if not current_project_id:
            self._show_warning("No Project", "Please open a project before generating reports.")
            return False
        return True

    def _handle_unsaved_changes(self) -> bool:
        """
        Handle unsaved changes before generating reports

        Returns:
            bool: True if changes were handled successfully, False if cancelled
        """
        if not self.project_manager.has_unsaved_changes():
            return True

        save_first = ConfirmDialog.ask(
            self.parent, "Unsaved Changes",
            "There are unsaved changes. Save before generating the report?",
            confirm_text="Save First", cancel_text="Generate Without Saving"
        )

        if save_first:
            success = self.project_manager.save_project()
            if not success:
                self._show_error("Failed to save project. Report may not include recent changes.")
                return False

        return True

    def _get_and_validate_basic_data(self) -> tuple:
        """
        Get and validate basic project and zones data

        Returns:
            tuple: (project_data, zones_data) or (None, None) if invalid
        """
        project_data = self._get_current_project_data()
        zones_data = self._get_zones_data()

        if not project_data:
            self._show_warning("No Project Data", "Unable to retrieve project data.")
            return None, None

        if not zones_data:
            self._show_warning("No Zones Data", "Unable to retrieve zones data.")
            return None, None

        return project_data, zones_data

    def _get_current_project_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current project data

        Returns:
            Optional[Dict]: Project data or None if not available
        """
        try:
            return self.project_manager.get_current_project_data()
        except Exception as e:
            self.logger.error(f"Error getting project data: {e}", exc_info=True)
            return None

    def _get_zones_data(self) -> Optional[Dict[str, Any]]:
        """
        Get live zones data, trying three sources in priority order:
          1. zones_view on the zones_tab (when helper is created from the zones tab)
          2. zones_view stored on project_manager (set by main window on startup)
          3. Saved zones_data embedded in the project file (last resort)
        """
        try:
            # 1. Direct zones_view on whatever tab was passed as zones_tab
            if hasattr(self.zones_tab, 'zones_view') and self.zones_tab.zones_view:
                return self.zones_tab.zones_view.to_json()

            # 2. zones_view stored on the project manager (wired up by main_window)
            if hasattr(self.project_manager, 'zones_view') and self.project_manager.zones_view:
                return self.project_manager.zones_view.to_json()

            # 3. Last resort: saved snapshot in the project file
            project_data = self._get_current_project_data()
            if project_data:
                return project_data.get('zones_data', {})
            return {}
        except Exception as e:
            self.logger.error(f"Error getting zones data: {e}", exc_info=True)
            return None

    def _get_speaker_layout(self) -> Optional[Dict[str, Any]]:
        """
        Get speaker layout data for all zones.

        Returns:
            Optional[Dict]: Speaker layout keyed by zone_id, or None if not available
        """
        try:
            # Prefer live data from the speaker view (all zones, not just the current one)
            if self.speaker_view and hasattr(self.speaker_view, 'layout_data'):
                layout = self.speaker_view.layout_data
                if layout:
                    return layout

            # Fall back to last-saved data in the project
            project_data = self._get_current_project_data()
            if project_data:
                return project_data.get('speaker_layout', {})

            return {}
        except Exception as e:
            self.logger.error(f"Error getting speaker layout: {e}", exc_info=True)
            return None

    def _show_validation_errors(self, report_type: str, errors: List[str]):
        """Show validation errors to user"""
        error_text = f"Cannot generate {report_type} due to the following errors:\n\n"
        error_text += "\n".join(f"• {error}" for error in errors)
        self._show_error(error_text)

    def _show_validation_warnings(self, report_type: str, warnings: List[str]):
        """Show validation warnings to user"""
        if not warnings:
            return

        warning_text = f"The following issues were found with {report_type} data:\n\n"
        warning_text += "\n".join(f"• {warning}" for warning in warnings)
        warning_text += "\n\nDo you want to continue generating the report?"

        return ConfirmDialog.ask(
            self.parent, "Data Warnings", warning_text,
            confirm_text="Continue", cancel_text="Cancel"
        )

    def _show_success(self, message: str, file_path: str = None):
        """Show success message to user"""
        if file_path:
            message += f"\n\nSaved to: {file_path}"
        AlertDialog.show_info(self.parent, "Success", message)

    def _show_warning(self, title: str, message: str):
        """Show warning message to user"""
        AlertDialog.show_warning(self.parent, title, message)

    def _show_error(self, message: str):
        """Show error message to user"""
        AlertDialog.show_error(self.parent, "Error", message)

    def get_available_formats(self) -> List[str]:
        """
        Get list of available report formats

        Returns:
            list: List of available formats
        """
        return self.report_generator.get_available_formats()

    def get_available_format_names(self) -> Dict[str, str]:
        """
        Get mapping of extensions to format names

        Returns:
            dict: Mapping of extensions to human-readable names
        """
        return self.report_generator.get_available_format_names()

    def set_speaker_view(self, speaker_view):
        """
        Set or update the speaker view for visual reports

        Args:
            speaker_view: Speaker view instance
        """
        self.speaker_view = speaker_view

        # Update the visual formatter
        if speaker_view:
            self.report_generator.add_visual_formatter(speaker_view)

    def generate_report_preview(self, report_type: str) -> Optional[str]:
        """
        Generate a preview of a report (returns HTML content as string)

        Args:
            report_type: Type of report ('project', 'speaker', 'material')

        Returns:
            Optional[str]: HTML content for preview or None if failed
        """
        try:
            if not self._validate_project_state():
                return None

            # Get data based on report type
            project_data, zones_data = self._get_and_validate_basic_data()
            if not project_data or not zones_data:
                return None

            # Create temporary HTML formatter for preview
            from utils.formatters.html_formatter import HTMLReportFormatter
            from utils.report_data_models import ReportData, ReportConfig

            formatter = HTMLReportFormatter(self.logger)

            if report_type == "speaker":
                speaker_layout = self._get_speaker_layout()
                if not speaker_layout:
                    return None

                report_data = ReportData(
                    project_data=project_data,
                    zones_data=zones_data,
                    speaker_layout=speaker_layout
                )
            else:
                report_data = ReportData(
                    project_data=project_data,
                    zones_data=zones_data
                )

            # Generate HTML content to string
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                result = formatter.generate(report_data, temp_path, ReportConfig())
                if result.success:
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        return f.read()
                return None
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            self.logger.error(f"Error generating report preview: {e}", exc_info=True)
            return None