"""
BADER Derneği - Köy İşlemleri Modülü
Köy Gelir, Gider, Kasa ve Virman sayfaları
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QHeaderView, QComboBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from qfluentwidgets import MessageBox
from database import Database
from models import (KoyKasaYoneticisi, KoyGelirYoneticisi, 
                    KoyGiderYoneticisi, KoyVirmanYoneticisi)
from ui_drawer import DrawerPanel
from ui_form_fields import (create_line_edit, create_text_edit, create_combo_box,
                            create_double_spin_box, create_date_edit)
from ui_helpers import export_table_to_excel
from datetime import datetime


# ========================================
# KÖY GELİR YÖNETİMİ
# ========================================

class KoyGelirWidget(QWidget):
    """Köy gelir yönetimi"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.gelir_yoneticisi = KoyGelirYoneticisi(db)
        self.kasa_yoneticisi = KoyKasaYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("KÖY GELİRLERİ")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.arama = QLineEdit()
        self.arama.setPlaceholderText("🔍 Ara...")
        self.arama.textChanged.connect(self.ara)
        self.arama.setMaximumWidth(250)
        toolbar.addWidget(self.arama)
        
        # Filtreler
        toolbar.addWidget(QLabel("Tür:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü")
        self.tur_filter.addItems(self.gelir_yoneticisi.gelir_turleri_listesi())
        self.tur_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.tur_filter)
        
        toolbar.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Gelir")
        self.ekle_btn.clicked.connect(self.ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        # Excel export
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "koy_gelirler", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Gelir Türü", "Açıklama", "Tutar", "Kasa", "Dekont No", "Belge No"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.duzenle)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def load_data(self):
        tur = self.tur_filter.currentText() if self.tur_filter.currentIndex() > 0 else None
        data = self.gelir_yoneticisi.gelir_listesi(gelir_turu=tur)
        
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item['gelir_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(item['tarih']))
            self.table.setItem(row, 2, QTableWidgetItem(item['gelir_turu']))
            self.table.setItem(row, 3, QTableWidgetItem(item['aciklama'] or '-'))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['tutar']:,.2f} ₺"))
            self.table.setItem(row, 5, QTableWidgetItem(item['kasa_adi']))
            self.table.setItem(row, 6, QTableWidgetItem(item.get('dekont_no') or '-'))
            self.table.setItem(row, 7, QTableWidgetItem(item.get('belge_no') or '-'))
    
    def ara(self):
        text = self.arama.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(2, 6)
            )
            self.table.setRowHidden(row, not match)
            
    def on_selection(self):
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
            self.sil_btn.setEnabled(True)
        else:
            self.current_id = None
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
    
    def ekle(self):
        form = self._create_form()
        drawer = DrawerPanel(self, "Yeni Köy Geliri", form)
        
        def on_submit():
            data = self._get_form_data(form)
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama boş bırakılamaz!", self).show()
                return
            try:
                self.gelir_yoneticisi.gelir_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Gelir kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def duzenle(self):
        if not self.current_id:
            return
        
        self.db.cursor.execute("SELECT * FROM koy_gelirleri WHERE gelir_id = ?", (self.current_id,))
        existing = dict(self.db.cursor.fetchone())
        
        form = self._create_form(existing)
        drawer = DrawerPanel(self, "Köy Geliri Düzenle", form)
        
        def on_submit():
            data = self._get_form_data(form)
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama boş bırakılamaz!", self).show()
                return
            try:
                self.gelir_yoneticisi.gelir_guncelle(self.current_id, **data)
                self.load_data()
                MessageBox("Başarılı", "Gelir güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def sil(self):
        if not self.current_id:
            return
        w = MessageBox("Sil", "Bu geliri silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.gelir_yoneticisi.gelir_sil(self.current_id)
                self.load_data()
                MessageBox("Başarılı", "Gelir silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
    
    def _create_form(self, data=None):
        form = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        form.tarih = create_date_edit("Tarih")
        if data:
            form.tarih[1].setDate(QDate.fromString(data['tarih'], "yyyy-MM-dd"))
        layout.addWidget(form.tarih[0])
        
        form.tur = create_combo_box("Gelir Türü")
        form.tur[1].addItems(self.gelir_yoneticisi.gelir_turleri_listesi())
        if data:
            form.tur[1].setCurrentText(data['gelir_turu'])
        layout.addWidget(form.tur[0])
        
        form.aciklama = create_line_edit("Açıklama *", "Gelir açıklaması...")
        if data:
            form.aciklama[1].setText(data.get('aciklama', ''))
        layout.addWidget(form.aciklama[0])
        
        form.tutar = create_double_spin_box("Tutar *")
        form.tutar[1].setMaximum(10000000)
        form.tutar[1].setSuffix(" ₺")
        if data:
            form.tutar[1].setValue(data['tutar'])
        layout.addWidget(form.tutar[0])
        
        form.kasa = create_combo_box("Kasa")
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for k in kasalar:
            form.kasa[1].addItem(f"{k['kasa_adi']} ({k['para_birimi']})", k['kasa_id'])
        if data:
            for i in range(form.kasa[1].count()):
                if form.kasa[1].itemData(i) == data['kasa_id']:
                    form.kasa[1].setCurrentIndex(i)
                    break
        layout.addWidget(form.kasa[0])
        
        form.dekont = create_line_edit("Dekont No", "")
        if data:
            form.dekont[1].setText(data.get('dekont_no', '') or '')
        layout.addWidget(form.dekont[0])
        
        form.tahsil_eden = create_line_edit("Tahsil Eden", "")
        if data:
            form.tahsil_eden[1].setText(data.get('tahsil_eden', '') or '')
        layout.addWidget(form.tahsil_eden[0])
        
        layout.addStretch()
        form.setLayout(layout)
        return form
    
    def _get_form_data(self, form):
        return {
            'tarih': form.tarih[1].date().toString("yyyy-MM-dd"),
            'gelir_turu': form.tur[1].currentText(),
            'aciklama': form.aciklama[1].text().strip(),
            'tutar': form.tutar[1].value(),
            'kasa_id': form.kasa[1].currentData(),
            'dekont_no': form.dekont[1].text().strip(),
            'tahsil_eden': form.tahsil_eden[1].text().strip()
        }


# ========================================
# KÖY GİDER YÖNETİMİ
# ========================================

class KoyGiderWidget(QWidget):
    """Köy gider yönetimi"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.gider_yoneticisi = KoyGiderYoneticisi(db)
        self.kasa_yoneticisi = KoyKasaYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        title = QLabel("KÖY GİDERLERİ")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        toolbar = QHBoxLayout()
        
        self.arama = QLineEdit()
        self.arama.setPlaceholderText("🔍 Ara...")
        self.arama.textChanged.connect(self.ara)
        self.arama.setMaximumWidth(250)
        toolbar.addWidget(self.arama)
        
        toolbar.addWidget(QLabel("Tür:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü")
        self.tur_filter.addItems(self.gider_yoneticisi.gider_turleri_listesi())
        self.tur_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.tur_filter)
        
        toolbar.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Gider")
        self.ekle_btn.clicked.connect(self.ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        # Excel export
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "koy_giderler", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Gider Türü", "Açıklama", "Tutar", "Kasa", "Dekont No", "İşlem No"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.duzenle)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def load_data(self):
        tur = self.tur_filter.currentText() if self.tur_filter.currentIndex() > 0 else None
        data = self.gider_yoneticisi.gider_listesi(gider_turu=tur)
        
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item['gider_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(item['tarih']))
            self.table.setItem(row, 2, QTableWidgetItem(item['gider_turu']))
            self.table.setItem(row, 3, QTableWidgetItem(item['aciklama'] or '-'))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['tutar']:,.2f} ₺"))
            self.table.setItem(row, 5, QTableWidgetItem(item['kasa_adi']))
            self.table.setItem(row, 6, QTableWidgetItem(item.get('dekont_no') or '-'))
            self.table.setItem(row, 7, QTableWidgetItem(item.get('islem_no') or '-'))
    
    def ara(self):
        text = self.arama.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(2, 6)
            )
            self.table.setRowHidden(row, not match)
            
    def on_selection(self):
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
            self.sil_btn.setEnabled(True)
        else:
            self.current_id = None
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
    
    def ekle(self):
        form = self._create_form()
        drawer = DrawerPanel(self, "Yeni Köy Gideri", form)
        
        def on_submit():
            data = self._get_form_data(form)
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama boş bırakılamaz!", self).show()
                return
            try:
                self.gider_yoneticisi.gider_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Gider kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def duzenle(self):
        if not self.current_id:
            return
        
        self.db.cursor.execute("SELECT * FROM koy_giderleri WHERE gider_id = ?", (self.current_id,))
        existing = dict(self.db.cursor.fetchone())
        
        form = self._create_form(existing)
        drawer = DrawerPanel(self, "Köy Gideri Düzenle", form)
        
        def on_submit():
            data = self._get_form_data(form)
            if not data['aciklama']:
                MessageBox("Uyarı", "Açıklama boş bırakılamaz!", self).show()
                return
            try:
                self.gider_yoneticisi.gider_guncelle(self.current_id, **data)
                self.load_data()
                MessageBox("Başarılı", "Gider güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def sil(self):
        if not self.current_id:
            return
        w = MessageBox("Sil", "Bu gideri silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.gider_yoneticisi.gider_sil(self.current_id)
                self.load_data()
                MessageBox("Başarılı", "Gider silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
    
    def _create_form(self, data=None):
        form = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        form.tarih = create_date_edit("Tarih")
        if data:
            form.tarih[1].setDate(QDate.fromString(data['tarih'], "yyyy-MM-dd"))
        layout.addWidget(form.tarih[0])
        
        form.tur = create_combo_box("Gider Türü")
        form.tur[1].addItems(self.gider_yoneticisi.gider_turleri_listesi())
        if data:
            form.tur[1].setCurrentText(data['gider_turu'])
        layout.addWidget(form.tur[0])
        
        form.aciklama = create_line_edit("Açıklama *", "Gider açıklaması...")
        if data:
            form.aciklama[1].setText(data.get('aciklama', ''))
        layout.addWidget(form.aciklama[0])
        
        form.tutar = create_double_spin_box("Tutar *")
        form.tutar[1].setMaximum(10000000)
        form.tutar[1].setSuffix(" ₺")
        if data:
            form.tutar[1].setValue(data['tutar'])
        layout.addWidget(form.tutar[0])
        
        form.kasa = create_combo_box("Kasa")
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for k in kasalar:
            form.kasa[1].addItem(f"{k['kasa_adi']} ({k['para_birimi']})", k['kasa_id'])
        if data:
            for i in range(form.kasa[1].count()):
                if form.kasa[1].itemData(i) == data['kasa_id']:
                    form.kasa[1].setCurrentIndex(i)
                    break
        layout.addWidget(form.kasa[0])
        
        form.dekont = create_line_edit("Dekont No", "")
        if data:
            form.dekont[1].setText(data.get('dekont_no', '') or '')
        layout.addWidget(form.dekont[0])
        
        form.odeyen = create_line_edit("Ödeyen", "")
        if data:
            form.odeyen[1].setText(data.get('odeyen', '') or '')
        layout.addWidget(form.odeyen[0])
        
        layout.addStretch()
        form.setLayout(layout)
        return form
    
    def _get_form_data(self, form):
        return {
            'tarih': form.tarih[1].date().toString("yyyy-MM-dd"),
            'gider_turu': form.tur[1].currentText(),
            'aciklama': form.aciklama[1].text().strip(),
            'tutar': form.tutar[1].value(),
            'kasa_id': form.kasa[1].currentData(),
            'dekont_no': form.dekont[1].text().strip(),
            'odeyen': form.odeyen[1].text().strip()
        }


# ========================================
# KÖY KASA YÖNETİMİ
# ========================================

class KoyKasaWidget(QWidget):
    """Köy kasa yönetimi"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.kasa_yoneticisi = KoyKasaYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        title = QLabel("KÖY KASALARI")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        toolbar = QHBoxLayout()
        toolbar.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Kasa")
        self.ekle_btn.clicked.connect(self.ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        # Excel export
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "koy_kasalar", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kasa Adı", "Para Birimi", "Devir Bakiye", "Toplam Gelir", "Toplam Gider", "Net Bakiye"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.duzenle)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def load_data(self):
        data = self.kasa_yoneticisi.tum_kasalar_ozet()
        
        self.table.setRowCount(len(data))
        for row, kasa in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(kasa['kasa_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(kasa['kasa_adi']))
            self.table.setItem(row, 2, QTableWidgetItem(kasa['para_birimi']))
            self.table.setItem(row, 3, QTableWidgetItem(f"{kasa['devir_bakiye']:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{kasa['toplam_gelir']:,.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{kasa['toplam_gider']:,.2f}"))
            
            net_item = QTableWidgetItem(f"{kasa['net_bakiye']:,.2f}")
            if kasa['net_bakiye'] >= 0:
                net_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                net_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 6, net_item)
    
    def on_selection(self):
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
        else:
            self.current_id = None
            self.duzenle_btn.setEnabled(False)
    
    def ekle(self):
        form = self._create_form()
        drawer = DrawerPanel(self, "Yeni Köy Kasası", form)
        
        def on_submit():
            data = self._get_form_data(form)
            if not data['kasa_adi']:
                MessageBox("Uyarı", "Kasa adı boş bırakılamaz!", self).show()
                return
            try:
                self.kasa_yoneticisi.kasa_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Kasa eklendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def duzenle(self):
        if not self.current_id:
            return
        
        self.db.cursor.execute("SELECT * FROM koy_kasalar WHERE kasa_id = ?", (self.current_id,))
        existing = dict(self.db.cursor.fetchone())
        
        form = self._create_form(existing)
        drawer = DrawerPanel(self, "Köy Kasası Düzenle", form)
        
        def on_submit():
            data = self._get_form_data(form)
            if not data['kasa_adi']:
                MessageBox("Uyarı", "Kasa adı boş bırakılamaz!", self).show()
                return
            try:
                self.kasa_yoneticisi.kasa_guncelle(self.current_id, **data)
                self.load_data()
                MessageBox("Başarılı", "Kasa güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def _create_form(self, data=None):
        form = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        form.kasa_adi = create_line_edit("Kasa Adı *", "Kasa adı...")
        if data:
            form.kasa_adi[1].setText(data['kasa_adi'])
        layout.addWidget(form.kasa_adi[0])
        
        form.para_birimi = create_combo_box("Para Birimi")
        form.para_birimi[1].addItems(["TL", "USD", "EUR"])
        if data:
            form.para_birimi[1].setCurrentText(data['para_birimi'])
        layout.addWidget(form.para_birimi[0])
        
        form.devir = create_double_spin_box("Devir Bakiye")
        form.devir[1].setMaximum(100000000)
        form.devir[1].setMinimum(-100000000)
        if data:
            form.devir[1].setValue(data['devir_bakiye'])
        layout.addWidget(form.devir[0])
        
        form.aciklama = create_text_edit("Açıklama", "", 80)
        if data:
            form.aciklama[1].setPlainText(data.get('aciklama', '') or '')
        layout.addWidget(form.aciklama[0])
        
        layout.addStretch()
        form.setLayout(layout)
        return form
    
    def _get_form_data(self, form):
        return {
            'kasa_adi': form.kasa_adi[1].text().strip(),
            'para_birimi': form.para_birimi[1].currentText(),
            'devir_bakiye': form.devir[1].value(),
            'aciklama': form.aciklama[1].toPlainText().strip()
        }


# ========================================
# KÖY VİRMAN YÖNETİMİ
# ========================================

class KoyVirmanWidget(QWidget):
    """Köy virman yönetimi"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.virman_yoneticisi = KoyVirmanYoneticisi(db)
        self.kasa_yoneticisi = KoyKasaYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        title = QLabel("KÖY VİRMANLARI")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        toolbar = QHBoxLayout()
        toolbar.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Virman")
        self.ekle_btn.clicked.connect(self.ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        # Excel export
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "koy_virmanlar", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Gönderen Kasa", "Alan Kasa", "Tutar", "Açıklama"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def load_data(self):
        data = self.virman_yoneticisi.virman_listesi()
        
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item['virman_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(item['tarih']))
            self.table.setItem(row, 2, QTableWidgetItem(item['gonderen_kasa_adi']))
            self.table.setItem(row, 3, QTableWidgetItem(item['alan_kasa_adi']))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['tutar']:,.2f} ₺"))
            self.table.setItem(row, 5, QTableWidgetItem(item.get('aciklama') or '-'))
    
    def on_selection(self):
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.sil_btn.setEnabled(True)
        else:
            self.current_id = None
            self.sil_btn.setEnabled(False)
    
    def ekle(self):
        form = self._create_form()
        drawer = DrawerPanel(self, "Yeni Köy Virmanı", form)
        
        def on_submit():
            data = self._get_form_data(form)
            if data['gonderen_kasa_id'] == data['alan_kasa_id']:
                MessageBox("Uyarı", "Gönderen ve alan kasa aynı olamaz!", self).show()
                return
            try:
                self.virman_yoneticisi.virman_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Virman kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def sil(self):
        if not self.current_id:
            return
        w = MessageBox("Sil", "Bu virmanı silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.virman_yoneticisi.virman_sil(self.current_id)
                self.load_data()
                MessageBox("Başarılı", "Virman silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
    
    def _create_form(self):
        form = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        form.tarih = create_date_edit("Tarih")
        layout.addWidget(form.tarih[0])
        
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        
        form.gonderen = create_combo_box("Gönderen Kasa")
        for k in kasalar:
            form.gonderen[1].addItem(f"{k['kasa_adi']} ({k['para_birimi']})", k['kasa_id'])
        layout.addWidget(form.gonderen[0])
        
        form.alan = create_combo_box("Alan Kasa")
        for k in kasalar:
            form.alan[1].addItem(f"{k['kasa_adi']} ({k['para_birimi']})", k['kasa_id'])
        layout.addWidget(form.alan[0])
        
        form.tutar = create_double_spin_box("Tutar *")
        form.tutar[1].setMaximum(10000000)
        form.tutar[1].setSuffix(" ₺")
        layout.addWidget(form.tutar[0])
        
        form.aciklama = create_line_edit("Açıklama", "")
        layout.addWidget(form.aciklama[0])
        
        layout.addStretch()
        form.setLayout(layout)
        return form
    
    def _get_form_data(self, form):
        return {
            'tarih': form.tarih[1].date().toString("yyyy-MM-dd"),
            'gonderen_kasa_id': form.gonderen[1].currentData(),
            'alan_kasa_id': form.alan[1].currentData(),
            'tutar': form.tutar[1].value(),
            'aciklama': form.aciklama[1].text().strip()
        }

