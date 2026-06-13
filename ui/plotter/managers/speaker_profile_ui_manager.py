import logging
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QDialog, QStyle
from PySide6.QtCore import QObject, Signal, Qt

from ui.dialogs.speaker_profile_dialog import SpeakerProfileDialog
from ui.dialogs.alert_dialog import AlertDialog


class SpeakerProfileUIManager(QObject):
    """Manages speaker profile UI interactions, selection, and placement integration"""

    # Signals
    profile_selected = Signal(object)  # profile object
    profile_selection_cleared = Signal()
    placement_requested = Signal(object)  # profile object for placement
    profile_library_changed = Signal()  # when profiles are added/removed/edited

    def __init__(self, profile_list_widget, profile_manager, create_btn, edit_btn, place_btn, parent=None):
        """Initialize speaker profile UI management

        Args:
            profile_list_widget (QListWidget): The profile list widget
            profile_manager (SpeakerProfileManager): The data/persistence manager
            create_btn (QPushButton): Create profile button
            edit_btn (QPushButton): Edit profile button
            place_btn (QPushButton): Place speaker button
            parent: Parent object
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # UI components
        self.profile_list = profile_list_widget
        self.profile_manager = profile_manager  # This is your existing SpeakerProfileManager
        self.create_btn = create_btn
        self.edit_btn = edit_btn
        self.place_btn = place_btn

        # Current state
        self.selected_profile = None
        self.selected_profile_key = None

        # Configure profile list widget
        self._configure_profile_list()

        # Connect UI signals
        self._connect_ui_signals()

        # Load profiles initially
        self.refresh_profile_list()

    def _configure_profile_list(self):
        """Configure the profile list widget"""
        self.profile_list.setAlternatingRowColors(True)

    def _connect_ui_signals(self):
        """Connect UI widget signals"""
        self.profile_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        self.create_btn.clicked.connect(self._on_create_profile)
        self.edit_btn.clicked.connect(self._on_edit_profile)
        self.place_btn.clicked.connect(self._on_place_speaker)

    def refresh_profile_list(self):
        """Refresh the profile list from the profile manager"""
        self.logger.debug("Refreshing profile list")

        # Store current selection
        current_key = self.selected_profile_key

        # Clear list
        self.profile_list.clear()
        self.selected_profile = None
        self.selected_profile_key = None

        # Get profiles from the data manager
        profiles = self.profile_manager.list_profiles()

        # Add to list view
        for key, profile in profiles:
            item = QListWidgetItem(f"{profile.manufacturer} - {profile.name}")
            item.setData(Qt.UserRole, key)  # Store profile key as data

            # Add icon based on speaker type
            if profile.model_type == "Pendant":
                item.setIcon(self.parent().style().standardIcon(QStyle.SP_ArrowUp))
            else:  # In-Ceiling (default)
                item.setIcon(self.parent().style().standardIcon(QStyle.SP_ArrowDown))

            self.profile_list.addItem(item)

        # Restore selection if possible
        if current_key:
            self.select_profile_by_key(current_key)

        # Update button states
        self._update_button_states()

        self.logger.debug(f"Loaded {len(profiles)} profiles into list")

    def _on_list_selection_changed(self):
        """Handle selection changes in the profile list"""
        # Get selected items
        items = self.profile_list.selectedItems()
        if not items:
            self.selected_profile = None
            self.selected_profile_key = None
            self.profile_selection_cleared.emit()
            self._update_button_states()
            return

        # Get profile key from item data
        key = items[0].data(Qt.UserRole)

        # Get profile from the data manager
        profile = self.profile_manager.get_profile(key)
        if profile:
            self.selected_profile = profile
            self.selected_profile_key = key
            self.profile_selected.emit(profile)
            self.logger.debug(f"Selected profile: {profile.manufacturer} - {profile.name}")
        else:
            self.logger.warning(f"Profile not found for key: {key}")
            self.selected_profile = None
            self.selected_profile_key = None
            self.profile_selection_cleared.emit()

        self._update_button_states()

    def _update_button_states(self):
        """Update button enabled/disabled states based on selection"""
        has_selection = self.selected_profile is not None

        # Create button is always enabled (assuming UI is enabled)
        # Edit and place buttons depend on having a selection
        self.edit_btn.setEnabled(has_selection)
        self.place_btn.setEnabled(has_selection)

    def _on_create_profile(self):
        """Handle create profile button click"""
        dialog = SpeakerProfileDialog(self.parent())

        if dialog.exec() == QDialog.Accepted:
            # Get profile from dialog
            profile = dialog.get_profile()

            # Add to data manager
            if self.profile_manager.add_profile(profile):
                # Refresh the list
                self.refresh_profile_list()

                # Select the new profile
                new_key = f"{profile.manufacturer}_{profile.name}"
                self.select_profile_by_key(new_key)

                # Emit library changed signal
                self.profile_library_changed.emit()

                AlertDialog.show_info(self.parent(), "Profile Created",
                                     f"Created '{profile.name}' successfully.")
                self.logger.info(f"Created new profile: {profile.manufacturer} - {profile.name}")
            else:
                AlertDialog.show_error(self.parent(), "Creation Error",
                                       "Failed to add profile to library.")
                self.logger.error(f"Failed to create profile: {profile.manufacturer} - {profile.name}")

    def _on_edit_profile(self):
        """Handle edit profile button click"""
        if not self.selected_profile:
            return

        # Show profile dialog with selected profile
        dialog = SpeakerProfileDialog(self.parent(), self.selected_profile)

        if dialog.exec() == QDialog.Accepted:
            # Get updated profile from dialog
            updated_profile = dialog.get_profile()

            # Generate keys for comparison
            old_key = self.selected_profile_key
            new_key = f"{updated_profile.manufacturer}_{updated_profile.name}"

            # Remove old profile if name or manufacturer changed
            if old_key != new_key:
                self.profile_manager.remove_profile(old_key)

            # Add updated profile
            if self.profile_manager.add_profile(updated_profile):
                # Refresh the list
                self.refresh_profile_list()

                # Select the updated profile
                self.select_profile_by_key(new_key)

                # Emit library changed signal
                self.profile_library_changed.emit()

                AlertDialog.show_info(self.parent(), "Profile Updated",
                                     f"Updated '{updated_profile.name}' successfully.")
                self.logger.info(f"Updated profile: {updated_profile.manufacturer} - {updated_profile.name}")
            else:
                AlertDialog.show_error(self.parent(), "Update Error",
                                       "Failed to update profile.")
                self.logger.error(f"Failed to update profile: {updated_profile.manufacturer} - {updated_profile.name}")

    def _on_place_speaker(self):
        """Handle place speaker button click"""
        if not self.selected_profile:
            AlertDialog.show_warning(self.parent(), "No Speaker Selected",
                                     "Please select a speaker profile first.")
            return

        # Emit placement requested signal
        self.placement_requested.emit(self.selected_profile)
        self.logger.debug(
            f"Placement requested for profile: {self.selected_profile.manufacturer} - {self.selected_profile.name}")

    def select_profile_by_key(self, key):
        """Select a profile by its key

        Args:
            key (str): Profile key to select

        Returns:
            bool: True if profile was found and selected
        """
        if not key:
            return False

        # Find the list item with this key
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            if item.data(Qt.UserRole) == key:
                self.profile_list.setCurrentItem(item)
                return True

        return False

    def get_selected_profile(self):
        """Get the currently selected profile

        Returns:
            SpeakerProfile: Selected profile or None
        """
        return self.selected_profile

    def get_selected_profile_key(self):
        """Get the currently selected profile key

        Returns:
            str: Selected profile key or None
        """
        return self.selected_profile_key

    def clear_selection(self):
        """Clear the current profile selection"""
        self.profile_list.clearSelection()
        self.selected_profile = None
        self.selected_profile_key = None
        self.profile_selection_cleared.emit()
        self._update_button_states()

    def set_ui_enabled(self, enabled):
        """Enable or disable all UI components

        Args:
            enabled (bool): Whether to enable the UI
        """
        self.profile_list.setEnabled(enabled)
        self.create_btn.setEnabled(enabled)

        # Edit and place buttons also depend on having a selection
        has_selection = self.selected_profile is not None
        self.edit_btn.setEnabled(enabled and has_selection)
        self.place_btn.setEnabled(enabled and has_selection)

    def get_profile_count(self):
        """Get the number of profiles in the list

        Returns:
            int: Number of profiles
        """
        return self.profile_list.count()