"""
Compact professional toolbar for the Zones editor.

Replaces the old QToolBar/QAction approach with a QWidget containing
grouped QPushButton and QToolButton controls — much more styling control
and screen-space efficient.
"""

import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QToolButton, QPushButton,
                               QComboBox, QFrame, QMenu, QStyleFactory,
                               QButtonGroup, QLabel)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor, QAction

from ui.styles.base_styles import Colors, Typography

# ── Arrow SVG for QComboBox (same pattern as project_dialog) ─────────────────
_ARROW_SVG = os.path.normpath(
    os.path.join(__file__, "..", "..", "..", "resources", "arrow_down.svg")
)


class ToolbarManager(QObject):
    """Creates and manages the compact zones toolbar widget."""

    # ── Signals ────────────────────────────────────────────────────────────
    # Navigation / project identity (merged from EditorHeaderBar)
    back_requested = Signal()
    header_tab_changed = Signal(int)   # 0 = Zones, 1 = Speaker Plotter

    load_background_requested = Signal(str)
    calibrate_scale_requested = Signal()
    draw_zone_requested = Signal()
    create_zone_requested = Signal()      # NEW — "Enter Dimensions" in menu
    line_color_changed = Signal(object)   # QColor
    grid_toggled = Signal(bool)
    snap_toggled = Signal(bool)
    grid_resolution_requested = Signal(int)
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    zoom_reset_requested = Signal()
    zoom_fit_requested = Signal()
    save_requested = Signal()             # kept for compatibility
    export_image_requested = Signal()
    clear_zones_requested = Signal()
    clear_all_requested = Signal()

    # ── Constants ─────────────────────────────────────────────────────────
    _GRID_SIZES = [4, 6, 8, 12, 16, 24]
    _DEFAULT_GRID_SIZE = 12

    # ── Shared QMenu stylesheet (applied directly to each popup) ──────────
    # Note: we intentionally omit border/border-radius here.
    # On macOS, Fusion style renders its own clean 1px border; adding an
    # explicit border on top creates the "nested card" double-frame artefact.
    _MENU_STYLE = f"""
        QMenu {{
            background-color: {Colors.WHITE};
            padding: 4px 0;
        }}
        QMenu::item {{
            padding: 6px 20px 6px 16px;
            font-size: 12px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QMenu::item:selected {{
            background-color: {Colors.PRIMARY_LIGHT};
            color: {Colors.PRIMARY};
        }}
        QMenu::separator {{
            height: 1px;
            background: {Colors.BORDER_MEDIUM};
            margin: 4px 0;
        }}
    """

    def __init__(self, parent_tab):
        super().__init__(parent_tab)
        self.parent_tab = parent_tab

        # Widget references (set during create_toolbar)
        self.toolbar = None
        self.zone_btn = None
        self.grid_btn = None
        self.snap_btn = None
        self.grid_size_combo = None
        self.color_swatch_btn = None
        self.zoom_label_btn = None
        self.reports_btn = None

        # Identity / navigation widgets (merged from EditorHeaderBar)
        self._project_label = None
        self._modified_dot = None
        self._tab_btn_group = None

        self._current_line_color = QColor(0, 128, 255)

        # Keep Fusion QStyle references alive — Python GC would collect them
        # otherwise since QWidget.setStyle() doesn't take ownership in PySide6.
        self._menu_fusion_styles = []


    # ── Construction ──────────────────────────────────────────────────────

    def create_toolbar(self) -> QWidget:
        """Build and return the compact toolbar widget."""
        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(42)

        # Force Fusion style so QComboBox popup renders correctly on macOS
        fusion = QStyleFactory.create("Fusion")
        if fusion:
            self.toolbar.setStyle(fusion)

        self.toolbar.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.GRAY_100};
                border-bottom: 1px solid {Colors.BORDER_MEDIUM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
        """)

        layout = QHBoxLayout(self.toolbar)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        # ── Navigation / project identity ─────────────────────────────────
        back_btn = QPushButton("← Projects")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setToolTip("Return to projects list")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: 11px;
                font-weight: 500;
                padding: 2px 4px;
                min-height: 26px;
            }}
            QPushButton:hover {{ color: {Colors.PRIMARY_HOVER}; text-decoration: underline; }}
        """)
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn)

        self._project_label = QLabel("No Project")
        self._project_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                border: none;
                padding: 0 4px;
            }}
        """)
        layout.addWidget(self._project_label)

        self._modified_dot = QLabel("●")
        self._modified_dot.setStyleSheet(f"""
            QLabel {{
                color: {Colors.WARNING};
                font-size: 8px;
                background: transparent;
                border: none;
                padding: 0;
            }}
        """)
        self._modified_dot.setVisible(False)
        self._modified_dot.setToolTip("Unsaved changes")
        layout.addWidget(self._modified_dot)

        layout.addSpacing(2)
        layout.addWidget(self._sep())

        # ── Tab toggles (Zones / Speaker Plotter) ─────────────────────────
        layout.addWidget(self._tab_toggle_widget())
        layout.addWidget(self._sep())

        # ── Primary actions ───────────────────────────────────────────────
        bg_btn = self._primary_btn("+ Floorplan", "Load a floorplan image (floor plan, photo, PDF…)")
        bg_btn.clicked.connect(lambda: self.load_background_requested.emit(""))
        layout.addWidget(bg_btn)

        layout.addSpacing(2)

        self.zone_btn = self._zone_split_btn()
        layout.addWidget(self.zone_btn)

        layout.addWidget(self._sep())

        # ── Drawing tools ─────────────────────────────────────────────────
        cal_btn = self._icon_btn("⊙  Calibrate", "Calibrate scale — measure a known distance")
        cal_btn.clicked.connect(self.calibrate_scale_requested.emit)
        layout.addWidget(cal_btn)

        # Color swatch moved into the + Zone dropdown menu
        self.color_swatch_btn = None

        self.grid_btn = self._toggle_btn("⊞  Grid", "Show/hide the drawing grid", checked=True)
        self.grid_btn.clicked.connect(lambda checked: self.grid_toggled.emit(checked))
        layout.addWidget(self.grid_btn)

        self.snap_btn = self._toggle_btn("⊡  Snap", "Snap drawing points to the grid", checked=True)
        self.snap_btn.clicked.connect(lambda checked: self.snap_toggled.emit(checked))
        layout.addWidget(self.snap_btn)

        self.grid_size_combo = self._grid_combo()
        self.grid_size_combo.setToolTip("Grid size — smaller = finer grid for precise floor plan tracing")
        layout.addWidget(self.grid_size_combo)

        layout.addWidget(self._sep())

        # ── Zoom cluster ──────────────────────────────────────────────────
        layout.addWidget(self._zoom_cluster())

        fit_btn = self._icon_btn("⊞ Fit", "Fit all content to view (Ctrl+F)")
        fit_btn.clicked.connect(self.zoom_fit_requested.emit)
        layout.addWidget(fit_btn)

        # ── Spacer ────────────────────────────────────────────────────────
        layout.addStretch()

        # ── Reports menu ──────────────────────────────────────────────────
        self.reports_btn = self._menu_btn("Reports ▾", "Generate project, speaker, and material reports")
        layout.addWidget(self.reports_btn)

        # ── More (⋮) menu ─────────────────────────────────────────────────
        layout.addWidget(self._more_btn())

        # ── Save ──────────────────────────────────────────────────────────
        layout.addWidget(self._sep())
        save_btn = self._primary_btn("Save", "Save the project (Ctrl+S)")
        save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(save_btn)

        return self.toolbar

    # ── Widget factories ──────────────────────────────────────────────────

    def _primary_btn(self, text, tooltip="") -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 12px;
                min-height: 28px;
                max-height: 28px;
            }}
            QPushButton:hover   {{ background-color: {Colors.PRIMARY_HOVER}; }}
            QPushButton:pressed {{ background-color: {Colors.PRIMARY_ACTIVE}; }}
            QPushButton:disabled {{ background-color: {Colors.GRAY_500}; color: white; }}
        """)
        return btn

    def _icon_btn(self, text, tooltip="") -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._icon_style())
        return btn

    def _toggle_btn(self, text, tooltip="", checked=False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._icon_style())
        return btn

    @staticmethod
    def _icon_style() -> str:
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 5px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                font-weight: 500;
                padding: 3px 8px;
                min-height: 26px;
                max-height: 26px;
            }}
            QPushButton:hover:!pressed {{ background-color: {Colors.GRAY_200}; border-color: {Colors.BORDER_MEDIUM}; }}
            QPushButton:pressed        {{ background-color: {Colors.GRAY_400}; }}
            QPushButton:checked        {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
                font-weight: 600;
            }}
            QPushButton:disabled {{ color: {Colors.GRAY_500}; }}
        """

    def _zone_split_btn(self) -> QToolButton:
        """Zone creation dropdown button — single click opens the menu, no split-line divider."""
        btn = QToolButton()
        btn.setText("+ Zone ▾")
        # InstantPopup: the whole button is one click target → no internal divider
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setToolTip("Add a zone")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 12px;
                min-height: 28px;
                max-height: 28px;
            }}
            QToolButton:hover   {{ background-color: {Colors.PRIMARY_HOVER}; }}
            QToolButton:pressed {{ background-color: {Colors.PRIMARY_ACTIVE}; }}
            QToolButton:disabled {{ background-color: {Colors.GRAY_500}; color: white; }}
            QToolButton::menu-indicator {{ image: none; }}
        """)

        menu = QMenu(self.parent_tab)
        self._style_menu(menu)

        dims_act = QAction("⊡  Enter Dimensions", self.parent_tab)
        dims_act.setToolTip("Create a rectangular zone by specifying its dimensions")
        dims_act.triggered.connect(self.create_zone_requested.emit)

        draw_act = QAction("✏  Draw Zone", self.parent_tab)
        draw_act.setToolTip("Draw a freehand polygon zone by clicking points on the canvas")
        draw_act.triggered.connect(self.draw_zone_requested.emit)

        color_act = QAction("🎨  Line Color…", self.parent_tab)
        color_act.setToolTip("Change the drawing line color")
        color_act.triggered.connect(lambda: self.line_color_changed.emit(QColor()))

        menu.addAction(dims_act)
        menu.addAction(draw_act)
        menu.addSeparator()
        menu.addAction(color_act)
        btn.setMenu(menu)
        return btn

    def _color_swatch(self) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(24, 24)
        btn.setToolTip("Drawing line color — click to change")
        btn.setCursor(Qt.PointingHandCursor)
        self._apply_swatch_style(btn, self._current_line_color)
        return btn

    def _apply_swatch_style(self, btn: QPushButton, color: QColor):
        c = color.name() if isinstance(color, QColor) else str(color)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c};
                border: 2px solid {Colors.GRAY_400};
                border-radius: 4px;
            }}
            QPushButton:hover {{ border-color: {Colors.ACCENT}; }}
        """)

    def _grid_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setFixedHeight(26)
        combo.setFixedWidth(80)
        combo.setToolTip("Grid spacing")
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 5px;
                padding: 2px 4px 2px 6px;
                font-size: 11px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QComboBox:hover {{ border-color: {Colors.GRAY_500}; }}
            QComboBox::drop-down {{
                border: none;
                width: 18px;
                subcontrol-origin: padding;
                subcontrol-position: right center;
            }}
            QComboBox::down-arrow {{
                image: url("{_ARROW_SVG}");
                width: 10px;
                height: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                selection-color: {Colors.PRIMARY};
                font-size: 11px;
            }}
        """)
        for size in self._GRID_SIZES:
            combo.addItem(f"{size} px", size)
        try:
            combo.setCurrentIndex(self._GRID_SIZES.index(self._DEFAULT_GRID_SIZE))
        except ValueError:
            combo.setCurrentIndex(0)
        combo.currentIndexChanged.connect(self._on_grid_size_changed)
        return combo

    def _on_grid_size_changed(self, index: int):
        sizes = self._GRID_SIZES
        size = sizes[index] if 0 <= index < len(sizes) else self._DEFAULT_GRID_SIZE
        self.grid_resolution_requested.emit(size)

    def _zoom_cluster(self) -> QWidget:
        """Returns the [−] [100%] [+] grouped zoom widget."""
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        _base = f"""
            QPushButton {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                font-weight: 500;
                min-height: 26px;
                max-height: 26px;
                padding: 0 6px;
            }}
            QPushButton:hover   {{ background-color: {Colors.GRAY_100}; }}
            QPushButton:pressed {{ background-color: {Colors.GRAY_200}; }}
        """

        zoom_out = QPushButton("−")
        zoom_out.setFixedWidth(26)
        zoom_out.setToolTip("Zoom out (Ctrl+−)")
        zoom_out.setStyleSheet(_base + """
            QPushButton {
                border-top-left-radius: 5px;
                border-bottom-left-radius: 5px;
                border-right: none;
            }
        """)
        zoom_out.setCursor(Qt.PointingHandCursor)
        zoom_out.clicked.connect(self.zoom_out_requested.emit)

        self.zoom_label_btn = QPushButton("100%")
        self.zoom_label_btn.setFixedWidth(50)
        self.zoom_label_btn.setToolTip("Click to reset zoom to 100% (Ctrl+0)")
        self.zoom_label_btn.setStyleSheet(_base + f"""
            QPushButton {{
                border-radius: 0;
                border-right: none;
                font-size: 10px;
                color: {Colors.TEXT_SECONDARY};
            }}
        """)
        self.zoom_label_btn.setCursor(Qt.PointingHandCursor)
        self.zoom_label_btn.clicked.connect(self.zoom_reset_requested.emit)

        zoom_in = QPushButton("+")
        zoom_in.setFixedWidth(26)
        zoom_in.setToolTip("Zoom in (Ctrl++)")
        zoom_in.setStyleSheet(_base + """
            QPushButton {
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
        """)
        zoom_in.setCursor(Qt.PointingHandCursor)
        zoom_in.clicked.connect(self.zoom_in_requested.emit)

        layout.addWidget(zoom_out)
        layout.addWidget(self.zoom_label_btn)
        layout.addWidget(zoom_in)
        layout.addSpacing(4)
        return container

    def _menu_btn(self, text, tooltip="") -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 5px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                font-weight: 500;
                padding: 3px 10px;
                min-height: 26px;
                max-height: 26px;
            }}
            QToolButton:hover {{ background-color: {Colors.GRAY_200}; }}
            QToolButton::menu-indicator {{ image: none; }}
        """)
        return btn

    def _more_btn(self) -> QToolButton:
        """⋮ overflow menu: Export, Clear Zones, Clear All."""
        btn = QToolButton()
        btn.setText("⋮")
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setToolTip("More options")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(30, 26)
        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 5px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
                padding: 0;
            }}
            QToolButton:hover {{ background-color: {Colors.GRAY_200}; }}
            QToolButton::menu-indicator {{ image: none; }}
        """)

        menu = QMenu(self.parent_tab)
        self._style_menu(menu)

        export_act = QAction("Export Image…", self.parent_tab)
        export_act.triggered.connect(self.export_image_requested.emit)
        menu.addAction(export_act)

        menu.addSeparator()

        clear_zones_act = QAction("Clear Zones", self.parent_tab)
        clear_zones_act.setToolTip("Remove all zones but keep the floorplan")
        clear_zones_act.triggered.connect(self.clear_zones_requested.emit)
        menu.addAction(clear_zones_act)

        clear_all_act = QAction("Clear All", self.parent_tab)
        clear_all_act.setToolTip("Remove zones and the floorplan")
        clear_all_act.triggered.connect(self.clear_all_requested.emit)
        menu.addAction(clear_all_act)

        btn.setMenu(menu)
        return btn

    @staticmethod
    def _sep() -> QFrame:
        sep = QFrame()
        sep.setFixedSize(1, 22)
        sep.setStyleSheet(f"background-color: {Colors.BORDER_MEDIUM}; border: none;")
        return sep

    # ── Tab toggle widget (Zones / Speaker Plotter) ───────────────────────

    def _tab_toggle_widget(self) -> QWidget:
        """Segmented-control [Zones] [Speaker Plotter] navigation — visually distinct from action buttons."""
        container = QWidget()
        # Gray tray background makes the control read as "navigation", not "action"
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.GRAY_400};
                border-radius: 7px;
                border: none;
            }}
        """)
        clayout = QHBoxLayout(container)
        clayout.setContentsMargins(2, 2, 2, 2)
        clayout.setSpacing(1)

        _pill_base = f"""
            QPushButton {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: 11px;
                font-weight: 500;
                padding: 3px 12px;
                border: 1px solid transparent;
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                min-height: 24px;
                max-height: 24px;
                outline: none;
            }}
            QPushButton:hover:!checked {{
                background-color: {Colors.GRAY_300};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                border-color: {Colors.BORDER_MEDIUM};
                font-weight: 600;
            }}
        """

        zones_btn = QPushButton("Zones")
        zones_btn.setCheckable(True)
        zones_btn.setChecked(True)
        zones_btn.setCursor(Qt.PointingHandCursor)
        zones_btn.setStyleSheet(_pill_base + """
            QPushButton {
                border-top-left-radius: 5px;
                border-bottom-left-radius: 5px;
                border-top-right-radius: 0;
                border-bottom-right-radius: 0;
            }
        """)

        plotter_btn = QPushButton("Speaker Plotter")
        plotter_btn.setCheckable(True)
        plotter_btn.setCursor(Qt.PointingHandCursor)
        plotter_btn.setStyleSheet(_pill_base + """
            QPushButton {
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
        """)

        self._tab_btn_group = QButtonGroup(container)
        self._tab_btn_group.setExclusive(True)
        self._tab_btn_group.addButton(zones_btn, 0)
        self._tab_btn_group.addButton(plotter_btn, 1)

        zones_btn.clicked.connect(lambda: self.header_tab_changed.emit(0))
        plotter_btn.clicked.connect(lambda: self.header_tab_changed.emit(1))

        clayout.addWidget(zones_btn)
        clayout.addWidget(plotter_btn)
        return container

    # ── Menu styling helper ────────────────────────────────────────────────

    def _style_menu(self, menu: QMenu):
        """Apply Fusion style + consistent stylesheet to a QMenu popup.

        On macOS, QMenu popups open as native top-level windows and ignore
        any stylesheet set on a parent widget.  Setting the style and
        stylesheet directly on the QMenu object itself fixes both the
        'black border' artefact and the nested-card appearance.
        """
        menu.setStyleSheet(self._MENU_STYLE)
        fusion = QStyleFactory.create("Fusion")
        if fusion:
            menu.setStyle(fusion)
            # PySide6 does NOT transfer ownership on setStyle(), so we keep a
            # reference here to prevent Python GC from freeing the style
            # while it's still in use.
            self._menu_fusion_styles.append(fusion)

    # ── State management ──────────────────────────────────────────────────

    # Project identity (EditorHeaderBar API parity)

    def set_project_name(self, name: str):
        """Update the project name label in the toolbar."""
        if self._project_label:
            self._project_label.setText(name or "No Project")

    def set_modified(self, is_modified: bool):
        """Show/hide the unsaved-changes indicator dot."""
        if self._modified_dot:
            self._modified_dot.setVisible(is_modified)

    def set_active_tab(self, index: int):
        """Programmatically sync the tab toggle pills without emitting a signal."""
        if not self._tab_btn_group:
            return
        btn = self._tab_btn_group.button(index)
        if btn and not btn.isChecked():
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)

    def set_report_menu(self, menu: QMenu):
        """Attach the report QMenu to the Reports toolbar button."""
        if self.reports_btn and menu:
            self._style_menu(menu)
            self.reports_btn.setMenu(menu)

    def update_draw_zone_button(self):
        """No-op: the zone button is always enabled.

        'Enter Dimensions' (main click) works without a background image.
        'Draw Zone' (dropdown) checks for a background at action time.
        """
        pass

    def set_grid_action_state(self, is_visible: bool):
        if self.grid_btn:
            self.grid_btn.setChecked(is_visible)

    def set_snap_action_state(self, is_enabled: bool):
        if self.snap_btn:
            self.snap_btn.setChecked(is_enabled)

    def enable_snap_action(self, enabled: bool):
        if self.snap_btn:
            self.snap_btn.setEnabled(enabled)

    def update_color_swatch(self, color: QColor):
        """Update the color swatch button to show the new line color."""
        if self.color_swatch_btn and isinstance(color, QColor) and color.isValid():
            self._current_line_color = color
            self._apply_swatch_style(self.color_swatch_btn, color)

    def update_zoom_label(self, zoom_percent: int):
        """Update the zoom percentage readout."""
        if self.zoom_label_btn:
            self.zoom_label_btn.setText(f"{zoom_percent}%")

    # ── Legacy compatibility ───────────────────────────────────────────────
    # These properties existed in the old QAction-based design.
    # Return None — callers that used these as guards (if action:) still work.

    @property
    def draw_zone_action(self):
        return None

    @property
    def line_color_action(self):
        return None

    @property
    def toggle_grid_action(self):
        return None

    @property
    def toggle_snap_action(self):
        return None

    @property
    def grid_resolution_action(self):
        return None
