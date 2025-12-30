"""
BADER - Kurulum Sihirbazı ve Lisans Aktivasyonu
İlk açılış için lisans kodu ve admin şifresi kurulumu
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
                             QDialog, QApplication, QLabel)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap
from qfluentwidgets import (CardWidget, LineEdit, PasswordLineEdit, PushButton, 
                            PrimaryPushButton, MessageBox, TitleLabel, SubtitleLabel,
                            BodyLabel, CaptionLabel, InfoBar, InfoBarPosition,
                            ProgressRing, FluentIcon as FIF, IconWidget, StrongBodyLabel,
                            ProgressBar, CheckBox)
from typing import Optional, Dict
import hashlib
import json
import os


class SetupWorker(QThread):
    """Arka plan işlemleri için thread"""
    finished = pyqtSignal(bool, str, object)
    
    def __init__(self, task_func, *args):
        super().__init__()
        self.task_func = task_func
        self.args = args
    
    def run(self):
        try:
            result = self.task_func(*self.args)
            if isinstance(result, tuple):
                if len(result) >= 3:
                    self.finished.emit(result[0], result[1], result[2])
                else:
                    self.finished.emit(result[0], result[1], None)
            else:
                self.finished.emit(True, str(result), None)
        except Exception as e:
            self.finished.emit(False, str(e), None)


class SetupWizard(QDialog):
    """
    İlk Kurulum Sihirbazı
    1. Hoşgeldin ekranı
    2. Lisans aktivasyonu
    3. Admin hesabı oluşturma
    4. Kurum bilgileri
    5. Tamamlandı
    """
    
    setup_completed = pyqtSignal(dict)  # Admin bilgileri
    
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.worker = None
        self.license_data = None
        self.admin_data = None
        
        self.setWindowTitle("BADER - Kurulum Sihirbazı")
        self.setFixedSize(600, 550)
        self.setModal(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget for pages
        self.stack = QStackedWidget()
        
        # Pages
        self.stack.addWidget(self._create_welcome_page())      # 0
        self.stack.addWidget(self._create_license_page())      # 1
        self.stack.addWidget(self._create_admin_page())        # 2
        self.stack.addWidget(self._create_org_page())          # 3
        self.stack.addWidget(self._create_complete_page())     # 4
        
        layout.addWidget(self.stack)
        self.setLayout(layout)
    
    def _create_page_container(self, title: str, subtitle: str, icon=None) -> tuple:
        """Sayfa container'ı oluştur"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        if icon:
            icon_widget = IconWidget(icon)
            icon_widget.setFixedSize(48, 48)
            header.addWidget(icon_widget)
        
        title_layout = QVBoxLayout()
        title_label = TitleLabel(title)
        subtitle_label = BodyLabel(subtitle)
        subtitle_label.setWordWrap(True)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header.addLayout(title_layout)
        header.addStretch()
        
        layout.addLayout(header)
        layout.addSpacing(10)
        
        # Content area
        content = CardWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        content.setLayout(content_layout)
        layout.addWidget(content)
        
        # Button area
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        page.setLayout(layout)
        return page, content_layout, button_layout
    
    def _create_welcome_page(self):
        """Hoşgeldin sayfası"""
        page, content, buttons = self._create_page_container(
            "BADER'e Hoş Geldiniz",
            "Dernek Yönetim Sistemi kurulum sihirbazına hoş geldiniz.",
            FIF.HOME
        )
        
        # Welcome message
        welcome_text = StrongBodyLabel(
            "Bu sihirbaz size aşağıdaki adımlarda yardımcı olacak:"
        )
        content.addWidget(welcome_text)
        
        steps = [
            "✅ Lisans anahtarınızı aktifleştirme",
            "✅ Yönetici hesabı oluşturma",
            "✅ Kurum bilgilerini girme"
        ]
        
        for step in steps:
            label = BodyLabel(step)
            content.addWidget(label)
        
        content.addStretch()
        
        info = CaptionLabel(
            "Kurulum tamamlandıktan sonra sistemi kullanmaya başlayabilirsiniz."
        )
        content.addWidget(info)
        
        # Buttons
        buttons.addStretch()
        next_btn = PrimaryPushButton("Başla")
        next_btn.setFixedWidth(120)
        next_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        buttons.addWidget(next_btn)
        
        return page
    
    def _create_license_page(self):
        """Lisans aktivasyon sayfası"""
        page, content, buttons = self._create_page_container(
            "Lisans Aktivasyonu",
            "Ürünü kullanmak için lisans anahtarınızı girin.",
            FIF.CERTIFICATE
        )
        
        # Server URL
        url_label = CaptionLabel("Server URL")
        content.addWidget(url_label)
        
        self.server_url_edit = LineEdit()
        self.server_url_edit.setPlaceholderText("http://157.90.154.48:8080/api")
        self.server_url_edit.setText("http://157.90.154.48:8080/api")
        content.addWidget(self.server_url_edit)
        
        # License Key
        key_label = BodyLabel("Lisans Anahtarı")
        content.addWidget(key_label)
        
        self.license_key_edit = LineEdit()
        self.license_key_edit.setPlaceholderText("BADER-XXXX-XXXX veya API Key")
        content.addWidget(self.license_key_edit)
        
        # Status
        self.license_status = CaptionLabel("")
        self.license_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.addWidget(self.license_status)
        
        # Progress
        self.license_progress = ProgressRing()
        self.license_progress.setFixedSize(30, 30)
        self.license_progress.hide()
        content.addWidget(self.license_progress, alignment=Qt.AlignmentFlag.AlignCenter)
        
        content.addStretch()
        
        # Buttons
        back_btn = PushButton("Geri")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        buttons.addWidget(back_btn)
        
        buttons.addStretch()
        
        self.license_next_btn = PrimaryPushButton("Aktifleştir")
        self.license_next_btn.setFixedWidth(120)
        self.license_next_btn.clicked.connect(self._activate_license)
        buttons.addWidget(self.license_next_btn)
        
        return page
    
    def _create_admin_page(self):
        """Admin hesabı oluşturma sayfası"""
        page, content, buttons = self._create_page_container(
            "Yönetici Hesabı",
            "Sistem yöneticisi hesabını oluşturun.",
            FIF.PEOPLE
        )
        
        # Admin username
        user_label = BodyLabel("Kullanıcı Adı")
        content.addWidget(user_label)
        
        self.admin_username_edit = LineEdit()
        self.admin_username_edit.setPlaceholderText("admin")
        self.admin_username_edit.setText("admin")
        content.addWidget(self.admin_username_edit)
        
        # Admin full name
        name_label = BodyLabel("Ad Soyad")
        content.addWidget(name_label)
        
        self.admin_name_edit = LineEdit()
        self.admin_name_edit.setPlaceholderText("Sistem Yöneticisi")
        content.addWidget(self.admin_name_edit)
        
        # Admin email
        email_label = BodyLabel("E-posta (Opsiyonel)")
        content.addWidget(email_label)
        
        self.admin_email_edit = LineEdit()
        self.admin_email_edit.setPlaceholderText("admin@dernek.com")
        content.addWidget(self.admin_email_edit)
        
        # Password
        pass_label = BodyLabel("Şifre")
        content.addWidget(pass_label)
        
        self.admin_password_edit = PasswordLineEdit()
        self.admin_password_edit.setPlaceholderText("En az 6 karakter")
        content.addWidget(self.admin_password_edit)
        
        # Confirm Password
        confirm_label = BodyLabel("Şifre Tekrar")
        content.addWidget(confirm_label)
        
        self.admin_confirm_edit = PasswordLineEdit()
        self.admin_confirm_edit.setPlaceholderText("Şifreyi tekrar girin")
        content.addWidget(self.admin_confirm_edit)
        
        content.addStretch()
        
        # Buttons
        back_btn = PushButton("Geri")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        buttons.addWidget(back_btn)
        
        buttons.addStretch()
        
        next_btn = PrimaryPushButton("Devam")
        next_btn.setFixedWidth(120)
        next_btn.clicked.connect(self._validate_admin)
        buttons.addWidget(next_btn)
        
        return page
    
    def _create_org_page(self):
        """Kurum bilgileri sayfası"""
        page, content, buttons = self._create_page_container(
            "Kurum Bilgileri",
            "Derneğinizin temel bilgilerini girin.",
            FIF.LIBRARY
        )
        
        # Kurum adı
        name_label = BodyLabel("Dernek/Kurum Adı")
        content.addWidget(name_label)
        
        self.org_name_edit = LineEdit()
        self.org_name_edit.setPlaceholderText("Örnek: ABC Derneği")
        content.addWidget(self.org_name_edit)
        
        # Vergi No
        tax_label = BodyLabel("Vergi Numarası (Opsiyonel)")
        content.addWidget(tax_label)
        
        self.org_tax_edit = LineEdit()
        self.org_tax_edit.setPlaceholderText("XXXXXXXXXX")
        content.addWidget(self.org_tax_edit)
        
        # Adres
        addr_label = BodyLabel("Adres (Opsiyonel)")
        content.addWidget(addr_label)
        
        self.org_address_edit = LineEdit()
        self.org_address_edit.setPlaceholderText("Dernek adresi")
        content.addWidget(self.org_address_edit)
        
        # Telefon
        phone_label = BodyLabel("Telefon (Opsiyonel)")
        content.addWidget(phone_label)
        
        self.org_phone_edit = LineEdit()
        self.org_phone_edit.setPlaceholderText("0XXX XXX XX XX")
        content.addWidget(self.org_phone_edit)
        
        content.addStretch()
        
        # Buttons
        back_btn = PushButton("Geri")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        buttons.addWidget(back_btn)
        
        buttons.addStretch()
        
        next_btn = PrimaryPushButton("Kurulumu Tamamla")
        next_btn.setFixedWidth(150)
        next_btn.clicked.connect(self._complete_setup)
        buttons.addWidget(next_btn)
        
        return page
    
    def _create_complete_page(self):
        """Kurulum tamamlandı sayfası"""
        page, content, buttons = self._create_page_container(
            "Kurulum Tamamlandı!",
            "BADER başarıyla kuruldu ve kullanıma hazır.",
            FIF.ACCEPT
        )
        
        # Success message
        success_text = StrongBodyLabel("🎉 Tebrikler!")
        success_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.addWidget(success_text)
        
        info_text = BodyLabel(
            "Sistem kullanıma hazır. Şimdi giriş yaparak\n"
            "uygulamayı kullanmaya başlayabilirsiniz."
        )
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.addWidget(info_text)
        
        content.addSpacing(20)
        
        # Summary
        self.summary_label = CaptionLabel("")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.addWidget(self.summary_label)
        
        content.addStretch()
        
        # Buttons
        buttons.addStretch()
        
        finish_btn = PrimaryPushButton("Giriş Yap")
        finish_btn.setFixedWidth(150)
        finish_btn.clicked.connect(self._finish_setup)
        buttons.addWidget(finish_btn)
        
        buttons.addStretch()
        
        return page
    
    def _activate_license(self):
        """Lisans aktivasyonu"""
        license_key = self.license_key_edit.text().strip()
        server_url = self.server_url_edit.text().strip()
        
        if not license_key:
            MessageBox("Uyarı", "Lisans anahtarı boş bırakılamaz!", self).exec()
            return
        
        self.license_next_btn.setEnabled(False)
        self.license_progress.show()
        self.license_status.setText("Aktifleştiriliyor...")
        
        # Server'a bağlan
        from server_client import get_server_client
        client = get_server_client()
        
        if server_url:
            client.set_server_url(server_url)
        
        self.worker = SetupWorker(client.activate_license, license_key)
        self.worker.finished.connect(self._on_activation_complete)
        self.worker.start()
    
    def _on_activation_complete(self, success, message, data):
        self.license_next_btn.setEnabled(True)
        self.license_progress.hide()
        
        if success:
            self.license_status.setText("✅ Aktivasyon başarılı!")
            self.license_status.setStyleSheet("color: #2ECC71;")
            self.license_data = data
            
            # Eğer license_data'da müşteri adı varsa, kurum adına koy
            if data and data.get('name'):
                self.org_name_edit.setText(data['name'])
            
            # Sonraki sayfaya geç
            QTimer.singleShot(500, lambda: self.stack.setCurrentIndex(2))
        else:
            self.license_status.setText("❌ " + message)
            self.license_status.setStyleSheet("color: #E74C3C;")
    
    def _validate_admin(self):
        """Admin bilgilerini doğrula"""
        username = self.admin_username_edit.text().strip()
        name = self.admin_name_edit.text().strip()
        password = self.admin_password_edit.text()
        confirm = self.admin_confirm_edit.text()
        
        if not username:
            MessageBox("Uyarı", "Kullanıcı adı boş bırakılamaz!", self).exec()
            return
        
        if not name:
            MessageBox("Uyarı", "Ad soyad boş bırakılamaz!", self).exec()
            return
        
        if len(password) < 6:
            MessageBox("Uyarı", "Şifre en az 6 karakter olmalıdır!", self).exec()
            return
        
        if password != confirm:
            MessageBox("Uyarı", "Şifreler eşleşmiyor!", self).exec()
            return
        
        self.admin_data = {
            'username': username,
            'name': name,
            'email': self.admin_email_edit.text().strip(),
            'password': password
        }
        
        self.stack.setCurrentIndex(3)
    
    def _complete_setup(self):
        """Kurulumu tamamla"""
        org_name = self.org_name_edit.text().strip()
        
        if not org_name:
            MessageBox("Uyarı", "Kurum adı boş bırakılamaz!", self).exec()
            return
        
        # Veritabanına kaydet
        try:
            if self.db:
                # Sistem ayarlarını kaydet
                self._save_system_settings({
                    'org_name': org_name,
                    'org_tax': self.org_tax_edit.text().strip(),
                    'org_address': self.org_address_edit.text().strip(),
                    'org_phone': self.org_phone_edit.text().strip(),
                    'setup_completed': True,
                    'license_key': self.license_data.get('customer_id') if self.license_data else '',
                    'api_key': self.license_data.get('api_key') if self.license_data else ''
                })
                
                # Admin kullanıcısını oluştur
                self._create_admin_user()
            
            # Özet göster
            self.summary_label.setText(
                f"Kurum: {org_name}\n"
                f"Yönetici: {self.admin_data['username']}"
            )
            
            self.stack.setCurrentIndex(4)
            
        except Exception as e:
            MessageBox("Hata", f"Kurulum hatası: {str(e)}", self).exec()
    
    def _save_system_settings(self, settings: dict):
        """Sistem ayarlarını kaydet"""
        if not self.db:
            return
        
        # Ayarlar tablosu yoksa oluştur
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sistem_ayarlari (
                anahtar TEXT PRIMARY KEY,
                deger TEXT,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        for key, value in settings.items():
            self.db.cursor.execute("""
                INSERT OR REPLACE INTO sistem_ayarlari (anahtar, deger, guncelleme_tarihi)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value) if isinstance(value, (dict, list, bool)) else str(value)))
        
        self.db.commit()
    
    def _create_admin_user(self):
        """Admin kullanıcısını oluştur"""
        if not self.db or not self.admin_data:
            return
        
        # Önce mevcut admin varsa sil (ilk kurulum)
        self.db.cursor.execute("DELETE FROM kullanicilar WHERE rol = 'admin'")
        
        # Yeni admin oluştur
        password_hash = hashlib.sha256(self.admin_data['password'].encode()).hexdigest()
        
        self.db.cursor.execute("""
            INSERT INTO kullanicilar (kullanici_adi, sifre_hash, ad_soyad, email, rol, aktif)
            VALUES (?, ?, ?, ?, 'admin', 1)
        """, (
            self.admin_data['username'],
            password_hash,
            self.admin_data['name'],
            self.admin_data['email']
        ))
        
        self.db.commit()
    
    def _finish_setup(self):
        """Kurulumu bitir ve çık"""
        self.setup_completed.emit(self.admin_data or {})
        self.accept()


def check_setup_required(db) -> bool:
    """Kurulum gerekli mi kontrol et"""
    try:
        db.cursor.execute("""
            SELECT deger FROM sistem_ayarlari WHERE anahtar = 'setup_completed'
        """)
        result = db.cursor.fetchone()
        if result:
            return not (result[0] == 'True' or result[0] == 'true' or result[0] == '1')
        return True
    except:
        return True


def get_system_setting(db, key: str, default=None):
    """Sistem ayarını al"""
    try:
        db.cursor.execute("""
            SELECT deger FROM sistem_ayarlari WHERE anahtar = ?
        """, (key,))
        result = db.cursor.fetchone()
        if result:
            return result[0]
        return default
    except:
        return default
