"""
HTML report formatter - Enhanced with full project details
"""

import os
import math
from typing import Dict, List, Any
from PySide6.QtCore import QDateTime
from utils.formatters.base_formatter import BaseReportFormatter
from utils.report_data_models import ReportData, ReportConfig, ReportGenerationResult


class HTMLReportFormatter(BaseReportFormatter):
    """HTML report formatter with comprehensive project details"""

    @property
    def file_extension(self) -> str:
        return '.html'

    @property
    def file_filter(self) -> str:
        return "HTML Files (*.html)"

    @property
    def format_name(self) -> str:
        return "HTML Report"

    def generate(self, data: ReportData, file_path: str, config: ReportConfig = None) -> ReportGenerationResult:
        config = self._ensure_config(config)
        warnings = self.validate_data(data)

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                self._write_html_content(f, data, config)

            self.logger.info(f"HTML report generated: {file_path}")
            return self._create_success_result(file_path, warnings)

        except Exception as e:
            error_msg = f"Error generating HTML report: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_result(error_msg, warnings)

    def _write_html_content(self, f, data: ReportData, config: ReportConfig):
        """Write complete HTML content"""
        f.write(self._get_html_header(data.project_data))
        f.write(self._get_project_header_section(data.project_data))
        f.write(self._get_project_overview_section(data.project_data))
        f.write(self._get_client_information_section(data.project_data))
        f.write(self._get_system_requirements_section(data.project_data))

        if data.speaker_layout:
            self._write_speaker_sections(f, data, config)
        else:
            self._write_zones_sections(f, data)

        self._write_summary_section(f, data)
        self._write_recommendations_section(f, data)
        f.write('</div></body></html>')

    def _get_html_header(self, project_data: Dict[str, Any]) -> str:
        """Generate HTML header with enhanced CSS"""
        project_name = project_data.get('name', 'Unnamed Project')
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Audio System Report: {project_name}</title>
    <style>
        {self._get_enhanced_css_styles()}
    </style>
</head>
<body>
<div class="container">
'''

    def _get_enhanced_css_styles(self) -> str:
        """Return enhanced CSS styles for professional reports"""
        return '''
        body { 
            font-family: 'Helvetica Neue', Arial, Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 0; line-height: 1.6; 
            background-color: #fafafa; color: #333;
        }
        .container { 
            max-width: 1200px; margin: 0 auto; background: white; 
            padding: 40px; 
            border: 1px solid #e0e0e0;
            border-bottom: 3px solid #d0d0d0;
            border-right: 2px solid #d5d5d5;
        }
        .header { 
            text-align: center; border-bottom: 3px solid #2c3e50; 
            padding-bottom: 30px; margin-bottom: 40px;
        }
        .project-title { 
            color: #2c3e50; font-size: 32px; font-weight: bold; 
            margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px;
        }
        .report-subtitle { 
            color: #7f8c8d; font-size: 18px; margin-bottom: 10px;
        }
        .generated-date { 
            color: #95a5a6; font-size: 14px; font-style: italic;
        }
        .section { 
            margin-bottom: 40px; page-break-inside: avoid;
        }
        .section-title { 
            color: #2c3e50; font-size: 24px; font-weight: bold;
            border-left: 6px solid #3498db; padding-left: 15px;
            margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.5px;
        }
        .subsection-title { 
            color: #34495e; font-size: 18px; font-weight: 600;
            margin: 25px 0 15px 0; border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }
        .info-grid { 
            display: grid; grid-template-columns: 1fr 1fr; gap: 30px; 
            margin-bottom: 25px;
        }
        .info-card { 
            background: #f8f9fa; border: 1px solid #e9ecef; 
            border-radius: 8px; padding: 20px;
        }
        .info-label { 
            font-weight: 600; color: #495057; font-size: 12px;
            text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px;
        }
        .info-value { 
            color: #212529; font-size: 16px; word-wrap: break-word;
        }
        .status-badge { 
            display: inline-block; padding: 6px 12px; border-radius: 20px;
            font-size: 12px; font-weight: bold; text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-planning { background: #6c757d; color: white; }
        .status-design { background: #007bff; color: white; }
        .status-approved { background: #28a745; color: white; }
        .status-in-progress { background: #fd7e14; color: white; }
        .status-completed { background: #20c997; color: white; }
        .tags-container { 
            display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;
        }
        .tag { 
            background: #e3f2fd; color: #1976d2; border: 1px solid #bbdefb;
            border-radius: 15px; padding: 4px 12px; font-size: 12px; font-weight: 500;
        }
        table { 
            border-collapse: collapse; width: 100%; margin: 25px 0; 
            background: white; border-radius: 8px; overflow: hidden;
            border: 1px solid #e0e0e0;
            border-bottom: 2px solid #d0d0d0;
        }
        th, td { 
            padding: 15px; text-align: left; border-bottom: 1px solid #e9ecef; 
        }
        th { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.5px; font-size: 12px;
        }
        tr:nth-child(even) { background-color: #f8f9fa; }
        tr:hover { background-color: #e8f4f8; }
        .summary-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 12px; 
            margin: 40px 0; text-align: center;
        }
        .summary-title { 
            font-size: 24px; font-weight: bold; margin-bottom: 20px;
        }
        .summary-stats { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px; margin-top: 25px;
        }
        .stat-item { 
            background: rgba(255,255,255,0.2); padding: 15px; 
            border-radius: 8px; text-align: center;
        }
        .stat-number { 
            font-size: 28px; font-weight: bold; display: block;
        }
        .stat-label { 
            font-size: 14px; opacity: 0.9; text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .recommendations { 
            background: #fff3cd; border: 1px solid #ffeaa7;
            border-radius: 8px; padding: 25px; margin-top: 30px;
        }
        .recommendations h3 { 
            color: #856404; margin-top: 0; font-size: 20px;
        }
        .recommendations ol { 
            padding-left: 20px; color: #856404;
        }
        .recommendations li { 
            margin-bottom: 10px; line-height: 1.6;
        }
        .ceiling-speakers { color: #0066cc; font-weight: bold; }
        .pendant-speakers { color: #009933; font-weight: bold; }
        .surface-speakers { color: #cc3300; font-weight: bold; }
        .power-requirements { 
            background: #e8f5e8; border-left: 4px solid #28a745;
            padding: 15px; margin: 15px 0; border-radius: 4px;
        }
        @media print {
            body { background: white; }
            .container { border: 1px solid #ccc !important; }
            .section { page-break-inside: avoid; }
        }
        '''

    def _get_project_header_section(self, project_data: Dict[str, Any]) -> str:
        """Generate project header section"""
        project_name = project_data.get('name', 'Unnamed Project')
        report_type = "Speaker Placement Report" if 'speaker_layout' in str(project_data) else "Audio System Design Report"

        return f'''
<div class="header">
    <div class="project-title">{project_name}</div>
    <div class="report-subtitle">{report_type}</div>
    <div class="generated-date">Generated: {QDateTime.currentDateTime().toString('MMMM dd, yyyy at hh:mm AP')}</div>
</div>
'''

    def _get_project_overview_section(self, project_data: Dict[str, Any]) -> str:
        """Generate comprehensive project overview"""
        status = project_data.get('project_status', '')
        status_class = f"status-{status.lower().replace(' ', '-')}" if status else "status-planning"

        completion_date = self._format_date(project_data.get('target_completion_date', ''))
        created_date = self._format_date(project_data.get('created_at', ''))
        modified_date = self._format_date(project_data.get('last_modified', ''))

        return f'''
<div class="section">
    <h2 class="section-title">Project Overview</h2>
    
    <div class="info-grid">
        <div class="info-card">
            <div class="info-label">Project Status</div>
            <div class="info-value">
                <span class="status-badge {status_class}">{status or 'Planning'}</span>
            </div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Project Type</div>
            <div class="info-value">{project_data.get('project_type', 'Background Music')}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Facility Type</div>
            <div class="info-value">{project_data.get('facility_type', 'Not specified')}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Budget Range</div>
            <div class="info-value">{project_data.get('budget_range', 'Not specified')}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Installation Type</div>
            <div class="info-value">{project_data.get('installation_type', 'Not specified')}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Target Completion</div>
            <div class="info-value">{completion_date or 'Not specified'}</div>
        </div>
    </div>
    
    <div class="subsection-title">Project Description</div>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db;">
        {project_data.get('description', 'No description provided')}
    </div>
    
    <div class="info-grid" style="margin-top: 25px;">
        <div class="info-card">
            <div class="info-label">Created</div>
            <div class="info-value">{created_date}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Last Modified</div>
            <div class="info-value">{modified_date}</div>
        </div>
    </div>
</div>
'''

    def _get_client_information_section(self, project_data: Dict[str, Any]) -> str:
        """Generate client information section"""
        return f'''
<div class="section">
    <h2 class="section-title">Client Information</h2>
    
    <div class="info-grid">
        <div class="info-card">
            <div class="info-label">Client Name</div>
            <div class="info-value">{project_data.get('client_name', 'Not specified')}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Project Contact</div>
            <div class="info-value">{project_data.get('project_contact', 'Not specified')}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Contact Phone</div>
            <div class="info-value">{project_data.get('contact_phone', 'Not specified')}</div>
        </div>
        
        <div class="info-card">
            <div class="info-label">Project Location</div>
            <div class="info-value">{project_data.get('project_location', 'Not specified')}</div>
        </div>
    </div>
</div>
'''

    def _get_system_requirements_section(self, project_data: Dict[str, Any]) -> str:
        """Generate system requirements section"""
        # Audio sources
        audio_sources = project_data.get('primary_audio_sources', [])
        audio_sources_html = self._create_tags_html(audio_sources) if audio_sources else '<span class="tag">None specified</span>'

        # Control methods
        control_methods = project_data.get('control_system_type', [])
        control_methods_html = self._create_tags_html(control_methods) if control_methods else '<span class="tag">None specified</span>'

        # Environmental factors
        environmental_factors = project_data.get('environmental_factors', [])
        environmental_html = self._create_tags_html(environmental_factors) if environmental_factors else '<span class="tag">None specified</span>'

        # Power requirements
        power_requirements = self._format_power_requirements(project_data)

        return f'''
<div class="section">
    <h2 class="section-title">System Requirements</h2>
    
    <div class="subsection-title">Audio Sources</div>
    <div class="tags-container">
        {audio_sources_html}
    </div>
    
    <div class="subsection-title">Control Methods</div>
    <div class="tags-container">
        {control_methods_html}
    </div>
    
    <div class="subsection-title">Network Infrastructure</div>
    <div class="info-value" style="margin-bottom: 20px;">{project_data.get('network_infrastructure', 'Not specified')}</div>
    
    <div class="subsection-title">Environmental Considerations</div>
    <div class="tags-container">
        {environmental_html}
    </div>
    
    <div class="subsection-title">Power Requirements</div>
    <div class="power-requirements">
        {power_requirements}
    </div>
    
    <div class="subsection-title">Project Notes</div>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 10px;">
        {project_data.get('project_notes', 'No additional notes') or 'No additional notes'}
    </div>
</div>
'''

    def _create_tags_html(self, items: List[str]) -> str:
        """Create HTML for tag display"""
        if not items:
            return '<span class="tag">None specified</span>'

        if isinstance(items, str):
            items = [items]

        return ''.join(f'<span class="tag">{item}</span>' for item in items)

    def _format_power_requirements(self, project_data: Dict[str, Any]) -> str:
        """Format power requirements for display"""
        requirements = ["120V AC Standard"]

        if project_data.get('ups_required', False):
            requirements.append("UPS/Battery Backup Required")
        if project_data.get('voltage_240_available', False):
            requirements.append("240V Available")
        if project_data.get('power_conditioning_needed', False):
            requirements.append("Power Conditioning Required")
        if project_data.get('dedicated_circuit_required', False):
            requirements.append("Dedicated Circuit Required")

        return "<br>".join(f"• {req}" for req in requirements)

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

    def _write_speaker_sections(self, f, data: ReportData, config: ReportConfig):
        """Write speaker-specific sections"""
        zones = data.zones_data.get('zones', [])
        self._write_speaker_summary_table(f, zones, data.speaker_layout)
        self._write_detailed_speaker_zones(f, zones, data)

    def _write_zones_sections(self, f, data: ReportData):
        """Write zone information for non-speaker reports"""
        zones = data.zones_data.get('zones', [])
        f.write('<div class="section">')
        f.write('<h2 class="section-title">Zone Configuration</h2>')

        if not zones:
            f.write('<div class="info-value">No zones have been configured for this project.</div>')
            f.write('</div>')
            return

        for i, zone in enumerate(zones):
            f.write('<div class="info-card" style="margin-bottom: 20px;">')
            f.write(f'<h3 style="color: #2c3e50; margin-top: 0;">Zone {i + 1}: {zone.get("name", f"Zone {i + 1}")}</h3>')

            f.write('<div class="info-grid" style="margin-top: 15px;">')

            f.write('<div>')
            f.write('<div class="info-label">Environment Type</div>')
            f.write(f'<div class="info-value">{zone.get("environment_type", "Enclosed")}</div>')
            f.write('</div>')

            f.write('<div>')
            f.write('<div class="info-label">Target SPL</div>')
            f.write(f'<div class="info-value">{zone.get("target_spl", "N/A")} dB</div>')
            f.write('</div>')

            if zone.get('environment_type', 'enclosed') == 'enclosed':
                f.write('<div>')
                f.write('<div class="info-label">Ceiling Height</div>')
                f.write(f'<div class="info-value">{zone.get("ceiling_height", "N/A")} ft</div>')
                f.write('</div>')

            f.write('<div>')
            f.write('<div class="info-label">Area</div>')
            f.write(f'<div class="info-value">{zone.get("area", "Not calculated")} ft²</div>')
            f.write('</div>')

            f.write('</div>')

            # Controllers and materials
            self._write_zone_equipment(f, zone)
            f.write('</div>')

        f.write('</div>')

    def _write_zone_equipment(self, f, zone: Dict[str, Any]):
        """Write controllers and materials for a zone"""
        controllers = zone.get('controllers', [])
        materials = zone.get('materials', [])
        notes = zone.get('notes', '')

        if controllers or materials or notes:
            f.write('<div style="margin-top: 15px;">')

            if controllers:
                f.write('<div class="subsection-title">Controllers</div>')
                f.write('<ul>')
                for controller in controllers:
                    qty = controller.get('quantity', 1)
                    f.write(f'<li>{controller.get("type", "Unknown")}: {qty}</li>')
                f.write('</ul>')

            if materials:
                f.write('<div class="subsection-title">Materials</div>')
                f.write('<ul>')
                for material in materials:
                    qty = material.get('quantity', 1)
                    details = material.get('details', '')
                    detail_text = f' ({details})' if details else ''
                    f.write(f'<li>{material.get("type", "Unknown")}{detail_text}: {qty}</li>')
                f.write('</ul>')

            if notes:
                f.write('<div class="subsection-title">Notes</div>')
                f.write(f'<div class="info-value">{notes}</div>')

            f.write('</div>')

    def _write_speaker_summary_table(self, f, zones: List[Dict], speaker_layout: Dict):
        """Write speaker summary table"""
        f.write('<div class="section">')
        f.write('<h2 class="section-title">Speaker Configuration Summary</h2>')
        f.write('<table>')
        f.write('<tr><th>Zone</th><th>Speaker Count</th><th>Speaker Types</th><th>Total Power</th><th>Target SPL</th></tr>')

        for zone in zones:
            zone_id = str(zone.get('id', ''))
            zone_speakers = speaker_layout.get(zone_id, {})
            if not zone_speakers:
                continue

            zone_power = sum(s.get('power', 0) for s in zone_speakers.values())
            type_counts = self._count_speaker_types(zone_speakers)
            type_str = self._format_speaker_types(type_counts)

            f.write('<tr>')
            f.write(f'<td><strong>{zone.get("name", f"Zone {zone_id}")}</strong></td>')
            f.write(f'<td>{len(zone_speakers)}</td>')
            f.write(f'<td>{type_str}</td>')
            f.write(f'<td>{zone_power} W</td>')
            f.write(f'<td>{zone.get("target_spl", "N/A")} dB</td>')
            f.write('</tr>')

        f.write('</table>')
        f.write('</div>')

    def _format_speaker_types(self, type_counts: Dict[str, int]) -> str:
        """Format speaker type counts for display"""
        parts = []
        for speaker_type, count in type_counts.items():
            if count > 0:
                css_class = speaker_type.lower().replace(' ', '-') + '-speakers'
                parts.append(f'<span class="{css_class}">{count} {speaker_type}</span>')
        return ', '.join(parts)

    def _write_detailed_speaker_zones(self, f, zones: List[Dict], data: ReportData):
        """Write detailed zone sections for speaker reports"""
        f.write('<div class="section">')
        f.write('<h2 class="section-title">Detailed Zone Analysis</h2>')

        for zone in zones:
            zone_id = str(zone.get('id', ''))
            zone_speakers = data.speaker_layout.get(zone_id, {})
            if not zone_speakers:
                continue

            zone_name = zone.get('name', f'Zone {zone_id}')

            f.write('<div class="info-card" style="margin-bottom: 30px;">')
            f.write(f'<h3 style="color: #2c3e50; margin-top: 0;">{zone_name}</h3>')

            # Zone properties grid
            f.write('<div class="info-grid">')
            f.write('<div>')
            f.write('<div class="info-label">Ceiling Height</div>')
            f.write(f'<div class="info-value">{zone.get("ceiling_height", "N/A")} ft</div>')
            f.write('</div>')

            f.write('<div>')
            f.write('<div class="info-label">Target SPL</div>')
            f.write(f'<div class="info-value">{zone.get("target_spl", "N/A")} dB</div>')
            f.write('</div>')

            f.write('<div>')
            f.write('<div class="info-label">Area</div>')
            f.write(f'<div class="info-value">{zone.get("area", "N/A")} ft²</div>')
            f.write('</div>')

            f.write('<div>')
            f.write('<div class="info-label">Environment</div>')
            f.write(f'<div class="info-value">{zone.get("environment_type", "Enclosed")}</div>')
            f.write('</div>')
            f.write('</div>')

            # Speaker details table
            self._write_zone_speaker_table(f, zone_speakers)

            # Spacing analysis — computed directly from position data + scale_factor
            scale_factor = data.zones_data.get('scale_factor', 12.0) if data.zones_data else 12.0
            spacing = self._compute_spacing_summary(zone_speakers, scale_factor)
            self._write_spacing_section(f, spacing)

            f.write('</div>')

        f.write('</div>')

    def _write_zone_speaker_table(self, f, zone_speakers: Dict):
        """Write detailed speaker table for a specific zone"""
        if not zone_speakers:
            return

        f.write('<div class="subsection-title">Speaker Details</div>')
        f.write('<table>')
        f.write('<tr><th>#</th><th>Model</th><th>Type</th><th>Power</th><th>Sensitivity</th><th>Dispersion</th><th>Notes</th></tr>')

        for idx, (speaker_id, speaker) in enumerate(zone_speakers.items(), start=1):
            speaker_type = speaker.get('type', 'Unknown')
            power = speaker.get('power', 0)
            sensitivity = speaker.get('sensitivity', 0)
            dispersion = speaker.get('dispersion_angle', 90)

            # Build human-readable model name from stored profile fields
            manufacturer = speaker.get('manufacturer', '').strip()
            model_name = speaker.get('name', '').strip()
            if manufacturer and model_name:
                model_label = f"{manufacturer} {model_name}"
            elif model_name:
                model_label = model_name
            elif manufacturer:
                model_label = manufacturer
            else:
                model_label = f"Speaker {idx}"

            # Notes: type-specific sizing info
            notes = ""
            if speaker_type == "Pendant":
                mounting_height = speaker.get('mounting_height', 8)
                notes = f"Hanging height: {mounting_height} ft"
            else:  # In-Ceiling (default)
                diameter = speaker.get('diameter', 6)
                notes = f'Diameter: {diameter}"'

            # CSS class for type colouring
            css_class = speaker_type.lower().replace(' ', '-') + '-speakers'

            f.write('<tr>')
            f.write(f'<td style="text-align:center;color:#666;">{idx}</td>')
            f.write(f'<td><strong>{model_label}</strong></td>')
            f.write(f'<td><span class="{css_class}">{speaker_type}</span></td>')
            f.write(f'<td>{power} W</td>')
            f.write(f'<td>{sensitivity} dB</td>')
            f.write(f'<td>{dispersion}&deg;</td>')
            f.write(f'<td>{notes}</td>')
            f.write('</tr>')

        f.write('</table>')

    def _compute_spacing_summary(self, speakers_dict: Dict, scale_factor: float) -> dict:
        """
        Compute nearest-neighbor spacing summary purely from position data.

        Args:
            speakers_dict: {speaker_id: speaker_data} where each speaker has a 'position' key
            scale_factor: pixels-per-foot conversion (from zones_data['scale_factor'])

        Returns:
            Dict with min_ft, max_ft, avg_ft, uniform, distances — or None if < 2 speakers.
        """
        if scale_factor <= 0:
            scale_factor = 12.0  # 12 px/ft default (1 px = 1 inch)

        speakers = [s for s in speakers_dict.values() if s.get('position')]
        if len(speakers) < 2:
            return None

        measured_pairs = set()
        distances = []

        for spk in speakers:
            pos = spk['position']
            x1, y1 = pos[0], pos[1]

            # Find nearest neighbor
            best_other, best_dist = None, float('inf')
            for other in speakers:
                if other.get('id') == spk.get('id'):
                    continue
                op = other.get('position')
                if not op:
                    continue
                d = math.hypot(x1 - op[0], y1 - op[1])
                if d < best_dist:
                    best_dist = d
                    best_other = other

            if best_other is None:
                continue

            pair_id = tuple(sorted([spk.get('id', ''), best_other.get('id', '')]))
            if pair_id in measured_pairs:
                continue
            measured_pairs.add(pair_id)
            distances.append(best_dist / scale_factor)

        if not distances:
            return None

        mn, mx = min(distances), max(distances)
        return {
            'min_ft':    mn,
            'max_ft':    mx,
            'avg_ft':    sum(distances) / len(distances),
            'uniform':   (mx - mn) < 0.5,
            'distances': distances,
        }

    def _write_spacing_section(self, f, spacing_summary):
        """Write speaker spacing analysis block. No-op if summary is None."""
        if not spacing_summary:
            return

        mn  = spacing_summary['min_ft']
        mx  = spacing_summary['max_ft']
        avg = spacing_summary['avg_ft']
        uniform = spacing_summary['uniform']
        count   = len(spacing_summary.get('distances', []))

        uniformity_color = '#28a745' if uniform else '#fd7e14'
        uniformity_label = 'Uniform ✓' if uniform else 'Variable'

        f.write('<div class="subsection-title">Speaker Spacing Analysis</div>')
        f.write('<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:15px 0 10px;">')

        for label, value in [
            ('Min Spacing',  f'{mn:.1f} ft'),
            ('Max Spacing',  f'{mx:.1f} ft'),
            ('Avg Spacing',  f'{avg:.1f} ft'),
            ('Uniformity',   f'<span style="color:{uniformity_color};font-weight:bold;">{uniformity_label}</span>'),
        ]:
            f.write(
                f'<div style="background:#f8f9fa;border:1px solid #e9ecef;border-radius:6px;'
                f'padding:12px;text-align:center;">'
                f'<div style="font-size:11px;font-weight:600;color:#495057;text-transform:uppercase;'
                f'letter-spacing:0.5px;">{label}</div>'
                f'<div style="font-size:18px;color:#212529;margin-top:5px;">{value}</div>'
                f'</div>'
            )

        f.write('</div>')

        if not uniform:
            diff = mx - mn
            f.write(
                f'<p style="font-size:12px;color:#856404;background:#fff3cd;padding:8px 12px;'
                f'border-radius:4px;margin:0 0 15px;">'
                f'&#9888; Spacing varies by {diff:.1f} ft across {count} measured pairs. '
                f'Review placement for uniform coverage.'
                f'</p>'
            )

    def _write_summary_section(self, f, data: ReportData):
        """Write enhanced summary section"""
        f.write('<div class="summary-card">')
        f.write('<div class="summary-title">Project Summary</div>')

        if data.speaker_layout:
            self._write_speaker_summary(f, data)
        else:
            self._write_zone_summary(f, data)

        f.write('</div>')

    def _write_speaker_summary(self, f, data: ReportData):
        """Write speaker-specific summary with statistics"""
        total_speakers = sum(len(speakers) for speakers in data.speaker_layout.values())
        total_power = self._calculate_total_power(data.speaker_layout)
        zones_with_speakers = len(data.speaker_layout)

        type_counts = {"In-Ceiling": 0, "Pendant": 0}
        for zone_speakers in data.speaker_layout.values():
            zone_counts = self._count_speaker_types(zone_speakers)
            for speaker_type, count in zone_counts.items():
                type_counts[speaker_type] += count

        f.write('<div class="summary-stats">')

        f.write('<div class="stat-item">')
        f.write(f'<span class="stat-number">{total_speakers}</span>')
        f.write('<span class="stat-label">Total Speakers</span>')
        f.write('</div>')

        f.write('<div class="stat-item">')
        f.write(f'<span class="stat-number">{total_power}W</span>')
        f.write('<span class="stat-label">Total Power</span>')
        f.write('</div>')

        f.write('<div class="stat-item">')
        f.write(f'<span class="stat-number">{zones_with_speakers}</span>')
        f.write('<span class="stat-label">Zones with Speakers</span>')
        f.write('</div>')

        # Speaker type breakdown
        for speaker_type, count in type_counts.items():
            if count > 0:
                f.write('<div class="stat-item">')
                f.write(f'<span class="stat-number">{count}</span>')
                f.write(f'<span class="stat-label">{speaker_type}</span>')
                f.write('</div>')

        f.write('</div>')

        # Amplifier recommendations
        if total_power > 0:
            f.write('<div style="margin-top: 30px; padding: 20px; background: rgba(255,255,255,0.2); border-radius: 8px;">')
            f.write('<h3 style="margin-top: 0; color: white;">Amplifier Recommendations</h3>')
            self._write_amplifier_recommendations_text(f, total_power)
            f.write('</div>')

    def _write_zone_summary(self, f, data: ReportData):
        """Write zone-specific summary"""
        zones = data.zones_data.get('zones', [])
        summary = self._get_material_summary(data.zones_data)

        total_controllers = sum(summary['controllers'].values())
        total_materials = sum(summary['materials'].values())

        f.write('<div class="summary-stats">')

        f.write('<div class="stat-item">')
        f.write(f'<span class="stat-number">{len(zones)}</span>')
        f.write('<span class="stat-label">Total Zones</span>')
        f.write('</div>')

        f.write('<div class="stat-item">')
        f.write(f'<span class="stat-number">{total_controllers}</span>')
        f.write('<span class="stat-label">Controllers</span>')
        f.write('</div>')

        f.write('<div class="stat-item">')
        f.write(f'<span class="stat-number">{total_materials}</span>')
        f.write('<span class="stat-label">Materials</span>')
        f.write('</div>')

        f.write('</div>')

    def _write_amplifier_recommendations_text(self, f, total_power: int):
        """Write amplifier recommendations as text"""
        amp_power = total_power * 1.2  # 20% headroom

        f.write('<p style="color: white; margin: 0;">Based on total power requirements with 20% headroom:</p>')
        f.write('<ul style="color: white; margin: 10px 0;">')

        if amp_power <= 120:
            f.write('<li>Single 120W 70V amplifier</li>')
        elif amp_power <= 250:
            f.write('<li>Single 250W 70V amplifier</li>')
        elif amp_power <= 500:
            f.write('<li>Single 500W 70V amplifier</li>')
        else:
            channels = math.ceil(amp_power / 500)
            f.write(f'<li>Multiple amplifiers: {channels} × 500W 70V amplifiers</li>')

        f.write('</ul>')

    def _write_recommendations_section(self, f, data: ReportData):
        """Write comprehensive recommendations section"""
        f.write('<div class="recommendations">')
        f.write('<h3>Installation & Commissioning Recommendations</h3>')
        f.write('<ol>')

        if data.speaker_layout:
            recommendations = [
                "<strong>Pre-Installation Verification:</strong> Confirm all speaker locations are accessible and comply with local building codes before installation begins.",
                "<strong>Acoustic Testing:</strong> After installation, use an SPL meter to verify coverage meets design requirements at multiple listening positions throughout each zone.",
                "<strong>Room Acoustics Assessment:</strong> Evaluate the acoustic properties of each space and consider acoustic treatment if excessive reverberation or echo is present.",
                "<strong>Electrical Infrastructure:</strong> Ensure 70V wiring is properly sized for power requirements and use plenum-rated cable where mandated by local codes.",
                "<strong>System Commissioning:</strong> Test each zone independently, verify proper operation of all speakers, and confirm amplifier tap settings match design specifications.",
                "<strong>Documentation:</strong> Maintain comprehensive records of speaker locations, power settings, wiring paths, and system configuration for future maintenance and troubleshooting.",
                "<strong>Regular Maintenance:</strong> Schedule periodic inspection and testing to ensure optimal performance and early detection of potential issues.",
                "<strong>Emergency Integration:</strong> Verify system integration with fire alarm and emergency notification systems as required by local fire codes and AHJ requirements."
            ]
        else:
            recommendations = [
                "<strong>Zone Planning Review:</strong> Verify all zone assignments provide appropriate coverage for the intended use and acoustic requirements.",
                "<strong>Equipment Compatibility:</strong> Confirm controller compatibility with selected materials and verify power requirements are within system capacity.",
                "<strong>Infrastructure Assessment:</strong> Evaluate electrical, network, and mounting infrastructure requirements before proceeding with detailed design.",
                "<strong>Code Compliance:</strong> Review local building and fire codes to ensure all planned installations meet regulatory requirements.",
                "<strong>System Integration Planning:</strong> Plan integration with existing building systems including fire alarm, security, and building automation systems.",
                "<strong>Documentation Standards:</strong> Establish documentation requirements for as-built drawings, system configuration, and maintenance procedures."
            ]

        for rec in recommendations:
            f.write(f'<li>{rec}</li>')

        f.write('</ol>')
        f.write('</div>')