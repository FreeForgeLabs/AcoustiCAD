import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QFrame, QMessageBox,
                             QScrollArea)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QPixmap, QDesktopServices

from ui.styles.base_styles import Colors


class StartupDialog(QDialog):
    """Custom startup dialog with welcome message"""

    def __init__(self, version="0.9.0-beta", kofi_link=None, parent=None):
        super().__init__(parent)
        self.version = version
        self.kofi_link = kofi_link or "https://ko-fi.com/watersheep"
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("AcoustiCAD")
        self.setFixedSize(600, 520)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 25, 30, 25)

        # ── Header: logo + title side-by-side ────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(18)

        # Logo
        logo_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__),
                                 '..', 'resources', 'AppIcon_preview.png')
        icon_path = os.path.normpath(icon_path)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(
                72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        header_layout.addWidget(logo_label)

        # Title + version stacked vertically
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.setAlignment(Qt.AlignVCenter)

        title_label = QLabel("AcoustiCAD")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        title_col.addWidget(title_label)

        version_label = QLabel(f"Version {self.version}")
        version_font = QFont()
        version_font.setPointSize(11)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        version_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        title_col.addWidget(version_label)

        header_layout.addLayout(title_col)
        layout.addLayout(header_layout)

        # ── Separator ────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"color: {Colors.BORDER_DARK};")
        layout.addWidget(line)

        # ── Scrollable welcome message ────────────────────────────────────
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(280)

        message_text = """Welcome to AcoustiCAD!

Thank you for demoing our software. We're excited to help you create amazing audio experiences and design professional sound systems with precision and ease.

LICENSING & USAGE
This software is free and open source under the MIT license — free for personal, educational, and commercial use. See the LICENSE file for full terms.

Copyright © 2026 Free Forge Labs. Released under the MIT License.

⚠️ BETA SOFTWARE NOTICE
This is beta software and may contain bugs or incomplete features. Please save your work frequently and report any issues.

UPCOMING FEATURES
• Automatic room plotting and optimization
• SPL heat map visualizations
• Comprehensive speaker profile database
• Enhanced export capabilities

SUPPORT & FEEDBACK
For technical support, bug reports, or feature requests:
• Email: support@freeforgelabs.com
• Website: freeforgelabs.com
• Documentation and updates available online

SUPPORTING DEVELOPMENT
AcoustiCAD is developed independently and made freely available. If you find it valuable, please consider supporting continued development through the donation options below. Your contribution helps keep this software free and enables new features.

Ready to design your perfect audio system? Click "Get Started" to begin!"""

        message_widget = QTextEdit()
        message_widget.setPlainText(message_text.strip())
        message_widget.setReadOnly(True)
        message_widget.setFrameStyle(QFrame.NoFrame)
        message_widget.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                font-size: 11px;
                line-height: 1.5;
                color: {Colors.TEXT_PRIMARY};
                border: none;
                padding: 10px;
            }}
        """)
        scroll_area.setWidget(message_widget)
        layout.addWidget(scroll_area)

        # ── Buttons ───────────────────────────────────────────────────────
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        support_button = QPushButton("Support Developer")
        support_button.setFixedSize(160, 40)
        support_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.WARNING};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {Colors.WARNING_HOVER}; }}
            QPushButton:pressed {{ background-color: #a04000; }}
        """)
        support_button.clicked.connect(self.show_donation_options)
        button_layout.addWidget(support_button)

        button_layout.addStretch()

        ok_button = QPushButton("Get Started")
        ok_button.setFixedSize(140, 40)
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
            QPushButton:pressed {{ background-color: {Colors.PRIMARY_ACTIVE}; }}
        """)
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.GRAY_200};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 10px;
            }}
            QScrollArea {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 6px;
            }}
        """)

    def show_donation_options(self):
        """Show donation options dialog"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Support Development")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("Thank you for supporting AcoustiCAD! 💝")
        msg_box.setInformativeText(
            "Your contribution helps keep this software free and enables "
            "continued development of new features.\n\n"
            "Choose your preferred donation method:"
        )
        kofi_button = msg_box.addButton("Ko-fi", QMessageBox.ActionRole)
        msg_box.addButton("Maybe Later", QMessageBox.RejectRole)
        msg_box.exec()

        if msg_box.clickedButton() == kofi_button:
            QDesktopServices.openUrl(QUrl(self.kofi_link))
