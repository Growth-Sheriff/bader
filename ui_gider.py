"""
BADER Derneği - Gider Yönetimi UI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QDialog, QFormLayout,
                             QDoubleSpinBox, QDateEdit, QHeaderView, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from qfluentwidgets import MessageBox
from database import Database
from models import GiderYoneticisi, KasaYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import create_line_edit, create_combo_box, create_text_edit, create_date_edit, create_double_spin_box
from ui_helpers import export_table_to_excel, setup_resizable_table
from ui_login import session


class GiderFormWidget(QWidget):
    """Gider ekleme/düzenleme formu"""
    
    def __init__(self, db: Database, gider_data: dict = None):
        super().__init__()
        self.db = db
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.gider_yoneticisi = GiderYoneticisi(db)
        self.gider_data = gider_data
        self.setup_ui()
        self.load_kasalar()
        self.load_gider_turleri()
        
        if gider_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Tarih
        self.tarih_edit = create_date_edit("Tarih *")
        self.tarih_edit[1].setDate(QDate.currentDate())
        layout.addWidget(self.tarih_edit[0])
        
        # Gider Türü
        self.gider_turu_combo = create_combo_box("Gider Türü *")
        self.gider_turu_combo[1].setEditable(True)
        self.gider_turu_combo[1].currentTextChanged.connect(self.on_tur_changed)
        layout.addWidget(self.gider_turu_combo[0])
        
        # Alt Kategori
        self.alt_kategori_combo = create_combo_box("Alt Kategori")
        self.alt_kategori_combo[1].setEditable(True)
        layout.addWidget(self.alt_kategori_combo[0])
        
        # Açıklama
        self.aciklama_edit = create_line_edit("Açıklama *", "Gider açıklaması...")
        layout.addWidget(self.aciklama_edit[0])
        
        # Tutar
        self.tutar_spin = create_double_spin_box("Tutar *")
        self.tutar_spin[1].setMinimum(0.01)
        self.tutar_spin[1].setMaximum(10000000)
        self.tutar_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tutar_spin[0])
        
        # Kasa
        self.kasa_combo = create_combo_box("Kasa *")
        layout.addWidget(self.kasa_combo[0])
        
        # Ödeyen
        self.odeyen_edit = create_line_edit("Ödeyen", "Ödemeyi yapan kişi...")
        layout.addWidget(self.odeyen_edit[0])
        
        # Notlar
        self.notlar_edit = create_text_edit("Notlar", "Ek notlar...")
        layout.addWidget(self.notlar_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
    
    def on_tur_changed(self, tur: str):
        """Gider türü değiştiğinde alt kategorileri güncelle"""
        self.alt_kategori_combo[1].clear()
        alt_kategoriler = self.gider_yoneticisi.gider_alt_kategorileri(tur)
        if alt_kategoriler:
            self.alt_kategori_combo[1].addItems(alt_kategoriler)
        self.alt_kategori_combo[0].setVisible(len(alt_kategoriler) > 0)
        
    def load_kasalar(self):
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            self.kasa_combo[1].addItem(
                f"{kasa['kasa_adi']} ({kasa['para_birimi']})",
                kasa['kasa_id']
            )
            
    def load_gider_turleri(self):
        turler = self.gider_yoneticisi.gider_turleri_listesi()
        self.gider_turu_combo[1].addItems(turler)
        # İlk yüklemede alt kategorileri doldur
        if turler:
            self.on_tur_changed(turler[0])
        
    def load_data(self):
        if self.gider_data:
            self.tarih_edit[1].setDate(QDate.fromString(self.gider_data['tarih'], "yyyy-MM-dd"))
            self.gider_turu_combo[1].setCurrentText(self.gider_data['gider_turu'])
            
            # Alt kategori varsa ayarla
            alt_kat = self.gider_data.get('alt_kategori', '')
            if alt_kat:
                self.alt_kategori_combo[1].setCurrentText(alt_kat)
            
            self.aciklama_edit[1].setText(self.gider_data['aciklama'])
            self.tutar_spin[1].setValue(self.gider_data['tutar'])
            
            for i in range(self.kasa_combo[1].count()):
                if self.kasa_combo[1].itemData(i) == self.gider_data['kasa_id']:
                    self.kasa_combo[1].setCurrentIndex(i)
                    break
                    
            self.odeyen_edit[1].setText(self.gider_data.get('odeyen', ''))
            self.notlar_edit[1].setPlainText(self.gider_data.get('notlar', ''))
            
    def get_data(self):
        alt_kategori = self.alt_kategori_combo[1].currentText().strip() if self.alt_kategori_combo[0].isVisible() else ""
        return {
            'tarih': self.tarih_edit[1].date().toString("yyyy-MM-dd"),
            'gider_turu': self.gider_turu_combo[1].currentText().strip(),
            'alt_kategori': alt_kategori,
            'aciklama': self.aciklama_edit[1].text().strip(),
            'tutar': self.tutar_spin[1].value(),
            'kasa_id': self.kasa_combo[1].currentData(),
            'odeyen': self.odeyen_edit[1].text().strip(),
            'notlar': self.notlar_edit[1].toPlainText().strip()
        }


class GiderWidget(QWidget):
    """Gider yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.gider_yoneticisi = GiderYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        self.load_giderler()
        self.apply_permissions()
    
    def apply_permissions(self):
        """Kullanıcı izinlerine göre butonları ayarla"""
        self.ekle_btn.setVisible(session.has_permission('gider_ekle'))
        self.duzenle_btn.setVisible(session.has_permission('gider_duzenle'))
        self.sil_btn.setVisible(session.has_permission('gider_sil'))
        self.export_btn.setVisible(session.has_permission('rapor_export'))
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("GİDER YÖNETİMİ")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        # Filtreler
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Tarih Aralığı:"))
        self.baslangic_date = QDateEdit()
        self.baslangic_date.setDate(QDate.currentDate().addMonths(-1))
        self.baslangic_date.setCalendarPopup(True)
        self.baslangic_date.dateChanged.connect(self.load_giderler)
        filter_layout.addWidget(self.baslangic_date)
        
        filter_layout.addWidget(QLabel("-"))
        self.bitis_date = QDateEdit()
        self.bitis_date.setDate(QDate.currentDate())
        self.bitis_date.setCalendarPopup(True)
        self.bitis_date.dateChanged.connect(self.load_giderler)
        filter_layout.addWidget(self.bitis_date)
        
        filter_layout.addWidget(QLabel("Gider Türü:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü", None)
        self.load_gider_tur_filter()
        self.tur_filter.currentIndexChanged.connect(self.load_giderler)
        filter_layout.addWidget(self.tur_filter)
        
        filter_layout.addWidget(QLabel("Kasa:"))
        self.kasa_filter = QComboBox()
        self.kasa_filter.addItem("Tümü", None)
        self.load_kasa_filter()
        self.kasa_filter.currentIndexChanged.connect(self.load_giderler)
        filter_layout.addWidget(self.kasa_filter)
        
        filter_layout.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Gider")
        self.ekle_btn.clicked.connect(self.gider_ekle)
        filter_layout.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.gider_duzenle)
        self.duzenle_btn.setEnabled(False)
        filter_layout.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.gider_sil)
        self.sil_btn.setEnabled(False)
        filter_layout.addWidget(self.sil_btn)
        
        # Excel export
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.setToolTip("Listeyi Excel'e Aktar")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "giderler", self))
        filter_layout.addWidget(self.export_btn)
        
        layout.addLayout(filter_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "İşlem No", "Gider Türü", "Açıklama", 
            "Tutar", "Kasa", "Ödeyen", "Notlar"
        ])
        
        # Responsive sütunlar - hareket ettirilebilir, sağ tık ile gizle/göster
        setup_resizable_table(self.table, table_id="giderler_tablosu", stretch_column=4)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Inline editing KAPALI
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.gider_duzenle)  # Çift tıkla → Drawer aç
        
        layout.addWidget(self.table)
        
        # Toplam
        self.toplam_label = QLabel("Toplam Gider: 0.00 ₺")
        self.toplam_label.setProperty("class", "subtitle")
        layout.addWidget(self.toplam_label)
        
        self.setLayout(layout)
        
    def load_kasa_filter(self):
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            self.kasa_filter.addItem(kasa['kasa_adi'], kasa['kasa_id'])
            
    def load_gider_tur_filter(self):
        turler = self.gider_yoneticisi.gider_turleri_listesi()
        for tur in turler:
            self.tur_filter.addItem(tur, tur)
            
    def load_giderler(self):
        """Giderleri yükle"""
        baslangic = self.baslangic_date.date().toString("yyyy-MM-dd")
        bitis = self.bitis_date.date().toString("yyyy-MM-dd")
        tur = self.tur_filter.currentData()
        kasa_id = self.kasa_filter.currentData()
        
        giderler = self.gider_yoneticisi.gider_listesi(
            baslangic_tarih=baslangic,
            bitis_tarih=bitis,
            gider_turu=tur,
            kasa_id=kasa_id
        )
        
        self.table.setRowCount(0)
        toplam = 0.0
        
        for gider in giderler:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(gider['gider_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(gider['tarih']))
            self.table.setItem(row, 2, QTableWidgetItem(gider['islem_no']))
            self.table.setItem(row, 3, QTableWidgetItem(gider['gider_turu']))
            self.table.setItem(row, 4, QTableWidgetItem(gider['aciklama']))
            
            tutar_item = QTableWidgetItem(f"{gider['tutar']:.2f} ₺")
            tutar_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 5, tutar_item)
            
            self.table.setItem(row, 6, QTableWidgetItem(gider['kasa_adi']))
            self.table.setItem(row, 7, QTableWidgetItem(gider.get('odeyen', '-')))
            self.table.setItem(row, 8, QTableWidgetItem(gider.get('notlar', '-')))
            
            toplam += gider['tutar']
        
        self.toplam_label.setText(f"Toplam Gider: {toplam:,.2f} ₺")
        
    def on_selection_changed(self):
        selected = self.table.selectionModel().hasSelection()
        self.duzenle_btn.setEnabled(selected)
        self.sil_btn.setEnabled(selected)
    
    def gider_ekle(self):
        """Yeni gider ekle"""
        form_widget = GiderFormWidget(self.db)
        drawer = DrawerPanel(self, "Yeni Gider Ekle", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama alanı boş bırakılamaz!", self).show()
                return
            
            # Bakiye kontrolü
            from models import KasaYoneticisi
            kasa_yoneticisi = KasaYoneticisi(self.db)
            bakiye_bilgi = kasa_yoneticisi.kasa_bakiye_hesapla(data['kasa_id'])
            
            if bakiye_bilgi and bakiye_bilgi.get('net_bakiye', 0) < data['tutar']:
                MessageBox(
                    "Yetersiz Bakiye", 
                    f"Kasada yeterli bakiye yok!\n\n"
                    f"Mevcut Bakiye: {bakiye_bilgi['net_bakiye']:,.2f} ₺\n"
                    f"Gider Tutarı: {data['tutar']:,.2f} ₺", 
                    self
                ).show()
                return
                
            try:
                self.gider_yoneticisi.gider_ekle(**data)
                self.load_giderler()
                MessageBox("Başarılı", "Gider kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Gider eklenirken hata:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
                
    def gider_duzenle(self):
        """Gider düzenle"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        gider_id = int(self.table.item(row, 0).text())
        
        self.db.cursor.execute("SELECT * FROM giderler WHERE gider_id = ?", (gider_id,))
        gider_data = dict(self.db.cursor.fetchone())
        
        form_widget = GiderFormWidget(self.db, gider_data)
        drawer = DrawerPanel(self, "Gider Düzenle", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama alanı boş bırakılamaz!", self).show()
                return
                
            try:
                self.gider_yoneticisi.gider_guncelle(gider_id, **data)
                self.load_giderler()
                MessageBox("Başarılı", "Gider güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Güncelleme hatası:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
                
    def gider_sil(self):
        """Gider sil"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        gider_id = int(self.table.item(row, 0).text())
        tutar = self.table.item(row, 5).text()
        
        w = MessageBox("Gider Sil", f"{tutar} tutarındaki gideri silmek istediğinize emin misiniz?", self)
        if w.exec():
            try:
                self.gider_yoneticisi.gider_sil(gider_id)
                self.load_giderler()
                MessageBox("Başarılı", "Gider silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Silme hatası:\n{e}", self).show()

