"""
MeasurementRenderer — draws nearest-neighbor spacing lines between speakers.

Each speaker pair (A → nearest B) gets one dimension line with a feet label.
Coordinates are in canvas pixels (matching speaker position storage).
Distances are converted to feet via scale_manager for display.
"""
import math
import logging
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF

logger = logging.getLogger(__name__)

# ── Visual constants (canvas pixels) ──────────────────────────────────────────
_OFFSET_PX   = 20    # perpendicular distance from speaker-to-speaker line
_ARROW_PX    = 7     # arrowhead length
_ARROW_W_PX  = 3     # arrowhead half-width
_FONT_SIZE   = 8     # pt — scales with zoom (intentional)
_LINE_COLOR  = QColor(30, 30, 30, 210)
_TEXT_BG     = QColor(255, 255, 255, 220)


class MeasurementRenderer:
    """Renders nearest-neighbor spacing annotations between speakers."""

    def __init__(self, scale_manager):
        self.scale_manager = scale_manager
        self.visible = False

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_visible(self, visible: bool):
        self.visible = visible

    def is_visible(self) -> bool:
        return self.visible

    def clear(self):
        self.visible = False

    def draw_measurements(self, painter, speakers_dict, zone_data):
        """Draw nearest-neighbor dimension lines for all speaker pairs."""
        if not self.visible or not speakers_dict:
            return

        speakers = [s for s in speakers_dict.values() if s.get('position')]
        if len(speakers) < 2:
            return

        painter.save()
        try:
            self._draw_nearest_neighbor_lines(painter, speakers)
        finally:
            painter.restore()

    # ── Nearest-neighbor logic ─────────────────────────────────────────────────

    def _draw_nearest_neighbor_lines(self, painter, speakers):
        """One dimension line per unique adjacent pair."""
        measured_pairs = set()

        for spk in speakers:
            pos1 = spk.get('position')
            x1, y1 = pos1[0], pos1[1]

            # Find single nearest neighbor
            nearest, dist_px = self._nearest_neighbor(spk, speakers)
            if nearest is None:
                continue

            pair_id = tuple(sorted([spk['id'], nearest['id']]))
            if pair_id in measured_pairs:
                continue
            measured_pairs.add(pair_id)

            pos2 = nearest.get('position')
            x2, y2 = pos2[0], pos2[1]

            dist_ft = self.scale_manager.pixels_to_feet(dist_px)
            self._draw_dimension_line(painter, x1, y1, x2, y2, dist_ft)

    @staticmethod
    def _nearest_neighbor(speaker, all_speakers):
        """Return (nearest_speaker, distance_px) for the closest other speaker."""
        pos = speaker.get('position')
        x, y = pos[0], pos[1]
        best_spk, best_dist = None, float('inf')
        for other in all_speakers:
            if other['id'] == speaker['id']:
                continue
            op = other.get('position')
            if not op:
                continue
            d = math.hypot(x - op[0], y - op[1])
            if d < best_dist:
                best_dist = d
                best_spk = other
        return best_spk, best_dist

    # ── Drawing helpers ────────────────────────────────────────────────────────

    def _draw_dimension_line(self, painter, x1, y1, x2, y2, dist_ft):
        """Draw an offset dimension line with arrowheads and a feet label."""
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 1:
            return

        # Perpendicular unit vector — offset the line above/beside the speakers
        perp_x = -dy / length
        perp_y =  dx / length

        ox1 = x1 + perp_x * _OFFSET_PX
        oy1 = y1 + perp_y * _OFFSET_PX
        ox2 = x2 + perp_x * _OFFSET_PX
        oy2 = y2 + perp_y * _OFFSET_PX

        pen = QPen(_LINE_COLOR, 1, Qt.SolidLine)
        pen.setCosmetic(False)
        painter.setPen(pen)

        # Main dimension line
        painter.drawLine(QPointF(ox1, oy1), QPointF(ox2, oy2))

        # Extension lines (from speaker centre to dimension line)
        ext = _OFFSET_PX * 1.15
        painter.drawLine(QPointF(x1, y1), QPointF(x1 + perp_x * ext, y1 + perp_y * ext))
        painter.drawLine(QPointF(x2, y2), QPointF(x2 + perp_x * ext, y2 + perp_y * ext))

        # Arrowheads
        self._draw_arrowhead(painter, ox1, oy1, ox2, oy2)
        self._draw_arrowhead(painter, ox2, oy2, ox1, oy1)

        # Label at midpoint
        mid_x = (ox1 + ox2) / 2
        mid_y = (oy1 + oy2) / 2
        self._draw_label(painter, mid_x, mid_y, self._format_ft(dist_ft))

    def _draw_arrowhead(self, painter, tip_x, tip_y, tail_x, tail_y):
        """Filled triangle arrowhead pointing from tail toward tip."""
        dx, dy = tip_x - tail_x, tip_y - tail_y
        length = math.hypot(dx, dy)
        if length < 0.01:
            return
        ux, uy = dx / length, dy / length          # unit vector toward tip
        px, py = -uy, ux                            # perpendicular

        tip  = QPointF(tip_x, tip_y)
        base1 = QPointF(tip_x - ux * _ARROW_PX + px * _ARROW_W_PX,
                        tip_y - uy * _ARROW_PX + py * _ARROW_W_PX)
        base2 = QPointF(tip_x - ux * _ARROW_PX - px * _ARROW_W_PX,
                        tip_y - uy * _ARROW_PX - py * _ARROW_W_PX)

        path = QPainterPath()
        path.moveTo(tip)
        path.lineTo(base1)
        path.lineTo(base2)
        path.closeSubpath()
        painter.fillPath(path, QBrush(_LINE_COLOR))

    def _draw_label(self, painter, x, y, text):
        """White-backed text label centred on (x, y)."""
        font = QFont("Arial", _FONT_SIZE, QFont.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        th = fm.height()

        pad = 2
        bg = QRectF(x - tw / 2 - pad, y - th / 2 - pad, tw + pad * 2, th + pad * 2)
        painter.fillRect(bg, _TEXT_BG)

        painter.setPen(QPen(_LINE_COLOR))
        painter.drawText(QPointF(x - tw / 2, y + th / 2 - fm.descent()), text)

    @staticmethod
    def _format_ft(feet: float) -> str:
        """Format feet as e.g. '8.3 ft' or '12'-6"'."""
        whole = int(feet)
        inches = round((feet - whole) * 12)
        if inches == 0:
            return f"{whole}'-0\""
        if inches == 12:
            return f"{whole + 1}'-0\""
        return f"{whole}'-{inches}\""

    # ── Report data helper ─────────────────────────────────────────────────────

    def get_spacing_summary(self, speakers_dict) -> dict:
        """
        Calculate nearest-neighbor distances for all speakers.
        Returns a dict suitable for report generation:
          {
            'min_ft': float, 'max_ft': float, 'avg_ft': float,
            'uniform': bool,   # True if all distances within 6 inches
            'distances': [float, ...]
          }
        Returns None if fewer than 2 speakers.
        """
        speakers = [s for s in speakers_dict.values() if s.get('position')]
        if len(speakers) < 2:
            return None

        measured_pairs = set()
        distances = []

        for spk in speakers:
            nearest, dist_px = self._nearest_neighbor(spk, speakers)
            if nearest is None:
                continue
            pair_id = tuple(sorted([spk['id'], nearest['id']]))
            if pair_id in measured_pairs:
                continue
            measured_pairs.add(pair_id)
            distances.append(self.scale_manager.pixels_to_feet(dist_px))

        if not distances:
            return None

        mn, mx = min(distances), max(distances)
        return {
            'min_ft':    mn,
            'max_ft':    mx,
            'avg_ft':    sum(distances) / len(distances),
            'uniform':   (mx - mn) < 0.5,   # within 6 inches = "uniform"
            'distances': distances,
        }
