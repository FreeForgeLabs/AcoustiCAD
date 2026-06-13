"""
Tab management for the main window.
"""

import logging
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStackedWidget, QTabWidget, QWidget, QVBoxLayout
from ui.projects.project_tab import ProjectTab
from ui.zones.zones_tab import ZonesTab
from ui.plotter.plotter_tab import PlotterTab
from .editor_header_bar import EditorHeaderBar
from .constants import UIConstants, Messages
from .error_decorator import handle_ui_errors


class TabManager:
    """Manages tab creation, signals, and navigation for the main window"""

    def __init__(self, main_window, storage, project_manager):
        self.main_window = main_window
        self.storage = storage
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)

        # State tracking
        self.tab_changing = False
        self.previous_tab_index = 0
        self.signals_connected = False
        self.initialization_complete = False

        # Tab references
        self.stack_widget = None      # outer QStackedWidget (home vs editor)
        self.tab_widget = None        # inner QTabWidget (Zones | Plotter)
        self.editor_header = None     # EditorHeaderBar
        self.project_tab = None
        self.zones_tab = None
        self.plotter_tab = None

        # Signal connections configuration
        self.signal_connections = []
        self.pending_connections = []

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @handle_ui_errors()
    def create_tabs(self):
        """Create the stacked widget, project home screen, and editor page."""
        self.logger.debug("Starting tab creation")

        try:
            # Outer stack: page 0 = project browser, page 1 = editor
            self.stack_widget = QStackedWidget()
            self.main_window.setCentralWidget(self.stack_widget)

            # Page 0 – project home screen
            self._create_project_tab()

            # Page 1 – editor (header bar + Zones/Plotter tab widget)
            self._create_editor_page()

            # Start on the home screen
            self.stack_widget.setCurrentIndex(0)

            self.logger.debug("Tabs created successfully")

        except Exception as e:
            self.logger.critical(f"Critical error during tab creation: {e}", exc_info=True)
            raise

    def _create_project_tab(self):
        try:
            self.project_tab = ProjectTab(self.storage, self.project_manager)
            self.stack_widget.addWidget(self.project_tab)   # index 0
            self.logger.debug("Project tab created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create project tab: {e}")
            raise

    def _create_editor_page(self):
        """Build the editor page.

        The old EditorHeaderBar row has been merged into the zones toolbar so
        everything lives in a single compact strip.  We keep the EditorHeaderBar
        object alive (but off-screen) so any legacy code that checks
        ``tab_manager.editor_header`` doesn't crash.
        """
        try:
            editor_widget = QWidget()
            layout = QVBoxLayout(editor_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Keep the header object for backward-compat (main_window may
            # reference it) but do NOT add it to the layout — its controls
            # have moved into the toolbar.
            self.editor_header = EditorHeaderBar()
            # Dormant connections kept so nothing crashes if the object is
            # still referenced; they never fire since the widget is invisible.
            self.editor_header.back_clicked.connect(self._on_back_clicked)
            self.editor_header.save_clicked.connect(self._on_save_clicked)

            # Inner tab widget (Zones + Plotter only)
            self.tab_widget = QTabWidget()
            self.tab_widget.tabBar().hide()
            layout.addWidget(self.tab_widget)

            self._create_zones_tab()
            self._create_plotter_tab()

            self.tab_widget.setCurrentIndex(UIConstants.ZONES_TAB_INDEX)
            self.tab_widget.currentChanged.connect(self.on_tab_changed)

            # Wire toolbar navigation signals (toolbar lives inside zones_tab)
            if self.zones_tab and hasattr(self.zones_tab, 'toolbar_manager'):
                tm = self.zones_tab.toolbar_manager
                tm.back_requested.connect(self._on_back_clicked)
                tm.save_requested.connect(self._on_save_clicked)
                tm.header_tab_changed.connect(self.tab_widget.setCurrentIndex)

            self.stack_widget.addWidget(editor_widget)  # index 1
            self.logger.debug("Editor page created successfully")

        except Exception as e:
            self.logger.error(f"Failed to create editor page: {e}")
            raise

    def _create_zones_tab(self):
        try:
            self.zones_tab = ZonesTab(self.storage, self.project_manager)
            self.tab_widget.addTab(self.zones_tab, "Zones")
            self.logger.debug("Zones tab created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create zones tab: {e}")
            raise

    def _create_plotter_tab(self):
        try:
            self.plotter_tab = PlotterTab(self.storage, self.project_manager)
            self.tab_widget.addTab(self.plotter_tab, "Speaker Plotter")

            # Wire plotter toolbar navigation signals so the user can get
            # back to zones / projects from the plotter tab.
            if hasattr(self.plotter_tab, 'toolbar') and self.plotter_tab.toolbar:
                tb = self.plotter_tab.toolbar
                if hasattr(tb, 'back_requested'):
                    tb.back_requested.connect(self._on_back_clicked)
                if hasattr(tb, 'save_requested'):
                    tb.save_requested.connect(self._on_save_clicked)
                if hasattr(tb, 'tab_changed'):
                    tb.tab_changed.connect(self.tab_widget.setCurrentIndex)

            self.logger.debug("Plotter tab created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create plotter tab: {e}")
            raise

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def show_home_screen(self):
        """Switch to the project browser (stack page 0)."""
        self.stack_widget.setCurrentIndex(0)

    def show_editor(self, project_name: str):
        """Switch to the editor view (stack page 1) for the given project."""
        # Update the off-screen header object (legacy compat)
        if self.editor_header:
            self.editor_header.set_project_name(project_name)
            self.editor_header.set_modified(False)
        # Update the visible zones toolbar
        self._set_toolbar_project(project_name, modified=False)
        # Also update the plotter toolbar nav bar
        self._set_plotter_toolbar_project(project_name, modified=False)
        self.stack_widget.setCurrentIndex(1)

    def is_editor_visible(self) -> bool:
        return self.stack_widget is not None and self.stack_widget.currentIndex() == 1

    # ── Toolbar proxy helpers ──────────────────────────────────────────────

    def _get_toolbar_manager(self):
        """Return the zones_tab's ToolbarManager if available, else None."""
        try:
            if self.zones_tab and hasattr(self.zones_tab, 'toolbar_manager'):
                return self.zones_tab.toolbar_manager
        except Exception:
            pass
        return None

    def _set_toolbar_project(self, name: str, modified: bool = False):
        tm = self._get_toolbar_manager()
        if tm:
            tm.set_project_name(name)
            tm.set_modified(modified)

    def _set_toolbar_modified(self, is_modified: bool):
        tm = self._get_toolbar_manager()
        if tm:
            tm.set_modified(is_modified)

    def _set_toolbar_active_tab(self, index: int):
        tm = self._get_toolbar_manager()
        if tm:
            tm.set_active_tab(index)
        # Keep plotter toolbar pill in sync too
        self._set_plotter_toolbar_active_tab(index)

    # ── Plotter toolbar proxy helpers ──────────────────────────────────

    def _get_plotter_toolbar(self):
        """Return the plotter_tab's toolbar widget if available."""
        try:
            if self.plotter_tab and hasattr(self.plotter_tab, 'toolbar'):
                return self.plotter_tab.toolbar
        except Exception:
            pass
        return None

    def _set_plotter_toolbar_project(self, name: str, modified: bool = False):
        tb = self._get_plotter_toolbar()
        if tb and hasattr(tb, 'set_project_name'):
            tb.set_project_name(name)
            tb.set_modified(modified)

    def _set_plotter_toolbar_modified(self, is_modified: bool):
        tb = self._get_plotter_toolbar()
        if tb and hasattr(tb, 'set_modified'):
            tb.set_modified(is_modified)

    def _set_plotter_toolbar_active_tab(self, index: int):
        tb = self._get_plotter_toolbar()
        if tb and hasattr(tb, 'set_active_tab'):
            tb.set_active_tab(index)

    # Header button callbacks
    def _on_back_clicked(self):
        if hasattr(self.main_window, 'back_to_projects'):
            self.main_window.back_to_projects()

    def _on_save_clicked(self):
        if hasattr(self.main_window, 'on_save'):
            self.main_window.on_save()

    # Legacy aliases kept so existing main_window.py call-sites still work
    def switch_to_projects_tab(self):
        self.show_home_screen()

    def switch_to_zones_tab(self):
        if not self.is_editor_visible():
            return
        self.tab_widget.setCurrentIndex(UIConstants.ZONES_TAB_INDEX)
        if self.editor_header:
            self.editor_header.set_active_tab(UIConstants.ZONES_TAB_INDEX)
        self._set_toolbar_active_tab(UIConstants.ZONES_TAB_INDEX)

    def switch_to_plotter_tab(self):
        if not self.is_editor_visible():
            return
        self.tab_widget.setCurrentIndex(UIConstants.PLOTTER_TAB_INDEX)
        if self.editor_header:
            self.editor_header.set_active_tab(UIConstants.PLOTTER_TAB_INDEX)
        self._set_toolbar_active_tab(UIConstants.PLOTTER_TAB_INDEX)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    @handle_ui_errors()
    def connect_tab_signals(self):
        """Connect signals between tabs with proper initialisation checks."""
        if self.signals_connected:
            self.logger.warning("Signals already connected, skipping")
            return

        self.logger.debug("Starting signal connection process")

        try:
            if not self._verify_tab_initialization():
                self.logger.warning("Not all tabs are properly initialised, deferring signal connections")
                QTimer.singleShot(100, self.connect_tab_signals)
                return

            self._define_signal_connections()
            self._connect_signals_safely()

            self.signals_connected = True
            self.initialization_complete = True
            self.logger.info("Tab signal connections completed successfully")

        except Exception as e:
            self.logger.critical(f"Critical error during signal connection: {e}", exc_info=True)
            raise

    def _verify_tab_initialization(self):
        checks = [
            ("project_tab", self.project_tab is not None),
            ("zones_tab", self.zones_tab is not None),
            ("plotter_tab", self.plotter_tab is not None),
        ]

        if self.zones_tab:
            checks.append(("zones_tab.zones_view", hasattr(self.zones_tab, 'zones_view')))
            if hasattr(self.zones_tab, 'zones_view') and self.zones_tab.zones_view:
                checks.append(("zones_view.zones_modified", hasattr(self.zones_tab.zones_view, 'zones_modified')))

        if self.plotter_tab:
            checks.append(("plotter_tab.speaker_view", hasattr(self.plotter_tab, 'speaker_view')))

        failed_checks = [name for name, check in checks if not check]
        if failed_checks:
            self.logger.debug(f"Initialisation checks failed: {failed_checks}")
            return False

        self.logger.debug("All initialisation checks passed")
        return True

    def _define_signal_connections(self):
        self.signal_connections = []

        if self.project_tab and hasattr(self.project_tab, 'project_selected'):
            if self.zones_tab and hasattr(self.zones_tab, 'set_current_project'):
                self.signal_connections.append(
                    (self.project_tab, 'project_selected', self.zones_tab, 'set_current_project',
                     "Project selection to zones tab")
                )
            if self.plotter_tab and hasattr(self.plotter_tab, 'set_current_project'):
                self.signal_connections.append(
                    (self.project_tab, 'project_selected', self.plotter_tab, 'set_current_project',
                     "Project selection to plotter tab")
                )

        if self.zones_tab and hasattr(self.zones_tab, 'zones_updated'):
            if self.project_tab and hasattr(self.project_tab, 'load_projects'):
                self.signal_connections.append(
                    (self.zones_tab, 'zones_updated', self.project_tab, 'load_projects',
                     "Zones updates to project list refresh")
                )
            if hasattr(self.main_window, 'on_project_changed'):
                self.signal_connections.append(
                    (self.zones_tab, 'zones_updated', self.main_window, 'on_project_changed',
                     "Zones updates to main window")
                )

        if self.plotter_tab:
            if hasattr(self.plotter_tab, 'speaker_layout_changed') and hasattr(self.main_window, 'on_project_changed'):
                self.signal_connections.append(
                    (self.plotter_tab, 'speaker_layout_changed', self.main_window, 'on_project_changed',
                     "Speaker layout changes to main window")
                )
            if hasattr(self.plotter_tab, 'obstruction_layout_changed') and hasattr(self.main_window, 'on_project_changed'):
                self.signal_connections.append(
                    (self.plotter_tab, 'obstruction_layout_changed', self.main_window, 'on_project_changed',
                     "Obstruction layout changes to main window")
                )

        if (self.zones_tab and
                hasattr(self.zones_tab, 'zones_view') and
                self.zones_tab.zones_view and
                hasattr(self.zones_tab.zones_view, 'zones_modified') and
                hasattr(self.main_window, 'on_project_changed')):
            self.signal_connections.append(
                (self.zones_tab.zones_view, 'zones_modified', self.main_window, 'on_project_changed',
                 "Zones view modifications to main window")
            )

        self.logger.debug(f"Defined {len(self.signal_connections)} signal connections")

    def _connect_signals_safely(self):
        connected_count = 0
        failed_connections = []

        for source, signal_name, target, slot_name, description in self.signal_connections:
            try:
                if not hasattr(source, signal_name):
                    failed_connections.append(f"{description} - missing signal '{signal_name}'")
                    continue
                if not hasattr(target, slot_name):
                    failed_connections.append(f"{description} - missing slot '{slot_name}'")
                    continue

                signal = getattr(source, signal_name)
                slot = getattr(target, slot_name)

                if not hasattr(signal, 'connect'):
                    failed_connections.append(f"{description} - '{signal_name}' is not a signal")
                    continue
                if not callable(slot):
                    failed_connections.append(f"{description} - '{slot_name}' is not callable")
                    continue

                signal.connect(slot)
                connected_count += 1
                self.logger.debug(f"Connected: {description}")

            except Exception as e:
                failed_connections.append(f"{description} - error: {e}")
                self.logger.error(f"Error connecting {description}: {e}")

        self.logger.info(f"Connected {connected_count} signals between tabs")
        if failed_connections:
            self.logger.warning(f"Failed to connect {len(failed_connections)} signals:")
            for failure in failed_connections:
                self.logger.warning(f"  - {failure}")

    # ------------------------------------------------------------------
    # Tab-change handler (Zones ↔ Plotter only)
    # ------------------------------------------------------------------

    @handle_ui_errors()
    def on_tab_changed(self, index):
        if self.tab_changing:
            return
        if not self.initialization_complete:
            self.logger.debug(f"Tab change ignored - initialisation not complete: {index}")
            return

        self.tab_changing = True
        try:
            self.logger.debug(f"Editor tab changed from {self.previous_tab_index} to {index}")

            # Keep header pill toggle in sync (no-op if already correct)
            if self.editor_header:
                self.editor_header.set_active_tab(index)
            self._set_toolbar_active_tab(index)

            if (index == UIConstants.PLOTTER_TAB_INDEX and
                    self.previous_tab_index != UIConstants.PLOTTER_TAB_INDEX and
                    self.plotter_tab and
                    hasattr(self.plotter_tab, 'refresh_zones')):
                if self.project_manager.get_current_project_id():
                    # Push live zones into the in-memory project data so the plotter
                    # always reflects what's drawn, even before an explicit save.
                    self._sync_live_zones_to_project_data()
                    QTimer.singleShot(UIConstants.REFRESH_DELAY_MS, self.plotter_tab.refresh_zones)

            self.previous_tab_index = index

            if not self.project_manager.get_current_project_id():
                return

            if self.project_manager.has_unsaved_changes():
                self.main_window.status_label.setText(Messages.UNSAVED_CHANGES)

        except Exception as e:
            self.logger.error(f"Error in tab change handler: {e}")
        finally:
            self.tab_changing = False

    def _sync_live_zones_to_project_data(self):
        """Copy the zones_tab's in-memory zones into the current project data dict.

        This lets the plotter always reflect what's drawn without requiring an
        explicit save first.  The project remains marked as modified.
        """
        try:
            if not (self.zones_tab and
                    hasattr(self.zones_tab, 'zones_view') and
                    self.zones_tab.zones_view):
                return

            project_data = self.project_manager.get_current_project_data()
            if not project_data:
                return

            zv = self.zones_tab.zones_view
            live_zones_data = {
                'zones': zv.zones.copy() if hasattr(zv, 'zones') else [],
                'scale_factor': (zv.scale_manager.get_scale_factor()
                                 if hasattr(zv, 'scale_manager') else 12.0),
                'background_path': (zv.background_manager.get_background_path()
                                    if hasattr(zv, 'background_manager') else None),
            }
            project_data['zones_data'] = live_zones_data

        except Exception as e:
            self.logger.error(f"Error syncing live zones to project data: {e}")

    # ------------------------------------------------------------------
    # Accessors / status
    # ------------------------------------------------------------------

    def get_current_tab_index(self):
        return self.tab_widget.currentIndex() if self.tab_widget else 0

    def set_current_tab(self, index):
        if self.tab_widget and 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)

    def get_initialization_status(self):
        status = {
            'tabs_created': all([self.project_tab, self.zones_tab, self.plotter_tab]),
            'signals_connected': self.signals_connected,
            'initialization_complete': self.initialization_complete,
            'stack_widget_exists': self.stack_widget is not None,
            'tab_widget_exists': self.tab_widget is not None,
        }
        if self.zones_tab:
            status['zones_view_exists'] = hasattr(self.zones_tab, 'zones_view')
        return status

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self):
        try:
            for source, signal_name, target, slot_name, description in self.signal_connections:
                try:
                    signal = getattr(source, signal_name, None)
                    if signal and hasattr(signal, 'disconnect'):
                        signal.disconnect()
                except Exception:
                    pass

            self.signal_connections.clear()
            self.pending_connections.clear()
            self.signals_connected = False
            self.initialization_complete = False

        except Exception as e:
            self.logger.error(f"Error in TabManager cleanup: {e}")
