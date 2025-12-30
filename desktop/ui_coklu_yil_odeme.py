"""
Çok Yıllık Ödeme - Yıl Bazlı Muhasebe Sistemi
Üyelerin birden fazla yıl için aidat ödemesi yapabilmesi
Modern Drawer Panel UI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QFrame, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
from qfluentwidgets import (PushButton, ComboBox, SpinBox, TableWidget, CardWidget,
                           MessageBox, InfoBar, InfoBarPosition, BodyLabel, SubtitleLabel)
from datetime import datetime
from typing import Optional
from ui_drawer import DrawerPanel


class CokluYilOdemeFormWidget(QWidget):
    """Çok yıllık ödeme formu - Drawer içinde"""
    
    def __init__(self, db=None, uye_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.uye_id = uye_id
        self.uye_adi = ""
        self.yillik_aidat = 100.0
        
        self.init_ui()
        self.load_uye_bilgi()
        
    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Üye bilgisi kartı
        uye_card = CardWidget()
        uye_layout = QVBoxLayout()
        uye_layout.setContentsMargins(15, 12, 15, 12)
        
        self.uye_label = BodyLabel("Üye: Seçilmedi")
        self.uye_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #333;")
        uye_layout.addWidget(self.uye_label)
        
        uye_card.setLayout(uye_layout)
        layout.addWidget(uye_card)
        
        # Yıl seçimi
        yil_frame = QFrame()
        yil_layout = QHBoxLayout(yil_frame)
        
        yil_layout.addWidget(QLabel("Başlangıç Yılı:"))
        self.baslangic_spin = SpinBox()
        self.baslangic_spin.setRange(2020, 2050)
        self.baslangic_spin.setValue(datetime.now().year)
        self.baslangic_spin.setMinimumWidth(100)
        self.baslangic_spin.valueChanged.connect(self.hesapla_ozet)
        yil_layout.addWidget(self.baslangic_spin)
        
        yil_layout.addWidget(QLabel("Bitiş Yılı:"))
        self.bitis_spin = SpinBox()
        self.bitis_spin.setRange(2020, 2050)
        self.bitis_spin.setValue(datetime.now().year)
        self.bitis_spin.setMinimumWidth(100)
        self.bitis_spin.valueChanged.connect(self.hesapla_ozet)
        yil_layout.addWidget(self.bitis_spin)
        
        yil_layout.addStretch()
        layout.addWidget(yil_frame)
        
        # Kasa seçimi
        kasa_frame = QFrame()
        kasa_layout = QHBoxLayout(kasa_frame)
        kasa_layout.addWidget(QLabel("Kasa:"))
        self.kasa_combo = ComboBox()
        self.kasa_combo.setMinimumWidth(200)
        self.load_kasalar()
        kasa_layout.addWidget(self.kasa_combo)
        kasa_layout.addStretch()
        layout.addWidget(kasa_frame)
        
        # Tarih seçimi
        tarih_frame = QFrame()
        tarih_layout = QHBoxLayout(tarih_frame)
        tarih_layout.addWidget(QLabel("Tahsil Tarihi:"))
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        self.tarih_edit.setDisplayFormat("dd.MM.yyyy")
        tarih_layout.addWidget(self.tarih_edit)
        tarih_layout.addStretch()
        layout.addWidget(tarih_frame)
        
        # Özet bölgesi
        ozet_label = QLabel("📊 Ödeme Özeti")
        ozet_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(ozet_label)
        
        # Özet tablo
        self.ozet_table = TableWidget()
        self.ozet_table.setColumnCount(3)
        self.ozet_table.setHorizontalHeaderLabels(["Yıl", "Tutar", "Durum"])
        self.ozet_table.setColumnWidth(0, 100)
        self.ozet_table.setColumnWidth(1, 150)
        self.ozet_table.setColumnWidth(2, 200)
        self.ozet_table.setMaximumHeight(200)
        layout.addWidget(self.ozet_table)
        
        # Toplam tutar
        self.toplam_label = QLabel("Toplam: 0 TL")
        self.toplam_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.toplam_label.setStyleSheet("color: #1976D2; padding: 10px;")
        layout.addWidget(self.toplam_label)
        
        # Uyarı mesajı
        uyari_card = CardWidget()
        uyari_card.setStyleSheet("""
            CardWidget {
                background-color: #FFF3E0;
                border: 2px solid #FF9800;
            }
        """)
        uyari_layout = QVBoxLayout()
        uyari_layout.setContentsMargins(15, 12, 15, 12)
        
        uyari_label = BodyLabel("⚠️  UYARI")
        uyari_label.setStyleSheet("font-weight: 700; color: #FF9800;")
        uyari_layout.addWidget(uyari_label)
        
        self.uyari_text = BodyLabel(
            "Bu ödeme kasaya girecektir ama seçilen yıllara ait "
            "aidat ödenmiş sayılacaktır. Gelecek yılların parasını "
            "şimdiden tahsil ediyorsunuz."
        )
        self.uyari_text.setWordWrap(True)
        uyari_layout.addWidget(self.uyari_text)
        
        uyari_card.setLayout(uyari_layout)
        layout.addWidget(uyari_card)
        
        layout.addStretch()
        
    def load_kasalar(self):
        """Kasaları yükle"""
        if not self.db:
            return
        
        from models import KasaYoneticisi
        kasa_yoneticisi = KasaYoneticisi(self.db)
        kasalar = kasa_yoneticisi.kasa_listesi()
        
        for kasa in kasalar:
            self.kasa_combo.addItem(
                f"{kasa['kasa_adi']} ({kasa['para_birimi']})",
                kasa['kasa_id']
            )
        
        # Varsayılan kasa seç
        for i in range(self.kasa_combo.count()):
            if "DERNEK KASA TL" in self.kasa_combo.itemText(i):
                self.kasa_combo.setCurrentIndex(i)
                break
    
    def load_uye_bilgi(self):
        """Üye bilgilerini yükle"""
        if not self.db or not self.uye_id:
            return
        
        from models import UyeYoneticisi
        uye_yoneticisi = UyeYoneticisi(self.db)
        uye = uye_yoneticisi.uye_getir(self.uye_id)
        
        if uye:
            self.uye_adi = uye['ad_soyad']
            self.yillik_aidat = uye['ozel_aidat_tutari'] if uye['ozel_aidat_tutari'] else 100.0
            
            self.uye_label.setText(f"Üye: {self.uye_adi} (Yıllık Aidat: {self.yillik_aidat:,.2f} ₺)")
            
            self.hesapla_ozet()
    
    def hesapla_ozet(self):
        """Ödeme özetini hesapla"""
        baslangic = self.baslangic_spin.value()
        bitis = self.bitis_spin.value()
        
        if bitis < baslangic:
            bitis = baslangic
            self.bitis_spin.setValue(bitis)
        
        # Tabloyu temizle
        self.ozet_table.setRowCount(0)
        
        toplam = 0
        tahsil_yili = datetime.now().year
        
        for yil in range(baslangic, bitis + 1):
            row = self.ozet_table.rowCount()
            self.ozet_table.insertRow(row)
            
            # Yıl
            yil_item = QTableWidgetItem(str(yil))
            yil_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ozet_table.setItem(row, 0, yil_item)
            
            # Tutar
            tutar_item = QTableWidgetItem(f"{self.yillik_aidat:,.2f} ₺")
            tutar_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ozet_table.setItem(row, 1, tutar_item)
            
            # Durum
            if yil == tahsil_yili:
                durum = "Normal"
                durum_color = QColor("#4CAF50")
            elif yil < tahsil_yili:
                durum = "Geriye Dönük"
                durum_color = QColor("#FF9800")
            else:
                durum = "Peşin"
                durum_color = QColor("#2196F3")
            
            durum_item = QTableWidgetItem(f"✓ {durum}")
            durum_item.setForeground(durum_color)
            durum_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ozet_table.setItem(row, 2, durum_item)
            
            toplam += self.yillik_aidat
        
        self.toplam_label.setText(f"Toplam: {toplam:,.2f} ₺")
        
        # Yıl sayısını güncelle
        yil_sayisi = bitis - baslangic + 1
        self.uyari_text.setText(
            f"Bu ödeme {datetime.now().year} yılı kasasına girecektir ama "
            f"{baslangic}-{bitis} yılları ({yil_sayisi} yıl) için aidat "
            f"ödenmiş sayılacaktır."
        )
    
    def get_data(self):
        """Form verilerini al"""
        return {
            'baslangic': self.baslangic_spin.value(),
            'bitis': self.bitis_spin.value(),
            'kasa_id': self.kasa_combo.currentData(),
            'tarih': self.tarih_edit.date().toString("yyyy-MM-dd"),
            'yillik_aidat': self.yillik_aidat,
            'uye_id': self.uye_id,
            'uye_adi': self.uye_adi
        }
    
    def validate(self):
        """Form validasyonu"""
        if not self.db or not self.uye_id:
            MessageBox("Hata", "Üye bilgisi eksik!", self).exec()
            return False
        
        if self.kasa_combo.currentIndex() < 0:
            MessageBox("Hata", "Lütfen kasa seçiniz!", self).exec()
            return False
        
        return True


class KasaTahakkukFormWidget(QWidget):
    """Kasa tahakkuk detay formu - Drawer içinde"""
    
    def __init__(self, db=None, kasa_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.kasa_id = kasa_id
        
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Kasa adı
        self.baslik_label = SubtitleLabel("Kasa Tahakkuk Detayı")
        layout.addWidget(self.baslik_label)
        
        # Bakiye kartları
        card_layout = QHBoxLayout()
        card_layout.setSpacing(10)
        
        # Fiziksel bakiye
        self.fiziksel_card = self.create_compact_card("💰 Fiziksel", "0 ₺", "#4CAF50")
        card_layout.addWidget(self.fiziksel_card)
        
        # Tahakkuk
        self.tahakkuk_card = self.create_compact_card("📊 Tahakkuk", "0 ₺", "#FF9800")
        card_layout.addWidget(self.tahakkuk_card)
        
        # Serbest bakiye
        self.serbest_card = self.create_compact_card("✅ Serbest", "0 ₺", "#2196F3")
        card_layout.addWidget(self.serbest_card)
        
        layout.addLayout(card_layout)
        
        # Gelecek yıl tahakkukları
        detay_label = BodyLabel("📅 Gelecek Yıl Tahakkukları")
        detay_label.setStyleSheet("font-weight: 700; font-size: 12px; margin-top: 10px;")
        layout.addWidget(detay_label)
        
        self.tahakkuk_table = TableWidget()
        self.tahakkuk_table.setColumnCount(3)
        self.tahakkuk_table.setHorizontalHeaderLabels(["Yıl", "İşlem Sayısı", "Tutar"])
        self.tahakkuk_table.setColumnWidth(0, 100)
        self.tahakkuk_table.setColumnWidth(1, 100)
        self.tahakkuk_table.setColumnWidth(2, 150)
        self.tahakkuk_table.setMaximumHeight(200)
        layout.addWidget(self.tahakkuk_table)
        
        # Uyarı
        self.uyari_label = BodyLabel("")
        self.uyari_label.setWordWrap(True)
        layout.addWidget(self.uyari_label)
        
        layout.addStretch()
    
    def create_compact_card(self, baslik: str, deger: str, renk: str) -> CardWidget:
        """Kompakt kart widget oluştur"""
        card = CardWidget()
        card.setMinimumHeight(80)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(5)
        
        baslik_label = BodyLabel(baslik)
        baslik_label.setStyleSheet(f"color: {renk}; font-size: 11px; font-weight: 600;")
        card_layout.addWidget(baslik_label)
        
        deger_label = SubtitleLabel(deger)
        deger_label.setStyleSheet(f"color: {renk}; font-size: 16px; font-weight: 700;")
        deger_label.setObjectName("deger_label")
        card_layout.addWidget(deger_label)
        
        card.setLayout(card_layout)
        return card
    
    def load_data(self):
        """Verileri yükle"""
        if not self.db or not self.kasa_id:
            return
        
        from models import KasaYoneticisi
        kasa_yoneticisi = KasaYoneticisi(self.db)
        
        # Kasa adı
        kasalar = kasa_yoneticisi.kasa_listesi()
        kasa_adi = next((k['kasa_adi'] for k in kasalar if k['kasa_id'] == self.kasa_id), "Bilinmeyen")
        self.baslik_label.setText(f"📊 {kasa_adi}")
        
        # Tahakkuk detayı
        detay = kasa_yoneticisi.kasa_tahakkuk_detay(self.kasa_id)
        
        # Kartları güncelle
        fiziksel = detay.get('fiziksel_bakiye', 0)
        tahakkuk = detay.get('tahakkuk_toplami', 0)
        serbest = detay.get('serbest_bakiye', 0)
        
        self.fiziksel_card.findChild(SubtitleLabel, "deger_label").setText(f"{fiziksel:,.2f} ₺")
        self.tahakkuk_card.findChild(SubtitleLabel, "deger_label").setText(f"{tahakkuk:,.2f} ₺")
        self.serbest_card.findChild(SubtitleLabel, "deger_label").setText(f"{serbest:,.2f} ₺")
        
        # Tablo
        self.tahakkuk_table.setRowCount(0)
        gelecek_yil_detay = detay.get('gelecek_yil_detay', [])
        
        for tahakkuk_yil in gelecek_yil_detay:
            row = self.tahakkuk_table.rowCount()
            self.tahakkuk_table.insertRow(row)
            
            self.tahakkuk_table.setItem(row, 0, QTableWidgetItem(str(tahakkuk_yil['yil'])))
            self.tahakkuk_table.setItem(row, 1, QTableWidgetItem(str(tahakkuk_yil['adet'])))
            self.tahakkuk_table.setItem(row, 2, QTableWidgetItem(f"{tahakkuk_yil['tutar']:,.2f} ₺"))
        
        # Uyarı mesajı
        if serbest < 0:
            self.uyari_label.setText(
                f"⚠️  CARİ AÇIK: Serbest bakiye negatif ({serbest:,.2f} ₺). "
                f"Gelecek yılların parasını kullanmış durumdasınız!"
            )
            self.uyari_label.setStyleSheet(
                "background-color: #FFEBEE; color: #C62828; padding: 10px; "
                "border: 2px solid #EF5350; border-radius: 5px;"
            )
        elif tahakkuk > fiziksel * 0.8 and fiziksel > 0:
            oran = (tahakkuk / fiziksel * 100) if fiziksel > 0 else 0
            self.uyari_label.setText(
                f"⚠️  YÜKSEK TAHAKKUK: Tahakkuk oranı %{oran:.0f}. "
                f"Gelecek yıllara ait para kasanın büyük kısmını oluşturuyor!"
            )
            self.uyari_label.setStyleSheet(
                "background-color: #FFF3E0; color: #E65100; padding: 10px; "
                "border: 2px solid #FF9800; border-radius: 5px;"
            )
        else:
            self.uyari_label.setText(
                f"✅ Kasa durumu normal. Serbest bakiye yeterli."
            )
            self.uyari_label.setStyleSheet(
                "background-color: #E8F5E9; color: #2E7D32; padding: 10px; "
                "border: 2px solid #4CAF50; border-radius: 5px;"
            )
