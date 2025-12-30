"""
BADER Derneği - Köy İşlemleri Dashboard
Köy modülü ana sayfa ve özet bilgiler
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt
from database import Database
from models import KoyKasaYoneticisi, KoyGelirYoneticisi, KoyGiderYoneticisi
from datetime import datetime


class StatCard(QFrame):
    """İstatistik kartı"""
    
    def __init__(self, title: str, value: str, color: str = "#64B5F6"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
        """)
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #97959e;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(title_label)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 24px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.value_label)
        
        self.setLayout(layout)
    
    def set_value(self, value: str):
        self.value_label.setText(value)


class KoyDashboardWidget(QWidget):
    """Köy işlemleri dashboard"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.kasa_yoneticisi = KoyKasaYoneticisi(db)
        self.gelir_yoneticisi = KoyGelirYoneticisi(db)
        self.gider_yoneticisi = KoyGiderYoneticisi(db)
        
        self.setup_ui()
        self.load_dashboard()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Başlık
        title = QLabel("KÖY İŞLEMLERİ DASHBOARD")
        title.setStyleSheet("""
            QLabel {
                color: #444050;
                font-size: 22px;
                font-weight: 700;
            }
        """)
        layout.addWidget(title)
        
        # Özet bilgi
        info = QLabel(f"📅 {datetime.now().year} Yılı Özeti")
        info.setStyleSheet("color: #97959e; font-size: 14px;")
        layout.addWidget(info)
        
        # İstatistik kartları
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        
        self.gelir_card = StatCard("TOPLAM GELİR", "0.00 ₺", "#4CAF50")
        cards_layout.addWidget(self.gelir_card, 0, 0)
        
        self.gider_card = StatCard("TOPLAM GİDER", "0.00 ₺", "#f44336")
        cards_layout.addWidget(self.gider_card, 0, 1)
        
        self.net_card = StatCard("NET BAKIYE", "0.00 ₺", "#64B5F6")
        cards_layout.addWidget(self.net_card, 0, 2)
        
        self.kasa_card = StatCard("KASA BAKIYE", "0.00 ₺", "#FF9800")
        cards_layout.addWidget(self.kasa_card, 0, 3)
        
        layout.addLayout(cards_layout)
        
        # Kasa Özeti Grubu
        kasa_group = QGroupBox("KASA ÖZETİ")
        kasa_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                color: #444050;
                padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        
        kasa_layout = QVBoxLayout()
        kasa_layout.setContentsMargins(20, 30, 20, 20)
        
        self.kasa_list_layout = QVBoxLayout()
        self.kasa_list_layout.setSpacing(10)
        kasa_layout.addLayout(self.kasa_list_layout)
        
        kasa_group.setLayout(kasa_layout)
        layout.addWidget(kasa_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_dashboard(self):
        """Dashboard verilerini yükle"""
        yil = datetime.now().year
        baslangic = f"{yil}-01-01"
        bitis = f"{yil}-12-31"
        
        # Toplam gelir
        gelirler = self.gelir_yoneticisi.gelir_listesi(baslangic_tarih=baslangic, bitis_tarih=bitis)
        toplam_gelir = sum(g['tutar'] for g in gelirler)
        self.gelir_card.set_value(f"{toplam_gelir:,.2f} ₺")
        
        # Toplam gider
        giderler = self.gider_yoneticisi.gider_listesi(baslangic_tarih=baslangic, bitis_tarih=bitis)
        toplam_gider = sum(g['tutar'] for g in giderler)
        self.gider_card.set_value(f"{toplam_gider:,.2f} ₺")
        
        # Net bakiye
        net = toplam_gelir - toplam_gider
        self.net_card.set_value(f"{net:,.2f} ₺")
        
        # Kasa bakiye
        kasalar = self.kasa_yoneticisi.tum_kasalar_ozet()
        toplam_kasa = sum(k['net_bakiye'] for k in kasalar)
        self.kasa_card.set_value(f"{toplam_kasa:,.2f} ₺")
        
        # Kasa listesi temizle
        while self.kasa_list_layout.count():
            item = self.kasa_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Kasa listesi doldur
        for kasa in kasalar:
            row = QHBoxLayout()
            
            name = QLabel(f"💰 {kasa['kasa_adi']}")
            name.setStyleSheet("color: #444050; font-size: 14px; font-weight: 500;")
            row.addWidget(name)
            
            row.addStretch()
            
            balance = QLabel(f"{kasa['net_bakiye']:,.2f} {kasa['para_birimi']}")
            if kasa['net_bakiye'] >= 0:
                balance.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: 600;")
            else:
                balance.setStyleSheet("color: #f44336; font-size: 14px; font-weight: 600;")
            row.addWidget(balance)
            
            row_widget = QWidget()
            row_widget.setLayout(row)
            self.kasa_list_layout.addWidget(row_widget)
        
        if not kasalar:
            no_data = QLabel("Henüz kasa tanımlanmamış.")
            no_data.setStyleSheet("color: #97959e; font-size: 13px;")
            self.kasa_list_layout.addWidget(no_data)


