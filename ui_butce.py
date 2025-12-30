"""
BADER Derneği - Bütçe Planlama Modülü
Yıllık bütçe planlama ve takip
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QFrame,
                             QComboBox, QGroupBox, QGridLayout,
                             QHeaderView, QProgressBar)
from PyQt5.QtCore import Qt
from qfluentwidgets import MessageBox
from PyQt5.QtGui import QColor
from database import Database
from models import ButceYoneticisi, RaporYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import create_line_edit, create_combo_box, create_double_spin_box, create_spin_box
from ui_helpers import export_table_to_excel
from datetime import datetime


class ButceFormWidget(QWidget):
    """Bütçe kalemi formu"""
    
    def __init__(self, db: Database, butce_data: dict = None):
        super().__init__()
        self.db = db
        self.butce_data = butce_data
        self.setup_ui()
        
        if butce_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Yıl
        self.yil_spin = create_spin_box("Yıl *")
        self.yil_spin[1].setMinimum(2020)
        self.yil_spin[1].setMaximum(2050)
        self.yil_spin[1].setValue(datetime.now().year)
        layout.addWidget(self.yil_spin[0])
        
        # Tür (Gelir/Gider)
        self.tur_combo = create_combo_box("Tür *", searchable=False)
        self.tur_combo[1].addItems(["GELİR", "GİDER"])
        layout.addWidget(self.tur_combo[0])
        
        # Kategori
        self.kategori_edit = create_line_edit("Kategori *", "Ör: Aidat, Kira, Personel...")
        layout.addWidget(self.kategori_edit[0])
        
        # Planlanan Tutar
        self.planlanan_spin = create_double_spin_box("Planlanan Tutar *")
        self.planlanan_spin[1].setMaximum(100000000)
        self.planlanan_spin[1].setSuffix(" ₺")
        layout.addWidget(self.planlanan_spin[0])
        
        # Gerçekleşen Tutar
        self.gerceklesen_spin = create_double_spin_box("Gerçekleşen Tutar")
        self.gerceklesen_spin[1].setMaximum(100000000)
        self.gerceklesen_spin[1].setSuffix(" ₺")
        layout.addWidget(self.gerceklesen_spin[0])
        
        # Açıklama
        self.aciklama_edit = create_line_edit("Açıklama", "Açıklama...")
        layout.addWidget(self.aciklama_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_data(self):
        if not self.butce_data:
            return
        
        self.yil_spin[1].setValue(self.butce_data.get('yil', datetime.now().year))
        
        tur = self.butce_data.get('tur', 'GELİR')
        idx = self.tur_combo[1].findText(tur)
        if idx >= 0:
            self.tur_combo[1].setCurrentIndex(idx)
        
        self.kategori_edit[1].setText(self.butce_data.get('kategori', ''))
        self.planlanan_spin[1].setValue(self.butce_data.get('planlanan_tutar', 0) or 0)
        self.gerceklesen_spin[1].setValue(self.butce_data.get('gerceklesen_tutar', 0) or 0)
        self.aciklama_edit[1].setText(self.butce_data.get('aciklama', '') or '')
        
    def get_data(self) -> dict:
        return {
            'yil': self.yil_spin[1].value(),
            'kategori': self.kategori_edit[1].text().strip(),
            'tur': self.tur_combo[1].currentText(),
            'planlanan_tutar': self.planlanan_spin[1].value(),
            'gerceklesen_tutar': self.gerceklesen_spin[1].value() or None,
            'aciklama': self.aciklama_edit[1].text().strip()
        }
    
    def validate(self) -> bool:
        if not self.kategori_edit[1].text().strip():
            MessageBox("Uyarı", "Kategori boş bırakılamaz!", self).show()
            return False
        if self.planlanan_spin[1].value() <= 0:
            MessageBox("Uyarı", "Planlanan tutar sıfırdan büyük olmalıdır!", self).show()
            return False
        return True


class StatCard(QFrame):
    """İstatistik kartı"""
    
    def __init__(self, title: str, value: str, color: str = "#64B5F6"):
        super().__init__()
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid rgba(47, 43, 61, 0.08);
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
        """)
        self.setMinimumHeight(80)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #97959e; font-size: 11px; font-weight: 600;")
        layout.addWidget(self.title_label)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 700;")
        layout.addWidget(self.value_label)
        
        self.setLayout(layout)
    
    def set_value(self, value: str):
        self.value_label.setText(value)


class ButceWidget(QWidget):
    """Bütçe planlama ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.butce_yoneticisi = ButceYoneticisi(db)
        self.rapor_yoneticisi = RaporYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık ve yıl seçimi
        header = QHBoxLayout()
        
        title = QLabel("BÜTÇE PLANLAMA")
        title.setProperty("class", "title")
        header.addWidget(title)
        
        header.addStretch()
        
        header.addWidget(QLabel("Yıl:"))
        self.yil_combo = QComboBox()
        current_year = datetime.now().year
        for y in range(current_year + 2, 2019, -1):
            self.yil_combo.addItem(str(y), y)
        self.yil_combo.setCurrentIndex(2)  # Mevcut yıl
        self.yil_combo.currentIndexChanged.connect(self.load_data)
        header.addWidget(self.yil_combo)
        
        layout.addLayout(header)
        
        # Özet kartları
        cards = QHBoxLayout()
        cards.setSpacing(15)
        
        self.plan_gelir_card = StatCard("Plan. Gelir", "0.00 ₺", "#4CAF50")
        cards.addWidget(self.plan_gelir_card)
        
        self.plan_gider_card = StatCard("Plan. Gider", "0.00 ₺", "#f44336")
        cards.addWidget(self.plan_gider_card)
        
        self.gercek_gelir_card = StatCard("Gerç. Gelir", "0.00 ₺", "#66BB6A")
        cards.addWidget(self.gercek_gelir_card)
        
        self.gercek_gider_card = StatCard("Gerç. Gider", "0.00 ₺", "#EF5350")
        cards.addWidget(self.gercek_gider_card)
        
        self.net_card = StatCard("Net Fark", "0.00 ₺", "#64B5F6")
        cards.addWidget(self.net_card)
        
        layout.addLayout(cards)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.ekle_btn = QPushButton("➕ Bütçe Kalemi Ekle")
        self.ekle_btn.clicked.connect(self.butce_ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.butce_duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.butce_sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        toolbar.addStretch()
        
        self.sync_btn = QPushButton("🔄 Gerçekleşeni Güncelle")
        self.sync_btn.setToolTip("Gelir ve gider verilerinden gerçekleşen tutarları güncelle")
        self.sync_btn.clicked.connect(self.sync_gerceklesen)
        toolbar.addWidget(self.sync_btn)
        
        self.export_btn = QPushButton("📊 Excel")
        self.export_btn.clicked.connect(lambda: export_table_to_excel(self.table, "butce", self))
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tür", "Kategori", "Planlanan", "Gerçekleşen", "Fark", "Oran"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.butce_duzenle)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
    def load_data(self):
        """Bütçe verilerini yükle"""
        yil = self.yil_combo.currentData()
        butce_list = self.butce_yoneticisi.butce_listesi(yil)
        
        # Tablo doldur
        self.table.setRowCount(len(butce_list))
        
        toplam_plan_gelir = 0
        toplam_plan_gider = 0
        toplam_gercek_gelir = 0
        toplam_gercek_gider = 0
        
        for row, b in enumerate(butce_list):
            self.table.setItem(row, 0, QTableWidgetItem(str(b['butce_id'])))
            
            tur_item = QTableWidgetItem(b['tur'])
            if b['tur'] == 'GELİR':
                tur_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                tur_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 1, tur_item)
            
            self.table.setItem(row, 2, QTableWidgetItem(b['kategori']))
            
            planlanan = b['planlanan_tutar'] or 0
            gerceklesen = b['gerceklesen_tutar'] or 0
            fark = gerceklesen - planlanan
            oran = (gerceklesen / planlanan * 100) if planlanan > 0 else 0
            
            self.table.setItem(row, 3, QTableWidgetItem(f"{planlanan:,.2f} ₺"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{gerceklesen:,.2f} ₺"))
            
            fark_item = QTableWidgetItem(f"{fark:,.2f} ₺")
            if b['tur'] == 'GELİR':
                fark_item.setForeground(Qt.GlobalColor.darkGreen if fark >= 0 else Qt.GlobalColor.darkRed)
            else:
                fark_item.setForeground(Qt.GlobalColor.darkRed if fark > 0 else Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 5, fark_item)
            
            oran_item = QTableWidgetItem(f"%{oran:.1f}")
            if oran >= 80:
                oran_item.setForeground(Qt.GlobalColor.darkGreen)
            elif oran >= 50:
                oran_item.setForeground(QColor("#FF9800"))
            else:
                oran_item.setForeground(Qt.GlobalColor.darkRed)
            self.table.setItem(row, 6, oran_item)
            
            # Toplamları hesapla
            if b['tur'] == 'GELİR':
                toplam_plan_gelir += planlanan
                toplam_gercek_gelir += gerceklesen
            else:
                toplam_plan_gider += planlanan
                toplam_gercek_gider += gerceklesen
        
        # Kartları güncelle
        self.plan_gelir_card.set_value(f"{toplam_plan_gelir:,.2f} ₺")
        self.plan_gider_card.set_value(f"{toplam_plan_gider:,.2f} ₺")
        self.gercek_gelir_card.set_value(f"{toplam_gercek_gelir:,.2f} ₺")
        self.gercek_gider_card.set_value(f"{toplam_gercek_gider:,.2f} ₺")
        
        net_plan = toplam_plan_gelir - toplam_plan_gider
        net_gercek = toplam_gercek_gelir - toplam_gercek_gider
        self.net_card.set_value(f"{net_gercek:,.2f} ₺")
        
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
    
    def butce_ekle(self):
        """Yeni bütçe kalemi ekle"""
        form = ButceFormWidget(self.db)
        form.yil_spin[1].setValue(self.yil_combo.currentData())
        
        drawer = DrawerPanel(self, "Bütçe Kalemi Ekle", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                result = self.butce_yoneticisi.butce_ekle(**data)
                if result == -1:
                    MessageBox("Uyarı", "Bu kategori için zaten bir kayıt var!", self).show()
                    return
                self.load_data()
                MessageBox("Başarılı", "Bütçe kalemi eklendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def butce_duzenle(self):
        """Bütçe kalemi düzenle"""
        if not self.current_id:
            return
        
        # Mevcut veriyi al
        yil = self.yil_combo.currentData()
        butce_list = self.butce_yoneticisi.butce_listesi(yil)
        butce = next((b for b in butce_list if b['butce_id'] == self.current_id), None)
        
        if not butce:
            return
        
        form = ButceFormWidget(self.db, butce)
        drawer = DrawerPanel(self, "Bütçe Kalemi Düzenle", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                self.butce_yoneticisi.butce_guncelle(
                    self.current_id,
                    planlanan_tutar=data['planlanan_tutar'],
                    gerceklesen_tutar=data['gerceklesen_tutar'],
                    aciklama=data['aciklama']
                )
                self.load_data()
                MessageBox("Başarılı", "Bütçe kalemi güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def butce_sil(self):
        """Bütçe kalemi sil"""
        if not self.current_id:
            return
        
        w = MessageBox("Bütçe Sil", "Bu bütçe kalemini silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.db.cursor.execute("DELETE FROM butce_planlari WHERE butce_id = ?", (self.current_id,))
                self.db.commit()
                self.load_data()
                self.current_id = None
                MessageBox("Başarılı", "Bütçe kalemi silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
    
    def sync_gerceklesen(self):
        """Gerçekleşen tutarları gelir/gider verilerinden güncelle"""
        yil = self.yil_combo.currentData()
        baslangic = f"{yil}-01-01"
        bitis = f"{yil}-12-31"
        
        try:
            # Gelir dağılımı
            gelir_dagilimi = self.rapor_yoneticisi.gelir_turu_dagilimi(baslangic, bitis)
            for g in gelir_dagilimi:
                self.db.cursor.execute("""
                    UPDATE butce_planlari 
                    SET gerceklesen_tutar = ?
                    WHERE yil = ? AND tur = 'GELİR' AND kategori = ?
                """, (g['toplam'], yil, g['gelir_turu']))
            
            # Gider dağılımı
            gider_dagilimi = self.rapor_yoneticisi.gider_turu_dagilimi(baslangic, bitis)
            for g in gider_dagilimi:
                self.db.cursor.execute("""
                    UPDATE butce_planlari 
                    SET gerceklesen_tutar = ?
                    WHERE yil = ? AND tur = 'GİDER' AND kategori = ?
                """, (g['toplam'], yil, g['gider_turu']))
            
            self.db.commit()
            self.load_data()
            MessageBox("Başarılı", "Gerçekleşen tutarlar güncellendi!", self).show()
            
        except Exception as e:
            MessageBox("Hata", str(e), self).show()


