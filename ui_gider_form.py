"""GİDER FORM WIDGET"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QDate
from qfluentwidgets import MessageBox
from database import Database
from models import GiderYoneticisi, KasaYoneticisi
from ui_form_fields import *

class GiderFormWidget(QWidget):
    def __init__(self, parent=None, db: Database = None, gider_data: dict = None):
        super().__init__(parent)
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
        
        self.tarih_edit = create_date_edit()
        layout.addWidget(FormField("Tarih", self.tarih_edit, required=True))
        
        self.gider_turu_combo = create_combo_box([], searchable=True)
        self.gider_turu_combo.setEditable(True)
        layout.addWidget(FormField("Gider Türü", self.gider_turu_combo, required=True))
        
        self.aciklama_edit = create_line_edit("Gider açıklaması...")
        layout.addWidget(FormField("Açıklama", self.aciklama_edit, required=True))
        
        self.tutar_spin = create_double_spin_box(0.01, 10000000, 0, " ₺")
        layout.addWidget(FormField("Tutar", self.tutar_spin, required=True))
        
        self.kasa_combo = create_combo_box([], searchable=True)
        layout.addWidget(FormField("Kasa", self.kasa_combo, required=True))
        
        self.odeme_yapan_edit = create_line_edit("Ödeme yapan kişi...")
        layout.addWidget(FormField("Ödeme Yapan", self.odeme_yapan_edit))
        
        self.notlar_edit = create_text_edit("Ek notlar...", 80)
        layout.addWidget(FormField("Notlar", self.notlar_edit))
        
        self.setLayout(layout)
        
    def load_kasalar(self):
        self.kasa_combo.clear()
        for kasa in self.kasa_yoneticisi.kasa_listesi():
            self.kasa_combo.addItem(f"{kasa['kasa_adi']} ({kasa['para_birimi']})", kasa['kasa_id'])
            
    def load_gider_turleri(self):
        self.gider_turu_combo.clear()
        for tur in self.gider_yoneticisi.gider_turleri_listesi():
            self.gider_turu_combo.addItem(tur)  # String liste, dict değil
            
    def load_data(self):
        if self.gider_data:
            self.tarih_edit.setDate(QDate.fromString(self.gider_data['tarih'], "yyyy-MM-dd"))
            self.gider_turu_combo.setCurrentText(self.gider_data['gider_turu'])
            self.aciklama_edit.setText(self.gider_data['aciklama'])
            self.tutar_spin.setValue(self.gider_data['tutar'])
            for i in range(self.kasa_combo.count()):
                if self.kasa_combo.itemData(i) == self.gider_data['kasa_id']:
                    self.kasa_combo.setCurrentIndex(i)
                    break
            self.odeme_yapan_edit.setText(self.gider_data.get('odeme_yapan', ''))
            self.notlar_edit.setPlainText(self.gider_data.get('notlar', ''))
            
    def get_data(self):
        return {
            'tarih': self.tarih_edit.date().toString("yyyy-MM-dd"),
            'gider_turu': self.gider_turu_combo.currentText(),
            'aciklama': self.aciklama_edit.text().strip(),
            'tutar': self.tutar_spin.value(),
            'kasa_id': self.kasa_combo.currentData(),
            'odeme_yapan': self.odeme_yapan_edit.text().strip(),
            'notlar': self.notlar_edit.toPlainText().strip()
        }
    
    def validate(self):
        if not self.aciklama_edit.text().strip():
            MessageBox("Uyarı", "Açıklama zorunludur!", self).show()
            return False
        if self.tutar_spin.value() <= 0:
            MessageBox("Uyarı", "Tutar 0'dan büyük olmalıdır!", self).show()
            return False
        if not self.kasa_combo.currentData():
            MessageBox("Uyarı", "Kasa seçilmelidir!", self).show()
            return False
        return True
