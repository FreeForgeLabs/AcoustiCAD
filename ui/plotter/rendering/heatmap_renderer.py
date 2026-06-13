"""
HeatmapRenderer - Renders a 2D coverage quality heatmap over the zone floor.
Colors: green=good coverage, yellow=marginal, red=no coverage.
"""
import math
import logging
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtCore import Qt, QRect
from core.zones.geometry_utils import point_inside_polygon

logger = logging.getLogger(__name__)

_COVERAGE_COLORS = [
    (0.0,  QColor(220, 50,  50,  160)),
    (0.4,  QColor(230, 160, 30,  160)),
    (0.7,  QColor(200, 220, 50,  140)),
    (1.0,  QColor(40,  190, 80,  120)),
]


def _lerp_color(a, b, t):
    return QColor(
        int(a.red()   + (b.red()   - a.red())   * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue()  + (b.blue()  - a.blue())  * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def _coverage_color(ratio):
    ratio = max(0.0, min(1.0, ratio))
    for i in range(len(_COVERAGE_COLORS) - 1):
        t0, c0 = _COVERAGE_COLORS[i]
        t1, c1 = _COVERAGE_COLORS[i + 1]
        if t0 <= ratio <= t1:
            t = (ratio - t0) / (t1 - t0) if (t1 - t0) > 0 else 0
            return _lerp_color(c0, c1, t)
    return _COVERAGE_COLORS[-1][1]


class HeatmapRenderer:
    SAMPLE_SPACING_FT = 1.0

    def __init__(self):
        self._enabled = False
        self._cached_image = None
        self._cache_key = None

    def set_enabled(self, enabled):
        self._enabled = enabled
        if not enabled:
            self._cached_image = None
            self._cache_key = None

    def is_enabled(self):
        return self._enabled

    def invalidate_cache(self):
        self._cached_image = None
        self._cache_key = None

    def draw_heatmap(self, painter, zone, speakers, viewport_manager, scale_factor):
        """Draw heatmap onto the painter. Call this with the UNTRANSFORMED painter
        (i.e., after painter.restore() has reset the translate/scale transform)."""
        if not self._enabled or not zone or not zone.get('points'):
            return

        cache_key = self._make_cache_key(zone, speakers, scale_factor)
        if cache_key != self._cache_key or self._cached_image is None:
            self._cached_image = self._render_image(zone, speakers, viewport_manager, scale_factor)
            self._cache_key = cache_key

        if self._cached_image:
            painter.drawImage(0, 0, self._cached_image)

    def _make_cache_key(self, zone, speakers, scale_factor):
        pts = tuple(zone.get('points', []))
        spk_key = tuple(sorted(
            (s.get('id', i), tuple(s.get('position', ())), s.get('dispersion_angle', 0))
            for i, s in enumerate(speakers.values())
        ))
        return (pts, spk_key, round(scale_factor, 2))

    def _render_image(self, zone, speakers, viewport_manager, scale_factor):
        try:
            points = zone['points']
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)

            w = viewport_manager.view_width
            h = viewport_manager.view_height

            image = QImage(int(w), int(h), QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            img_painter = QPainter(image)

            cell_px = max(4, int(self.SAMPLE_SPACING_FT * scale_factor))

            # Precompute speaker coverage radii
            speaker_coverages = []
            for spk in speakers.values():
                pos = spk.get('position')
                if not pos:
                    continue
                radius = self._calc_radius(spk, zone)
                if radius > 0:
                    speaker_coverages.append((pos[0], pos[1], radius))

            # No speakers → nothing to render; return None so no overlay is drawn
            if not speaker_coverages:
                img_painter.end()
                return None

            x_ft = min_x
            while x_ft <= max_x:
                y_ft = min_y
                while y_ft <= max_y:
                    if point_inside_polygon((x_ft, y_ft), points):
                        quality = self._coverage_quality(x_ft, y_ft, speaker_coverages)
                        color = _coverage_color(quality)
                        screen_pos = viewport_manager.world_to_screen(x_ft, y_ft)
                        sx, sy = screen_pos[0], screen_pos[1]
                        img_painter.fillRect(QRect(int(sx), int(sy), cell_px, cell_px), color)
                    y_ft += self.SAMPLE_SPACING_FT
                x_ft += self.SAMPLE_SPACING_FT

            img_painter.end()
            return image
        except Exception as e:
            logger.error("HeatmapRenderer error: %s", e, exc_info=True)
            return None

    def _calc_radius(self, speaker, zone):
        spk_type = speaker.get('type', 'In-Ceiling')
        if spk_type == 'Pendant':
            # Per-speaker mounting_height, falling back to zone pendant default (9 ft)
            height = speaker.get('mounting_height', zone.get('pendant_height', 9.0))
        else:
            height = speaker.get('ceiling_height', zone.get('ceiling_height', 10.0))
        listener_height = speaker.get('listener_height', zone.get('listener_height', 4.0))
        coverage_height = max(0.1, height - listener_height)
        angle = speaker.get('dispersion_angle', speaker.get('dispersion_angle_h', 90.0))
        angle_rad = math.radians(angle / 2)
        return max(1.0, min(coverage_height * math.tan(angle_rad), 50.0))

    def _coverage_quality(self, x, y, speaker_coverages):
        if not speaker_coverages:
            return 0.0
        best = 0.0
        for sx, sy, radius in speaker_coverages:
            dist = math.sqrt((x - sx) ** 2 + (y - sy) ** 2)
            if radius > 0:
                quality = max(0.0, 1.0 - (dist / radius))
                best = max(best, quality)
        return best
