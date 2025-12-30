"""
BADER Derneği - Kullanıcı Yönetimi
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel,
                             QHeaderView, QLineEdit)
from PyQt5.QtCore import Qt
from qfluentwidgets import MessageBox
from database import Database
from models import KullaniciYoneticisi
from ui_drawer import DrawerPanel
from ui_form_fields import create_line_edit, create_combo_box


class KullaniciFormWidget(QWidget):
    """Kullanıcı formu"""
    
    def __init__(self, kullanici_data: dict = None, is_new: bool = True):
        super().__init__()
        self.kullanici_data = kullanici_data
        self.is_new = is_new
        self.setup_ui()
        
        if kullanici_data and not is_new:
            self.load_data()
            
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Kullanıcı Adı
        self.username_edit = create_line_edit("Kullanıcı Adı *", "Giriş için kullanılacak")
        layout.addWidget(self.username_edit[0])
        
        # Ad Soyad
        self.ad_soyad_edit = create_line_edit("Ad Soyad *", "Kullanıcının adı")
        layout.addWidget(self.ad_soyad_edit[0])
        
        # E-posta
        self.email_edit = create_line_edit("E-posta", "ornek@email.com")
        layout.addWidget(self.email_edit[0])
        
        # Şifre
        self.sifre_edit = create_line_edit("Şifre" + (" *" if self.is_new else ""), 
                                           "Yeni şifre" if not self.is_new else "En az 6 karakter")
        self.sifre_edit[1].setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.sifre_edit[0])
        
        # Şifre Tekrar
        self.sifre2_edit = create_line_edit("Şifre Tekrar" + (" *" if self.is_new else ""), "Şifreyi tekrar girin")
        self.sifre2_edit[1].setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.sifre2_edit[0])
        
        # Rol
        self.rol_combo = create_combo_box("Rol *", searchable=False)
        self.rol_combo[1].addItems(["görüntüleyici", "muhasebeci", "admin"])
        layout.addWidget(self.rol_combo[0])
        
        # Bilgi metni
        info_label = QLabel("""
            <p style="color: #666; font-size: 11px; margin-top: 15px;">
            <b>Roller:</b><br>
            • <b>admin:</b> Tüm yetkilere sahip<br>
            • <b>muhasebeci:</b> Mali işlemler + düzenleme<br>
            • <b>görüntüleyici:</b> Sadece görüntüleme
            </p>
        """)
        layout.addWidget(info_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_data(self):
        if not self.kullanici_data:
            return
        
        self.username_edit[1].setText(self.kullanici_data.get('kullanici_adi', ''))
        self.username_edit[1].setEnabled(False)  # Kullanıcı adı değiştirilemez
        
        self.ad_soyad_edit[1].setText(self.kullanici_data.get('ad_soyad', ''))
        self.email_edit[1].setText(self.kullanici_data.get('email', '') or '')
        
        rol = self.kullanici_data.get('rol', 'görüntüleyici')
        idx = self.rol_combo[1].findText(rol)
        if idx >= 0:
            self.rol_combo[1].setCurrentIndex(idx)
        
    def get_data(self) -> dict:
        return {
            'kullanici_adi': self.username_edit[1].text().strip(),
            'ad_soyad': self.ad_soyad_edit[1].text().strip(),
            'email': self.email_edit[1].text().strip(),
            'sifre': self.sifre_edit[1].text(),
            'rol': self.rol_combo[1].currentText()
        }
    
    def validate(self) -> bool:
        data = self.get_data()
        
        if not data['kullanici_adi']:
            MessageBox("Uyarı", "Kullanıcı adı boş bırakılamaz!", self).show()
            return False
        
        if not data['ad_soyad']:
            MessageBox("Uyarı", "Ad Soyad boş bırakılamaz!", self).show()
            return False
        
        if self.is_new and not data['sifre']:
            MessageBox("Uyarı", "Şifre boş bırakılamaz!", self).show()
            return False
        
        if data['sifre'] and len(data['sifre']) < 6:
            MessageBox("Uyarı", "Şifre en az 6 karakter olmalıdır!", self).show()
            return False
        
        if data['sifre'] and data['sifre'] != self.sifre2_edit[1].text():
            MessageBox("Uyarı", "Şifreler eşleşmiyor!", self).show()
            return False
        
        return True


class KullanicilarWidget(QWidget):
    """Kullanıcı yönetimi ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.kullanici_yoneticisi = KullaniciYoneticisi(db)
        self.current_id = None
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("KULLANICI YÖNETİMİ")
        title.setProperty("class", "title")
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.ekle_btn = QPushButton("➕ Yeni Kullanıcı")
        self.ekle_btn.clicked.connect(self.kullanici_ekle)
        toolbar.addWidget(self.ekle_btn)
        
        self.duzenle_btn = QPushButton("✏️ Düzenle")
        self.duzenle_btn.clicked.connect(self.kullanici_duzenle)
        self.duzenle_btn.setEnabled(False)
        toolbar.addWidget(self.duzenle_btn)
        
        self.sil_btn = QPushButton("🗑️ Sil")
        self.sil_btn.setProperty("class", "danger")
        self.sil_btn.clicked.connect(self.kullanici_sil)
        self.sil_btn.setEnabled(False)
        toolbar.addWidget(self.sil_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kullanıcı Adı", "Ad Soyad", "E-posta", "Rol", "Son Giriş"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection)
        self.table.doubleClicked.connect(self.kullanici_duzenle)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def load_data(self):
        """Kullanıcıları yükle"""
        kullanicilar = self.kullanici_yoneticisi.kullanici_listesi()
        
        self.table.setRowCount(len(kullanicilar))
        
        for row, k in enumerate(kullanicilar):
            self.table.setItem(row, 0, QTableWidgetItem(str(k['kullanici_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(k['kullanici_adi']))
            self.table.setItem(row, 2, QTableWidgetItem(k['ad_soyad']))
            self.table.setItem(row, 3, QTableWidgetItem(k.get('email', '') or '-'))
            
            # Rol renklendirme
            rol_item = QTableWidgetItem(k['rol'])
            if k['rol'] == 'admin':
                rol_item.setForeground(Qt.GlobalColor.darkRed)
            elif k['rol'] == 'muhasebeci':
                rol_item.setForeground(Qt.GlobalColor.darkBlue)
            self.table.setItem(row, 4, rol_item)
            
            son_giris = k.get('son_giris', '')
            if son_giris:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(son_giris.replace('Z', '+00:00'))
                    son_giris = dt.strftime('%d.%m.%Y %H:%M')
                except:
                    pass
            self.table.setItem(row, 5, QTableWidgetItem(son_giris or '-'))
    
    def on_selection(self):
        """Seçim değiştiğinde"""
        selected = self.table.selectedItems()
        if selected:
            self.current_id = int(self.table.item(selected[0].row(), 0).text())
            self.duzenle_btn.setEnabled(True)
            # Admin koruması
            username = self.table.item(selected[0].row(), 1).text()
            self.sil_btn.setEnabled(username != 'admin')
        else:
            self.current_id = None
            self.duzenle_btn.setEnabled(False)
            self.sil_btn.setEnabled(False)
    
    def kullanici_ekle(self):
        """Yeni kullanıcı ekle"""
        form = KullaniciFormWidget(is_new=True)
        drawer = DrawerPanel(self, "Yeni Kullanıcı", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                result = self.kullanici_yoneticisi.kullanici_ekle(
                    kullanici_adi=data['kullanici_adi'],
                    sifre=data['sifre'],
                    ad_soyad=data['ad_soyad'],
                    email=data['email'],
                    rol=data['rol']
                )
                if result == -1:
                    MessageBox("Uyarı", "Bu kullanıcı adı zaten mevcut!", self).show()
                    return
                self.load_data()
                MessageBox("Başarılı", "Kullanıcı eklendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def kullanici_duzenle(self):
        """Kullanıcı düzenle"""
        if not self.current_id:
            return
        
        # Kullanıcı verisini al
        kullanicilar = self.kullanici_yoneticisi.kullanici_listesi()
        kullanici = next((k for k in kullanicilar if k['kullanici_id'] == self.current_id), None)
        
        if not kullanici:
            return
        
        form = KullaniciFormWidget(kullanici_data=kullanici, is_new=False)
        drawer = DrawerPanel(self, "Kullanıcı Düzenle", form)
        
        def on_submit():
            if not form.validate():
                return
            data = form.get_data()
            try:
                # Rol güncelle
                self.db.cursor.execute("""
                    UPDATE kullanicilar 
                    SET ad_soyad = ?, email = ?, rol = ?
                    WHERE kullanici_id = ?
                """, (data['ad_soyad'], data['email'], data['rol'], self.current_id))
                
                # Şifre güncelle (varsa)
                if data['sifre']:
                    self.kullanici_yoneticisi.sifre_degistir(self.current_id, data['sifre'])
                
                self.db.commit()
                self.load_data()
                MessageBox("Başarılı", "Kullanıcı güncellendi!", self).show()
                drawer.close()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()
        
        drawer.accepted.connect(on_submit)
        drawer.show()
    
    def kullanici_sil(self):
        """Kullanıcı sil"""
        if not self.current_id:
            return
        
        # Admin kontrolü
        username = self.table.item(self.table.currentRow(), 1).text()
        if username == 'admin':
            MessageBox("Uyarı", "Admin kullanıcısı silinemez!", self).show()
            return
        
        w = MessageBox("Kullanıcı Sil", "Bu kullanıcıyı silmek istediğinizden emin misiniz?", self)
        if w.exec():
            try:
                self.db.cursor.execute("DELETE FROM kullanicilar WHERE kullanici_id = ?", (self.current_id,))
                self.db.commit()
                self.load_data()
                self.current_id = None
                MessageBox("Başarılı", "Kullanıcı silindi!", self).show()
            except Exception as e:
                MessageBox("Hata", str(e), self).show()


