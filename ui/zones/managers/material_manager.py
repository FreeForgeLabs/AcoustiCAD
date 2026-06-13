from PySide6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout,
                             QVBoxLayout, QInputDialog, QMenu)
from PySide6.QtCore import Qt, Signal

from ui.dialogs.alert_dialog import AlertDialog
from ui.dialogs.confirm_dialog import ConfirmDialog
from ui.styles.base_styles import Colors


class MaterialManager:
    """Manages material operations for zones"""

    def __init__(self, parent=None):
        self.parent_panel = parent
        self.selected_zone_index = None
        self.materials_list = None
        self.add_material_btn = None
        self.remove_material_btn = None

    def create_materials_section(self):
        """Create the materials UI section"""
        from PySide6.QtWidgets import QGroupBox

        # Materials section
        materials_group = QGroupBox("Materials")
        materials_section_layout = QVBoxLayout(materials_group)

        # Add buttons in a horizontal layout
        materials_button_layout = QHBoxLayout()

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

        # Add material button
        self.add_material_btn = QPushButton("Add")
        self.add_material_btn.setStyleSheet(btn_style)
        self.add_material_btn.clicked.connect(self.add_material)
        materials_button_layout.addWidget(self.add_material_btn)

        # Remove material button
        self.remove_material_btn = QPushButton("Remove")
        self.remove_material_btn.setStyleSheet(btn_style)
        self.remove_material_btn.clicked.connect(self.remove_selected_material)
        materials_button_layout.addWidget(self.remove_material_btn)

        # Add stretch to push buttons to the left
        materials_button_layout.addStretch()
        materials_section_layout.addLayout(materials_button_layout)

        # List to display added materials
        self.materials_list = QTreeWidget()
        self.materials_list.setHeaderLabels(["Type", "Quantity", "Details"])
        self.materials_list.setColumnWidth(0, 150)
        self.materials_list.setColumnWidth(1, 80)
        self.materials_list.setMinimumHeight(120)
        self.materials_list.setAlternatingRowColors(True)
        self.materials_list.setStyleSheet(f"""
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
        self.materials_list.itemDoubleClicked.connect(self.edit_material_quantity)
        self.materials_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.materials_list.customContextMenuRequested.connect(self.show_material_context_menu)

        materials_section_layout.addWidget(self.materials_list)

        return materials_group

    def set_selected_zone_index(self, index):
        """Set the currently selected zone index"""
        self.selected_zone_index = index

    def _dialog_style(self):
        """Explicit light stylesheet for input dialogs (prevents macOS dark mode bleed-through)"""
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

    def add_material(self):
        """Handler for adding a material to the zone"""
        if self.selected_zone_index is None:
            return

        material_types = [
            "Speaker Cable",
            "Signal Cable",
            "CAT Cable",
            "Conduit",
            "Mounting Bracket",
            "Wall Plate",
            "Connector",
            "Junction Box",
            "Cable Tie / Velcro",
            "Custom Material"
        ]

        dlg = QInputDialog(self.parent_panel)
        dlg.setWindowTitle("Add Material")
        dlg.setLabelText("Select material type:")
        dlg.setComboBoxItems(material_types)
        dlg.setComboBoxEditable(False)
        dlg.setStyleSheet(self._dialog_style())
        if not dlg.exec():
            return
        material_type = dlg.textValue()
        if not material_type:
            return

        if material_type == "Custom Material":
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Custom Material")
            dlg.setLabelText("Enter custom material name:")
            dlg.setInputMode(QInputDialog.TextInput)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return
            material_type = dlg.textValue()
            if not material_type:
                return

        # Get material-specific details
        quantity, details = self._get_material_details(material_type)
        if quantity is None:
            return

        # Check if this material type already exists with same details
        existing_item = self._find_material_item(material_type, details)
        if existing_item:
            # Update quantity instead of adding a new one
            existing_qty = int(existing_item.text(1))
            existing_item.setText(1, str(existing_qty + quantity))
            self._update_material_in_zone(material_type, existing_qty + quantity, details)
        else:
            # Add new material
            self._add_new_material_item(material_type, quantity, details)
            self._update_material_in_zone(material_type, quantity, details)

    def _get_material_details(self, material_type):
        """Get quantity and details for specific material types"""
        quantity = 1
        details = ""

        if material_type == "Speaker Cable":
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Speaker Cable Length")
            dlg.setLabelText("Enter length in feet:")
            dlg.setInputMode(QInputDialog.DoubleInput)
            dlg.setDoubleMinimum(0.1)
            dlg.setDoubleMaximum(10000)
            dlg.setDoubleValue(25)
            dlg.setDoubleDecimals(1)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return None, None
            length = dlg.doubleValue()

            dlg2 = QInputDialog(self.parent_panel)
            dlg2.setWindowTitle("Speaker Cable Gauge")
            dlg2.setLabelText("Select wire gauge:")
            dlg2.setComboBoxItems(["10 AWG", "12 AWG", "14 AWG", "16 AWG", "18 AWG"])
            dlg2.setComboBoxEditable(False)
            dlg2.setStyleSheet(self._dialog_style())
            gauge = "12 AWG"
            if dlg2.exec():
                gauge = dlg2.textValue()
            details = f"{length} ft / {gauge}"

        elif material_type in ("Signal Cable", "CAT Cable"):
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle(f"{material_type} Length")
            dlg.setLabelText("Enter length in feet:")
            dlg.setInputMode(QInputDialog.DoubleInput)
            dlg.setDoubleMinimum(0.1)
            dlg.setDoubleMaximum(10000)
            dlg.setDoubleValue(25)
            dlg.setDoubleDecimals(1)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return None, None
            details = f"{dlg.doubleValue()} ft"

        elif material_type == "Wall Plate":
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Wall Plate Quantity")
            dlg.setLabelText("How many wall plates?")
            dlg.setInputMode(QInputDialog.IntInput)
            dlg.setIntMinimum(1)
            dlg.setIntMaximum(100)
            dlg.setIntValue(1)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return None, None
            quantity = dlg.intValue()

            dlg2 = QInputDialog(self.parent_panel)
            dlg2.setWindowTitle("Wall Plate Gang")
            dlg2.setLabelText("Select gang size:")
            dlg2.setComboBoxItems(["Single Gang", "Double Gang", "Triple Gang", "Blank"])
            dlg2.setComboBoxEditable(False)
            dlg2.setStyleSheet(self._dialog_style())
            gang = "Single Gang"
            if dlg2.exec():
                gang = dlg2.textValue()

            dlg3 = QInputDialog(self.parent_panel)
            dlg3.setWindowTitle("Wall Plate Connectors")
            dlg3.setLabelText("Select connector type:")
            dlg3.setComboBoxItems([
                "XLR", "TRS 1/4\"", "TRS 3.5mm", "Speakon", "RJ45",
                "HDMI", "VGA", "USB", "Combo XLR/TRS", "Blank Insert", "Mixed"
            ])
            dlg3.setComboBoxEditable(False)
            dlg3.setStyleSheet(self._dialog_style())
            connector = ""
            if dlg3.exec():
                connector = dlg3.textValue()

            details = f"{gang}" + (f" / {connector}" if connector else "")

        elif material_type == "Mounting Bracket":
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Bracket Quantity")
            dlg.setLabelText("How many brackets?")
            dlg.setInputMode(QInputDialog.IntInput)
            dlg.setIntMinimum(1)
            dlg.setIntMaximum(100)
            dlg.setIntValue(1)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return None, None
            quantity = dlg.intValue()

            dlg2 = QInputDialog(self.parent_panel)
            dlg2.setWindowTitle("Bracket Type")
            dlg2.setLabelText("Select bracket type:")
            dlg2.setComboBoxItems(["Wall", "Ceiling", "Pole", "Truss", "Custom"])
            dlg2.setComboBoxEditable(False)
            dlg2.setStyleSheet(self._dialog_style())
            if dlg2.exec():
                details = dlg2.textValue()

        elif material_type == "Connector":
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Connector Quantity")
            dlg.setLabelText("How many connectors?")
            dlg.setInputMode(QInputDialog.IntInput)
            dlg.setIntMinimum(1)
            dlg.setIntMaximum(100)
            dlg.setIntValue(1)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return None, None
            quantity = dlg.intValue()

            dlg2 = QInputDialog(self.parent_panel)
            dlg2.setWindowTitle("Connector Type")
            dlg2.setLabelText("Select connector type:")
            dlg2.setComboBoxItems(["XLR", "TRS", "Speakon", "Terminal Block", "Custom"])
            dlg2.setComboBoxEditable(False)
            dlg2.setStyleSheet(self._dialog_style())
            if dlg2.exec():
                details = dlg2.textValue()

        elif material_type == "Conduit":
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Conduit Length")
            dlg.setLabelText("Enter length in feet:")
            dlg.setInputMode(QInputDialog.DoubleInput)
            dlg.setDoubleMinimum(0.1)
            dlg.setDoubleMaximum(1000)
            dlg.setDoubleValue(10)
            dlg.setDoubleDecimals(1)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return None, None
            details = f"{dlg.doubleValue()} ft"

        else:
            dlg = QInputDialog(self.parent_panel)
            dlg.setWindowTitle("Material Quantity")
            dlg.setLabelText(f"How many {material_type}s?")
            dlg.setInputMode(QInputDialog.IntInput)
            dlg.setIntMinimum(1)
            dlg.setIntMaximum(100)
            dlg.setIntValue(1)
            dlg.setStyleSheet(self._dialog_style())
            if not dlg.exec():
                return None, None
            quantity = dlg.intValue()

        return quantity, details

    def _find_material_item(self, material_type, details):
        """Find existing material item in the list"""
        root = self.materials_list.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == material_type and item.text(2) == details:
                return item
        return None

    def _add_new_material_item(self, material_type, quantity, details):
        """Add new material item to the list"""
        item = QTreeWidgetItem(self.materials_list)
        item.setText(0, material_type)
        item.setText(1, str(quantity))
        item.setText(2, details)

    def _update_material_in_zone(self, material_type, quantity, details):
        """Update or add material to the zone data"""
        if self.selected_zone_index is None:
            return

        zones_view = self._get_zones_view()
        if not zones_view or self.selected_zone_index >= len(zones_view.zones):
            return

        # Get current zone data
        zone = zones_view.zones[self.selected_zone_index]

        # Initialize materials list if it doesn't exist
        if 'materials' not in zone:
            zone['materials'] = []

        # Check if material already exists with matching type and details
        material_found = False
        for material in zone['materials']:
            if (material.get('type') == material_type and
                    material.get('details') == details):
                material['quantity'] = quantity
                material_found = True
                break

        # If material not found, add it
        if not material_found:
            zone['materials'].append({
                'type': material_type,
                'quantity': quantity,
                'details': details
            })

        # Signal zone modified
        self._emit_material_changed('materials', zone['materials'])

    def remove_selected_material(self):
        """Remove the currently selected material from the list"""
        if self.selected_zone_index is None:
            return

        selected_items = self.materials_list.selectedItems()
        if not selected_items:
            AlertDialog.show_info(self.parent_panel, "No Selection",
                                  "Please select a material to remove.")
            return

        # Get the selected material
        item = selected_items[0]
        material_type = item.text(0)
        details = item.text(2)

        # Confirm removal
        if not ConfirmDialog.ask(
            self.parent_panel,
            "Remove Material",
            f"Remove {material_type} from this zone?",
            confirm_text="Remove",
            danger=True,
        ):
            return

        # Remove from the list widget
        self._remove_material_item(item)

        # Remove from the zone data
        self._remove_material_from_zone_data(material_type, details)

    def _remove_material_item(self, item):
        """Remove material item from the list widget"""
        root = self.materials_list.invisibleRootItem()
        for i in range(root.childCount()):
            if root.child(i) == item:
                root.removeChild(item)
                break

    def _remove_material_from_zone_data(self, material_type, details):
        """Remove material from zone data"""
        zones_view = self._get_zones_view()
        if not zones_view or self.selected_zone_index >= len(zones_view.zones):
            return

        zone = zones_view.zones[self.selected_zone_index]
        if 'materials' not in zone:
            return

        materials = zone['materials']

        # Find and remove the matching material
        for i, material in enumerate(materials):
            if (material.get('type') == material_type and
                    material.get('details') == details):
                materials.pop(i)
                break

        # Signal zone modified
        self._emit_material_changed('materials', materials)

    def show_material_context_menu(self, position):
        """Show context menu for materials list"""
        if self.selected_zone_index is None:
            return

        # Get the item at the position
        item = self.materials_list.itemAt(position)
        if not item:
            return

        # Create context menu
        menu = QMenu()
        edit_action = menu.addAction("Edit Quantity")
        edit_details_action = menu.addAction("Edit Details")
        remove_action = menu.addAction("Remove Material")

        # Show the menu and get the selected action
        action = menu.exec_(self.materials_list.mapToGlobal(position))

        if action == edit_action:
            self.edit_material_quantity(item)
        elif action == edit_details_action:
            self.edit_material_details(item)
        elif action == remove_action:
            self.remove_material(item)

    def edit_material_quantity(self, item, column=None):
        """Edit the quantity of a material"""
        if self.selected_zone_index is None:
            return

        # Get material info from the item
        material_type = item.text(0)
        current_qty = int(item.text(1))
        details = item.text(2)

        dlg = QInputDialog(self.parent_panel)
        dlg.setWindowTitle("Edit Quantity")
        dlg.setLabelText(f"Enter quantity for {material_type}:")
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

        # Update the zone data
        self._update_material_in_zone(material_type, quantity, details)

    def edit_material_details(self, item):
        """Edit the details of a material"""
        if self.selected_zone_index is None:
            return

        # Get material info from the item
        material_type = item.text(0)
        quantity = int(item.text(1))
        current_details = item.text(2)

        dlg = QInputDialog(self.parent_panel)
        dlg.setWindowTitle("Edit Details")
        dlg.setLabelText(f"Enter details for {material_type}:")
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setTextValue(current_details)
        dlg.setStyleSheet(self._dialog_style())
        if not dlg.exec():
            return
        details = dlg.textValue()

        # Update the item in the list
        item.setText(2, details)

        # Remove old material and add with new details
        self._remove_material_from_zone_data(material_type, current_details)
        self._update_material_in_zone(material_type, quantity, details)

    def remove_material(self, item):
        """Remove a material from the zone"""
        if self.selected_zone_index is None:
            return

        material_type = item.text(0)
        details = item.text(2)

        # Confirm removal
        if not ConfirmDialog.ask(
            self.parent_panel,
            "Remove Material",
            f"Remove {material_type} from this zone?",
            confirm_text="Remove",
            danger=True,
        ):
            return

        # Remove from the list widget
        self._remove_material_item(item)

        # Remove from the zone data
        self._remove_material_from_zone_data(material_type, details)

    def load_materials_for_zone(self, zone):
        """Load materials for the given zone"""
        # Clear the materials list first
        self.materials_list.clear()

        # Update materials list with zone's materials
        if 'materials' in zone and zone['materials']:
            for material in zone['materials']:
                item = QTreeWidgetItem(self.materials_list)
                item.setText(0, material.get('type', 'Unknown'))
                item.setText(1, str(material.get('quantity', 1)))
                item.setText(2, material.get('details', ''))

    def clear_materials(self):
        """Clear the materials list"""
        if self.materials_list:
            self.materials_list.clear()

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

    def _emit_material_changed(self, property_name, value):
        """Emit material changed signal"""
        if hasattr(self.parent_panel, 'user_action'):
            self.parent_panel.user_action.emit(
                'zone', self.selected_zone_index, property_name, value
            )