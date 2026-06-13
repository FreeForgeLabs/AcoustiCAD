"""
Component styling system for Audio System Designer.
Reusable styles for buttons, inputs, cards, and other UI components.
"""

from .base_styles import Colors, Typography, Spacing, BorderRadius, Shadows, Transitions, Icons


class ButtonStyles:
    """Modern button styling system"""

    @staticmethod
    def get_base_button_style():
        """Base button styling shared by all button variants"""
        return f"""
            QPushButton {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                border-radius: {BorderRadius.MD};
                padding: {Spacing.BASE} {Spacing.LG};
                border: 1px solid transparent;
                text-align: center;
                min-width: 80px;
            }}
        """

    @staticmethod
    def get_primary_button_style():
        """Primary button styling (main actions)"""
        return ButtonStyles.get_base_button_style() + f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border-color: {Colors.PRIMARY};
            }}

            QPushButton:hover:!pressed {{
                background-color: {Colors.PRIMARY_HOVER};
                border-color: {Colors.PRIMARY_HOVER};
            }}

            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_ACTIVE};
                border-color: {Colors.PRIMARY_ACTIVE};
            }}

            QPushButton:disabled {{
                background-color: {Colors.GRAY_400};
                color: {Colors.TEXT_MUTED};
                border-color: {Colors.GRAY_400};
            }}
        """

    @staticmethod
    def get_secondary_button_style():
        """Secondary button styling"""
        return ButtonStyles.get_base_button_style() + f"""
            QPushButton {{
                background-color: {Colors.GRAY_100};
                color: {Colors.TEXT_PRIMARY};
                border-color: {Colors.BORDER_MEDIUM};
            }}

            QPushButton:hover:!pressed {{
                background-color: {Colors.GRAY_200};
                border-color: {Colors.BORDER_DARK};
            }}

            QPushButton:pressed {{
                background-color: {Colors.GRAY_300};
                border-color: {Colors.BORDER_DARK};
            }}

            QPushButton:disabled {{
                background-color: {Colors.GRAY_200};
                color: {Colors.TEXT_MUTED};
                border-color: {Colors.BORDER_LIGHT};
            }}
        """

    @staticmethod
    def get_icon_button_style():
        """Icon button styling (for toolbar buttons)"""
        return f"""
            QAction {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
            }}

            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: {BorderRadius.MD};
                padding: {Spacing.BASE};
                margin: {Spacing.XS};
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                min-width: 32px;
                min-height: 32px;
            }}

            QToolButton:hover:!pressed {{
                background-color: {Colors.GRAY_100};
                border-color: {Colors.BORDER_LIGHT};
            }}

            QToolButton:pressed {{
                background-color: {Colors.GRAY_200};
                border-color: {Colors.BORDER_MEDIUM};
            }}

            QToolButton:checked {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}

            QToolButton:disabled {{
                background-color: transparent;
                color: {Colors.TEXT_MUTED};
                border-color: transparent;
            }}
        """

    @staticmethod
    def get_toggle_button_style():
        """Toggle button styling (for checkable buttons)"""
        return ButtonStyles.get_base_button_style() + f"""
            QPushButton {{
                background-color: {Colors.GRAY_100};
                color: {Colors.TEXT_PRIMARY};
                border-color: {Colors.BORDER_MEDIUM};
            }}

            QPushButton:hover:!pressed:!checked {{
                background-color: {Colors.GRAY_200};
                border-color: {Colors.BORDER_DARK};
            }}

            QPushButton:checked {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border-color: {Colors.PRIMARY};
            }}

            QPushButton:checked:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                border-color: {Colors.PRIMARY_HOVER};
            }}

            QPushButton:pressed {{
                background-color: {Colors.GRAY_300};
            }}
        """

    @staticmethod
    def get_danger_button_style():
        """Danger button styling (for destructive actions)"""
        return ButtonStyles.get_base_button_style() + f"""
            QPushButton {{
                background-color: {Colors.ERROR};
                color: {Colors.TEXT_LIGHT};
                border-color: {Colors.ERROR};
            }}

            QPushButton:hover:!pressed {{
                background-color: {Colors.ERROR_HOVER};
                border-color: {Colors.ERROR_HOVER};
            }}

            QPushButton:pressed {{
                background-color: {Colors.ERROR_HOVER};
                border-color: {Colors.ERROR_HOVER};
            }}
        """


class InputStyles:
    """Modern input field styling"""

    @staticmethod
    def get_input_style():
        """Standard input field styling"""
        return f"""
            QLineEdit, QTextEdit, QComboBox {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                padding: {Spacing.BASE} {Spacing.MD};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.MD};
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT};
            }}

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid {Colors.PRIMARY};
                background-color: {Colors.GRAY_50};
                outline: none;
            }}

            QLineEdit:hover:!focus, QTextEdit:hover:!focus, QComboBox:hover:!focus {{
                border-color: {Colors.BORDER_DARK};
            }}

            QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{
                background-color: {Colors.GRAY_200};
                color: {Colors.TEXT_MUTED};
                border-color: {Colors.BORDER_LIGHT};
            }}
        """


class CardStyles:
    """Modern card styling for containers"""

    @staticmethod
    def get_card_style():
        """Standard card styling"""
        return f"""
            QFrame, QGroupBox {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                padding: {Spacing.LG};
                margin: {Spacing.SM};
            }}

            QFrame:hover, QGroupBox:hover {{
                border-color: {Colors.BORDER_MEDIUM};
                background-color: {Colors.GRAY_50};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {Spacing.MD};
                padding: 0 {Spacing.BASE} 0 {Spacing.BASE};
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_SM};
            }}
        """


class ToolbarStyles:
    """Modern toolbar styling"""

    @staticmethod
    def get_toolbar_style():
        """Modern toolbar with glass effect"""
        return f"""
            QToolBar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.WHITE}, 
                    stop:0.05 {Colors.GRAY_50},
                    stop:0.95 {Colors.GRAY_100}, 
                    stop:1 {Colors.GRAY_200});
                border: none;
                border-bottom: 1px solid {Colors.BORDER_MEDIUM};
                padding: {Spacing.SM} {Spacing.MD};
                spacing: {Spacing.XS};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}

            QToolBar::separator {{
                background-color: {Colors.BORDER_MEDIUM};
                width: 1px;
                margin: {Spacing.SM} {Spacing.BASE};
                border-radius: 1px;
            }}

            QToolBar QWidget {{
                background-color: transparent;
            }}
        """


class TabStyles:
    """Modern tab widget styling"""

    @staticmethod
    def get_tab_widget_style():
        """Modern tab widget styling"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
                background-color: {Colors.BG_SECONDARY};
                margin-top: -1px;
            }}

            QTabWidget::tab-bar {{
                alignment: left;
            }}

            QTabBar::tab {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-bottom: none;
                border-top-left-radius: {BorderRadius.MD};
                border-top-right-radius: {BorderRadius.MD};
                padding: {Spacing.MD} {Spacing.XL};
                margin-right: {Spacing.XS};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                font-size: {Typography.FONT_SIZE_SM};
                color: {Colors.TEXT_SECONDARY};
                min-width: 100px;
            }}

            QTabBar::tab:selected {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 1px solid {Colors.BG_SECONDARY};
                margin-bottom: -1px;
            }}

            QTabBar::tab:hover:!selected {{
                background-color: {Colors.GRAY_50};
                color: {Colors.TEXT_PRIMARY};
            }}
        """


class StatusStyles:
    """Status indicator styling"""

    @staticmethod
    def get_status_bar_style():
        """Modern status bar styling"""
        return f"""
            QStatusBar {{
                background-color: {Colors.GRAY_100};
                border-top: 1px solid {Colors.BORDER_LIGHT};
                padding: {Spacing.SM} {Spacing.MD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_XS};
                color: {Colors.TEXT_SECONDARY};
            }}

            QStatusBar QLabel {{
                background-color: transparent;
                padding: {Spacing.XS} {Spacing.SM};
                border-radius: {BorderRadius.SM};
            }}
        """


class IconMixin:
    """Mixin for adding icons to components"""

    @staticmethod
    def add_icon_to_text(icon, text, spacing="  "):
        """Add an icon before text with proper spacing"""
        return f"{icon}{spacing}{text}"

    @staticmethod
    def get_icon_button_text(icon, text="", size="medium"):
        """Get properly formatted icon button text"""
        if size == "small":
            spacing = " "
        elif size == "large":
            spacing = "   "
        else:  # medium
            spacing = "  "

        if text:
            return f"{icon}{spacing}{text}"
        return icon