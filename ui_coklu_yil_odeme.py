"""
Çok Yıllık Ödeme - Yıl Bazlı Muhasebe Sistemi
Üyelerin birden fazla yıl için aidat ödemesi yapabilmesi
Modern Drawer Panel UI - Geliştirilmiş Versiyon
Her yıl için ayrı dekont, banka bilgisi, tahsilat türü
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QFrame, QDateEdit,
                             QCheckBox, QLineEdit, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
from qfluentwidgets import (PushButton, ComboBox, SpinBox, TableWidget, CardWidget,
                           MessageBox, InfoBar, InfoBarPosition, BodyLabel, SubtitleLabel,
                           LineEdit)
from datetime import datetime
from typing import Optional, Dict, List
from ui_drawer import DrawerPanel


class YilOdemeWidget(QWidget):
    """Tek bir yıl için ödeme bilgisi widget'ı"""
    
    def __init__(self, yil: int, tutar: float, parent=None):
        super().__init__(parent)
        self.yil = yil
        self.tutar = tutar
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        
        # Üst satır - Yıl, Checkbox, Tutar
        top_layout = QHBoxLayout()
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.on_check_changed)
        top_layout.addWidget(self.checkbox)
        
        yil_label = QLabel(f"<b>{self.yil}</b>")
        yil_label.setMinimumWidth(60)
        top_layout.addWidget(yil_label)
        
        tutar_label = QLabel(f"{self.tutar:,.2f} ₺")
        tutar_label.setStyleSheet("color: #1976D2; font-weight: 600;")
        tutar_label.setMinimumWidth(100)
        top_layout.addWidget(tutar_label)
        
        # Durum
        tahsil_yili = datetime.now().year
        if self.yil == tahsil_yili:
            durum = "Normal"
            durum_color = "#4CAF50"
        elif self.yil < tahsil_yili:
            durum = "Geriye Dönük"
            durum_color = "#FF9800"
        else:
            durum = "Peşin"
            durum_color = "#2196F3"
        
        durum_label = QLabel(durum)
        durum_label.setStyleSheet(f"color: {durum_color}; font-weight: 500;")
        top_layout.addWidget(durum_label)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Alt satır - Dekont, Banka, Tahsilat Türü
        details_layout = QHBoxLayout()
        details_layout.setSpacing(8)
        
        self.dekont_edit = QLineEdit()
        self.dekont_edit.setPlaceholderText("Dekont No")
        self.dekont_edit.setMaximumWidth(120)
        details_layout.addWidget(self.dekont_edit)
        
        self.banka_edit = QLineEdit()
        self.banka_edit.setPlaceholderText("Banka / Şube")
        self.banka_edit.setMaximumWidth(150)
        details_layout.addWidget(self.banka_edit)
        
        self.tahsilat_combo = ComboBox()
        self.tahsilat_combo.addItems(["Nakit", "Havale/EFT", "Kredi Kartı", "Çek"])
        self.tahsilat_combo.setMaximumWidth(120)
        details_layout.addWidget(self.tahsilat_combo)
        
        details_layout.addStretch()
        layout.addLayout(details_layout)
        
        # Stil
        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
            }
        """)
        
    def on_check_changed(self, state):
        """Checkbox değiştiğinde opacity ayarla"""
        opacity = "1.0" if state else "0.5"
        enabled = state == Qt.CheckState.Checked.value
        self.dekont_edit.setEnabled(enabled)
        self.banka_edit.setEnabled(enabled)
        self.tahsilat_combo.setEnabled(enabled)
        
    def is_selected(self) -> bool:
        return self.checkbox.isChecked()
    
    def get_data(self) -> Dict:
        return {
            'yil': self.yil,
            'tutar': self.tutar,
            'dekont_no': self.dekont_edit.text().strip(),
            'banka': self.banka_edit.text().strip(),
            'tahsilat_turu': self.tahsilat_combo.currentText()
        }


class CokluYilOdemeFormWidget(QWidget):
    """Çok yıllık ödeme formu - Drawer içinde - Geliştirilmiş"""
    
    def __init__(self, db=None, uye_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.uye_id = uye_id
        self.uye_adi = ""
        self.yillik_aidat = 100.0
        self.yil_widgets: List[YilOdemeWidget] = []
        
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
        
        # Yıl seçimi aralığı
        yil_frame = QFrame()
        yil_layout = QHBoxLayout(yil_frame)
        
        yil_layout.addWidget(QLabel("Başlangıç Yılı:"))
        self.baslangic_spin = SpinBox()
        self.baslangic_spin.setRange(2020, 2050)
        self.baslangic_spin.setValue(datetime.now().year)
        self.baslangic_spin.setMinimumWidth(100)
        self.baslangic_spin.valueChanged.connect(self.yillari_olustur)
        yil_layout.addWidget(self.baslangic_spin)
        
        yil_layout.addWidget(QLabel("Bitiş Yılı:"))
        self.bitis_spin = SpinBox()
        self.bitis_spin.setRange(2020, 2050)
        self.bitis_spin.setValue(datetime.now().year)
        self.bitis_spin.setMinimumWidth(100)
        self.bitis_spin.valueChanged.connect(self.yillari_olustur)
        yil_layout.addWidget(self.bitis_spin)
        
        yil_layout.addStretch()
        layout.addWidget(yil_frame)
        
        # Kasa ve Tarih yan yana
        ortak_frame = QFrame()
        ortak_layout = QHBoxLayout(ortak_frame)
        
        ortak_layout.addWidget(QLabel("Kasa:"))
        self.kasa_combo = ComboBox()
        self.kasa_combo.setMinimumWidth(180)
        self.load_kasalar()
        ortak_layout.addWidget(self.kasa_combo)
        
        ortak_layout.addWidget(QLabel("Tahsil Tarihi:"))
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        self.tarih_edit.setDisplayFormat("dd.MM.yyyy")
        ortak_layout.addWidget(self.tarih_edit)
        
        ortak_layout.addStretch()
        layout.addWidget(ortak_frame)
        
        # Yıl seçimi bölgesi
        yillar_label = QLabel("📅 Ödenecek Yıllar (işaretli olanlar ödenecek)")
        yillar_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(yillar_label)
        
        # Tümünü seç/kaldır
        secim_layout = QHBoxLayout()
        self.tumunu_sec_btn = PushButton("✓ Tümünü Seç")
        self.tumunu_sec_btn.clicked.connect(self.tumunu_sec)
        secim_layout.addWidget(self.tumunu_sec_btn)
        
        self.tumunu_kaldir_btn = PushButton("✗ Tümünü Kaldır")
        self.tumunu_kaldir_btn.clicked.connect(self.tumunu_kaldir)
        secim_layout.addWidget(self.tumunu_kaldir_btn)
        
        secim_layout.addStretch()
        layout.addLayout(secim_layout)
        
        # Scroll area for year widgets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(250)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.yillar_container = QWidget()
        self.yillar_layout = QVBoxLayout(self.yillar_container)
        self.yillar_layout.setSpacing(8)
        self.yillar_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.yillar_container)
        layout.addWidget(scroll)
        
        # Toplam tutar
        self.toplam_label = QLabel("Toplam: 0 ₺ (0 yıl seçili)")
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
            
            self.yillari_olustur()
    
    def yillari_olustur(self):
        """Yıl widget'larını oluştur"""
        baslangic = self.baslangic_spin.value()
        bitis = self.bitis_spin.value()
        
        if bitis < baslangic:
            bitis = baslangic
            self.bitis_spin.setValue(bitis)
        
        # Mevcut widget'ları temizle
        for widget in self.yil_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.yil_widgets.clear()
        
        # Yeni widget'ları oluştur
        for yil in range(baslangic, bitis + 1):
            widget = YilOdemeWidget(yil, self.yillik_aidat)
            widget.checkbox.stateChanged.connect(self.hesapla_toplam)
            self.yillar_layout.addWidget(widget)
            self.yil_widgets.append(widget)
        
        self.hesapla_toplam()
    
    def tumunu_sec(self):
        """Tüm yılları seç"""
        for widget in self.yil_widgets:
            widget.checkbox.setChecked(True)
    
    def tumunu_kaldir(self):
        """Tüm yıl seçimlerini kaldır"""
        for widget in self.yil_widgets:
            widget.checkbox.setChecked(False)
    
    def hesapla_toplam(self):
        """Toplam tutarı hesapla"""
        secili_sayisi = sum(1 for w in self.yil_widgets if w.is_selected())
        toplam = secili_sayisi * self.yillik_aidat
        
        self.toplam_label.setText(f"Toplam: {toplam:,.2f} ₺ ({secili_sayisi} yıl seçili)")
        
        # Uyarı metnini güncelle
        if secili_sayisi > 0:
            secili_yillar = [str(w.yil) for w in self.yil_widgets if w.is_selected()]
            yillar_str = ", ".join(secili_yillar)
            self.uyari_text.setText(
                f"Bu ödeme {datetime.now().year} yılı kasasına girecektir ama "
                f"{yillar_str} yılları için aidat ödenmiş sayılacaktır."
            )
        else:
            self.uyari_text.setText("Lütfen en az bir yıl seçiniz.")
    
    def get_data(self):
        """Form verilerini al"""
        secili_yillar = [w.get_data() for w in self.yil_widgets if w.is_selected()]
        
        return {
            'secili_yillar': secili_yillar,
            'kasa_id': self.kasa_combo.currentData(),
            'tarih': self.tarih_edit.date().toString("yyyy-MM-dd"),
            'yillik_aidat': self.yillik_aidat,
            'uye_id': self.uye_id,
            'uye_adi': self.uye_adi,
            'toplam_tutar': len(secili_yillar) * self.yillik_aidat
        }
    
    def validate(self):
        """Form validasyonu"""
        if not self.db or not self.uye_id:
            MessageBox("Hata", "Üye bilgisi eksik!", self).exec()
            return False
        
        if self.kasa_combo.currentIndex() < 0:
            MessageBox("Hata", "Lütfen kasa seçiniz!", self).exec()
            return False
        
        secili_sayisi = sum(1 for w in self.yil_widgets if w.is_selected())
        if secili_sayisi == 0:
            MessageBox("Hata", "Lütfen en az bir yıl seçiniz!", self).exec()
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
