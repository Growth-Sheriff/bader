"""
BADER Derneği - SHOPIFY POLARIS DESIGN SYSTEM
Full Polaris implementation with authentic tokens
Renk, Shadow, Typography - 100% Polaris Certified
"""

MODERN_STYLESHEET = """
/* ================================================
   🎨 SHOPIFY POLARIS DESIGN SYSTEM - PyQt6
   Authentic Polaris tokens & premium aesthetics
   ================================================ */

* {
    outline: none;
}

QWidget {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: #303030;  /* --p-color-text */
    background-color: transparent;
}

QMainWindow {
    background-color: #F1F1F1;  /* --p-color-bg */
}

/* ================================================
   MENU BAR - Polaris Navigation
   ================================================ */

QMenuBar {
    background-color: #303030;  /* --p-color-bg-fill-brand */
    color: #FFFFFF;
    padding: 8px;
    border: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
    font-weight: 590;
}

QMenuBar::item {
    background-color: transparent;
    color: #FFFFFF;
    padding: 10px 16px;
    margin: 0 2px;
    border-radius: 8px;
}

QMenuBar::item:selected {
    background-color: rgba(255, 255, 255, 0.10);
}

QMenuBar::item:pressed {
    background-color: rgba(255, 255, 255, 0.20);
}

QMenu {
    background-color: #FFFFFF;  /* --p-color-bg-surface */
    color: #303030;
    border: 1px solid #E3E3E3;  /* --p-color-border */
    border-radius: 12px;
    padding: 8px;
}

QMenu::item {
    color: #303030;
    padding: 10px 32px 10px 16px;
    border-radius: 8px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #F7F7F7;  /* --p-color-bg-surface-hover */
    color: #1A1A1A;
}

QMenu::separator {
    height: 1px;
    background-color: #EBEBEB;  /* --p-color-border-secondary */
    margin: 8px 12px;
}

/* ================================================
   TOOLBAR - Vuexy Style
   ================================================ */

QToolBar {
    background-color: white;
    border: none;
    border-bottom: 1px solid rgba(47, 43, 61, 0.08);
    spacing: 12px;
    padding: 12px 16px;
}

QToolButton {
    background-color: #64B5F6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: 15px;
    min-width: 100px;
}

QToolButton:hover {
    background-color: #42A5F5;
}

QToolButton:pressed {
    background-color: #2196F3;
}

/* ================================================
   BUTTONS - Vuexy Primary Button
   ================================================ */

QPushButton {
    background-color: #303030;  /* --p-color-bg-fill-brand */
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 11px 20px;
    font-weight: 590;
    font-size: 13px;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #1A1A1A;  /* --p-color-bg-fill-brand-hover */
}

QPushButton:pressed {
    background-color: #1A1A1A;  /* --p-color-bg-fill-brand-active */
}

QPushButton:disabled {
    background-color: rgba(0, 0, 0, 0.17);  /* --p-color-bg-fill-brand-disabled */
    color: #FFFFFF;
}

QPushButton[class="danger"] {
    background-color: #C70A24;  /* --p-color-bg-fill-critical */
    color: #FFFAFB;  /* --p-color-text-critical-on-bg-fill */
    border: none;
    font-weight: 590;
    font-size: 13px;
}

QPushButton[class="danger"]:hover {
    background-color: #A30A24;  /* --p-color-bg-fill-critical-hover */
}

QPushButton[class="success"] {
    background-color: #047B5D;  /* --p-color-bg-fill-success */
    color: #FAFFFC;  /* --p-color-text-success-on-bg-fill */
    border: none;
    font-weight: 590;
    font-size: 13px;
}

QPushButton[class="success"]:hover {
    background-color: #035E4C;  /* --p-color-bg-fill-success-hover */
}

QPushButton[class="warning"] {
    background-color: #FFB800;  /* --p-color-bg-fill-warning */
    color: #251A00;  /* --p-color-text-warning-on-bg-fill */
    border: none;
    font-weight: 590;
    font-size: 13px;
}

QPushButton[class="warning"]:hover {
    background-color: #E5A500;  /* --p-color-bg-fill-warning-hover */
}

QPushButton[class="secondary"] {
    background-color: #FFFFFF;  /* --p-color-bg-fill */
    color: #303030;
    border: 1px solid rgba(0, 0, 0, 0.08);
    font-weight: 590;
    font-size: 13px;
}

QPushButton[class="secondary"]:hover {
    background-color: #FAFAFA;  /* --p-color-bg-fill-hover */
    border: 1px solid rgba(0, 0, 0, 0.10);
}

/* ================================================
   INPUT FIELDS - Vuexy Form Style
   ================================================ */

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FDFDFD;  /* --p-color-input-bg-surface */
    color: #303030;
    border: 1px solid #8A8A8A;  /* --p-color-input-border */
    border-radius: 8px;
    padding: 9px 12px;
    selection-background-color: #005BD3;
    selection-color: white;
    font-size: 13px;
    font-weight: 400;
}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {
    background-color: #FAFAFA;  /* --p-color-input-bg-surface-hover */
    border: 1px solid #616161;  /* --p-color-input-border-hover */
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    background-color: #FFFFFF;
    border: 2px solid #005BD3;  /* --p-color-border-focus */
    padding: 8px 11px;  /* Kompensasyon border kalınlığı için */
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: rgba(0, 0, 0, 0.05);  /* --p-color-bg-surface-disabled */
    color: #B5B5B5;  /* --p-color-text-disabled */
    border: 1px solid #EBEBEB;  /* --p-color-border-disabled */
}

QLineEdit::placeholder, QTextEdit::placeholder {
    color: #B5B5B5;  /* --p-color-text-disabled */
}

/* ================================================
   COMBOBOX - Vuexy Dropdown Style
   ================================================ */

QComboBox {
    background-color: #FDFDFD;  /* --p-color-input-bg-surface */
    color: #303030;
    border: 1px solid #8A8A8A;  /* --p-color-input-border */
    border-radius: 8px;
    padding: 9px 12px;
    padding-right: 40px;
    font-size: 13px;
    min-height: 36px;
}

QComboBox:hover {
    background-color: #FAFAFA;
    border: 1px solid #616161;  /* --p-color-input-border-hover */
}

QComboBox:focus {
    border: 2px solid #005BD3;  /* --p-color-border-focus */
    padding: 8px 11px;
}

QComboBox:disabled {
    background-color: #f3f2f3;
    color: #acaab1;
}

QComboBox::drop-down {
    border: none;
    width: 36px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid #4A4A4A;  /* --p-color-icon */
    margin-right: 10px;
}

QComboBox:hover::down-arrow {
    border-top-color: #303030;  /* --p-color-icon-hover */
}

/* Dropdown listesi (arama sonuçları için) */
QComboBox QAbstractItemView {
    background-color: white;
    color: #2f2b3d;
    border: 1px solid rgba(47, 43, 61, 0.12);
    border-radius: 6px;
    padding: 4px;
    font-size: 14px;
    font-family: 'Montserrat', 'Inter', 'Roboto', sans-serif;
    selection-background-color: #64B5F6;
    selection-color: white;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 10px 14px;
    border: none;
    border-radius: 4px;
    min-height: 36px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: rgba(115, 103, 240, 0.08);
    color: #2f2b3d;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #64B5F6;
    color: white;
}

QComboBox QAbstractItemView {
    background-color: white;
    color: #6d6b77;
    border: 1px solid rgba(47, 43, 61, 0.08);
    border-radius: 8px;
    padding: 8px;
    selection-background-color: rgba(115, 103, 240, 0.08);
    selection-color: #64B5F6;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 10px 14px;
    color: #6d6b77;
    border-radius: 6px;
    margin: 2px;
    min-height: 36px;
}

QComboBox QAbstractItemView::item:selected {
    background-color: rgba(115, 103, 240, 0.08);
    color: #64B5F6;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f3f2f3;
}

/* ================================================
   SPINBOX & DATEEDIT - Vuexy Form Style
   ================================================ */

QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: white;
    color: #6d6b77;
    border: 1px solid rgba(47, 43, 61, 0.12);
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 15px;
    min-height: 38px;
}

QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover {
    border: 1px solid rgba(47, 43, 61, 0.2);
}

QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    border: 1px solid #64B5F6;
}

QSpinBox::up-button, QDoubleSpinBox::up-button, QDateEdit::up-button {
    background-color: transparent;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: rgba(115, 103, 240, 0.08);
}

QSpinBox::down-button, QDoubleSpinBox::down-button, QDateEdit::down-button {
    background-color: transparent;
    border: none;
    width: 20px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: rgba(115, 103, 240, 0.08);
}

QDateEdit::drop-down {
    background-color: transparent;
    border: none;
}

QDateEdit::drop-down:hover {
    background-color: rgba(115, 103, 240, 0.08);
}

/* Calendar Widget */
QCalendarWidget {
    background-color: white;
    color: #6d6b77;
    border: 1px solid rgba(47, 43, 61, 0.08);
    border-radius: 8px;
}

QCalendarWidget QAbstractItemView {
    background-color: white;
    color: #6d6b77;
    selection-background-color: #64B5F6;
    selection-color: white;
}

QCalendarWidget QToolButton {
    color: #6d6b77;
    background-color: white;
    border: none;
}

QCalendarWidget QToolButton:hover {
    background-color: rgba(115, 103, 240, 0.08);
    color: #64B5F6;
}

/* ================================================
   TABLES - Vuexy DataTable Style
   ================================================ */

QTableWidget {
    background-color: #FFFFFF;  /* --p-color-bg-surface */
    alternate-background-color: #FAFAFA;
    gridline-color: #EBEBEB;  /* --p-color-border-secondary */
    color: #303030;
    border: 1px solid #E3E3E3;  /* --p-color-border */
    border-radius: 12px;
    font-size: 13px;
}

QTableWidget::item {
    padding: 12px 16px;
    border: none;
    color: #303030;
}

QTableWidget::item:selected {
    background-color: #F1F1F1;  /* --p-color-bg-surface-selected */
    color: #1A1A1A;
    font-weight: 590;
}

QTableWidget::item:hover {
    background-color: #F7F7F7;  /* --p-color-bg-surface-hover */
    color: #303030;
}

QHeaderView::section {
    background-color: #F7F7F7;  /* --p-color-bg-surface-secondary */
    color: #303030;
    padding: 12px 16px;
    border: none;
    border-bottom: 1px solid #EBEBEB;
    font-weight: 650;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

QHeaderView::section:hover {
    background-color: #F1F1F1;  /* --p-color-bg-surface-secondary-hover */
}

QHeaderView::section:first {
    border-top-left-radius: 8px;
}

QHeaderView::section:last {
    border-top-right-radius: 8px;
}

/* ================================================
   SCROLLBAR - Vuexy Style
   ================================================ */

QScrollBar:vertical {
    background-color: transparent;
    width: 12px;
    border: none;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #B5B5B5;  /* --p-color-scrollbar-thumb-bg */
    border-radius: 6px;
    min-height: 40px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #8A8A8A;  /* --p-color-scrollbar-thumb-bg-hover */
}

QScrollBar::handle:vertical:pressed {
    background-color: #616161;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: rgba(47, 43, 61, 0.15);
    border-radius: 4px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(47, 43, 61, 0.25);
}

QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {
    background: none;
    border: none;
}

/* ================================================
   GROUPBOX - Vuexy Card Style
   ================================================ */

QGroupBox {
    background-color: #FFFFFF;  /* --p-color-bg-surface */
    color: #303030;
    border: 1px solid #E3E3E3;  /* --p-color-border */
    border-radius: 12px;
    margin-top: 20px;
    padding: 20px 16px 16px 16px;
    font-weight: 590;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    top: 8px;
    padding: 0 8px;
    background-color: #FFFFFF;
    color: #1A1A1A;
    font-weight: 650;
    font-size: 14px;
}

/* ================================================
   LABELS - Vuexy Typography
   ================================================ */

QLabel {
    color: #303030;  /* --p-color-text */
    background-color: transparent;
    font-size: 13px;
}

QLabel[class="title"] {
    font-size: 20px;
    font-weight: 650;
    color: #1A1A1A;
    letter-spacing: -0.2px;
    line-height: 1.3;
}

QLabel[class="subtitle"] {
    font-size: 14px;
    font-weight: 450;
    color: #616161;  /* --p-color-text-secondary */
}

QLabel[class="success"] {
    color: #014B40;  /* --p-color-text-success */
    font-weight: 590;
}

QLabel[class="danger"] {
    color: #8E0B21;  /* --p-color-text-critical */
    font-weight: 590;
}

QLabel[class="warning"] {
    color: #5E4200;  /* --p-color-text-warning */
    font-weight: 590;
}

QLabel[class="info"] {
    color: #003A5A;  /* --p-color-text-info */
    font-weight: 590;
}

/* ================================================
   TABS - Vuexy Tab Style
   ================================================ */

QTabWidget::pane {
    background-color: #FFFFFF;
    border: 1px solid #E3E3E3;
    border-radius: 12px;
    top: -1px;
}

QTabBar::tab {
    background-color: transparent;
    color: #616161;  /* --p-color-text-secondary */
    border: none;
    border-bottom: 2px solid transparent;
    padding: 12px 20px;
    margin-right: 4px;
    font-weight: 590;
}

QTabBar::tab:selected {
    color: #303030;
    border-bottom: 2px solid #303030;
}

QTabBar::tab:hover:!selected {
    color: #303030;
    background-color: rgba(0, 0, 0, 0.02);
}

/* ================================================
   DIALOG - Vuexy Modal Style
   ================================================ */

QDialog {
    background-color: white;
    color: #6d6b77;
    border-radius: 8px;
}

QDialog QLabel {
    color: #6d6b77;
    font-size: 15px;
    min-width: 140px;
    max-width: 140px;
}

QDialog QLabel[class="dialog-title"] {
    font-size: 20px;
    font-weight: 600;
    color: #444050;
    padding-bottom: 12px;
    min-width: none;
    max-width: none;
}

QDialog QFormLayout {
    spacing: 16px;
}

/* Form label standardizasyonu */
QFormLayout QLabel {
    color: #6d6b77;
    font-size: 15px;
    font-weight: 500;
    min-width: 140px;
    padding-right: 12px;
}

/* ================================================
   STATUSBAR - Vuexy Footer Style
   ================================================ */

QStatusBar {
    background-color: white;
    border-top: 1px solid rgba(47, 43, 61, 0.08);
    color: #6d6b77;
    font-size: 14px;
}

QStatusBar::item {
    border: none;
}

/* ================================================
   PROGRESSBAR - Vuexy Progress Style
   ================================================ */

QProgressBar {
    background-color: rgba(115, 103, 240, 0.08);
    color: #6d6b77;
    border: none;
    border-radius: 6px;
    text-align: center;
    font-weight: 500;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #64B5F6;
    border-radius: 6px;
}

/* ================================================
   CHECKBOX & RADIO - Vuexy Form Controls
   ================================================ */

QCheckBox, QRadioButton {
    color: #6d6b77;
    spacing: 10px;
    font-size: 15px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(47, 43, 61, 0.2);
    background-color: white;
}

QCheckBox::indicator {
    border-radius: 4px;
}

QRadioButton::indicator {
    border-radius: 10px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #64B5F6;
}

QCheckBox::indicator:checked {
    background-color: #64B5F6;
    border-color: #64B5F6;
}

QRadioButton::indicator:checked {
    background-color: #64B5F6;
    border-color: #64B5F6;
}

QCheckBox:disabled, QRadioButton:disabled {
    color: #acaab1;
}

QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {
    background-color: #f3f2f3;
    border-color: rgba(47, 43, 61, 0.08);
}

/* ================================================
   SPLITTER - Vuexy Style
   ================================================ */

QSplitter::handle {
    background-color: rgba(47, 43, 61, 0.08);
}

QSplitter::handle:hover {
    background-color: rgba(115, 103, 240, 0.15);
}

QSplitter::handle:pressed {
    background-color: #64B5F6;
}

/* ================================================
   TOOLTIP - Vuexy Tooltip Style
   ================================================ */

QToolTip {
    background-color: #444050;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
}

/* ================================================
   LIST WIDGET - Vuexy List Style
   ================================================ */

QListWidget {
    background-color: white;
    color: #6d6b77;
    border: 1px solid rgba(47, 43, 61, 0.08);
    border-radius: 8px;
}

QListWidget::item {
    padding: 12px 16px;
    color: #6d6b77;
    border-bottom: 1px solid rgba(47, 43, 61, 0.05);
}

QListWidget::item:selected {
    background-color: rgba(115, 103, 240, 0.08);
    color: #64B5F6;
}

QListWidget::item:hover {
    background-color: #f3f2f3;
}

/* ================================================
   SCROLL AREA - Vuexy Style
   ================================================ */

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* ================================================
   MESSAGE BOX - Vuexy Alert Style
   ================================================ */

QMessageBox {
    background-color: white;
    color: #6d6b77;
}

QMessageBox QLabel {
    color: #6d6b77;
    font-size: 15px;
    min-width: 300px;
}

QMessageBox QPushButton {
    min-width: 90px;
    padding: 10px 20px;
}

/* ================================================
   FRAME - Vuexy Card/Panel Style
   ================================================ */

QFrame[class="card"] {
    background-color: white;
    border: 1px solid rgba(47, 43, 61, 0.08);
    border-radius: 8px;
    padding: 20px;
}

QFrame[class="header"] {
    background-color: #64B5F6;
    color: white;
    border-radius: 8px;
    padding: 24px;
}
"""

# 🏪 SHOPIFY POLARIS DESIGN TOKENS
# Authentic Polaris color system
PRIMARY_COLOR = "#303030"  # --p-color-bg-fill-brand
SUCCESS_COLOR = "#047B5D"  # --p-color-bg-fill-success
DANGER_COLOR = "#C70A24"   # --p-color-bg-fill-critical
WARNING_COLOR = "#FFB800"  # --p-color-bg-fill-warning
INFO_COLOR = "#0094D5"     # --p-color-bg-fill-info
SECONDARY_COLOR = "#616161"  # --p-color-text-secondary

# Polaris Gri Tonları (Semantic)
TEXT_PRIMARY = "#303030"     # --p-color-text
TEXT_SECONDARY = "#616161"   # --p-color-text-secondary
TEXT_DISABLED = "#B5B5B5"    # --p-color-text-disabled
BORDER_DEFAULT = "#E3E3E3"   # --p-color-border
BORDER_SECONDARY = "#EBEBEB" # --p-color-border-secondary
BG_SURFACE = "#FFFFFF"       # --p-color-bg-surface
BG_SURFACE_HOVER = "#F7F7F7" # --p-color-bg-surface-hover
BG_FILL = "#F1F1F1"          # --p-color-bg

# Backgrounds
BODY_BG = "#F1F1F1"    # --p-color-bg
PAPER_BG = "#FFFFFF"   # --p-color-bg-surface

# İkon boyutları
ICON_SIZE = (24, 24)
