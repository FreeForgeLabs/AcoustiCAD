"""
Main window package for Audio System Designer.

This package contains the main application window and its supporting components.
"""

try:
    # Import the main class so it can be imported as before
    from .main_window import MainWindow
    # Make the main class available at package level
    __all__ = ['MainWindow']
except ImportError as e:
    # Fallback: if the new structure isn't ready, show a helpful error
    print(f"Error importing MainWindow from package: {e}")
    print("Make sure all required files are in place:")
    print("- constants.py")
    print("- error_decorator.py")
    print("- menu_manager.py")
    print("- tab_manager.py")
    print("- main_window.py")
    raise