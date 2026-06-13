from PySide6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout,
                             QVBoxLayout, QInputDialog, QMenu)
from PySide6.QtCore import Qt, Signal

from ui.dialogs.alert_dialog import AlertDialog
from ui.dialogs.confirm_dialog import ConfirmDialog
from ui.styles.base_styles import Colors


class ControllerManager:
    """Manages controller operations for zones"""

    # Signal for when controller data changes
    controller_changed = Signal(str, int, str, object)  # type, index, property_name, value

    def __init__(self, parent=None):
        self.parent_panel = parent
        self.selected_zone_index = None
        self.controllers_list = None
        self.add_controller_btn = None
        self.remove_controller_btn = None

    def create_controllers_section(self):
        """Create the controllers UI section"""
        from PySide6.QtWidgets import QGroupBox

        # Controllers section
        controllers_group = QGroupBox("Controllers")
        controllers_layout = QVBoxLayout(controllers_group)

        # Add buttons in a horizontal layout
        controller_button_layout = QHBoxLayout()

        btn_style = f"""
            QPushButton {{
                background-color: {Colors.GRAY_200};
                color: {Colors.GRAY_800};
                border: 1px solid {Colors.GRAY_300};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {Colors.GRAY_300}; }}
            QPushButton:pressed {{ background-color: {Colors.GRAY_400}; }}
        """

        # Add controller button
        self.add_controller_btn = QPushButton("Add")
        self.add_controller_btn.setStyleSheet(btn_style)
        self.add_controller_btn.clicked.connect(self.add_controller)
        controller_button_layout.addWidget(self.add_controller_btn)

        # Remove controller button
        self.remove_controller_btn = QPushButton("Remove")
        self.remove_controller_btn.setStyleSheet(btn_style)
        self.remove_controller_btn.clicked.connect(self.remove_selected_controller)
        controller_button_layout.addWidget(self.remove_controller_btn)

        # Add stretch to push buttons to the left
        controller_button_layout.addStretch()
        controllers_layout.addLayout(controller_button_layout)

        # List to display added controllers
        self.controllers_list = QTreeWidget()
        self.controllers_list.setHeaderLabels(["Type", "Quantity"])
        self.controllers_list.setColumnWidth(0, 200)
        self.controllers_list.setMinimumHeight(120)
        self.controllers_list.setAlternatingRowColors(True)
        self.controllers_list.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Colors.WHITE};
                border: none;
                alternate-background-color: {Colors.GRAY_100};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 5px 4px;
                border-bottom: 1px solid {Colors.GRAY_200};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
            }}
            QTreeWidget::item:hover:!selected {{ background-color: {Colors.GRAY_100}; }}
            QHeaderView::section {{
                background-color: {Colors.GRAY_100};
                padding: 5px 8px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER_MEDIUM};
                font-size: 10px;
                font-weight: 600;
                color: {Colors.TEXT_SECONDARY};
            }}
        """)

        # Enable double-click editing and context menu
        self.controllers_list.itemDoubleClicked.connect(self.edit_controller_quantity)
        self.controllers_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.controllers_list.customContextMenuRequested.connect(self.show_controller_context_menu)

        controllers_layout.addWidget(self.controllers_list)

        return controllers_group

    def set_selected_zone_index(self, index):
        """Set the currently selected zone index"""
        self.selected_zone_index = index

    def _dialog_style(self):
        """Explicit light stylesheet for input dialogs (prevents macOS dark mode bleed-through)"""
        from ui.styles.base_styles import Colors
        return f"""
            QDialog {{ background-color: {Colors.WHITE}; color: {Colors.TEXT_PRIMARY}; }}
            QLabel {{ color: {Colors.TEXT_PRIMARY}; }}
            QComboBox {{
                color: {Colors.TEXT_PRIMARY}; background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM}; border-radius: 3px; padding: 3px 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.WHITE}; color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT}; selection-color: {Colors.PRIMARY};
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox {{
                color: {Colors.TEXT_PRIMARY}; background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM}; border-radius: 3px; padding: 3px 6px;
            }}
            QPushButton {{
                color: {Colors.GRAY_800}; background-color: {Colors.GRAY_200};
                border: 1px solid {Colors.GRAY_300}; border-radius: 4px; padding: 4px 12px;
            }}
            QPushButton:hover {{ background-color: {Colors.GRAY_300}; }}
        """

    def add_controller(self):
        """Handler for adding a controller to the zone"""
        if self.selected_zone_index is None:
            return

        controller_types = [
            "Volume Controller",
            "Zone,Source,Volume Controller",
            "Ambient Noise Sensor",
            "Bluetooth Input",
            "Audio Input",
            "Custom Controller"
        ]

        dlg = QInputDialog(self.parent_panel)
        dlg.setWindowTitle("Add Controller")
        dlg.setLabelText("Select controller type:")
        dlg.setComboBoxItems(controller_types)
        dlg.setComboBoxEditable(False)
        dlg.setStyleSheet(self._dialog_style())
        if not dlg.exec():
            return
        controller_type = dlg.textValue()
        if not controller_type:
            return

        if controller_type == "Custom Controller":
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Custom Controller")
            dlg.setLabelText("Enter custom controller name:")
            dlg.setInputMode(QInputDialog.TextInput)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return
            controller_type = dlg.textValue()
            if not controller_type:
                return

        dlg = QInputDialog(self.parent_panel)
        dlg.setWindowTitle("Controller Quantity")
        dlg.setLabelText(f"How many {controller_type}s?")
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntMinimum(1)
        dlg.setIntMaximum(100)
        dlg.setIntValue(1)
        dlg.setStyleSheet(self._dialog_style())
        if not dlg.exec():
            return
        quantity = dlg.intValue()

        # Check if this controller type already exists
        existing_item = self._find_controller_item(controller_type)
        if existing_item:
            # Update quantity instead of adding a new one
            existing_qty = int(existing_item.text(1))
            existing_item.setText(1, str(existing_qty + quantity))

            # Update in zone data
            self._update_controller_in_zone_data(controller_type, existing_qty + quantity)
        else:
            # Add new controller
            self._add_new_controller_item(controller_type, quantity)
            self._add_controller_to_zone_data(controller_type, quantity)

    def _find_controller_item(self, controller_type):
        """Find existing controller item in the list"""
        root = self.controllers_list.invisibleRootItem()
        for i in range(root.childCount()):
            if root.child(i).text(0) == controller_type:
                return root.child(i)
        return None

    def _add_new_controller_item(self, controller_type, quantity):
        """Add new controller item to the list"""
        item = QTreeWidgetItem(self.controllers_list)
        item.setText(0, controller_type)
        item.setText(1, str(quantity))

    def _add_controller_to_zone_data(self, controller_type, quantity):
        """Add controller to the zone's data"""
        if not self._get_zones_view():
            return

        zones = self._get_zones_view().zones
        if self.selected_zone_index >= len(zones):
            return

        # Initialize controllers list if it doesn't exist
        if 'controllers' not in zones[self.selected_zone_index]:
            zones[self.selected_zone_index]['controllers'] = []

        # Add the controller to the zone's controller list
        zones[self.selected_zone_index]['controllers'].append({
            'type': controller_type,
            'quantity': quantity
        })

        # Signal zone modified
        self._emit_controller_changed('controllers', zones[self.selected_zone_index]['controllers'])

    def _update_controller_in_zone_data(self, controller_type, new_quantity):
        """Update existing controller quantity in zone data"""
        if not self._get_zones_view():
            return

        zones = self._get_zones_view().zones
        if (self.selected_zone_index >= len(zones) or
                'controllers' not in zones[self.selected_zone_index]):
            return

        controllers = zones[self.selected_zone_index]['controllers']
        for controller in controllers:
            if controller.get('type') == controller_type:
                controller['quantity'] = new_quantity
                break

        # Signal zone modified
        self._emit_controller_changed('controllers', controllers)

    def remove_selected_controller(self):
        """Remove the currently selected controller from the list"""
        if self.selected_zone_index is None:
            return

        selected_items = self.controllers_list.selectedItems()
        if not selected_items:
            AlertDialog.show_info(self.parent_panel, "No Selection",
                                  "Please select a controller to remove.")
            return

        # Get the selected controller
        item = selected_items[0]
        controller_type = item.text(0)

        # Confirm removal
        if not ConfirmDialog.ask(
            self.parent_panel,
            "Remove Controller",
            f"Remove {controller_type} from this zone?",
            confirm_text="Remove",
            danger=True,
        ):
            return

        # Remove from the list widget
        self._remove_controller_item(item)

        # Remove from the zone data
        self._remove_controller_from_zone_data(controller_type)

    def _remove_controller_item(self, item):
        """Remove controller item from the list widget"""
        root = self.controllers_list.invisibleRootItem()
        for i in range(root.childCount()):
            if root.child(i) == item:
                root.removeChild(item)
                break

    def _remove_controller_from_zone_data(self, controller_type):
        """Remove controller from zone data"""
        if not self._get_zones_view():
            return

        zones = self._get_zones_view().zones
        if (self.selected_zone_index >= len(zones) or
                'controllers' not in zones[self.selected_zone_index]):
            return

        controllers = zones[self.selected_zone_index]['controllers']

        # Find and remove the matching controller
        for i, controller in enumerate(controllers):
            if controller.get('type') == controller_type:
                controllers.pop(i)
                break

        # Signal zone modified
        self._emit_controller_changed('controllers', controllers)

    def show_controller_context_menu(self, position):
        """Show context menu for controllers list"""
        if self.selected_zone_index is None:
            return

        # Get the item at the position
        item = self.controllers_list.itemAt(position)
        if not item:
            return

        # Create context menu
        menu = QMenu()
        edit_action = menu.addAction("Edit Quantity")
        remove_action = menu.addAction("Remove Controller")

        # Show the menu and get the selected action
        action = menu.exec_(self.controllers_list.mapToGlobal(position))

        if action == edit_action:
            self.edit_controller_quantity(item)
        elif action == remove_action:
            self.remove_controller(item)

    def edit_controller_quantity(self, item, column=None):
        """Edit the quantity of a controller (works with double-click or context menu)"""
        if self.selected_zone_index is None:
            return

        # Get controller type from the item
        controller_type = item.text(0)
        current_qty = int(item.text(1))

        dlg = QInputDialog(self.parent_panel)
        dlg.setWindowTitle("Edit Quantity")
        dlg.setLabelText(f"Enter quantity for {controller_type}:")
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntMinimum(1)
        dlg.setIntMaximum(100)
        dlg.setIntValue(current_qty)
        dlg.setStyleSheet(self._dialog_style())
        if not dlg.exec():
            return
        quantity = dlg.intValue()

        # Update the item in the list
        item.setText(1, str(quantity))

        # Update the data in the zone
        self._update_controller_in_zone_data(controller_type, quantity)

    def remove_controller(self, item):
        """Remove a controller from the zone"""
        if self.selected_zone_index is None:
            return

        controller_type = item.text(0)

        # Confirm removal
        if not ConfirmDialog.ask(
            self.parent_panel,
            "Remove Controller",
            f"Remove {controller_type} from this zone?",
            confirm_text="Remove",
            danger=True,
        ):
            return

        # Remove from the list widget
        self._remove_controller_item(item)

        # Remove from the zone data
        self._remove_controller_from_zone_data(controller_type)

    def load_controllers_for_zone(self, zone):
        """Load controllers for the given zone"""
        # Clear the controllers list first
        self.controllers_list.clear()

        # Update controllers list with zone's controllers
        if 'controllers' in zone and zone['controllers']:
            for controller in zone['controllers']:
                item = QTreeWidgetItem(self.controllers_list)
                item.setText(0, controller.get('type', 'Unknown'))
                item.setText(1, str(controller.get('quantity', 1)))

    def clear_controllers(self):
        """Clear the controllers list"""
        if self.controllers_list:
            self.controllers_list.clear()

    def _get_zones_view(self):
        """Get the zones view from parent hierarchy"""
        if not self.parent_panel:
            return None

        # Try to find zones_view through parent hierarchy
        parent = self.parent_panel.parent()
        while parent:
            if hasattr(parent, 'zones_view'):
                return parent.zones_view
            if hasattr(parent, 'parent') and callable(parent.parent):
                parent = parent.parent()
            else:
                break
        return None

    def _emit_controller_changed(self, property_name, value):
        """Emit controller changed signal"""
        if hasattr(self.parent_panel, 'user_action'):
            self.parent_panel.user_action.emit(
                'zone', self.selected_zone_index, property_name, value
            )