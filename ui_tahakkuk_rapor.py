"""
BADER Derneği - Tahakkuk Raporları UI
Yıl Bazlı Muhasebe - Tahakkuk Takip ve Raporlama
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from qfluentwidgets import (PushButton, TitleLabel, SubtitleLabel, BodyLabel,
                            CardWidget, ComboBox, SpinBox, MessageBox)
from database import Database
from models import TahakkukYoneticisi, KasaYoneticisi, GelirYoneticisi
from datetime import datetime
from ui_drawer import DrawerPanel
from ui_helpers import export_table_to_excel


class TahakkukStatCard(CardWidget):
    """Tahakkuk istatistik kartı"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", 
                 color: str = "#64B5F6", icon: str = "📊"):
        super().__init__()
        self.setMinimumHeight(110)
        self.setMinimumWidth(200)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(6)
        
        # İkon ve başlık
        header_layout = QHBoxLayout()
        icon_label = BodyLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        title_label = BodyLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px; font-weight: 600;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Değer
        self.value_label = TitleLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 700;")
        layout.addWidget(self.value_label)
        
        # Alt başlık
        if subtitle:
            self.subtitle_label = BodyLabel(subtitle)
            self.subtitle_label.setStyleSheet("color: #999; font-size: 11px;")
            layout.addWidget(self.subtitle_label)
        else:
            self.subtitle_label = None
        
        self.setLayout(layout)
    
    def set_value(self, value: str, subtitle: str = None):
        self.value_label.setText(value)
        if subtitle and self.subtitle_label:
            self.subtitle_label.setText(subtitle)


class TahakkukRaporWidget(QWidget):
    """Tahakkuk raporları ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.tahakkuk_yoneticisi = TahakkukYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.gelir_yoneticisi = GelirYoneticisi(db)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(15)
        
        # Başlık
        title_label = TitleLabel("📊 TAHAKKUK RAPORLARI")
        layout.addWidget(title_label)
        
        subtitle = BodyLabel("Yıl bazlı gelir tahakkuklarının takibi ve analizi")
        subtitle.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(subtitle)
        
        # Filtre bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)
        
        filter_layout.addWidget(BodyLabel("Yıl:"))
        self.yil_spin = SpinBox()
        self.yil_spin.setRange(2020, 2050)
        self.yil_spin.setValue(datetime.now().year)
        self.yil_spin.setFixedWidth(100)
        self.yil_spin.valueChanged.connect(self.load_data)
        filter_layout.addWidget(self.yil_spin)
        
        filter_layout.addWidget(BodyLabel("Kasa:"))
        self.kasa_combo = ComboBox()
        self.kasa_combo.setFixedWidth(200)
        self.kasa_combo.addItem("Tümü", None)
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            self.kasa_combo.addItem(kasa['kasa_adi'], kasa['kasa_id'])
        self.kasa_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.kasa_combo)
        
        filter_layout.addStretch()
        
        self.yenile_btn = PushButton("🔄 Yenile")
        self.yenile_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(self.yenile_btn)
        
        self.export_btn = PushButton("📄 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.detay_table, "tahakkuk_raporu", self))
        filter_layout.addWidget(self.export_btn)
        
        layout.addLayout(filter_layout)
        
        # İstatistik kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.fiziksel_card = TahakkukStatCard(
            "FİZİKSEL BAKİYE", "0 ₺", "Kasadaki toplam para", "#4CAF50", "💰"
        )
        cards_layout.addWidget(self.fiziksel_card)
        
        self.tahakkuk_card = TahakkukStatCard(
            "GELİR TAHAKKUKU", "0 ₺", "Gelecek yıllara ait", "#FF9800", "📅"
        )
        cards_layout.addWidget(self.tahakkuk_card)
        
        self.serbest_card = TahakkukStatCard(
            "SERBEST BAKİYE", "0 ₺", "Kullanılabilir para", "#2196F3", "✅"
        )
        cards_layout.addWidget(self.serbest_card)
        
        self.uyari_card = TahakkukStatCard(
            "DURUM", "Normal", "", "#4CAF50", "🔔"
        )
        cards_layout.addWidget(self.uyari_card)
        
        cards_layout.addStretch()
        layout.addLayout(cards_layout)
        
        # Yıl bazında özet
        ozet_label = SubtitleLabel("📅 YIL BAZINDA TAHAKKUK ÖZETİ")
        ozet_label.setStyleSheet("margin-top: 10px;")
        layout.addWidget(ozet_label)
        
        self.ozet_table = QTableWidget()
        self.ozet_table.setColumnCount(5)
        self.ozet_table.setHorizontalHeaderLabels([
            "Yıl", "İşlem Sayısı", "Toplam Tutar", "Durum", "Açıklama"
        ])
        self.ozet_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.ozet_table.setAlternatingRowColors(True)
        self.ozet_table.setMaximumHeight(200)
        self.ozet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.ozet_table)
        
        # Detay listesi
        detay_label = SubtitleLabel("📝 TAHAKKUK DETAY LİSTESİ")
        layout.addWidget(detay_label)
        
        self.detay_table = QTableWidget()
        self.detay_table.setColumnCount(8)
        self.detay_table.setHorizontalHeaderLabels([
            "ID", "Tahsil Tarihi", "Ait Olduğu Yıl", "Üye", 
            "Açıklama", "Tutar", "Kasa", "Durum"
        ])
        self.detay_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.detay_table.setAlternatingRowColors(True)
        self.detay_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.detay_table)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Verileri yükle"""
        yil = self.yil_spin.value()
        kasa_id = self.kasa_combo.currentData()
        
        # Toplam bakiye hesapla
        try:
            if kasa_id:
                # kasa_tahakkuk_detay dict döndürür
                bakiye_bilgi = self.kasa_yoneticisi.kasa_tahakkuk_detay(kasa_id)
                fiziksel = bakiye_bilgi.get('fiziksel_bakiye', 0)
                tahakkuk = bakiye_bilgi.get('tahakkuk_toplami', 0)
                serbest = bakiye_bilgi.get('serbest_bakiye', 0)
            else:
                # Tüm kasalar için toplam
                fiziksel = 0
                tahakkuk = 0
                serbest = 0
                kasalar = self.kasa_yoneticisi.kasa_listesi()
                for kasa in kasalar:
                    bakiye = self.kasa_yoneticisi.kasa_tahakkuk_detay(kasa['kasa_id'])
                    fiziksel += bakiye.get('fiziksel_bakiye', 0)
                    tahakkuk += bakiye.get('tahakkuk_toplami', 0)
                    serbest += bakiye.get('serbest_bakiye', 0)
            
            # Kartları güncelle
            self.fiziksel_card.set_value(f"{fiziksel:,.0f} ₺")
            self.tahakkuk_card.set_value(f"{tahakkuk:,.0f} ₺")
            self.serbest_card.set_value(f"{serbest:,.0f} ₺")
            
            # Durum kartı
            if serbest < 0:
                self.uyari_card.set_value("⚠️ CARİ AÇIK")
                self.uyari_card.value_label.setStyleSheet("color: #F44336; font-size: 20px; font-weight: 700;")
            elif tahakkuk > fiziksel * 0.8 and fiziksel > 0:
                self.uyari_card.set_value("⚠️ YÜKSEK")
                self.uyari_card.value_label.setStyleSheet("color: #FF9800; font-size: 20px; font-weight: 700;")
            else:
                self.uyari_card.set_value("✅ Normal")
                self.uyari_card.value_label.setStyleSheet("color: #4CAF50; font-size: 20px; font-weight: 700;")
        except Exception as e:
            print(f"Bakiye hesaplama hatası: {e}")
        
        # Yıl bazında özet
        self.load_yil_ozet()
        
        # Detay listesi
        self.load_detay(yil, kasa_id)
    
    def load_yil_ozet(self):
        """Yıl bazında tahakkuk özeti yükle"""
        self.ozet_table.setRowCount(0)
        
        try:
            # Yıl bazında özet al (parametre almayan versiyon)
            ozet_list = self.tahakkuk_yoneticisi.tahakkuk_ozet()
            
            # Özet boşsa veya liste değilse çık
            if not ozet_list or not isinstance(ozet_list, list):
                return
            
            # Yıllara göre grupla
            yil_gruplari = {}
            for item in ozet_list:
                yil = item.get('yil')
                if yil:
                    if yil not in yil_gruplari:
                        yil_gruplari[yil] = {'adet': 0, 'tutar': 0}
                    yil_gruplari[yil]['adet'] += item.get('adet', 0)
                    yil_gruplari[yil]['tutar'] += item.get('tutar', 0)
            
            bugun_yil = datetime.now().year
            
            for yil in sorted(yil_gruplari.keys()):
                data = yil_gruplari[yil]
                toplam_tutar = data['tutar']
                islem_sayisi = data['adet']
                
                if toplam_tutar == 0:
                    continue
                
                row = self.ozet_table.rowCount()
                self.ozet_table.insertRow(row)
                
                # Yıl
                yil_item = QTableWidgetItem(str(yil))
                yil_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if yil == bugun_yil:
                    yil_item.setBackground(QColor("#E8F5E9"))
                elif yil > bugun_yil:
                    yil_item.setBackground(QColor("#E3F2FD"))
                self.ozet_table.setItem(row, 0, yil_item)
                
                # İşlem sayısı
                self.ozet_table.setItem(row, 1, QTableWidgetItem(str(islem_sayisi)))
                
                # Tutar
                tutar_item = QTableWidgetItem(f"{toplam_tutar:,.2f} ₺")
                tutar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.ozet_table.setItem(row, 2, tutar_item)
                
                # Durum
                if yil == bugun_yil:
                    durum = "Cari Yıl"
                    durum_color = QColor("#4CAF50")
                elif yil < bugun_yil:
                    durum = "Geçmiş"
                    durum_color = QColor("#9E9E9E")
                else:
                    durum = "Gelecek (Tahakkuk)"
                    durum_color = QColor("#2196F3")
                
                durum_item = QTableWidgetItem(durum)
                durum_item.setForeground(durum_color)
                self.ozet_table.setItem(row, 3, durum_item)
                
                # Açıklama
                aciklama = f"{yil} yılına ait peşin tahsil edilen gelirler"
                self.ozet_table.setItem(row, 4, QTableWidgetItem(aciklama))
                
        except Exception as e:
            print(f"Yıl özeti yükleme hatası: {e}")
    
    def load_detay(self, yil: int, kasa_id: int = None):
        """Tahakkuk detay listesini yükle"""
        self.detay_table.setRowCount(0)
        
        try:
            # Seçilen yıl ve sonrası için tahakkukları getir
            tahakkuklar = self.tahakkuk_yoneticisi.tahakkuk_listesi(yil)
            
            for tahakkuk in tahakkuklar:
                # Kasa filtresi
                if kasa_id and tahakkuk.get('kasa_id') != kasa_id:
                    continue
                
                row = self.detay_table.rowCount()
                self.detay_table.insertRow(row)
                
                # ID
                self.detay_table.setItem(row, 0, QTableWidgetItem(str(tahakkuk.get('id', '-'))))
                
                # Tahsil tarihi
                tahsil_tarihi = tahakkuk.get('tahsil_tarihi', '-')
                self.detay_table.setItem(row, 1, QTableWidgetItem(str(tahsil_tarihi)))
                
                # Ait olduğu yıl
                ait_yil = tahakkuk.get('ait_oldugu_yil', yil)
                yil_item = QTableWidgetItem(str(ait_yil))
                if ait_yil > datetime.now().year:
                    yil_item.setBackground(QColor("#E3F2FD"))
                self.detay_table.setItem(row, 2, yil_item)
                
                # Üye
                uye_adi = tahakkuk.get('uye_adi', '-')
                self.detay_table.setItem(row, 3, QTableWidgetItem(str(uye_adi)))
                
                # Açıklama
                aciklama = tahakkuk.get('aciklama', '-')
                self.detay_table.setItem(row, 4, QTableWidgetItem(str(aciklama)))
                
                # Tutar
                tutar = tahakkuk.get('tutar', 0)
                tutar_item = QTableWidgetItem(f"{tutar:,.2f} ₺")
                tutar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.detay_table.setItem(row, 5, tutar_item)
                
                # Kasa
                kasa_adi = tahakkuk.get('kasa_adi', '-')
                self.detay_table.setItem(row, 6, QTableWidgetItem(str(kasa_adi)))
                
                # Durum
                durum = tahakkuk.get('durum', 'Bekliyor')
                durum_item = QTableWidgetItem(durum)
                if durum == 'Aktif':
                    durum_item.setForeground(QColor("#4CAF50"))
                elif durum == 'İptal':
                    durum_item.setForeground(QColor("#9E9E9E"))
                else:
                    durum_item.setForeground(QColor("#2196F3"))
                self.detay_table.setItem(row, 7, durum_item)
                
        except Exception as e:
            print(f"Detay yükleme hatası: {e}")
