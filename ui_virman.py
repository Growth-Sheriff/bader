"""
BADER Derneği - Virman (Kasa Transfer) UI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QDialog, QFormLayout,
                             QDoubleSpinBox, QDateEdit, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from qfluentwidgets import MessageBox
from database import Database
from models import VirmanYoneticisi, KasaYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import create_line_edit, create_combo_box, create_date_edit, create_double_spin_box
from ui_helpers import export_table_to_excel, setup_resizable_table
from ui_login import session


class VirmanFormWidget(QWidget):
    """Virman ekleme formu"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.setup_ui()
        self.load_kasalar()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Bilgi
        info_label = QLabel("💸 Kasalar arası para transferi yapın")
        info_label.setProperty("class", "subtitle")
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 6px;
            }
        """)
        layout.addWidget(info_label)
        
        # Tarih
        self.tarih_edit = create_date_edit("Tarih *")
        self.tarih_edit[1].setDate(QDate.currentDate())
        layout.addWidget(self.tarih_edit[0])
        
        # Gönderen Kasa
        self.gonderen_combo = create_combo_box("Gönderen Kasa *")
        layout.addWidget(self.gonderen_combo[0])
        
        # Alan Kasa
        self.alan_combo = create_combo_box("Alan Kasa *")
        layout.addWidget(self.alan_combo[0])
        
        # Tutar
        self.tutar_spin = create_double_spin_box("Tutar *")
        self.tutar_spin[1].setMinimum(0.01)
        self.tutar_spin[1].setMaximum(10000000)
        self.tutar_spin[1].setSuffix(" ₺")
        layout.addWidget(self.tutar_spin[0])
        
        # Açıklama
        self.aciklama_edit = create_line_edit("Açıklama", "Virman açıklaması...")
        layout.addWidget(self.aciklama_edit[0])
        
        # Uyarı
        warning = QLabel("⚠️ Gönderen ve alan kasa farklı olmalıdır!")
        warning.setStyleSheet("""
            QLabel {
                color: #E65100;
                font-size: 12px;
                padding: 8px;
                background-color: #FFF3E0;
                border-radius: 4px;
                border-left: 3px solid #FF9800;
            }
        """)
        layout.addWidget(warning)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_kasalar(self):
        kasalar = self.kasa_yoneticisi.kasa_listesi()
        for kasa in kasalar:
            self.gonderen_combo[1].addItem(
                f"{kasa['kasa_adi']} ({kasa['para_birimi']})",
                kasa['kasa_id']
            )
            self.alan_combo[1].addItem(
                f"{kasa['kasa_adi']} ({kasa['para_birimi']})",
                kasa['kasa_id']
            )
            
    def get_data(self):
        return {
            'tarih': self.tarih_edit[1].date().toString("yyyy-MM-dd"),
            'gonderen_kasa_id': self.gonderen_combo[1].currentData(),
            'alan_kasa_id': self.alan_combo[1].currentData(),
            'tutar': self.tutar_spin[1].value(),
            'aciklama': self.aciklama_edit[1].text().strip()
        }


class VirmanWidget(QWidget):
    """Virman yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.virman_yoneticisi = VirmanYoneticisi(db)
        self.setup_ui()
        self.load_virmanlar()
        self.apply_permissions()
    
    def apply_permissions(self):
        """Kullanıcı izinlerine göre butonları ayarla"""
        self.ekle_btn.setVisible(session.has_permission('kasa_islem'))
        self.sil_btn.setVisible(session.has_permission('kasa_islem'))
        self.export_btn.setVisible(session.has_permission('rapor_export'))
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("VİRMAN İŞLEMLERİ")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)
        
        subtitle = QLabel("Kasalar arası para transferi")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        toolbar_layout.addWidget(QLabel("Tarih Aralığı:"))
        self.baslangic_date = QDateEdit()
        self.baslangic_date.setDate(QDate.currentDate().addMonths(-1))
        self.baslangic_date.setCalendarPopup(True)
        self.baslangic_date.dateChanged.connect(self.load_virmanlar)
        toolbar_layout.addWidget(self.baslangic_date)
        
        toolbar_layout.addWidget(QLabel("-"))
        self.bitis_date = QDateEdit()
        self.bitis_date.setDate(QDate.currentDate())
        self.bitis_date.setCalendarPopup(True)
        self.bitis_date.dateChanged.connect(self.load_virmanlar)
        toolbar_layout.addWidget(self.bitis_date)
        
        toolbar_layout.addStretch()
        
        self.ekle_btn = QPushButton("➕ Yeni Virman")
        self.ekle_btn.clicked.connect(self.virman_ekle)
        toolbar_layout.addWidget(self.ekle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.virman_sil)
        self.sil_btn.setEnabled(False)
        toolbar_layout.addWidget(self.sil_btn)
        
        # Excel export
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.setToolTip("Listeyi Excel'e Aktar")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "virmanlar", self))
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Gönderen Kasa", "Alan Kasa", "Tutar", "Açıklama"
        ])
        
        # Responsive sütunlar - hareket ettirilebilir, sağ tık ile gizle/göster
        setup_resizable_table(self.table, table_id="virmanlar_tablosu", stretch_column=5)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Inline editing KAPALI
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Toplam
        self.toplam_label = QLabel("Toplam Virman: 0.00 ₺")
        self.toplam_label.setProperty("class", "subtitle")
        layout.addWidget(self.toplam_label)
        
        self.setLayout(layout)
        
    def load_virmanlar(self):
        """Virmanları yükle"""
        baslangic = self.baslangic_date.date().toString("yyyy-MM-dd")
        bitis = self.bitis_date.date().toString("yyyy-MM-dd")
        
        virmanlar = self.virman_yoneticisi.virman_listesi(
            baslangic_tarih=baslangic,
            bitis_tarih=bitis
        )
        
        self.table.setRowCount(0)
        toplam = 0.0
        
        for virman in virmanlar:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(virman['virman_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(virman['tarih']))
            self.table.setItem(row, 2, QTableWidgetItem(virman['gonderen_kasa_adi']))
            self.table.setItem(row, 3, QTableWidgetItem(virman['alan_kasa_adi']))
            self.table.setItem(row, 4, QTableWidgetItem(f"{virman['tutar']:.2f} ₺"))
            self.table.setItem(row, 5, QTableWidgetItem(virman.get('aciklama', '-')))
            
            toplam += virman['tutar']
        
        self.toplam_label.setText(f"Toplam Virman: {toplam:,.2f} ₺")
        
    def on_selection_changed(self):
        self.sil_btn.setEnabled(self.table.selectionModel().hasSelection())
    
    def virman_ekle(self):
        """Yeni virman ekle"""
        form_widget = VirmanFormWidget(self.db)
        drawer = DrawerPanel(self, "Yeni Virman İşlemi", form_widget)
        
        def on_submit():
            data = form_widget.get_data()
            
            if data['gonderen_kasa_id'] == data['alan_kasa_id']:
                MessageBox("Uyarı", "Gönderen ve alan kasa aynı olamaz!", self).show()
                return
            
            # Bakiye kontrolü
            from models import KasaYoneticisi
            kasa_yoneticisi = KasaYoneticisi(self.db)
            bakiye_bilgi = kasa_yoneticisi.kasa_bakiye_hesapla(data['gonderen_kasa_id'])
            
            if bakiye_bilgi and bakiye_bilgi.get('net_bakiye', 0) < data['tutar']:
                MessageBox(
                    "Yetersiz Bakiye", 
                    f"Gönderen kasada yeterli bakiye yok!\n\n"
                    f"Mevcut Bakiye: {bakiye_bilgi['net_bakiye']:,.2f} ₺\n"
                    f"İstenen Tutar: {data['tutar']:,.2f} ₺", 
                    self
                ).show()
                return
                
            try:
                self.virman_yoneticisi.virman_ekle(**data)
                self.load_virmanlar()
                MessageBox("Başarılı", "Virman işlemi tamamlandı!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", f"Virman eklenirken hata:\n{e}", self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
                
    def virman_sil(self):
        """Virman sil"""
        if not self.table.selectionModel().hasSelection():
            return
            
        row = self.table.currentRow()
        virman_id = int(self.table.item(row, 0).text())
        tutar = self.table.item(row, 4).text()
        
        w = MessageBox("Virman Sil", f"{tutar} tutarındaki virmanı silmek istediğinize emin misiniz?", self)
        if w.exec():
            try:
                self.virman_yoneticisi.virman_sil(virman_id)
                self.load_virmanlar()
                MessageBox("Başarılı", "Virman silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", f"Silme hatası:\n{e}", self).show()

