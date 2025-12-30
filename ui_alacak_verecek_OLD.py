"""
BADER Derneği - Alacak-Verecek Takip Modülü
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QDateEdit, QLineEdit, QTextEdit, QComboBox,
                             QDoubleSpinBox, QGroupBox, QGridLayout, QLabel,
                             QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor
from qfluentwidgets import (PushButton, TitleLabel, SubtitleLabel, BodyLabel,
                            CardWidget, MessageBox)
from database import Database
from models import AlacakYoneticisi, VerecekYoneticisi, UyeYoneticisi, KasaYoneticisi
from datetime import datetime


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


class YeniAlacakDialog(QDialog):
    """Yeni alacak ekleme dialog"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.alacak_yoneticisi = AlacakYoneticisi(db)
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Yeni Alacak Ekle")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Alacak Türü
        self.tur_combo = QComboBox()
        self.tur_combo.addItems(['Kira Kaporu', 'Borç', 'Taksitli Satış', 'Emanet', 'Diğer'])
        form_layout.addRow("Alacak Türü:", self.tur_combo)
        
        # Kişi/Kurum
        self.kisi_edit = QLineEdit()
        form_layout.addRow("Kişi/Kurum:*", self.kisi_edit)
        
        # Telefon
        self.telefon_edit = QLineEdit()
        form_layout.addRow("Telefon:", self.telefon_edit)
        
        # Üye Seç (Opsiyonel)
        uye_layout = QHBoxLayout()
        self.uye_combo = QComboBox()
        self.uye_combo.addItem("-- Üye Seçilmedi --", None)
        uyeler = self.uye_yoneticisi.uye_listesi(durum='Aktif')
        for uye in uyeler:
            self.uye_combo.addItem(f"{uye['ad_soyad']} ({uye['uye_no']})", uye['uye_id'])
        uye_layout.addWidget(self.uye_combo)
        form_layout.addRow("Üye:", uye_layout)
        
        # Toplam Tutar
        self.tutar_spin = QDoubleSpinBox()
        self.tutar_spin.setRange(0, 999999999)
        self.tutar_spin.setDecimals(2)
        self.tutar_spin.setSuffix(" ₺")
        form_layout.addRow("Toplam Tutar:*", self.tutar_spin)
        
        # Tarih
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        form_layout.addRow("Tarih:", self.tarih_edit)
        
        # Vade Tarihi
        self.vade_edit = QDateEdit()
        self.vade_edit.setDate(QDate.currentDate().addMonths(1))
        self.vade_edit.setCalendarPopup(True)
        form_layout.addRow("Vade Tarihi:", self.vade_edit)
        
        # Açıklama
        self.aciklama_edit = QTextEdit()
        self.aciklama_edit.setMaximumHeight(60)
        form_layout.addRow("Açıklama:*", self.aciklama_edit)
        
        # İlk Tahsilat Grubu
        ilk_grup = QGroupBox("İlk Tahsilat (Kapora)")
        ilk_layout = QFormLayout()
        
        self.ilk_tutar_spin = QDoubleSpinBox()
        self.ilk_tutar_spin.setRange(0, 999999999)
        self.ilk_tutar_spin.setDecimals(2)
        self.ilk_tutar_spin.setSuffix(" ₺")
        ilk_layout.addRow("Tutar:", self.ilk_tutar_spin)
        
        self.kasa_combo = QComboBox()
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            if kasa['aktif']:
                self.kasa_combo.addItem(kasa['kasa_adi'], kasa['kasa_id'])
        ilk_layout.addRow("Kasa:", self.kasa_combo)
        
        ilk_grup.setLayout(ilk_layout)
        form_layout.addRow(ilk_grup)
        
        layout.addLayout(form_layout)
        
        # Butonlar
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.kaydet)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def kaydet(self):
        """Alacağı kaydet"""
        kisi = self.kisi_edit.text().strip()
        tutar = self.tutar_spin.value()
        aciklama = self.aciklama_edit.toPlainText().strip()
        
        if not kisi or tutar <= 0 or not aciklama:
            w = MessageBox("Uyarı", "Lütfen gerekli alanları doldurun!", self)
            w.exec()
            return
        
        try:
            alacak_id = self.alacak_yoneticisi.alacak_ekle(
                alacak_turu=self.tur_combo.currentText(),
                aciklama=aciklama,
                kisi_kurum=kisi,
                kisi_telefon=self.telefon_edit.text(),
                toplam_tutar=tutar,
                alacak_tarihi=self.tarih_edit.date().toString("yyyy-MM-dd"),
                vade_tarihi=self.vade_edit.date().toString("yyyy-MM-dd"),
                ilk_tahsilat=self.ilk_tutar_spin.value(),
                kasa_id=self.kasa_combo.currentData() if self.ilk_tutar_spin.value() > 0 else None,
                uye_id=self.uye_combo.currentData()
            )
            
            w = MessageBox("Başarılı", "Alacak kaydı oluşturuldu!", self)
            w.exec()
            self.accept()
            
        except Exception as e:
            w = MessageBox("Hata", f"Alacak eklenirken hata oluştu:\n{str(e)}", self)
            w.exec()


class TahsilatDialog(QDialog):
    """Tahsilat yapma dialog"""
    
    def __init__(self, db: Database, alacak_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.alacak_id = alacak_id
        self.alacak_yoneticisi = AlacakYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Tahsilat Yap")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Alacak bilgisi
        alacak = self.alacak_yoneticisi.alacak_detay(self.alacak_id)
        
        info_label = BodyLabel(f"""
        <b>Kişi:</b> {alacak['kisi_kurum']}<br>
        <b>Açıklama:</b> {alacak['aciklama']}<br>
        <b>Toplam:</b> {alacak['toplam_tutar']:,.2f} ₺<br>
        <b>Tahsil Edilen:</b> {alacak['tahsil_edilen']:,.2f} ₺<br>
        <b>Kalan:</b> {alacak['kalan_tutar']:,.2f} ₺
        """)
        info_label.setStyleSheet("background-color: #f5f5f5; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        
        # Tutar
        self.tutar_spin = QDoubleSpinBox()
        self.tutar_spin.setRange(0, alacak['kalan_tutar'])
        self.tutar_spin.setValue(alacak['kalan_tutar'])
        self.tutar_spin.setDecimals(2)
        self.tutar_spin.setSuffix(" ₺")
        form_layout.addRow("Tahsilat Tutarı:*", self.tutar_spin)
        
        # Tarih
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        form_layout.addRow("Tarih:", self.tarih_edit)
        
        # Kasa
        self.kasa_combo = QComboBox()
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            if kasa['aktif']:
                self.kasa_combo.addItem(kasa['kasa_adi'], kasa['kasa_id'])
        form_layout.addRow("Kasa:*", self.kasa_combo)
        
        # Ödeme Şekli
        self.odeme_combo = QComboBox()
        self.odeme_combo.addItems(['Nakit', 'Banka', 'Kredi Kartı', 'Senet'])
        form_layout.addRow("Ödeme Şekli:", self.odeme_combo)
        
        # Açıklama
        self.aciklama_edit = QLineEdit()
        form_layout.addRow("Açıklama:", self.aciklama_edit)
        
        layout.addLayout(form_layout)
        
        # Butonlar
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.kaydet)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def kaydet(self):
        """Tahsilatı kaydet"""
        tutar = self.tutar_spin.value()
        
        if tutar <= 0:
            w = MessageBox("Uyarı", "Tahsilat tutarı 0'dan büyük olmalı!", self)
            w.exec()
            return
        
        try:
            self.alacak_yoneticisi.tahsilat_ekle(
                alacak_id=self.alacak_id,
                tutar=tutar,
                kasa_id=self.kasa_combo.currentData(),
                tahsilat_tarihi=self.tarih_edit.date().toString("yyyy-MM-dd"),
                odeme_sekli=self.odeme_combo.currentText(),
                aciklama=self.aciklama_edit.text()
            )
            
            w = MessageBox("Başarılı", "Tahsilat kaydedildi!", self)
            w.exec()
            self.accept()
            
        except Exception as e:
            w = MessageBox("Hata", f"Tahsilat kaydedilirken hata oluştu:\n{str(e)}", self)
            w.exec()


class YeniVerecekDialog(QDialog):
    """Yeni verecek ekleme dialog"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.verecek_yoneticisi = VerecekYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Yeni Verecek Ekle")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Verecek Türü
        self.tur_combo = QComboBox()
        self.tur_combo.addItems(['Tedarikçi', 'Alınan Borç', 'Taksitli Alım', 'Fatura', 'Diğer'])
        form_layout.addRow("Verecek Türü:", self.tur_combo)
        
        # Kişi/Kurum
        self.kisi_edit = QLineEdit()
        form_layout.addRow("Kişi/Kurum:*", self.kisi_edit)
        
        # Telefon
        self.telefon_edit = QLineEdit()
        form_layout.addRow("Telefon:", self.telefon_edit)
        
        # Toplam Tutar
        self.tutar_spin = QDoubleSpinBox()
        self.tutar_spin.setRange(0, 999999999)
        self.tutar_spin.setDecimals(2)
        self.tutar_spin.setSuffix(" ₺")
        form_layout.addRow("Toplam Tutar:*", self.tutar_spin)
        
        # Tarih
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        form_layout.addRow("Tarih:", self.tarih_edit)
        
        # Vade Tarihi
        self.vade_edit = QDateEdit()
        self.vade_edit.setDate(QDate.currentDate().addMonths(1))
        self.vade_edit.setCalendarPopup(True)
        form_layout.addRow("Vade Tarihi:", self.vade_edit)
        
        # Fatura No
        self.fatura_edit = QLineEdit()
        form_layout.addRow("Fatura No:", self.fatura_edit)
        
        # Açıklama
        self.aciklama_edit = QTextEdit()
        self.aciklama_edit.setMaximumHeight(60)
        form_layout.addRow("Açıklama:*", self.aciklama_edit)
        
        layout.addLayout(form_layout)
        
        # Butonlar
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.kaydet)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def kaydet(self):
        """Verecek kaydet"""
        kisi = self.kisi_edit.text().strip()
        tutar = self.tutar_spin.value()
        aciklama = self.aciklama_edit.toPlainText().strip()
        
        if not kisi or tutar <= 0 or not aciklama:
            w = MessageBox("Uyarı", "Lütfen gerekli alanları doldurun!", self)
            w.exec()
            return
        
        try:
            verecek_id = self.verecek_yoneticisi.verecek_ekle(
                verecek_turu=self.tur_combo.currentText(),
                aciklama=aciklama,
                kisi_kurum=kisi,
                kisi_telefon=self.telefon_edit.text(),
                toplam_tutar=tutar,
                verecek_tarihi=self.tarih_edit.date().toString("yyyy-MM-dd"),
                vade_tarihi=self.vade_edit.date().toString("yyyy-MM-dd"),
                fatura_no=self.fatura_edit.text()
            )
            
            w = MessageBox("Başarılı", "Verecek kaydı oluşturuldu!", self)
            w.exec()
            self.accept()
            
        except Exception as e:
            w = MessageBox("Hata", f"Verecek eklenirken hata oluştu:\n{str(e)}", self)
            w.exec()


class OdemeDialog(QDialog):
    """Ödeme yapma dialog"""
    
    def __init__(self, db: Database, verecek_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.verecek_id = verecek_id
        self.verecek_yoneticisi = VerecekYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Ödeme Yap")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Verecek bilgisi
        verecek = self.verecek_yoneticisi.verecek_detay(self.verecek_id)
        
        info_label = BodyLabel(f"""
        <b>Kişi:</b> {verecek['kisi_kurum']}<br>
        <b>Açıklama:</b> {verecek['aciklama']}<br>
        <b>Toplam:</b> {verecek['toplam_tutar']:,.2f} ₺<br>
        <b>Ödenen:</b> {verecek['odenen']:,.2f} ₺<br>
        <b>Kalan:</b> {verecek['kalan_tutar']:,.2f} ₺
        """)
        info_label.setStyleSheet("background-color: #f5f5f5; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        
        # Tutar
        self.tutar_spin = QDoubleSpinBox()
        self.tutar_spin.setRange(0, verecek['kalan_tutar'])
        self.tutar_spin.setValue(verecek['kalan_tutar'])
        self.tutar_spin.setDecimals(2)
        self.tutar_spin.setSuffix(" ₺")
        form_layout.addRow("Ödeme Tutarı:*", self.tutar_spin)
        
        # Tarih
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        form_layout.addRow("Tarih:", self.tarih_edit)
        
        # Kasa
        self.kasa_combo = QComboBox()
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            if kasa['aktif']:
                self.kasa_combo.addItem(kasa['kasa_adi'], kasa['kasa_id'])
        form_layout.addRow("Kasa:*", self.kasa_combo)
        
        # Ödeme Şekli
        self.odeme_combo = QComboBox()
        self.odeme_combo.addItems(['Nakit', 'Banka', 'Kredi Kartı', 'Senet'])
        form_layout.addRow("Ödeme Şekli:", self.odeme_combo)
        
        # Açıklama
        self.aciklama_edit = QLineEdit()
        form_layout.addRow("Açıklama:", self.aciklama_edit)
        
        layout.addLayout(form_layout)
        
        # Butonlar
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.kaydet)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def kaydet(self):
        """Ödemeyi kaydet"""
        tutar = self.tutar_spin.value()
        
        if tutar <= 0:
            w = MessageBox("Uyarı", "Ödeme tutarı 0'dan büyük olmalı!", self)
            w.exec()
            return
        
        try:
            self.verecek_yoneticisi.odeme_yap(
                verecek_id=self.verecek_id,
                tutar=tutar,
                kasa_id=self.kasa_combo.currentData(),
                odeme_tarihi=self.tarih_edit.date().toString("yyyy-MM-dd"),
                odeme_sekli=self.odeme_combo.currentText(),
                aciklama=self.aciklama_edit.text()
            )
            
            w = MessageBox("Başarılı", "Ödeme kaydedildi!", self)
            w.exec()
            self.accept()
            
        except Exception as e:
            w = MessageBox("Hata", f"Ödeme kaydedilirken hata oluştu:\n{str(e)}", self)
            w.exec()


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
        """Yeni alacak ekle"""
        dialog = YeniAlacakDialog(self.db, self)
        if dialog.exec():
            self.load_data()
    
    def yeni_verecek(self):
        """Yeni verecek ekle"""
        dialog = YeniVerecekDialog(self.db, self)
        if dialog.exec():
            self.load_data()
    
    def tahsilat_yap(self):
        """Seçili alacak için tahsilat yap"""
        selected = self.alacak_table.selectedItems()
        if not selected:
            w = MessageBox("Uyarı", "Lütfen bir alacak seçin!", self)
            w.exec()
            return
        
        row = selected[0].row()
        alacak_id = int(self.alacak_table.item(row, 0).text())
        
        dialog = TahsilatDialog(self.db, alacak_id, self)
        if dialog.exec():
            self.load_data()
    
    def odeme_yap(self):
        """Seçili verecek için ödeme yap"""
        selected = self.verecek_table.selectedItems()
        if not selected:
            w = MessageBox("Uyarı", "Lütfen bir verecek seçin!", self)
            w.exec()
            return
        
        row = selected[0].row()
        verecek_id = int(self.verecek_table.item(row, 0).text())
        
        dialog = OdemeDialog(self.db, verecek_id, self)
        if dialog.exec():
            self.load_data()
