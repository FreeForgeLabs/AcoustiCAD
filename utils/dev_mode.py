from PySide6 import QtCore
from PySide6.QtWidgets import QDockWidget, QTextEdit, QTabWidget
import logging

class _QtLogHandler(logging.Handler):
    """Handler that outputs log messages to a Qt text widget"""

    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

class DevTools:
    """Centralized development tools manager"""

    def __init__(self, main_window, config_manager):
        self.main_window = main_window
        self.config = config_manager
        self.active_tools = []

        # Initialize requested tools
        self.initialize_tools()

    def initialize_tools(self):
        """Initialize development tools based on configuration"""
        # Create debug console by default when in dev mode
        # No need to check additional flags since dev mode is already enabled
        self._setup_debug_console()

        # Set up enhanced logging if desired
        self._setup_enhanced_logging()

        # We can add more tools later

    def _setup_enhanced_logging(self):
        """Configure advanced logging features"""
        # Set debug level
        logging.getLogger().setLevel(logging.DEBUG)

        # Create a log formatter that includes file and line number
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )

        # Apply to all handlers
        for handler in logging.getLogger().handlers:
            handler.setFormatter(detailed_formatter)

        logging.debug("Enhanced logging enabled")

    def _setup_debug_console(self):
        """Add a debug console to the main window"""
        # Create a dockable widget
        dock = QDockWidget("Debug Console", self.main_window)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

        # Create tabs for different debug views
        tab_widget = QTabWidget()

        # Log viewer tab
        log_view = QTextEdit()
        log_view.setReadOnly(True)
        tab_widget.addTab(log_view, "Logs")

        # Add our custom log handler
        log_handler = _QtLogHandler(log_view)
        log_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logging.getLogger().addHandler(log_handler)

        dock.setWidget(tab_widget)
        self.main_window.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        dock.show()  # Explicitly show the dock widget
        self.active_tools.append(dock)
        logging.debug("Debug console initialized and displayed")

    def show(self):
        """Show all development tool widgets"""
        for tool in self.active_tools:
            if hasattr(tool, 'show'):
                tool.show()
        logging.debug("Development tools displayed")
