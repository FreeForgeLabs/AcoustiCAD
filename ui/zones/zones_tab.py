import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut

from ui.dialogs.confirm_dialog import ConfirmDialog

from ui.zones.zones_view import ZonesView
from ui.zones.properties_panel import PropertiesPanel
from core.project_manager import ProjectManager
from utils.report_menu_helper import ReportMenuHelper
from ui.zones.managers.toolbar_manager import ToolbarManager
from ui.zones.managers.toolbar_action_handler import ToolbarActionHandler
from ui.zones.managers.export_manager import ExportManager
from ui.zones.managers.grid_visual_manager import GridVisualManager

# Import shared styling system
from ui.styles.base_styles import Colors, Typography, Spacing, BorderRadius



class ZonesTab(QWidget):
    """Tab for editing zones with consistent shared styling - matches plotter tab"""

    zones_updated = Signal()  # Signal to notify other tabs of zone changes

    def __init__(self, storage, project_manager=None, parent=None):
        super().__init__(parent)

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Use provided project manager or create a new one
        if project_manager:
            self.project_manager = project_manager
        else:
            self.project_manager = ProjectManager(storage)

        self.current_project_id = None

        # Initialize managers
        self._init_managers()

        # Initialize UI
        self.init_ui()
        self.setup_shortcuts()
        self._connect_manager_signals()

        # Apply shared styling
        self._apply_shared_styling()

        # Enable grid and snap by default
        self._setup_default_grid_settings()

    def _init_managers(self):
        """Initialize all specialized managers"""
        self.toolbar_manager = ToolbarManager(self)
        self.toolbar_action_handler = ToolbarActionHandler(self)
        self.export_manager = ExportManager(self)
        self.grid_visual_manager = GridVisualManager(self)

    def init_ui(self):
        """Initialize the UI components with consistent shared styling"""
        # Main layout with consistent background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create toolbar using toolbar manager
        toolbar = self.toolbar_manager.create_toolbar()
        main_layout.addWidget(toolbar)

        # Create ReportMenuHelper and attach its menu to the toolbar Reports button
        self.report_helper = ReportMenuHelper(self, self, self.project_manager)
        report_menu = self.report_helper.create_report_menu()
        self.toolbar_manager.set_report_menu(report_menu)

        # Create horizontal layout for view and properties panel with consistent spacing
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        # Create the zones view with shared styling
        self.zones_view = ZonesView(self.project_manager)

        # Apply shared styling to zones view
        self.zones_view.setStyleSheet(f"""
            ZonesView {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                margin: {Spacing.SM};
            }}
        """)

        # Connect ZonesView signals with proper semantic handling
        self.zones_view.selection_changed.connect(self.update_properties_panel)
        self.zones_view.zones_modified.connect(self.on_zones_modified)
        self.zones_view.zones_refreshed.connect(self.on_zones_refreshed)
        self.zones_view.zones_structure_changed.connect(self.on_zones_structure_changed)

        # Live zoom readout — update toolbar label whenever the canvas zoom changes
        self.zones_view.canvas.zoom_changed.connect(self._on_canvas_zoom_changed)

        content_layout.addWidget(self.zones_view, 3)  # 3:1 ratio

        # Tell the project manager about our zones_view for thumbnail generation
        self.project_manager.set_zones_view(self.zones_view)

        # Collapse/expand toggle button between view and panel
        self._panel_visible = True
        self.panel_toggle_btn = QPushButton("‹")
        self.panel_toggle_btn.setFixedWidth(16)
        self.panel_toggle_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.panel_toggle_btn.setToolTip("Collapse properties panel")
        self.panel_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.panel_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.GRAY_200};
                border: none;
                border-radius: 0px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 600;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {Colors.GRAY_300};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self.panel_toggle_btn.clicked.connect(self._toggle_properties_panel)
        content_layout.addWidget(self.panel_toggle_btn)

        # Create properties panel with shared styling
        self.properties_panel = PropertiesPanel()

        # Apply shared styling to properties panel
        self.properties_panel.setStyleSheet(f"""
            PropertiesPanel {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                margin: {Spacing.SM};
            }}
        """)

        # Connect to the correct signal name
        self.properties_panel.user_action.connect(self.on_user_action)

        content_layout.addWidget(self.properties_panel, 1)  # 3:1 ratio

        main_layout.addLayout(content_layout)

        # Status bar with shared styling (similar to main window status)
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

    def _apply_shared_styling(self):
        """Apply shared styling system to match plotter tab"""
        # Main tab background - consistent grey like plotter tab
        self.setStyleSheet(f"""
            ZonesTab {{
                background-color: {Colors.BG_SECONDARY};
                border: none;
            }}
        """)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Zoom shortcuts
        self.shortcut_zoom_in = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in.activated.connect(self.on_zoom_in)

        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.on_zoom_out)

        self.shortcut_zoom_reset = QShortcut(QKeySequence("Ctrl+0"), self)
        self.shortcut_zoom_reset.activated.connect(self.on_zoom_reset)

        self.shortcut_zoom_fit = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_zoom_fit.activated.connect(self.on_zoom_fit)

    def _connect_manager_signals(self):
        """Connect signals from managers to appropriate handlers"""
        # Toolbar manager signals -> action handler
        toolbar = self.toolbar_manager
        action_handler = self.toolbar_action_handler

        # Connect toolbar signals to action handler methods
        toolbar.load_background_requested.connect(action_handler.handle_load_background)
        toolbar.calibrate_scale_requested.connect(self.zones_view.start_calibration)
        toolbar.draw_zone_requested.connect(action_handler.handle_draw_zone)
        toolbar.create_zone_requested.connect(self.properties_panel.on_create_zone)
        toolbar.line_color_changed.connect(action_handler.handle_line_color_change)
        # Grid resolution: combo now sends the actual pixel value directly
        toolbar.grid_resolution_requested.connect(
            self.grid_visual_manager.handle_grid_resolution_request
        )

        # Direct connections for simple actions
        toolbar.zoom_in_requested.connect(self.on_zoom_in)
        toolbar.zoom_out_requested.connect(self.on_zoom_out)
        toolbar.zoom_reset_requested.connect(self.on_zoom_reset)
        toolbar.zoom_fit_requested.connect(self.on_zoom_fit)
        toolbar.save_requested.connect(self.on_save)
        toolbar.export_image_requested.connect(self.export_manager.export_image)
        toolbar.clear_zones_requested.connect(self.on_clear_zones)
        toolbar.clear_all_requested.connect(self.on_clear_all)

        # Grid manager signals
        toolbar.grid_toggled.connect(self._handle_grid_toggle)
        toolbar.snap_toggled.connect(self._handle_snap_toggle)

        # Grid visual manager signals back to toolbar (for state sync)
        self.grid_visual_manager.grid_toggled.connect(self.toolbar_manager.set_grid_action_state)
        self.grid_visual_manager.snap_toggled.connect(self.toolbar_manager.set_snap_action_state)

        # Export manager signals
        self.export_manager.export_started.connect(self._on_export_started)
        self.export_manager.export_completed.connect(self._on_export_completed)

    def _setup_default_grid_settings(self):
        """Setup default grid settings"""
        try:
            self.grid_visual_manager.initialize_default_grid_settings()
            self.grid_visual_manager.sync_toolbar_with_grid_state()
        except Exception as e:
            self.logger.error(f"Error setting up default grid settings: {e}", exc_info=True)

    def _handle_grid_toggle(self, checked):
        """Handle grid toggle from toolbar"""
        try:
            actual_state = self.grid_visual_manager.toggle_grid()
            self.toolbar_manager.set_grid_action_state(actual_state)
            self.logger.debug(f"Grid toggled via toolbar, actual state: {actual_state}")
        except Exception as e:
            self.logger.error(f"Error handling grid toggle: {e}", exc_info=True)

    def _handle_snap_toggle(self, checked):
        """Handle snap toggle from toolbar"""
        try:
            actual_state = self.grid_visual_manager.toggle_snap()
            self.toolbar_manager.set_snap_action_state(actual_state)
            self.logger.debug(f"Snap toggled via toolbar, actual state: {actual_state}")
        except Exception as e:
            self.logger.error(f"Error handling snap toggle: {e}", exc_info=True)

    def _update_status_with_scale(self, project_name=None):
        """Update status bar with project name and scale info"""
        # Get scale info
        scale_factor = self.project_manager.get_scale_manager().get_scale_factor()

        if not self.project_manager.get_scale_manager().is_calibrated():
            scale_text = "Scale: Not Calibrated ⚠"
        else:
            scale_text = f"Scale: {scale_factor:.1f} px/ft ✓"

        # Combine with project name
        if project_name:
            status = f"Project: {project_name} | {scale_text}"
        else:
            status = f"No project selected | {scale_text}"

        self.status_label.setText(status)


    # ==================== PROJECT MANAGEMENT ====================


    def set_current_project(self, project_id, project_name=None):
        """Set the current project and update UI accordingly"""
        self.current_project_id = project_id

        # Update status label with scale info
        self._update_status_with_scale(project_name)

        # Clear current content without signals
        self.zones_view.clear_all()
        self.properties_panel.show_no_selection()

        # Reset scale to default value
        if hasattr(self.zones_view, 'scale_manager'):
            self.zones_view.scale_manager.reset_to_default()

        # Load zones data for this project if available
        if project_id:
            self.load_zones_for_project(project_id)

        # Update toolbar state
        self.toolbar_manager.update_draw_zone_button()
        self.toolbar_manager.update_zoom_label(100)

        # Update properties panel once after all loading is complete
        self.update_properties_panel()

        # Reset modification flags
        if self.project_manager:
            self.project_manager.zones_modified = False
            self.project_manager.project_modified = False

    def load_zones_for_project(self, project_id):
        """Load zones data for the current project"""
        if not project_id:
            return

        try:
            project_data = self.project_manager.get_current_project_data()
            if not project_data:
                self.logger.warning(f"No project data found for project ID: {project_id}")
                return

            # Load scale data from project first
            if 'scale_data' in project_data:
                scale_data = project_data['scale_data']
                self.project_manager.scale_manager.load_scale_data(scale_data)
                self.logger.debug(f"Loaded scale factor from project: {scale_data.get('scale_factor', 12.0)}")

            # Check if project has zones data
            if 'zones_data' in project_data:
                zones_data = project_data['zones_data']

                if isinstance(zones_data, dict) and 'zones' in zones_data:
                    zone_count = len(zones_data['zones'])
                    self.logger.debug(f"Found {zone_count} zones in project {project_id}")

                    if zone_count > 0:
                        first_zone = zones_data['zones'][0]
                        self.logger.debug(
                            f"First zone: {first_zone.get('name', 'unnamed')}, "
                            f"has points: {'points' in first_zone}"
                        )
                else:
                    self.logger.warning(f"Project has zones_data but in unexpected format: {type(zones_data)}")

                # Load the zones data
                self.zones_view.from_json(zones_data)
            else:
                # Normal state for a brand-new or never-edited project — not a problem.
                self.logger.debug(f"Project {project_id} has no zones_data key (no zones drawn yet)")

        except Exception as e:
            self.logger.error(f"Error loading zones for project {project_id}: {e}", exc_info=True)

    # ==================== ZOOM OPERATIONS ====================

    def _on_canvas_zoom_changed(self, factor: float):
        """Update toolbar zoom label whenever canvas zoom changes."""
        self.toolbar_manager.update_zoom_label(round(factor * 100))

    def on_zoom_in(self):
        """Handle zoom in action"""
        self.zones_view.zoom_in()

    def on_zoom_out(self):
        """Handle zoom out action"""
        self.zones_view.zoom_out()

    def on_zoom_reset(self):
        """Handle zoom reset action"""
        self.zones_view.reset_zoom()

    def on_zoom_fit(self):
        """Handle zoom fit action"""
        self.zones_view.fit_to_view()

    # ==================== SAVE OPERATIONS ====================

    def on_save(self):
        """Handle save button click"""
        try:
            project_id = self.project_manager.get_current_project_id()
            if not project_id:
                self.logger.warning("No project selected to save zones to")
                return False

            project_data = self.project_manager.get_current_project_data()
            if not project_data:
                self.logger.error("No project data available")
                return False

            project_data = project_data.copy()

            if not self.save_data(project_data):
                self.logger.error("Failed to save zones data")
                return False

            self.project_manager.current_project_data = project_data

            success = self.project_manager.save_project()

            if success:
                self.project_manager.zones_modified = False
                self.project_manager.project_modified = False
                self.logger.info(f"Project {project_id} saved successfully")
                return True
            else:
                self.logger.error(f"Failed to save project {project_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error in on_save: {e}", exc_info=True)
            return False

    def save_data(self, project_data):
        """Save zones data to the project"""
        try:
            zones_data = {
                'scale_factor': self.zones_view.scale_manager.get_scale_factor(),
                'background_path': self.zones_view.background_manager.get_background_path(),
                'zones': self.zones_view.zones.copy() if hasattr(self.zones_view, 'zones') else []
            }

            project_data['zones_data'] = zones_data
            self.logger.debug(f"Saved zones data with {len(zones_data['zones'])} zones")
            return True

        except Exception as e:
            self.logger.error(f"Error saving zones data: {e}", exc_info=True)
            return False

    def has_unsaved_changes(self):
        """Check if this tab has unsaved changes"""
        return self.project_manager.zones_modified or self.project_manager.project_modified

    # ==================== CLEAR OPERATIONS ====================

    def on_clear_zones(self):
        """Handle clear zones action"""
        try:
            if not self.zones_view.zones:
                return

            confirmed = ConfirmDialog.ask(
                self,
                "Clear Zones",
                "This will remove all zones but keep the background image.\n\n"
                "This action cannot be undone.",
                confirm_text="Clear Zones",
                danger=True,
            )

            if confirmed:
                old_zones = self.zones_view.zones.copy()
                self.zones_view.zones = []
                self.zones_view.selected_zone_index = None
                self.zones_view.canvas.update()

                self.on_zones_modified()
                self.on_zones_structure_changed()
                self.zones_view.selection_changed.emit()

                self.logger.info(f"Cleared {len(old_zones)} zones, background preserved")

        except Exception as e:
            self.logger.error(f"Error in clear zones: {e}", exc_info=True)

    def on_clear_all(self):
        """Handle clear all action"""
        confirmed = ConfirmDialog.ask(
            self,
            "Clear All",
            "This will remove all zones and the background image.\n\n"
            "This action cannot be undone.",
            confirm_text="Clear All",
            danger=True,
        )

        if confirmed:
            self.zones_view.clear_all()

            if hasattr(self.zones_view, 'scale_manager'):
                self.zones_view.scale_manager.reset_to_default()

            self.on_zones_modified()
            self.on_zones_structure_changed()
            self.update_properties_panel()
            self.logger.info("All content cleared (background, zones, and scale)")

    # ==================== EXPORT STATUS HANDLERS ====================

    def _on_export_started(self, message):
        """Handle export started signal"""
        self.status_label.setText(message)

    def _on_export_completed(self, file_path, success):
        """Handle export completed signal"""
        if success:
            self.status_label.setText("Export completed successfully")
        else:
            self.status_label.setText("Export failed")

    # ==================== ZONE MANAGEMENT ====================

    def update_properties_panel(self, force_zone_index=None):
        """Update the properties panel with current selection"""
        if force_zone_index is not None and 0 <= force_zone_index < len(self.zones_view.zones):
            self.zones_view.selected_zone_index = force_zone_index

        selected_zone = self.zones_view.get_selected_zone()

        self.properties_panel.update_tree(
            self.zones_view.zones,
            self.zones_view.selected_zone_index
        )

        if selected_zone:
            self.properties_panel.show_zone_properties(selected_zone)
        else:
            self.properties_panel.show_no_selection()

    def on_user_action(self, change_type, index, item_type, value):
        """Handle user actions from properties panel"""

        if change_type == 'select':
            if item_type == 'zone':
                self.zones_view.selected_zone_index = index
                self.zones_view.canvas.update()
                self.update_properties_panel()

        elif change_type == 'zone' and 0 <= index < len(self.zones_view.zones):
            self.zones_view.update_zone(index, {item_type: value})

        elif change_type == 'delete':
            if item_type == 'zone':
                if 0 <= index < len(self.zones_view.zones):
                    self.logger.info(f"Deleting zone at index {index}")
                    success = self.zones_view.delete_selected_zone()
                    if success:
                        self.logger.info("Zone deleted successfully")
                        self.update_properties_panel()
                    else:
                        self.logger.warning("Failed to delete zone")
                else:
                    self.logger.warning(f"Invalid zone index for deletion: {index}")

    def on_zones_modified(self):
        """Handle zones modified signal"""
        self.update_properties_panel()
        self.project_manager.set_zones_modified(True)
        self.project_manager.project_modified = True
        self.zones_updated.emit()

        # Update status to show scale changes
        project_data = self.project_manager.get_current_project_data()
        self._update_status_with_scale(project_data.get('name') if project_data else None)

    def on_zones_refreshed(self):
        """Handle zones refreshed signal"""
        self.update_properties_panel()

    def on_zones_structure_changed(self):
        """Handle zones structure changed signal"""
        self.toolbar_manager.update_draw_zone_button()

    # ==================== PANEL COLLAPSE ====================

    def _toggle_properties_panel(self):
        """Collapse or expand the right-side properties panel."""
        if self._panel_visible:
            self.properties_panel.hide()
            self.panel_toggle_btn.setText("›")
            self.panel_toggle_btn.setToolTip("Expand properties panel")
            self._panel_visible = False
            # Highlight the toggle strip so it's obvious the panel can be reopened
            self.panel_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PRIMARY};
                    border: none;
                    border-radius: 0px;
                    color: white;
                    font-size: 13px;
                    font-weight: 700;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background-color: {Colors.PRIMARY_HOVER};
                    color: white;
                }}
            """)
        else:
            self.properties_panel.show()
            self.panel_toggle_btn.setText("‹")
            self.panel_toggle_btn.setToolTip("Collapse properties panel")
            self._panel_visible = True
            # Restore subtle grey style
            self.panel_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.GRAY_200};
                    border: none;
                    border-radius: 0px;
                    color: {Colors.TEXT_SECONDARY};
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background-color: {Colors.GRAY_300};
                    color: {Colors.TEXT_PRIMARY};
                }}
            """)