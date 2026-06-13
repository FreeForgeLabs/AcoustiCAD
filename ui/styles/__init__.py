"""
Modern styling system for Audio System Designer.

This package provides a comprehensive design system with:
- Base design tokens (colors, typography, spacing)
- Reusable component styles (buttons, inputs, cards)
- Specialized styling for toolbars and other UI elements

Usage:
    from ui.styles.base_styles import Colors, Typography
    from ui.styles.component_styles import ButtonStyles
    from ui.styles.toolbar_styles import ModernToolbarStyles, ToolbarFactory
"""

# Try to import everything, but handle missing files gracefully
try:
    from .base_styles import (
        Colors,
        Typography,
        Spacing,
        BorderRadius,
        Shadows,
        Transitions,
        ZIndex,
        Icons,
        BaseStyles
    )
except ImportError:
    print("Warning: base_styles.py not found - create this file first")
    # Provide empty classes as fallback
    class Colors: pass
    class Typography: pass
    class Spacing: pass
    class BorderRadius: pass
    class Shadows: pass
    class Transitions: pass
    class ZIndex: pass
    class Icons: pass
    class BaseStyles: pass

try:
    from .component_styles import (
        ButtonStyles,
        InputStyles,
        CardStyles,
        ToolbarStyles,
        TabStyles,
        StatusStyles,
        IconMixin
    )
except ImportError:
    print("Warning: component_styles.py not found - create this file first")
    class ButtonStyles: pass
    class InputStyles: pass
    class CardStyles: pass
    class ToolbarStyles: pass
    class TabStyles: pass
    class StatusStyles: pass
    class IconMixin: pass

try:
    from .toolbar_styles import (
        ModernToolbarStyles,
        ToolbarSections,
        ToolbarBuilder,
        ToolbarThemes,
        ToolbarFactory,
        ProToolbarStyles,
        ProToolbarSections,
        ProToolbarBuilder,
        ProToolbarFactory
    )
except ImportError:
    print("Warning: toolbar_styles.py not found - create this file first")
    class ModernToolbarStyles: pass
    class ToolbarSections: pass
    class ToolbarBuilder: pass
    class ToolbarThemes: pass
    class ToolbarFactory: pass
    class ProToolbarStyles: pass
    class ProToolbarSections: pass
    class ProToolbarBuilder: pass
    class ProToolbarFactory: pass

try:
    from .main_window_styles import (
        ProMainWindowStyles,
        MainWindowStyleManager,
        apply_professional_main_window_styling
    )
except ImportError:
    print("Warning: main_window_styles.py not found - create this file first")
    class ProMainWindowStyles: pass
    class MainWindowStyleManager: pass
    def apply_professional_main_window_styling(window): pass

__all__ = [
    # Base styles
    'Colors',
    'Typography',
    'Spacing',
    'BorderRadius',
    'Shadows',
    'Transitions',
    'ZIndex',
    'Icons',
    'BaseStyles',

    # Component styles
    'ButtonStyles',
    'InputStyles',
    'CardStyles',
    'ToolbarStyles',
    'TabStyles',
    'StatusStyles',
    'IconMixin',

    # Toolbar styles
    'ModernToolbarStyles',
    'ToolbarSections',
    'ToolbarBuilder',
    'ToolbarThemes',
    'ToolbarFactory',
    'ProToolbarStyles',
    'ProToolbarSections',
    'ProToolbarBuilder',
    'ProToolbarFactory',

    # Main window styles
    'ProMainWindowStyles',
    'MainWindowStyleManager',
    'apply_professional_main_window_styling'
]