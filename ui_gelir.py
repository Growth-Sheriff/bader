"""
BADER Derneği - Gelir Yönetimi UI (DRAWER PANEL)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QHeaderView, QComboBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from qfluentwidgets import MessageBox
from datetime import datetime
from database import Database
from models import GelirYoneticisi, KasaYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import (FormField, create_line_edit, create_text_edit, 
                            create_combo_box, create_double_spin_box, create_date_edit)
from ui_helpers import export_table_to_excel
from ui_login import session


class GelirFormWidget(QWidget):
    """Gelir formu - Drawer içinde"""
    
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
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Tarih
        self.tarih_edit = create_date_edit("Tarih *")
        layout.addWidget(self.tarih_edit[0])
        
        # Gelir Türü
        self.gelir_turu_combo = create_combo_box("Gelir Türü *", searchable=True)
        self.gelir_turu_combo[1].addItems([
            "KİRA", "BAĞIŞ", "DÜĞÜN", "KINA", "TOPLANTI", "DAVET", "DİĞER"
        ])
        layout.addWidget(self.gelir_turu_combo[0])
        
        # Açıklama
        self.aciklama_edit = create_line_edit("Açıklama *", "Gelir açıklaması...")
        layout.addWidget(self.aciklama_edit[0])
        
        # Tutar
        self.tutar_spin = create_double_spin_box("Tutar *")
        self.tutar_spin[1].setMinimum(0.01)
        self.tutar_spin[1].setMaximum(10000000)
        self.tutar_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tutar_spin[0])
        
        # Kasa
        self.kasa_combo = create_combo_box("Kasa *", searchable=True)
        layout.addWidget(self.kasa_combo[0])
        
        # Tahsil Eden
        self.tahsil_eden_edit = create_line_edit("Tahsil Eden", "Tahsil eden kişi...")
        layout.addWidget(self.tahsil_eden_edit[0])
        
        # Dekont No
        self.dekont_edit = create_line_edit("Dekont No", "Dekont numarası...")
        layout.addWidget(self.dekont_edit[0])
        
        # Notlar
        self.notlar_edit = create_text_edit("Notlar", "Ek notlar...", 80)
        layout.addWidget(self.notlar_edit[0])
        
        # Uyarı
        warning = QLabel("ℹ️ AİDAT gelirler otomatik oluşturulur.")
        warning.setStyleSheet("color: #ff9f43; font-size: 12px; padding: 10px;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_kasalar(self):
        self.kasa_combo[1].clear()
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            self.kasa_combo[1].addItem(
                f"{kasa['kasa_adi']} ({kasa['para_birimi']})",
                kasa['kasa_id']
            )
            
    def load_data(self):
        if self.gelir_data:
            self.tarih_edit[1].setDate(QDate.fromString(self.gelir_data['tarih'], "yyyy-MM-dd"))
            self.gelir_turu_combo[1].setCurrentText(self.gelir_data['gelir_turu'])
            self.aciklama_edit[1].setText(self.gelir_data['aciklama'])
            self.tutar_spin[1].setValue(self.gelir_data['tutar'])
            
            for i in range(self.kasa_combo[1].count()):
                if self.kasa_combo[1].itemData(i) == self.gelir_data['kasa_id']:
                    self.kasa_combo[1].setCurrentIndex(i)
                    break
                    
            self.tahsil_eden_edit[1].setText(self.gelir_data.get('tahsil_eden', ''))
            self.dekont_edit[1].setText(self.gelir_data.get('dekont_no', ''))
            self.notlar_edit[1].setPlainText(self.gelir_data.get('notlar', ''))
            
    def get_data(self):
        return {
            'tarih': self.tarih_edit[1].date().toString("yyyy-MM-dd"),
            'gelir_turu': self.gelir_turu_combo[1].currentText(),
            'aciklama': self.aciklama_edit[1].text().strip(),
            'tutar': self.tutar_spin[1].value(),
            'kasa_id': self.kasa_combo[1].currentData(),
            'tahsil_eden': self.tahsil_eden_edit[1].text().strip(),
            'dekont_no': self.dekont_edit[1].text().strip(),
            'notlar': self.notlar_edit[1].toPlainText().strip()
        }
    
    def validate(self):
        if not self.aciklama_edit[1].text().strip():
            MessageBox("Uyarı", "Açıklama alanı zorunludur!", self).show()
            return False
        if self.tutar_spin[1].value() <= 0:
            MessageBox("Uyarı", "Tutar 0'dan büyük olmalıdır!", self).show()
            return False
        if not self.kasa_combo[1].currentData():
            MessageBox("Uyarı", "Kasa seçilmelidir!", self).show()
            return False
        return True


class GelirWidget(QWidget):
    """Gelir yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.gelir_yoneticisi = GelirYoneticisi(db)
        self.current_gelir_id = None
        
        self.setup_ui()
        self.load_gelirler()
        self.apply_permissions()
    
    def apply_permissions(self):
        """Kullanıcı izinlerine göre butonları ayarla"""
        self.ekle_btn.setVisible(session.has_permission('gelir_ekle'))
        self.duzenle_btn.setVisible(session.has_permission('gelir_duzenle'))
        self.sil_btn.setVisible(session.has_permission('gelir_sil'))
        self.export_btn.setVisible(session.has_permission('rapor_export'))
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.arama_edit = QLineEdit()
        self.arama_edit.setPlaceholderText("🔍 Gelir ara...")
        self.arama_edit.textChanged.connect(self.ara)
        self.arama_edit.setMaximumWidth(250)
        toolbar.addWidget(self.arama_edit)
        
        # Gelir türü filtresi
        toolbar.addWidget(QLabel("Tür:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü", None)
        self.tur_filter.addItems(["AİDAT", "KİRA", "BAĞIŞ", "DÜĞÜN", "KINA", "TOPLANTI", "DAVET", "DİĞER"])
        self.tur_filter.currentIndexChanged.connect(self.load_gelirler)
        self.tur_filter.setMinimumWidth(120)
        toolbar.addWidget(self.tur_filter)
        
        # Tarih filtreleri
        toolbar.addWidget(QLabel("Başlangıç:"))
        self.baslangic_tarih = QDateEdit()
        self.baslangic_tarih.setCalendarPopup(True)
        self.baslangic_tarih.setDate(QDate(datetime.now().year, 1, 1))
        self.baslangic_tarih.dateChanged.connect(self.load_gelirler)
        toolbar.addWidget(self.baslangic_tarih)
        
        toolbar.addWidget(QLabel("Bitiş:"))
        self.bitis_tarih = QDateEdit()
        self.bitis_tarih.setCalendarPopup(True)
        self.bitis_tarih.setDate(QDate.currentDate())
        self.bitis_tarih.dateChanged.connect(self.load_gelirler)
        toolbar.addWidget(self.bitis_tarih)
        
        # Filtreyi temizle butonu
        self.temizle_btn = QPushButton("🔄")
        self.temizle_btn.setToolTip("Filtreleri Temizle")
        self.temizle_btn.setMaximumWidth(40)
        self.temizle_btn.clicked.connect(self.filtreleri_temizle)
        toolbar.addWidget(self.temizle_btn)
        
        toolbar.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Gelir")
        self.ekle_btn.clicked.connect(self.gelir_ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.gelir_duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.gelir_sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        # Excel export
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.setToolTip("Listeyi Excel'e Aktar")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "gelirler", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Ait Yıl", "Gelir Türü", "Açıklama", "Tutar", "Kasa", "Dekont No", "Belge No"
        ])
        
        # Sütun genişliklerini otomatik ayarla
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Açıklama stretch
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Inline editing KAPALI
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.gelir_duzenle)  # Çift tıkla → Drawer aç
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
    def load_gelirler(self):
        # Filtreleri al
        gelir_turu = self.tur_filter.currentText() if self.tur_filter.currentIndex() > 0 else None
        baslangic = self.baslangic_tarih.date().toString("yyyy-MM-dd")
        bitis = self.bitis_tarih.date().toString("yyyy-MM-dd")
        
        gelirler = self.gelir_yoneticisi.gelir_listesi(
            baslangic_tarih=baslangic,
            bitis_tarih=bitis,
            gelir_turu=gelir_turu
        )
        self.table.setRowCount(len(gelirler))
        
        for row, gelir in enumerate(gelirler):
            self.table.setItem(row, 0, QTableWidgetItem(str(gelir['gelir_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(gelir['tarih']))
            
            # Ait olduğu yıl kolonu
            ait_yil = gelir.get('ait_oldugu_yil')
            if not ait_yil:
                # Tarihten yılı al
                ait_yil = gelir['tarih'][:4] if gelir.get('tarih') else '-'
            ait_yil_item = QTableWidgetItem(str(ait_yil))
            # Gelecek yıl ise mavi renk
            try:
                if int(ait_yil) > datetime.now().year:
                    ait_yil_item.setForeground(QColor("#2196F3"))
                    ait_yil_item.setText(f"{ait_yil} ⏩")
            except:
                pass
            self.table.setItem(row, 2, ait_yil_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(gelir['gelir_turu']))
            self.table.setItem(row, 4, QTableWidgetItem(gelir['aciklama']))
            self.table.setItem(row, 5, QTableWidgetItem(f"{gelir['tutar']:.2f} ₺"))
            self.table.setItem(row, 6, QTableWidgetItem(gelir['kasa_adi']))
            self.table.setItem(row, 7, QTableWidgetItem(gelir.get('dekont_no', '') or '-'))
            self.table.setItem(row, 8, QTableWidgetItem(gelir.get('belge_no', '')))
    
    def filtreleri_temizle(self):
        """Filtreleri temizle"""
        self.tur_filter.setCurrentIndex(0)
        self.baslangic_tarih.setDate(QDate(datetime.now().year, 1, 1))
        self.bitis_tarih.setDate(QDate.currentDate())
        self.arama_edit.clear()
        self.load_gelirler()
            
    def ara(self):
        text = self.arama_edit.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(2, 6)
            )
            self.table.setRowHidden(row, not match)
            
    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if selected:
            self.current_gelir_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
            self.sil_btn.setEnabled(True)
        else:
            self.current_gelir_id = None
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
    
    def gelir_ekle(self):
        """Yeni gelir ekle"""
        form_widget = GelirFormWidget(self, self.db)
        drawer = DrawerPanel(self, "Yeni Gelir Ekle", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama boş bırakılamaz!", self).show()
                return
            
            try:
                self.gelir_yoneticisi.gelir_ekle(**data)
                self.load_gelirler()
                MessageBox("Başarılı", "Gelir kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Gelir eklenirken hata:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def gelir_duzenle(self):
        """Gelir düzenle"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        gelir_id = int(self.table.item(row, 0).text())
        
        # Gelir verilerini al
        self.db.cursor.execute("SELECT * FROM gelirler WHERE gelir_id = ?", (gelir_id,))
        gelir_data = dict(self.db.cursor.fetchone())
        
        if gelir_data.get('gelir_turu') == 'AİDAT':
            MessageBox("Uyarı", "Aidat gelirler düzenlenemez!", self).show()
            return
        
        form_widget = GelirFormWidget(self, self.db, gelir_data)
        drawer = DrawerPanel(self, "Gelir Düzenle", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama boş bırakılamaz!", self).show()
                return
            
            try:
                self.gelir_yoneticisi.gelir_guncelle(gelir_id, **data)
                self.load_gelirler()
                MessageBox("Başarılı", "Gelir güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Güncelleme hatası:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
        
    def gelir_sil(self):
        """Gelir sil"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        gelir_id = int(self.table.item(row, 0).text())
        
        # Gelir türünü kontrol et
        self.db.cursor.execute("SELECT gelir_turu FROM gelirler WHERE gelir_id = ?", (gelir_id,))
        result = self.db.cursor.fetchone()
        
        if result and result['gelir_turu'] == 'AİDAT':
            MessageBox("Uyarı", "Aidat gelirler silinemez!", self).show()
            return
            
        w = MessageBox("Gelir Sil", "Bu geliri silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.gelir_yoneticisi.gelir_sil(gelir_id)
                self.load_gelirler()
                MessageBox("Başarılı", "Gelir silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Silme hatası:\n{e}", self).show()

