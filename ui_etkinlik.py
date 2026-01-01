"""
BADER Derneği - Etkinlik Yönetimi Modülü
Düğün, kına, toplantı, davet takibi
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QHeaderView, QComboBox, QDateEdit,
                             QFrame, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from qfluentwidgets import MessageBox
from database import Database
from models import EtkinlikYoneticisi, UyeYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import (create_line_edit, create_text_edit, create_combo_box,
                            create_double_spin_box, create_date_edit, create_spin_box)
from ui_helpers import export_table_to_excel, setup_resizable_table
from datetime import datetime


class EtkinlikFormWidget(QWidget):
    """Etkinlik formu"""
    
    SECTION_STYLE = """
        QLabel {
            color: #64B5F6;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 8px 0 5px 0;
            border-bottom: 2px solid #64B5F6;
            margin-top: 10px;
        }
    """
    
    def __init__(self, db: Database, etkinlik_data: dict = None):
        super().__init__()
        self.db = db
        self.etkinlik_data = etkinlik_data
        self.uye_yoneticisi = UyeYoneticisi(db)
        self.setup_ui()
        
        if etkinlik_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # TEMEL BİLGİLER
        section1 = QLabel("TEMEL BİLGİLER")
        section1.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section1)
        
        # Etkinlik Türü
        self.tur_combo = create_combo_box("Etkinlik Türü *", searchable=False)
        self.tur_combo[1].addItems([
            "DÜĞÜN", "NİŞAN", "KINA", "SÜNNET", "CENAZE", "MEVLİT",
            "TOPLANTI", "GENEL KURUL", "DAVET", "PİKNİK", "GEZİ", "DİĞER"
        ])
        layout.addWidget(self.tur_combo[0])
        
        # Başlık
        self.baslik_edit = create_line_edit("Başlık *", "Etkinlik başlığı")
        layout.addWidget(self.baslik_edit[0])
        
        # Açıklama
        self.aciklama_edit = create_text_edit("Açıklama", "Etkinlik hakkında detaylar...", max_height=60)
        layout.addWidget(self.aciklama_edit[0])
        
        # TARİH VE KONUM
        section2 = QLabel("TARİH VE KONUM")
        section2.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section2)
        
        # Tarih
        self.tarih_edit = create_date_edit("Tarih *")
        self.tarih_edit[1].setDate(QDate.currentDate())
        layout.addWidget(self.tarih_edit[0])
        
        # Saat
        self.saat_edit = create_line_edit("Saat", "14:00")
        layout.addWidget(self.saat_edit[0])
        
        # Bitiş Tarihi
        self.bitis_edit = create_date_edit("Bitiş Tarihi")
        layout.addWidget(self.bitis_edit[0])
        
        # Mekan
        self.mekan_edit = create_line_edit("Mekan", "Dernek salonu, otel adı vb.")
        layout.addWidget(self.mekan_edit[0])
        
        # Durum
        self.durum_combo = create_combo_box("Durum", searchable=False)
        self.durum_combo[1].addItems(["Planlandı", "Devam Ediyor", "Tamamlandı", "İptal"])
        layout.addWidget(self.durum_combo[0])
        
        # FİNANSAL
        section3 = QLabel("FİNANSAL TAHMİNLER")
        section3.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section3)
        
        # Tahmini Gelir
        self.tahmini_gelir_spin = create_double_spin_box("Tahmini Gelir")
        self.tahmini_gelir_spin[1].setMaximum(10000000)
        self.tahmini_gelir_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tahmini_gelir_spin[0])
        
        # Tahmini Gider
        self.tahmini_gider_spin = create_double_spin_box("Tahmini Gider")
        self.tahmini_gider_spin[1].setMaximum(10000000)
        self.tahmini_gider_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tahmini_gider_spin[0])
        
        # Gerçekleşen Gelir
        self.gerceklesen_gelir_spin = create_double_spin_box("Gerçekleşen Gelir")
        self.gerceklesen_gelir_spin[1].setMaximum(10000000)
        self.gerceklesen_gelir_spin[1].setSuffix(" ₺")
        layout.addWidget(self.gerceklesen_gelir_spin[0])
        
        # Gerçekleşen Gider
        self.gerceklesen_gider_spin = create_double_spin_box("Gerçekleşen Gider")
        self.gerceklesen_gider_spin[1].setMaximum(10000000)
        self.gerceklesen_gider_spin[1].setSuffix(" ₺")
        layout.addWidget(self.gerceklesen_gider_spin[0])
        
        # DİĞER
        section4 = QLabel("DİĞER")
        section4.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section4)
        
        # Sorumlu Üye
        self.sorumlu_combo = create_combo_box("Sorumlu Üye", searchable=True)
        self.sorumlu_combo[1].addItem("Seçiniz...", None)
        uyeler = self.uye_yoneticisi.uye_listesi()
        for u in uyeler:
            self.sorumlu_combo[1].addItem(u['ad_soyad'], u['uye_id'])
        layout.addWidget(self.sorumlu_combo[0])
        
        # Notlar
        self.notlar_edit = create_text_edit("Notlar", "Ek notlar...", max_height=50)
        layout.addWidget(self.notlar_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_data(self):
        """Mevcut etkinlik verilerini yükle"""
        if not self.etkinlik_data:
            return
        
        idx = self.tur_combo[1].findText(self.etkinlik_data.get('etkinlik_turu', ''))
        if idx >= 0:
            self.tur_combo[1].setCurrentIndex(idx)
        
        self.baslik_edit[1].setText(self.etkinlik_data.get('baslik', ''))
        self.aciklama_edit[1].setPlainText(self.etkinlik_data.get('aciklama', '') or '')
        
        tarih = self.etkinlik_data.get('tarih')
        if tarih:
            self.tarih_edit[1].setDate(QDate.fromString(tarih, "yyyy-MM-dd"))
        
        self.saat_edit[1].setText(self.etkinlik_data.get('saat', '') or '')
        
        bitis = self.etkinlik_data.get('bitis_tarihi')
        if bitis:
            self.bitis_edit[1].setDate(QDate.fromString(bitis, "yyyy-MM-dd"))
        
        self.mekan_edit[1].setText(self.etkinlik_data.get('mekan', '') or '')
        
        idx = self.durum_combo[1].findText(self.etkinlik_data.get('durum', 'Planlandı'))
        if idx >= 0:
            self.durum_combo[1].setCurrentIndex(idx)
        
        self.tahmini_gelir_spin[1].setValue(self.etkinlik_data.get('tahmini_gelir', 0) or 0)
        self.tahmini_gider_spin[1].setValue(self.etkinlik_data.get('tahmini_gider', 0) or 0)
        self.gerceklesen_gelir_spin[1].setValue(self.etkinlik_data.get('gerceklesen_gelir', 0) or 0)
        self.gerceklesen_gider_spin[1].setValue(self.etkinlik_data.get('gerceklesen_gider', 0) or 0)
        
        sorumlu_id = self.etkinlik_data.get('sorumlu_uye_id')
        if sorumlu_id:
            for i in range(self.sorumlu_combo[1].count()):
                if self.sorumlu_combo[1].itemData(i) == sorumlu_id:
                    self.sorumlu_combo[1].setCurrentIndex(i)
                    break
        
        self.notlar_edit[1].setPlainText(self.etkinlik_data.get('notlar', '') or '')
        
    def get_data(self) -> dict:
        """Form verilerini al"""
        bitis = self.bitis_edit[1].date().toString("yyyy-MM-dd")
        if bitis == "2000-01-01":
            bitis = None
            
        return {
            'etkinlik_turu': self.tur_combo[1].currentText(),
            'baslik': self.baslik_edit[1].text().strip(),
            'aciklama': self.aciklama_edit[1].toPlainText().strip(),
            'tarih': self.tarih_edit[1].date().toString("yyyy-MM-dd"),
            'saat': self.saat_edit[1].text().strip(),
            'bitis_tarihi': bitis,
            'mekan': self.mekan_edit[1].text().strip(),
            'durum': self.durum_combo[1].currentText(),
            'tahmini_gelir': self.tahmini_gelir_spin[1].value(),
            'tahmini_gider': self.tahmini_gider_spin[1].value(),
            'gerceklesen_gelir': self.gerceklesen_gelir_spin[1].value(),
            'gerceklesen_gider': self.gerceklesen_gider_spin[1].value(),
            'sorumlu_uye_id': self.sorumlu_combo[1].currentData(),
            'notlar': self.notlar_edit[1].toPlainText().strip()
        }
    
    def validate(self) -> bool:
        if not self.baslik_edit[1].text().strip():
            MessageBox("Uyarı", "Başlık boş bırakılamaz!", self).show()
            return False
        return True


class EtkinlikWidget(QWidget):
    """Etkinlik yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.etkinlik_yoneticisi = EtkinlikYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("ETKİNLİK YÖNETİMİ")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Arama
        self.arama_edit = QLineEdit()
        self.arama_edit.setPlaceholderText("🔍 Etkinlik ara...")
        self.arama_edit.textChanged.connect(self.ara)
        self.arama_edit.setMaximumWidth(250)
        toolbar.addWidget(self.arama_edit)
        
        # Tür filtresi
        toolbar.addWidget(QLabel("Tür:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü", None)
        self.tur_filter.addItems([
            "DÜĞÜN", "NİŞAN", "KINA", "SÜNNET", "CENAZE", "MEVLİT",
            "TOPLANTI", "GENEL KURUL", "DAVET", "PİKNİK", "GEZİ", "DİĞER"
        ])
        self.tur_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.tur_filter)
        
        # Durum filtresi
        toolbar.addWidget(QLabel("Durum:"))
        self.durum_filter = QComboBox()
        self.durum_filter.addItems(["Tümü", "Planlandı", "Devam Ediyor", "Tamamlandı", "İptal"])
        self.durum_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.durum_filter)
        
        toolbar.addStretch()
        
        # Butonlar
        self.ekle_btn = QPushButton("➕ Yeni Etkinlik")
        self.ekle_btn.clicked.connect(self.etkinlik_ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.etkinlik_duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.etkinlik_sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "etkinlikler", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tür", "Başlık", "Tarih", "Saat", "Mekan", "Durum", "Katılımcı", "Sorumlu"
        ])
        setup_resizable_table(self.table, table_id="etkinlikler_tablosu", stretch_column=2)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.etkinlik_duzenle)
        
        layout.addWidget(self.table)
        
        # İstatistik
        self.stats_label = QLabel("Toplam: 0 etkinlik")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        
    def load_data(self):
        """Etkinlikleri yükle"""
        tur = self.tur_filter.currentText() if self.tur_filter.currentIndex() > 0 else None
        durum = self.durum_filter.currentText() if self.durum_filter.currentIndex() > 0 else None
        
        etkinlikler = self.etkinlik_yoneticisi.etkinlik_listesi(
            etkinlik_turu=tur,
            durum=durum
        )
        
        self.table.setRowCount(len(etkinlikler))
        
        for row, e in enumerate(etkinlikler):
            self.table.setItem(row, 0, QTableWidgetItem(str(e['etkinlik_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(e['etkinlik_turu']))
            self.table.setItem(row, 2, QTableWidgetItem(e['baslik']))
            self.table.setItem(row, 3, QTableWidgetItem(e['tarih']))
            self.table.setItem(row, 4, QTableWidgetItem(e.get('saat', '') or '-'))
            self.table.setItem(row, 5, QTableWidgetItem(e.get('mekan', '') or '-'))
            
            # Durum renklendirme
            durum_item = QTableWidgetItem(e['durum'])
            if e['durum'] == 'Tamamlandı':
                durum_item.setForeground(Qt.GlobalColor.darkGreen)
            elif e['durum'] == 'İptal':
                durum_item.setForeground(Qt.GlobalColor.darkRed)
            elif e['durum'] == 'Devam Ediyor':
                durum_item.setForeground(Qt.GlobalColor.darkBlue)
            self.table.setItem(row, 6, durum_item)
            
            self.table.setItem(row, 7, QTableWidgetItem(str(e.get('katilimci_sayisi', 0))))
            self.table.setItem(row, 8, QTableWidgetItem(e.get('sorumlu_adi', '-') or '-'))
        
        self.stats_label.setText(f"Toplam: {len(etkinlikler)} etkinlik")
        
    def ara(self):
        """Ara"""
        text = self.arama_edit.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in [1, 2, 5, 8]
            )
            self.table.setRowHidden(row, not match)
            
    def on_selection(self):
        """Seçim değiştiğinde"""
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
            self.sil_btn.setEnabled(True)
        else:
            self.current_id = None
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
    
    def etkinlik_ekle(self):
        """Yeni etkinlik ekle"""
        form = EtkinlikFormWidget(self.db)
        drawer = DrawerPanel(self, "Yeni Etkinlik", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.etkinlik_yoneticisi.etkinlik_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Etkinlik eklendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def etkinlik_duzenle(self):
        """Etkinlik düzenle"""
        if not self.current_id:
            return
        
        etkinlik = self.etkinlik_yoneticisi.etkinlik_getir(self.current_id)
        if not etkinlik:
            return
        
        form = EtkinlikFormWidget(self.db, etkinlik)
        drawer = DrawerPanel(self, "Etkinlik Düzenle", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.etkinlik_yoneticisi.etkinlik_guncelle(self.current_id, **data)
                self.load_data()
                MessageBox("Başarılı", "Etkinlik güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def etkinlik_sil(self):
        """Etkinlik sil"""
        if not self.current_id:
            return
        
        w = MessageBox("Etkinlik Sil", "Bu etkinliği silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.etkinlik_yoneticisi.etkinlik_sil(self.current_id)
                self.load_data()
                self.current_id = None
                MessageBox("Başarılı", "Etkinlik silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()


