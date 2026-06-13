"""
Editor header bar shown above the Zones/Plotter tabs when a project is open.
Provides back navigation, project name, modification indicator, view tab toggles,
and save button.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QButtonGroup

from ui.styles.base_styles import Colors, Typography
from ui.styles.component_styles import ButtonStyles


class EditorHeaderBar(QWidget):
    """Thin header bar displayed above the Zones/Plotter tab widget."""

    back_clicked = Signal()
    save_clicked = Signal()
    tab_changed = Signal(int)   # 0 = Zones, 1 = Speaker Plotter

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"""
            EditorHeaderBar {{
                background-color: {Colors.WHITE};
                border-bottom: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)

        # ── Back button ────────────────────────────────────────────────────
        self.back_btn = QPushButton("← Projects")
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                color: {Colors.PRIMARY_HOVER};
                text-decoration: underline;
            }}
        """)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_clicked)

        # ── Separator ─────────────────────────────────────────────────────
        sep1 = self._make_separator()

        # ── Project name ──────────────────────────────────────────────────
        self.project_label = QLabel("No Project")
        self.project_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                background: transparent;
                border: none;
            }}
        """)

        # ── Unsaved-changes dot (hidden by default) ────────────────────────
        self.modified_dot = QLabel("●")
        self.modified_dot.setStyleSheet(f"""
            QLabel {{
                color: {Colors.WARNING};
                font-size: 10px;
                background: transparent;
                border: none;
            }}
        """)
        self.modified_dot.setVisible(False)
        self.modified_dot.setToolTip("Unsaved changes")

        # ── Stretch — pushes tabs to centre ──────────────────────────────
        # (nothing here; we use addStretch below)

        # ── Tab toggle pill buttons ───────────────────────────────────────
        toggle_container = QWidget()
        toggle_container.setStyleSheet("background: transparent; border: none;")
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(0)

        # Shared pill base style
        _pill_base = f"""
            QPushButton {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                padding: 5px 16px;
                border: 1px solid {Colors.BORDER_MEDIUM};
                background-color: {Colors.GRAY_100};
                color: {Colors.TEXT_SECONDARY};
                min-height: 28px;
                max-height: 28px;
                outline: none;
            }}
            QPushButton:hover:!checked {{
                background-color: {Colors.GRAY_200};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Colors.PRIMARY};
                color: white;
                border-color: {Colors.PRIMARY};
            }}
        """

        self.zones_toggle = QPushButton("Zones")
        self.zones_toggle.setCheckable(True)
        self.zones_toggle.setChecked(True)
        self.zones_toggle.setStyleSheet(_pill_base + """
            QPushButton {
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                border-right: none;
            }
        """)
        self.zones_toggle.setCursor(Qt.PointingHandCursor)

        self.plotter_toggle = QPushButton("Speaker Plotter")
        self.plotter_toggle.setCheckable(True)
        self.plotter_toggle.setStyleSheet(_pill_base + """
            QPushButton {
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)
        self.plotter_toggle.setCursor(Qt.PointingHandCursor)

        # Exclusive group so only one can be active at a time
        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)
        self._tab_group.addButton(self.zones_toggle, 0)
        self._tab_group.addButton(self.plotter_toggle, 1)

        # Emit tab_changed signal when toggled
        self.zones_toggle.clicked.connect(lambda: self.tab_changed.emit(0))
        self.plotter_toggle.clicked.connect(lambda: self.tab_changed.emit(1))

        toggle_layout.addWidget(self.zones_toggle)
        toggle_layout.addWidget(self.plotter_toggle)

        # ── Separator ─────────────────────────────────────────────────────
        sep2 = self._make_separator()

        # ── Save button ───────────────────────────────────────────────────
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        self.save_btn.clicked.connect(self.save_clicked)

        # ── Assemble ──────────────────────────────────────────────────────
        layout.addWidget(self.back_btn)
        layout.addWidget(sep1)
        layout.addWidget(self.project_label)
        layout.addWidget(self.modified_dot)
        layout.addStretch()
        layout.addWidget(toggle_container)
        layout.addWidget(sep2)
        layout.addWidget(self.save_btn)

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _make_separator():
        sep = QWidget()
        sep.setFixedSize(1, 24)
        sep.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
        return sep

    # ── Public API ────────────────────────────────────────────────────────

    def set_project_name(self, name: str):
        self.project_label.setText(name or "Untitled Project")

    def set_modified(self, modified: bool):
        self.modified_dot.setVisible(modified)

    def set_active_tab(self, index: int):
        """Programmatically update the active tab pill (no signal emitted)."""
        btn = self._tab_group.button(index)
        if btn and not btn.isChecked():
            # Temporarily block to avoid emitting tab_changed during sync
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)
