"""
Enhanced HTML formatter with visual elements like thumbnails and snapshots
Updated to work with the new SpeakerView architecture
"""

from typing import Dict, List, Any
from utils.formatters.html_formatter import HTMLReportFormatter
from utils.report_data_models import ReportData, ReportConfig, ReportGenerationResult


class VisualReportFormatter(HTMLReportFormatter):
    """
    Enhanced HTML formatter with visual elements like thumbnails and snapshots
    Updated to work with the new component-based SpeakerView architecture
    """

    def __init__(self, logger=None, speaker_view=None):
        super().__init__(logger)
        self.speaker_view = speaker_view

    @property
    def format_name(self) -> str:
        return "Visual HTML Report"

    def generate(self, data: ReportData, file_path: str, config: ReportConfig = None) -> ReportGenerationResult:
        """Generate visual report with enhanced features"""
        config = self._ensure_config(config)
        warnings = self.validate_data(data)

        # Add warning if speaker view is not available for visual features
        if not self.speaker_view and (config.include_thumbnails or config.include_snapshots):
            warnings.append("Speaker view not available - visual features will be disabled")
            config.include_thumbnails = False
            config.include_snapshots = False

        try:
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                self._write_visual_html_content(f, data, config)

            self.logger.info(f"Visual HTML report generated: {file_path}")
            return self._create_success_result(file_path, warnings)

        except Exception as e:
            error_msg = f"Error generating visual HTML report: {e}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_result(error_msg, warnings)

    def _get_project_info_section(self, project_data: Dict[str, Any]) -> str:
        """Generate project info section for visual reports"""
        # Use the parent class methods
        sections = []
        sections.append(self._get_project_header_section(project_data))
        sections.append(self._get_project_overview_section(project_data))
        sections.append(self._get_client_information_section(project_data))
        sections.append(self._get_system_requirements_section(project_data))
        return ''.join(sections)

    def _write_visual_html_content(self, f, data: ReportData, config: ReportConfig):
        """Write HTML content with visual enhancements"""
        f.write(self._get_enhanced_html_header(data.project_data))
        f.write(self._get_project_info_section(data.project_data))

        if data.speaker_layout and self.speaker_view:
            self._write_visual_speaker_sections(f, data, config)
        else:
            # Fall back to standard sections
            if data.speaker_layout:
                self._write_speaker_sections(f, data, config)
            else:
                self._write_zones_sections(f, data)

        self._write_summary_section(f, data)
        self._write_recommendations_section(f, data)
        f.write('</div></body></html>')

    def _get_enhanced_html_header(self, project_data: Dict[str, Any]) -> str:
        """Get enhanced HTML header with visual styling"""
        project_name = project_data.get('name', 'Unnamed Project')
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Visual Report: {project_name}</title>
    <style>
        {self._get_enhanced_css_styles()}
    </style>
</head>
<body>
<div class="container">
'''

    def _get_enhanced_css_styles(self) -> str:
        """Return enhanced CSS styles for visual reports"""
        base_styles = super()._get_enhanced_css_styles()  # Call the correct parent method
        visual_styles = '''
        .thumbnail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .thumbnail-item {
            text-align: center;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
            background: white;
            transition: transform 0.2s;
        }
        .thumbnail-item:hover {
            transform: translateY(-2px);
            background-color: #f8f9fa;
            border-color: #95a5a6;
        }
        .thumbnail-image {
            width: 100%;
            height: 200px;
            object-fit: contain;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .thumbnail-caption {
            margin-top: 10px;
            font-weight: bold;
            color: #2c3e50;
            font-size: 14px;
        }
        .zone-snapshot {
            text-align: center;
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        .zone-image {
            max-width: 100%;
            height: auto;
            border: 2px solid #bdc3c7;
            border-radius: 4px;
        }
        .zone-properties {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .properties-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        '''
        return base_styles + visual_styles

    def _write_visual_speaker_sections(self, f, data: ReportData, config: ReportConfig):
        """Write speaker sections with visual elements"""
        zones = data.zones_data.get('zones', [])

        # Generate thumbnails if enabled and speaker_view available
        thumbnails = {}
        if config.include_thumbnails and self.speaker_view:
            try:
                # Use the new snapshot renderer through SpeakerView
                thumbnails = self.speaker_view.capture_all_zones_thumbnails(
                    zones, data.speaker_layout, data.obstruction_layout or {}
                )
                self.logger.info(f"Generated {len(thumbnails)} thumbnails")
            except Exception as e:
                self.logger.warning(f"Could not generate thumbnails: {e}")

        # Write thumbnail overview
        if thumbnails:
            self._write_thumbnail_overview(f, zones, data.speaker_layout, thumbnails)

        # Write summary table
        self._write_speaker_summary_table(f, zones, data.speaker_layout)

        # Write detailed sections — always use the visual path so measurements
        # are included even when snapshots are disabled.
        self._write_detailed_visual_zones(f, zones, data, config)

    def _write_thumbnail_overview(self, f, zones: List[Dict], speaker_layout: Dict, thumbnails: Dict):
        """Write thumbnail overview section"""
        f.write('<h2>Zone Overview</h2>')
        f.write('<div class="thumbnail-grid">')

        for zone in zones:
            zone_id = str(zone.get('id', ''))
            if zone_id in thumbnails and zone_id in speaker_layout:
                zone_name = zone.get('name', f'Zone {zone_id}')
                speaker_count = len(speaker_layout[zone_id])

                # Convert thumbnail to base64 if available
                thumbnail_data = self._pixmap_to_base64(thumbnails[zone_id])
                if thumbnail_data:
                    f.write('<div class="thumbnail-item">')
                    f.write(f'<img src="{thumbnail_data}" alt="{zone_name}" class="thumbnail-image">')
                    f.write(f'<div class="thumbnail-caption">{zone_name}<br>{speaker_count} Speakers</div>')
                    f.write('</div>')

        f.write('</div>')

    def _write_detailed_visual_zones(self, f, zones: List[Dict], data: ReportData, config: ReportConfig):
        """Write detailed zone sections with visual snapshots"""
        f.write('<h2>Detailed Zone Analysis</h2>')

        for zone in zones:
            zone_id = str(zone.get('id', ''))
            zone_speakers = data.speaker_layout.get(zone_id, {})
            if not zone_speakers:
                continue

            zone_name = zone.get('name', f'Zone {zone_id}')

            f.write('<div class="zone-section">')
            f.write(f'<h3 class="zone-title">{zone_name}</h3>')

            # Generate snapshot for this zone (only when enabled)
            if config.include_snapshots:
                snapshot = self._generate_zone_snapshot_new(zone, data)
                if snapshot:
                    snapshot_data = self._pixmap_to_base64(snapshot)
                    if snapshot_data:
                        f.write('<div class="zone-snapshot">')
                        f.write(f'<img src="{snapshot_data}" alt="{zone_name} Layout" class="zone-image">')
                        f.write('</div>')

            # Zone properties
            self._write_zone_properties(f, zone)

            # Speaker details table
            self._write_zone_speaker_table(f, zone_speakers)

            # Spacing analysis — always included unless config says otherwise.
            # Try the live renderer first (has calibrated scale_manager); fall back
            # to the parent-class position-based computation.
            if config.include_measurements:
                spacing = self._get_zone_spacing(zone_speakers)
                if spacing is None:
                    scale_factor = (data.zones_data.get('scale_factor', 12.0)
                                    if data.zones_data else 12.0)
                    spacing = self._compute_spacing_summary(zone_speakers, scale_factor)
                self._write_spacing_section(f, spacing)

            f.write('</div>')

    def _get_zone_spacing(self, zone_speakers: Dict[str, Any]):
        """Return spacing summary dict for zone_speakers, or None if unavailable."""
        try:
            # Prefer the live measurement_renderer which has the calibrated scale_manager
            if self.speaker_view and hasattr(self.speaker_view, 'measurement_renderer'):
                return self.speaker_view.measurement_renderer.get_spacing_summary(zone_speakers)
        except Exception as e:
            self.logger.warning(f"Could not compute zone spacing via renderer: {e}")
        return None

    def _generate_zone_snapshot_new(self, zone: Dict[str, Any], data: ReportData) -> Any:
        """
        Generate a snapshot for a specific zone without destroying the rest of the
        speaker layout.

        The old code called load_speaker_layout({zone_id: ...}) which *replaces*
        the entire layout_data with a single zone — wiping every other zone's speakers
        from memory. We now save the full layout beforehand and restore it in finally.
        """
        zone_name = zone.get('name', 'Unknown')
        zone_id = str(zone.get('id', ''))

        if not self.speaker_view:
            self.logger.warning("capture_zone_snapshot: no speaker_view available")
            return None

        try:
            sdm = getattr(self.speaker_view, 'speaker_data_manager', None)

            # ── Save complete original state ──────────────────────────────────
            original_zone    = getattr(self.speaker_view, 'current_zone', None)
            original_zone_id = getattr(sdm, 'current_zone_id', None) if sdm else None
            # Critical: save the FULL layout so we can restore all zones afterwards.
            # load_speaker_layout() replaces layout_data entirely, so without this
            # every zone except the one being snapshotted would lose its speakers.
            original_full_layout = sdm.get_layout_data() if sdm else None

            try:
                # ── Set up state for this zone's snapshot ─────────────────────
                if sdm:
                    # Patch this zone's speakers with the report data, then switch to it.
                    # We update layout_data directly rather than calling load_speaker_layout
                    # so the other zones are left untouched.
                    if zone_id in data.speaker_layout:
                        sdm.layout_data[zone_id] = data.speaker_layout[zone_id].copy()
                    sdm.set_current_zone(zone_id)

                if hasattr(self.speaker_view, 'set_current_zone'):
                    self.speaker_view.set_current_zone(zone)
                else:
                    self.speaker_view.current_zone = zone

                if hasattr(self.speaker_view, 'obstruction_manager') and data.obstruction_layout:
                    self.speaker_view.obstruction_manager.set_current_zone(zone_id)
                    if zone_id in data.obstruction_layout:
                        self.speaker_view.obstruction_manager.obstructions = data.obstruction_layout[zone_id]

                # ── Capture ───────────────────────────────────────────────────
                if hasattr(self.speaker_view, 'snapshot_renderer'):
                    snapshot = self.speaker_view.snapshot_renderer.capture_zone_snapshot(
                        width=1400, height=1000, include_legend=True
                    )
                elif hasattr(self.speaker_view, 'capture_zone_snapshot'):
                    snapshot = self.speaker_view.capture_zone_snapshot(
                        width=1400, height=1000, include_legend=True
                    )
                else:
                    self.logger.warning(f"No snapshot capture method available for {zone_name}")
                    return None

                return snapshot

            finally:
                # ── Restore complete original state ───────────────────────────
                # 1. Reload the full layout (restores all zones' speaker data)
                if sdm and original_full_layout is not None:
                    sdm.load_speaker_layout(original_full_layout)

                # 2. Restore the active zone (must happen after layout restore)
                if sdm and original_zone_id is not None:
                    sdm.set_current_zone(original_zone_id)

                # 3. Restore the view's zone reference
                if original_zone is not None:
                    if hasattr(self.speaker_view, 'set_current_zone'):
                        self.speaker_view.set_current_zone(original_zone)
                    else:
                        self.speaker_view.current_zone = original_zone

        except Exception as e:
            self.logger.error(f"Could not generate snapshot for zone {zone_name}: {e}", exc_info=True)
            return None

    def _generate_zone_snapshot(self, zone: Dict[str, Any], data: ReportData) -> Any:
        """
        DEPRECATED: Old method - kept for compatibility but redirects to new method
        """
        self.logger.warning("Using deprecated _generate_zone_snapshot - redirecting to new method")
        return self._generate_zone_snapshot_new(zone, data)

    def _write_zone_properties(self, f, zone: Dict[str, Any]):
        """Write zone properties section"""
        f.write('<div class="zone-properties">')
        f.write('<h4>Zone Properties</h4>')
        f.write('<div class="properties-grid">')
        f.write(
            f'<div class="property-item"><span class="label">Ceiling Height:</span> {zone.get("ceiling_height", "N/A")} ft</div>')
        f.write(
            f'<div class="property-item"><span class="label">Target SPL:</span> {zone.get("target_spl", "N/A")} dB</div>')
        f.write(f'<div class="property-item"><span class="label">Area:</span> {zone.get("area", "N/A")} ft²</div>')
        f.write(
            f'<div class="property-item"><span class="label">Environment:</span> {zone.get("environment_type", "Enclosed")}</div>')
        f.write('</div>')
        f.write('</div>')

    def _pixmap_to_base64(self, pixmap) -> str:
        """Convert QPixmap to base64 data URL using the new architecture"""
        try:
            # First try to use the new snapshot renderer's method
            if (hasattr(self.speaker_view, 'snapshot_renderer') and
                hasattr(self.speaker_view.snapshot_renderer, 'pixmap_to_base64')):
                return self.speaker_view.snapshot_renderer.pixmap_to_base64(pixmap)

            # Then try the speaker view's delegated method
            elif hasattr(self.speaker_view, 'pixmap_to_base64'):
                return self.speaker_view.pixmap_to_base64(pixmap)

            else:
                # Fallback implementation
                from PySide6.QtCore import QBuffer, QIODevice
                from PySide6.QtGui import QPixmap
                import base64

                if not isinstance(pixmap, QPixmap):
                    return ""

                buffer = QBuffer()
                buffer.open(QIODevice.WriteOnly)
                pixmap.save(buffer, "PNG")
                buffer.close()

                data = buffer.data()
                base64_data = base64.b64encode(data).decode()
                return f"data:image/png;base64,{base64_data}"

        except Exception as e:
            self.logger.warning(f"Could not convert pixmap to base64: {e}")
            return ""