from PySide6.QtWidgets import QLabel, QTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption

from ui.styles.base_styles import Colors


class ZonePropertiesManager:
    """Manages zone notes UI — advanced properties were removed as dead code."""

    def __init__(self, parent=None):
        self.parent_panel = parent
        self.selected_zone_index = None
        self.notes_edit = None

    def create_notes_section(self):
        """Create the notes section with styled components"""
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(8, 8, 8, 8)

        notes_label = QLabel("Zone Notes")
        notes_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.GRAY_700};
                font-weight: 600;
                font-size: 11px;
                margin-bottom: 4px;
            }}
        """)
        notes_layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter notes about this zone here...")
        self.notes_edit.setMinimumHeight(100)
        self.notes_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 8px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                font-family: "Helvetica Neue", "Arial", sans-serif;
            }}
            QTextEdit:focus {{
                border: 2px solid {Colors.PRIMARY};
            }}
        """)

        document = self.notes_edit.document()
        option = QTextOption()
        option.setTextDirection(Qt.LeftToRight)
        document.setDefaultTextOption(option)

        self.notes_edit.textChanged.connect(self.on_notes_changed)

        notes_layout.addWidget(self.notes_edit)
        notes_layout.addStretch()

        return notes_tab

    def set_selected_zone_index(self, index):
        """Set the currently selected zone index"""
        self.selected_zone_index = index

    def show_zone_properties(self, zone):
        """Load notes for the selected zone (skipped if the user is actively typing)."""
        if self.notes_edit and not self.notes_edit.hasFocus():
            self.notes_edit.blockSignals(True)
            self.notes_edit.setText(zone.get('notes', ''))
            self.notes_edit.blockSignals(False)

    def clear_notes(self):
        """Clear the notes section"""
        if self.notes_edit:
            self.notes_edit.blockSignals(True)
            self.notes_edit.clear()
            self.notes_edit.blockSignals(False)

    def on_notes_changed(self):
        """Handle notes text changes"""
        if self.selected_zone_index is None or not self.notes_edit:
            return
        self._emit_property_changed('notes', self.notes_edit.toPlainText())

    def _emit_property_changed(self, property_name, value):
        """Emit property changed signal"""
        if hasattr(self.parent_panel, 'user_action') and self.selected_zone_index is not None:
            self.parent_panel.user_action.emit(
                'zone', self.selected_zone_index, property_name, value
            )
