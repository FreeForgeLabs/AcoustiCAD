"""
Abstract base class for report formatters
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from utils.report_data_models import ReportData, ReportConfig, ReportGenerationResult


class BaseReportFormatter(ABC):
    """Abstract base class for report formatters"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def generate(self, data: ReportData, file_path: str, config: ReportConfig = None) -> ReportGenerationResult:
        """
        Generate report in specific format

        Args:
            data: Report data container
            file_path: Output file path
            config: Report configuration

        Returns:
            ReportGenerationResult: Result of the generation operation
        """
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format"""
        pass

    @property
    @abstractmethod
    def file_filter(self) -> str:
        """Return the file filter for file dialogs"""
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return human-readable format name"""
        pass

    def validate_data(self, data: ReportData) -> List[str]:
        """
        Validate report data and return any warnings

        Args:
            data: Report data to validate

        Returns:
            List[str]: List of validation warnings
        """
        warnings = []

        if not data.project_data:
            warnings.append("Project data is empty")

        if not data.zones_data:
            warnings.append("Zones data is empty")

        zones = data.zones_data.get('zones', [])
        if not zones:
            warnings.append("No zones found in project")

        return warnings

    def _create_success_result(self, file_path: str, warnings: List[str] = None) -> ReportGenerationResult:
        """Create a successful result"""
        return ReportGenerationResult(
            success=True,
            file_path=file_path,
            warnings=warnings or []
        )

    def _create_error_result(self, error_message: str, warnings: List[str] = None) -> ReportGenerationResult:
        """Create a failed result"""
        return ReportGenerationResult(
            success=False,
            error_message=error_message,
            warnings=warnings or []
        )

    def _ensure_config(self, config: ReportConfig = None) -> ReportConfig:
        """Ensure we have a valid config object"""
        return config or ReportConfig()

    def _count_speaker_types(self, speakers: Dict) -> Dict[str, int]:
        """Count speakers by type"""
        counts = {"In-Ceiling": 0, "Pendant": 0}
        for speaker in speakers.values():
            speaker_type = speaker.get('type', 'Unknown')
            if speaker_type in counts:
                counts[speaker_type] += 1
        return counts

    def _calculate_total_power(self, speaker_layout: Dict[str, Any]) -> int:
        """Calculate total power consumption across all speakers"""
        total_power = 0
        for zone_speakers in speaker_layout.values():
            for speaker in zone_speakers.values():
                total_power += speaker.get('power', 0)
        return total_power

    def _get_material_summary(self, zones_data: Dict[str, Any]) -> Dict[str, int]:
        """Get consolidated material counts"""
        materials_dict = {}
        controllers_dict = {}

        zones = zones_data.get('zones', [])

        for zone in zones:
            # Process controllers
            for controller in zone.get('controllers', []):
                controller_type = controller.get('type', 'Unknown')
                qty = controller.get('quantity', 1)
                controllers_dict[controller_type] = controllers_dict.get(controller_type, 0) + qty

            # Process materials
            for material in zone.get('materials', []):
                material_type = material.get('type', 'Unknown')
                details = material.get('details', '')
                key = f"{material_type} ({details})" if details else material_type
                qty = material.get('quantity', 1)
                materials_dict[key] = materials_dict.get(key, 0) + qty

        return {'materials': materials_dict, 'controllers': controllers_dict}