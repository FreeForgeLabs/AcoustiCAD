import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from pathlib import Path

from utils.dev_mode import DevTools
from utils.logger import get_logger
from utils.storage import _platform_app_dir
from ui.styles.base_styles import BaseStyles

from error_handler import setup_error_handling, setup_logging

# Version imports
import __version__ as version_module
__version__ = version_module.__version__
APP_NAME = version_module.APP_NAME
APP_ORGANIZATION = version_module.APP_ORGANIZATION
APP_DOMAIN = version_module.APP_DOMAIN
get_version_string = version_module.get_version_string


def setup_application_directories():
    """Set up application directories with proper error handling.

    Runtime data (logs, crashes, projects, etc.) lives in the OS user-data dir —
    ~/Library/Application Support/AcoustiCAD on macOS — the same place Storage
    uses. This keeps everything under one runtime root instead of also littering
    the home folder with a stray ~/AcoustiCAD. Path comes from Storage's
    _platform_app_dir() so the two modules can never drift (single source of truth).
    The legacy AudioSystemDesigner → AcoustiCAD migration is handled by Storage.
    """
    app_dir = Path(_platform_app_dir(APP_NAME))

    try:
        app_dir.mkdir(exist_ok=True)

        # Create subdirectories
        subdirs = ["logs", "projects", "speaker_profiles", "exports", "backups"]
        for subdir in subdirs:
            (app_dir / subdir).mkdir(exist_ok=True)

        return app_dir

    except PermissionError:
        print(f"Error: Permission denied creating directories at {app_dir}")
        print("Please run the application with appropriate permissions or choose a different location.")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating application directories: {e}")
        sys.exit(1)


# Set up app directories
app_dir = setup_application_directories()

# Initialize proper logging using the error_handler module
try:
    # Use the proper logging setup from error_handler
    logger = setup_logging(app_dir, debug_mode=False)
    logger.info(f"Application starting, directories initialized at {app_dir}")
    logger.info(f"Version: {get_version_string()}")
except Exception as e:
    print(f"Failed to initialize logging: {e}")
    sys.exit(1)

# Import modules
try:
    from ui.main_window import MainWindow
    from utils.storage import Storage
    from utils.config_manager import ConfigManager

except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)


def main():
    logger.info(f"Starting {APP_NAME} v{get_version_string()}...")

    try:
        # Error handling
        crash_handler = setup_error_handling(app_dir)
        logger.info("Global error handling initialized")

        # Create the application
        app = QApplication(sys.argv)

        app.setStyleSheet(BaseStyles.get_global_app_stylesheet())

        # Set application properties
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(APP_ORGANIZATION)
        app.setOrganizationDomain(APP_DOMAIN)
        app.setApplicationVersion(get_version_string())
        logger.debug(f"Application properties set: {APP_NAME} v{get_version_string()}")

        # Initialize storage
        storage = Storage()
        logger.info("Storage initialized")

        # Initialize configuration manager.
        # Bundled defaults live inside the install (read-only in packaged builds).
        # User overrides live alongside Storage in the OS user-data dir so they
        # survive reinstalls and don't try to write to a read-only .app bundle.
        bundled_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        user_config_dir = os.path.join(storage.app_dir, "config")
        config_manager = ConfigManager(
            config_dir=bundled_config_dir,
            user_config_dir=user_config_dir,
        )
        logger.info(
            f"ConfigManager initialized — bundled: {bundled_config_dir}, "
            f"user: {user_config_dir}"
        )

        # Check if dev mode is enabled in configuration
        dev_mode_enabled = config_manager.get(key="dev_mode_enabled", default=False, section="ui")

        logger.info(f"Development mode is {'enabled' if dev_mode_enabled else 'disabled'}")


        window = MainWindow(storage)
        logger.info("Main window created")

        # Add DevTools if enabled in config
        if dev_mode_enabled:
            dev_panel = DevTools(window, config_manager)
            # Store reference to prevent garbage collection
            window.dev_panel = dev_panel
            logger.debug("Development tools enabled")

        window.show()
        logger.info("Application UI displayed")

        # Unsaved-changes prompt is handled by MainWindow.closeEvent — no need
        # for a lastWindowClosed hook (it would run AFTER the close decision is
        # already made, so it could only log, not prompt).

        # Start the event loop
        logger.info("Entering application main loop")
        return app.exec()

    except Exception as e:
        logger.exception(f"Unhandled exception in main: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        logger.info(f"Application exited with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Critical error: {e}")
        sys.exit(1)