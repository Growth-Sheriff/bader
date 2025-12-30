"""
BADER Derneği - Raporlar Modülü
Borçlu üye listesi, mali raporlar, aidat tahsilat oranları
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QFrame, QLabel,
                             QGroupBox, QGridLayout, QDateEdit,
                             QHeaderView, QTabWidget, QFileDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from qfluentwidgets import (MessageBox, PushButton, ComboBox, TitleLabel, 
                            SubtitleLabel, BodyLabel, CardWidget, SpinBox)
from database import Database
from models import UyeYoneticisi, AidatYoneticisi, RaporYoneticisi, KasaYoneticisi
from ui_helpers import export_table_to_excel
from datetime import datetime


class StatCard(CardWidget):
    """İstatistik kartı - FluentWidgets"""
    
    def __init__(self, title: str, value: str, color: str = "#64B5F6"):
        super().__init__()
        self.color = color
        self.setStyleSheet(f"""
            CardWidget {{
                background-color: white;
                border: 1px solid #E3E3E3;
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
        """)
        self.setMinimumHeight(100)
        self.setMinimumWidth(200)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(6)
        
        self.title_label = BodyLabel(title.upper())
        self.title_label.setStyleSheet("""
            color: #616161;
            font-size: 11px;
            font-weight: 650;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(self.title_label)
        
        self.value_label = TitleLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {color};
            font-size: 24px;
            font-weight: 700;
        """)
        layout.addWidget(self.value_label)
        
        self.setLayout(layout)
    
    def set_value(self, value: str):
        self.value_label.setText(value)


class BorcluUyelerWidget(QWidget):
    """Borçlu üyeler listesi"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.aidat_yoneticisi = AidatYoneticisi(db)
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık ve filtreler
        header_layout = QHBoxLayout()
        
        title = TitleLabel("BORÇLU ÜYE LİSTESİ")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Yıl filtresi
        header_layout.addWidget(BodyLabel("Yıl:"))
        self.yil_combo = ComboBox()
        current_year = datetime.now().year
        for y in range(current_year + 1, 2019, -1):
            self.yil_combo.addItem(str(y), y)
        self.yil_combo.currentIndexChanged.connect(self.load_data)
        header_layout.addWidget(self.yil_combo)
        
        # Minimum borç filtresi
        header_layout.addWidget(BodyLabel("Min Borç:"))
        self.min_borc_combo = ComboBox()
        self.min_borc_combo.addItems(["Tümü", "100 ₺+", "500 ₺+", "1000 ₺+"])
        self.min_borc_combo.currentIndexChanged.connect(self.load_data)
        header_layout.addWidget(self.min_borc_combo)
        
        # Excel export
        self.export_btn = PushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "borclu_uyeler", self))
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.toplam_card = StatCard("Toplam Borçlu", "0", "#f44336")
        stats_layout.addWidget(self.toplam_card)
        
        self.borc_card = StatCard("Toplam Borç", "0.00 ₺", "#FF9800")
        stats_layout.addWidget(self.borc_card)
        
        self.tahsilat_card = StatCard("Tahsilat Oranı", "%0", "#4CAF50")
        stats_layout.addWidget(self.tahsilat_card)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Üye No", "Ad Soyad", "Telefon", "Yıl", "Aidat Tutarı", "Ödenen", "Borç"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def load_data(self):
        """Borçlu üyeleri yükle"""
        yil = self.yil_combo.currentData()
        min_borc_text = self.min_borc_combo.currentText()
        
        # Min borç hesapla
        min_borc = 0
        if "100" in min_borc_text:
            min_borc = 100
        elif "500" in min_borc_text:
            min_borc = 500
        elif "1000" in min_borc_text:
            min_borc = 1000
        
        # Aidat listesi al
        aidatlar = self.aidat_yoneticisi.aidat_listesi(yil=yil)
        
        # Borçlu olanları filtrele
        borclu_liste = []
        toplam_borc = 0
        toplam_aidat = 0
        toplam_odenen = 0
        
        for aidat in aidatlar:
            kalan = aidat['odenecek_tutar']
            toplam_aidat += aidat['yillik_aidat_tutari']
            toplam_odenen += aidat.get('toplam_odenen', 0) or 0
            
            if kalan > min_borc:
                borclu_liste.append(aidat)
                toplam_borc += kalan
        
        # Tabloyu doldur
        self.table.setRowCount(len(borclu_liste))
        
        for row, item in enumerate(borclu_liste):
            # Üye bilgilerini al
            uye = self.uye_yoneticisi.uye_getir(item['uye_id'])
            uye_no = uye.get('uye_no', '-') if uye else '-'
            
            self.table.setItem(row, 0, QTableWidgetItem(uye_no or str(item['uye_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(item['ad_soyad']))
            self.table.setItem(row, 2, QTableWidgetItem(uye.get('telefon', '-') if uye else '-'))
            self.table.setItem(row, 3, QTableWidgetItem(str(item['yil'])))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['yillik_aidat_tutari']:,.2f} ₺"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{item.get('toplam_odenen', 0) or 0:,.2f} ₺"))
            
            borc_item = QTableWidgetItem(f"{item['odenecek_tutar']:,.2f} ₺")
            borc_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 6, borc_item)
        
        # İstatistikleri güncelle
        self.toplam_card.set_value(str(len(borclu_liste)))
        self.borc_card.set_value(f"{toplam_borc:,.2f} ₺")
        
        # Tahsilat oranı
        if toplam_aidat > 0:
            oran = (toplam_odenen / toplam_aidat) * 100
            self.tahsilat_card.set_value(f"%{oran:.1f}")
        else:
            self.tahsilat_card.set_value("%0")


class MaliRaporWidget(QWidget):
    """Mali durum raporu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.rapor_yoneticisi = RaporYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık ve filtreler
        header_layout = QHBoxLayout()
        
        title = TitleLabel("MALİ DURUM RAPORU")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Tarih aralığı
        header_layout.addWidget(BodyLabel("Başlangıç:"))
        self.baslangic_date = QDateEdit()
        self.baslangic_date.setCalendarPopup(True)
        self.baslangic_date.setDate(QDate(datetime.now().year, 1, 1))
        self.baslangic_date.dateChanged.connect(self.load_data)
        header_layout.addWidget(self.baslangic_date)
        
        header_layout.addWidget(BodyLabel("Bitiş:"))
        self.bitis_date = QDateEdit()
        self.bitis_date.setCalendarPopup(True)
        self.bitis_date.setDate(QDate.currentDate())
        self.bitis_date.dateChanged.connect(self.load_data)
        header_layout.addWidget(self.bitis_date)
        
        layout.addLayout(header_layout)
        
        # Özet kartları
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)
        
        self.gelir_card = StatCard("Toplam Gelir", "0.00 ₺", "#4CAF50")
        cards_layout.addWidget(self.gelir_card, 0, 0)
        
        self.gider_card = StatCard("Toplam Gider", "0.00 ₺", "#f44336")
        cards_layout.addWidget(self.gider_card, 0, 1)
        
        self.net_card = StatCard("Net Sonuç", "0.00 ₺", "#64B5F6")
        cards_layout.addWidget(self.net_card, 0, 2)
        
        self.kasa_card = StatCard("Kasa Bakiye", "0.00 ₺", "#FF9800")
        cards_layout.addWidget(self.kasa_card, 0, 3)
        
        layout.addLayout(cards_layout)
        
        # Alt bölümler
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Gelir dağılımı
        gelir_group = QGroupBox("GELİR DAĞILIMI")
        gelir_layout = QVBoxLayout()
        self.gelir_table = QTableWidget()
        self.gelir_table.setColumnCount(3)
        self.gelir_table.setHorizontalHeaderLabels(["Gelir Türü", "Adet", "Toplam"])
        self.gelir_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gelir_table.setAlternatingRowColors(True)
        gelir_layout.addWidget(self.gelir_table)
        gelir_group.setLayout(gelir_layout)
        bottom_layout.addWidget(gelir_group)
        
        # Gider dağılımı
        gider_group = QGroupBox("GİDER DAĞILIMI")
        gider_layout = QVBoxLayout()
        self.gider_table = QTableWidget()
        self.gider_table.setColumnCount(3)
        self.gider_table.setHorizontalHeaderLabels(["Gider Türü", "Adet", "Toplam"])
        self.gider_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gider_table.setAlternatingRowColors(True)
        gider_layout.addWidget(self.gider_table)
        gider_group.setLayout(gider_layout)
        bottom_layout.addWidget(gider_group)
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
        
    def load_data(self):
        """Rapor verilerini yükle"""
        baslangic = self.baslangic_date.date().toString("yyyy-MM-dd")
        bitis = self.bitis_date.date().toString("yyyy-MM-dd")
        
        # Gelir dağılımı
        gelir_dagilimi = self.rapor_yoneticisi.gelir_turu_dagilimi(baslangic, bitis)
        toplam_gelir = sum(g['toplam'] for g in gelir_dagilimi)
        
        self.gelir_table.setRowCount(len(gelir_dagilimi))
        for row, g in enumerate(gelir_dagilimi):
            self.gelir_table.setItem(row, 0, QTableWidgetItem(g['gelir_turu']))
            self.gelir_table.setItem(row, 1, QTableWidgetItem(str(g['adet'])))
            self.gelir_table.setItem(row, 2, QTableWidgetItem(f"{g['toplam']:,.2f} ₺"))
        
        # Gider dağılımı
        gider_dagilimi = self.rapor_yoneticisi.gider_turu_dagilimi(baslangic, bitis)
        toplam_gider = sum(g['toplam'] for g in gider_dagilimi)
        
        self.gider_table.setRowCount(len(gider_dagilimi))
        for row, g in enumerate(gider_dagilimi):
            self.gider_table.setItem(row, 0, QTableWidgetItem(g['gider_turu']))
            self.gider_table.setItem(row, 1, QTableWidgetItem(str(g['adet'])))
            self.gider_table.setItem(row, 2, QTableWidgetItem(f"{g['toplam']:,.2f} ₺"))
        
        # Kartları güncelle
        self.gelir_card.set_value(f"{toplam_gelir:,.2f} ₺")
        self.gider_card.set_value(f"{toplam_gider:,.2f} ₺")
        
        net = toplam_gelir - toplam_gider
        self.net_card.set_value(f"{net:,.2f} ₺")
        
        # Kasa bakiyesi
        kasa_ozet = self.kasa_yoneticisi.tum_kasalar_ozet(baslangic, bitis)
        toplam_kasa = sum(k['net_bakiye'] for k in kasa_ozet)
        self.kasa_card.set_value(f"{toplam_kasa:,.2f} ₺")


class AidatTahsilatRaporuWidget(QWidget):
    """Aidat tahsilat oranları raporu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.aidat_yoneticisi = AidatYoneticisi(db)
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        header_layout = QHBoxLayout()
        
        title = TitleLabel("AİDAT TAHSİLAT ORANLARI")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.export_btn = PushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "aidat_tahsilat", self))
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Yıl", "Toplam Üye", "Tahsilat Tamamlanan", "Kısmi Ödeme", "Ödeme Yok", "Tahsilat Oranı"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def load_data(self):
        """Tahsilat oranlarını yükle"""
        current_year = datetime.now().year
        
        rows = []
        for yil in range(current_year, 2019, -1):
            aidatlar = self.aidat_yoneticisi.aidat_listesi(yil=yil)
            
            toplam = len(aidatlar)
            tamamlanan = len([a for a in aidatlar if a['durum'] == 'Tamamlandı'])
            kismi = len([a for a in aidatlar if a['durum'] == 'Kısmi'])
            eksik = len([a for a in aidatlar if a['durum'] == 'Eksik'])
            
            oran = (tamamlanan / toplam * 100) if toplam > 0 else 0
            
            rows.append({
                'yil': yil,
                'toplam': toplam,
                'tamamlanan': tamamlanan,
                'kismi': kismi,
                'eksik': eksik,
                'oran': oran
            })
        
        self.table.setRowCount(len(rows))
        
        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['yil'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['toplam'])))
            
            tamamlanan_item = QTableWidgetItem(str(row['tamamlanan']))
            tamamlanan_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row_idx, 2, tamamlanan_item)
            
            kismi_item = QTableWidgetItem(str(row['kismi']))
            kismi_item.setForeground(QColor("#FF9800"))
            self.table.setItem(row_idx, 3, kismi_item)
            
            eksik_item = QTableWidgetItem(str(row['eksik']))
            eksik_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row_idx, 4, eksik_item)
            
            oran_item = QTableWidgetItem(f"%{row['oran']:.1f}")
            if row['oran'] >= 80:
                oran_item.setForeground(Qt.GlobalColor.darkGreen)
            elif row['oran'] >= 50:
                oran_item.setForeground(QColor("#FF9800"))
            else:
                oran_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row_idx, 5, oran_item)


class RaporlarWidget(QWidget):
    """Raporlar ana sayfası - Tab sistemi"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #f8f7fa;
            }
            QTabBar::tab {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #64B5F6;
                color: white;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
        """)
        
        # Borçlu üyeler
        self.borclu_widget = BorcluUyelerWidget(self.db)
        self.tabs.addTab(self.borclu_widget, "📋 Borçlu Üyeler")
        
        # Mali rapor
        self.mali_widget = MaliRaporWidget(self.db)
        self.tabs.addTab(self.mali_widget, "💰 Mali Durum")
        
        # Aidat tahsilat
        self.tahsilat_widget = AidatTahsilatRaporuWidget(self.db)
        self.tabs.addTab(self.tahsilat_widget, "📊 Tahsilat Oranları")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def refresh_all(self):
        """Tüm raporları yenile"""
        self.borclu_widget.load_data()
        self.mali_widget.load_data()
        self.tahsilat_widget.load_data()


