"""
BADER Derneği - Gelir Yönetimi UI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QDialog, QFormLayout,
                             QDoubleSpinBox, QDateEdit, QHeaderView, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from qfluentwidgets import MessageBox
from database import Database
from models import GelirYoneticisi, KasaYoneticisi
from datetime import datetime


class GelirDialog(QDialog):
    """Gelir ekleme/düzenleme dialog"""
    
    def __init__(self, parent=None, db: Database = None, gelir_data: dict = None):
        super().__init__(parent)
        self.db = db
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.gelir_data = gelir_data
        self.setup_ui()
        self.load_kasalar()
        
        if gelir_data:
            self.load_data()
            
    def setup_ui(self):
        self.setWindowTitle("Gelir Ekle / Düzenle")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        form_layout.addRow("Tarih *:", self.tarih_edit)
        
        self.gelir_turu_combo = QComboBox()
        self.gelir_turu_combo.addItems([
            "KİRA", "BAĞIŞ", "DÜĞÜN", "KINA", "TOPLANTI", "DAVET", "DİĞER"
        ])
        form_layout.addRow("Gelir Türü *:", self.gelir_turu_combo)
        
        self.aciklama_edit = QLineEdit()
        self.aciklama_edit.setPlaceholderText("Gelir açıklaması...")
        form_layout.addRow("Açıklama *:", self.aciklama_edit)
        
        self.tutar_spin = QDoubleSpinBox()
        self.tutar_spin.setMinimum(0.01)
        self.tutar_spin.setMaximum(10000000)
        self.tutar_spin.setDecimals(2)
        self.tutar_spin.setSuffix(" ₺")
        form_layout.addRow("Tutar *:", self.tutar_spin)
        
        self.kasa_combo = QComboBox()
        form_layout.addRow("Kasa *:", self.kasa_combo)
        
        self.tahsil_eden_edit = QLineEdit()
        self.tahsil_eden_edit.setPlaceholderText("Tahsil eden kişi...")
        form_layout.addRow("Tahsil Eden:", self.tahsil_eden_edit)
        
        self.notlar_edit = QTextEdit()
        self.notlar_edit.setPlaceholderText("Ek notlar...")
        self.notlar_edit.setMaximumHeight(80)
        form_layout.addRow("Notlar:", self.notlar_edit)
        
        layout.addLayout(form_layout)
        
        # Uyarı
        warning = QLabel("ℹ️ AİDAT türündeki gelirler otomatik oluşturulur, manuel eklenemez.")
        warning.setProperty("class", "warning")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.kaydet_btn = QPushButton("Kaydet")
        self.kaydet_btn.clicked.connect(self.accept)
        
        self.iptal_btn = QPushButton("İptal")
        self.iptal_btn.setProperty("class", "secondary")
        self.iptal_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.kaydet_btn)
        button_layout.addWidget(self.iptal_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def load_kasalar(self):
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            self.kasa_combo.addItem(
                f"{kasa['kasa_adi']} ({kasa['para_birimi']})",
                kasa['kasa_id']
            )
            
    def load_data(self):
        if self.gelir_data:
            self.tarih_edit.setDate(QDate.fromString(self.gelir_data['tarih'], "yyyy-MM-dd"))
            self.gelir_turu_combo.setCurrentText(self.gelir_data['gelir_turu'])
            self.aciklama_edit.setText(self.gelir_data['aciklama'])
            self.tutar_spin.setValue(self.gelir_data['tutar'])
            
            # Kasayı seç
            for i in range(self.kasa_combo.count()):
                if self.kasa_combo.itemData(i) == self.gelir_data['kasa_id']:
                    self.kasa_combo.setCurrentIndex(i)
                    break
                    
            self.tahsil_eden_edit.setText(self.gelir_data.get('tahsil_eden', ''))
            self.notlar_edit.setPlainText(self.gelir_data.get('notlar', ''))
            
    def get_data(self):
        return {
            'tarih': self.tarih_edit.date().toString("yyyy-MM-dd"),
            'gelir_turu': self.gelir_turu_combo.currentText(),
            'aciklama': self.aciklama_edit.text().strip(),
            'tutar': self.tutar_spin.value(),
            'kasa_id': self.kasa_combo.currentData(),
            'tahsil_eden': self.tahsil_eden_edit.text().strip(),
            'notlar': self.notlar_edit.toPlainText().strip()
        }


class GelirWidget(QWidget):
    """Gelir yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.gelir_yoneticisi = GelirYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        self.load_gelirler()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("GELİR YÖNETİMİ")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Filtreler
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Tarih Aralığı:"))
        self.baslangic_date = QDateEdit()
        self.baslangic_date.setDate(QDate.currentDate().addMonths(-1))
        self.baslangic_date.setCalendarPopup(True)
        self.baslangic_date.dateChanged.connect(self.load_gelirler)
        filter_layout.addWidget(self.baslangic_date)
        
        filter_layout.addWidget(QLabel("-"))
        self.bitis_date = QDateEdit()
        self.bitis_date.setDate(QDate.currentDate())
        self.bitis_date.setCalendarPopup(True)
        self.bitis_date.dateChanged.connect(self.load_gelirler)
        filter_layout.addWidget(self.bitis_date)
        
        filter_layout.addWidget(QLabel("Gelir Türü:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü", None)
        self.tur_filter.addItems([
            "AİDAT", "KİRA", "BAĞIŞ", "DÜĞÜN", "KINA", "TOPLANTI", "DAVET", "DİĞER"
        ])
        self.tur_filter.currentIndexChanged.connect(self.load_gelirler)
        filter_layout.addWidget(self.tur_filter)
        
        filter_layout.addWidget(QLabel("Kasa:"))
        self.kasa_filter = QComboBox()
        self.kasa_filter.addItem("Tümü", None)
        self.load_kasa_filter()
        self.kasa_filter.currentIndexChanged.connect(self.load_gelirler)
        filter_layout.addWidget(self.kasa_filter)
        
        filter_layout.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Gelir")
        self.ekle_btn.clicked.connect(self.gelir_ekle)
        filter_layout.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.gelir_duzenle)
        self.duzenle_btn.setEnabled(False)
        filter_layout.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.gelir_sil)
        self.sil_btn.setEnabled(False)
        filter_layout.addWidget(self.sil_btn)
        
        layout.addLayout(filter_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Belge No", "Gelir Türü", "Açıklama", 
            "Tutar", "Kasa", "Tahsil Eden", "Notlar"
        ])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.gelir_duzenle)
        
        layout.addWidget(self.table)
        
        # Toplam
        self.toplam_label = QLabel("Toplam Gelir: 0.00 ₺")
        self.toplam_label.setProperty("class", "subtitle")
        layout.addWidget(self.toplam_label)
        
        self.setLayout(layout)
        
    def load_kasa_filter(self):
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            self.kasa_filter.addItem(kasa['kasa_adi'], kasa['kasa_id'])
            
    def load_gelirler(self):
        """Gelirleri yükle"""
        baslangic = self.baslangic_date.date().toString("yyyy-MM-dd")
        bitis = self.bitis_date.date().toString("yyyy-MM-dd")
        tur = self.tur_filter.currentText() if self.tur_filter.currentIndex() > 0 else None
        kasa_id = self.kasa_filter.currentData()
        
        gelirler = self.gelir_yoneticisi.gelir_listesi(
            baslangic_tarih=baslangic,
            bitis_tarih=bitis,
            gelir_turu=tur,
            kasa_id=kasa_id
        )
        
        self.table.setRowCount(0)
        toplam = 0.0
        
        for gelir in gelirler:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(gelir['gelir_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(gelir['tarih']))
            self.table.setItem(row, 2, QTableWidgetItem(gelir['belge_no']))
            
            tur_item = QTableWidgetItem(gelir['gelir_turu'])
            if gelir['gelir_turu'] == 'AİDAT':
                tur_item.setForeground(Qt.GlobalColor.darkBlue)
            self.table.setItem(row, 3, tur_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(gelir['aciklama']))
            self.table.setItem(row, 5, QTableWidgetItem(f"{gelir['tutar']:.2f} ₺"))
            self.table.setItem(row, 6, QTableWidgetItem(gelir['kasa_adi']))
            self.table.setItem(row, 7, QTableWidgetItem(gelir.get('tahsil_eden', '-')))
            self.table.setItem(row, 8, QTableWidgetItem(gelir.get('notlar', '-')))
            
            toplam += gelir['tutar']
        
        self.toplam_label.setText(f"Toplam Gelir: {toplam:,.2f} ₺")
        
    def on_selection_changed(self):
        selected = self.table.selectionModel().hasSelection()
        
        # AİDAT gelirlerini düzenlemek/silmek yasak
        if selected:
            row = self.table.currentRow()
            gelir_turu = self.table.item(row, 3).text()
            
            if gelir_turu == "AİDAT":
                self.duzenle_btn.setEnabled(False)
                self.sil_btn.setEnabled(False)
            else:
                self.duzenle_btn.setEnabled(True)
                self.sil_btn.setEnabled(True)
        else:
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
            
    def gelir_ekle(self):
        """Yeni gelir ekle"""
        dialog = GelirDialog(self, self.db)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama alanı boş bırakılamaz!", self).show()
                return
                
            try:
                self.gelir_yoneticisi.gelir_ekle(**data)
                self.load_gelirler()
                MessageBox("Başarılı", "Gelir kaydedildi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Gelir eklenirken hata:\n{e}", self).show()
                
    def gelir_duzenle(self):
        """Gelir düzenle"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        gelir_id = int(self.table.item(row, 0).text())
        
        # Gelir bilgilerini al
        self.db.cursor.execute("SELECT * FROM gelirler WHERE gelir_id = ?", (gelir_id,))
        gelir_data = dict(self.db.cursor.fetchone())
        
        dialog = GelirDialog(self, self.db, gelir_data)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama alanı boş bırakılamaz!", self).show()
                return
                
            try:
                self.gelir_yoneticisi.gelir_guncelle(gelir_id, **data)
                self.load_gelirler()
                MessageBox("Başarılı", "Gelir güncellendi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Güncelleme hatası:\n{e}", self).show()
                
    def gelir_sil(self):
        """Gelir sil"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        gelir_id = int(self.table.item(row, 0).text())
        tutar = self.table.item(row, 5).text()
        
        w = MessageBox("Gelir Sil", f"{tutar} tutarındaki geliri silmek istediğinize emin misiniz?", self)
        if w.exec():
            try:
                self.gelir_yoneticisi.gelir_sil(gelir_id)
                self.load_gelirler()
                MessageBox("Başarılı", "Gelir silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Silme hatası:\n{e}", self).show()

