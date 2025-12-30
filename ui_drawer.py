"""
BADER Derneği - Drawer Panel Widget
Sağdan açılan animasyonlu form paneli
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QColor


class DrawerPanel(QWidget):
    """Sağdan açılan animasyonlu panel"""
    
    accepted = pyqtSignal()  # Kaydet butonuna tıklandığında
    rejected = pyqtSignal()  # İptal butonuna tıklandığında
    closed = pyqtSignal()  # Panel kapatıldığında
    
    def __init__(self, parent, title: str, content_widget: QWidget, width=500):
        super().__init__(parent)
        self.drawer_width = width
        self.is_open = False
        self._title = title
        self._content_widget = content_widget
        self.setup_ui()
        self.set_title(title)
        self.set_content(content_widget)
        
    def setup_ui(self):
        """UI'ı oluştur"""
        # Overlay (karartma efekti)
        self.overlay = QFrame(self.parent())
        self.overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(47, 43, 61, 0.5);
            }
        """)
        self.overlay.hide()
        self.overlay.mousePressEvent = lambda e: self.close_drawer()
        
        # Drawer container
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-left: 1px solid rgba(47, 43, 61, 0.08);
            }
        """)
        
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid rgba(47, 43, 61, 0.08);
                padding: 20px;
            }
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        self.title_label = QLabel("Form")
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #2f2b3d;
            font-family: 'Montserrat', sans-serif;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Geri ok butonu
        back_btn = QPushButton("←")
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64B5F6;
                font-size: 28px;
                font-weight: 600;
                padding: 0;
                min-width: 40px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: rgba(115, 103, 240, 0.08);
                border-radius: 6px;
            }
        """)
        back_btn.clicked.connect(self.close_drawer)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setToolTip("Geri")
        header_layout.addWidget(back_btn)
        
        header.setLayout(header_layout)
        main_layout.addWidget(header)
        
        # Content area (scroll)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: none;
            }
        """)
        # Scroll area'nın büyümesine izin ver ama footer'a yer bırak
        from PyQt5.QtWidgets import QSizePolicy
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: white;")
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(20)
        self.content_widget.setLayout(self.content_layout)
        
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)
        
        # Footer (butonlar) - TAMAMEN SABİT
        footer = QFrame()
        footer.setFixedHeight(80)  # Daha yüksek
        footer.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid rgba(47, 43, 61, 0.08);
            }
        """)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(24, 20, 24, 20)
        footer_layout.setSpacing(12)
        
        footer_layout.addStretch()
        
        # İptal butonu
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setMinimumWidth(110)
        self.cancel_btn.setMinimumHeight(42)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f2f3;
                color: #2f2b3d;
                border: 1px solid rgba(47, 43, 61, 0.12);
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Montserrat', 'Inter', 'Roboto', sans-serif;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #e8e7ea;
                border-color: rgba(47, 43, 61, 0.2);
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        footer_layout.addWidget(self.cancel_btn)
        
        # Kaydet butonu
        self.submit_btn = QPushButton("Kaydet")
        self.submit_btn.setMinimumWidth(110)
        self.submit_btn.setMinimumHeight(42)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #64B5F6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                font-family: 'Montserrat', 'Inter', 'Roboto', sans-serif;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
            QPushButton:pressed {
                background-color: #2196F3;
            }
        """)
        self.submit_btn.clicked.connect(self._on_submit)
        footer_layout.addWidget(self.submit_btn)
        
        footer.setLayout(footer_layout)
        main_layout.addWidget(footer)
        
        self.setLayout(main_layout)
        
        # Başlangıçta gizli
        self.hide()
        
    def set_content(self, widget: QWidget):
        """İçerik widget'ını ayarla"""
        # Mevcut içeriği temizle
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Yeni widget ekle
        self.content_layout.addWidget(widget)
        self.content_layout.addStretch()
        
    def set_title(self, title: str):
        """Başlığı ayarla"""
        self.title_label.setText(title)
        
    def open_drawer(self):
        """Drawer'ı aç (animasyonlu)"""
        if self.is_open:
            return
            
        self.is_open = True
        
        # Parent boyutunu al
        parent_width = self.parent().width()
        parent_height = self.parent().height()
        
        # Overlay'i göster ve ÖNE ÇIKAR
        self.overlay.setGeometry(0, 0, parent_width, parent_height)
        self.overlay.show()
        self.overlay.raise_()  # EN ÖNE ÇIKAR
        
        # Drawer'ı sağda konumlandır (başlangıçta dışarıda)
        self.setGeometry(parent_width, 0, self.drawer_width, parent_height)
        self.show()
        self.raise_()  # EN ÖNE ÇIKAR
        
        # Animasyon
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)  # 300ms
        self.animation.setStartValue(QRect(parent_width, 0, self.drawer_width, parent_height))
        self.animation.setEndValue(QRect(parent_width - self.drawer_width, 0, self.drawer_width, parent_height))
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        
    def close_drawer(self):
        """Drawer'ı kapat (animasyonlu)"""
        if not self.is_open:
            return
            
        self.is_open = False
        
        # Animasyon
        parent_width = self.parent().width()
        parent_height = self.parent().height()
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(250)  # 250ms
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(parent_width, 0, self.drawer_width, parent_height))
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.animation.finished.connect(self._on_close_finished)
        self.animation.start()
        
    def _on_close_finished(self):
        """Kapanma animasyonu bittiğinde"""
        self.hide()
        self.overlay.hide()
        self.closed.emit()
    
    def _on_submit(self):
        """Kaydet butonuna tıklandığında"""
        self.accepted.emit()
    
    def _on_cancel(self):
        """İptal butonuna tıklandığında"""
        self.rejected.emit()
        self.close_drawer()
    
    def show(self):
        """Drawer'ı göster (override)"""
        super().show()
        self.open_drawer()
    
    def close(self):
        """Drawer'ı kapat (override)"""
        self.close_drawer()
        
    def resizeEvent(self, event):
        """Parent resize olduğunda"""
        super().resizeEvent(event)
        if self.is_open and self.parent():
            parent_width = self.parent().width()
            parent_height = self.parent().height()
            self.setGeometry(parent_width - self.drawer_width, 0, self.drawer_width, parent_height)
            self.overlay.setGeometry(0, 0, parent_width, parent_height)

