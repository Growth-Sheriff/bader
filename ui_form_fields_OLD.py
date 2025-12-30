"""
BADER Derneği - Standart Form Field Widgets
Eşit boyutlu, tutarlı form elemanları
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QSpinBox,
                             QDoubleSpinBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from ui_helpers import make_searchable_combobox


class FormField(QWidget):
    """Standart form field - Label + Input"""
    
    LABEL_WIDTH = 140  # Sabit label genişliği
    
    def __init__(self, label_text: str, widget: QWidget, required: bool = False):
        super().__init__()
        self.label_text = label_text
        self.input_widget = widget
        self.required = required
        self.setup_ui()
        
    def setup_ui(self):
        """UI'ı oluştur"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Label - SABİT genişlik - Polaris style
        label = QLabel(self.label_text)
        label.setStyleSheet("""
            QLabel {
                color: #303030;
                font-size: 13px;
                font-weight: 590;
            }
        """)
        label.setFixedWidth(self.LABEL_WIDTH)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label)
        
        # Input widget - EXPAND - Polaris height
        self.input_widget.setMinimumHeight(36)
        layout.addWidget(self.input_widget, 1)
        
        self.setLayout(layout)


def create_line_edit(label: str, placeholder: str = "") -> tuple[QWidget, QLineEdit]:
    """Standard QLineEdit oluştur - (container, widget) döndürür"""
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    container = FormField(label, edit)
    return (container, edit)


def create_text_edit(label: str, placeholder: str = "", max_height: int = 100) -> tuple[QWidget, QTextEdit]:
    """Standard QTextEdit oluştur - (container, widget) döndürür"""
    edit = QTextEdit()
    edit.setPlaceholderText(placeholder)
    edit.setMaximumHeight(max_height)
    container = FormField(label, edit)
    return (container, edit)


def create_combo_box(label: str, searchable: bool = True) -> tuple[QWidget, QComboBox]:
    """Standard QComboBox oluştur (arama özellikli) - (container, widget) döndürür"""
    combo = QComboBox()
    if searchable:
        make_searchable_combobox(combo)
    container = FormField(label, combo)
    return (container, combo)


def create_spin_box(label: str, minimum: int = 0, maximum: int = 999999, value: int = 0) -> tuple[QWidget, QSpinBox]:
    """Standard QSpinBox oluştur - (container, widget) döndürür"""
    spin = QSpinBox()
    spin.setMinimum(minimum)
    spin.setMaximum(maximum)
    spin.setValue(value)
    container = FormField(label, spin)
    return (container, spin)


def create_double_spin_box(label: str, minimum: float = 0.0, maximum: float = 999999.99, 
                           value: float = 0.0, suffix: str = "") -> tuple[QWidget, QDoubleSpinBox]:
    """Standard QDoubleSpinBox oluştur - (container, widget) döndürür"""
    spin = QDoubleSpinBox()
    spin.setMinimum(minimum)
    spin.setMaximum(maximum)
    spin.setValue(value)
    spin.setDecimals(2)
    if suffix:
        spin.setSuffix(suffix)
    container = FormField(label, spin)
    return (container, spin)


def create_date_edit(label: str, date: QDate = None) -> tuple[QWidget, QDateEdit]:
    """Standard QDateEdit oluştur - (container, widget) döndürür"""
    edit = QDateEdit()
    edit.setDate(date or QDate.currentDate())
    edit.setCalendarPopup(True)
    container = FormField(label, edit)
    return (container, edit)

