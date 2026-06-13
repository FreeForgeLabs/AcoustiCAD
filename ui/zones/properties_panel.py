import logging

logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
                             QWidget, QDialog, QTabWidget, QLabel, QScrollArea,
                             QStyleFactory)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor

from ui.dialogs.confirm_dialog import ConfirmDialog
from ui.styles.base_styles import Colors
from ui.dialogs.zone_creation_dialog import ZoneCreationDialog
from ui.zones.managers.controller_manager import ControllerManager
from ui.zones.managers.material_manager import MaterialManager
from ui.zones.managers.zone_properties_manager import ZonePropertiesManager
from ui.zones.widgets.zone_panel_widgets import (
    ZoneStatusBadge, CompactZoneCard, ZoneCard,
    ModernLineEdit, ModernComboBox, ModernSpinBox, SPLSuggestionWidget
)

_GROUP_BOX_STYLE = f"""
    QGroupBox {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.BORDER_MEDIUM};
        border-radius: 8px;
        margin: 2px;
        padding-top: 16px;
        font-weight: 600;
        font-size: 11px;
        color: {Colors.TEXT_PRIMARY};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
        background-color: {Colors.WHITE};
    }}
"""


class PropertiesPanel(QWidget):
    """Panel for displaying and editing zone properties with modern tabbed interface"""

    user_action = Signal(str, int, str, object)  # type, index, property_name, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.room_names = set()  # Keep track of room names
        self.selected_zone_index = None  # Track currently selected zone index

        # CRITICAL: Flag to prevent infinite recursion during updates
        self._updating_programmatically = False

        # Initialize properties card reference
        self.zone_properties_card = None

        # Force Fusion style so QGroupBox inside managers renders cleanly on macOS
        fusion = QStyleFactory.create("Fusion")
        if fusion:
            self.setStyle(fusion)

        # Ensure the widget's own background is painted (needed for stylesheet
        # background-color to take effect on a custom QWidget subclass)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Initialize managers
        self.controller_manager = ControllerManager(self)
        self.material_manager = MaterialManager(self)
        self.zone_properties_manager = ZonePropertiesManager(self)

        self.init_ui()

    def init_ui(self):
        """Initialize the UI components with modern tabbed interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(0)

        # Create modern tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget {{
                background-color: {Colors.WHITE};
            }}
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 8px;
                background-color: {Colors.GRAY_100};
                margin-top: -1px;
            }}
            QTabWidget::tab-bar {{
                alignment: left;
            }}
            QTabBar {{
                background-color: {Colors.WHITE};
            }}
            QTabBar::tab {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 500;
                font-size: 11px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.GRAY_100};
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 1px solid {Colors.GRAY_100};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Colors.GRAY_50};
                color: {Colors.GRAY_700};
            }}
        """)

        # Create the three tabs using modern design
        self.zones_tab = self.create_zones_tab()
        self.materials_tab = self.create_materials_tab()
        self.notes_tab = self.create_notes_tab()

        # Add tabs to tab widget
        self.tab_widget.addTab(self.zones_tab, "Zones")
        self.tab_widget.addTab(self.materials_tab, "Materials")
        self.tab_widget.addTab(self.notes_tab, "Notes")

        # Add the tab widget to the main layout
        main_layout.addWidget(self.tab_widget)

        # No selection message - visible when no zone is selected
        self.no_selection = QLabel("Select a zone to view properties")
        self.no_selection.setAlignment(Qt.AlignCenter)
        self.no_selection.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
                font-style: italic;
                padding: 40px;
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 8px;
                margin: 4px;
            }}
        """)
        main_layout.addWidget(self.no_selection)

    def create_zones_tab(self):
        """Create the zones tab with space-efficient design"""
        zones_tab = QWidget()
        zones_layout = QVBoxLayout(zones_tab)
        zones_layout.setContentsMargins(8, 8, 8, 8)
        zones_layout.setSpacing(6)

        # Compact Zone Tree Card with buttons at bottom
        tree_card = CompactZoneCard("Zone Management")

        # Connect button signals
        tree_card.create_btn.clicked.connect(self.on_create_zone)
        tree_card.delete_btn.clicked.connect(lambda: self.on_delete_item('zone'))

        # Store references for enabling/disabling
        self.create_zone_btn = tree_card.create_btn
        self.delete_zone_btn = tree_card.delete_btn

        # "Create Zone" has moved to the toolbar's "+ Zone" split button
        self.create_zone_btn.setVisible(False)

        # Compact zone tree widget
        self.item_tree = QTreeWidget()
        self.item_tree.setHeaderLabels(["Zone", "Area"])
        self.item_tree.setColumnWidth(0, 120)
        self.item_tree.setAlternatingRowColors(True)
        self.item_tree.setRootIsDecorated(False)
        self.item_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Colors.WHITE};
                border: none;
                selection-background-color: {Colors.PRIMARY_LIGHT};
                alternate-background-color: {Colors.GRAY_100};
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px 4px;
                border-bottom: 1px solid {Colors.GRAY_200};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
            }}
            QTreeWidget::item:hover:!selected {{
                background-color: {Colors.GRAY_100};
                color: {Colors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Colors.GRAY_100};
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
                font-weight: 600;
                font-size: 9px;
                text-transform: uppercase;
                color: {Colors.TEXT_SECONDARY};
            }}
        """)
        self.item_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)

        # Add tree to card - it will expand to fill available space
        tree_card.add_content(self.item_tree)

        # Set minimum height for the tree card to show multiple zones
        tree_card.setMinimumHeight(180)

        zones_layout.addWidget(tree_card, 1)  # Give it stretch factor of 1

        # Compact Zone Properties Card (audio-focused)
        props_card = self.create_audio_zone_properties_section()
        zones_layout.addWidget(props_card)

        return zones_tab

    def create_audio_zone_properties_section(self):
        """Create compact audio-focused zone properties section"""
        props_card = ZoneCard("Zone Properties")

        # Zone Name
        self.zone_name_edit = ModernLineEdit("Zone Name", "Enter zone name...")
        props_card.content_layout.addWidget(self.zone_name_edit)

        # Area display (read-only)
        area_widget = QWidget()
        area_layout = QHBoxLayout(area_widget)
        area_layout.setContentsMargins(0, 0, 0, 0)
        area_layout.setSpacing(8)

        area_label = QLabel("AREA")
        area_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                min-width: 60px;
            }}
        """)
        area_layout.addWidget(area_label)

        self.zone_area_badge = ZoneStatusBadge("Not calculated", "uncalibrated")
        area_layout.addWidget(self.zone_area_badge)
        area_layout.addStretch()

        props_card.content_layout.addWidget(area_widget)

        # Audio-focused properties in 2x2 grid
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        grid_layout.setSpacing(4)

        # Row 1: Ceiling Height + Ceiling Type
        row1_widget = QWidget()
        row1_layout = QHBoxLayout(row1_widget)
        row1_layout.setSpacing(8)

        self.ceiling_height = ModernSpinBox("Ceiling Height", " ft", 6.0, 30.0, 0.5, 9.0)
        row1_layout.addWidget(self.ceiling_height)

        self.ceiling_type = ModernComboBox("Ceiling Type", [
            "Open Ceiling", "Drop Ceiling", "Drywall", "Concrete", "Other"
        ])
        row1_layout.addWidget(self.ceiling_type)

        grid_layout.addWidget(row1_widget)

        # Row 1.5: Listener Height (ear level used for speaker coverage calculations)
        row_lh_widget = QWidget()
        row_lh_layout = QHBoxLayout(row_lh_widget)
        row_lh_layout.setSpacing(8)

        self.listener_height = ModernSpinBox("Listener Height", " ft", 3.0, 8.0, 0.5, 5.5)
        self.listener_height.setToolTip(
            "Ear level height used for speaker coverage calculations "
            "(seated: ~4 ft, standing: ~5.5 ft)"
        )
        row_lh_layout.addWidget(self.listener_height)
        row_lh_layout.addStretch()

        grid_layout.addWidget(row_lh_widget)

        # Row 2: Target SPL (with suggestion) + Ambient Noise
        row2_widget = QWidget()
        row2_layout = QHBoxLayout(row2_widget)
        row2_layout.setSpacing(8)

        self.target_spl = SPLSuggestionWidget()
        row2_layout.addWidget(self.target_spl)

        self.ambient_noise = ModernSpinBox("Ambient Noise", " dB", 30.0, 65.0, 1.0, 45.0)
        row2_layout.addWidget(self.ambient_noise)

        grid_layout.addWidget(row2_widget)

        props_card.content_layout.addWidget(grid_widget)

        # Connect signals for property changes
        if hasattr(self.zone_name_edit, 'line_edit'):
            self.zone_name_edit.line_edit.textChanged.connect(self._on_zone_name_changed)
        if hasattr(self.ceiling_height, 'spin_box'):
            self.ceiling_height.spin_box.valueChanged.connect(self._on_ceiling_height_changed)
        if hasattr(self.listener_height, 'spin_box'):
            self.listener_height.spin_box.valueChanged.connect(self._on_listener_height_changed)
        if hasattr(self.ceiling_type, 'combo_box'):
            self.ceiling_type.combo_box.currentTextChanged.connect(self._on_ceiling_type_changed)
        if hasattr(self.target_spl, 'spl_spinbox'):
            self.target_spl.spl_spinbox.valueChanged.connect(self._on_target_spl_changed)
        if hasattr(self.ambient_noise, 'spin_box'):
            self.ambient_noise.spin_box.valueChanged.connect(self._on_ambient_noise_changed)

        # Initially hide the properties card
        props_card.setVisible(False)
        self.zone_properties_card = props_card

        return props_card

    def _on_zone_name_changed(self):
        """Handle zone name changes"""
        if not self._updating_programmatically and self.selected_zone_index is not None:
            new_name = self.zone_name_edit.text()
            self.user_action.emit('zone', self.selected_zone_index, 'name', new_name)

    def _on_ceiling_height_changed(self):
        """Handle ceiling height changes."""
        if not self._updating_programmatically and self.selected_zone_index is not None:
            new_height = self.ceiling_height.value()
            self.user_action.emit('zone', self.selected_zone_index, 'ceiling_height', new_height)

    def _on_listener_height_changed(self):
        """Handle listener height changes."""
        if not self._updating_programmatically and self.selected_zone_index is not None:
            self.user_action.emit('zone', self.selected_zone_index, 'listener_height',
                                  self.listener_height.value())

    def _on_ceiling_type_changed(self):
        """Handle ceiling type changes"""
        if not self._updating_programmatically and self.selected_zone_index is not None:
            new_type = self.ceiling_type.currentText()
            self.user_action.emit('zone', self.selected_zone_index, 'ceiling_type', new_type)

    def _on_target_spl_changed(self):
        """Handle target SPL changes"""
        if not self._updating_programmatically and self.selected_zone_index is not None:
            new_spl = self.target_spl.value()
            self.user_action.emit('zone', self.selected_zone_index, 'target_spl', new_spl)

    def _on_ambient_noise_changed(self):
        """Handle ambient noise changes"""
        if not self._updating_programmatically and self.selected_zone_index is not None:
            new_ambient = self.ambient_noise.value()
            self.user_action.emit('zone', self.selected_zone_index, 'ambient_noise', new_ambient)

            # Update SPL suggestion based on new ambient noise level
            self.target_spl.updateSuggestion(new_ambient)

    def create_materials_tab(self):
        """Create the materials tab with modern styling"""
        materials_tab = QWidget()
        materials_layout = QVBoxLayout(materials_tab)
        materials_layout.setContentsMargins(8, 8, 8, 8)
        materials_layout.setSpacing(8)

        # Controllers Card
        controllers_section = self.controller_manager.create_controllers_section()
        if hasattr(controllers_section, 'setStyleSheet'):
            controllers_section.setStyleSheet(_GROUP_BOX_STYLE)
        materials_layout.addWidget(controllers_section)

        # Materials Card
        materials_section = self.material_manager.create_materials_section()
        if hasattr(materials_section, 'setStyleSheet'):
            materials_section.setStyleSheet(_GROUP_BOX_STYLE)
        materials_layout.addWidget(materials_section)

        materials_layout.addStretch(1)
        return materials_tab

    def create_notes_tab(self):
        """Create the notes tab with modern styling"""
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(8, 8, 8, 8)
        notes_layout.setSpacing(8)

        # Notes Card
        notes_section = self.zone_properties_manager.create_notes_section()
        if hasattr(notes_section, 'setStyleSheet'):
            notes_section.setStyleSheet(_GROUP_BOX_STYLE)
        notes_layout.addWidget(notes_section)

        notes_layout.addStretch(1)
        return notes_tab

    # ==================== TREE DISPLAY MANAGEMENT ====================

    def update_tree(self, zones, selected_zone=None):
        """Refresh the tree display WITHOUT emitting signals - PROGRAMMATIC UPDATE ONLY"""
        # Guard against recursive calls
        if self._updating_programmatically:
            return

        self._updating_programmatically = True

        try:
            # Block tree signals during update
            self.item_tree.blockSignals(True)

            # Clear tree
            self.item_tree.clear()

            # Store the selected indices
            self.selected_zone_index = selected_zone

            # Update managers with selection
            if selected_zone is not None:
                self.controller_manager.set_selected_zone_index(selected_zone)
                self.material_manager.set_selected_zone_index(selected_zone)
                self.zone_properties_manager.set_selected_zone_index(selected_zone)

            # If no zones, show the "no selection" panel
            if not zones:
                self.show_no_selection()
                return

            # Find scale manager to check calibration
            scale_manager = self._find_scale_manager()
            is_scale_calibrated = scale_manager and scale_manager.is_calibrated()

            # Add zones to tree with modern styling
            for zone_idx, zone in enumerate(zones):
                # Create zone item
                zone_item = QTreeWidgetItem(self.item_tree)
                zone_item.setText(0, zone.get('name', f"Zone {zone_idx + 1}"))

                # Add area with status badge styling
                if is_scale_calibrated and 'area' in zone and zone['area'] is not None:
                    zone_item.setText(1, f"{zone['area']:.1f} ft²")
                else:
                    zone_item.setText(1, "Not scaled")

                # Store zone index for selection
                zone_item.setData(0, Qt.UserRole, ('zone', zone_idx))

                # Modern color scheme for zones
                zone_colors = [
                    QColor(230, 255, 230),  # Light green
                    QColor(230, 240, 255),  # Light blue
                    QColor(255, 240, 240),  # Light red
                    QColor(255, 250, 230),  # Light yellow
                    QColor(255, 245, 220),  # Light orange
                    QColor(248, 240, 255),  # Light purple
                ]

                color_index = zone.get('color_index', zone_idx % 6)
                zone_color = zone_colors[color_index % len(zone_colors)]

                zone_item.setBackground(0, QBrush(zone_color))
                zone_item.setBackground(1, QBrush(zone_color))

                # Highlight if selected with modern blue
                if zone_idx == selected_zone:
                    selected_color = QColor(227, 242, 253)  # Modern blue selection
                    zone_item.setBackground(0, QBrush(selected_color))
                    zone_item.setBackground(1, QBrush(selected_color))

            # Select the appropriate item if we have a selected zone
            if selected_zone is not None and 0 <= selected_zone < len(zones):
                item = self.item_tree.topLevelItem(selected_zone)
                if item:
                    item.setSelected(True)
                    self.item_tree.setCurrentItem(item)

            # Enable delete button if a zone is selected
            self.delete_zone_btn.setEnabled(self.selected_zone_index is not None)

        finally:
            # CRITICAL: Always restore signals and clear flag
            self.item_tree.blockSignals(False)
            self._updating_programmatically = False

    # ==================== ZONE TREE MANAGEMENT ====================

    def on_tree_selection_changed(self):
        """Handle selection changes in the tree widget"""
        try:
            if self._updating_programmatically:
                return

            selected_items = self.item_tree.selectedItems()
            if not selected_items:
                self.delete_zone_btn.setEnabled(False)
                return

            item = selected_items[0]
            item_data = item.data(0, Qt.UserRole)

            if not item_data:
                # This is a room header, not a zone
                self.delete_zone_btn.setEnabled(False)
                return

            item_type, index = item_data

            zones_view = self._find_zones_view()
            zones_count = len(zones_view.zones) if zones_view else 0

            if item_type == 'zone' and 0 <= index < zones_count:
                self.selected_zone_index = index
                self.controller_manager.set_selected_zone_index(index)
                self.material_manager.set_selected_zone_index(index)
                self.zone_properties_manager.set_selected_zone_index(index)
                self.delete_zone_btn.setEnabled(True)
                self.user_action.emit('select', index, 'zone', None)
            else:
                self.delete_zone_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"Error in on_tree_selection_changed: {e}")
            self.delete_zone_btn.setEnabled(False)

    # ==================== ZONE PROPERTY DISPLAY ====================

    def show_zone_properties(self, zone):
        """Show properties for the selected zone - PROGRAMMATIC UPDATE"""
        # CRITICAL: Set flag to prevent recursion from property widgets
        self._updating_programmatically = True

        try:
            # Hide no selection message
            self.no_selection.setVisible(False)

            # Show our modern zone properties card if it exists
            if self.zone_properties_card is not None:
                self.zone_properties_card.setVisible(True)

                # Update audio-focused property fields
                self.zone_name_edit.setText(zone.get('name', ''))

                # Update area badge
                if 'area' in zone and zone['area'] is not None:
                    area_text = f"{zone['area']:.1f} ft²"
                    self.zone_area_badge.setText(area_text)
                    self.zone_area_badge.status_type = "calibrated"
                else:
                    self.zone_area_badge.setText("Not scaled")
                    self.zone_area_badge.status_type = "uncalibrated"
                self.zone_area_badge.update_style()

                # Update audio properties
                ceiling_height = zone.get('ceiling_height', 9.0)
                self.ceiling_height.setValue(ceiling_height)

                ceiling_type = zone.get('ceiling_type', 'Open Ceiling')
                self.ceiling_type.setCurrentText(ceiling_type)

                listener_height = zone.get('listener_height', 5.5)
                self.listener_height.setValue(listener_height)

                target_spl = zone.get('target_spl', 75.0)
                self.target_spl.setValue(target_spl)

                ambient_noise = zone.get('ambient_noise', 45.0)
                self.ambient_noise.setValue(ambient_noise)

                # Update SPL suggestion based on ambient noise
                self.target_spl.updateSuggestion(ambient_noise)

            # Enable delete button when showing zone properties
            self.delete_zone_btn.setEnabled(True)

            # Load data into managers
            self.controller_manager.load_controllers_for_zone(zone)
            self.material_manager.load_materials_for_zone(zone)

            # Load notes into the notes tab
            self.zone_properties_manager.show_zone_properties(zone)

        finally:
            # CRITICAL: Always clear the flag
            self._updating_programmatically = False

    def show_no_selection(self):
        """Show the 'no selection' message"""
        # CRITICAL: Set flag during UI updates
        self._updating_programmatically = True

        try:
            # Hide modern zone properties card if it exists
            if self.zone_properties_card is not None:
                self.zone_properties_card.setVisible(False)

            # Show no selection message
            self.no_selection.setVisible(True)

            # Disable delete button since no zone is selected
            self.delete_zone_btn.setEnabled(False)

            # Clear managers
            self.controller_manager.clear_controllers()
            self.material_manager.clear_materials()
            self.zone_properties_manager.clear_notes()

        finally:
            # CRITICAL: Always clear the flag
            self._updating_programmatically = False

    # ==================== ZONE CREATION AND DELETION ====================

    def on_create_zone(self):
        """Handle create zone button click"""
        try:
            # Create and configure dialog
            dialog = ZoneCreationDialog(self)

            # Populate with existing room names
            dialog.set_room_names(self.room_names)

            # Show dialog
            result = dialog.exec()

            if result == QDialog.Accepted:
                # Get zone data from dialog
                zone_data = dialog.get_zone_data()

                # Add zone through ZonesView
                parent_view = self._find_zones_view()
                if parent_view:
                    parent_view.create_rectangle_zone(zone_data)

                    # Emit zones_modified signal through ZonesView
                    parent_view.zones_modified.emit()

                    # Refresh tree display to show the new zone
                    self.update_tree(parent_view.zones, len(parent_view.zones) - 1)

        except Exception as e:
            logger.error(f"Error creating zone: {e}", exc_info=True)
            from ui.dialogs.alert_dialog import AlertDialog
            AlertDialog.show_error(self, "Error", f"Failed to create zone: {str(e)}")

    def on_delete_item(self, item_type):
        """Handle delete button clicks"""
        try:
            if item_type == 'zone' and self.selected_zone_index is not None:
                zones_view = self._find_zones_view()
                zones = zones_view.zones if zones_view else []

                if 0 <= self.selected_zone_index < len(zones):
                    zone = zones[self.selected_zone_index]
                    zone_name = zone.get('name', f"Zone {self.selected_zone_index + 1}")
                    confirmed = ConfirmDialog.ask(
                        self,
                        "Delete Zone",
                        f"Delete '{zone_name}'? This action cannot be undone.",
                        confirm_text="Delete",
                        danger=True,
                    )
                    if confirmed:
                        self.user_action.emit('delete', self.selected_zone_index, 'zone', None)
                else:
                    from ui.dialogs.alert_dialog import AlertDialog
                    AlertDialog.show_warning(self, "Zone Not Found", "The selected zone no longer exists.")

        except Exception as e:
            logger.error(f"Error in on_delete_item: {e}")
            from ui.dialogs.alert_dialog import AlertDialog
            AlertDialog.show_error(self, "Error", f"Failed to delete zone: {str(e)}")

    # ==================== UTILITY METHODS ====================

    def _find_zones_view(self):
        """Find the ZonesView in the parent hierarchy"""
        parent = self.parent()
        while parent:
            # Check if parent is ZonesView
            if hasattr(parent, 'create_rectangle_zone'):
                return parent

            # Check if parent has zones_view property
            if hasattr(parent, 'zones_view'):
                return parent.zones_view

            # Move up to parent's parent
            if hasattr(parent, 'parent') and callable(parent.parent):
                parent = parent.parent()
            else:
                break

        return None

    def _find_scale_manager(self):
        """Find the scale manager in the parent hierarchy"""
        parent = self.parent()
        while parent:
            # Check if parent has scale_manager directly
            if hasattr(parent, 'scale_manager'):
                return parent.scale_manager

            # Check if parent has canvas with scale_manager
            if hasattr(parent, 'canvas') and hasattr(parent.canvas, 'scale_manager'):
                return parent.canvas.scale_manager

            # Check if parent is zones_view
            if hasattr(parent, 'zones_view') and parent.zones_view:
                if hasattr(parent.zones_view, 'scale_manager'):
                    return parent.zones_view.scale_manager
                if (hasattr(parent.zones_view, 'canvas') and
                        hasattr(parent.zones_view.canvas, 'scale_manager')):
                    return parent.zones_view.canvas.scale_manager

            # Move up to parent's parent
            if hasattr(parent, 'parent') and callable(parent.parent):
                parent = parent.parent()
            else:
                break

        return None