from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtCore import Qt

from ui.styles.base_styles import Colors, Typography, BorderRadius
from ui.styles.component_styles import ButtonStyles


class UnsavedChangesDialog(QDialog):
    """Styled dialog asking what to do with unsaved changes."""

    SAVE = 1
    DONT_SAVE = 2
    CANCEL = 0

    def __init__(self, message=None, parent=None):
        super().__init__(parent)
        if message is None:
            message = "You have unsaved changes. Would you like to save them before continuing?"
        self.message = message
        self._result_code = self.CANCEL
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Unsaved Changes")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setSizeGripEnabled(False)

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

        icon_label = QLabel("💾")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                background: transparent;
                border: none;
                padding: 0;
            }
        """)
        icon_label.setAlignment(Qt.AlignVCenter)
        title_layout.addWidget(icon_label)

        title_label = QLabel("Unsaved Changes")
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
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_MD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(message_label)
        layout.addSpacing(24)

        # ── Buttons ────────────────────────────────────────────────────
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(ButtonStyles.get_secondary_button_style())
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setDefault(False)
        self.cancel_button.setAutoDefault(False)

        self.dont_save_button = QPushButton("Don't Save")
        self.dont_save_button.setStyleSheet(ButtonStyles.get_secondary_button_style())
        self.dont_save_button.clicked.connect(self.accept_dont_save)
        self.dont_save_button.setDefault(False)
        self.dont_save_button.setAutoDefault(False)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(ButtonStyles.get_primary_button_style())
        self.save_button.clicked.connect(self.accept_save)
        self.save_button.setDefault(True)

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.dont_save_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def accept_save(self):
        self._result_code = self.SAVE
        self.done(self.SAVE)

    def accept_dont_save(self):
        self._result_code = self.DONT_SAVE
        self.done(self.DONT_SAVE)

    def reject(self):
        self._result_code = self.CANCEL
        super().reject()
