"""
BADER Derneği - Giriş Ekranı ve Yetki Sistemi (Windows 11 Fluent Design)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from qfluentwidgets import (CardWidget, LineEdit, PushButton, PrimaryPushButton,
                            CheckBox, MessageBox, TitleLabel, SubtitleLabel,
                            BodyLabel, CaptionLabel, setTheme, Theme)
from database import Database
from models import KullaniciYoneticisi
from typing import Optional


class LoginWidget(QWidget):
    """Giriş ekranı"""
    
    login_successful = pyqtSignal(dict)  # Kullanıcı bilgileri
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.kullanici_yoneticisi = KullaniciYoneticisi(db)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("BADER - Giriş")
        self.setFixedSize(460, 540)
        setTheme(Theme.AUTO)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo ve başlık - Fluent Card
        logo_card = CardWidget()
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setSpacing(8)
        logo_layout.setContentsMargins(24, 24, 24, 24)
        
        logo_label = TitleLabel("BADER")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        subtitle = SubtitleLabel("Dernek Yönetim Sistemi")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(subtitle)
        
        logo_card.setLayout(logo_layout)
        layout.addWidget(logo_card)
        
        # Form alanları - Fluent Card
        form_card = CardWidget()
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(28, 28, 28, 28)
        
        # Hoşgeldiniz - Fluent typography
        welcome = SubtitleLabel("Hoş Geldiniz")
        form_layout.addWidget(welcome)
        
        info = BodyLabel("Devam etmek için giriş yapın")
        form_layout.addWidget(info)
        
        form_layout.addSpacing(10)
        
        # Kullanıcı adı - Fluent label
        user_label = BodyLabel("Kullanıcı Adı")
        form_layout.addWidget(user_label)
        
        self.username_edit = LineEdit()
        self.username_edit.setPlaceholderText("Kullanıcı adınızı girin")
        form_layout.addWidget(self.username_edit)
        
        # Şifre - Fluent style
        pass_label = BodyLabel("Şifre")
        form_layout.addWidget(pass_label)
        
        self.password_edit = LineEdit()
        self.password_edit.setPlaceholderText("Şifrenizi girin")
        self.password_edit.setEchoMode(LineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self.login)
        form_layout.addWidget(self.password_edit)
        
        # Beni hatırla - Fluent checkbox
        self.remember_check = CheckBox("Beni hatırla")
        form_layout.addWidget(self.remember_check)
        
        form_layout.addSpacing(8)
        
        # Giriş butonu - Fluent Primary
        self.login_btn = PrimaryPushButton("Giriş Yap")
        self.login_btn.clicked.connect(self.login)
        form_layout.addWidget(self.login_btn)
        
        form_card.setLayout(form_layout)
        layout.addWidget(form_card)
        
        # Varsayılan bilgi
        info_label = CaptionLabel("Varsayılan: admin / admin123")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Otomatik focus
        self.username_edit.setFocus()
        
    def login(self):
        """Giriş yap"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            MessageBox("Uyarı", "Kullanıcı adı ve şifre boş bırakılamaz!", self).show()
            return
        
        # Giriş kontrolü
        kullanici = self.kullanici_yoneticisi.giris_kontrol(username, password)
        
        if kullanici:
            self.login_successful.emit(kullanici)
        else:
            MessageBox("Hata", "Kullanıcı adı veya şifre hatalı!", self).show()
            self.password_edit.clear()
            self.password_edit.setFocus()


class SessionManager:
    """Oturum yöneticisi - Singleton"""
    
    _instance = None
    _current_user = None
    _permissions = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_user(self, user: dict):
        """Aktif kullanıcıyı ayarla"""
        self._current_user = user
        self._permissions = None  # Reset permissions
        
    def get_user(self) -> Optional[dict]:
        """Aktif kullanıcıyı al"""
        return self._current_user
    
    def get_user_id(self) -> Optional[int]:
        """Kullanıcı ID'si"""
        return self._current_user['kullanici_id'] if self._current_user else None
    
    def get_user_name(self) -> str:
        """Kullanıcı adı"""
        return self._current_user['ad_soyad'] if self._current_user else "Misafir"
    
    def get_role(self) -> str:
        """Kullanıcı rolü"""
        return self._current_user['rol'] if self._current_user else "görüntüleyici"
    
    def is_admin(self) -> bool:
        """Admin mi?"""
        return self.get_role() == 'admin'
    
    def is_muhasebeci(self) -> bool:
        """Muhasebeci veya üstü mü?"""
        return self.get_role() in ['admin', 'muhasebeci']
    
    def can_edit(self) -> bool:
        """Düzenleme yetkisi var mı?"""
        return self.get_role() in ['admin', 'muhasebeci']
    
    def can_delete(self) -> bool:
        """Silme yetkisi var mı?"""
        return self.get_role() == 'admin'
    
    def has_permission(self, permission: str) -> bool:
        """Belirli bir izni kontrol et"""
        if not self._current_user:
            return False
        
        # Admin her şeyi yapabilir
        if self.is_admin():
            return True
        
        # İzinleri yükle (cache)
        if self._permissions is None:
            self._load_permissions()
        
        return self._permissions.get(permission, False)
    
    def _load_permissions(self):
        """Kullanıcı izinlerini yükle"""
        import json
        self._permissions = {}
        
        if not self._current_user:
            return
        
        izinler = self._current_user.get('izinler')
        if izinler:
            try:
                self._permissions = json.loads(izinler) if isinstance(izinler, str) else izinler
            except:
                pass
    
    def logout(self):
        """Çıkış yap"""
        self._current_user = None
        self._permissions = None


# Global session instance
session = SessionManager()


