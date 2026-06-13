from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QPushButton)
from PySide6.QtCore import Signal


class SpeakerProfilePanel(QWidget):
    """Panel for selecting and managing speaker profiles"""

    # Signals
    profile_selected = Signal(object)  # profile object
    profile_selection_cleared = Signal()
    placement_requested = Signal(object)  # profile object for placement
    profile_library_changed = Signal()  # when profiles are added/removed/edited

    def __init__(self, profile_data_manager, parent=None):
        """Initialize the speaker profile panel

        Args:
            profile_data_manager: The SpeakerProfileManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.profile_data_manager = profile_data_manager
        self.speaker_profile_ui_manager = None  # Will be set after creation

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Speaker profile list (flat, no QGroupBox wrapper)
        self.profile_list = QListWidget()
        layout.addWidget(self.profile_list)

        # Profile buttons
        button_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create Profile")
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)  # Disabled until selection
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.edit_btn)
        layout.addLayout(button_layout)

        # Add placement button
        self.place_btn = QPushButton("Place Speaker")
        self.place_btn.setEnabled(False)  # Disabled until selection
        layout.addWidget(self.place_btn)

        layout.addStretch(1)  # Push everything to top

    def setup_manager(self, speaker_profile_ui_manager):
        """Setup the UI manager after creation

        Args:
            speaker_profile_ui_manager: The SpeakerProfileUIManager instance
        """
        self.speaker_profile_ui_manager = speaker_profile_ui_manager

        # Connect the manager's signals to our signals
        self.speaker_profile_ui_manager.profile_selected.connect(self.profile_selected.emit)
        self.speaker_profile_ui_manager.profile_selection_cleared.connect(self.profile_selection_cleared.emit)
        self.speaker_profile_ui_manager.placement_requested.connect(self.placement_requested.emit)
        self.speaker_profile_ui_manager.profile_library_changed.connect(self.profile_library_changed.emit)

    def get_profile_list_widget(self):
        """Get the profile list widget for the manager"""
        return self.profile_list

    def get_create_button(self):
        """Get the create button for the manager"""
        return self.create_btn

    def get_edit_button(self):
        """Get the edit button for the manager"""
        return self.edit_btn

    def get_place_button(self):
        """Get the place button for the manager"""
        return self.place_btn

    def set_enabled(self, enabled):
        """Enable or disable the panel"""
        self.setEnabled(enabled)
