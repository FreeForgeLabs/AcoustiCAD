import os
import re

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QFormLayout, QTextEdit,
                             QComboBox, QWidget, QFrame, QDateEdit, QScrollArea,
                             QCheckBox, QListWidget, QListWidgetItem, QPushButton,
                             QStyleFactory)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QFont

from ui.styles.base_styles import Colors, Typography, Spacing, BorderRadius
from ui.styles.component_styles import ButtonStyles
from ui.dialogs.alert_dialog import AlertDialog

# Resolve the arrow SVG path once at import time so the stylesheet can reference it
_ARROW_SVG = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'resources', 'arrow_down.svg')
).replace('\\', '/')


class MultiSelectComboBox(QComboBox):
    """ComboBox that allows multiple selections with checkboxes"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Select options...")

        self.list_widget = QListWidget()
        self.setModel(self.list_widget.model())
        self.setView(self.list_widget)
        self.list_widget.itemChanged.connect(self.update_text)
        self.items = []

    def addItems(self, items):
        self.items = items
        self.list_widget.clear()
        for item_text in items:
            item = QListWidgetItem(item_text)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

    def setCheckedItems(self, checked_items):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked if item.text() in checked_items else Qt.Unchecked)
        self.update_text()

    def getCheckedItems(self):
        return [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        ]

    def update_text(self):
        checked = self.getCheckedItems()
        if not checked:
            self.lineEdit().setText("")
            self.lineEdit().setPlaceholderText("Select options...")
        elif len(checked) == 1:
            self.lineEdit().setText(checked[0])
        else:
            self.lineEdit().setText(f"{len(checked)} items selected")


class ProjectDialog(QDialog):
    """Dialog for creating or editing a project"""

    def __init__(self, parent=None, existing_project=None):
        super().__init__(parent)
        self.existing_project = existing_project
        self.is_edit_mode = existing_project is not None

        self.setWindowTitle("Edit Project" if self.is_edit_mode else "New Project")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        # Use Fusion style so Qt renders all widgets itself instead of delegating to
        # macOS native rendering — this gives us proper combo arrows + light popups
        self._fusion_style = QStyleFactory.create("Fusion")
        if self._fusion_style:
            self.setStyle(self._fusion_style)

        self._apply_dialog_style()
        self.init_ui()

        if self.is_edit_mode:
            self.populate_fields()

    # ── Styling helpers ────────────────────────────────────────────────────────

    def _apply_dialog_style(self):
        """Global stylesheet — forces light theme on all child widgets."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_SECONDARY};
            }}

            QScrollArea {{
                background-color: transparent;
                border: none;
            }}

            /* Inputs */
            QLineEdit, QTextEdit, QDateEdit {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                padding: {Spacing.BASE} {Spacing.MD};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.MD};
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY_LIGHT};
                min-height: 26px;
            }}
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {{
                border: 2px solid {Colors.PRIMARY};
                background-color: {Colors.GRAY_50};
            }}
            QLineEdit:hover:!focus, QTextEdit:hover:!focus, QDateEdit:hover:!focus {{
                border-color: {Colors.BORDER_DARK};
            }}

            /* Combo boxes — explicit light style to override macOS dark mode */
            QComboBox {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                padding: 6px {Spacing.MD};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.MD};
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                min-height: 26px;
            }}
            QComboBox:focus {{
                border: 2px solid {Colors.PRIMARY};
            }}
            QComboBox:hover:!focus {{
                border-color: {Colors.BORDER_DARK};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border: none;
                border-left: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 0 {BorderRadius.MD} {BorderRadius.MD} 0;
            }}
            QComboBox::down-arrow {{
                image: url("{_ARROW_SVG}");
                width: 10px;
                height: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.MD};
                padding: 2px;
                selection-background-color: {Colors.PRIMARY_LIGHT};
                selection-color: {Colors.PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px {Spacing.MD};
                min-height: 24px;
                border-radius: {BorderRadius.SM};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
            }}

            /* Checkboxes */
            QCheckBox {{
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                color: {Colors.TEXT_PRIMARY};
                spacing: 8px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.SM};
                background-color: {Colors.WHITE};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.PRIMARY};
                border-color: {Colors.PRIMARY};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Colors.BORDER_DARK};
            }}

            /* MultiSelect list */
            QListWidget {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                color: {Colors.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
                outline: none;
                border-radius: {BorderRadius.MD};
            }}
            QListWidget::item {{
                padding: 5px 8px;
                border: none;
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item:hover {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
            }}

            /* Generic labels */
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)

    def _create_section(self, title):
        """Return (frame, inner_layout) — a styled white card with title + divider."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.LG};
            }}
        """)

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(16, 14, 16, 16)
        inner.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
                padding: 0;
            }}
        """)
        inner.addWidget(title_label)

        divider = QWidget()
        divider.setFixedHeight(2)
        divider.setStyleSheet(f"background-color: {Colors.PRIMARY}; border: none;")
        inner.addWidget(divider)

        return frame, inner

    @staticmethod
    def _make_form():
        """Consistent form layout for all sections."""
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setSpacing(10)
        form.setContentsMargins(0, 4, 0, 0)
        return form

    @staticmethod
    def _form_label(text):
        """Muted, right-aligned form row label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-weight: {Typography.FONT_WEIGHT_MEDIUM};
                background: transparent;
                border: none;
            }}
        """)
        return label

    @staticmethod
    def _hint_label(text):
        """Small italic hint label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-style: italic;
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        return label

    def _setup_calendar(self):
        """Apply app styling to the QDateEdit's calendar popup."""
        cal = self.completion_date_input.calendarWidget()
        if not cal:
            return

        # Use Fusion style so Qt renders the calendar itself (removes green circles etc.)
        if self._fusion_style:
            cal.setStyle(self._fusion_style)

        # Fix weekend text — remove the default red color
        normal_fmt = QTextCharFormat()
        normal_fmt.setForeground(QColor(Colors.TEXT_PRIMARY))
        cal.setWeekdayTextFormat(Qt.Saturday, normal_fmt)
        cal.setWeekdayTextFormat(Qt.Sunday, normal_fmt)

        # Style the column headers (Mon, Tue, etc.)
        header_fmt = QTextCharFormat()
        header_fmt.setForeground(QColor(Colors.TEXT_SECONDARY))
        header_fmt.setFontWeight(QFont.DemiBold)
        cal.setHeaderTextFormat(header_fmt)

        cal.setStyleSheet(f"""
            QCalendarWidget {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_MEDIUM};
                border-radius: {BorderRadius.LG};
            }}

            /* Navigation bar (← June 2026 →) */
            QCalendarWidget #qt_calendar_navigationbar {{
                background-color: {Colors.PRIMARY};
                padding: 6px 8px;
                border-radius: {BorderRadius.LG} {BorderRadius.LG} 0 0;
            }}

            /* All buttons in the nav bar */
            QCalendarWidget QToolButton {{
                background-color: transparent;
                color: {Colors.WHITE};
                border: none;
                border-radius: {BorderRadius.MD};
                padding: 4px 8px;
                font-size: {Typography.FONT_SIZE_SM};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.18);
            }}
            QCalendarWidget QToolButton:pressed {{
                background-color: rgba(255, 255, 255, 0.30);
            }}

            /* Month/year label in the middle of nav bar */
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {{
                font-size: {Typography.FONT_SIZE_MD};
                font-weight: {Typography.FONT_WEIGHT_SEMIBOLD};
                padding: 4px 12px;
            }}

            /* The date grid */
            QCalendarWidget QAbstractItemView {{
                background-color: {Colors.WHITE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY};
                selection-color: {Colors.WHITE};
                alternate-background-color: {Colors.WHITE};
                gridline-color: {Colors.BORDER_LIGHT};
                outline: none;
                font-family: {Typography.FONT_FAMILY_PRIMARY};
                font-size: {Typography.FONT_SIZE_SM};
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: {Colors.TEXT_MUTED};
            }}

            /* Spin box for year if shown */
            QCalendarWidget QSpinBox {{
                background-color: transparent;
                color: {Colors.WHITE};
                border: none;
                font-size: {Typography.FONT_SIZE_SM};
                font-family: {Typography.FONT_FAMILY_PRIMARY};
            }}
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {{
                border: none;
                background: transparent;
            }}
        """)

    # ── UI construction ────────────────────────────────────────────────────────

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scrollable content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet(f"background-color: {Colors.BG_SECONDARY};")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(16, 16, 16, 8)
        scroll_layout.setSpacing(12)

        # ── Project Information ────────────────────────────────────────
        section, slayout = self._create_section("Project Information")
        form = self._make_form()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter project name")
        form.addRow(self._form_label("Project Name:"), self.name_input)

        self.project_status_combo = QComboBox()
        self.project_status_combo.addItems(["Planning", "Design", "Approved", "In Progress", "Completed"])
        form.addRow(self._form_label("Project Status:"), self.project_status_combo)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter project description")
        self.description_input.setMaximumHeight(80)
        form.addRow(self._form_label("Description:"), self.description_input)

        self.project_type_combo = QComboBox()
        self.project_type_combo.addItems(["Background Music", "Foreground Music", "Background & Foreground"])
        form.addRow(self._form_label("Project Type:"), self.project_type_combo)

        self.facility_type_combo = QComboBox()
        self.facility_type_combo.addItems([
            "Retail", "House of Worship", "Entertainment", "Corporate",
            "Healthcare", "Government", "K-12", "University",
            "Fitness Center/Gym", "Restaurant/Bar", "Other"
        ])
        form.addRow(self._form_label("Facility Type:"), self.facility_type_combo)

        self.budget_range_combo = QComboBox()
        self.budget_range_combo.addItems([
            "TBD", "Under $10k", "$10k - $25k", "$25k - $50k",
            "$50k - $100k", "$100k - $250k", "$250k+"
        ])
        form.addRow(self._form_label("Budget Range:"), self.budget_range_combo)

        self.installation_type_combo = QComboBox()
        self.installation_type_combo.addItems([
            "New Construction", "Retrofit", "Renovation", "Tenant Improvement", "Mixed"
        ])
        form.addRow(self._form_label("Installation Type:"), self.installation_type_combo)

        self.completion_date_input = QDateEdit()
        self.completion_date_input.setDate(QDate.currentDate().addMonths(3))
        self.completion_date_input.setCalendarPopup(True)
        form.addRow(self._form_label("Target Completion:"), self.completion_date_input)
        self._setup_calendar()

        slayout.addLayout(form)
        scroll_layout.addWidget(section)

        # ── Client & Contact ───────────────────────────────────────────
        section, slayout = self._create_section("Client & Contact Information")
        form = self._make_form()

        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Client or company name")
        form.addRow(self._form_label("Client Name:"), self.client_name_input)

        self.project_contact_input = QLineEdit()
        self.project_contact_input.setPlaceholderText("Primary contact person")
        form.addRow(self._form_label("Project Contact:"), self.project_contact_input)

        self.contact_phone_input = QLineEdit()
        self.contact_phone_input.setPlaceholderText("(555) 123-4567")
        self.contact_phone_input.editingFinished.connect(self.format_phone_on_focus_loss)
        form.addRow(self._form_label("Contact Phone:"), self.contact_phone_input)

        self.project_address_input = QLineEdit()
        self.project_address_input.setPlaceholderText("Street address")
        form.addRow(self._form_label("Address:"), self.project_address_input)

        self.project_city_input = QLineEdit()
        self.project_city_input.setPlaceholderText("City")
        form.addRow(self._form_label("City:"), self.project_city_input)

        state_zip_layout = QHBoxLayout()
        state_zip_layout.setSpacing(8)
        state_zip_layout.setContentsMargins(0, 0, 0, 0)
        self.project_state_input = QLineEdit()
        self.project_state_input.setPlaceholderText("State")
        self.project_state_input.setMaximumWidth(100)
        state_zip_layout.addWidget(self.project_state_input)
        self.project_zip_input = QLineEdit()
        self.project_zip_input.setPlaceholderText("ZIP Code")
        self.project_zip_input.setMaximumWidth(120)
        state_zip_layout.addWidget(self.project_zip_input)
        state_zip_layout.addStretch()
        state_zip_widget = QWidget()
        state_zip_widget.setStyleSheet("background: transparent;")
        state_zip_widget.setLayout(state_zip_layout)
        form.addRow(self._form_label("State / ZIP:"), state_zip_widget)

        slayout.addLayout(form)
        scroll_layout.addWidget(section)

        # ── System Requirements ────────────────────────────────────────
        section, slayout = self._create_section("System Requirements")
        form = self._make_form()

        self.audio_sources_combo = MultiSelectComboBox()
        self.audio_sources_combo.addItems([
            "Streaming Device", "Microphone/Paging", "Bluetooth Input",
            "CD Player", "AV Presentation", "FM/AM Radio Tuner",
            "Satellite Radio", "Auxiliary Input", "Network Audio Stream"
        ])
        form.addRow(self._form_label("Primary Audio Inputs:"), self.audio_sources_combo)

        self.control_system_combo = MultiSelectComboBox()
        self.control_system_combo.addItems([
            "Simple Volume Controls", "DSP-based System", "Integrated AV Control",
            "App-based Control", "Touch Panel Control", "Wall-mounted Controls", "Wireless Remote"
        ])
        form.addRow(self._form_label("Control Methods:"), self.control_system_combo)

        self.network_infrastructure_combo = QComboBox()
        self.network_infrastructure_combo.addItems([
            "Existing Network", "New Network Required", "Dante/AoIP Required",
            "Wireless Only", "TBD"
        ])
        form.addRow(self._form_label("Network Infrastructure:"), self.network_infrastructure_combo)

        self.environmental_factors_combo = MultiSelectComboBox()
        self.environmental_factors_combo.addItems([
            "Indoor Only", "Outdoor Zones Included", "Weather Resistance Required",
            "High Humidity Environment", "Temperature Extremes", "Standard Environment"
        ])
        form.addRow(self._form_label("Environmental Factors:"), self.environmental_factors_combo)

        slayout.addLayout(form)
        scroll_layout.addWidget(section)

        # ── Power Requirements ─────────────────────────────────────────
        section, slayout = self._create_section("Power Requirements")
        slayout.addWidget(self._hint_label("120V AC assumed available. Check additional requirements:"))

        self.ups_required_cb = QCheckBox("UPS/Battery Backup Required")
        self.voltage_240_cb = QCheckBox("240V Available/Required")
        self.power_conditioning_cb = QCheckBox("Power Conditioning Needed")
        self.dedicated_circuit_cb = QCheckBox("Dedicated Circuit Required")
        for cb in (self.ups_required_cb, self.voltage_240_cb,
                   self.power_conditioning_cb, self.dedicated_circuit_cb):
            slayout.addWidget(cb)

        scroll_layout.addWidget(section)

        # ── Project Notes ──────────────────────────────────────────────
        section, slayout = self._create_section("Project Notes")
        slayout.addWidget(self._hint_label(
            "Initial requirements, special considerations, constraints, etc."
        ))

        self.project_notes_input = QTextEdit()
        self.project_notes_input.setPlaceholderText(
            "Enter project notes here...\n\n"
            "Examples:\n"
            "• Initial client requirements and expectations\n"
            "• Architectural constraints or special considerations\n"
            "• Timeline requirements or scheduling notes\n"
            "• Budget discussions and priorities\n"
            "• Existing equipment to integrate or replace\n"
            "• Input sources needed: CD player, FM tuner, satellite radio, etc."
        )
        self.project_notes_input.setMinimumHeight(120)
        slayout.addWidget(self.project_notes_input)

        scroll_layout.addWidget(section)

        # Edit-mode notice
        if self.is_edit_mode:
            notice = QFrame()
            notice.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.WARNING_BG};
                    border: 1px solid {Colors.WARNING_BORDER_ALT};
                    border-radius: {BorderRadius.MD};
                }}
            """)
            notice_layout = QVBoxLayout(notice)
            notice_layout.setContentsMargins(12, 10, 12, 10)
            notice_label = QLabel(
                "<b>Note:</b> Changes to project information will be saved. "
                "Zone-specific settings like SPL targets and ceiling heights "
                "are configured in the Zones section."
            )
            notice_label.setWordWrap(True)
            notice_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_PRIMARY};
                    font-size: {Typography.FONT_SIZE_SM};
                    font-family: {Typography.FONT_FAMILY_PRIMARY};
                    background: transparent;
                    border: none;
                }}
            """)
            notice_layout.addWidget(notice_label)
            scroll_layout.addWidget(notice)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area, 1)

        # ── Button bar ─────────────────────────────────────────────────
        button_bar = QWidget()
        button_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.WHITE};
                border-top: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)
        bar_layout = QHBoxLayout(button_bar)
        bar_layout.setContentsMargins(16, 12, 16, 12)
        bar_layout.setSpacing(8)
        bar_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(ButtonStyles.get_secondary_button_style())
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setDefault(False)
        cancel_btn.setAutoDefault(False)

        save_btn = QPushButton("Save Changes" if self.is_edit_mode else "Create Project")
        save_btn.setStyleSheet(ButtonStyles.get_primary_button_style())
        save_btn.clicked.connect(self.validate_and_accept)
        save_btn.setDefault(True)

        bar_layout.addWidget(cancel_btn)
        bar_layout.addWidget(save_btn)
        main_layout.addWidget(button_bar)

    # ── Logic ──────────────────────────────────────────────────────────────────

    def format_phone_on_focus_loss(self):
        digits = re.sub(r'\D', '', self.contact_phone_input.text())
        if len(digits) == 10:
            self.contact_phone_input.setText(f"({digits[:3]}) {digits[3:6]}-{digits[6:]}")
        elif len(digits) == 11 and digits[0] == '1':
            self.contact_phone_input.setText(f"1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}")

    def populate_fields(self):
        self._set_combo_value(self.project_status_combo, self.existing_project.get('project_status', 'Planning'))
        self._set_combo_value(self.project_type_combo, self.existing_project.get('project_type', 'Background Music'))
        self._set_combo_value(self.facility_type_combo, self.existing_project.get('facility_type', 'Corporate'))
        self._set_combo_value(self.budget_range_combo, self.existing_project.get('budget_range', 'TBD'))
        self._set_combo_value(self.installation_type_combo, self.existing_project.get('installation_type', 'New Construction'))
        self._set_combo_value(self.network_infrastructure_combo, self.existing_project.get('network_infrastructure', 'TBD'))

        self.name_input.setText(self.existing_project.get('name', ''))
        self.description_input.setText(self.existing_project.get('description', ''))

        completion_date_str = self.existing_project.get('target_completion_date', '')
        if completion_date_str:
            date = QDate.fromString(completion_date_str, Qt.ISODate)
            if date.isValid():
                self.completion_date_input.setDate(date)

        self.client_name_input.setText(self.existing_project.get('client_name', ''))
        self.project_contact_input.setText(self.existing_project.get('project_contact', ''))
        self.contact_phone_input.setText(self.existing_project.get('contact_phone', ''))

        if 'project_address' in self.existing_project:
            self.project_address_input.setText(self.existing_project.get('project_address', ''))
            self.project_city_input.setText(self.existing_project.get('project_city', ''))
            self.project_state_input.setText(self.existing_project.get('project_state', ''))
            self.project_zip_input.setText(self.existing_project.get('project_zip', ''))
        elif self.existing_project.get('project_location'):
            self.project_address_input.setText(self.existing_project['project_location'])

        def _to_list(val, exclude='TBD'):
            if isinstance(val, list):
                return val
            return [val] if val and val != exclude else []

        self.audio_sources_combo.setCheckedItems(
            _to_list(self.existing_project.get('primary_audio_sources', []))
        )
        self.control_system_combo.setCheckedItems(
            _to_list(self.existing_project.get('control_system_type', []))
        )
        self.environmental_factors_combo.setCheckedItems(
            _to_list(self.existing_project.get('environmental_factors', []), exclude='Standard Environment')
        )

        self.ups_required_cb.setChecked(self.existing_project.get('ups_required', False))
        self.voltage_240_cb.setChecked(self.existing_project.get('voltage_240_available', False))
        self.power_conditioning_cb.setChecked(self.existing_project.get('power_conditioning_needed', False))
        self.dedicated_circuit_cb.setChecked(self.existing_project.get('dedicated_circuit_required', False))

        self.project_notes_input.setText(self.existing_project.get('project_notes', ''))

    def _set_combo_value(self, combo, value):
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            AlertDialog.show_warning(self, "Validation Error", "Project name is required.")
            self.name_input.setFocus()
            return
        self.accept()

    def get_project_data(self):
        project_data = {
            'name': self.name_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'project_type': self.project_type_combo.currentText(),
            'project_status': self.project_status_combo.currentText(),
            'facility_type': self.facility_type_combo.currentText(),
            'budget_range': self.budget_range_combo.currentText(),
            'installation_type': self.installation_type_combo.currentText(),
            'target_completion_date': self.completion_date_input.date().toString(Qt.ISODate),
            'client_name': self.client_name_input.text().strip(),
            'project_contact': self.project_contact_input.text().strip(),
            'contact_phone': self.contact_phone_input.text().strip(),
            'project_address': self.project_address_input.text().strip(),
            'project_city': self.project_city_input.text().strip(),
            'project_state': self.project_state_input.text().strip(),
            'project_zip': self.project_zip_input.text().strip(),
            'project_location': self._get_combined_address(),
            'primary_audio_sources': self.audio_sources_combo.getCheckedItems(),
            'control_system_type': self.control_system_combo.getCheckedItems(),
            'network_infrastructure': self.network_infrastructure_combo.currentText(),
            'environmental_factors': self.environmental_factors_combo.getCheckedItems(),
            'ups_required': self.ups_required_cb.isChecked(),
            'voltage_240_available': self.voltage_240_cb.isChecked(),
            'power_conditioning_needed': self.power_conditioning_cb.isChecked(),
            'dedicated_circuit_required': self.dedicated_circuit_cb.isChecked(),
            'project_notes': self.project_notes_input.toPlainText().strip(),
        }

        if self.is_edit_mode:
            project_data['id'] = self.existing_project.get('id')
            project_data['created_at'] = self.existing_project.get('created_at')
            for key in ('zones_data', 'preview_thumbnail'):
                if key in self.existing_project:
                    project_data[key] = self.existing_project[key]

        return project_data

    def _get_combined_address(self):
        parts = []
        address = self.project_address_input.text().strip()
        if address:
            parts.append(address)
        city_state_zip = [
            v for v in (
                self.project_city_input.text().strip(),
                self.project_state_input.text().strip(),
                self.project_zip_input.text().strip(),
            ) if v
        ]
        if city_state_zip:
            parts.append(', '.join(city_state_zip))
        return ', '.join(parts)
