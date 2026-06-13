"""Auto Layout Dialog — pick profile, grid type, overlap, see live preview, confirm placement."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QButtonGroup, QFrame, QWidget
)
from PySide6.QtCore import Qt, Signal

from ui.styles.base_styles import Colors, Typography, BorderRadius


class AutoLayoutDialog(QDialog):
    """Dialog for configuring and confirming auto speaker layout."""

    layout_confirmed = Signal(object, str, float)  # (profile, grid_type, overlap_pct)

    # Overlap options: (label, pct_value)
    _OVERLAP_OPTIONS = [
        ("Wide", -25.0),
        ("Minimal", 0.0),
        ("Standard", 15.0),
        ("Dense", 25.0),
        ("Max", 50.0),
    ]

    def __init__(self, zone, profile_manager, auto_layout_manager, current_profile=None, parent=None):
        super().__init__(parent)
        self.zone = zone
        self.profile_manager = profile_manager
        self.auto_layout_manager = auto_layout_manager
        self.current_profile = current_profile

        self._selected_profile = None
        self._grid_type = 'rect'
        self._overlap_pct = 15.0
        self._layout_method = 'bbox'
        self._result = None

        self.setWindowTitle("Auto Layout")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._build_ui()
        self._populate_profiles()
        self._update_preview()

    # ── UI Construction ───────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
        """)

        # ── Zone info row ─────────────────────────────────────────────
        zone_name = self.zone.get('name', 'Zone') if self.zone else 'Zone'
        zone_area_str = ""
        if self.zone and 'points' in self.zone and self.zone['points']:
            pts = self.zone['points']
            # Shoelace formula for pixel area then approximate sq ft
            # Just show name; area in ft comes from zone data if available
            length = self.zone.get('length')
            width = self.zone.get('width')
            if length and width:
                zone_area_str = f"  ·  {length * width:.0f} ft²"

        zone_label = QLabel(f"Zone: {zone_name}{zone_area_str}")
        zone_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_BASE};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        root.addWidget(zone_label)

        # ── Profile section label ─────────────────────────────────────
        root.addWidget(self._section_label("SPEAKER PROFILE"))

        # ── Profile list ──────────────────────────────────────────────
        self.profile_list = QListWidget()
        self.profile_list.setMinimumHeight(140)
        self.profile_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.BG_PRIMARY};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.BASE};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {Colors.GRAY_100};
            }}
        """)
        self.profile_list.itemSelectionChanged.connect(self._on_profile_changed)
        root.addWidget(self.profile_list)

        # ── Grid pattern section ──────────────────────────────────────
        root.addWidget(self._section_label("GRID PATTERN"))
        grid_row = QHBoxLayout()
        grid_row.setSpacing(4)
        grid_row.setContentsMargins(0, 0, 0, 0)

        self._grid_btn_group = QButtonGroup(self)
        self._grid_btn_group.setExclusive(True)

        self._rect_btn = self._toggle_btn("\u229e Rect", checked=True)
        self._hex_btn = self._toggle_btn("\u2b21 Hex", checked=False)

        self._grid_btn_group.addButton(self._rect_btn, 0)
        self._grid_btn_group.addButton(self._hex_btn, 1)

        self._rect_btn.clicked.connect(lambda: self._on_grid_changed('rect'))
        self._hex_btn.clicked.connect(lambda: self._on_grid_changed('hex'))

        grid_row.addWidget(self._rect_btn)
        grid_row.addWidget(self._hex_btn)
        grid_row.addStretch()
        root.addLayout(grid_row)

        # ── Coverage overlap section ──────────────────────────────────
        root.addWidget(self._section_label("COVERAGE OVERLAP"))
        overlap_row = QHBoxLayout()
        overlap_row.setSpacing(4)
        overlap_row.setContentsMargins(0, 0, 0, 0)

        self._overlap_btn_group = QButtonGroup(self)
        self._overlap_btn_group.setExclusive(True)

        self._overlap_btns = []
        for idx, (label, pct) in enumerate(self._OVERLAP_OPTIONS):
            btn = self._toggle_btn(label, checked=(pct == 15.0))
            self._overlap_btn_group.addButton(btn, idx)
            btn.clicked.connect(lambda _checked, p=pct: self._on_overlap_changed(p))
            overlap_row.addWidget(btn)

        overlap_row.addStretch()
        root.addLayout(overlap_row)

        # ── Layout method section ─────────────────────────────────────
        root.addWidget(self._section_label("LAYOUT METHOD"))
        method_row = QHBoxLayout()
        method_row.setSpacing(4)
        method_row.setContentsMargins(0, 0, 0, 0)

        self._method_btn_group = QButtonGroup(self)
        self._method_btn_group.setExclusive(True)

        self._bbox_btn = self._toggle_btn("Standard", checked=True)
        self._centroid_btn = self._toggle_btn("Shape-Aware", checked=False)

        self._method_btn_group.addButton(self._bbox_btn, 0)
        self._method_btn_group.addButton(self._centroid_btn, 1)

        self._bbox_btn.clicked.connect(lambda: self._on_method_changed('bbox'))
        self._centroid_btn.clicked.connect(lambda: self._on_method_changed('centroid'))

        method_row.addWidget(self._bbox_btn)
        method_row.addWidget(self._centroid_btn)
        method_row.addStretch()
        root.addLayout(method_row)

        # ── Preview strip ─────────────────────────────────────────────
        top_sep = QFrame()
        top_sep.setFrameShape(QFrame.HLine)
        top_sep.setFrameShadow(QFrame.Plain)
        top_sep.setFixedHeight(1)
        top_sep.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
        root.addWidget(top_sep)

        self.preview_label = QLabel("Select a profile to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                background: transparent;
                border: none;
                padding: 6px 0;
            }}
        """)
        root.addWidget(self.preview_label)

        bot_sep = QFrame()
        bot_sep.setFrameShape(QFrame.HLine)
        bot_sep.setFrameShadow(QFrame.Plain)
        bot_sep.setFixedHeight(1)
        bot_sep.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
        root.addWidget(bot_sep)

        # ── Button row ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._outline_btn_style())
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.place_btn = QPushButton("Place Speakers")
        self.place_btn.setEnabled(False)
        self.place_btn.setStyleSheet(self._primary_btn_style())
        self.place_btn.clicked.connect(self._on_place)
        btn_row.addWidget(self.place_btn)

        root.addLayout(btn_row)

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_XS};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
                letter-spacing: 0.5px;
            }}
        """)
        return lbl

    def _toggle_btn(self, text, checked=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.BASE};
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                padding: 5px 12px;
                min-height: 26px;
            }}
            QPushButton:hover:!pressed:!checked {{
                background-color: {Colors.GRAY_100};
            }}
            QPushButton:checked {{
                background-color: {Colors.PRIMARY};
                color: white;
                border-color: {Colors.PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            }}
            QPushButton:pressed {{
                background-color: {Colors.GRAY_200};
            }}
        """)
        return btn

    @staticmethod
    def _outline_btn_style():
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.MD};
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                padding: 6px 16px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {Colors.GRAY_100};
            }}
        """

    @staticmethod
    def _primary_btn_style():
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                border: none;
                border-radius: {BorderRadius.MD};
                color: white;
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                padding: 6px 16px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_ACTIVE};
            }}
            QPushButton:disabled {{
                background-color: {Colors.GRAY_400};
                color: {Colors.TEXT_MUTED};
            }}
        """

    # ── Data Population ───────────────────────────────────────────────

    def _populate_profiles(self):
        """Load profiles from profile_manager and populate the list."""
        profiles = self.profile_manager.list_profiles()
        preselect_index = None

        for idx, (key, profile) in enumerate(profiles):
            label = f"{profile.manufacturer} — {profile.name}  ·  {profile.dispersion_angle_h}° {profile.model_type}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, (key, profile))
            self.profile_list.addItem(item)

            # Pre-select the currently active profile
            if self.current_profile is not None and profile is self.current_profile:
                preselect_index = idx
            elif self.current_profile is not None and preselect_index is None:
                # Fall back: match by key
                if key == f"{self.current_profile.manufacturer}_{self.current_profile.name}":
                    preselect_index = idx

        if preselect_index is not None:
            self.profile_list.setCurrentRow(preselect_index)

    # ── Event Handlers ────────────────────────────────────────────────

    def _on_profile_changed(self):
        items = self.profile_list.selectedItems()
        if items:
            _key, profile = items[0].data(Qt.UserRole)
            self._selected_profile = profile
        else:
            self._selected_profile = None
        self._update_preview()

    def _on_grid_changed(self, grid_type):
        self._grid_type = grid_type
        self._update_preview()

    def _on_overlap_changed(self, pct):
        self._overlap_pct = pct
        self._update_preview()

    def _on_method_changed(self, method):
        self._layout_method = method
        self._update_preview()

    def _on_place(self):
        if self._selected_profile is None:
            return
        self._result = (self._selected_profile, self._grid_type, self._overlap_pct, self._layout_method)
        self.layout_confirmed.emit(self._selected_profile, self._grid_type, self._overlap_pct)
        self.accept()

    # ── Preview ───────────────────────────────────────────────────────

    def _update_preview(self):
        """Recalculate preview and update the label."""
        if self._selected_profile is None or not self.zone:
            self.preview_label.setText("Select a profile to preview")
            self.place_btn.setEnabled(False)
            return

        try:
            count, spacing_ft = self.auto_layout_manager.preview_layout(
                self.zone,
                self._selected_profile,
                self._grid_type,
                self._overlap_pct,
                layout_method=self._layout_method,
            )
        except Exception:
            self.preview_label.setText("Could not calculate layout")
            self.place_btn.setEnabled(False)
            return

        if count == 0 or spacing_ft <= 0:
            self.preview_label.setText("Could not calculate a valid layout for this configuration")
            self.place_btn.setEnabled(False)
            return

        # Build styled preview text (bold numbers, muted labels)
        self.preview_label.setText(
            f"<span style='color:{Colors.TEXT_SECONDARY}'>Spacing: </span>"
            f"<b style='color:{Colors.TEXT_PRIMARY}'>{spacing_ft:.1f} ft</b>"
            f"<span style='color:{Colors.TEXT_SECONDARY}'>  ·  Speakers: </span>"
            f"<b style='color:{Colors.TEXT_PRIMARY}'>{count}</b>"
        )
        self.preview_label.setTextFormat(Qt.RichText)
        self.place_btn.setEnabled(True)

    # ── Public API ────────────────────────────────────────────────────

    def get_result(self):
        """Return (profile, grid_type, overlap_pct, layout_method) or None if cancelled."""
        return self._result
