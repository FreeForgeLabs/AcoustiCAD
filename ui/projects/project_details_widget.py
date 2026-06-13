from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QScrollArea, QVBoxLayout,
                             QWidget)

from ui.styles.base_styles import BorderRadius, Colors, Spacing, Typography

# Shared style for small uppercase-style field labels
_SUBLABEL_STYLE = f"""
    QLabel {{
        color: {Colors.TEXT_SECONDARY};
        font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
        font-size: {Typography.FONT_SIZE_SM};
        background: transparent;
        border: none;
    }}
"""

# Shared style for plain value labels (transparent, no border)
_VALUE_LABEL_STYLE = f"""
    QLabel {{
        color: {Colors.TEXT_PRIMARY};
        font-size: {Typography.FONT_SIZE_BASE};
        background: transparent;
        border: none;
    }}
"""


class StatusBadge(QLabel):
    """Color-coded status badge"""

    _COLORS = {
        "planning":    Colors.SECONDARY,
        "design":      Colors.PRIMARY,
        "approved":    Colors.SUCCESS,
        "in progress": Colors.WARNING,
        "completed":   Colors.SUCCESS,
        "default":     Colors.SECONDARY,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(80)
        self.setVisible(False)

    def set_status(self, status):
        if not status:
            self.setVisible(False)
            return
        self.setText(status)
        bg = self._COLORS.get(status.lower(), self._COLORS["default"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {Colors.TEXT_LIGHT};
                border-radius: 13px;
                padding: 6px 14px;
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                font-size: {Typography.FONT_SIZE_SM};
            }}
        """)
        self.setVisible(True)


class ClickablePhoneLabel(QLabel):
    """Phone label that opens the system dialer on click"""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QLabel {{
                color: {Colors.PRIMARY};
                text-decoration: underline;
                background: transparent;
                border: none;
            }}
            QLabel:hover {{
                color: {Colors.PRIMARY_HOVER};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            phone = self.text().strip()
            if phone:
                QDesktopServices.openUrl(QUrl(f"tel:{phone}"))
                self.clicked.emit()
        super().mousePressEvent(event)


class TagChip(QLabel):
    """Small chip for displaying multi-select items"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: 12px;
                padding: 4px 10px;
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                margin: 2px;
            }}
        """)


class SectionHeader(QWidget):
    """Section header: bold label + a separator line"""

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 6)
        layout.setSpacing(4)

        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(label)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")
        layout.addWidget(separator)


class FieldRow(QWidget):
    """A label/value row used for displaying a single project field"""

    def __init__(self, label_text, value_widget, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setStyleSheet(_SUBLABEL_STYLE)
        label.setFixedWidth(110)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(label)
        layout.addWidget(value_widget, 1)


# --- Field schema ---------------------------------------------------------
#
# The four repetitive sections of the details panel (Project Details,
# Client & Contact, System Requirements, Project Information) are built
# from this schema. Header, description, power, and notes blocks stay
# hand-built because they're one-of-a-kind shapes.

@dataclass
class FieldSpec:
    label: str            # sublabel shown on the left ("TYPE:", "CLIENT:")
    key: str              # key into project_data dict
    kind: str = "text"    # "text" | "phone" | "chips"
    wrap: bool = False    # word-wrap for long text values
    formatter: Optional[Callable[[object], str]] = None  # value -> display string


def _first_10_or_unknown(value):
    return value[:10] if value else "Unknown"


SECTIONS: list[tuple[str, list[FieldSpec]]] = [
    ("Project Details", [
        FieldSpec("TYPE:",         "project_type"),
        FieldSpec("FACILITY:",     "facility_type"),
        FieldSpec("BUDGET:",       "budget_range"),
        FieldSpec("INSTALLATION:", "installation_type"),
    ]),
    ("Client & Contact", [
        FieldSpec("CLIENT:",   "client_name",       wrap=True),
        FieldSpec("CONTACT:",  "project_contact",   wrap=True),
        FieldSpec("PHONE:",    "contact_phone",     kind="phone"),
        FieldSpec("LOCATION:", "project_location",  wrap=True),
    ]),
    ("System Requirements", [
        FieldSpec("AUDIO SOURCES:",   "primary_audio_sources",  kind="chips"),
        FieldSpec("CONTROL METHODS:", "control_system_type",    kind="chips"),
        FieldSpec("NETWORK:",         "network_infrastructure"),
        FieldSpec("ENVIRONMENT:",     "environmental_factors",  kind="chips"),
    ]),
    ("Project Information", [
        FieldSpec("CREATED:",  "created_at",    formatter=_first_10_or_unknown),
        FieldSpec("MODIFIED:", "last_modified", formatter=_first_10_or_unknown),
    ]),
]


class ProjectDetailsWidget(QWidget):
    """Read-only project details view"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Schema-driven widgets are stashed here, keyed by project_data key.
        self._field_widgets: dict[str, QLabel] = {}
        self._chip_layouts: dict[str, QHBoxLayout] = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setStyleSheet(f"""
            ProjectDetailsWidget {{
                background-color: {Colors.WHITE};
                border: none;
            }}
        """)

        # --- Placeholder (shown when no project selected) ---
        self.placeholder = QLabel("Select a project to view details")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: {Typography.FONT_SIZE_MD};
                background: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(self.placeholder)

        # --- Scrollable content (shown when a project is selected) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background: white; border: none; }")
        self.scroll_area.setVisible(False)

        self.content_container = QWidget()
        self.content_container.setStyleSheet("background: white;")
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(0)

        self._build_header(content_layout)
        for title, fields in SECTIONS[:3]:  # first three before power/notes
            self._build_schema_section(title, fields, content_layout)
        self._build_power_section(content_layout)
        self._build_notes_section(content_layout)
        self._build_schema_section(*SECTIONS[3], parent_layout=content_layout)

        content_layout.addStretch()

        self.scroll_area.setWidget(self.content_container)
        self.scroll_area.viewport().setStyleSheet("background: white;")
        main_layout.addWidget(self.scroll_area)

    # --- Section builders --------------------------------------------------

    def _build_header(self, parent_layout):
        self.name_label = QLabel("")
        self.name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 22px;
                font-weight: {Typography.FONT_WEIGHT_BOLD};
                background: transparent;
                border: none;
            }}
        """)
        parent_layout.addWidget(self.name_label)

        status_row = QWidget()
        status_row.setStyleSheet("background: transparent; border: none;")
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 4, 0, 4)
        status_layout.setSpacing(12)

        self.status_badge = StatusBadge()
        status_layout.addWidget(self.status_badge)

        self.completion_date_label = QLabel("")
        self.completion_date_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_BASE};
                background: transparent;
                border: none;
            }}
        """)
        status_layout.addWidget(self.completion_date_label)
        status_layout.addStretch()
        parent_layout.addWidget(status_row)

        self.description_label = QLabel("")
        self.description_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.GRAY_700};
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                padding: 12px;
                font-size: {Typography.FONT_SIZE_BASE};
                margin-top: 4px;
                margin-bottom: 4px;
            }}
        """)
        parent_layout.addWidget(self.description_label)

    def _build_schema_section(self, title, fields, parent_layout):
        parent_layout.addWidget(SectionHeader(title))
        section = QWidget()
        section.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        for spec in fields:
            if spec.kind == "chips":
                layout.addWidget(self._create_chip_section(spec.label, spec.key))
            elif spec.kind == "phone":
                widget = ClickablePhoneLabel()
                self._field_widgets[spec.key] = widget
                layout.addWidget(FieldRow(spec.label, widget))
            else:  # "text"
                widget = self._make_value_label(wrap=spec.wrap)
                self._field_widgets[spec.key] = widget
                layout.addWidget(FieldRow(spec.label, widget))

        parent_layout.addWidget(section)

    def _build_power_section(self, parent_layout):
        parent_layout.addWidget(SectionHeader("Power & Infrastructure"))
        section = QWidget()
        section.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        req_label = QLabel("REQUIREMENTS:")
        req_label.setStyleSheet(_SUBLABEL_STYLE)
        layout.addWidget(req_label)

        self.power_requirements_label = self._make_value_label(wrap=True)
        layout.addWidget(self.power_requirements_label)
        parent_layout.addWidget(section)

    def _build_notes_section(self, parent_layout):
        parent_layout.addWidget(SectionHeader("Project Notes"))
        self.project_notes_label = QLabel("")
        self.project_notes_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.project_notes_label.setWordWrap(True)
        self.project_notes_label.setMinimumHeight(60)
        self.project_notes_label.setAlignment(Qt.AlignTop)
        self.project_notes_label.setStyleSheet(f"""
            QLabel {{
                padding: 12px;
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.MD};
                color: {Colors.GRAY_700};
                font-size: {Typography.FONT_SIZE_BASE};
            }}
        """)
        parent_layout.addWidget(self.project_notes_label)

    # --- Widget factories --------------------------------------------------

    def _make_value_label(self, wrap=False):
        label = QLabel("")
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet(_VALUE_LABEL_STYLE)
        if wrap:
            label.setWordWrap(True)
        return label

    def _create_chip_section(self, label_text, key):
        widget = QWidget()
        widget.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setStyleSheet(_SUBLABEL_STYLE)
        layout.addWidget(label)

        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        chips_layout = QHBoxLayout(container)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setAlignment(Qt.AlignLeft)
        layout.addWidget(container)

        self._chip_layouts[key] = chips_layout
        return widget

    def _populate_chips(self, layout, items):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            none_label = QLabel("None specified")
            none_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_MUTED};
                    font-style: italic;
                    font-size: {Typography.FONT_SIZE_BASE};
                    background: transparent;
                    border: none;
                }}
            """)
            layout.addWidget(none_label)
        else:
            if isinstance(items, str):
                items = [items]
            for item in items:
                layout.addWidget(TagChip(item))

        layout.addStretch()

    # --- Load / clear ------------------------------------------------------

    def load_project_data(self, project_data):
        if not project_data:
            self.clear_project_details()
            return

        # Header block (one-of-a-kind shapes)
        self.name_label.setText(project_data.get('name', ''))
        self.status_badge.set_status(project_data.get('project_status', ''))
        self.description_label.setText(
            project_data.get('description', '') or "No description provided"
        )
        self._set_completion_date(project_data.get('target_completion_date', ''))

        # Schema-driven fields
        for _title, fields in SECTIONS:
            for spec in fields:
                if spec.kind == "chips":
                    self._populate_chips(
                        self._chip_layouts[spec.key],
                        project_data.get(spec.key, [])
                    )
                else:
                    raw = project_data.get(spec.key, '')
                    display = spec.formatter(raw) if spec.formatter else raw
                    self._field_widgets[spec.key].setText(display)

        # Special-shape sections
        self.power_requirements_label.setText(self._format_power_requirements(project_data))
        self.project_notes_label.setText(
            project_data.get('project_notes', '') or "No notes entered"
        )

        self.placeholder.setVisible(False)
        self.scroll_area.setVisible(True)

    def clear_project_details(self):
        self.scroll_area.setVisible(False)
        self.placeholder.setVisible(True)

    # --- Formatters --------------------------------------------------------

    def _set_completion_date(self, completion_date):
        if not completion_date:
            self.completion_date_label.setText('')
            return
        try:
            date_obj = datetime.fromisoformat(completion_date.replace('Z', '+00:00'))
            self.completion_date_label.setText("Due: " + date_obj.strftime('%b %d, %Y'))
        except ValueError:
            self.completion_date_label.setText("Due: " + completion_date)

    def _format_power_requirements(self, project_data):
        extras = []
        if project_data.get('ups_required'):
            extras.append("UPS/Battery Backup")
        if project_data.get('voltage_240_available'):
            extras.append("240V Available")
        if project_data.get('power_conditioning_needed'):
            extras.append("Power Conditioning")
        if project_data.get('dedicated_circuit_required'):
            extras.append("Dedicated Circuit")
        return "120V AC only" if not extras else "120V AC + " + ", ".join(extras)
