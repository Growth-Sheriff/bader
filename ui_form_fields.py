"""
BADER Derneği - Standart Form Field Widgets
Modern FluentWidgets Uyumlu - Polaris Design
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QSpinBox,
                             QDoubleSpinBox, QDateEdit, QFrame)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont


# Modern Input Stilleri
INPUT_STYLE = """
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
        background-color: #FAFAFA;
        border: 1.5px solid #E0E0E0;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 14px;
        font-family: 'Inter', 'Roboto', 'Segoe UI', sans-serif;
        color: #1A1A1A;
        min-height: 20px;
    }
    QLineEdit:focus, QTextEdit:focus, 
    QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
        border: 2px solid #64B5F6;
        background-color: #FFFFFF;
    }
    QLineEdit:hover, QTextEdit:hover,
    QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover {
        border-color: #BDBDBD;
        background-color: #FFFFFF;
    }
    QComboBox {
        background-color: #FAFAFA;
        border: 1.5px solid #E0E0E0;
        border-radius: 8px;
        padding: 10px 14px;
        padding-right: 30px;
        font-size: 14px;
        font-family: 'Inter', 'Roboto', 'Segoe UI', sans-serif;
        color: #1A1A1A;
        min-height: 20px;
    }
    QComboBox:focus {
        border: 2px solid #64B5F6;
        background-color: #FFFFFF;
    }
    QComboBox:hover {
        border-color: #BDBDBD;
        background-color: #FFFFFF;
    }
    QComboBox:on {
        border: 2px solid #64B5F6;
        background-color: #FFFFFF;
    }
    QComboBox::drop-down {
        border: none;
        width: 30px;
        subcontrol-origin: padding;
        subcontrol-position: right center;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #666;
        margin-right: 10px;
    }
    QComboBox QAbstractItemView {
        background-color: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 4px;
        selection-background-color: #E3F2FD;
        selection-color: #1976D2;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        min-height: 32px;
        padding: 6px 12px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #F5F5F5;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: #E3F2FD;
        color: #1976D2;
    }
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 24px;
        border: none;
        background: transparent;
    }
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 24px;
        border: none;
        background: transparent;
    }
"""

LABEL_STYLE = """
    QLabel {
        color: #424242;
        font-size: 13px;
        font-weight: 600;
        font-family: 'Inter', 'Roboto', 'Segoe UI', sans-serif;
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
    }
"""


class FormField(QWidget):
    """Modern Form Field - Dikey Label + Input"""
    
    def __init__(self, label_text: str, widget: QWidget, required: bool = False, hint: str = ""):
        super().__init__()
        self.label_text = label_text
        self.input_widget = widget
        self.required = required
        self.hint = hint
        self.setup_ui()
        
    def setup_ui(self):
        """UI'ı oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(6)
        
        # Label satırı
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(4)
        
        # Label
        label = QLabel(self.label_text)
        label.setStyleSheet(LABEL_STYLE)
        label_layout.addWidget(label)
        
        # Required yıldız
        if self.required or self.label_text.endswith('*'):
            star = QLabel("*")
            star.setStyleSheet("color: #F44336; font-size: 14px; font-weight: bold;")
            label_layout.addWidget(star)
        
        label_layout.addStretch()
        layout.addLayout(label_layout)
        
        # Input widget
        self.input_widget.setStyleSheet(INPUT_STYLE)
        self.input_widget.setMinimumHeight(42)
        layout.addWidget(self.input_widget)
        
        # Hint text (opsiyonel)
        if self.hint:
            hint_label = QLabel(self.hint)
            hint_label.setStyleSheet("color: #9E9E9E; font-size: 11px;")
            layout.addWidget(hint_label)
        
        self.setLayout(layout)


def create_line_edit(label: str, placeholder: str = "", hint: str = "") -> tuple[QWidget, QLineEdit]:
    """Modern QLineEdit oluştur"""
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    required = label.endswith('*') or '*' in label
    container = FormField(label.replace('*', '').strip(), edit, required=required, hint=hint)
    return (container, edit)


def create_text_edit(label: str, placeholder: str = "", max_height: int = 100) -> tuple[QWidget, QTextEdit]:
    """Modern QTextEdit oluştur"""
    edit = QTextEdit()
    edit.setPlaceholderText(placeholder)
    edit.setMaximumHeight(max_height)
    required = label.endswith('*') or '*' in label
    container = FormField(label.replace('*', '').strip(), edit, required=required)
    return (container, edit)


def create_combo_box(label: str, items: list = None, searchable: bool = False) -> tuple[QWidget, QComboBox]:
    """Modern QComboBox oluştur"""
    combo = QComboBox()
    combo.setMaxVisibleItems(15)  # Dropdown'da daha fazla öğe göster
    combo.setMinimumWidth(150)  # Minimum genişlik
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
    
    if items:
        combo.addItems(items)
    if searchable:
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        if combo.completer():
            combo.completer().setCompletionMode(combo.completer().CompletionMode.PopupCompletion)
            combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
    
    required = label.endswith('*') or '*' in label
    container = FormField(label.replace('*', '').strip(), combo, required=required)
    return (container, combo)


def create_spin_box(label: str, minimum: int = 0, maximum: int = 999999, value: int = 0) -> tuple[QWidget, QSpinBox]:
    """Modern QSpinBox oluştur"""
    spin = QSpinBox()
    spin.setMinimum(minimum)
    spin.setMaximum(maximum)
    spin.setValue(value)
    required = label.endswith('*') or '*' in label
    container = FormField(label.replace('*', '').strip(), spin, required=required)
    return (container, spin)


def create_double_spin_box(label: str, minimum: float = 0.0, maximum: float = 999999.99, 
                           suffix: str = " ₺", decimals: int = 2) -> tuple[QWidget, QDoubleSpinBox]:
    """Modern QDoubleSpinBox oluştur"""
    spin = QDoubleSpinBox()
    spin.setMinimum(minimum)
    spin.setMaximum(maximum)
    spin.setDecimals(decimals)
    if suffix:
        spin.setSuffix(suffix)
    required = label.endswith('*') or '*' in label
    container = FormField(label.replace('*', '').strip(), spin, required=required)
    return (container, spin)


def create_date_edit(label: str, date: QDate = None) -> tuple[QWidget, QDateEdit]:
    """Modern QDateEdit oluştur"""
    edit = QDateEdit()
    edit.setDate(date or QDate.currentDate())
    edit.setCalendarPopup(True)
    edit.setDisplayFormat("dd.MM.yyyy")
    required = label.endswith('*') or '*' in label
    container = FormField(label.replace('*', '').strip(), edit, required=required)
    return (container, edit)


# Section başlık oluşturucu
def create_section_label(text: str, color: str = "#64B5F6") -> QLabel:
    """Form section başlığı oluştur"""
    label = QLabel(text.upper())
    label.setStyleSheet(f"""
        QLabel {{
            color: {color};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 12px 0 8px 0;
            border-bottom: 2px solid {color};
            margin-top: 8px;
            background: transparent;
        }}
    """)
    return label


# Eski API uyumluluğu için wrapper'lar
def make_searchable_combobox(combo: QComboBox):
    """ComboBox'ı aranabilir yap"""
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    if combo.completer():
        combo.completer().setCompletionMode(combo.completer().CompletionMode.PopupCompletion)

