"""
Main report generator class - Updated with default directory and enhanced project details
"""

import os
import logging
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import QFileDialog
from ui.dialogs.alert_dialog import AlertDialog

# Import data models
from utils.report_data_models import ReportData, ReportConfig, ReportGenerationResult, BatchReportResult

# Import formatters
from utils.formatters.html_formatter import HTMLReportFormatter
from utils.formatters.text_formatter import TextReportFormatter
from utils.formatters.csv_formatter import CSVReportFormatter
from utils.formatters.pdf_formatter import PDFReportFormatter
from utils.formatters.visual_formatter import VisualReportFormatter


class ReportGenerator:
    """
    Main report generator class - refactored for better maintainability
    """

    def __init__(self, parent=None, storage=None):
        self.parent = parent
        self.storage = storage
        self.logger = logging.getLogger(__name__)

        # Initialize formatters
        self.html_formatter = HTMLReportFormatter(self.logger)
        self.text_formatter = TextReportFormatter(self.logger)
        self.csv_formatter = CSVReportFormatter(self.logger)
        self.pdf_formatter = PDFReportFormatter(self.logger, self.html_formatter)

        self.formatters = {
            '.html': self.html_formatter,
            '.txt': self.text_formatter,
            '.pdf': self.pdf_formatter,
            '.csv': self.csv_formatter
        }

        # Set default reports directory
        self.reports_dir = self._get_default_reports_directory()

        # Try to get reports directory from storage if available
        if storage and hasattr(storage, 'get_reports_dir'):
            try:
                storage_dir = storage.get_reports_dir()
                if storage_dir and os.path.exists(storage_dir):
                    self.reports_dir = storage_dir
                    self.logger.debug(f"Using reports directory from storage: {self.reports_dir}")
                else:
                    self.logger.debug(f"Using default reports directory: {self.reports_dir}")
            except Exception as e:
                self.logger.warning(f"Could not get reports directory from storage: {e}")
                self.logger.debug(f"Using default reports directory: {self.reports_dir}")

    def _get_default_reports_directory(self) -> str:
        """Get the default reports directory in user's Documents folder"""
        try:
            # Get user's Documents directory
            documents_dir = os.path.join(os.path.expanduser("~"), "Documents")

            # Create AcoustiCAD Reports subdirectory.
            # Note: the canonical migration lives in utils/storage.py — Storage is the
            # primary path. This fallback only fires if Storage isn't available.
            reports_dir = os.path.join(documents_dir, "AcoustiCAD Reports")

            # Create the directory if it doesn't exist
            os.makedirs(reports_dir, exist_ok=True)

            return reports_dir
        except Exception as e:
            self.logger.error(f"Could not create default reports directory: {e}")
            # Fallback to user's home directory
            return os.path.expanduser("~")

    def generate_project_report(self, project_data: Dict[str, Any], zones_data: Dict[str, Any],
                              file_path: str = None) -> ReportGenerationResult:
        """
        Generate a comprehensive project report with full client and project details

        Args:
            project_data: The project data including client info, system requirements, etc.
            zones_data: The zones data
            file_path: Path to save the report. If None, will prompt user.

        Returns:
            ReportGenerationResult: Result of the operation
        """
        try:
            if not file_path:
                file_path = self._get_save_file_path(project_data, "Project_Report")
                if not file_path:
                    return ReportGenerationResult(success=False, error_message="No file path selected")

            # Prepare report data with enhanced project information
            report_data = ReportData(
                project_data=project_data,
                zones_data=zones_data
            )

            return self._generate_report(report_data, file_path)

        except Exception as e:
            error_msg = f"Error generating project report: {e}"
            self.logger.error(error_msg, exc_info=True)
            self._show_error(f"Failed to generate project report: {str(e)}")
            return ReportGenerationResult(success=False, error_message=error_msg)

    def generate_speaker_report(self, project_data: Dict[str, Any], speaker_layout: Dict[str, Any],
                                zones_data: Dict[str, Any] = None,
                                file_path: str = None) -> ReportGenerationResult:
        """
        Generate a comprehensive speaker placement report

        Args:
            project_data: The project data
            speaker_layout: The speaker layout data (all zones)
            zones_data: Live zones data from the zones tab. If None, falls back to
                        project_data['zones_data'] for backwards compatibility.
            file_path: Path to save the report. If None, will prompt user.

        Returns:
            ReportGenerationResult: Result of the operation
        """
        try:
            if not file_path:
                file_path = self._get_save_file_path(project_data, "Speaker_Report")
                if not file_path:
                    return ReportGenerationResult(success=False, error_message="No file path selected")

            # Use live zones_data if provided, otherwise fall back to what's embedded in project_data
            if zones_data is None:
                zones_data = project_data.get('zones_data', {})
            obstruction_layout = project_data.get('obstruction_layout', {})

            # Prepare report data
            report_data = ReportData(
                project_data=project_data,
                zones_data=zones_data,
                speaker_layout=speaker_layout,
                obstruction_layout=obstruction_layout
            )

            # Use enhanced config for speaker reports
            config = ReportConfig(
                include_thumbnails=True,
                include_snapshots=True,
                high_resolution=True
            )
            self.logger.info(
                f"Created config: snapshots={config.include_snapshots}, thumbnails={config.include_thumbnails}")

            return self._generate_report(report_data, file_path, config)

        except Exception as e:
            error_msg = f"Error generating speaker report: {e}"
            self.logger.error(error_msg, exc_info=True)
            self._show_error(f"Failed to generate speaker report: {str(e)}")
            return ReportGenerationResult(success=False, error_message=error_msg)

    def generate_material_list(self, zones_data: Dict[str, Any], file_path: str = None) -> ReportGenerationResult:
        """
        Generate a material list for ordering/inventory

        Args:
            zones_data: The zones data
            file_path: Path to save the report. If None, will prompt user.

        Returns:
            ReportGenerationResult: Result of the operation
        """
        try:
            if not file_path:
                file_path = self._get_save_file_path({}, "Material_List", default_ext='.csv')
                if not file_path:
                    return ReportGenerationResult(success=False, error_message="No file path selected")

            # Prepare report data
            report_data = ReportData(
                project_data={},
                zones_data=zones_data
            )

            return self._generate_report(report_data, file_path)

        except Exception as e:
            error_msg = f"Error generating material list: {e}"
            self.logger.error(error_msg, exc_info=True)
            self._show_error(f"Failed to generate material list: {str(e)}")
            return ReportGenerationResult(success=False, error_message=error_msg)

    def generate_batch_reports(self, report_types: List[str], project_data: Dict[str, Any],
                             zones_data: Dict[str, Any], speaker_layout: Dict[str, Any] = None) -> BatchReportResult:
        """
        Generate multiple reports in batch

        Args:
            report_types: List of report types to generate ('project', 'speaker', 'material')
            project_data: The project data
            zones_data: The zones data
            speaker_layout: Optional speaker layout data

        Returns:
            BatchReportResult: Results of all generation operations
        """
        results = {}
        successful = 0
        failed = 0

        for report_type in report_types:
            try:
                if report_type == "project":
                    result = self.generate_project_report(project_data, zones_data)
                elif report_type == "speaker" and speaker_layout:
                    result = self.generate_speaker_report(project_data, speaker_layout, zones_data)
                elif report_type == "material":
                    result = self.generate_material_list(zones_data)
                else:
                    result = ReportGenerationResult(
                        success=False,
                        error_message=f"Unknown report type or missing data: {report_type}"
                    )

                results[report_type] = result
                if result.success:
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                error_msg = f"Error generating {report_type} report: {e}"
                self.logger.error(error_msg, exc_info=True)
                results[report_type] = ReportGenerationResult(success=False, error_message=error_msg)
                failed += 1

        return BatchReportResult(
            total_requested=len(report_types),
            successful=successful,
            failed=failed,
            results=results
        )

    def _generate_report(self, data: ReportData, file_path: str, config: ReportConfig = None) -> ReportGenerationResult:
        """
        Generate report using appropriate formatter

        Args:
            data: Report data container
            file_path: Output file path
            config: Report configuration

        Returns:
            ReportGenerationResult: Result of the operation
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Determine format from extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            # Get appropriate formatter
            formatter = self.formatters.get(ext)
            if not formatter:
                # Default to text format
                formatter = self.text_formatter
                file_path = os.path.splitext(file_path)[0] + '.txt'

            # Generate report
            result = formatter.generate(data, file_path, config)

            if result.success:
                self.logger.info(f"Report generated successfully: {file_path}")

            return result

        except Exception as e:
            error_msg = f"Error in _generate_report: {e}"
            self.logger.error(error_msg, exc_info=True)
            return ReportGenerationResult(success=False, error_message=error_msg)

    def _get_save_file_path(self, project_data: Dict[str, Any], report_type: str,
                          default_ext: str = '.html') -> str:
        """
        Get file path for saving report through dialog

        Args:
            project_data: Project data for generating default filename
            report_type: Type of report for filename
            default_ext: Default file extension

        Returns:
            str: Selected file path or empty string if cancelled
        """
        try:
            # Set initial directory to reports directory
            initial_dir = self.reports_dir

            # Generate default filename
            default_name = self._generate_default_filename(project_data, report_type) + default_ext
            default_path = os.path.join(initial_dir, default_name)

            # Create file filter based on available formatters.
            # Put the formatter matching default_ext first so macOS selects
            # that filter by default — preventing a double-extension like .csv.html.
            matching_filter = None
            other_filters = []
            for formatter in self.formatters.values():
                if formatter.file_extension == default_ext:
                    matching_filter = formatter.file_filter
                else:
                    other_filters.append(formatter.file_filter)
            filters = ([matching_filter] if matching_filter else []) + other_filters + ["All Files (*)"]
            filter_string = ";;".join(filters)

            # Show save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent,
                f"Save {report_type.replace('_', ' ')}",
                default_path,
                filter_string
            )

            return file_path

        except Exception as e:
            self.logger.error(f"Error getting save file path: {e}", exc_info=True)
            return ""

    def _generate_default_filename(self, project_data: Dict[str, Any], report_type: str) -> str:
        """
        Generate default filename for report

        Args:
            project_data: Project data
            report_type: Type of report

        Returns:
            str: Default filename without extension
        """
        try:
            # Start with report type
            default_name = report_type

            # Add project info if available
            if 'name' in project_data and project_data['name']:
                # Clean project name for filename
                clean_name = "".join(
                    c if c.isalnum() or c in " _-" else "_"
                    for c in project_data['name']
                )
                # Limit length to avoid filesystem issues
                clean_name = clean_name[:50]
                default_name = f"{clean_name}_{report_type}"
            elif 'id' in project_data:
                default_name = f"{report_type}_{project_data['id']}"

            return default_name

        except Exception as e:
            self.logger.error(f"Error generating default filename: {e}", exc_info=True)
            return report_type

    def _show_error(self, message: str):
        """Show error message to user"""
        if self.parent:
            AlertDialog.show_error(self.parent, "Error", message)

    def add_visual_formatter(self, speaker_view):
        """
        Add visual formatter with speaker view integration

        Args:
            speaker_view: Speaker view instance for visual report generation
        """
        from utils.formatters.visual_formatter import VisualReportFormatter
        visual_formatter = VisualReportFormatter(self.logger, speaker_view)
        self.formatters['.html'] = visual_formatter  # Replace the HTML formatter
        self.logger.info(f"Visual formatter registered, speaker_view available: {speaker_view is not None}")

    def get_available_formats(self) -> List[str]:
        """Get list of available report formats"""
        return list(self.formatters.keys())

    def get_available_format_names(self) -> Dict[str, str]:
        """Get mapping of extensions to human-readable format names"""
        return {ext: formatter.format_name for ext, formatter in self.formatters.items()}

    def get_reports_directory(self) -> str:
        """Get the reports directory path"""
        return self.reports_dir or ""

    def set_reports_directory(self, path: str):
        """Set the reports directory path"""
        self.reports_dir = path
        # Only try to set in storage if it has the method
        if self.storage and hasattr(self.storage, 'set_reports_dir'):
            try:
                self.storage.set_reports_dir(path)
            except Exception as e:
                self.logger.warning(f"Could not save reports directory to storage: {e}")

    def validate_report_data(self, report_type: str, project_data: Dict[str, Any],
                           zones_data: Dict[str, Any], speaker_layout: Dict[str, Any] = None) -> List[str]:
        """
        Validate data for report generation

        Args:
            report_type: Type of report to validate for
            project_data: Project data
            zones_data: Zones data
            speaker_layout: Optional speaker layout data

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        if not project_data and report_type != "material":
            errors.append("Project data is required")

        if not zones_data:
            errors.append("Zones data is required")

        zones = zones_data.get('zones', [])
        if not zones:
            errors.append("No zones found in project")

        if report_type == "speaker":
            if not speaker_layout:
                errors.append("Speaker layout data is required for speaker reports")
            elif not any(speakers for speakers in speaker_layout.values()):
                errors.append("No speakers found in speaker layout")

        if report_type == "material":
            # Check if any zones have materials or controllers
            has_materials = False
            for zone in zones:
                if zone.get('materials') or zone.get('controllers'):
                    has_materials = True
                    break
            if not has_materials:
                errors.append("No materials or controllers found in any zones")

        return errors

    def get_formatter_by_extension(self, extension: str):
        """Get formatter by file extension"""
        return self.formatters.get(extension.lower())

    def register_custom_formatter(self, extension: str, formatter):
        """Register a custom formatter for a file extension"""
        self.formatters[extension.lower()] = formatter

    def get_report_statistics(self, report_data: ReportData) -> Dict[str, Any]:
        """
        Get statistical information about the report data

        Args:
            report_data: Report data to analyze

        Returns:
            Dict with statistical information
        """
        stats = {
            'zones_count': 0,
            'total_speakers': 0,
            'total_power': 0,
            'speaker_types': {},
            'materials_count': 0,
            'controllers_count': 0
        }

        try:
            # Zone statistics
            zones = report_data.zones_data.get('zones', [])
            stats['zones_count'] = len(zones)

            # Speaker statistics
            if report_data.speaker_layout:
                for zone_speakers in report_data.speaker_layout.values():
                    stats['total_speakers'] += len(zone_speakers)
                    for speaker in zone_speakers.values():
                        stats['total_power'] += speaker.get('power', 0)
                        speaker_type = speaker.get('type', 'Unknown')
                        stats['speaker_types'][speaker_type] = stats['speaker_types'].get(speaker_type, 0) + 1

            # Material statistics
            for zone in zones:
                stats['materials_count'] += len(zone.get('materials', []))
                stats['controllers_count'] += len(zone.get('controllers', []))

        except Exception as e:
            self.logger.error(f"Error calculating report statistics: {e}", exc_info=True)

        return stats

    def export_configuration(self) -> Dict[str, Any]:
        """
        Export current generator configuration

        Returns:
            Dict with configuration data
        """
        return {
            'reports_directory': self.reports_dir,
            'available_formats': self.get_available_formats(),
            'format_names': self.get_available_format_names(),
            'has_visual_formatter': '.html' in self.formatters and isinstance(self.formatters['.html'], VisualReportFormatter)
        }

    def import_configuration(self, config: Dict[str, Any]):
        """
        Import generator configuration

        Args:
            config: Configuration data to import
        """
        try:
            if 'reports_directory' in config:
                self.set_reports_directory(config['reports_directory'])
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}", exc_info=True)

    def clear_cache(self):
        """Clear any cached data or temporary files"""
        try:
            # Clear any formatter-specific caches
            for formatter in self.formatters.values():
                if hasattr(formatter, 'clear_cache'):
                    formatter.clear_cache()
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}", exc_info=True)

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.formatters.keys())

    def is_format_supported(self, file_path: str) -> bool:
        """
        Check if a file format is supported

        Args:
            file_path: File path to check

        Returns:
            bool: True if format is supported
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.formatters

    def get_format_description(self, extension: str) -> str:
        """
        Get description of a format

        Args:
            extension: File extension

        Returns:
            str: Format description
        """
        formatter = self.formatters.get(extension.lower())
        if formatter:
            return formatter.format_name
        return "Unknown format"

    def estimate_generation_time(self, report_data: ReportData, format_ext: str) -> float:
        """
        Estimate report generation time in seconds

        Args:
            report_data: Report data to analyze
            format_ext: Target format extension

        Returns:
            float: Estimated time in seconds
        """
        try:
            # Base time estimates (in seconds)
            base_times = {
                '.txt': 0.1,
                '.csv': 0.1,
                '.html': 0.5,
                '.pdf': 2.0
            }

            base_time = base_times.get(format_ext.lower(), 1.0)

            # Adjust based on data complexity
            zones_count = len(report_data.zones_data.get('zones', []))
            complexity_factor = 1 + (zones_count * 0.1)

            # Visual reports take longer
            if (format_ext == '.html' and
                isinstance(self.formatters.get('.html'), VisualReportFormatter) and
                report_data.speaker_layout):
                complexity_factor *= 3

            return base_time * complexity_factor

        except Exception as e:
            self.logger.error(f"Error estimating generation time: {e}", exc_info=True)
            return 1.0  # Default estimate

    def get_memory_usage_estimate(self, report_data: ReportData) -> int:
        """
        Estimate memory usage in MB

        Args:
            report_data: Report data to analyze

        Returns:
            int: Estimated memory usage in MB
        """
        try:
            # Base memory usage
            base_mb = 5

            # Add for zones
            zones_count = len(report_data.zones_data.get('zones', []))
            base_mb += zones_count * 0.1

            # Add for speakers
            if report_data.speaker_layout:
                speaker_count = sum(len(speakers) for speakers in report_data.speaker_layout.values())
                base_mb += speaker_count * 0.05

            # Visual reports use more memory
            if isinstance(self.formatters.get('.html'), VisualReportFormatter):
                base_mb *= 2

            return max(1, int(base_mb))

        except Exception as e:
            self.logger.error(f"Error estimating memory usage: {e}", exc_info=True)
            return 10  # Default estimate