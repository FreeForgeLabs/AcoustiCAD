from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt

from ui.styles.base_styles import Colors, Typography, Spacing, BorderRadius
from ui.styles.component_styles import ButtonStyles


class ConfirmDialog(QDialog):
    """
    Custom styled confirmation dialog to replace native QMessageBox.question().

    Usage (static helper):
        confirmed = ConfirmDialog.ask(
            parent, "Delete Project",
            "Are you sure? This cannot be undone.",
            confirm_text="Delete",
            danger=True
        )

    Usage (direct):
        dlg = ConfirmDialog(parent, title, message, ...)
        dlg.exec()
        if dlg.was_confirmed(): ...
    """

    def __init__(self, parent, title, message,
                 confirm_text="Confirm", cancel_text="Cancel",
                 danger=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setSizeGripEnabled(False)
        self._confirmed = False

        self._build_ui(title, message, confirm_text, cancel_text, danger)

    def _build_ui(self, title, message, confirm_text, cancel_text, danger):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.WHITE};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        # ── Title row ──────────────────────────────────────────────────
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        title_layout.setContentsMargins(0, 0, 0, 12)

        if danger:
            icon_label = QLabel("⚠️")
            icon_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 20px;
                    background: transparent;
                    border: none;
                    padding: 0;
                }}
            """)
            icon_label.setAlignment(Qt.AlignVCenter)
            title_layout.addWidget(icon_label)

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
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

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

        # ── Buttons ────────────────────────────────────────────────────
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setStyleSheet(ButtonStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setDefault(False)
        cancel_btn.setAutoDefault(False)

        confirm_btn = QPushButton(confirm_text)
        if danger:
            confirm_btn.setStyleSheet(ButtonStyles.get_danger_button_style())
        else:
            confirm_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        confirm_btn.clicked.connect(self._on_confirm)
        confirm_btn.setDefault(True)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        layout.addLayout(button_layout)

    def _on_confirm(self):
        self._confirmed = True
        self.accept()

    def was_confirmed(self):
        """Return True if the user clicked the confirm button."""
        return self._confirmed

    @staticmethod
    def ask(parent, title, message,
            confirm_text="Confirm", cancel_text="Cancel",
            danger=False):
        """
        Convenience method.  Returns True if the user confirmed.

        Example:
            if ConfirmDialog.ask(self, "Delete", "Sure?", confirm_text="Delete", danger=True):
                ...do delete...
        """
        dlg = ConfirmDialog(parent, title, message, confirm_text, cancel_text, danger)
        dlg.exec()
        return dlg.was_confirmed()
