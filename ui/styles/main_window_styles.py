"""
Professional main window styling for Audio System Designer.
Clean tab styling that matches the toolbar aesthetic.
"""

from .base_styles import Colors, Typography


class ProMainWindowStyles:
    """Professional main window styling - matches toolbar design"""

    @staticmethod
    def get_tab_widget_style():
        """Professional tab widget styling"""
        return f"""
            QTabWidget {{
                background-color: {Colors.GRAY_100};
                border: none;
            }}

            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-top: none;
                background-color: {Colors.WHITE};
                margin: 0px;
            }}

            QTabWidget::tab-bar {{
                alignment: left;
                background-color: {Colors.GRAY_100};
            }}

            QTabBar {{
                background-color: {Colors.GRAY_100};
                border: none;
            }}

            QTabBar::tab {{
                background-color: transparent;
                border: 1px solid transparent;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 20px;
                margin-right: 2px;
                margin-top: 4px;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-weight: 500;
                font-size: 12px;
                color: {Colors.TEXT_SECONDARY};
                min-width: 80px;
            }}

            QTabBar::tab:hover:!selected {{
                background-color: {Colors.GRAY_100};
                border-color: {Colors.GRAY_200};
                color: {Colors.TEXT_PRIMARY};
            }}

            QTabBar::tab:selected {{
                background-color: {Colors.WHITE};
                color: {Colors.PRIMARY};
                border-color: {Colors.BORDER_MEDIUM};
                border-bottom: 1px solid {Colors.WHITE};
                font-weight: 600;
                margin-bottom: -1px;
            }}

            QTabBar::tab:disabled {{
                color: {Colors.GRAY_500};
                background-color: transparent;
            }}
        """

    @staticmethod
    def get_status_bar_style():
        """Professional status bar styling"""
        return f"""
            QStatusBar {{
                background-color: {Colors.GRAY_100};
                border-top: 1px solid {Colors.BORDER_MEDIUM};
                padding: 4px 8px;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: 11px;
                color: {Colors.TEXT_SECONDARY};
                min-height: 24px;
                max-height: 24px;
            }}

            QStatusBar QLabel {{
                background-color: transparent;
                padding: 2px 6px;
                border-radius: 3px;
                color: {Colors.TEXT_SECONDARY};
            }}

            QStatusBar QLabel[text="Unsaved Changes"] {{
                background-color: {Colors.WARNING_BG};
                color: {Colors.WARNING_TEXT_DARK};
                border: 1px solid {Colors.WARNING};
            }}

            QStatusBar QLabel[text="Ready"] {{
                color: {Colors.SUCCESS};
            }}
        """

    @staticmethod
    def get_main_window_style():
        """Professional main window background"""
        return f"""
            QMainWindow {{
                background-color: {Colors.GRAY_100};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
        """

    @staticmethod
    def get_menu_bar_style():
        """Professional menu bar styling"""
        return f"""
            QMenuBar {{
                background-color: {Colors.GRAY_100};
                border-bottom: 1px solid {Colors.BORDER_MEDIUM};
                padding: 2px;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: 12px;
                color: {Colors.TEXT_PRIMARY};
            }}

            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
                margin: 2px;
            }}

            QMenuBar::item:selected {{
                background-color: {Colors.GRAY_100};
                border: 1px solid {Colors.GRAY_200};
            }}

            QMenuBar::item:pressed {{
                background-color: {Colors.PRIMARY_LIGHT};
                border: 1px solid {Colors.PRIMARY};
            }}

            QMenu {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 6px;
                padding: 4px;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: 12px;
                color: {Colors.TEXT_PRIMARY};
            }}

            QMenu::item {{
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
                margin: 1px;
            }}

            QMenu::item:selected {{
                background-color: {Colors.GRAY_100};
                border: 1px solid {Colors.GRAY_200};
            }}

            QMenu::separator {{
                height: 1px;
                background-color: {Colors.GRAY_200};
                margin: 4px 8px;
            }}
        """


class MainWindowStyleManager:
    """Manager for applying professional styling to the main window"""

    @staticmethod
    def apply_professional_styling(main_window):
        """Apply all professional styling to the main window"""

        # Combine all styles
        complete_style = (
                ProMainWindowStyles.get_main_window_style() +
                ProMainWindowStyles.get_tab_widget_style() +
                ProMainWindowStyles.get_status_bar_style() +
                ProMainWindowStyles.get_menu_bar_style()
        )

        # Apply to main window
        main_window.setStyleSheet(complete_style)

    @staticmethod
    def apply_compact_layout(main_window):
        """Apply space-saving layout settings"""

        # Get the tab widget and make it more compact
        if hasattr(main_window, 'tab_widget') and main_window.tab_widget:
            tab_widget = main_window.tab_widget

            # Make tabs more compact
            tab_bar = tab_widget.tabBar()
            if tab_bar:
                tab_bar.setExpanding(False)  # Don't expand tabs to fill width

        # Make status bar more compact
        if hasattr(main_window, 'status_bar') and main_window.status_bar:
            main_window.status_bar.setMaximumHeight(28)

    @staticmethod
    def set_professional_window_properties(main_window):
        """Set professional window properties"""

        # Set a professional window title
        current_title = main_window.windowTitle()
        if current_title == "Audio System Designer":
            # Keep as is, or could add version/project info later
            pass

        # Set minimum size for professional appearance
        main_window.setMinimumSize(1200, 800)  # Slightly larger for professional tools


# Example usage for main_window.py
def apply_professional_main_window_styling(main_window):
    """
    Convenience function to apply all professional styling to main window.
    Call this in main_window.py after UI initialization.
    """
    MainWindowStyleManager.apply_professional_styling(main_window)
    MainWindowStyleManager.apply_compact_layout(main_window)
    MainWindowStyleManager.set_professional_window_properties(main_window)