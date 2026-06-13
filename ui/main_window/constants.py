"""
Constants and configuration values for the AcoustiCAD application.
"""


class UIConstants:
    """UI-related constants"""
    MIN_WINDOW_WIDTH = 1000
    MIN_WINDOW_HEIGHT = 700

    # Editor tab indices (Projects is a separate screen, not a tab)
    ZONES_TAB_INDEX = 0
    PLOTTER_TAB_INDEX = 1

    # Timing
    REFRESH_DELAY_MS = 100
    STATUS_MESSAGE_TIMEOUT = 5000

    # Qt attributes
    TOUCH_SYNTHESIZE_MOUSE = True


class Messages:
    """User-facing messages"""
    # Status messages
    READY = "Ready"
    UNSAVED_CHANGES = "Unsaved Changes"
    PROJECT_SAVED = "Project saved"
    PROJECT_LOADED = "Project loaded"
    SAVE_FAILED = "Save failed"
    LOAD_FAILED = "Failed to load project"
    ERROR_LOADING_PROJECT = "Error loading project"

    # Dialog messages
    UNSAVED_CHANGES_NEW_PROJECT = "You have unsaved changes. Would you like to save them before creating a new project?"
    UNSAVED_CHANGES_OPEN_PROJECT = "You have unsaved changes. Would you like to save them before opening another project?"
    UNSAVED_CHANGES_EXIT = "You have unsaved changes. Would you like to save them before exiting?"
    UNSAVED_CHANGES_LOAD_PROJECT = "You have unsaved changes. Would you like to save them before loading a different project?"

    # Error messages
    SAVE_FAILED_CONTINUE = "Failed to save changes. Continue anyway?"
    SAVE_FAILED_EXIT = "Failed to save changes. Exit anyway?"
    SAVE_FAILED_LOAD = "Failed to save changes. Load project anyway?"

    # Menu items
    NO_RECENT_PROJECTS = "No Recent Projects"
    CLEAR_RECENT_PROJECTS = "Clear Recent Projects"

    # About dialog
    ABOUT_TITLE = "About AcoustiCAD"
    ABOUT_TEXT = ("AcoustiCAD\n\n"
                  "A tool for designing audio systems for venues.\n\n"
                  "Version {version}")


class WindowSettings:
    """Window and UI settings keys"""
    WINDOW_GEOMETRY = "window_geometry"
    WINDOW_STATE = "window_state"
    RECENT_PROJECTS = "recent_projects"


class AppInfo:
    """Application information"""
    WINDOW_TITLE = "AcoustiCAD"