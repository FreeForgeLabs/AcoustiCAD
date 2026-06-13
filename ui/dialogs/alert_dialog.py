"""
Styled single-button alert dialog — replaces native QMessageBox popups.

Usage (static helpers):
    AlertDialog.show_info(parent, "Title", "Message text")
    AlertDialog.show_warning(parent, "Title", "Message text")
    AlertDialog.show_error(parent, "Title", "Message text")

Usage (direct):
    dlg = AlertDialog(parent, "Title", "Message text", icon="warning")
    dlg.exec()
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt

from ui.styles.base_styles import Colors, Typography
from ui.styles.component_styles import ButtonStyles


class AlertDialog(QDialog):
    """Styled alert dialog with a single OK button."""

    # Icon choices: "info", "warning", "error", or None
    _ICONS = {
        "info":    ("ℹ", Colors.PRIMARY),
        "warning": ("⚠", Colors.WARNING),
        "error":   ("✕", Colors.ERROR),
    }

    def __init__(self, parent, title, message, icon=None, ok_text="OK"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMaximumWidth(520)
        self.setSizeGripEnabled(False)
        self._build_ui(title, message, icon, ok_text)

    def _build_ui(self, title, message, icon, ok_text):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.WHITE};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        # ── Title row ──────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 12)

        if icon and icon in self._ICONS:
            glyph, color = self._ICONS[icon]
            icon_label = QLabel(glyph)
            icon_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 18px;
                    background: transparent;
                    border: none;
                    padding: 0;
                }}
            """)
            icon_label.setAlignment(Qt.AlignVCenter)
            title_row.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_LG};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        title_label.setAlignment(Qt.AlignVCenter)
        title_row.addWidget(title_label)
        title_row.addStretch()
        layout.addLayout(title_row)

        # ── Divider ────────────────────────────────────────────────────
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT}; border: none;")
        layout.addWidget(divider)
        layout.addSpacing(16)

        # ── Message ────────────────────────────────────────────────────
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_MD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
                line-height: 1.5;
            }}
        """)
        layout.addWidget(message_label)
        layout.addSpacing(24)

        # ── OK button ──────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton(ok_text)
        ok_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    # ── Static convenience methods ─────────────────────────────────────

    @staticmethod
    def show_info(parent, title, message, ok_text="OK"):
        """Show an informational alert."""
        dlg = AlertDialog(parent, title, message, icon="info", ok_text=ok_text)
        dlg.exec()

    @staticmethod
    def show_warning(parent, title, message, ok_text="OK"):
        """Show a warning alert."""
        dlg = AlertDialog(parent, title, message, icon="warning", ok_text=ok_text)
        dlg.exec()

    @staticmethod
    def show_error(parent, title, message, ok_text="OK"):
        """Show an error alert."""
        dlg = AlertDialog(parent, title, message, icon="error", ok_text=ok_text)
        dlg.exec()
