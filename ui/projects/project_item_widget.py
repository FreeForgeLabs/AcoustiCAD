import logging
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core.thumbnail_generator import ThumbnailGenerator

from ui.styles.base_styles import Colors, Typography, BorderRadius


class ProjectItemWidget(QWidget):
    """Custom widget for displaying a project item with thumbnail in the project list.

    Selection is driven by the parent QListWidget's itemSelectionChanged signal —
    this widget is purely visual. Click events propagate up to the QListWidget
    via Qt's default event handling.
    """

    _thumbnail_generator = None  # Shared across all instances

    @classmethod
    def _get_thumbnail_generator(cls):
        if cls._thumbnail_generator is None:
            cls._thumbnail_generator = ThumbnailGenerator()
        return cls._thumbnail_generator

    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.project_data = project_data
        self.project_id = project_data.get('id')
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(100, 75)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.GRAY_200};
                border: 1px solid {Colors.BORDER_MEDIUM};
            }}
        """)
        layout.addWidget(self.thumbnail_label)

        info_layout = QVBoxLayout()

        self.name_label = QLabel(self.project_data.get('name', 'Unnamed Project'))
        self.name_label.setStyleSheet(f"""
            QLabel {{
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-size: {Typography.FONT_SIZE_BASE};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        info_layout.addWidget(self.name_label)

        description = self.project_data.get('description', '')
        if len(description) > 80:
            description = description[:77] + "..."
        self.desc_label = QLabel(description)
        self.desc_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_SM};
                background: transparent;
                border: none;
            }}
        """)
        info_layout.addWidget(self.desc_label)

        meta_layout = QHBoxLayout()

        created_at = self.project_data.get('created_at', '')
        if created_at:
            self.created_label = QLabel(f"Created: {created_at[:10]}")
            self.created_label.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: {Typography.FONT_SIZE_SM}; background: transparent; border: none;"
            )
            meta_layout.addWidget(self.created_label)

        modified_at = self.project_data.get('last_modified', '')
        if modified_at:
            self.modified_label = QLabel(f"Modified: {modified_at[:10]}")
            self.modified_label.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: {Typography.FONT_SIZE_SM}; background: transparent; border: none;"
            )
            meta_layout.addWidget(self.modified_label)

        info_layout.addLayout(meta_layout)
        info_layout.addStretch(1)
        layout.addLayout(info_layout, 1)

        self.setMinimumHeight(90)
        self.setStyleSheet(f"""
            ProjectItemWidget {{
                border: 1px solid transparent;
                background-color: transparent;
            }}
            ProjectItemWidget:hover {{
                border: 1px solid {Colors.PRIMARY};
                background-color: {Colors.PRIMARY_LIGHT};
                border-radius: {BorderRadius.BASE};
            }}
        """)

        self.load_thumbnail()
        self.setMouseTracking(True)

    def load_thumbnail(self):
        thumbnail_data = self.project_data.get('preview_thumbnail')
        self.logger.debug(
            f"Loading thumbnail for project {self.project_id}, "
            f"thumbnail exists: {thumbnail_data is not None}"
        )

        if thumbnail_data:
            image = self._get_thumbnail_generator().base64_to_image(thumbnail_data)
            if image:
                pixmap = QPixmap.fromImage(image)
                self.thumbnail_label.setPixmap(pixmap.scaled(
                    self.thumbnail_label.width(),
                    self.thumbnail_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
                return

        self.thumbnail_label.setText("No Preview")
