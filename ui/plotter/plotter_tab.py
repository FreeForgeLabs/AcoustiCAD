import logging
import os

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
                             QApplication, QFrame, QStackedWidget,
                             QComboBox, QPushButton, QButtonGroup, QListWidget,
                             QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeySequence, QShortcut

from ui.plotter.speaker_view import SpeakerView
from ui.plotter.components.speaker_properties_panel import SpeakerPropertiesPanel
from ui.plotter.managers.zone_selection_manager import ZoneSelectionManager
from ui.plotter.managers.speaker_profile_ui_manager import SpeakerProfileUIManager
from ui.plotter.components.obstruction_properties_panel import ObstructionPropertiesPanel
from ui.plotter.components.toolbar_widget import ToolbarWidget
from ui.plotter.interactions.auto_layout_manager import AutoLayoutManager

from core.speaker_profiles import SpeakerProfileManager

# Import shared styling system
from ui.styles.base_styles import Colors, Typography, Spacing, BorderRadius
from ui.dialogs.alert_dialog import AlertDialog
from ui.dialogs.confirm_dialog import ConfirmDialog

# Right panel page indices
PANEL_EMPTY = 0
PANEL_ZONE = 1
PANEL_SPEAKER_SINGLE = 2
PANEL_SPEAKER_MULTI = 3
PANEL_OBSTRUCTION = 4


class PlotterToolbarActionHandler:
    """Handles toolbar actions for plotter tab"""

    def __init__(self, plotter_tab):
        self.plotter_tab = plotter_tab
        self.logger = logging.getLogger(__name__)

    def handle_show_coverage_toggle(self, checked):
        """Handle show coverage toggle"""
        if self.plotter_tab.speaker_view:
            self.plotter_tab.speaker_view.set_show_coverage(checked)
            if checked:
                QTimer.singleShot(100, self.plotter_tab.speaker_view.force_coverage_display)

    def handle_min_spacing_toggle(self, checked):
        """Handle minimum spacing toggle"""
        if checked:
            # Use a default spacing value (36 inches) since obstruction_control_panel is removed
            spacing_value = 36.0
            self.plotter_tab.speaker_view.set_min_speaker_distance(spacing_value)
        else:
            self.plotter_tab.speaker_view.set_min_speaker_distance(None)

    def handle_show_grid_toggle(self, checked):
        """Handle show grid toggle"""
        if self.plotter_tab.speaker_view:
            self.plotter_tab.speaker_view.set_acoustic_grid_visible(checked)

            # Update grid info label when grid is shown
            if checked:
                self._update_grid_info_label()

    def handle_grid_snapping_toggle(self, checked):
        """Handle grid snapping toggle"""
        if self.plotter_tab.speaker_view:
            self.plotter_tab.speaker_view.set_grid_snapping_enabled(checked)
            self.logger.info(f"Grid snapping {'enabled' if checked else 'disabled'}")

    def handle_show_measurements_toggle(self, checked):
        """Handle show measurements toggle"""
        self.logger.info(f"Measurements toggle clicked: {checked}")
        if self.plotter_tab.speaker_view:
            self.plotter_tab.speaker_view.set_measurements_visible(checked)
            self.logger.info(f"Measurements {'shown' if checked else 'hidden'}")
        else:
            self.logger.warning("No speaker view available for measurements toggle")

    def _update_grid_info_label(self):
        """Update the grid info label in toolbar"""
        if not self.plotter_tab.speaker_view:
            self.logger.warning("Cannot update grid info: No speaker view")
            return

        try:
            # Get grid info
            grid_info = self.plotter_tab.speaker_view.get_grid_info()
            self.logger.debug(f"Grid info: {grid_info}")

            # Check if grid is configured
            if grid_info.get('has_zone') and grid_info.get('has_profile'):
                grid_spacing = self.plotter_tab.speaker_view.get_grid_spacing_formatted()
                self.plotter_tab.toolbar.update_grid_info(f"Grid: {grid_spacing}")
                self.logger.info(f"Grid configured: {grid_spacing}")
            else:
                self.plotter_tab.toolbar.update_grid_info("Grid: --")
                missing = []
                if not grid_info.get('has_zone'):
                    missing.append("zone")
                if not grid_info.get('has_profile'):
                    missing.append("speaker profile")
                self.logger.info(f"Grid not configured - missing: {', '.join(missing)}")

        except Exception as e:
            self.logger.error(f"Error updating grid info label: {e}", exc_info=True)
            self.plotter_tab.toolbar.update_grid_info("Grid: Error")


class PlotterTab(QWidget):
    """Tab for planning and visualizing speaker placement with clean shared styling matching zones tab"""

    # Signals
    speaker_layout_changed = Signal()
    obstruction_layout_changed = Signal()

    def __init__(self, storage, project_manager=None, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.logger = logging.getLogger(__name__)

        # Use provided project manager or create a new one
        if project_manager:
            self.project_manager = project_manager
        else:
            from core.project_manager import ProjectManager
            self.project_manager = ProjectManager(storage)

        # Initialize speaker profile data manager
        self.profile_data_manager = SpeakerProfileManager(self.storage.get_speaker_profiles_dir())
        self.current_project_id = None
        self._current_project_data = None
        self._backgrounds_loaded = False

        # Initialize action handler
        self.action_handler = PlotterToolbarActionHandler(self)

        # Initialize UI
        self.init_ui()
        self._init_managers()
        self._connect_signals()
        self._setup_shortcuts()
        self._apply_shared_styling()

    def init_ui(self):
        """Initialize the UI components with clean shared styling matching zones tab"""
        # Main layout with consistent background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create toolbar using existing ToolbarWidget with shared styling
        self.toolbar = ToolbarWidget(self)
        main_layout.addWidget(self.toolbar)

        # Create horizontal layout for content with consistent spacing
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        # Left panel: zones and recommendations
        left_panel = self._create_left_panel()
        left_panel.setMinimumWidth(200)
        left_panel.setMaximumWidth(230)
        content_layout.addWidget(left_panel)

        # Center: speaker view with shared styling
        self.speaker_view = SpeakerView(self.project_manager.get_scale_manager(), self)
        self.speaker_view.speaker_selected.connect(self.on_speaker_selected)
        self.speaker_view.obstruction_selected.connect(self.on_obstruction_selected)

        # Apply shared styling to speaker view (matching zones tab)
        self.speaker_view.setStyleSheet(f"""
            SpeakerView {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                margin: {Spacing.SM};
            }}
        """)

        content_layout.addWidget(self.speaker_view, 1)

        # Right panel: context-sensitive smart panel
        right_panel = self._create_right_panel()
        right_panel.setMinimumWidth(260)
        right_panel.setMaximumWidth(290)
        content_layout.addWidget(right_panel)

        main_layout.addLayout(content_layout)

        # Status bar — compact, matching zones tab exactly
        self.status_label = QLabel("No project selected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.GRAY_100};
                border-top: 1px solid {Colors.BORDER_LIGHT};
                padding: 2px {Spacing.MD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_XS};
                color: {Colors.TEXT_SECONDARY};
                min-height: 18px;
                max-height: 18px;
            }}
        """)
        main_layout.addWidget(self.status_label)

        # Create ReportMenuHelper and attach its menu to the Reports toolbar button
        from utils.report_menu_helper import ReportMenuHelper
        self.report_helper = ReportMenuHelper(self, self, self.project_manager,
                                              speaker_view=self.speaker_view)
        report_menu = self.report_helper.create_report_menu()
        self.toolbar.set_report_menu(report_menu)

    def _create_left_panel(self):
        """Create clean left panel matching zones tab styling exactly"""
        panel = QWidget()
        panel.setObjectName("leftPanel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setStyleSheet(f"""
            QWidget#leftPanel {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                margin: {Spacing.SM};
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        # Zone tree filling the space
        self.zone_tree = QTreeWidget()
        self.zone_tree.setHeaderLabels(["Name", "Area (ft²)"])
        self.zone_tree.setColumnWidth(0, 150)

        # Apply shared tree styling
        self.zone_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QTreeWidget::item {{
                padding: {Spacing.BASE};
                border-bottom: 1px solid {Colors.GRAY_100};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Colors.GRAY_100};
                padding: {Spacing.BASE};
                border: none;
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_XS};
                color: {Colors.TEXT_SECONDARY};
            }}
        """)
        layout.addWidget(self.zone_tree)

        return panel

    # ==================== RIGHT PANEL (stacked) ====================

    def _create_right_panel(self):
        panel = QWidget()
        panel.setObjectName("rightPanel")
        panel.setStyleSheet(f"""
            QWidget#rightPanel {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                margin: {Spacing.SM};
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        self._right_stack = QStackedWidget()
        self._right_stack.addWidget(self._make_panel_empty())           # 0
        self._right_stack.addWidget(self._make_panel_zone())            # 1
        self._right_stack.addWidget(self._make_panel_speaker_single())  # 2
        self._right_stack.addWidget(self._make_panel_speaker_multi())   # 3
        self._right_stack.addWidget(self._make_panel_obstruction())     # 4
        layout.addWidget(self._right_stack)

        return panel

    def _make_panel_empty(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("Select a zone\nto get started")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        v.addStretch()
        v.addWidget(lbl)
        v.addStretch()
        return w

    def _make_panel_zone(self):
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 4, 0, 0)
        v.setSpacing(12)

        def section_label(text):
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
                    padding-bottom: 4px;
                }}
            """)
            return lbl

        def hsep():
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFixedHeight(1)
            line.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
            return line

        # ── Zone identity header ──────────────────────────────────────────
        self._panel_zone_name_lbl = QLabel("—")
        self._panel_zone_name_lbl.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_LG};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
                padding-bottom: 2px;
            }}
        """)
        v.addWidget(self._panel_zone_name_lbl)

        # Ceiling height (read-only info) + Pendant height (editable default)
        zone_info_row = QHBoxLayout()
        zone_info_row.setSpacing(8)

        ceiling_col = QVBoxLayout()
        ceiling_col.setSpacing(3)
        ceiling_cap = QLabel("CEILING")
        ceiling_cap.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Typography.FONT_SIZE_XS}; font-family: {Typography.FONT_FAMILY_PRIMARY}; font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; background: transparent; border: none;")
        self._panel_zone_ceiling_lbl = QLabel("— ft")
        self._panel_zone_ceiling_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: {Typography.FONT_SIZE_SM}; font-family: {Typography.FONT_FAMILY_PRIMARY}; background: transparent; border: none;")
        ceiling_col.addWidget(ceiling_cap)
        ceiling_col.addWidget(self._panel_zone_ceiling_lbl)

        pendant_col = QVBoxLayout()
        pendant_col.setSpacing(3)
        pendant_cap = QLabel("PENDANT HEIGHT")
        pendant_cap.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Typography.FONT_SIZE_XS}; font-family: {Typography.FONT_FAMILY_PRIMARY}; font-weight: {Typography.FONT_WEIGHT_SEMIBOLD}; background: transparent; border: none;")
        self._panel_pendant_spin = QDoubleSpinBox()
        self._panel_pendant_spin.setRange(4.0, 19.0)
        self._panel_pendant_spin.setSingleStep(0.5)
        self._panel_pendant_spin.setValue(9.0)
        self._panel_pendant_spin.setSuffix(" ft")
        self._panel_pendant_spin.setToolTip("Default hanging height for pendant speakers in this zone.\nIndividual speakers can be adjusted when selected.")
        self._panel_pendant_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.SM};
                padding: 4px 6px;
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                background: {Colors.WHITE};
                max-height: 26px;
            }}
            QDoubleSpinBox:focus {{ border-color: {Colors.PRIMARY}; }}
        """)
        self._panel_pendant_spin.valueChanged.connect(self._on_panel_pendant_changed)
        pendant_col.addWidget(pendant_cap)
        pendant_col.addWidget(self._panel_pendant_spin)

        zone_info_row.addLayout(ceiling_col)
        zone_info_row.addLayout(pendant_col)
        zone_info_row.addStretch()
        v.addLayout(zone_info_row)

        v.addWidget(hsep())

        # AUTO LAYOUT section
        v.addWidget(section_label("AUTO LAYOUT"))

        # Profile dropdown
        profile_lbl = QLabel("Profile")
        profile_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: {Typography.FONT_SIZE_SM}; font-family: {Typography.FONT_FAMILY_PRIMARY}; background: transparent; border: none;")
        v.addWidget(profile_lbl)

        self._panel_profile_combo = QComboBox()
        self._panel_profile_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                padding: 6px 10px;
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                background: {Colors.WHITE};
            }}
            QComboBox:focus {{ border-color: {Colors.PRIMARY}; }}
            QComboBox::drop-down {{ border: none; padding-right: 8px; }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                selection-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER_MEDIUM};
            }}
        """)
        self._panel_profile_combo.currentIndexChanged.connect(self._on_panel_profile_changed)
        v.addWidget(self._panel_profile_combo)

        # Profile sub-label (shows type + angle)
        self._panel_profile_sublabel = QLabel("")
        self._panel_profile_sublabel.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Typography.FONT_SIZE_XS}; font-family: {Typography.FONT_FAMILY_PRIMARY}; background: transparent; border: none;")
        v.addWidget(self._panel_profile_sublabel)

        # Manage profiles row (small buttons)
        mgmt_row = QHBoxLayout()
        mgmt_row.setSpacing(4)
        self._panel_new_profile_btn = QPushButton("+ New")
        self._panel_edit_profile_btn = QPushButton("Edit")
        for btn in (self._panel_new_profile_btn, self._panel_edit_profile_btn):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {Colors.BORDER_LIGHT};
                    border-radius: {BorderRadius.SM};
                    padding: 3px 8px;
                    font-size: {Typography.FONT_SIZE_XS};
                    font-family: {Typography.FONT_FAMILY_PRIMARY};
                    color: {Colors.TEXT_SECONDARY};
                }}
                QPushButton:hover {{ background: {Colors.GRAY_50}; color: {Colors.TEXT_PRIMARY}; }}
            """)
        self._panel_new_profile_btn.clicked.connect(self._on_panel_new_profile)
        self._panel_edit_profile_btn.clicked.connect(self._on_panel_edit_profile)
        mgmt_row.addWidget(self._panel_new_profile_btn)
        mgmt_row.addWidget(self._panel_edit_profile_btn)
        mgmt_row.addStretch()
        v.addLayout(mgmt_row)

        v.addWidget(hsep())

        # Grid type toggle
        v.addWidget(section_label("GRID PATTERN"))
        grid_row = QHBoxLayout()
        grid_row.setSpacing(4)
        self._panel_rect_btn = QPushButton("⊞ Rect")
        self._panel_hex_btn  = QPushButton("⬡ Hex")
        self._panel_grid_group = QButtonGroup(w)
        self._panel_grid_group.setExclusive(True)
        for i, (btn, gtype) in enumerate([(self._panel_rect_btn, 'rect'), (self._panel_hex_btn, 'hex')]):
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setProperty("gridType", gtype)
            btn.clicked.connect(self._on_panel_grid_changed)
            self._panel_grid_group.addButton(btn, i)
            grid_row.addWidget(btn)
        grid_row.addStretch()
        v.addLayout(grid_row)

        v.addWidget(hsep())

        # Overlap buttons
        v.addWidget(section_label("COVERAGE OVERLAP"))
        overlap_row = QHBoxLayout()
        overlap_row.setSpacing(4)
        self._panel_overlap_btns = []
        for label, pct in [("Wide", -25), ("Minimal", 0), ("Standard", 15), ("Dense", 25), ("Max", 50)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(pct == 15)  # default Standard
            btn.setProperty("overlapPct", pct)
            btn.clicked.connect(self._on_panel_overlap_changed)
            self._panel_overlap_btns.append(btn)
            overlap_row.addWidget(btn)
        v.addLayout(overlap_row)

        v.addWidget(hsep())

        # Layout method toggle
        v.addWidget(section_label("LAYOUT METHOD"))
        method_row = QHBoxLayout()
        method_row.setSpacing(4)
        self._panel_layout_bbox_btn = QPushButton("Standard")
        self._panel_layout_centroid_btn = QPushButton("Shape-Aware")
        self._panel_layout_method_group = QButtonGroup(w)
        self._panel_layout_method_group.setExclusive(True)
        for i, (btn, method) in enumerate([
            (self._panel_layout_bbox_btn, 'bbox'),
            (self._panel_layout_centroid_btn, 'centroid'),
        ]):
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setProperty("layoutMethod", method)
            btn.clicked.connect(self._on_panel_layout_method_changed)
            self._panel_layout_method_group.addButton(btn, i)
            method_row.addWidget(btn)
        method_row.addStretch()
        v.addLayout(method_row)

        # Apply toggle button styling to grid + overlap + method buttons
        toggle_style = f"""
            QPushButton {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.SM};
                padding: 5px 8px;
                font-size: {Typography.FONT_SIZE_XS};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                color: {Colors.TEXT_SECONDARY};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
            }}
            QPushButton:checked {{
                background: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
                color: {Colors.WHITE};
            }}
            QPushButton:hover:!checked {{ background: {Colors.GRAY_50}; }}
        """
        for btn in ([self._panel_rect_btn, self._panel_hex_btn]
                    + self._panel_overlap_btns
                    + [self._panel_layout_bbox_btn, self._panel_layout_centroid_btn]):
            btn.setStyleSheet(toggle_style)

        v.addWidget(hsep())

        # Preview strip
        self._panel_preview_lbl = QLabel("Select a profile")
        self._panel_preview_lbl.setAlignment(Qt.AlignCenter)
        self._panel_preview_lbl.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: {Colors.GRAY_50};
                border: none;
                border-radius: {BorderRadius.SM};
                padding: 8px;
            }}
        """)
        v.addWidget(self._panel_preview_lbl)

        # Generate button
        self._panel_generate_btn = QPushButton("⚡ Generate Layout")
        self._panel_generate_btn.setEnabled(False)
        self._panel_generate_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.PRIMARY};
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.MD};
                padding: 9px 12px;
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QPushButton:hover {{ background: {Colors.PRIMARY_HOVER}; }}
            QPushButton:disabled {{ background: {Colors.GRAY_400}; color: {Colors.TEXT_MUTED}; }}
        """)
        self._panel_generate_btn.clicked.connect(self._on_panel_generate_layout)
        v.addWidget(self._panel_generate_btn)

        v.addWidget(hsep())

        # Manual place button
        v.addWidget(section_label("MANUAL PLACEMENT"))
        self._panel_place_btn = QPushButton("• Place Speaker")
        self._panel_place_btn.setCheckable(True)
        self._panel_place_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                padding: 8px 12px;
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QPushButton:checked {{
                background: {Colors.PRIMARY_LIGHT};
                border-color: {Colors.PRIMARY};
                color: {Colors.PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
            }}
            QPushButton:hover:!checked {{ background: {Colors.GRAY_50}; }}
        """)
        self._panel_place_btn.clicked.connect(self._on_panel_place_toggled)
        v.addWidget(self._panel_place_btn)

        v.addStretch()
        return w

    def _make_panel_speaker_single(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self.properties_panel = SpeakerPropertiesPanel()
        self.properties_panel.property_changed.connect(self.on_speaker_property_changed)
        self._apply_properties_panel_styling(self.properties_panel)
        v.addWidget(self.properties_panel)
        return w

    def _make_panel_speaker_multi(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)
        v.addStretch()

        self._multi_count_lbl = QLabel("N speakers selected")
        self._multi_count_lbl.setAlignment(Qt.AlignCenter)
        self._multi_count_lbl.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        v.addWidget(self._multi_count_lbl)

        self._multi_delete_btn = QPushButton("🗑 Delete Selected")
        self._multi_delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.ERROR};
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.MD};
                padding: 9px 12px;
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QPushButton:hover {{ background: {Colors.ERROR_HOVER}; }}
        """)
        self._multi_delete_btn.clicked.connect(self.speaker_view.delete_selected_speakers)
        v.addWidget(self._multi_delete_btn)
        v.addStretch()
        return w

    def _make_panel_obstruction(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        self.obstruction_properties_panel = ObstructionPropertiesPanel()
        self.obstruction_properties_panel.property_changed.connect(self.on_obstruction_property_changed)
        self._apply_properties_panel_styling(self.obstruction_properties_panel)
        v.addWidget(self.obstruction_properties_panel)
        return w

    def _apply_properties_panel_styling(self, panel):
        """Apply clean styling to properties panels"""
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
            QDoubleSpinBox, QTextEdit {{
                padding: 8px 12px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QDoubleSpinBox:focus, QTextEdit:focus {{
                border: 2px solid {Colors.PRIMARY};
                background-color: {Colors.GRAY_50};
            }}
            QPushButton {{
                background-color: {Colors.ERROR};
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.MD};
                padding: 8px 16px;
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {Colors.ERROR_HOVER};
            }}
        """)

    def _init_managers(self):
        """Initialize managers after UI creation"""
        self.zone_selection_manager = ZoneSelectionManager(self.zone_tree, self)

        # Hidden profile list widget — SpeakerProfileUIManager requires one but it's never shown
        self._hidden_profile_list = QListWidget()
        # Create dummy buttons to satisfy SpeakerProfileUIManager's interface
        _dummy_create_btn = QPushButton()
        _dummy_edit_btn = QPushButton()
        _dummy_place_btn = QPushButton()

        self.speaker_profile_ui_manager = SpeakerProfileUIManager(
            self._hidden_profile_list,
            self.profile_data_manager,
            _dummy_create_btn,
            _dummy_edit_btn,
            _dummy_place_btn,
            self
        )

        # Auto-layout manager
        self._auto_layout_manager = AutoLayoutManager(self.speaker_view.acoustic_grid_manager)
        self.speaker_view.set_auto_layout_manager(self._auto_layout_manager)

    def _setup_shortcuts(self):
        """Register keyboard shortcuts using platform system defaults."""
        QShortcut(QKeySequence.Undo, self).activated.connect(self._on_undo)
        QShortcut(QKeySequence.Redo, self).activated.connect(self._on_redo)
        QShortcut(QKeySequence.Save, self).activated.connect(self.on_save_layout)

    def _on_undo(self):
        """Undo the last speaker operation."""
        dm = self.speaker_view.speaker_data_manager
        if dm.undo():
            # Selection was cleared by the speakers_cleared signal; update right panel
            zone = self.speaker_view.current_zone
            if zone:
                self._set_right_panel_state(PANEL_ZONE)
        else:
            QApplication.beep()   # nothing to undo — audible feedback

    def _on_redo(self):
        """Redo the last undone speaker operation."""
        dm = self.speaker_view.speaker_data_manager
        if dm.redo():
            zone = self.speaker_view.current_zone
            if zone:
                self._set_right_panel_state(PANEL_ZONE)
        else:
            QApplication.beep()

    def _connect_signals(self):
        """Connect all signals"""
        # Toolbar signals through action handler
        self.toolbar.show_coverage_toggled.connect(self.action_handler.handle_show_coverage_toggle)
        self.toolbar.min_spacing_toggled.connect(self.action_handler.handle_min_spacing_toggle)
        self.toolbar.save_layout_requested.connect(self.on_save_layout)

        # Grid and measurement toolbar signals
        self.toolbar.show_grid_toggled.connect(self.action_handler.handle_show_grid_toggle)
        self.toolbar.grid_snapping_toggled.connect(self.action_handler.handle_grid_snapping_toggle)
        self.toolbar.show_measurements_toggled.connect(self.action_handler.handle_show_measurements_toggle)

        # Obstruct mode
        self.toolbar.obstruct_mode_toggled.connect(self._on_obstruct_mode_toggled)

        # Zone selection signals
        self.zone_selection_manager.zone_selected.connect(self._on_zone_selected)
        self.zone_selection_manager.zone_selection_cleared.connect(self._on_zone_selection_cleared)

        # Layout / viz toolbar signals
        self.toolbar.grid_type_changed.connect(self.speaker_view.set_grid_type)
        self.toolbar.viz_mode_changed.connect(self.speaker_view.set_viz_mode)
        self.toolbar.auto_layout_requested.connect(self._on_auto_layout_requested)

        # Multi-select and clear signals
        self.speaker_view.speakers_selection_changed.connect(self._on_speakers_selection_changed)
        self.toolbar.clear_speakers_requested.connect(self._on_clear_speakers_requested)

        # Obstruction selection → panel state
        self.speaker_view.obstruction_selected.connect(self._on_obstruction_selected_panel)

        # Placement mode changes → reset place button
        self.speaker_view.placement_manager.placement_mode_changed.connect(self._on_placement_mode_changed_panel)

        # Profile library changes → repopulate combo
        self.speaker_profile_ui_manager.profile_library_changed.connect(self._on_profile_library_changed)

    def _apply_shared_styling(self):
        """Apply shared styling system matching zones tab"""
        self.setStyleSheet(f"""
            PlotterTab {{
                background-color: {Colors.BG_SECONDARY};
                border: none;
            }}
        """)

    # ==================== SIGNAL HANDLERS ====================

    def _on_zone_selected(self, zone):
        """Handle zone selection"""
        try:
            # Load background and layouts on first zone selection (deferred from project load)
            if not self._backgrounds_loaded and self._current_project_data:
                self._load_project_backgrounds_and_layouts(self._current_project_data)
                self._backgrounds_loaded = True

            self.speaker_view.set_current_zone(zone)
            self.speaker_view.set_show_coverage(True)
            self.speaker_view.force_coverage_display()

            # Update grid info when zone changes
            if hasattr(self, 'action_handler'):
                self.action_handler._update_grid_info_label()

            # Switch to zone panel and populate
            self._set_right_panel_state(PANEL_ZONE)
            self._populate_zone_panel_header(zone)
            self._populate_profile_combo()
            self._update_zone_panel_preview()

            self.update()
            QApplication.processEvents()
        except Exception as e:
            self.logger.error(f"Error handling zone selection: {e}", exc_info=True)

    def _on_zone_selection_cleared(self):
        """Handle zone selection cleared"""
        self.speaker_view.clear_zone()
        self._set_right_panel_state(PANEL_EMPTY)

    def _on_profile_library_changed(self):
        """Handle profile library changes — repopulate combo"""
        self.logger.debug("Profile library changed")
        self._populate_profile_combo()

    def _on_obstruct_mode_toggled(self, enabled):
        """Toggle obstruction drawing mode on the speaker view"""
        if not enabled:
            # Deactivate obstruction mode
            if hasattr(self.speaker_view, 'obstruction_mode'):
                self.speaker_view.obstruction_mode = False
            return

        # Always reset the toolbar button — dialog decides whether to proceed
        self.toolbar.set_obstruct_mode(False)

        # Open selection dialog
        from ui.plotter.dialogs.obstruction_dialog import ObstructionDialog
        dialog = ObstructionDialog(self)
        if dialog.exec() != dialog.Accepted:
            return

        result = dialog.get_result()
        if not result:
            return

        obs_type = result["type"]
        radius_in = result["radius_inches"]

        # Activate placement mode with chosen type + size
        self.speaker_view.placement_manager.start_obstruction_placement(obs_type, radius_override=radius_in)
        # Keep the button visually active while placing
        self.toolbar.set_obstruct_mode(True)

    # ==================== AUTO LAYOUT ====================

    def _get_selected_profile(self):
        """Return the currently selected speaker profile from the panel combo."""
        return self._get_selected_profile_from_panel()

    def _on_auto_layout_requested(self):
        """Handle auto layout button click — opens the Auto Layout dialog."""
        from ui.plotter.dialogs.auto_layout_dialog import AutoLayoutDialog
        zone = self.speaker_view.current_zone
        if not zone:
            return
        dialog = AutoLayoutDialog(
            zone=zone,
            profile_manager=self.profile_data_manager,
            auto_layout_manager=self._auto_layout_manager,
            current_profile=self._get_selected_profile(),
            parent=self,
        )
        if dialog.exec() == AutoLayoutDialog.Accepted:
            result = dialog.get_result()
            if result:
                profile, grid_type, overlap_pct, layout_method = result
                self.speaker_view.set_grid_type(grid_type)
                self.speaker_view.run_auto_layout(
                    zone, profile, overlap_pct=overlap_pct, layout_method=layout_method)

    def _on_speakers_selection_changed(self, speaker_ids):
        """Handle speaker multi-selection changes."""
        count = len(speaker_ids)
        if count == 0:
            self.properties_panel.clear()
            # Return to zone panel if zone is active
            if self.speaker_view.current_zone:
                self._set_right_panel_state(PANEL_ZONE)
            else:
                self._set_right_panel_state(PANEL_EMPTY)
        elif count == 1:
            speaker_data = self.speaker_view.speaker_data_manager.get_speaker(speaker_ids[0])
            if speaker_data:
                self.properties_panel.show_speaker_properties(speaker_data)
            self._set_right_panel_state(PANEL_SPEAKER_SINGLE)
        else:
            self._multi_count_lbl.setText(f"{count} speakers selected")
            self._set_right_panel_state(PANEL_SPEAKER_MULTI)

    def _on_clear_speakers_requested(self):
        """Handle clear all speakers request."""
        zone = self.speaker_view.current_zone
        if not zone:
            return
        count = self.speaker_view.speaker_data_manager.get_speaker_count()
        if count == 0:
            return
        if ConfirmDialog.ask(
            self, "Clear Speakers",
            f"Remove all {count} speakers from '{zone.get('name', 'this zone')}'?",
            confirm_text="Remove All",
            danger=True,
        ):
            self.speaker_view.clear_all_speakers()

    # ==================== OBSTRUCTION PANEL ====================

    def _on_obstruction_selected_panel(self, obstruction_id):
        """Handle obstruction selection — update panel."""
        if obstruction_id:
            obs_data = self.speaker_view.obstruction_manager.get_selected_obstruction()
            if obs_data and hasattr(self, 'obstruction_properties_panel'):
                self.obstruction_properties_panel.show_obstruction_properties(obs_data)
            self._set_right_panel_state(PANEL_OBSTRUCTION)
        else:
            if self.speaker_view.current_zone:
                self._set_right_panel_state(PANEL_ZONE)
            else:
                self._set_right_panel_state(PANEL_EMPTY)

    # ==================== TOOLBAR ACTIONS ====================

    def on_save_layout(self):
        """Handle save layout action"""
        current_project_id = self.project_manager.get_current_project_id()
        if not current_project_id:
            AlertDialog.show_warning(self, "No Project", "Please select a project before saving the layout.")
            return False

        try:
            # Get layout data
            speaker_layout = {}
            for zone_id, speakers in self.speaker_view.layout_data.items():
                if speakers:
                    speaker_layout[zone_id] = speakers

            obstruction_layout = self.speaker_view.obstruction_manager.zone_obstructions

            # Update project data
            success = self.project_manager.update_project_data(speaker_layout, 'speaker_layout')
            if not success:
                AlertDialog.show_error(self, "Error", "Failed to update speaker layout data")
                return False

            success = self.project_manager.update_project_data(obstruction_layout, 'obstruction_layout')
            if not success:
                AlertDialog.show_error(self, "Error", "Failed to update obstruction layout data")
                return False

            # Save project
            success = self.project_manager.save_project()
            if success:
                self.status_label.setText("Layout saved successfully")
                self.project_manager.project_modified = False
                return True
            else:
                self.status_label.setText("Failed to save layout")
                return False

        except Exception as e:
            self.logger.error(f"Error saving layout: {e}", exc_info=True)
            AlertDialog.show_error(self, "Error", f"Failed to save layout: {str(e)}")
            return False

    # ==================== SPEAKER/OBSTRUCTION SELECTION ====================

    def on_speaker_selected(self, speaker_id):
        """Handle speaker selection (single-click, legacy signal)"""
        try:
            if not speaker_id:
                self.properties_panel.clear()
                return

            speaker_data = self.speaker_view.speaker_data_manager.get_speaker(speaker_id)
            if speaker_data:
                self.properties_panel.show_speaker_properties(speaker_data)
                self._set_right_panel_state(PANEL_SPEAKER_SINGLE)
            else:
                self.properties_panel.clear()

        except Exception as e:
            self.logger.error(f"Error in speaker selection: {e}", exc_info=True)
            self.properties_panel.clear()

    def on_obstruction_selected(self, obstruction_id):
        """Handle obstruction selection (legacy signal — delegates to panel handler)"""
        self._on_obstruction_selected_panel(obstruction_id)

    def on_speaker_property_changed(self, speaker_id, property_name, value):
        """Handle speaker property changes"""
        try:
            if property_name == 'delete':
                self.speaker_view.delete_selected_speakers()
                self.speaker_layout_changed.emit()
                if hasattr(self, 'project_manager'):
                    self.project_manager.project_modified = True
                return

            success = self.speaker_view.speaker_data_manager.update_speaker(speaker_id, property_name, value)
            if success:
                self.speaker_view.update()
                self.speaker_layout_changed.emit()
                if hasattr(self, 'project_manager'):
                    self.project_manager.project_modified = True

        except Exception as e:
            self.logger.error(f"Error updating speaker property: {e}", exc_info=True)

    def on_obstruction_property_changed(self, obstruction_id, property_name, value):
        """Handle obstruction property changes"""
        try:
            if property_name == 'delete':
                if self.speaker_view.delete_selected_obstruction():
                    self.obstruction_layout_changed.emit()
                    if hasattr(self, 'project_manager'):
                        self.project_manager.project_modified = True
                return

            success = self.speaker_view.obstruction_manager.update_obstruction(obstruction_id, property_name, value)
            if success:
                self.speaker_view.update()
                self.obstruction_layout_changed.emit()
                if hasattr(self, 'project_manager'):
                    self.project_manager.project_modified = True

        except Exception as e:
            self.logger.error(f"Error updating obstruction property: {e}", exc_info=True)

    # ==================== RIGHT PANEL STATE ====================

    def _set_right_panel_state(self, state):
        """Switch the right panel stack to the given state."""
        if hasattr(self, '_right_stack'):
            self._right_stack.setCurrentIndex(state)

    # ==================== ZONE PANEL HEADER ====================

    def _populate_zone_panel_header(self, zone):
        """Update the zone name, ceiling info, and pendant height spinner in the zone panel."""
        if not hasattr(self, '_panel_zone_name_lbl'):
            return
        self._panel_zone_name_lbl.setText(zone.get('name', 'Zone'))
        ceiling = zone.get('ceiling_height', 9.0)
        self._panel_zone_ceiling_lbl.setText(f"{ceiling:.0f} ft")
        max_pendant = max(4.0, ceiling - 1.0)
        self._panel_pendant_spin.blockSignals(True)
        self._panel_pendant_spin.setMaximum(max_pendant)
        self._panel_pendant_spin.setValue(min(zone.get('pendant_height', 9.0), max_pendant))
        self._panel_pendant_spin.blockSignals(False)

    def _on_panel_pendant_changed(self, value):
        """Store pendant height on the zone dict and update the speaker data manager."""
        zone = self.speaker_view.current_zone if hasattr(self, 'speaker_view') else None
        if not zone:
            return
        zone['pendant_height'] = value
        self.speaker_view.speaker_data_manager.set_zone_pendant_height(value)
        # Invalidate heatmap so coverage circles/heatmap recalculate with new height
        if hasattr(self.speaker_view, 'heatmap_renderer'):
            self.speaker_view.heatmap_renderer.invalidate_cache()
        self.speaker_view.update()

    # ==================== PROFILE COMBO MANAGEMENT ====================

    def _populate_profile_combo(self):
        """Populate the profile dropdown from profile_data_manager."""
        if not hasattr(self, '_panel_profile_combo'):
            return
        self._panel_profile_combo.blockSignals(True)
        current_profile = self._get_selected_profile_from_panel()
        self._panel_profile_combo.clear()

        if not hasattr(self, 'profile_data_manager') or not self.profile_data_manager:
            self._panel_profile_combo.blockSignals(False)
            return

        profiles = self.profile_data_manager.profiles  # dict key->SpeakerProfile
        selected_idx = 0
        for i, (key, profile) in enumerate(profiles.items()):
            display = f"{profile.manufacturer} — {profile.name}" if hasattr(profile, 'manufacturer') and profile.manufacturer else profile.name
            self._panel_profile_combo.addItem(display, userData=(key, profile))
            if current_profile and profile.name == current_profile.name:
                selected_idx = i

        if self._panel_profile_combo.count() > 0:
            self._panel_profile_combo.setCurrentIndex(selected_idx)

        self._panel_profile_combo.blockSignals(False)
        self._on_panel_profile_changed(self._panel_profile_combo.currentIndex())

    def _get_selected_profile_from_panel(self):
        """Get the profile currently selected in the panel dropdown."""
        if not hasattr(self, '_panel_profile_combo'):
            return None
        data = self._panel_profile_combo.currentData()
        if data:
            return data[1]  # (key, profile) tuple
        return None

    def _on_panel_profile_changed(self, index):
        """Handle profile dropdown selection change."""
        profile = self._get_selected_profile_from_panel()
        if profile:
            type_str = getattr(profile, 'model_type', 'Unknown')
            angle_str = f"{getattr(profile, 'dispersion_angle_h', '?')}°"
            self._panel_profile_sublabel.setText(f"{angle_str} · {type_str}")
        else:
            self._panel_profile_sublabel.setText("")
        self._update_zone_panel_preview()

    def _on_panel_grid_changed(self):
        self._update_zone_panel_preview()

    def _on_panel_overlap_changed(self):
        sender = self.sender()
        for btn in self._panel_overlap_btns:
            btn.setChecked(btn is sender)
        self._update_zone_panel_preview()

    def _on_panel_layout_method_changed(self):
        self._update_zone_panel_preview()

    def _get_panel_overlap_pct(self):
        for btn in self._panel_overlap_btns:
            if btn.isChecked():
                return btn.property("overlapPct")
        return 15

    def _get_panel_grid_type(self):
        return 'hex' if self._panel_hex_btn.isChecked() else 'rect'

    def _get_panel_layout_method(self):
        if hasattr(self, '_panel_layout_centroid_btn') and self._panel_layout_centroid_btn.isChecked():
            return 'centroid'
        return 'bbox'

    def _update_zone_panel_preview(self):
        """Update the speaker count/spacing preview in the zone panel."""
        if not hasattr(self, '_panel_preview_lbl'):
            return
        zone = self.speaker_view.current_zone if hasattr(self, 'speaker_view') else None
        profile = self._get_selected_profile_from_panel()
        if not zone or not profile:
            self._panel_preview_lbl.setText("Select a profile")
            self._panel_generate_btn.setEnabled(False)
            return
        try:
            grid_type = self._get_panel_grid_type()
            overlap_pct = self._get_panel_overlap_pct()
            layout_method = self._get_panel_layout_method()
            count, spacing_ft = self._auto_layout_manager.preview_layout(
                zone, profile, grid_type, overlap_pct, layout_method=layout_method)
            self._panel_preview_lbl.setText(f"<b>{count}</b> speakers · <b>{spacing_ft:.1f} ft</b> spacing")
            self._panel_generate_btn.setEnabled(count > 0)
        except Exception:
            self._panel_preview_lbl.setText("—")
            self._panel_generate_btn.setEnabled(False)

    def _on_panel_generate_layout(self):
        """Generate layout using right panel settings (no dialog)."""
        zone = self.speaker_view.current_zone
        profile = self._get_selected_profile_from_panel()
        if not zone or not profile:
            return
        grid_type = self._get_panel_grid_type()
        overlap_pct = self._get_panel_overlap_pct()
        layout_method = self._get_panel_layout_method()

        count, spacing_ft = self._auto_layout_manager.preview_layout(
            zone, profile, grid_type, overlap_pct, layout_method=layout_method)
        if count == 0:
            return

        if ConfirmDialog.ask(
            self, "Generate Layout",
            f"Place {count} speakers at {spacing_ft:.1f} ft spacing in '{zone.get('name', 'this zone')}'?",
            confirm_text="Place Speakers",
        ):
            self.speaker_view.speaker_data_manager.push_undo_snapshot()
            self.speaker_view.run_auto_layout(
                zone, profile, overlap_pct=overlap_pct, layout_method=layout_method)
            if hasattr(self.speaker_view, 'set_grid_type'):
                self.speaker_view.set_grid_type(grid_type)

    def _on_panel_place_toggled(self, checked):
        """Toggle manual speaker placement mode."""
        if checked:
            profile = self._get_selected_profile_from_panel()
            if not profile:
                AlertDialog.show_warning(self, "Place Speaker", "Select a profile first.")
                self._panel_place_btn.setChecked(False)
                return
            # Set profile then activate placement mode
            self.speaker_view.set_speaker_profile(profile)
            self.speaker_view.set_placement_mode(True)
            self._panel_place_btn.setText("● Placing… (click to stop)")
        else:
            self.speaker_view.set_placement_mode(False)
            self._panel_place_btn.setText("• Place Speaker")

    def _on_placement_mode_changed_panel(self, enabled, mode_type):
        """Sync place button state when placement mode changes externally."""
        if hasattr(self, '_panel_place_btn'):
            if not enabled or mode_type != "speaker":
                self._panel_place_btn.setChecked(False)
                self._panel_place_btn.setText("• Place Speaker")

    def _on_panel_new_profile(self):
        """Open create profile dialog."""
        if hasattr(self, 'speaker_profile_ui_manager'):
            self.speaker_profile_ui_manager._on_create_profile()
        else:
            from ui.dialogs.speaker_profile_dialog import SpeakerProfileDialog
            dialog = SpeakerProfileDialog(self)
            if dialog.exec():
                profile = dialog.get_profile()
                if profile:
                    self.profile_data_manager.add_profile(profile)
                    self._populate_profile_combo()

    def _on_panel_edit_profile(self):
        """Open edit profile dialog for selected profile."""
        if hasattr(self, 'speaker_profile_ui_manager'):
            self.speaker_profile_ui_manager._on_edit_profile()
        else:
            pass  # fallback: no-op if manager not available

    # ==================== PROJECT MANAGEMENT ====================

    def set_current_project(self, project_id, project_name=None):
        """Set current project and update UI"""
        self.current_project_id = project_id

        if project_name:
            self.status_label.setText(f"Project: {project_name}")
        else:
            self.status_label.setText("No project selected")

        self._clear_current_state()

        if project_id:
            self.load_zones_for_project(project_id)

        if self.project_manager:
            self.project_manager.project_modified = False
            self.project_manager.zones_modified = False

    def _clear_current_state(self):
        """Clear current state when switching projects"""
        self.speaker_view.clear_zone()
        self.speaker_view.background_manager.clear_background()
        if hasattr(self.speaker_view, 'layout_data'):
            self.speaker_view.layout_data = {}
        self.speaker_view.selected_speaker_id = None
        self.zone_selection_manager.clear_selection()
        if hasattr(self, 'speaker_profile_ui_manager'):
            self.speaker_profile_ui_manager.clear_selection()
        self.properties_panel.clear()
        self._backgrounds_loaded = False
        self._current_project_data = None
        self._set_right_panel_state(PANEL_EMPTY)

    def load_zones_for_project(self, project_id):
        """Load zones data for current project"""
        if not project_id:
            return

        try:
            project_data = self.project_manager.get_current_project_data()
            if not project_data:
                return

            zones_data = project_data.get('zones_data', {})
            zones = zones_data.get('zones', [])

            if not zones:
                self.zone_selection_manager.clear_selection()
                return

            # Store project data so background can be loaded on first zone selection
            self._current_project_data = project_data
            self.zone_selection_manager.load_zones(zones)
            self.set_ui_enabled(True)

        except Exception as e:
            self.logger.error(f"Error loading zones for project: {e}", exc_info=True)
            self.zone_selection_manager.clear_selection()

    def _load_project_backgrounds_and_layouts(self, project_data):
        """Load background images and layout data"""
        zones_data = project_data.get('zones_data', {})
        if 'background_path' in zones_data:
            background_path = zones_data.get('background_path')
            if background_path and os.path.exists(background_path):
                self.speaker_view.load_background(background_path)

        if 'speaker_layout' in project_data:
            self.speaker_view.load_speaker_layout(project_data['speaker_layout'])

        if 'obstruction_layout' in project_data:
            self.speaker_view.load_obstruction_layout(project_data['obstruction_layout'])

    def set_ui_enabled(self, enabled):
        """Enable/disable UI elements"""
        self.toolbar.set_actions_enabled(enabled)
        if hasattr(self, '_panel_profile_combo'):
            self._panel_profile_combo.setEnabled(enabled)
        if hasattr(self, '_panel_generate_btn') and not enabled:
            self._panel_generate_btn.setEnabled(False)
        self.zone_tree.setEnabled(enabled)
        QApplication.processEvents()

    def set_report_generator(self, shared_report_generator):
        """Set shared report generator"""
        self.shared_report_generator = shared_report_generator

    def has_unsaved_changes(self):
        """Check for unsaved changes"""
        return self.project_manager.has_unsaved_changes()

    def refresh_zones(self):
        """Refresh zones list"""
        if hasattr(self, '_loading_project') and self._loading_project:
            return

        if hasattr(self, '_in_refresh') and self._in_refresh:
            return

        self._in_refresh = True
        try:
            project_data = self.project_manager.get_current_project_data()
            if not project_data:
                return

            zones_data = project_data.get('zones_data', {})
            zones = zones_data.get('zones', [])

            # Update stored project data; background loads via zone selection
            self._current_project_data = project_data
            self.zone_selection_manager.refresh_zones(zones)
            self.set_ui_enabled(True)
            self.speaker_view.set_show_coverage(True)
            self.speaker_view.force_coverage_display()

        except Exception as e:
            self.logger.error(f"Error refreshing zones: {e}", exc_info=True)
        finally:
            self._in_refresh = False
