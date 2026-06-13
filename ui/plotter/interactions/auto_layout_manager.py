"""
AutoLayoutManager - Generates optimal speaker layout grids for zones.
Supports rectangular and hexagonal grid patterns, constrained to zone polygon.
"""
import math
import logging
from core.zones.geometry_utils import point_inside_polygon

logger = logging.getLogger(__name__)


class AutoLayoutManager:
    GRID_RECT = 'rect'
    GRID_HEX = 'hex'

    LAYOUT_BBOX = 'bbox'        # Standard: grid centered on bounding box
    LAYOUT_CENTROID = 'centroid'  # Shape-aware: grid anchored to polygon centroid

    # Hard cap — warn the user if layout would exceed this count
    MAX_SPEAKERS = 100

    def __init__(self, acoustic_grid_manager):
        self.acoustic_grid_manager = acoustic_grid_manager

    def _spacing_in_pixels(self, spacing_ft):
        """Convert acoustic spacing (feet) to canvas pixels using the scale manager."""
        try:
            return self.acoustic_grid_manager.scale_manager.feet_to_pixels(spacing_ft)
        except Exception as e:
            logger.error("AutoLayoutManager: could not convert spacing to pixels: %s", e)
            return None

    def _apply_spacing_constraints(self, spacing, coverage_radius):
        """Apply dynamic minimum spacing based on coverage radius."""
        dynamic_min = max(coverage_radius * 0.3, 4.0)
        max_spacing = self.acoustic_grid_manager.MAX_SPACING_FT
        return max(dynamic_min, min(spacing, max_spacing))

    def _calc_spacing_with_overlap(self, profile, zone, overlap_pct):
        """Calculate spacing using a specific overlap percentage (0-100), overriding zone default."""
        if profile.model_type == "In-Ceiling":
            speaker_height = zone.get('ceiling_height', 10.0)
        elif profile.model_type == "Pendant":
            # Use zone pendant default, then profile default, then 9 ft
            speaker_height = zone.get('pendant_height',
                                      getattr(profile, 'default_mounting_height', 9.0))
        else:
            speaker_height = zone.get('ceiling_height', 10.0)

        listener_height = zone.get('listener_height') or 5.5
        coverage_height = max(speaker_height - listener_height, 1.0)
        dispersion_angle = profile.dispersion_angle_h
        if not dispersion_angle or dispersion_angle <= 0 or dispersion_angle > 180:
            dispersion_angle = 90.0

        angle_rad = math.radians(dispersion_angle / 2)
        coverage_radius = coverage_height * math.tan(angle_rad)

        overlap_decimal = min(0.5, overlap_pct / 100.0)  # negative allowed for Wide spacing
        ideal_spacing = 2 * coverage_radius * (1 - overlap_decimal)

        return self._apply_spacing_constraints(ideal_spacing, coverage_radius)

    def get_coverage_radius_ft(self, profile, zone):
        """Return the coverage radius in feet for the given profile and zone."""
        if profile.model_type == "In-Ceiling":
            speaker_height = zone.get('ceiling_height', 10.0)
        elif profile.model_type == "Pendant":
            # Use zone pendant default, then profile default, then 9 ft
            speaker_height = zone.get('pendant_height',
                                      getattr(profile, 'default_mounting_height', 9.0))
        else:
            speaker_height = zone.get('ceiling_height', 10.0)

        listener_height = zone.get('listener_height') or 5.5
        coverage_height = max(speaker_height - listener_height, 1.0)
        dispersion_angle = profile.dispersion_angle_h
        if not dispersion_angle or dispersion_angle <= 0 or dispersion_angle > 180:
            dispersion_angle = 90.0

        angle_rad = math.radians(dispersion_angle / 2)
        return coverage_height * math.tan(angle_rad)

    def preview_layout(self, zone, profile, grid_type=GRID_RECT, overlap_pct=None,
                       layout_method=None):
        """Return (count, spacing_ft) without placing anything."""
        if not zone or not zone.get('points') or not profile:
            return 0, 0.0
        try:
            if overlap_pct is not None:
                spacing_ft = self._calc_spacing_with_overlap(profile, zone, overlap_pct)
            else:
                raw_spacing = self.acoustic_grid_manager.calculate_ideal_speaker_spacing(profile, zone)
                coverage_radius = self.get_coverage_radius_ft(profile, zone)
                spacing_ft = self._apply_spacing_constraints(raw_spacing, coverage_radius)
            if not spacing_ft or spacing_ft <= 0:
                return 0, 0.0
            spacing_px = self._spacing_in_pixels(spacing_ft)
            if not spacing_px or spacing_px <= 0:
                return 0, 0.0
            positions = self._candidates_inside(zone, spacing_px, grid_type, layout_method)
            return len(positions), spacing_ft
        except Exception as e:
            logger.warning("AutoLayoutManager.preview_layout error: %s", e)
            return 0, 0.0

    def generate_layout(self, zone, profile, grid_type=GRID_RECT, overlap_pct=None,
                        layout_method=None):
        """Generate optimal speaker positions for a zone.

        Returns list of (x, y) tuples in canvas pixel coordinates.
        layout_method: LAYOUT_BBOX (default) or LAYOUT_CENTROID (shape-aware).
        """
        if not zone or not zone.get('points'):
            logger.warning("AutoLayoutManager: zone has no points")
            return []

        if overlap_pct is not None:
            spacing_ft = self._calc_spacing_with_overlap(profile, zone, overlap_pct)
        else:
            raw_spacing = self.acoustic_grid_manager.calculate_ideal_speaker_spacing(profile, zone)
            coverage_radius = self.get_coverage_radius_ft(profile, zone)
            spacing_ft = self._apply_spacing_constraints(raw_spacing, coverage_radius)

        if not spacing_ft or spacing_ft <= 0:
            logger.warning("AutoLayoutManager: invalid spacing %s", spacing_ft)
            return []

        spacing_px = self._spacing_in_pixels(spacing_ft)
        if not spacing_px or spacing_px <= 0:
            logger.warning("AutoLayoutManager: could not convert spacing to pixels")
            return []

        result = self._candidates_inside(zone, spacing_px, grid_type, layout_method)
        logger.info("AutoLayoutManager: %s/%s grid → %d inside zone (%.1f ft / %.1f px spacing)",
                    grid_type, layout_method or self.LAYOUT_BBOX, len(result), spacing_ft, spacing_px)
        return result

    def _centroid(self, points):
        """Compute the simple centroid (average) of the polygon vertices."""
        n = len(points)
        return sum(p[0] for p in points) / n, sum(p[1] for p in points) / n

    def _centroid_anchored_candidates(self, min_x, max_x, min_y, max_y, spacing, grid_type, points):
        """Generate a grid anchored to the polygon centroid instead of the bounding box corner.

        For L-shaped or asymmetrical rooms, anchoring to the centroid shifts the grid
        so it grows outward from the actual visual center of the shape rather than the
        corner of its bounding box — reducing the chance of one arm getting a partial row.
        """
        cx, cy = self._centroid(points)

        candidates = []
        if grid_type == self.GRID_HEX:
            row_h = spacing * math.sqrt(3) / 2
            up_rows   = math.ceil((cy - min_y) / row_h) + 1
            down_rows = math.ceil((max_y - cy) / row_h) + 1
            left_cols = math.ceil((cx - min_x) / spacing) + 1
            right_cols = math.ceil((max_x - cx) / spacing) + 1
            for row in range(-up_rows, down_rows + 1):
                y = cy + row * row_h
                x_off = (spacing / 2) if (row % 2 == 1) else 0
                for col in range(-left_cols, right_cols + 1):
                    candidates.append((cx + x_off + col * spacing, y))
        else:
            up_rows   = math.ceil((cy - min_y) / spacing) + 1
            down_rows = math.ceil((max_y - cy) / spacing) + 1
            left_cols = math.ceil((cx - min_x) / spacing) + 1
            right_cols = math.ceil((max_x - cx) / spacing) + 1
            for row in range(-up_rows, down_rows + 1):
                y = cy + row * spacing
                for col in range(-left_cols, right_cols + 1):
                    candidates.append((cx + col * spacing, y))

        return candidates

    def _candidates_inside(self, zone, spacing_px, grid_type, layout_method=None):
        """Generate grid candidates in canvas-pixel space and filter to zone polygon."""
        points = zone['points']
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        if layout_method == self.LAYOUT_CENTROID:
            candidates = self._centroid_anchored_candidates(
                min_x, max_x, min_y, max_y, spacing_px, grid_type, points)
        elif grid_type == self.GRID_HEX:
            candidates = self._hex_candidates(min_x, max_x, min_y, max_y, spacing_px)
        else:
            candidates = self._rect_candidates(min_x, max_x, min_y, max_y, spacing_px)

        return [(x, y) for x, y in candidates if point_inside_polygon((x, y), points)]

    def _rect_candidates(self, min_x, max_x, min_y, max_y, spacing):
        """Generate a centered rectangular grid within the bounding box."""
        W = max_x - min_x
        H = max_y - min_y

        n_cols = max(1, math.floor((W - spacing / 2) / spacing) + 1)
        n_rows = max(1, math.floor((H - spacing / 2) / spacing) + 1)
        start_x = min_x + (W - (n_cols - 1) * spacing) / 2
        start_y = min_y + (H - (n_rows - 1) * spacing) / 2

        return [
            (start_x + col * spacing, start_y + row * spacing)
            for col in range(n_cols)
            for row in range(n_rows)
        ]

    def _hex_candidates(self, min_x, max_x, min_y, max_y, spacing):
        """Generate a centered hexagonal grid within the bounding box."""
        W = max_x - min_x
        H = max_y - min_y
        row_height = spacing * math.sqrt(3) / 2

        n_cols = max(1, math.floor((W - spacing / 2) / spacing) + 1)
        n_rows = max(1, math.floor((H - row_height / 2) / row_height) + 1)
        start_x = min_x + (W - (n_cols - 1) * spacing) / 2
        start_y = min_y + (H - (n_rows - 1) * row_height) / 2

        candidates = []
        for row in range(n_rows):
            y = start_y + row * row_height
            x_off = (spacing / 2) if (row % 2 == 1) else 0
            for col in range(n_cols):
                candidates.append((start_x + x_off + col * spacing, y))
        return candidates
