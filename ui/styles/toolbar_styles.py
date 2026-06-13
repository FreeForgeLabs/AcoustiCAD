"""
Professional toolbar styling for Audio System Designer.
Clean, minimal design inspired by CAD and professional software.
"""

from .base_styles import Colors, Typography, Spacing, BorderRadius


class ProToolbarStyles:
    """Professional toolbar styling - clean and functional"""

    @staticmethod
    def get_toolbar_style():
        """Professional toolbar styling"""
        return f"""
            QToolBar {{
                background-color: {Colors.GRAY_100};
                border: none;
                border-bottom: 1px solid {Colors.BORDER_MEDIUM};
                padding: 6px;
                spacing: 2px;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                min-height: 40px;
                max-height: 40px;
            }}

            QToolBar::separator {{
                background-color: {Colors.BORDER_MEDIUM};
                width: 1px;
                margin: 8px 4px;
            }}
        """

    @staticmethod
    def get_button_style():
        """Professional toolbar button styling"""
        return f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px 10px;
                margin: 1px;
                color: {Colors.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: 11px;
                font-weight: 500;
                text-align: center;
                min-width: 60px;
                min-height: 28px;
                max-height: 28px;
            }}

            QToolButton:hover:!pressed {{
                background-color: {Colors.GRAY_100};
                border-color: {Colors.GRAY_200};
            }}

            QToolButton:pressed {{
                background-color: {Colors.PRIMARY_LIGHT};
                border-color: {Colors.PRIMARY};
            }}

            QToolButton:checked {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
                font-weight: 600;
            }}

            QToolButton:disabled {{
                background-color: transparent;
                color: {Colors.GRAY_500};
                border-color: transparent;
            }}
        """


class ProToolbarSections:
    """Professional toolbar sections with clean text-only labels"""

    # File Operations
    FILE_ACTIONS = {
        "load_background": {
            "text": "Load Floorplan",
            "tooltip": "Load a floorplan image for drawing zones"
        },
        "save": {
            "text": "Save",
            "tooltip": "Save the current project (Ctrl+S)"
        },
        "export": {
            "text": "Export",
            "tooltip": "Export the view as an image"
        }
    }

    # Drawing Tools
    DRAWING_ACTIONS = {
        "calibrate": {
            "text": "Calibrate Scale",
            "tooltip": "Calibrate the scale of the drawing"
        },
        "draw_zone": {
            "text": "Draw Zone",
            "tooltip": "Draw a new zone on the background"
        },
        "line_color": {
            "text": "Line Color",
            "tooltip": "Change drawing line color"
        }
    }

    # View Controls
    VIEW_ACTIONS = {
        "toggle_grid": {
            "text": "Grid",
            "tooltip": "Show/hide drawing grid"
        },
        "snap_grid": {
            "text": "Snap",
            "tooltip": "Enable/disable snapping to grid"
        },
        "grid_size": {
            "text": "Grid Size",
            "tooltip": "Set grid resolution in pixels"
        }
    }

    # Zoom Controls
    ZOOM_ACTIONS = {
        "zoom_in": {
            "text": "Zoom In",
            "tooltip": "Zoom in (Ctrl++)"
        },
        "zoom_out": {
            "text": "Zoom Out",
            "tooltip": "Zoom out (Ctrl+-)"
        },
        "zoom_reset": {
            "text": "Reset Zoom",
            "tooltip": "Reset zoom to 100% (Ctrl+0)"
        },
        "zoom_fit": {
            "text": "Fit View",
            "tooltip": "Fit content to view (Ctrl+F)"
        }
    }

    # Clear Operations
    CLEAR_ACTIONS = {
        "clear_zones": {
            "text": "Clear Zones",
            "tooltip": "Clear only the zones, keep background"
        },
        "clear_all": {
            "text": "Clear All",
            "tooltip": "Clear all content (zones and background)"
        }
    }


class ProToolbarBuilder:
    """Builder for professional toolbars"""

    def __init__(self, toolbar):
        self.toolbar = toolbar
        self.actions = {}

    def add_section(self, section_actions, add_separator=True):
        """Add a section of actions to the toolbar"""
        if add_separator and self.actions:  # Add separator before new sections (except first)
            self.toolbar.addSeparator()

        for action_key, action_config in section_actions.items():
            action = self.toolbar.addAction(action_config["text"])
            action.setStatusTip(action_config["tooltip"])
            self.actions[action_key] = action

        return self.actions

    def get_action(self, action_key):
        """Get a specific action by key"""
        return self.actions.get(action_key)

    def set_action_checkable(self, action_key, checkable=True, checked=False):
        """Make an action checkable and set its state"""
        action = self.get_action(action_key)
        if action:
            action.setCheckable(checkable)
            action.setChecked(checked)

    def set_action_enabled(self, action_key, enabled=True):
        """Enable or disable an action"""
        action = self.get_action(action_key)
        if action:
            action.setEnabled(enabled)

    def apply_professional_styling(self):
        """Apply professional styling to the toolbar"""
        style = ProToolbarStyles.get_toolbar_style() + ProToolbarStyles.get_button_style()
        self.toolbar.setStyleSheet(style)


class ProToolbarFactory:
    """Factory for creating professional toolbars"""

    @staticmethod
    def create_zones_toolbar(toolbar):
        """Create a professional zones toolbar"""
        builder = ProToolbarBuilder(toolbar)

        # Add sections with minimal separators
        builder.add_section(ProToolbarSections.FILE_ACTIONS, False)  # No separator for first
        builder.add_section(ProToolbarSections.DRAWING_ACTIONS)
        builder.add_section(ProToolbarSections.VIEW_ACTIONS)
        builder.add_section(ProToolbarSections.ZOOM_ACTIONS)
        builder.add_section(ProToolbarSections.CLEAR_ACTIONS)

        # Configure checkable actions
        builder.set_action_checkable("toggle_grid", True, True)
        builder.set_action_checkable("snap_grid", True, True)

        # Initially disable draw zone until background is loaded
        builder.set_action_enabled("draw_zone", False)

        # Apply professional styling
        builder.apply_professional_styling()

        return builder


# ---------------------------------------------------------------------------
# Legacy / alias classes kept for __init__.py compatibility
# ---------------------------------------------------------------------------

class ModernToolbarStyles(ProToolbarStyles):
    """Legacy alias for ProToolbarStyles."""
    pass


class ToolbarSections(ProToolbarSections):
    """Legacy alias for ProToolbarSections."""
    pass


class ToolbarBuilder(ProToolbarBuilder):
    """Legacy alias for ProToolbarBuilder."""
    pass


class ToolbarThemes:
    """Legacy stub — not implemented."""
    pass


class ToolbarFactory(ProToolbarFactory):
    """Legacy alias for ProToolbarFactory."""
    pass