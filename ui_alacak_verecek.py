"""
BADER Derneği - Alacak-Verecek Takip Modülü
Modern Drawer Panel UI - FluentWidgets
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from qfluentwidgets import (PushButton, TitleLabel, SubtitleLabel, BodyLabel,
                            CardWidget, MessageBox)
from database import Database
from models import AlacakYoneticisi, VerecekYoneticisi, UyeYoneticisi, KasaYoneticisi
from datetime import datetime
from ui_drawer import DrawerPanel
from ui_form_fields import (create_line_edit, create_text_edit, create_combo_box,
                            create_double_spin_box, create_date_edit)


class StatCard(CardWidget):
    """İstatistik kartı"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#64B5F6"):
        super().__init__()
        self.setMinimumHeight(100)
        self.setMinimumWidth(180)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)
        
        title_label = BodyLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 11px; font-weight: 600;")
        layout.addWidget(title_label)
        
        self.value_label = TitleLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700;")
        layout.addWidget(self.value_label)
        
        if subtitle:
            subtitle_label = BodyLabel(subtitle)
            subtitle_label.setStyleSheet("color: #999; font-size: 10px;")
            layout.addWidget(subtitle_label)
        
        self.setLayout(layout)
    
    def set_value(self, value: str):
        self.value_label.setText(value)


# ===== FORM WIDGETS =====

class YeniAlacakFormWidget(QWidget):
    """Yeni alacak formu - Drawer içinde"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.alacak_yoneticisi = AlacakYoneticisi(db)
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Alacak Türü
        self.tur_field = create_combo_box("Alacak Türü", 
            ['Kira Kaporu', 'Borç', 'Taksitli Satış', 'Emanet', 'Diğer'])
        layout.addWidget(self.tur_field[0])
        
        # Kişi/Kurum
        self.kisi_field = create_line_edit("Kişi/Kurum *", "Alacaklı kişi veya kurum adı")
        layout.addWidget(self.kisi_field[0])
        
        # Telefon
        self.telefon_field = create_line_edit("Telefon", "5XX XXX XX XX")
        layout.addWidget(self.telefon_field[0])
        
        # Üye Seç
        self.uye_field = create_combo_box("Üye (Opsiyonel)", [])
        self.uye_field[1].addItem("-- Üye Seçilmedi --", None)
        uyeler = self.uye_yoneticisi.uye_listesi(durum='Aktif')
        for uye in uyeler:
            uye_no = uye.get('uye_no') or uye.get('sicil_no') or str(uye['uye_id'])
            self.uye_field[1].addItem(f"{uye['ad_soyad']} ({uye_no})", uye['uye_id'])
        layout.addWidget(self.uye_field[0])
        
        # Toplam Tutar
        self.tutar_field = create_double_spin_box("Toplam Tutar *", 0, 999999999, " ₺")
        layout.addWidget(self.tutar_field[0])
        
        # Tarih
        self.tarih_field = create_date_edit("Alacak Tarihi")
        layout.addWidget(self.tarih_field[0])
        
        # Vade Tarihi
        self.vade_field = create_date_edit("Vade Tarihi")
        self.vade_field[1].setDate(QDate.currentDate().addMonths(1))
        layout.addWidget(self.vade_field[0])
        
        # Açıklama
        self.aciklama_field = create_text_edit("Açıklama *", "Alacak detayı...")
        layout.addWidget(self.aciklama_field[0])
        
        # Section: İlk Tahsilat
        section_label = BodyLabel("İLK TAHSİLAT (KAPORA)")
        section_label.setStyleSheet("""
            color: #64B5F6;
            font-size: 11px;
            font-weight: 700;
            padding: 8px 0 5px 0;
            border-bottom: 2px solid #64B5F6;
            margin-top: 10px;
        """)
        layout.addWidget(section_label)
        
        # İlk Tahsilat Tutarı
        self.ilk_tutar_field = create_double_spin_box("İlk Tahsilat Tutarı", 0, 999999999, " ₺")
        layout.addWidget(self.ilk_tutar_field[0])
        
        # Kasa
        self.kasa_field = create_combo_box("Kasa", [])
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            if kasa['aktif']:
                self.kasa_field[1].addItem(kasa['kasa_adi'], kasa['kasa_id'])
        layout.addWidget(self.kasa_field[0])
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self):
        """Form verilerini al"""
        return {
            'alacak_turu': self.tur_field[1].currentText(),
            'kisi_kurum': self.kisi_field[1].text().strip(),
            'kisi_telefon': self.telefon_field[1].text().strip(),
            'uye_id': self.uye_field[1].currentData(),
            'toplam_tutar': self.tutar_field[1].value(),
            'alacak_tarihi': self.tarih_field[1].date().toString("yyyy-MM-dd"),
            'vade_tarihi': self.vade_field[1].date().toString("yyyy-MM-dd"),
            'aciklama': self.aciklama_field[1].toPlainText().strip(),
            'ilk_tahsilat': self.ilk_tutar_field[1].value(),
            'kasa_id': self.kasa_field[1].currentData() if self.ilk_tutar_field[1].value() > 0 else None
        }
    
    def validate(self):
        """Form validasyonu"""
        data = self.get_data()
        if not data['kisi_kurum']:
            MessageBox("Uyarı", "Kişi/Kurum alanı boş bırakılamaz!", self).exec()
            return False
        if data['toplam_tutar'] <= 0:
            MessageBox("Uyarı", "Toplam tutar 0'dan büyük olmalı!", self).exec()
            return False
        if not data['aciklama']:
            MessageBox("Uyarı", "Açıklama alanı boş bırakılamaz!", self).exec()
            return False
        return True


class TahsilatFormWidget(QWidget):
    """Tahsilat formu - Drawer içinde"""
    
    def __init__(self, db: Database, alacak_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.alacak_id = alacak_id
        self.alacak_yoneticisi = AlacakYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Alacak bilgisi kartı
        alacak = self.alacak_yoneticisi.alacak_detay(self.alacak_id)
        
        info_card = CardWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(15, 12, 15, 12)
        
        info_label = BodyLabel(f"""
<b>Kişi:</b> {alacak['kisi_kurum']}<br>
<b>Açıklama:</b> {alacak['aciklama']}<br>
<b>Toplam:</b> {alacak['toplam_tutar']:,.2f} ₺<br>
<b>Tahsil Edilen:</b> {alacak['tahsil_edilen']:,.2f} ₺<br>
<b style="color: #F44336;">Kalan:</b> <b style="color: #F44336;">{alacak['kalan_tutar']:,.2f} ₺</b>
        """)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        info_card.setLayout(info_layout)
        layout.addWidget(info_card)
        
        # Tahsilat Tutarı
        self.tutar_field = create_double_spin_box("Tahsilat Tutarı *", 0, alacak['kalan_tutar'], " ₺")
        self.tutar_field[1].setValue(alacak['kalan_tutar'])
        layout.addWidget(self.tutar_field[0])
        
        # Tarih
        self.tarih_field = create_date_edit("Tahsilat Tarihi")
        layout.addWidget(self.tarih_field[0])
        
        # Kasa
        self.kasa_field = create_combo_box("Kasa *", [])
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            if kasa['aktif']:
                self.kasa_field[1].addItem(kasa['kasa_adi'], kasa['kasa_id'])
        layout.addWidget(self.kasa_field[0])
        
        # Ödeme Şekli
        self.odeme_field = create_combo_box("Ödeme Şekli", ['Nakit', 'Banka', 'Kredi Kartı', 'Senet'])
        layout.addWidget(self.odeme_field[0])
        
        # Açıklama
        self.aciklama_field = create_line_edit("Açıklama", "Tahsilat notu")
        layout.addWidget(self.aciklama_field[0])
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self):
        """Form verilerini al"""
        return {
            'alacak_id': self.alacak_id,
            'tutar': self.tutar_field[1].value(),
            'tahsilat_tarihi': self.tarih_field[1].date().toString("yyyy-MM-dd"),
            'kasa_id': self.kasa_field[1].currentData(),
            'odeme_sekli': self.odeme_field[1].currentText(),
            'aciklama': self.aciklama_field[1].text().strip()
        }
    
    def validate(self):
        """Form validasyonu"""
        data = self.get_data()
        if data['tutar'] <= 0:
            MessageBox("Uyarı", "Tahsilat tutarı 0'dan büyük olmalı!", self).exec()
            return False
        return True


class YeniVerecekFormWidget(QWidget):
    """Yeni verecek formu - Drawer içinde"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.verecek_yoneticisi = VerecekYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Verecek Türü
        self.tur_field = create_combo_box("Verecek Türü",
            ['Tedarikçi', 'Alınan Borç', 'Taksitli Alım', 'Fatura', 'Diğer'])
        layout.addWidget(self.tur_field[0])
        
        # Kişi/Kurum
        self.kisi_field = create_line_edit("Kişi/Kurum *", "Verecek alacağı kişi veya kurum")
        layout.addWidget(self.kisi_field[0])
        
        # Telefon
        self.telefon_field = create_line_edit("Telefon", "5XX XXX XX XX")
        layout.addWidget(self.telefon_field[0])
        
        # Toplam Tutar
        self.tutar_field = create_double_spin_box("Toplam Tutar *", 0, 999999999, " ₺")
        layout.addWidget(self.tutar_field[0])
        
        # Tarih
        self.tarih_field = create_date_edit("Verecek Tarihi")
        layout.addWidget(self.tarih_field[0])
        
        # Vade Tarihi
        self.vade_field = create_date_edit("Vade Tarihi")
        self.vade_field[1].setDate(QDate.currentDate().addMonths(1))
        layout.addWidget(self.vade_field[0])
        
        # Fatura No
        self.fatura_field = create_line_edit("Fatura No", "Fatura numarası")
        layout.addWidget(self.fatura_field[0])
        
        # Açıklama
        self.aciklama_field = create_text_edit("Açıklama *", "Verecek detayı...")
        layout.addWidget(self.aciklama_field[0])
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self):
        """Form verilerini al"""
        return {
            'verecek_turu': self.tur_field[1].currentText(),
            'kisi_kurum': self.kisi_field[1].text().strip(),
            'kisi_telefon': self.telefon_field[1].text().strip(),
            'toplam_tutar': self.tutar_field[1].value(),
            'verecek_tarihi': self.tarih_field[1].date().toString("yyyy-MM-dd"),
            'vade_tarihi': self.vade_field[1].date().toString("yyyy-MM-dd"),
            'fatura_no': self.fatura_field[1].text().strip(),
            'aciklama': self.aciklama_field[1].toPlainText().strip()
        }
    
    def validate(self):
        """Form validasyonu"""
        data = self.get_data()
        if not data['kisi_kurum']:
            MessageBox("Uyarı", "Kişi/Kurum alanı boş bırakılamaz!", self).exec()
            return False
        if data['toplam_tutar'] <= 0:
            MessageBox("Uyarı", "Toplam tutar 0'dan büyük olmalı!", self).exec()
            return False
        if not data['aciklama']:
            MessageBox("Uyarı", "Açıklama alanı boş bırakılamaz!", self).exec()
            return False
        return True


class OdemeFormWidget(QWidget):
    """Ödeme formu - Drawer içinde"""
    
    def __init__(self, db: Database, verecek_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.verecek_id = verecek_id
        self.verecek_yoneticisi = VerecekYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Verecek bilgisi kartı
        verecek = self.verecek_yoneticisi.verecek_detay(self.verecek_id)
        
        info_card = CardWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(15, 12, 15, 12)
        
        info_label = BodyLabel(f"""
<b>Kişi:</b> {verecek['kisi_kurum']}<br>
<b>Açıklama:</b> {verecek['aciklama']}<br>
<b>Toplam:</b> {verecek['toplam_tutar']:,.2f} ₺<br>
<b>Ödenen:</b> {verecek['odenen']:,.2f} ₺<br>
<b style="color: #F44336;">Kalan:</b> <b style="color: #F44336;">{verecek['kalan_tutar']:,.2f} ₺</b>
        """)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        info_card.setLayout(info_layout)
        layout.addWidget(info_card)
        
        # Ödeme Tutarı
        self.tutar_field = create_double_spin_box("Ödeme Tutarı *", 0, verecek['kalan_tutar'], " ₺")
        self.tutar_field[1].setValue(verecek['kalan_tutar'])
        layout.addWidget(self.tutar_field[0])
        
        # Tarih
        self.tarih_field = create_date_edit("Ödeme Tarihi")
        layout.addWidget(self.tarih_field[0])
        
        # Kasa
        self.kasa_field = create_combo_box("Kasa *", [])
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            if kasa['aktif']:
                self.kasa_field[1].addItem(kasa['kasa_adi'], kasa['kasa_id'])
        layout.addWidget(self.kasa_field[0])
        
        # Ödeme Şekli
        self.odeme_field = create_combo_box("Ödeme Şekli", ['Nakit', 'Banka', 'Kredi Kartı', 'Senet'])
        layout.addWidget(self.odeme_field[0])
        
        # Açıklama
        self.aciklama_field = create_line_edit("Açıklama", "Ödeme notu")
        layout.addWidget(self.aciklama_field[0])
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_data(self):
        """Form verilerini al"""
        return {
            'verecek_id': self.verecek_id,
            'tutar': self.tutar_field[1].value(),
            'odeme_tarihi': self.tarih_field[1].date().toString("yyyy-MM-dd"),
            'kasa_id': self.kasa_field[1].currentData(),
            'odeme_sekli': self.odeme_field[1].currentText(),
            'aciklama': self.aciklama_field[1].text().strip()
        }
    
    def validate(self):
        """Form validasyonu"""
        data = self.get_data()
        if data['tutar'] <= 0:
            MessageBox("Uyarı", "Ödeme tutarı 0'dan büyük olmalı!", self).exec()
            return False
        return True


# ===== ANA WIDGET =====

class AlacakVerecekWidget(QWidget):
    """Ana alacak-verecek widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.alacak_yoneticisi = AlacakYoneticisi(db)
        self.verecek_yoneticisi = VerecekYoneticisi(db)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(15)
        
        # Başlık
        title_label = TitleLabel("💰 ALACAK-VERECEK YÖNETİMİ")
        layout.addWidget(title_label)
        
        subtitle = BodyLabel("Alacak ve borç takip sistemi")
        subtitle.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(subtitle)
        
        # Özet kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.alacak_card = StatCard("TOPLAM ALACAK", "0 ₺", "", "#4CAF50")
        self.tahsil_card = StatCard("TAHSİL EDİLEN", "0 ₺", "", "#2196F3")
        self.verecek_card = StatCard("TOPLAM VERECEK", "0 ₺", "", "#F44336")
        self.odenen_card = StatCard("ÖDENEN", "0 ₺", "", "#FF9800")
        
        cards_layout.addWidget(self.alacak_card)
        cards_layout.addWidget(self.tahsil_card)
        cards_layout.addWidget(self.verecek_card)
        cards_layout.addWidget(self.odenen_card)
        cards_layout.addStretch()
        
        layout.addLayout(cards_layout)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.yeni_alacak_btn = PushButton("➕ Yeni Alacak")
        self.yeni_alacak_btn.clicked.connect(self.yeni_alacak)
        btn_layout.addWidget(self.yeni_alacak_btn)
        
        self.yeni_verecek_btn = PushButton("➕ Yeni Verecek")
        self.yeni_verecek_btn.clicked.connect(self.yeni_verecek)
        btn_layout.addWidget(self.yeni_verecek_btn)
        
        btn_layout.addStretch()
        
        self.yenile_btn = PushButton("🔄 Yenile")
        self.yenile_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.yenile_btn)
        
        layout.addLayout(btn_layout)
        
        # Tablar
        self.tabs = QTabWidget()
        
        # Alacaklar Tab
        alacak_widget = QWidget()
        alacak_layout = QVBoxLayout()
        
        self.alacak_table = QTableWidget()
        self.alacak_table.setColumnCount(8)
        self.alacak_table.setHorizontalHeaderLabels([
            "ID", "Kişi/Kurum", "Tür", "Toplam", "Tahsil", "Kalan", "Vade", "Durum"
        ])
        self.alacak_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.alacak_table.setAlternatingRowColors(True)
        self.alacak_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.alacak_table.doubleClicked.connect(self.tahsilat_yap)
        alacak_layout.addWidget(self.alacak_table)
        
        alacak_btn_layout = QHBoxLayout()
        self.tahsilat_btn = PushButton("💰 Tahsilat Yap")
        self.tahsilat_btn.clicked.connect(self.tahsilat_yap)
        alacak_btn_layout.addWidget(self.tahsilat_btn)
        alacak_btn_layout.addStretch()
        alacak_layout.addLayout(alacak_btn_layout)
        
        alacak_widget.setLayout(alacak_layout)
        self.tabs.addTab(alacak_widget, "📊 Alacaklar")
        
        # Verecekler Tab
        verecek_widget = QWidget()
        verecek_layout = QVBoxLayout()
        
        self.verecek_table = QTableWidget()
        self.verecek_table.setColumnCount(8)
        self.verecek_table.setHorizontalHeaderLabels([
            "ID", "Kişi/Kurum", "Tür", "Toplam", "Ödenen", "Kalan", "Vade", "Durum"
        ])
        self.verecek_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.verecek_table.setAlternatingRowColors(True)
        self.verecek_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verecek_table.doubleClicked.connect(self.odeme_yap)
        verecek_layout.addWidget(self.verecek_table)
        
        verecek_btn_layout = QHBoxLayout()
        self.odeme_btn = PushButton("💸 Ödeme Yap")
        self.odeme_btn.clicked.connect(self.odeme_yap)
        verecek_btn_layout.addWidget(self.odeme_btn)
        verecek_btn_layout.addStretch()
        verecek_layout.addLayout(verecek_btn_layout)
        
        verecek_widget.setLayout(verecek_layout)
        self.tabs.addTab(verecek_widget, "📉 Verecekler")
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
    
    def load_data(self):
        """Verileri yükle"""
        # Alacak özeti
        alacak_ozet = self.alacak_yoneticisi.ozet()
        self.alacak_card.set_value(f"{alacak_ozet.get('toplam_kalan_tutar', 0):,.0f} ₺")
        self.tahsil_card.set_value(f"{alacak_ozet.get('toplam_tahsil_edilen', 0):,.0f} ₺")
        
        # Verecek özeti
        verecek_ozet = self.verecek_yoneticisi.ozet()
        self.verecek_card.set_value(f"{verecek_ozet.get('toplam_kalan_tutar', 0):,.0f} ₺")
        self.odenen_card.set_value(f"{verecek_ozet.get('toplam_odenen', 0):,.0f} ₺")
        
        # Alacaklar tablosu
        alacaklar = self.alacak_yoneticisi.liste_getir()
        self.alacak_table.setRowCount(len(alacaklar))
        
        for row, alacak in enumerate(alacaklar):
            self.alacak_table.setItem(row, 0, QTableWidgetItem(str(alacak['id'])))
            self.alacak_table.setItem(row, 1, QTableWidgetItem(alacak['kisi_kurum']))
            self.alacak_table.setItem(row, 2, QTableWidgetItem(alacak['alacak_turu']))
            self.alacak_table.setItem(row, 3, QTableWidgetItem(f"{alacak['toplam_tutar']:,.2f}"))
            self.alacak_table.setItem(row, 4, QTableWidgetItem(f"{alacak['tahsil_edilen']:,.2f}"))
            
            kalan_item = QTableWidgetItem(f"{alacak['kalan_tutar']:,.2f}")
            if alacak['kalan_tutar'] > 0:
                kalan_item.setForeground(QColor("#F44336"))
            self.alacak_table.setItem(row, 5, kalan_item)
            
            vade = alacak['vade_tarihi'] if alacak['vade_tarihi'] else "-"
            vade_item = QTableWidgetItem(vade)
            if alacak['vade_tarihi'] and alacak['vade_tarihi'] < datetime.now().strftime("%Y-%m-%d"):
                if alacak['durum'] not in ['Tahsil Edildi', 'İptal']:
                    vade_item.setBackground(QColor("#FFEBEE"))
            self.alacak_table.setItem(row, 6, vade_item)
            
            durum_item = QTableWidgetItem(alacak['durum'])
            if alacak['durum'] == 'Tahsil Edildi':
                durum_item.setForeground(QColor("#4CAF50"))
            elif alacak['durum'] == 'İptal':
                durum_item.setForeground(QColor("#999"))
            self.alacak_table.setItem(row, 7, durum_item)
        
        # Verecekler tablosu
        verecekler = self.verecek_yoneticisi.liste_getir()
        self.verecek_table.setRowCount(len(verecekler))
        
        for row, verecek in enumerate(verecekler):
            self.verecek_table.setItem(row, 0, QTableWidgetItem(str(verecek['id'])))
            self.verecek_table.setItem(row, 1, QTableWidgetItem(verecek['kisi_kurum']))
            self.verecek_table.setItem(row, 2, QTableWidgetItem(verecek['verecek_turu']))
            self.verecek_table.setItem(row, 3, QTableWidgetItem(f"{verecek['toplam_tutar']:,.2f}"))
            self.verecek_table.setItem(row, 4, QTableWidgetItem(f"{verecek['odenen']:,.2f}"))
            
            kalan_item = QTableWidgetItem(f"{verecek['kalan_tutar']:,.2f}")
            if verecek['kalan_tutar'] > 0:
                kalan_item.setForeground(QColor("#F44336"))
            self.verecek_table.setItem(row, 5, kalan_item)
            
            vade = verecek['vade_tarihi'] if verecek['vade_tarihi'] else "-"
            vade_item = QTableWidgetItem(vade)
            if verecek['vade_tarihi'] and verecek['vade_tarihi'] < datetime.now().strftime("%Y-%m-%d"):
                if verecek['durum'] not in ['Ödendi', 'İptal']:
                    vade_item.setBackground(QColor("#FFEBEE"))
            self.verecek_table.setItem(row, 6, vade_item)
            
            durum_item = QTableWidgetItem(verecek['durum'])
            if verecek['durum'] == 'Ödendi':
                durum_item.setForeground(QColor("#4CAF50"))
            elif verecek['durum'] == 'İptal':
                durum_item.setForeground(QColor("#999"))
            self.verecek_table.setItem(row, 7, durum_item)
    
    def yeni_alacak(self):
        """Yeni alacak ekle - Drawer aç"""
        form = YeniAlacakFormWidget(self.db)
        drawer = DrawerPanel(self, "Yeni Alacak Ekle", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.alacak_yoneticisi.alacak_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Alacak kaydı oluşturuldu!", self).exec()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Alacak eklenirken hata:\n{str(e)}", self).exec()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def yeni_verecek(self):
        """Yeni verecek ekle - Drawer aç"""
        form = YeniVerecekFormWidget(self.db)
        drawer = DrawerPanel(self, "Yeni Verecek Ekle", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.verecek_yoneticisi.verecek_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Verecek kaydı oluşturuldu!", self).exec()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Verecek eklenirken hata:\n{str(e)}", self).exec()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def tahsilat_yap(self):
        """Seçili alacak için tahsilat yap - Drawer aç"""
        selected = self.alacak_table.selectedItems()
        if not selected:
            MessageBox("Uyarı", "Lütfen bir alacak seçin!", self).exec()
            return
        
        row = selected[0].row()
        alacak_id = int(self.alacak_table.item(row, 0).text())
        
        form = TahsilatFormWidget(self.db, alacak_id)
        drawer = DrawerPanel(self, "Tahsilat Yap", form, width=450)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.alacak_yoneticisi.tahsilat_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Tahsilat kaydedildi!", self).exec()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Tahsilat kaydedilirken hata:\n{str(e)}", self).exec()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def odeme_yap(self):
        """Seçili verecek için ödeme yap - Drawer aç"""
        selected = self.verecek_table.selectedItems()
        if not selected:
            MessageBox("Uyarı", "Lütfen bir verecek seçin!", self).exec()
            return
        
        row = selected[0].row()
        verecek_id = int(self.verecek_table.item(row, 0).text())
        
        form = OdemeFormWidget(self.db, verecek_id)
        drawer = DrawerPanel(self, "Ödeme Yap", form, width=450)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.verecek_yoneticisi.odeme_yap(**data)
                self.load_data()
                MessageBox("Başarılı", "Ödeme kaydedildi!", self).exec()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Ödeme kaydedilirken hata:\n{str(e)}", self).exec()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
