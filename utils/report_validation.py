"""
Report data validation utilities - Fixed to remove room assignment references
"""

import logging
from typing import Dict, List, Any, Optional
from utils.report_data_models import ReportData


class ReportValidator:
    """Validates report data and provides detailed feedback"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def validate_project_report_data(self, project_data: Dict[str, Any],
                                   zones_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data for project report generation

        Returns:
            Dict with 'errors' and 'warnings' keys containing lists of messages
        """
        errors = []
        warnings = []

        # Project data validation
        if not project_data:
            errors.append("Project data is missing")
        else:
            if not project_data.get('name'):
                warnings.append("Project name is not set")
            if not project_data.get('description'):
                warnings.append("Project description is not set")

        # Zones data validation
        zones_validation = self._validate_zones_data(zones_data)
        errors.extend(zones_validation['errors'])
        warnings.extend(zones_validation['warnings'])

        return {'errors': errors, 'warnings': warnings}

    def validate_speaker_report_data(self, project_data: Dict[str, Any],
                                   zones_data: Dict[str, Any],
                                   speaker_layout: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data for speaker report generation

        Returns:
            Dict with 'errors' and 'warnings' keys containing lists of messages
        """
        errors = []
        warnings = []

        # Basic project validation
        project_validation = self.validate_project_report_data(project_data, zones_data)
        errors.extend(project_validation['errors'])
        warnings.extend(project_validation['warnings'])

        # Speaker layout validation
        if not speaker_layout:
            errors.append("Speaker layout data is missing")
        else:
            speaker_validation = self._validate_speaker_layout(speaker_layout, zones_data)
            errors.extend(speaker_validation['errors'])
            warnings.extend(speaker_validation['warnings'])

        return {'errors': errors, 'warnings': warnings}

    def validate_material_list_data(self, zones_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data for material list generation

        Returns:
            Dict with 'errors' and 'warnings' keys containing lists of messages
        """
        errors = []
        warnings = []

        # Zones data validation
        zones_validation = self._validate_zones_data(zones_data)
        errors.extend(zones_validation['errors'])
        warnings.extend(zones_validation['warnings'])

        # Material-specific validation
        zones = zones_data.get('zones', [])
        has_materials = False
        has_controllers = False

        for zone in zones:
            materials = zone.get('materials', [])
            controllers = zone.get('controllers', [])

            if materials:
                has_materials = True
                # Validate material data
                for material in materials:
                    if not material.get('type'):
                        warnings.append(f"Material in zone '{zone.get('name', 'Unknown')}' has no type specified")
                    if not material.get('quantity'):
                        warnings.append(f"Material '{material.get('type', 'Unknown')}' has no quantity specified")

            if controllers:
                has_controllers = True
                # Validate controller data
                for controller in controllers:
                    if not controller.get('type'):
                        warnings.append(f"Controller in zone '{zone.get('name', 'Unknown')}' has no type specified")
                    if not controller.get('quantity'):
                        warnings.append(f"Controller '{controller.get('type', 'Unknown')}' has no quantity specified")

        if not has_materials and not has_controllers:
            errors.append("No materials or controllers found in any zones")
        elif not has_materials:
            warnings.append("No materials found - only controllers will be listed")
        elif not has_controllers:
            warnings.append("No controllers found - only materials will be listed")

        return {'errors': errors, 'warnings': warnings}

    def _validate_zones_data(self, zones_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate zones data structure"""
        errors = []
        warnings = []

        if not zones_data:
            errors.append("Zones data is missing")
            return {'errors': errors, 'warnings': warnings}

        zones = zones_data.get('zones', [])
        if not zones:
            errors.append("No zones found in project")
            return {'errors': errors, 'warnings': warnings}

        # Validate individual zones
        for i, zone in enumerate(zones):
            zone_name = zone.get('name', f'Zone {i+1}')

            if not zone.get('name'):
                warnings.append(f"Zone {i+1} has no name set")

            # Removed room_name validation since we got rid of zone to room assignment

            if not zone.get('target_spl'):
                warnings.append(f"Zone '{zone_name}' has no target SPL set")

            if zone.get('environment_type') == 'enclosed' and not zone.get('ceiling_height'):
                warnings.append(f"Enclosed zone '{zone_name}' has no ceiling height set")

            if not zone.get('area'):
                warnings.append(f"Zone '{zone_name}' has no area calculated")

        return {'errors': errors, 'warnings': warnings}

    def _validate_speaker_layout(self, speaker_layout: Dict[str, Any],
                                zones_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate speaker layout data"""
        errors = []
        warnings = []

        if not any(speakers for speakers in speaker_layout.values()):
            errors.append("No speakers found in speaker layout")
            return {'errors': errors, 'warnings': warnings}

        zones = zones_data.get('zones', [])
        zone_ids = {str(zone.get('id', i)) for i, zone in enumerate(zones)}

        total_speakers = 0

        for zone_id, zone_speakers in speaker_layout.items():
            if zone_id not in zone_ids:
                warnings.append(f"Speaker layout contains zone '{zone_id}' that doesn't exist in zones data")
                continue

            if not zone_speakers:
                continue

            zone_name = next((z.get('name', f'Zone {zone_id}') for z in zones
                            if str(z.get('id', '')) == zone_id), f'Zone {zone_id}')

            for speaker_id, speaker in zone_speakers.items():
                total_speakers += 1

                # Only warn if a type field is outright missing (position/type are required)
                if not speaker.get('type'):
                    warnings.append(f"Speaker {speaker_id[-8:]} in zone '{zone_name}' has no type specified")

        if total_speakers == 0:
            errors.append("No valid speakers found in layout")

        return {'errors': errors, 'warnings': warnings}

    def validate_report_data(self, data: ReportData, report_type: str = "general") -> Dict[str, List[str]]:
        """
        Validate ReportData object for specified report type

        Args:
            data: ReportData object to validate
            report_type: Type of report ('project', 'speaker', 'material', 'general')

        Returns:
            Dict with 'errors' and 'warnings' keys
        """
        if report_type == "project":
            return self.validate_project_report_data(data.project_data, data.zones_data)
        elif report_type == "speaker":
            return self.validate_speaker_report_data(
                data.project_data, data.zones_data, data.speaker_layout or {}
            )
        elif report_type == "material":
            return self.validate_material_list_data(data.zones_data)
        else:
            # General validation
            return self.validate_project_report_data(data.project_data, data.zones_data)


def validate_file_path(file_path: str) -> List[str]:
    """
    Validate file path for report generation

    Args:
        file_path: Path to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not file_path:
        errors.append("File path is empty")
        return errors

    import os

    # Check if directory exists or can be created
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except (OSError, PermissionError) as e:
            errors.append(f"Cannot create directory '{directory}': {e}")

    # Check if file can be written
    try:
        # Try to create/write to the file
        with open(file_path, 'w') as f:
            pass
        # Clean up test file
        if os.path.exists(file_path):
            os.remove(file_path)
    except (OSError, PermissionError) as e:
        errors.append(f"Cannot write to file '{file_path}': {e}")

    return errors