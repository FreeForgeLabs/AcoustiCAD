"""
Text report formatter - Enhanced with full project details
"""

import os
from typing import Dict, Any, List
from PySide6.QtCore import QDateTime
from utils.formatters.base_formatter import BaseReportFormatter
from utils.report_data_models import ReportData, ReportConfig, ReportGenerationResult


class TextReportFormatter(BaseReportFormatter):
    """Text report formatter with comprehensive project details"""

    @property
    def file_extension(self) -> str:
        return '.txt'

    @property
    def file_filter(self) -> str:
        return "Text Files (*.txt)"

    @property
    def format_name(self) -> str:
        return "Text Report"

    def generate(self, data: ReportData, file_path: str, config: ReportConfig = None) -> ReportGenerationResult:
        config = self._ensure_config(config)
        warnings = self.validate_data(data)

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w') as f:
                self._write_text_content(f, data)

            self.logger.info(f"Text report generated: {file_path}")
            return self._create_success_result(file_path, warnings)

        except Exception as e:
            error_msg = f"Error generating text report: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_result(error_msg, warnings)

    def _write_text_content(self, f, data: ReportData):
        """Write complete text content with full project details"""
        project_name = data.project_data.get('name', 'Unnamed Project')
        report_type = "Speaker Placement Report" if data.speaker_layout else "Audio System Design Report"

        # Header
        f.write("=" * 80 + "\n")
        f.write(f"{report_type.upper()}\n")
        f.write(f"{project_name.upper()}\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {QDateTime.currentDateTime().toString()}\n")
        f.write("=" * 80 + "\n\n")

        # Project Overview
        self._write_project_overview(f, data.project_data)

        # Client Information
        self._write_client_information(f, data.project_data)

        # System Requirements
        self._write_system_requirements(f, data.project_data)

        # Content sections
        if data.speaker_layout:
            self._write_speaker_content(f, data)
        else:
            self._write_zone_content(f, data)

        # Summary
        self._write_text_summary(f, data)

        # Recommendations
        self._write_recommendations(f, data)

    def _write_project_overview(self, f, project_data: Dict[str, Any]):
        """Write comprehensive project overview section"""
        f.write("PROJECT OVERVIEW\n")
        f.write("-" * 80 + "\n")
        f.write(f"Project Name: {project_data.get('name', 'Unnamed Project')}\n")
        f.write(f"Project Status: {project_data.get('project_status', 'Planning')}\n")
        f.write(f"Project Type: {project_data.get('project_type', 'Background Music')}\n")
        f.write(f"Facility Type: {project_data.get('facility_type', 'Not specified')}\n")
        f.write(f"Budget Range: {project_data.get('budget_range', 'Not specified')}\n")
        f.write(f"Installation Type: {project_data.get('installation_type', 'Not specified')}\n")

        # Dates
        completion_date = self._format_date(project_data.get('target_completion_date', ''))
        created_date = self._format_date(project_data.get('created_at', ''))
        modified_date = self._format_date(project_data.get('last_modified', ''))

        f.write(f"Target Completion: {completion_date}\n")
        f.write(f"Created: {created_date}\n")
        f.write(f"Last Modified: {modified_date}\n\n")

        # Description
        f.write("Project Description:\n")
        description = project_data.get('description', 'No description provided')
        f.write(self._wrap_text(description, indent="  "))
        f.write("\n\n")

    def _write_client_information(self, f, project_data: Dict[str, Any]):
        """Write client information section"""
        f.write("CLIENT INFORMATION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Client Name: {project_data.get('client_name', 'Not specified')}\n")
        f.write(f"Project Contact: {project_data.get('project_contact', 'Not specified')}\n")
        f.write(f"Contact Phone: {project_data.get('contact_phone', 'Not specified')}\n")
        f.write(f"Project Location: {project_data.get('project_location', 'Not specified')}\n\n")

    def _write_system_requirements(self, f, project_data: Dict[str, Any]):
        """Write system requirements section"""
        f.write("SYSTEM REQUIREMENTS\n")
        f.write("-" * 80 + "\n")

        # Audio sources
        audio_sources = project_data.get('primary_audio_sources', [])
        f.write("Audio Sources:\n")
        if audio_sources:
            for source in audio_sources:
                f.write(f"  • {source}\n")
        else:
            f.write("  • None specified\n")
        f.write("\n")

        # Control methods
        control_methods = project_data.get('control_system_type', [])
        f.write("Control Methods:\n")
        if control_methods:
            for method in control_methods:
                f.write(f"  • {method}\n")
        else:
            f.write("  • None specified\n")
        f.write("\n")

        # Network infrastructure
        f.write(f"Network Infrastructure: {project_data.get('network_infrastructure', 'Not specified')}\n\n")

        # Environmental factors
        environmental_factors = project_data.get('environmental_factors', [])
        f.write("Environmental Considerations:\n")
        if environmental_factors:
            for factor in environmental_factors:
                f.write(f"  • {factor}\n")
        else:
            f.write("  • None specified\n")
        f.write("\n")

        # Power requirements
        f.write("Power Requirements:\n")
        power_reqs = self._format_power_requirements_text(project_data)
        for req in power_reqs:
            f.write(f"  • {req}\n")
        f.write("\n")

        # Project notes
        notes = project_data.get('project_notes', '')
        if notes:
            f.write("Project Notes:\n")
            f.write(self._wrap_text(notes, indent="  "))
            f.write("\n\n")

    def _format_power_requirements_text(self, project_data: Dict[str, Any]) -> List[str]:
        """Format power requirements as list of strings"""
        requirements = ["120V AC Standard"]

        if project_data.get('ups_required', False):
            requirements.append("UPS/Battery Backup Required")
        if project_data.get('voltage_240_available', False):
            requirements.append("240V Available")
        if project_data.get('power_conditioning_needed', False):
            requirements.append("Power Conditioning Required")
        if project_data.get('dedicated_circuit_required', False):
            requirements.append("Dedicated Circuit Required")

        return requirements

    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        if not date_str:
            return "Not specified"

        try:
            if 'T' in date_str:
                date_str = date_str.split('T')[0]

            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str

    def _wrap_text(self, text: str, width: int = 76, indent: str = "") -> str:
        """Wrap text to specified width with optional indentation"""
        if not text:
            return indent + "None\n"

        import textwrap
        wrapper = textwrap.TextWrapper(
            width=width,
            initial_indent=indent,
            subsequent_indent=indent,
            break_long_words=False,
            break_on_hyphens=False
        )
        return wrapper.fill(text) + "\n"

    def _write_speaker_content(self, f, data: ReportData):
        """Write speaker-specific content"""
        zones = data.zones_data.get('zones', [])

        f.write("SPEAKER CONFIGURATION\n")
        f.write("-" * 80 + "\n\n")

        for zone in zones:
            zone_id = str(zone.get('id', ''))
            zone_speakers = data.speaker_layout.get(zone_id, {})
            if not zone_speakers:
                continue

            zone_name = zone.get('name', f'Zone {zone_id}')
            f.write(f"ZONE: {zone_name}\n")
            f.write("=" * 60 + "\n")

            # Zone properties
            f.write(f"Ceiling Height: {zone.get('ceiling_height', 'N/A')} ft\n")
            f.write(f"Target SPL: {zone.get('target_spl', 'N/A')} dB\n")
            f.write(f"Area: {zone.get('area', 'N/A')} ft²\n")
            f.write(f"Environment: {zone.get('environment_type', 'Enclosed')}\n\n")

            # Speaker details
            f.write(f"Speakers ({len(zone_speakers)}):\n")
            f.write("-" * 40 + "\n")

            total_zone_power = 0
            speaker_types = {}

            for speaker_id, speaker in zone_speakers.items():
                speaker_type = speaker.get('type', 'Unknown')
                power = speaker.get('power', 0)
                sensitivity = speaker.get('sensitivity', 0)
                dispersion = speaker.get('dispersion_angle', 90)

                total_zone_power += power
                speaker_types[speaker_type] = speaker_types.get(speaker_type, 0) + 1

                f.write(f"  Speaker ID: {speaker_id[-8:]}\n")
                f.write(f"    Type: {speaker_type}\n")
                f.write(f"    Power: {power}W\n")
                f.write(f"    Sensitivity: {sensitivity}dB\n")
                f.write(f"    Dispersion: {dispersion}°\n")

                # Additional info based on type
                if speaker_type == "Pendant":
                    mounting_height = speaker.get('mounting_height', 8)
                    f.write(f"    Mounting Height: {mounting_height} ft\n")
                else:  # In-Ceiling (default)
                    diameter = speaker.get('diameter', 6)
                    f.write(f"    Diameter: {diameter} in\n")

                f.write("\n")

            # Zone summary
            f.write("Zone Summary:\n")
            f.write(f"  Total Power: {total_zone_power}W\n")
            f.write(f"  Speaker Types: {', '.join(f'{count} {type_}' for type_, count in speaker_types.items())}\n")
            f.write("\n" + "=" * 60 + "\n\n")

    def _write_zone_content(self, f, data: ReportData):
        """Write zone content for non-speaker reports"""
        zones = data.zones_data.get('zones', [])

        f.write(f"ZONE CONFIGURATION ({len(zones)} zones)\n")
        f.write("-" * 80 + "\n\n")

        if not zones:
            f.write("No zones have been configured for this project.\n\n")
            return

        for i, zone in enumerate(zones):
            f.write(f"Zone {i + 1}: {zone.get('name', f'Zone {i + 1}')}\n")
            f.write("=" * 40 + "\n")
            f.write(f"Environment Type: {zone.get('environment_type', 'Enclosed')}\n")
            f.write(f"Target SPL: {zone.get('target_spl', 'N/A')} dB\n")

            if zone.get('environment_type', 'enclosed') == 'enclosed':
                f.write(f"Ceiling Height: {zone.get('ceiling_height', 'N/A')} ft\n")

            f.write(f"Area: {zone.get('area', 'Not calculated')} ft²\n\n")

            # Controllers and materials
            self._write_zone_equipment_text(f, zone)
            f.write("\n")

    def _write_zone_equipment_text(self, f, zone: Dict[str, Any]):
        """Write controllers and materials in text format"""
        controllers = zone.get('controllers', [])
        materials = zone.get('materials', [])
        notes = zone.get('notes', '')

        if controllers:
            f.write("Controllers:\n")
            for controller in controllers:
                qty = controller.get('quantity', 1)
                f.write(f"  • {controller.get('type', 'Unknown')}: {qty}\n")
            f.write("\n")

        if materials:
            f.write("Materials:\n")
            for material in materials:
                qty = material.get('quantity', 1)
                details = material.get('details', '')
                detail_text = f' ({details})' if details else ''
                f.write(f"  • {material.get('type', 'Unknown')}{detail_text}: {qty}\n")
            f.write("\n")

        if notes:
            f.write("Notes:\n")
            f.write(self._wrap_text(notes, indent="  "))

    def _write_text_summary(self, f, data: ReportData):
        """Write comprehensive summary section"""
        f.write("PROJECT SUMMARY\n")
        f.write("-" * 80 + "\n")

        if data.speaker_layout:
            total_speakers = sum(len(speakers) for speakers in data.speaker_layout.values())
            total_power = self._calculate_total_power(data.speaker_layout)
            zones_with_speakers = len(data.speaker_layout)

            # Speaker type breakdown
            type_counts = {"In-Ceiling": 0, "Pendant": 0}
            for zone_speakers in data.speaker_layout.values():
                zone_counts = self._count_speaker_types(zone_speakers)
                for speaker_type, count in zone_counts.items():
                    type_counts[speaker_type] += count

            f.write(f"Total Zones with Speakers: {zones_with_speakers}\n")
            f.write(f"Total Speakers: {total_speakers}\n")
            f.write(f"Total Power Consumption: {total_power}W\n\n")

            f.write("Speaker Type Breakdown:\n")
            for speaker_type, count in type_counts.items():
                if count > 0:
                    f.write(f"  • {speaker_type}: {count}\n")
            f.write("\n")

            # Amplifier recommendations
            if total_power > 0:
                self._write_amplifier_recommendations(f, total_power)
        else:
            zones = data.zones_data.get('zones', [])
            summary = self._get_material_summary(data.zones_data)
            total_controllers = sum(summary['controllers'].values())
            total_materials = sum(summary['materials'].values())

            f.write(f"Total Zones: {len(zones)}\n")
            f.write(f"Total Controllers: {total_controllers}\n")
            f.write(f"Total Materials: {total_materials}\n\n")

    def _write_amplifier_recommendations(self, f, total_power: int):
        """Write amplifier recommendations"""
        f.write("AMPLIFIER RECOMMENDATIONS\n")
        f.write("-" * 40 + "\n")

        amp_power = total_power * 1.2  # 20% headroom
        f.write(f"Required Power (with 20% headroom): {amp_power:.0f}W\n\n")

        f.write("Recommended Amplifier Configuration:\n")
        if amp_power <= 120:
            f.write("  • Single 120W 70V amplifier\n")
        elif amp_power <= 250:
            f.write("  • Single 250W 70V amplifier\n")
        elif amp_power <= 500:
            f.write("  • Single 500W 70V amplifier\n")
        else:
            import math
            channels = math.ceil(amp_power / 500)
            f.write(f"  • Multiple amplifiers: {channels} × 500W 70V amplifiers\n")
            f.write(f"  • Alternative: Single high-power amplifier ({amp_power:.0f}W or higher)\n")
        f.write("\n")

    def _write_recommendations(self, f, data: ReportData):
        """Write comprehensive recommendations section"""
        f.write("RECOMMENDATIONS\n")
        f.write("-" * 80 + "\n")

        if data.speaker_layout:
            recommendations = [
                "Pre-Installation Verification: Confirm all speaker locations are accessible and comply with local building codes before installation begins.",
                "Acoustic Testing: After installation, use an SPL meter to verify coverage meets design requirements at multiple listening positions throughout each zone.",
                "Room Acoustics Assessment: Evaluate the acoustic properties of each space and consider acoustic treatment if excessive reverberation is present.",
                "Electrical Infrastructure: Ensure 70V wiring is properly sized for power requirements and use plenum-rated cable where mandated by codes.",
                "System Commissioning: Test each zone independently, verify proper operation of all speakers, and confirm amplifier tap settings match specifications.",
                "Documentation: Maintain comprehensive records of speaker locations, power settings, wiring paths, and system configuration.",
                "Regular Maintenance: Schedule periodic inspection and testing to ensure optimal performance and early detection of issues.",
                "Emergency Integration: Verify system integration with fire alarm and emergency notification systems as required by local codes."
            ]
        else:
            recommendations = [
                "Zone Planning Review: Verify all zone assignments provide appropriate coverage for intended use and acoustic requirements.",
                "Equipment Compatibility: Confirm controller compatibility with selected materials and verify power requirements are within system capacity.",
                "Infrastructure Assessment: Evaluate electrical, network, and mounting infrastructure requirements before proceeding with detailed design.",
                "Code Compliance: Review local building and fire codes to ensure all planned installations meet regulatory requirements.",
                "System Integration Planning: Plan integration with existing building systems including fire alarm, security, and automation systems.",
                "Documentation Standards: Establish documentation requirements for as-built drawings, system configuration, and maintenance procedures."
            ]

        for i, rec in enumerate(recommendations, 1):
            f.write(f"{i}. {rec}\n\n")

        f.write("-" * 80 + "\n")
        f.write("End of Report\n")
        f.write("-" * 80 + "\n")