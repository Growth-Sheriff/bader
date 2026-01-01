"""
BADER Derneği - Belge Yönetimi Modülü
Dosya ekleme, görüntüleme, indirme
"""

import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QFrame,
                             QComboBox, QHeaderView, QFileDialog,
                             QLineEdit)
from PyQt5.QtCore import Qt
from qfluentwidgets import MessageBox
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from database import Database
from models import BelgeYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import create_line_edit, create_combo_box, create_text_edit
from ui_helpers import export_table_to_excel, setup_resizable_table
from ui_login import session


def get_belge_folder() -> str:
    """Belge klasörünü al"""
    folder = os.path.expanduser("~/Documents/BADER_Belgeler")
    os.makedirs(folder, exist_ok=True)
    return folder


def format_file_size(size: int) -> str:
    """Dosya boyutunu formatla"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


class BelgeFormWidget(QWidget):
    """Belge ekleme formu"""
    
    def __init__(self, belge_data: dict = None):
        super().__init__()
        self.belge_data = belge_data
        self.selected_file = None
        self.setup_ui()
        
        if belge_data:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Dosya seçimi
        file_frame = QFrame()
        file_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("Dosya seçilmedi")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #888; font-size: 13px;")
        file_layout.addWidget(self.file_label)
        
        select_btn = QPushButton("📁 Dosya Seç")
        select_btn.clicked.connect(self.select_file)
        select_btn.setFixedWidth(150)
        file_layout.addWidget(select_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        file_frame.setLayout(file_layout)
        layout.addWidget(file_frame)
        
        # Belge Türü
        self.tur_combo = create_combo_box("Belge Türü *", searchable=False)
        self.tur_combo[1].addItems(["DEKONT", "FATURA", "MAKBUZ", "SÖZLEŞME", "TUTANAK", "KARAR", "DİĞER"])
        layout.addWidget(self.tur_combo[0])
        
        # Başlık
        self.baslik_edit = create_line_edit("Başlık *", "Belge başlığı")
        layout.addWidget(self.baslik_edit[0])
        
        # Açıklama
        self.aciklama_edit = create_text_edit("Açıklama", "Belge hakkında notlar...", max_height=60)
        layout.addWidget(self.aciklama_edit[0])
        
        layout.addStretch()
        self.setLayout(layout)
        
    def select_file(self):
        """Dosya seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Dosya Seç", "",
            "Tüm Dosyalar (*);;PDF (*.pdf);;Resimler (*.png *.jpg *.jpeg);;Belgeler (*.doc *.docx *.xls *.xlsx)"
        )
        
        if file_path:
            self.selected_file = file_path
            filename = os.path.basename(file_path)
            size = os.path.getsize(file_path)
            self.file_label.setText(f"📄 {filename}\n({format_file_size(size)})")
            self.file_label.setStyleSheet("color: #4CAF50; font-size: 13px; font-weight: 500;")
    
    def load_data(self):
        """Mevcut veriyi yükle"""
        if not self.belge_data:
            return
        
        idx = self.tur_combo[1].findText(self.belge_data.get('belge_turu', ''))
        if idx >= 0:
            self.tur_combo[1].setCurrentIndex(idx)
        
        self.baslik_edit[1].setText(self.belge_data.get('baslik', ''))
        self.aciklama_edit[1].setPlainText(self.belge_data.get('aciklama', '') or '')
        
        if self.belge_data.get('dosya_adi'):
            self.file_label.setText(f"📄 {self.belge_data['dosya_adi']}")
            self.file_label.setStyleSheet("color: #64B5F6; font-size: 13px;")
        
    def get_data(self) -> dict:
        return {
            'belge_turu': self.tur_combo[1].currentText(),
            'baslik': self.baslik_edit[1].text().strip(),
            'aciklama': self.aciklama_edit[1].toPlainText().strip(),
            'selected_file': self.selected_file
        }
    
    def validate(self, is_new: bool = True) -> bool:
        data = self.get_data()
        
        if not data['baslik']:
            MessageBox("Uyarı", "Başlık boş bırakılamaz!", self).show()
            return False
        
        if is_new and not data['selected_file']:
            MessageBox("Uyarı", "Lütfen bir dosya seçin!", self).show()
            return False
        
        return True


class BelgelerWidget(QWidget):
    """Belge yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.belge_yoneticisi = BelgeYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        self.apply_permissions()
    
    def apply_permissions(self):
        """Kullanıcı izinlerine göre butonları ayarla"""
        self.ekle_btn.setVisible(session.has_permission('belge_ekle'))
        self.sil_btn.setVisible(session.has_permission('belge_sil'))
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("BELGE YÖNETİMİ")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Arama
        self.arama_edit = QLineEdit()
        self.arama_edit.setPlaceholderText("🔍 Belge ara...")
        self.arama_edit.textChanged.connect(self.ara)
        self.arama_edit.setMaximumWidth(250)
        toolbar.addWidget(self.arama_edit)
        
        # Tür filtresi
        toolbar.addWidget(QLabel("Tür:"))
        self.tur_filter = QComboBox()
        self.tur_filter.addItem("Tümü", None)
        self.tur_filter.addItems(["DEKONT", "FATURA", "MAKBUZ", "SÖZLEŞME", "TUTANAK", "KARAR", "DİĞER"])
        self.tur_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.tur_filter)
        
        toolbar.addStretch()
        
        # Butonlar
        self.ekle_btn = QPushButton("➕ Belge Ekle")
        self.ekle_btn.clicked.connect(self.belge_ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.ac_btn = QPushButton("📂 Aç")
        self.ac_btn.clicked.connect(self.belge_ac)
        self.ac_btn.setEnabled(False)
        toolbar.addWidget(self.ac_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.belge_sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tür", "Başlık", "Dosya", "Boyut", "Tarih"
        ])
        setup_resizable_table(self.table, table_id="belgeler_tablosu", stretch_column=2)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.belge_ac)
        
        layout.addWidget(self.table)
        
        # İstatistik
        self.stats_label = QLabel("Toplam: 0 belge")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        
    def load_data(self):
        """Belgeleri yükle"""
        tur = self.tur_filter.currentText() if self.tur_filter.currentIndex() > 0 else None
        
        belgeler = self.belge_yoneticisi.belge_listesi(belge_turu=tur)
        
        self.table.setRowCount(len(belgeler))
        
        for row, b in enumerate(belgeler):
            self.table.setItem(row, 0, QTableWidgetItem(str(b['belge_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(b['belge_turu']))
            self.table.setItem(row, 2, QTableWidgetItem(b['baslik']))
            self.table.setItem(row, 3, QTableWidgetItem(b['dosya_adi']))
            self.table.setItem(row, 4, QTableWidgetItem(format_file_size(b.get('dosya_boyutu', 0) or 0)))
            
            tarih = b.get('olusturma_tarihi', '')
            if tarih:
                try:
                    dt = datetime.fromisoformat(tarih.replace('Z', '+00:00'))
                    tarih = dt.strftime('%d.%m.%Y')
                except:
                    pass
            self.table.setItem(row, 5, QTableWidgetItem(tarih))
        
        self.stats_label.setText(f"Toplam: {len(belgeler)} belge")
        
    def ara(self):
        """Ara"""
        text = self.arama_edit.text().lower()
        for row in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in [1, 2, 3]
            )
            self.table.setRowHidden(row, not match)
            
    def on_selection(self):
        """Seçim değiştiğinde"""
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.ac_btn.setEnabled(True)
            self.sil_btn.setEnabled(True)
        else:
            self.current_id = None
            self.ac_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
    
    def belge_ekle(self):
        """Yeni belge ekle"""
        form = BelgeFormWidget()
        drawer = DrawerPanel(self, "Belge Ekle", form)
        
        def on_submit():
            if not form.validate(is_new=True):
                return
            
            data = form.get_data()
            selected_file = data['selected_file']
            
            try:
                # Dosyayı kopyala
                folder = get_belge_folder()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = os.path.basename(selected_file)
                name, ext = os.path.splitext(filename)
                new_filename = f"{timestamp}_{name}{ext}"
                dest_path = os.path.join(folder, new_filename)
                
                shutil.copy2(selected_file, dest_path)
                file_size = os.path.getsize(dest_path)
                
                # Veritabanına kaydet
                self.belge_yoneticisi.belge_ekle(
                    belge_turu=data['belge_turu'],
                    baslik=data['baslik'],
                    dosya_adi=filename,
                    dosya_yolu=dest_path,
                    dosya_boyutu=file_size,
                    aciklama=data['aciklama']
                )
                
                self.load_data()
                MessageBox("Başarılı", "Belge eklendi!", self).show()
                drawer.close()
                
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def belge_ac(self):
        """Belgeyi aç"""
        if not self.current_id:
            return
        
        belgeler = self.belge_yoneticisi.belge_listesi()
        belge = next((b for b in belgeler if b['belge_id'] == self.current_id), None)
        
        if belge and belge.get('dosya_yolu'):
            if os.path.exists(belge['dosya_yolu']):
                QDesktopServices.openUrl(QUrl.fromLocalFile(belge['dosya_yolu']))
            else:
                MessageBox("Uyarı", "Dosya bulunamadı!", self).show()
    
    def belge_sil(self):
        """Belge sil"""
        if not self.current_id:
            return
        
        w = MessageBox("Belge Sil", "Bu belgeyi silmek istediğinizden emin misiniz?\n(Dosya da silinecektir)", self)
        if w.exec():
            try:
                # Dosya yolunu al ve sil
                dosya_yolu = self.belge_yoneticisi.belge_sil(self.current_id)
                
                if dosya_yolu and os.path.exists(dosya_yolu):
                    try:
                        os.remove(dosya_yolu)
                    except:
                        pass
                
                self.load_data()
                self.current_id = None
                MessageBox("Başarılı", "Belge silindi!", self).show()
                
            except Exception as e:
                MessageBox("Hata", str(e), self).show()


