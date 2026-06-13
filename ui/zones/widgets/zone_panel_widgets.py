"""
Reusable widget classes for the zones properties panel.
"""
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QFrame, QLabel, QDoubleSpinBox, QLineEdit, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.styles.base_styles import Colors


class ZoneStatusBadge(QLabel):
    """Status badge for zone information"""

    def __init__(self, text="", status_type="default", parent=None):
        super().__init__(text, parent)
        self.status_type = status_type
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(22)
        self.setMinimumWidth(60)
        self.update_style()

    def update_style(self):
        """Update badge styling based on status type"""
        colors = {
            "calibrated":   Colors.SUCCESS,
            "uncalibrated": Colors.TEXT_SECONDARY,
            "selected":     Colors.PRIMARY,
            "error":        Colors.ERROR,
            "default":      Colors.TEXT_SECONDARY,
        }
        bg_color = colors.get(self.status_type.lower(), colors["default"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                border-radius: 11px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 0.5px;
            }}
        """)


class CompactZoneCard(QFrame):
    """Compact card container with zone tree and Create/Delete buttons at bottom."""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(f"""
            CompactZoneCard {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 8px;
                margin: 2px;
            }}
            CompactZoneCard:hover {{
                border: 1px solid {Colors.GRAY_400};
                background-color: {Colors.GRAY_50};
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)

        if title:
            self.title_label = QLabel(title)
            font = QFont()
            font.setPointSize(11)
            font.setBold(True)
            self.title_label.setFont(font)
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_PRIMARY};
                    border-bottom: 1px solid {Colors.ACCENT};
                    padding-bottom: 4px;
                    margin-bottom: 4px;
                }}
            """)
            self.main_layout.addWidget(self.title_label)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.main_layout.addWidget(self.content_widget, 1)

        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(0, 4, 0, 0)
        self.button_layout.setSpacing(6)

        self.create_btn = QPushButton("+ Zone")
        self.create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
                font-size: 10px;
                min-width: 60px;
            }}
            QPushButton:hover {{ background-color: {Colors.PRIMARY_HOVER}; }}
        """)
        self.button_layout.addWidget(self.create_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ERROR};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
                font-size: 10px;
                min-width: 60px;
            }}
            QPushButton:hover {{ background-color: {Colors.ERROR_HOVER}; }}
            QPushButton:disabled {{
                background-color: {Colors.TEXT_SECONDARY};
                color: {Colors.GRAY_500};
            }}
        """)
        self.delete_btn.setEnabled(False)
        self.button_layout.addWidget(self.delete_btn)

        self.button_layout.addStretch()
        self.main_layout.addWidget(self.button_widget)

    def add_content(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)


class ZoneCard(QFrame):
    """Card container for zone information sections."""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(f"""
            ZoneCard {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 8px;
                margin: 2px;
            }}
            ZoneCard:hover {{
                border: 1px solid {Colors.GRAY_400};
                background-color: {Colors.GRAY_50};
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)

        if title:
            self.title_label = QLabel(title)
            font = QFont()
            font.setPointSize(11)
            font.setBold(True)
            self.title_label.setFont(font)
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_PRIMARY};
                    border-bottom: 1px solid {Colors.ACCENT};
                    padding-bottom: 4px;
                    margin-bottom: 4px;
                }}
            """)
            self.main_layout.addWidget(self.title_label)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        self.main_layout.addWidget(self.content_widget)


class ModernLineEdit(QWidget):
    """Labelled line edit with consistent styling."""

    def __init__(self, label_text="", placeholder_text="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        if label_text:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_SECONDARY};
                    font-weight: 600;
                    font-size: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
            """)
            layout.addWidget(lbl)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder_text)
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px 10px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 6px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                selection-background-color: {Colors.PRIMARY_LIGHT};
                max-height: 28px;
            }}
            QLineEdit:focus {{
                border: 2px solid {Colors.PRIMARY};
                background-color: {Colors.GRAY_50};
            }}
            QLineEdit:hover:!focus {{ border: 1px solid {Colors.GRAY_400}; }}
        """)
        layout.addWidget(self.line_edit)

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)

    def setEnabled(self, enabled):
        self.line_edit.setEnabled(enabled)


class ModernComboBox(QWidget):
    """Labelled combo box with consistent styling."""

    def __init__(self, label_text="", items=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        if label_text:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_SECONDARY};
                    font-weight: 600;
                    font-size: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
            """)
            layout.addWidget(lbl)

        self.combo_box = QComboBox()
        self.combo_box.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 10px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 6px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                min-width: 120px;
                max-height: 28px;
            }}
            QComboBox:focus {{ border: 2px solid {Colors.PRIMARY}; }}
            QComboBox:hover:!focus {{ border: 1px solid {Colors.GRAY_400}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {Colors.TEXT_SECONDARY};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                selection-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER_MEDIUM};
            }}
        """)
        if items:
            self.combo_box.addItems(items)
        layout.addWidget(self.combo_box)

    def currentText(self):
        return self.combo_box.currentText()

    def setCurrentText(self, text):
        self.combo_box.setCurrentText(text)

    def addItems(self, items):
        self.combo_box.addItems(items)

    def clear(self):
        self.combo_box.clear()

    def setEnabled(self, enabled):
        self.combo_box.setEnabled(enabled)


class ModernSpinBox(QWidget):
    """Labelled double spin box with consistent styling."""

    def __init__(self, label_text="", suffix="", min_val=0, max_val=100,
                 step=1, default_val=0, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        if label_text:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_SECONDARY};
                    font-weight: 600;
                    font-size: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
            """)
            layout.addWidget(lbl)

        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(min_val, max_val)
        self.spin_box.setSingleStep(step)
        self.spin_box.setValue(default_val)
        if suffix:
            self.spin_box.setSuffix(suffix)
        self.spin_box.setStyleSheet(f"""
            QDoubleSpinBox {{
                padding: 6px 10px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 6px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                max-height: 28px;
            }}
            QDoubleSpinBox:focus {{ border: 2px solid {Colors.PRIMARY}; }}
            QDoubleSpinBox:hover:!focus {{ border: 1px solid {Colors.GRAY_400}; }}
        """)
        layout.addWidget(self.spin_box)

    def value(self):
        return self.spin_box.value()

    def setValue(self, value):
        self.spin_box.setValue(value)

    def setEnabled(self, enabled):
        self.spin_box.setEnabled(enabled)


class SPLSuggestionWidget(QWidget):
    """Target SPL spinbox with an inline ambient-noise-based suggestion."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        lbl = QLabel("TARGET SPL")
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        """)
        layout.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.spl_spinbox = QDoubleSpinBox()
        self.spl_spinbox.setRange(65.0, 95.0)
        self.spl_spinbox.setSingleStep(1.0)
        self.spl_spinbox.setSuffix(" dB")
        self.spl_spinbox.setValue(75.0)
        self.spl_spinbox.setFixedWidth(80)
        self.spl_spinbox.setStyleSheet(f"""
            QDoubleSpinBox {{
                padding: 6px 8px;
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 6px;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                font-size: 11px;
                max-height: 28px;
            }}
            QDoubleSpinBox:focus {{ border: 2px solid {Colors.PRIMARY}; }}
        """)
        row.addWidget(self.spl_spinbox)

        self.suggestion_label = QLabel("Suggested: 75 dB")
        self.suggestion_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.SUCCESS};
                font-size: 9px;
                font-style: italic;
                padding: 2px 4px;
            }}
        """)
        row.addWidget(self.suggestion_label)
        row.addStretch()

        layout.addLayout(row)

    def setValue(self, value):
        self.spl_spinbox.setValue(value)

    def value(self):
        return self.spl_spinbox.value()

    def updateSuggestion(self, ambient_noise):
        """Update suggestion label based on ambient noise (ambient + 15 dB rule)."""
        suggested = ambient_noise + 15
        self.suggestion_label.setText(f"Suggested: {suggested:.0f} dB")
