"""
BADER Derneği - Toplantı Yönetimi Modülü
Yönetim kurulu, genel kurul, komisyon toplantıları
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QHeaderView, QComboBox, QDateEdit,
                             QGroupBox, QTextEdit, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QDate
from qfluentwidgets import MessageBox
from database import Database
from models import ToplantiYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import (create_line_edit, create_text_edit, create_combo_box,
                            create_date_edit)
from ui_helpers import export_table_to_excel, setup_resizable_table
from datetime import datetime


class ToplantiFormWidget(QWidget):
    """Toplantı formu"""
    
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
    
    def __init__(self, toplanti_data: dict = None):
        super().__init__()
        self.toplanti_data = toplanti_data
        self.setup_ui()
        
        if toplanti_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # TEMEL BİLGİLER
        section1 = QLabel("TEMEL BİLGİLER")
        section1.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section1)
        
        # Toplantı Türü
        self.tur_combo = create_combo_box("Toplantı Türü *", searchable=False)
        self.tur_combo[1].addItems([
            "Yönetim Kurulu", "Genel Kurul", "Denetim Kurulu", "Komisyon", "Diğer"
        ])
        layout.addWidget(self.tur_combo[0])
        
        # Başlık
        self.baslik_edit = create_line_edit("Başlık *", "Toplantı başlığı")
        layout.addWidget(self.baslik_edit[0])
        
        # Tarih ve Saat
        self.tarih_edit = create_date_edit("Tarih *")
        self.tarih_edit[1].setDate(QDate.currentDate())
        layout.addWidget(self.tarih_edit[0])
        
        self.saat_edit = create_line_edit("Saat", "14:00")
        layout.addWidget(self.saat_edit[0])
        
        # Mekan
        self.mekan_edit = create_line_edit("Mekan", "Dernek binası, online vb.")
        layout.addWidget(self.mekan_edit[0])
        
        # TOPLANTI İÇERİĞİ
        section2 = QLabel("TOPLANTI İÇERİĞİ")
        section2.setStyleSheet(self.SECTION_STYLE)
        layout.addWidget(section2)
        
        # Gündem
        self.gundem_edit = create_text_edit("Gündem", "1. Açılış\n2. ...", max_height=80)
        layout.addWidget(self.gundem_edit[0])
        
        # Katılımcılar
        self.katilimcilar_edit = create_text_edit("Katılımcılar", "Katılımcı isimleri...", max_height=60)
        layout.addWidget(self.katilimcilar_edit[0])
        
        # Kararlar
        self.kararlar_edit = create_text_edit("Alınan Kararlar", "Karar 1:\nKarar 2:", max_height=80)
        layout.addWidget(self.kararlar_edit[0])
        
        # Tutanak
        self.tutanak_edit = create_text_edit("Tutanak / Özet", "Toplantı özeti...", max_height=60)
        layout.addWidget(self.tutanak_edit[0])
        
        # Bir Sonraki Toplantı
        self.sonraki_edit = create_date_edit("Bir Sonraki Toplantı")
        layout.addWidget(self.sonraki_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_data(self):
        """Mevcut toplantı verilerini yükle"""
        if not self.toplanti_data:
            return
        
        idx = self.tur_combo[1].findText(self.toplanti_data.get('toplanti_turu', ''))
        if idx >= 0:
            self.tur_combo[1].setCurrentIndex(idx)
        
        self.baslik_edit[1].setText(self.toplanti_data.get('baslik', ''))
        
        tarih = self.toplanti_data.get('tarih')
        if tarih:
            self.tarih_edit[1].setDate(QDate.fromString(tarih, "yyyy-MM-dd"))
        
        self.saat_edit[1].setText(self.toplanti_data.get('saat', '') or '')
        self.mekan_edit[1].setText(self.toplanti_data.get('mekan', '') or '')
        self.gundem_edit[1].setPlainText(self.toplanti_data.get('gundem', '') or '')
        self.katilimcilar_edit[1].setPlainText(self.toplanti_data.get('katilimcilar', '') or '')
        self.kararlar_edit[1].setPlainText(self.toplanti_data.get('kararlar', '') or '')
        self.tutanak_edit[1].setPlainText(self.toplanti_data.get('tutanak', '') or '')
        
        sonraki = self.toplanti_data.get('bir_sonraki_toplanti')
        if sonraki:
            self.sonraki_edit[1].setDate(QDate.fromString(sonraki, "yyyy-MM-dd"))
        
    def get_data(self) -> dict:
        """Form verilerini al"""
        sonraki = self.sonraki_edit[1].date().toString("yyyy-MM-dd")
        if sonraki == "2000-01-01":
            sonraki = None
            
        return {
            'toplanti_turu': self.tur_combo[1].currentText(),
            'baslik': self.baslik_edit[1].text().strip(),
            'tarih': self.tarih_edit[1].date().toString("yyyy-MM-dd"),
            'saat': self.saat_edit[1].text().strip(),
            'mekan': self.mekan_edit[1].text().strip(),
            'gundem': self.gundem_edit[1].toPlainText().strip(),
            'katilimcilar': self.katilimcilar_edit[1].toPlainText().strip(),
            'kararlar': self.kararlar_edit[1].toPlainText().strip(),
            'tutanak': self.tutanak_edit[1].toPlainText().strip(),
            'bir_sonraki_toplanti': sonraki
        }
    
    def validate(self) -> bool:
        if not self.baslik_edit[1].text().strip():
            MessageBox("Uyarı", "Başlık boş bırakılamaz!", self).show()
            return False
        return True


class ToplantiWidget(QWidget):
    """Toplantı yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.toplanti_yoneticisi = ToplantiYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("TOPLANTI KAYITLARI")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Arama
        self.arama_edit = QLineEdit()
        self.arama_edit.setPlaceholderText("🔍 Toplantı ara...")
        self.arama_edit.textChanged.connect(self.ara)
        self.arama_edit.setMaximumWidth(250)
        toolbar.addWidget(self.arama_edit)
        
        # Tür filtresi
        toolbar.addWidget(QLabel("Tür:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü", None)
        self.tur_filter.addItems([
            "Yönetim Kurulu", "Genel Kurul", "Denetim Kurulu", "Komisyon", "Diğer"
        ])
        self.tur_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.tur_filter)
        
        toolbar.addStretch()
        
        # Butonlar
        self.ekle_btn = QPushButton("➕ Yeni Toplantı")
        self.ekle_btn.clicked.connect(self.toplanti_ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.toplanti_duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.toplanti_sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "toplantilar", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tür", "Başlık", "Tarih", "Saat", "Mekan"
        ])
        setup_resizable_table(self.table, table_id="toplantilar_tablosu", stretch_column=2)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.toplanti_duzenle)
        
        layout.addWidget(self.table)
        
        # Detay görünümü
        self.detay_group = QGroupBox("TOPLANTI DETAYI")
        self.detay_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        detay_layout = QVBoxLayout()
        
        self.detay_text = QTextEdit()
        self.detay_text.setReadOnly(True)
        self.detay_text.setMinimumHeight(150)
        self.detay_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background: transparent;
                font-size: 13px;
            }
        """)
        detay_layout.addWidget(self.detay_text)
        
        self.detay_group.setLayout(detay_layout)
        layout.addWidget(self.detay_group)
        
        self.setLayout(layout)
        
    def load_data(self):
        """Toplantıları yükle"""
        tur = self.tur_filter.currentText() if self.tur_filter.currentIndex() > 0 else None
        
        toplantilar = self.toplanti_yoneticisi.toplanti_listesi(toplanti_turu=tur)
        
        self.table.setRowCount(len(toplantilar))
        
        for row, t in enumerate(toplantilar):
            self.table.setItem(row, 0, QTableWidgetItem(str(t['toplanti_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(t['toplanti_turu']))
            self.table.setItem(row, 2, QTableWidgetItem(t['baslik']))
            self.table.setItem(row, 3, QTableWidgetItem(t['tarih']))
            self.table.setItem(row, 4, QTableWidgetItem(t.get('saat', '') or '-'))
            self.table.setItem(row, 5, QTableWidgetItem(t.get('mekan', '') or '-'))
        
        self.detay_text.clear()
        
    def ara(self):
        """Ara"""
        text = self.arama_edit.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in [1, 2, 5]
            )
            self.table.setRowHidden(row, not match)
            
    def on_selection(self):
        """Seçim değiştiğinde"""
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
            self.sil_btn.setEnabled(True)
            self._show_detail()
        else:
            self.current_id = None
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
            self.detay_text.clear()
    
    def _show_detail(self):
        """Toplantı detayını göster"""
        if not self.current_id:
            return
        
        toplanti = self.toplanti_yoneticisi.toplanti_getir(self.current_id)
        if not toplanti:
            return
        
        html = f"""
        <style>
            .section {{ color: #64B5F6; font-weight: bold; margin-top: 10px; }}
            .content {{ margin-left: 10px; color: #444; }}
        </style>
        <p class="section">📋 GÜNDEM:</p>
        <p class="content">{(toplanti.get('gundem') or '-').replace(chr(10), '<br>')}</p>
        
        <p class="section">👥 KATILIMCILAR:</p>
        <p class="content">{toplanti.get('katilimcilar') or '-'}</p>
        
        <p class="section">✅ ALINAN KARARLAR:</p>
        <p class="content">{(toplanti.get('kararlar') or '-').replace(chr(10), '<br>')}</p>
        
        <p class="section">📝 TUTANAK:</p>
        <p class="content">{(toplanti.get('tutanak') or '-').replace(chr(10), '<br>')}</p>
        """
        
        if toplanti.get('bir_sonraki_toplanti'):
            html += f"""
            <p class="section">📅 BİR SONRAKİ TOPLANTI:</p>
            <p class="content">{toplanti['bir_sonraki_toplanti']}</p>
            """
        
        self.detay_text.setHtml(html)
    
    def toplanti_ekle(self):
        """Yeni toplantı ekle"""
        form = ToplantiFormWidget()
        drawer = DrawerPanel(self, "Yeni Toplantı", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.toplanti_yoneticisi.toplanti_ekle(**data)
                self.load_data()
                MessageBox("Başarılı", "Toplantı kaydedildi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def toplanti_duzenle(self):
        """Toplantı düzenle"""
        if not self.current_id:
            return
        
        toplanti = self.toplanti_yoneticisi.toplanti_getir(self.current_id)
        if not toplanti:
            return
        
        form = ToplantiFormWidget(toplanti)
        drawer = DrawerPanel(self, "Toplantı Düzenle", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.toplanti_yoneticisi.toplanti_guncelle(self.current_id, **data)
                self.load_data()
                MessageBox("Başarılı", "Toplantı güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def toplanti_sil(self):
        """Toplantı sil"""
        if not self.current_id:
            return
        
        w = MessageBox("Toplantı Sil", "Bu toplantı kaydını silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.toplanti_yoneticisi.toplanti_sil(self.current_id)
                self.load_data()
                self.current_id = None
                MessageBox("Başarılı", "Toplantı silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()


