"""
Error handling decorator for consistent error management across the application.
"""

import functools
import logging
from typing import Any, Callable, Optional

def handle_errors(
    default_return: Any = None,
    show_user_error: bool = True,
    status_message: Optional[str] = None,
    log_level: str = "error",
    show_message_box: bool = False,
    message_box_title: str = "Error"
):
    """
    Decorator for handling errors in GUI methods consistently.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # EMERGENCY FIX: Use simple print instead of logging to prevent recursion
                print(f"Error in {func.__name__}: {e}")

                # Show user error in status bar if requested and possible
                if show_user_error and hasattr(self, 'status_label'):
                    try:
                        message = status_message or f"{func.__name__.replace('_', ' ').title()} failed"
                        self.status_label.setText(message)
                    except:
                        pass  # Ignore status update errors

                # Show message box if requested
                if show_message_box:
                    try:
                        from ui.dialogs.alert_dialog import AlertDialog
                        AlertDialog.show_error(None, message_box_title, f"An error occurred: {str(e)}")
                    except:
                        pass  # Ignore message box errors

                return default_return
        return wrapper
    return decorator

# Specialized decorators for common use cases
def handle_project_errors(default_return=False):
    """Decorator specifically for project-related operations"""
    return handle_errors(
        default_return=default_return,
        show_user_error=True,
        show_message_box=True,
        message_box_title="Project Error"
    )

def handle_ui_errors(default_return=None):
    """Decorator for UI operations that should fail silently"""
    return handle_errors(
        default_return=default_return,
        show_user_error=False,
        log_level="warning"
    )

def handle_save_errors(default_return=False):
    """Decorator specifically for save operations"""
    return handle_errors(
        default_return=default_return,
        status_message="Save failed",
        show_message_box=True,
        message_box_title="Save Error"
    )