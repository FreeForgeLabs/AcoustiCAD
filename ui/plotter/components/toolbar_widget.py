"""
Compact plotter toolbar — same visual style as the zones-tab toolbar.

Includes navigation (← Projects, project name, tab pills, Save) so the
user can get back to zones or the project list without a dedicated header bar.
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QToolButton, QPushButton,
                               QLabel, QFrame, QMenu, QButtonGroup,
                               QStyleFactory, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QAction

from ui.styles.base_styles import Colors, Typography


class ToolbarWidget(QWidget):
    """Compact plotter toolbar with navigation and plotter-specific controls."""

    # ── Navigation signals (mirror ToolbarManager) ─────────────────────
    back_requested = Signal()
    tab_changed = Signal(int)        # 0 = Zones, 1 = Speaker Plotter
    save_requested = Signal()

    # ── Plotter action signals ─────────────────────────────────────────
    show_coverage_toggled = Signal(bool)
    min_spacing_toggled = Signal(bool)
    show_grid_toggled = Signal(bool)
    grid_snapping_toggled = Signal(bool)
    show_measurements_toggled = Signal(bool)
    save_layout_requested = Signal()
    export_report_requested = Signal()

    # ── Layout / viz signals ───────────────────────────────────────────
    grid_type_changed = Signal(str)   # 'rect' or 'hex'
    auto_layout_requested = Signal()
    viz_mode_changed = Signal(str)    # 'circles' or 'heatmap'
    clear_speakers_requested = Signal()
    obstruct_mode_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)

        fusion = QStyleFactory.create("Fusion")
        if fusion:
            self.setStyle(fusion)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.GRAY_200};
                border-bottom: 1px solid {Colors.BORDER_MEDIUM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
        """)

        self._project_label = None
        self._modified_dot = None
        self._tab_btn_group = None
        self._obstruct_btn = None
        self._reports_btn = None

        # Layout / viz state
        self._grid_type = 'rect'
        self._viz_mode = 'circles'

        # Legacy action stubs (code that calls these still works)
        self.show_coverage_action = _StubAction()
        self.min_spacing_action = _StubAction()
        self.show_grid_action = _StubAction()
        self.grid_snapping_action = _StubAction()
        self.show_measurements_action = _StubAction()
        self.save_layout_action = _StubAction()
        self.export_report_action = _StubAction()
        self.grid_info_label = None

        self._build()

    # ── Construction ──────────────────────────────────────────────────

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        # ── Navigation ────────────────────────────────────────────────
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

        # ── Tab toggles ───────────────────────────────────────────────
        layout.addWidget(self._tab_toggle_widget())
        layout.addWidget(self._sep())

        # ── Plotter controls ──────────────────────────────────────────
        self._cov_btn = self._toggle_btn("Coverage", "Show/hide speaker coverage patterns", checked=True)
        self._cov_btn.clicked.connect(lambda c: self.show_coverage_toggled.emit(c))
        self._cov_btn.clicked.connect(lambda c: self.show_coverage_action._set(c))
        layout.addWidget(self._cov_btn)

        self._meas_btn = self._toggle_btn("Measure", "Show dimension lines")
        self._meas_btn.clicked.connect(lambda c: self.show_measurements_toggled.emit(c))
        self._meas_btn.clicked.connect(lambda c: self.show_measurements_action._set(c))
        layout.addWidget(self._meas_btn)

        layout.addWidget(self._sep())

        # Auto Layout button
        auto_btn = self._small_icon_btn("Auto Layout", "Place speakers automatically using selected grid type")
        auto_btn.clicked.connect(self.auto_layout_requested.emit)
        layout.addWidget(auto_btn)

        # Clear all speakers button
        self._clear_btn = self._small_icon_btn("× Clear", "Remove all speakers from zone")
        self._clear_btn.clicked.connect(self.clear_speakers_requested.emit)
        layout.addWidget(self._clear_btn)

        self._obstruct_btn = self._toggle_btn("⬛ Obstruct", "Draw sound obstructions (walls, pillars)")
        self._obstruct_btn.clicked.connect(lambda c: self.obstruct_mode_toggled.emit(c))
        layout.addWidget(self._obstruct_btn)

        layout.addWidget(self._sep())

        # ── Reports dropdown ──────────────────────────────────────────
        self._reports_btn = self._menu_btn("Reports ▾", "Generate project, speaker, and material reports")
        layout.addWidget(self._reports_btn)

        # ── Spacer ────────────────────────────────────────────────────
        layout.addStretch()

        # ── Save ──────────────────────────────────────────────────────
        save_btn = self._primary_btn("Save", "Save the project (Ctrl+S)")
        save_btn.clicked.connect(self.save_requested.emit)
        save_btn.clicked.connect(self.save_layout_requested.emit)
        save_btn.clicked.connect(lambda: self.save_layout_action._set(True))
        layout.addWidget(save_btn)

    # ── Widget factories (same helpers as zones ToolbarManager) ───────

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
            QPushButton:disabled {{ color: {Colors.TEXT_MUTED}; }}
        """

    def _small_toggle_btn(self, text, tooltip="", checked=False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 4px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 10px;
                font-weight: 500;
                padding: 4px 8px;
                min-height: 22px;
                max-height: 22px;
            }}
            QPushButton:hover:!pressed {{ background-color: {Colors.GRAY_200}; }}
            QPushButton:pressed        {{ background-color: {Colors.GRAY_400}; }}
            QPushButton:checked        {{
                background-color: {Colors.PRIMARY};
                color: white;
                border-color: {Colors.PRIMARY};
                font-weight: 600;
            }}
            QPushButton:disabled {{ color: {Colors.TEXT_MUTED}; }}
        """)
        return btn

    def _small_icon_btn(self, text, tooltip="") -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 4px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 10px;
                font-weight: 500;
                padding: 4px 8px;
                min-height: 22px;
                max-height: 22px;
            }}
            QPushButton:hover {{ background-color: {Colors.GRAY_200}; }}
            QPushButton:pressed {{ background-color: {Colors.GRAY_400}; }}
            QPushButton:disabled {{ color: {Colors.TEXT_MUTED}; }}
        """)
        return btn

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
        cl = QHBoxLayout(container)
        cl.setContentsMargins(2, 2, 2, 2)
        cl.setSpacing(1)

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
        zones_btn.setCursor(Qt.PointingHandCursor)
        zones_btn.setStyleSheet(_pill_base + """
            QPushButton {
                border-top-left-radius: 5px; border-bottom-left-radius: 5px;
                border-top-right-radius: 0;  border-bottom-right-radius: 0;
            }
        """)

        plotter_btn = QPushButton("Speaker Plotter")
        plotter_btn.setCheckable(True)
        plotter_btn.setChecked(True)   # plotter tab is active when this bar is visible
        plotter_btn.setCursor(Qt.PointingHandCursor)
        plotter_btn.setStyleSheet(_pill_base + """
            QPushButton {
                border-top-left-radius: 0;  border-bottom-left-radius: 0;
                border-top-right-radius: 5px; border-bottom-right-radius: 5px;
            }
        """)

        self._tab_btn_group = QButtonGroup(container)
        self._tab_btn_group.setExclusive(True)
        self._tab_btn_group.addButton(zones_btn, 0)
        self._tab_btn_group.addButton(plotter_btn, 1)

        zones_btn.clicked.connect(lambda: self.tab_changed.emit(0))
        plotter_btn.clicked.connect(lambda: self.tab_changed.emit(1))

        cl.addWidget(zones_btn)
        cl.addWidget(plotter_btn)
        return container

    # ── Menu style constant (matches zones ToolbarManager) ────────────
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

    def set_report_menu(self, menu: QMenu):
        """Attach the report QMenu to the Reports toolbar button."""
        if self._reports_btn and menu:
            self._style_menu(menu)
            self._reports_btn.setMenu(menu)

    def _style_menu(self, menu: QMenu):
        """Apply Fusion style + consistent stylesheet to a QMenu popup."""
        menu.setStyleSheet(self._MENU_STYLE)
        fusion = QStyleFactory.create("Fusion")
        if fusion:
            menu.setStyle(fusion)

    @staticmethod
    def _sep() -> QFrame:
        sep = QFrame()
        sep.setFixedSize(1, 22)
        sep.setStyleSheet(f"background-color: {Colors.BORDER_MEDIUM}; border: none;")
        return sep

    # ── Public API (project identity, matching ToolbarManager) ────────

    def set_project_name(self, name: str):
        if self._project_label:
            self._project_label.setText(name or "No Project")

    def set_modified(self, is_modified: bool):
        if self._modified_dot:
            self._modified_dot.setVisible(is_modified)

    def set_active_tab(self, index: int):
        """Sync the tab pill without emitting a signal."""
        if not self._tab_btn_group:
            return
        btn = self._tab_btn_group.button(index)
        if btn and not btn.isChecked():
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)

    def update_grid_info(self, text: str):
        if self.grid_info_label:
            self.grid_info_label.setText(text)

    # ── Legacy action API (PlotterToolbarActionHandler uses these) ────

    def set_actions_enabled(self, enabled: bool):
        for btn in (self._cov_btn, self._meas_btn):
            if btn:
                btn.setEnabled(enabled)

    def is_show_coverage_checked(self):     return self._cov_btn.isChecked() if self._cov_btn else True
    def is_min_spacing_checked(self):       return False
    def is_show_grid_checked(self):         return False
    def is_grid_snapping_checked(self):     return False
    def is_show_measurements_checked(self): return self._meas_btn.isChecked() if self._meas_btn else False

    def set_show_coverage_checked(self, v):     self._cov_btn and self._cov_btn.setChecked(v)
    def set_min_spacing_checked(self, v):       pass
    def set_show_grid_checked(self, v):         pass
    def set_grid_snapping_checked(self, v):     pass
    def set_show_measurements_checked(self, v): self._meas_btn and self._meas_btn.setChecked(v)

    def is_obstruct_mode(self): return self._obstruct_btn.isChecked() if self._obstruct_btn else False
    def set_obstruct_mode(self, v): self._obstruct_btn and self._obstruct_btn.setChecked(v)

    # Action getters (legacy compatibility)
    def get_show_coverage_action(self):     return self.show_coverage_action
    def get_min_spacing_action(self):       return self.min_spacing_action
    def get_save_layout_action(self):       return self.save_layout_action
    def get_export_report_action(self):     return self.export_report_action
    def get_show_grid_action(self):         return self.show_grid_action
    def get_grid_snapping_action(self):     return self.grid_snapping_action
    def get_show_measurements_action(self): return self.show_measurements_action


class _StubAction:
    """Minimal stand-in for QAction used by PlotterToolbarActionHandler."""

    def __init__(self):
        self._checked = False

    def _set(self, v):
        self._checked = bool(v)

    def isChecked(self):
        return self._checked

    def setChecked(self, v):
        self._checked = bool(v)

    def setEnabled(self, v):
        pass

    def isEnabled(self):
        return True
