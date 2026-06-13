import sys
import traceback
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt

# Pulled into crash reports + dialog so triage has version + a real channel.
# Imported here (not threaded through) so the SSOT stays in __version__.py.
from __version__ import APP_NAME, get_version_string, __email__

class CrashHandler:
    """Handle application crashes gracefully"""

    def __init__(self, app_dir):
        self.app_dir = Path(app_dir)
        self.crash_dir = self.app_dir / "crashes"
        self.crash_dir.mkdir(exist_ok=True)

        # Set up crash logging
        self.logger = logging.getLogger(__name__)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow Ctrl+C to work normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Create crash report
        crash_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = self.crash_dir / f"crash_{crash_id}.log"

        # Log the crash
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(f"{APP_NAME} Crash Report\n")
                f.write(f"Version: {get_version_string()}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Python Version: {sys.version}\n")
                f.write(f"Platform: {sys.platform}\n")
                f.write("=" * 50 + "\n")
                f.write(error_msg)

            self.logger.critical(f"Application crashed: {error_msg}")

        except Exception as e:
            # If we can't write the crash file, at least log it
            self.logger.critical(f"Failed to write crash report: {e}")
            self.logger.critical(f"Original crash: {error_msg}")

        # Show user-friendly error dialog
        self.show_crash_dialog(crash_file, str(exc_value))

    def show_crash_dialog(self, crash_file, error_summary):
        """Show a user-friendly crash dialog"""
        try:
            app = QApplication.instance()
            if app is None:
                return

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle(f"{APP_NAME} - Unexpected Error")
            msg.setText("The application has encountered an unexpected error and needs to close.")
            msg.setInformativeText(
                f"Error: {error_summary}\n\n"
                f"A crash report has been saved to:\n{crash_file}\n\n"
                f"To report this issue, please email the crash report to {__email__}."
            )
            msg.setDetailedText(f"Crash report location: {crash_file}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

        except Exception:
            # Last resort - just print to console
            print(f"CRITICAL ERROR: {error_summary}")
            print(f"Crash report: {crash_file}")


def setup_error_handling(app_dir):
    """Set up global error handling"""
    crash_handler = CrashHandler(app_dir)
    sys.excepthook = crash_handler.handle_exception
    return crash_handler


def setup_logging(app_dir, debug_mode=False):
    """Set up comprehensive logging with recursion protection"""
    logs_dir = Path(app_dir) / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Active log is always logs_dir/app.log. TimedRotatingFileHandler renames it
    # to app.log.YYYY-MM-DD at midnight and prunes anything past backupCount.
    log_file = logs_dir / "app.log"

    # Set up logging configuration
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # CRITICAL: Clear any existing handlers to prevent conflicts
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(log_level)

    # Create formatters with simpler format to avoid recursion
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    try:
        # File handler with daily rotation + 7-day retention
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            backupCount=7,
            encoding='utf-8',
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Console handler with error protection
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # Test logging works
        main_logger = logging.getLogger(__name__)
        main_logger.info("Logging system initialized successfully")
        return main_logger

    except Exception as e:
        # Fallback: if file logging fails, use console only
        print(f"Warning: File logging failed ({e}), using console only")
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        return logging.getLogger(__name__)