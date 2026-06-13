import time
import logging
from PySide6.QtCore import QObject, Signal, QTimer


class CoverageManager(QObject):
    """Manages speaker coverage display, throttling, and forced updates"""

    # Signals
    coverage_changed = Signal(bool)  # show_coverage state changed
    update_requested = Signal()  # Request parent view update
    forced_update_requested = Signal()  # Request immediate parent update

    def __init__(self, parent_view):
        """Initialize the coverage manager

        Args:
            parent_view: The parent SpeakerView instance
        """
        super().__init__(parent_view)
        self.view = parent_view
        self.logger = logging.getLogger(__name__)

        # Coverage state
        self._show_coverage = True

        # Throttling state
        self._initial_update_done = False
        self._last_update_time = None
        self._throttle_threshold = 0.1  # 100ms minimum between updates

        # Schedule initial coverage display
        QTimer.singleShot(500, self.force_coverage_display)

        self.logger.debug("CoverageManager initialized with show_coverage=True")

    @property
    def show_coverage(self):
        """Get current coverage display state"""
        return self._show_coverage

    @show_coverage.setter
    def show_coverage(self, value):
        """Set coverage display state"""
        old_value = self._show_coverage
        self._show_coverage = bool(value)

        if old_value != self._show_coverage:
            self.coverage_changed.emit(self._show_coverage)
            self.logger.info(f"Coverage display changed to: {self._show_coverage}")

            # Force update when enabling coverage
            if self._show_coverage:
                self.force_coverage_display()
            else:
                self.request_update()

    def set_show_coverage(self, show):
        """Set whether to show coverage patterns

        Args:
            show (bool): Whether to show coverage patterns
        """
        self.logger.info(f"Setting show_coverage from {self._show_coverage} to {show}")

        old_value = self._show_coverage
        self._show_coverage = bool(show)

        # Emit signal for any value change
        if old_value != self._show_coverage:
            self.coverage_changed.emit(self._show_coverage)

        # Force update when show_coverage is enabled, regardless of value change
        if self._show_coverage:
            self.force_coverage_display()
        elif old_value != self._show_coverage:
            # Only update if the value actually changed
            self.request_update()

    def force_coverage_display(self):
        """Force coverage patterns to be displayed regardless of throttling"""
        self.logger.debug("Force coverage display called")

        # Explicitly ensure coverage is enabled
        self._show_coverage = True

        # Reset throttling mechanisms to bypass update throttling
        self._reset_throttling()

        # Request immediate forced update
        self.forced_update_requested.emit()

        self.logger.debug(f"Coverage display forcing complete, show_coverage={self._show_coverage}")

    def toggle_coverage_visualization(self):
        """Toggle coverage visualization for debugging"""
        self._show_coverage = not self._show_coverage
        self.logger.debug(f"Coverage visualization toggled to: {self._show_coverage}")

        # Emit signal and request update
        self.coverage_changed.emit(self._show_coverage)
        self.request_update()

    def should_throttle_update(self):
        """Check if updates should be throttled

        Returns:
            bool: True if update should be skipped due to throttling
        """
        current_time = time.time()

        # Always allow the first update for initial display
        if not self._initial_update_done:
            self._initial_update_done = True
            self._last_update_time = current_time
            return False

        # For subsequent updates, apply throttling
        if self._last_update_time is not None:
            # If less than threshold since last update, skip this one
            if current_time - self._last_update_time < self._throttle_threshold:
                return True

        # Update the timestamp and allow update
        self._last_update_time = current_time
        return False

    def request_update(self):
        """Request a standard throttled update"""
        if not self.should_throttle_update():
            self.update_requested.emit()

    def request_forced_update(self):
        """Request an immediate update bypassing throttling"""
        self._reset_throttling()
        self.forced_update_requested.emit()

    def _reset_throttling(self):
        """Reset throttling mechanisms to allow immediate updates"""
        self._initial_update_done = False
        self._last_update_time = None

    def handle_layout_loaded(self):
        """Handle when speaker layout is loaded - force coverage display"""
        self._show_coverage = True
        QTimer.singleShot(200, self.force_coverage_display)
        self.logger.debug("Scheduled coverage display for loaded speakers")

    def set_throttle_threshold(self, threshold_ms):
        """Set the update throttling threshold

        Args:
            threshold_ms (float): Minimum time between updates in milliseconds
        """
        self._throttle_threshold = threshold_ms / 1000.0  # Convert to seconds
        self.logger.debug(f"Update throttle threshold set to {threshold_ms}ms")

    def get_throttle_threshold(self):
        """Get current throttling threshold in milliseconds"""
        return self._throttle_threshold * 1000.0

    def disable_throttling(self):
        """Temporarily disable update throttling"""
        self._throttle_threshold = 0
        self.logger.debug("Update throttling disabled")

    def enable_throttling(self, threshold_ms=100):
        """Re-enable update throttling with specified threshold

        Args:
            threshold_ms (float): Minimum time between updates in milliseconds
        """
        self.set_throttle_threshold(threshold_ms)
        self.logger.debug(f"Update throttling enabled: {threshold_ms}ms")

    def reset_coverage_state(self):
        """Reset coverage manager to initial state"""
        self._show_coverage = True
        self._reset_throttling()
        self.coverage_changed.emit(self._show_coverage)
        self.logger.debug("Coverage manager reset to initial state")

    def get_coverage_stats(self):
        """Get statistics about coverage display

        Returns:
            dict: Coverage statistics
        """
        return {
            'show_coverage': self._show_coverage,
            'throttle_threshold_ms': self.get_throttle_threshold(),
            'initial_update_done': self._initial_update_done,
            'last_update_time': self._last_update_time
        }

    def schedule_delayed_coverage_display(self, delay_ms=200):
        """Schedule a delayed coverage display

        Args:
            delay_ms (int): Delay in milliseconds
        """
        QTimer.singleShot(delay_ms, self.force_coverage_display)
        self.logger.debug(f"Scheduled coverage display in {delay_ms}ms")