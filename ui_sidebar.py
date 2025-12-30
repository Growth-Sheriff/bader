"""
BADER Derneği - Vuexy Style Sidebar Navigation
Sol taraf vertical menü sistemi - Tab destekli (BADER / KÖY)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFrame, QScrollArea, QSpacerItem, QSizePolicy, QStackedWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont


class TabButton(QPushButton):
    """🎨 Polaris Tab Button"""
    
    def __init__(self, text: str):
        super().__init__(text)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #616161;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 12px 16px;
                font-size: 13px;
                font-weight: 590;
            }
            QPushButton:hover {
                color: #303030;
                background-color: rgba(0, 0, 0, 0.02);
            }
            QPushButton:checked {
                color: #303030;
                border-bottom: 2px solid #303030;
            }
        """)


class SidebarButton(QPushButton):
    """🎨 Polaris Navigation Item"""
    
    def __init__(self, text: str, icon: str = ""):
        super().__init__()
        self.setText(f"  {icon}  {text}" if icon else f"  {text}")
        self.setCheckable(True)
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Polaris navigation style
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #303030;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 590;
                margin: 2px 8px;
            }
            QPushButton:hover {
                background-color: #F7F7F7;
            }
            QPushButton:checked {
                background-color: #F1F1F1;
                color: #1A1A1A;
                font-weight: 650;
            }
            QPushButton:pressed {
                background-color: #EBEBEB;
            }
        """)


class Sidebar(QWidget):
    """Vuexy-style sol sidebar menü - Tab destekli (BADER / KÖY)"""
    
    # Signals
    menu_clicked = pyqtSignal(str)  # Menü adı
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.buttons = {}
        self.current_tab = "bader"
        self.setup_ui()
        
    def setup_ui(self):
        """UI'ı oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-right: 1px solid #E3E3E3;
            }
        """)
        
        # Logo/Brand alanı - Polaris style
        brand_frame = QFrame()
        brand_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-bottom: 1px solid #EBEBEB;
            }
        """)
        brand_layout = QVBoxLayout()
        brand_layout.setContentsMargins(16, 20, 16, 16)
        
        logo_label = QLabel("BADER")
        logo_label.setStyleSheet("""
            QLabel {
                color: #303030;
                font-size: 22px;
                font-weight: 700;
                letter-spacing: 0.5px;
                background: transparent;
                border: none;
            }
        """)
        brand_layout.addWidget(logo_label)
        
        subtitle_label = QLabel("Dernek & Köy Yönetim")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #97959e;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
        """)
        brand_layout.addWidget(subtitle_label)
        
        # Tab butonları
        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(0, 15, 0, 0)
        tab_layout.setSpacing(0)
        
        self.bader_tab = TabButton("BADER")
        self.bader_tab.setChecked(True)
        self.bader_tab.clicked.connect(lambda: self.switch_tab("bader"))
        tab_layout.addWidget(self.bader_tab)
        
        self.koy_tab = TabButton("KÖY")
        self.koy_tab.clicked.connect(lambda: self.switch_tab("koy"))
        tab_layout.addWidget(self.koy_tab)
        
        tab_layout.addStretch()
        brand_layout.addLayout(tab_layout)
        
        brand_frame.setLayout(brand_layout)
        layout.addWidget(brand_frame)
        
        # Stacked widget for menus
        self.menu_stack = QStackedWidget()
        
        # BADER menüsü
        bader_menu = self._create_bader_menu()
        self.menu_stack.addWidget(bader_menu)
        
        # KÖY menüsü
        koy_menu = self._create_koy_menu()
        self.menu_stack.addWidget(koy_menu)
        
        layout.addWidget(self.menu_stack)
        
        self.setLayout(layout)
        
        # İlk menüyü seç
        if "dashboard" in self.buttons:
            self.buttons["dashboard"].setChecked(True)
    
    def _create_bader_menu(self) -> QWidget:
        """BADER menüsünü oluştur"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        menu_widget = QWidget()
        menu_widget.setStyleSheet("background: transparent;")
        menu_layout = QVBoxLayout()
        menu_layout.setContentsMargins(0, 16, 0, 16)
        menu_layout.setSpacing(4)
        
        menu_header_style = """
            QLabel {
                color: #acaab1;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                padding: 8px 20px;
                background: transparent;
                border: none;
            }
        """
        
        # Ana Menü
        menu_header = QLabel("ANA MENÜ")
        menu_header.setStyleSheet(menu_header_style)
        menu_layout.addWidget(menu_header)
        
        self.create_menu_item(menu_layout, "dashboard", "📊", "Dashboard")
        
        menu_layout.addSpacing(8)
        
        # İşlemler
        islemler_header = QLabel("İŞLEMLER")
        islemler_header.setStyleSheet(menu_header_style)
        menu_layout.addWidget(islemler_header)
        
        self.create_menu_item(menu_layout, "uyeler", "👥", "Üyeler")
        self.create_menu_item(menu_layout, "ayrilanlar", "👤", "Ayrılan Üyeler")
        self.create_menu_item(menu_layout, "aidat", "💳", "Aidat Takip")
        self.create_menu_item(menu_layout, "gelir", "📈", "Gelir Yönetimi")
        self.create_menu_item(menu_layout, "gider", "📉", "Gider Yönetimi")
        self.create_menu_item(menu_layout, "virman", "💱", "Virman")
        self.create_menu_item(menu_layout, "kasa", "💰", "Kasa Yönetimi")
        
        menu_layout.addSpacing(8)
        
        # Etkinlik & Toplantı
        etkinlik_header = QLabel("ETKİNLİK & TOPLANTI")
        etkinlik_header.setStyleSheet(menu_header_style)
        menu_layout.addWidget(etkinlik_header)
        
        self.create_menu_item(menu_layout, "etkinlikler", "🎉", "Etkinlikler")
        self.create_menu_item(menu_layout, "toplantilar", "📋", "Toplantılar")
        
        menu_layout.addSpacing(8)
        
        # Raporlar & Belgeler
        rapor_header = QLabel("RAPORLAR & BELGELER")
        rapor_header.setStyleSheet(menu_header_style)
        menu_layout.addWidget(rapor_header)
        
        self.create_menu_item(menu_layout, "raporlar", "📊", "Raporlar")
        self.create_menu_item(menu_layout, "tahakkuk", "📅", "Tahakkuk Raporu")
        self.create_menu_item(menu_layout, "butce", "💵", "Bütçe Planlama")
        self.create_menu_item(menu_layout, "belgeler", "📎", "Belgeler")
        
        menu_layout.addSpacing(8)
        
        # Sistem
        sistem_header = QLabel("SİSTEM")
        sistem_header.setStyleSheet(menu_header_style)
        menu_layout.addWidget(sistem_header)
        
        self.create_menu_item(menu_layout, "devir", "🔄", "Yıl Sonu Devir")
        self.create_menu_item(menu_layout, "export", "📦", "Export & Yedekleme")
        self.create_menu_item(menu_layout, "kullanicilar", "🔑", "Kullanıcılar")
        self.create_menu_item(menu_layout, "ayarlar", "⚙️", "Ayarlar")
        
        menu_layout.addStretch()
        menu_widget.setLayout(menu_layout)
        scroll.setWidget(menu_widget)
        
        return scroll
    
    def _create_koy_menu(self) -> QWidget:
        """KÖY menüsünü oluştur"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        menu_widget = QWidget()
        menu_widget.setStyleSheet("background: transparent;")
        menu_layout = QVBoxLayout()
        menu_layout.setContentsMargins(0, 16, 0, 16)
        menu_layout.setSpacing(4)
        
        menu_header_style = """
            QLabel {
                color: #acaab1;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                padding: 8px 20px;
                background: transparent;
                border: none;
            }
        """
        
        # Köy Ana Menü
        menu_header = QLabel("KÖY İŞLEMLERİ")
        menu_header.setStyleSheet(menu_header_style)
        menu_layout.addWidget(menu_header)
        
        self.create_menu_item(menu_layout, "koy_dashboard", "📊", "Köy Dashboard")
        
        menu_layout.addSpacing(8)
        
        # Mali İşlemler
        mali_header = QLabel("MALİ İŞLEMLER")
        mali_header.setStyleSheet(menu_header_style)
        menu_layout.addWidget(mali_header)
        
        self.create_menu_item(menu_layout, "koy_gelir", "📈", "Köy Gelirleri")
        self.create_menu_item(menu_layout, "koy_gider", "📉", "Köy Giderleri")
        self.create_menu_item(menu_layout, "koy_virman", "💱", "Köy Virmanları")
        self.create_menu_item(menu_layout, "koy_kasa", "💰", "Köy Kasaları")
        
        menu_layout.addStretch()
        menu_widget.setLayout(menu_layout)
        scroll.setWidget(menu_widget)
        
        return scroll
    
    def switch_tab(self, tab: str):
        """Tab değiştir"""
        self.current_tab = tab
        
        if tab == "bader":
            self.bader_tab.setChecked(True)
            self.koy_tab.setChecked(False)
            self.menu_stack.setCurrentIndex(0)
        else:
            self.bader_tab.setChecked(False)
            self.koy_tab.setChecked(True)
            self.menu_stack.setCurrentIndex(1)
        
    def create_menu_item(self, layout, menu_id: str, icon: str, text: str):
        """Menü öğesi oluştur"""
        btn = SidebarButton(text, icon)
        btn.clicked.connect(lambda checked, mid=menu_id: self.on_menu_click(mid))
        self.buttons[menu_id] = btn
        layout.addWidget(btn)
        
    def on_menu_click(self, menu_id: str):
        """Menü tıklandığında"""
        # Tüm butonları deselect et
        for btn_id, btn in self.buttons.items():
            if btn_id != menu_id:
                btn.setChecked(False)
        
        # Tıklanan butonu select et
        if menu_id in self.buttons:
            self.buttons[menu_id].setChecked(True)
        
        # Signal gönder
        self.menu_clicked.emit(menu_id)
        
    def set_active_menu(self, menu_id: str):
        """Aktif menüyü dışarıdan ayarla"""
        if menu_id in self.buttons:
            self.on_menu_click(menu_id)


