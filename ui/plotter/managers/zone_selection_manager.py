import logging
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QBrush, QColor, QFont


class ZoneSelectionManager(QObject):
    """Manages zone tree display and selection logic"""

    # Signals
    zone_selected = Signal(dict)  # zone_data
    zone_selection_cleared = Signal()

    def __init__(self, tree_widget, parent=None):
        """Initialize zone selection manager

        Args:
            tree_widget (QTreeWidget): The zone tree widget to manage
            parent: Parent object
        """
        super().__init__(parent)
        self.tree_widget = tree_widget
        self.logger = logging.getLogger(__name__)

        # Current state
        self.current_zones = []
        self.selected_zone = None
        self._in_zone_selection = False
        self._in_refresh = False

        # Connect tree widget signals
        self.tree_widget.itemSelectionChanged.connect(self._on_tree_selection_changed)

        # Configure tree widget
        self._configure_tree_widget()

    def _configure_tree_widget(self):
        """Configure the tree widget appearance and behavior"""
        self.tree_widget.setHeaderLabels(["Name", "Area (ft²)"])
        self.tree_widget.setColumnWidth(0, 150)
        self.tree_widget.setAlternatingRowColors(True)

    def load_zones(self, zones):
        """Load and display zones in the tree

        Args:
            zones (list): List of zone data dictionaries
        """
        if self._in_refresh:
            self.logger.debug("Already refreshing zones")
            return

        self._in_refresh = True
        try:
            self.logger.debug(f"Loading {len(zones)} zones into tree")
            self.current_zones = zones.copy()
            self._update_tree_display()

        finally:
            self._in_refresh = False

    def _update_tree_display(self):
        """Update the tree widget display with current zones"""
        self.tree_widget.clear()

        if not self.current_zones:
            return

        # Group zones by room
        rooms_dict = self._group_zones_by_room()

        # Find scale manager to check calibration
        scale_manager = self._find_scale_manager()
        is_scale_calibrated = scale_manager and scale_manager.is_calibrated()

        # Add zones with rooms first
        for room_name in sorted(rooms_dict.keys()):
            if room_name:  # Only process zones with room names
                self._add_room_to_tree(room_name, rooms_dict[room_name], is_scale_calibrated)

        # Add unassigned zones
        if '' in rooms_dict and rooms_dict['']:
            self._add_unassigned_zones_to_tree(rooms_dict[''], is_scale_calibrated)

        # Expand all items by default
        self.tree_widget.expandAll()

    def _group_zones_by_room(self):
        """Group zones by room name

        Returns:
            dict: Dictionary of room_name -> list of zones
        """
        rooms_dict = {}

        # First pass: identify all rooms
        for zone in self.current_zones:
            room_name = zone.get('room_name', '')
            if room_name not in rooms_dict:
                rooms_dict[room_name] = []
            rooms_dict[room_name].append(zone)

        return rooms_dict

    def _add_room_to_tree(self, room_name, zones, is_scale_calibrated):
        """Add a room and its zones to the tree

        Args:
            room_name (str): Name of the room
            zones (list): List of zones in this room
            is_scale_calibrated (bool): Whether scale is calibrated
        """
        # Create room item as parent
        room_item = QTreeWidgetItem(self.tree_widget)
        room_item.setText(0, room_name)
        room_item.setBackground(0, QBrush(QColor(240, 240, 240)))
        room_item.setBackground(1, QBrush(QColor(240, 240, 240)))

        # Make room name bold
        font = QFont()
        font.setBold(True)
        room_item.setFont(0, font)

        # Add zones for this room
        for zone in zones:
            self._add_zone_to_tree(zone, room_item, is_scale_calibrated)

    def _add_unassigned_zones_to_tree(self, zones, is_scale_calibrated):
        """Add unassigned zones to the tree under 'Unassigned' header

        Args:
            zones (list): List of unassigned zones
            is_scale_calibrated (bool): Whether scale is calibrated
        """
        # Create unassigned header
        unassigned_item = QTreeWidgetItem(self.tree_widget)
        unassigned_item.setText(0, "Unassigned")
        unassigned_item.setBackground(0, QBrush(QColor(240, 240, 240)))
        unassigned_item.setBackground(1, QBrush(QColor(240, 240, 240)))

        # Make unassigned header bold
        font = QFont()
        font.setBold(True)
        unassigned_item.setFont(0, font)

        # Add unassigned zones
        for zone in zones:
            self._add_zone_to_tree(zone, unassigned_item, is_scale_calibrated)

    def _add_zone_to_tree(self, zone, parent_item, is_scale_calibrated):
        """Add a single zone to the tree

        Args:
            zone (dict): Zone data
            parent_item (QTreeWidgetItem): Parent tree item
            is_scale_calibrated (bool): Whether scale is calibrated
        """
        zone_idx = self.current_zones.index(zone)

        # Create zone item
        zone_item = QTreeWidgetItem(parent_item)
        zone_item.setText(0, zone.get('name', f"Zone {zone_idx + 1}"))

        # Add area or message
        if is_scale_calibrated and 'area' in zone and zone['area'] is not None:
            zone_item.setText(1, f"{zone['area']:.2f}")
        else:
            zone_item.setText(1, "Scale not set")

        # Store zone index for selection
        zone_item.setData(0, Qt.UserRole, ('zone', zone_idx))

        # Color the zone item
        color_index = zone.get('color_index', zone_idx % 6)
        zone_colors = [
            QColor(230, 255, 230),  # Light green
            QColor(230, 230, 255),  # Light blue
            QColor(255, 230, 230),  # Light red
            QColor(255, 255, 230),  # Light yellow
            QColor(255, 240, 220),  # Light orange
            QColor(250, 230, 250),  # Light purple
        ]
        zone_item.setBackground(0, QBrush(zone_colors[color_index % len(zone_colors)]))
        zone_item.setBackground(1, QBrush(zone_colors[color_index % len(zone_colors)]))

    def _auto_select_first_zone(self):
        """Automatically select the first available zone"""
        self._in_zone_selection = True
        try:
            # Find the first actual zone item (not a header)
            for i in range(self.tree_widget.topLevelItemCount()):
                top_item = self.tree_widget.topLevelItem(i)

                # If this is a room with child zones
                if top_item.childCount() > 0:
                    first_zone = top_item.child(0)
                    self.tree_widget.setCurrentItem(first_zone)
                    break

                # If this is a direct zone item (not a room)
                item_data = top_item.data(0, Qt.UserRole)
                if item_data and item_data[0] == 'zone':
                    self.tree_widget.setCurrentItem(top_item)
                    break
        finally:
            self._in_zone_selection = False

    def _on_tree_selection_changed(self):
        """Handle selection changes in the zone tree widget"""
        if self._in_zone_selection:
            return

        try:
            selected_items = self.tree_widget.selectedItems()
            if not selected_items:
                self.selected_zone = None
                self.zone_selection_cleared.emit()
                return

            item = selected_items[0]
            item_data = item.data(0, Qt.UserRole)

            if not item_data:
                # This is a room header, not a zone
                return

            item_type, index = item_data

            # Make sure the index is valid
            if item_type == 'zone' and 0 <= index < len(self.current_zones):
                zone = self.current_zones[index]

                # Ensure the zone has an ID
                if 'id' not in zone or not zone['id']:
                    import uuid
                    zone['id'] = str(uuid.uuid4())
                    self.logger.debug(f"Generated missing ID for zone: {zone.get('name', 'Unnamed')}")
                    # Update the zone in the current list
                    self.current_zones[index] = zone

                # Make sure the ID is a string
                zone['id'] = str(zone['id'])

                self.selected_zone = zone
                self.zone_selected.emit(zone)

                self.logger.debug(f"Selected zone: {zone.get('name', 'Unnamed')} (index {index})")
            else:
                self.logger.debug(f"Invalid selection data: {item_type}, {index}")

        except Exception as e:
            self.logger.error(f"Error in zone selection: {e}", exc_info=True)

    def get_selected_zone(self):
        """Get the currently selected zone

        Returns:
            dict: Selected zone data or None
        """
        return self.selected_zone

    def select_zone_by_id(self, zone_id):
        """Select a zone by its ID

        Args:
            zone_id (str): Zone ID to select

        Returns:
            bool: True if zone was found and selected
        """
        if not zone_id:
            return False

        # Find zone with matching ID
        for i, zone in enumerate(self.current_zones):
            if str(zone.get('id', '')) == str(zone_id):
                # Find the tree item for this zone
                return self._select_zone_by_index(i)

        return False

    def _select_zone_by_index(self, index):
        """Select a zone by its index in the current_zones list

        Args:
            index (int): Index of zone to select

        Returns:
            bool: True if zone was found and selected
        """
        # Search through all tree items to find the one with this index
        for i in range(self.tree_widget.topLevelItemCount()):
            top_item = self.tree_widget.topLevelItem(i)

            # Check if this top-level item is a zone
            item_data = top_item.data(0, Qt.UserRole)
            if item_data and item_data[0] == 'zone' and item_data[1] == index:
                self.tree_widget.setCurrentItem(top_item)
                return True

            # Check child items
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                item_data = child_item.data(0, Qt.UserRole)
                if item_data and item_data[0] == 'zone' and item_data[1] == index:
                    self.tree_widget.setCurrentItem(child_item)
                    return True

        return False

    def clear_selection(self):
        """Clear the current zone selection"""
        self.tree_widget.clearSelection()
        self.selected_zone = None
        self.zone_selection_cleared.emit()

    def refresh_zones(self, zones):
        """Refresh the zone display with new data

        Args:
            zones (list): Updated list of zones
        """
        current_selection_id = None
        if self.selected_zone and 'id' in self.selected_zone:
            current_selection_id = self.selected_zone['id']

        # Reload zones
        self.load_zones(zones)

        # Restore selection if possible
        if current_selection_id:
            self.select_zone_by_id(current_selection_id)

    def get_zone_count(self):
        """Get the number of zones currently loaded

        Returns:
            int: Number of zones
        """
        return len(self.current_zones)

    def get_all_zones(self):
        """Get all currently loaded zones

        Returns:
            list: Copy of current zones list
        """
        return self.current_zones.copy()

    def _find_scale_manager(self):
        """Find the scale manager in the parent hierarchy

        Returns:
            ScaleManager: Scale manager instance or None
        """
        parent = self.parent()

        while parent:
            # Check various possible locations for scale manager
            if hasattr(parent, 'scale_manager'):
                return parent.scale_manager
            if hasattr(parent, 'project_manager'):
                if hasattr(parent.project_manager, 'zones_view'):
                    if hasattr(parent.project_manager.zones_view, 'scale_manager'):
                        return parent.project_manager.zones_view.scale_manager
                    if (hasattr(parent.project_manager.zones_view, 'canvas') and
                            hasattr(parent.project_manager.zones_view.canvas, 'scale_manager')):
                        return parent.project_manager.zones_view.canvas.scale_manager

            # Move up the hierarchy
            if hasattr(parent, 'parent') and callable(parent.parent):
                parent = parent.parent()
            else:
                break

        return None