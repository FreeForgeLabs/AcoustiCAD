"""
Base styling system for Audio System Designer.
Core design tokens, colors, typography, and spacing.
"""


class Colors:
    """Modern color palette for the application"""

    # Primary Colors
    PRIMARY = "#007bff"
    PRIMARY_HOVER = "#0056b3"
    PRIMARY_ACTIVE = "#004085"
    PRIMARY_LIGHT = "#e3f2fd"

    # Secondary Colors
    SECONDARY = "#6c757d"
    SECONDARY_HOVER = "#545b62"
    SECONDARY_ACTIVE = "#3d4043"

    # Success/Error/Warning
    SUCCESS = "#28a745"
    SUCCESS_HOVER = "#1e7e34"
    ERROR = "#dc3545"
    ERROR_HOVER = "#c82333"
    WARNING = "#fd7e14"
    WARNING_HOVER = "#e8690b"
    WARNING_BG = "#fef7e0"       # Light yellow background for warning notices
    WARNING_BORDER_ALT = "#d4a800"  # Golden border for info/edit notices
    WARNING_TEXT_DARK = "#b7701a"   # Dark amber text for warning labels

    # Neutral Grays
    WHITE = "#ffffff"
    GRAY_50 = "#fafafa"
    GRAY_100 = "#f8f9fa"
    GRAY_200 = "#e9ecef"
    GRAY_300 = "#dee2e6"
    GRAY_400 = "#ced4da"
    GRAY_500 = "#adb5bd"
    GRAY_600 = "#6c757d"
    GRAY_700 = "#495057"
    GRAY_800 = "#343a40"
    GRAY_900 = "#212529"

    # Text Colors
    TEXT_PRIMARY = "#2c3e50"
    TEXT_SECONDARY = "#6c757d"
    TEXT_MUTED = "#adb5bd"
    TEXT_LIGHT = "#ffffff"

    # Background Colors
    BG_PRIMARY = "#ffffff"
    BG_SECONDARY = "#f8f9fa"
    BG_TERTIARY = "#e9ecef"
    BG_DARK = "#2c3e50"

    # Border Colors
    BORDER_LIGHT = "#e9ecef"
    BORDER_MEDIUM = "#dee2e6"
    BORDER_DARK = "#adb5bd"

    # Special Colors
    ACCENT = "#3498db"
    ACCENT_HOVER = "#2980b9"


class Typography:
    """Typography system with modern font stacks"""

    # Font Families
    FONT_FAMILY_PRIMARY = '"Helvetica Neue", "Arial"'
    FONT_FAMILY_MONO = '"SFMono-Regular", "Monaco", "Consolas", "Liberation Mono", "Courier New", monospace'

    # Font Sizes
    FONT_SIZE_XS = "10px"
    FONT_SIZE_SM = "11px"
    FONT_SIZE_BASE = "12px"
    FONT_SIZE_MD = "14px"
    FONT_SIZE_LG = "16px"
    FONT_SIZE_XL = "18px"
    FONT_SIZE_XXL = "20px"

    # Font Weights
    FONT_WEIGHT_LIGHT = "300"
    FONT_WEIGHT_NORMAL = "400"
    FONT_WEIGHT_MEDIUM = "500"
    FONT_WEIGHT_SEMIBOLD = "600"
    FONT_WEIGHT_BOLD = "700"

    # Line Heights
    LINE_HEIGHT_TIGHT = "1.2"
    LINE_HEIGHT_NORMAL = "1.4"
    LINE_HEIGHT_RELAXED = "1.6"


class Spacing:
    """Consistent spacing system"""

    XS = "2px"
    SM = "4px"
    BASE = "8px"
    MD = "12px"
    LG = "16px"
    XL = "20px"
    XXL = "24px"
    XXXL = "32px"
    HUGE = "48px"


class BorderRadius:
    """Border radius values for modern UI"""

    NONE = "0"
    SM = "3px"
    BASE = "4px"
    MD = "6px"
    LG = "8px"
    XL = "12px"
    ROUND = "50%"


class Shadows:
    """Modern shadow system for depth"""

    NONE = "none"
    SM = "0 1px 2px rgba(0, 0, 0, 0.05)"
    BASE = "0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)"
    MD = "0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06)"
    LG = "0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)"
    XL = "0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)"


class Transitions:
    """Smooth transitions for interactive elements"""

    FAST = "150ms ease"
    BASE = "200ms ease"
    SLOW = "300ms ease"
    SPRING = "250ms cubic-bezier(0.4, 0.0, 0.2, 1)"


class ZIndex:
    """Z-index layering system"""

    DROPDOWN = 1000
    STICKY = 1020
    FIXED = 1030
    MODAL_BACKDROP = 1040
    MODAL = 1050
    POPOVER = 1060
    TOOLTIP = 1070


class Icons:
    """Modern Unicode icons for UI elements"""

    # File Operations
    FOLDER = "📁"
    OPEN = "📂"
    SAVE = "💾"
    EXPORT = "📤"
    IMPORT = "📥"

    # Drawing Tools
    DRAW = "✏️"
    PENCIL = "🖊️"
    BRUSH = "🖌️"
    ERASER = "🧹"
    RULER = "📏"

    # View Controls
    ZOOM_IN = "🔍"
    ZOOM_OUT = "🔎"
    FIT_VIEW = "🖼️"
    GRID = "⊞"
    SNAP = "🧲"

    # Media
    IMAGE = "🖼️"
    BACKGROUND = "🌅"
    CAMERA = "📷"

    # Navigation
    ARROW_UP = "↑"
    ARROW_DOWN = "↓"
    ARROW_LEFT = "←"
    ARROW_RIGHT = "→"

    # Actions
    PLUS = "➕"
    MINUS = "➖"
    DELETE = "🗑️"
    CLEAR = "🧽"
    SETTINGS = "⚙️"

    # Audio
    SPEAKER = "🔊"
    VOLUME = "🔉"
    MICROPHONE = "🎤"

    # Building/Zones
    BUILDING = "🏢"
    ROOM = "🏠"
    ZONE = "📍"

    # Tools
    WRENCH = "🔧"
    HAMMER = "🔨"
    SCREWDRIVER = "🪛"

    # Status
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"


class BaseStyles:
    """Base style generator for consistent UI components"""

    @staticmethod
    def get_base_widget_style():
        """Get base widget styling"""
        return f"""
            QWidget {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_BASE};
                color: {Colors.TEXT_PRIMARY};
                background-color: {Colors.BG_PRIMARY};
            }}
        """

    @staticmethod
    def get_input_focus_style():
        """Get common focus styling for inputs"""
        return f"""
            border: 2px solid {Colors.PRIMARY};
            background-color: {Colors.GRAY_50};
            outline: none;
        """

    @staticmethod
    def get_hover_transition():
        """Get common hover transition"""
        return f"transition: all {Transitions.BASE};"

    @staticmethod
    def get_disabled_style():
        """Get common disabled styling"""
        return f"""
            background-color: {Colors.GRAY_200};
            color: {Colors.TEXT_MUTED};
            border-color: {Colors.BORDER_LIGHT};
        """

    @staticmethod
    def get_global_app_stylesheet():
        """Global QApplication stylesheet — applied once at startup in main.py.

        Verbatim move from main.py (recon #10). Values are intentionally not
        tokenized yet: tokenizing shifts the look (e.g. #f0f0f0 vs GRAY_200's
        #e9ecef), so that's a separate refactor with a visual diff check.
        """
        return """
            /* Global styles */
            QWidget {
                font-family: "Arial", "Helvetica";
            }

            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
            }

            QPushButton:hover {
                background-color: #e0e0e0;
            }

            QPushButton:pressed {
                background-color: #d0d0d0;
            }

            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
            }

            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-bottom-color: #ddd;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 10px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }

            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
        """