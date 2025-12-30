"""
BADER - Takım ve İzin Yönetimi
Kullanıcı ekleme, düzenleme ve detaylı izin yönetimi
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import (CardWidget, LineEdit, PasswordLineEdit, PushButton, 
                            PrimaryPushButton, MessageBox, TitleLabel, SubtitleLabel,
                            BodyLabel, CaptionLabel, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, IconWidget, StrongBodyLabel,
                            ComboBox, CheckBox, SwitchButton, TableWidget,
                            TransparentPushButton, ToolButton, Dialog)
from typing import Optional, Dict, List
import hashlib
import json


# ==================== İZİN TANIMLARI ====================

PERMISSIONS = {
    # Üye İşlemleri
    'uye_goruntule': {'label': 'Üyeleri Görüntüle', 'category': 'Üyeler', 'default': True},
    'uye_ekle': {'label': 'Üye Ekle', 'category': 'Üyeler', 'default': False},
    'uye_duzenle': {'label': 'Üye Düzenle', 'category': 'Üyeler', 'default': False},
    'uye_sil': {'label': 'Üye Sil', 'category': 'Üyeler', 'default': False},
    
    # Aidat İşlemleri
    'aidat_goruntule': {'label': 'Aidatları Görüntüle', 'category': 'Aidat', 'default': True},
    'aidat_tahsilat': {'label': 'Aidat Tahsilatı', 'category': 'Aidat', 'default': False},
    'aidat_duzenle': {'label': 'Aidat Düzenle', 'category': 'Aidat', 'default': False},
    
    # Gelir İşlemleri
    'gelir_goruntule': {'label': 'Gelirleri Görüntüle', 'category': 'Gelir', 'default': True},
    'gelir_ekle': {'label': 'Gelir Ekle', 'category': 'Gelir', 'default': False},
    'gelir_duzenle': {'label': 'Gelir Düzenle', 'category': 'Gelir', 'default': False},
    'gelir_sil': {'label': 'Gelir Sil', 'category': 'Gelir', 'default': False},
    
    # Gider İşlemleri
    'gider_goruntule': {'label': 'Giderleri Görüntüle', 'category': 'Gider', 'default': True},
    'gider_ekle': {'label': 'Gider Ekle', 'category': 'Gider', 'default': False},
    'gider_duzenle': {'label': 'Gider Düzenle', 'category': 'Gider', 'default': False},
    'gider_sil': {'label': 'Gider Sil', 'category': 'Gider', 'default': False},
    
    # Kasa İşlemleri
    'kasa_goruntule': {'label': 'Kasayı Görüntüle', 'category': 'Kasa', 'default': True},
    'kasa_islem': {'label': 'Kasa İşlemi Yap', 'category': 'Kasa', 'default': False},
    'virman': {'label': 'Virman İşlemi', 'category': 'Kasa', 'default': False},
    
    # Raporlar
    'rapor_goruntule': {'label': 'Raporları Görüntüle', 'category': 'Raporlar', 'default': True},
    'rapor_export': {'label': 'Rapor Dışa Aktar', 'category': 'Raporlar', 'default': False},
    
    # Belgeler
    'belge_goruntule': {'label': 'Belgeleri Görüntüle', 'category': 'Belgeler', 'default': True},
    'belge_ekle': {'label': 'Belge Ekle', 'category': 'Belgeler', 'default': False},
    'belge_sil': {'label': 'Belge Sil', 'category': 'Belgeler', 'default': False},
    'ocr_kullan': {'label': 'OCR Kullan', 'category': 'Belgeler', 'default': False},
    
    # Etkinlikler
    'etkinlik_goruntule': {'label': 'Etkinlikleri Görüntüle', 'category': 'Etkinlikler', 'default': True},
    'etkinlik_ekle': {'label': 'Etkinlik Ekle', 'category': 'Etkinlikler', 'default': False},
    'etkinlik_duzenle': {'label': 'Etkinlik Düzenle', 'category': 'Etkinlikler', 'default': False},
    
    # Yönetim
    'kullanici_yonetimi': {'label': 'Kullanıcı Yönetimi', 'category': 'Yönetim', 'default': False},
    'ayarlar': {'label': 'Ayarlar', 'category': 'Yönetim', 'default': False},
    'yedekleme': {'label': 'Yedekleme', 'category': 'Yönetim', 'default': False},
}

# Rol şablonları
ROLE_TEMPLATES = {
    'admin': {
        'label': 'Yönetici',
        'description': 'Tüm yetkilere sahip',
        'permissions': {k: True for k in PERMISSIONS.keys()}
    },
    'muhasebeci': {
        'label': 'Muhasebeci',
        'description': 'Mali işlemler için tam yetki',
        'permissions': {
            'uye_goruntule': True, 'uye_ekle': True, 'uye_duzenle': True,
            'aidat_goruntule': True, 'aidat_tahsilat': True, 'aidat_duzenle': True,
            'gelir_goruntule': True, 'gelir_ekle': True, 'gelir_duzenle': True, 'gelir_sil': True,
            'gider_goruntule': True, 'gider_ekle': True, 'gider_duzenle': True, 'gider_sil': True,
            'kasa_goruntule': True, 'kasa_islem': True, 'virman': True,
            'rapor_goruntule': True, 'rapor_export': True,
            'belge_goruntule': True, 'belge_ekle': True, 'ocr_kullan': True,
            'etkinlik_goruntule': True, 'etkinlik_ekle': True, 'etkinlik_duzenle': True,
        }
    },
    'sekreter': {
        'label': 'Sekreter',
        'description': 'Üye ve etkinlik işlemleri',
        'permissions': {
            'uye_goruntule': True, 'uye_ekle': True, 'uye_duzenle': True,
            'aidat_goruntule': True, 'aidat_tahsilat': True,
            'gelir_goruntule': True,
            'gider_goruntule': True,
            'kasa_goruntule': True,
            'rapor_goruntule': True,
            'belge_goruntule': True, 'belge_ekle': True,
            'etkinlik_goruntule': True, 'etkinlik_ekle': True, 'etkinlik_duzenle': True,
        }
    },
    'goruntuleyen': {
        'label': 'Görüntüleyen',
        'description': 'Sadece görüntüleme yetkisi',
        'permissions': {
            'uye_goruntule': True,
            'aidat_goruntule': True,
            'gelir_goruntule': True,
            'gider_goruntule': True,
            'kasa_goruntule': True,
            'rapor_goruntule': True,
            'belge_goruntule': True,
            'etkinlik_goruntule': True,
        }
    }
}


class TeamMemberDialog(QDialog):
    """Takım üyesi ekleme/düzenleme dialogu"""
    
    saved = pyqtSignal(dict)
    
    def __init__(self, db, member_data: dict = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.member_data = member_data
        self.is_edit = member_data is not None
        self.permission_checks = {}
        
        self.setWindowTitle("Kullanıcı Düzenle" if self.is_edit else "Yeni Kullanıcı")
        self.setFixedSize(550, 650)
        self.setModal(True)
        
        self.setup_ui()
        
        if self.is_edit:
            self._load_member_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık
        title = SubtitleLabel("Kullanıcı Düzenle" if self.is_edit else "Yeni Kullanıcı Ekle")
        layout.addWidget(title)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setSpacing(12)
        
        # Temel Bilgiler Card
        basic_card = CardWidget()
        basic_layout = QVBoxLayout()
        basic_layout.setContentsMargins(16, 16, 16, 16)
        basic_layout.setSpacing(10)
        
        basic_title = StrongBodyLabel("Temel Bilgiler")
        basic_layout.addWidget(basic_title)
        
        # Kullanıcı adı
        self.username_edit = LineEdit()
        self.username_edit.setPlaceholderText("Kullanıcı adı")
        if self.is_edit:
            self.username_edit.setEnabled(False)
        basic_layout.addWidget(BodyLabel("Kullanıcı Adı *"))
        basic_layout.addWidget(self.username_edit)
        
        # Ad Soyad
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("Ad Soyad")
        basic_layout.addWidget(BodyLabel("Ad Soyad *"))
        basic_layout.addWidget(self.name_edit)
        
        # E-posta
        self.email_edit = LineEdit()
        self.email_edit.setPlaceholderText("E-posta adresi")
        basic_layout.addWidget(BodyLabel("E-posta"))
        basic_layout.addWidget(self.email_edit)
        
        # Şifre
        if not self.is_edit:
            self.password_edit = PasswordLineEdit()
            self.password_edit.setPlaceholderText("Şifre (en az 6 karakter)")
            basic_layout.addWidget(BodyLabel("Şifre *"))
            basic_layout.addWidget(self.password_edit)
        else:
            # Şifre değiştirme checkbox
            self.change_password_check = CheckBox("Şifre Değiştir")
            self.change_password_check.stateChanged.connect(self._toggle_password_field)
            basic_layout.addWidget(self.change_password_check)
            
            self.password_edit = PasswordLineEdit()
            self.password_edit.setPlaceholderText("Yeni şifre")
            self.password_edit.hide()
            basic_layout.addWidget(self.password_edit)
        
        # Aktif/Pasif
        active_row = QHBoxLayout()
        active_row.addWidget(BodyLabel("Aktif"))
        active_row.addStretch()
        self.active_switch = SwitchButton()
        self.active_switch.setChecked(True)
        active_row.addWidget(self.active_switch)
        basic_layout.addLayout(active_row)
        
        basic_card.setLayout(basic_layout)
        form_layout.addWidget(basic_card)
        
        # Rol Seçimi Card
        role_card = CardWidget()
        role_layout = QVBoxLayout()
        role_layout.setContentsMargins(16, 16, 16, 16)
        role_layout.setSpacing(10)
        
        role_title = StrongBodyLabel("Rol Şablonu")
        role_layout.addWidget(role_title)
        
        self.role_combo = ComboBox()
        self.role_combo.addItem("Özel İzinler", "custom")
        for role_key, role_data in ROLE_TEMPLATES.items():
            self.role_combo.addItem(f"{role_data['label']} - {role_data['description']}", role_key)
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        role_layout.addWidget(self.role_combo)
        
        role_card.setLayout(role_layout)
        form_layout.addWidget(role_card)
        
        # İzinler Card
        perm_card = CardWidget()
        perm_layout = QVBoxLayout()
        perm_layout.setContentsMargins(16, 16, 16, 16)
        perm_layout.setSpacing(10)
        
        perm_title = StrongBodyLabel("Detaylı İzinler")
        perm_layout.addWidget(perm_title)
        
        # Kategorilere göre izinleri grupla
        categories = {}
        for perm_key, perm_data in PERMISSIONS.items():
            cat = perm_data['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((perm_key, perm_data))
        
        for category, perms in categories.items():
            cat_label = CaptionLabel(category)
            cat_label.setStyleSheet("color: #666; font-weight: bold;")
            perm_layout.addWidget(cat_label)
            
            for perm_key, perm_data in perms:
                check = CheckBox(perm_data['label'])
                check.setChecked(perm_data['default'])
                self.permission_checks[perm_key] = check
                perm_layout.addWidget(check)
            
            perm_layout.addSpacing(5)
        
        perm_card.setLayout(perm_layout)
        form_layout.addWidget(perm_card)
        
        form_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        cancel_btn = PushButton("İptal")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        btn_layout.addStretch()
        
        save_btn = PrimaryPushButton("Kaydet")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def _toggle_password_field(self, state):
        """Şifre alanını göster/gizle"""
        self.password_edit.setVisible(state == Qt.CheckState.Checked.value)
    
    def _on_role_changed(self, index):
        """Rol değiştiğinde izinleri güncelle"""
        role_key = self.role_combo.currentData()
        
        if role_key == 'custom':
            return
        
        if role_key in ROLE_TEMPLATES:
            role_perms = ROLE_TEMPLATES[role_key]['permissions']
            for perm_key, check in self.permission_checks.items():
                check.setChecked(role_perms.get(perm_key, False))
    
    def _load_member_data(self):
        """Mevcut üye verilerini yükle"""
        if not self.member_data:
            return
        
        self.username_edit.setText(self.member_data.get('kullanici_adi', ''))
        self.name_edit.setText(self.member_data.get('ad_soyad', ''))
        self.email_edit.setText(self.member_data.get('email', ''))
        self.active_switch.setChecked(self.member_data.get('aktif', 1) == 1)
        
        # İzinleri yükle
        permissions = self.member_data.get('izinler', {})
        if isinstance(permissions, str):
            try:
                permissions = json.loads(permissions)
            except:
                permissions = {}
        
        for perm_key, check in self.permission_checks.items():
            check.setChecked(permissions.get(perm_key, PERMISSIONS[perm_key]['default']))
    
    def _save(self):
        """Kullanıcıyı kaydet"""
        username = self.username_edit.text().strip()
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        
        if not username:
            MessageBox("Uyarı", "Kullanıcı adı boş bırakılamaz!", self).exec()
            return
        
        if not name:
            MessageBox("Uyarı", "Ad soyad boş bırakılamaz!", self).exec()
            return
        
        # Şifre kontrolü
        password = None
        if not self.is_edit:
            password = self.password_edit.text()
            if len(password) < 6:
                MessageBox("Uyarı", "Şifre en az 6 karakter olmalıdır!", self).exec()
                return
        elif hasattr(self, 'change_password_check') and self.change_password_check.isChecked():
            password = self.password_edit.text()
            if len(password) < 6:
                MessageBox("Uyarı", "Şifre en az 6 karakter olmalıdır!", self).exec()
                return
        
        # İzinleri topla
        permissions = {}
        for perm_key, check in self.permission_checks.items():
            permissions[perm_key] = check.isChecked()
        
        # Admin rolü belirle (tüm izinler açıksa)
        all_perms = all(permissions.values())
        role = 'admin' if all_perms else 'muhasebeci' if permissions.get('gelir_ekle') else 'görüntüleyici'
        
        try:
            if self.is_edit:
                # Güncelle
                if password:
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    self.db.cursor.execute("""
                        UPDATE kullanicilar 
                        SET ad_soyad = ?, email = ?, rol = ?, aktif = ?, 
                            izinler = ?, sifre_hash = ?
                        WHERE kullanici_id = ?
                    """, (name, email, role, 1 if self.active_switch.isChecked() else 0,
                          json.dumps(permissions), password_hash, self.member_data['kullanici_id']))
                else:
                    self.db.cursor.execute("""
                        UPDATE kullanicilar 
                        SET ad_soyad = ?, email = ?, rol = ?, aktif = ?, izinler = ?
                        WHERE kullanici_id = ?
                    """, (name, email, role, 1 if self.active_switch.isChecked() else 0,
                          json.dumps(permissions), self.member_data['kullanici_id']))
            else:
                # Yeni ekle
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                self.db.cursor.execute("""
                    INSERT INTO kullanicilar 
                    (kullanici_adi, sifre_hash, ad_soyad, email, rol, aktif, izinler)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                """, (username, password_hash, name, email, role, json.dumps(permissions)))
            
            self.db.commit()
            
            self.saved.emit({
                'username': username,
                'name': name,
                'email': email,
                'role': role,
                'permissions': permissions
            })
            
            self.accept()
            
        except Exception as e:
            MessageBox("Hata", f"Kaydetme hatası: {str(e)}", self).exec()


class TeamManagementWidget(QWidget):
    """Takım yönetimi widget'ı"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()
        self.load_users()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = SubtitleLabel("Takım Yönetimi")
        header.addWidget(title)
        
        header.addStretch()
        
        self.add_btn = PrimaryPushButton("Yeni Kullanıcı")
        self.add_btn.setIcon(FIF.ADD)
        self.add_btn.clicked.connect(self.add_user)
        header.addWidget(self.add_btn)
        
        layout.addLayout(header)
        
        # Açıklama
        desc = CaptionLabel("Takım üyelerinizi ekleyin ve izinlerini yönetin.")
        layout.addWidget(desc)
        
        # Kullanıcı listesi
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Kullanıcı Adı", "Ad Soyad", "E-posta", "Rol", "Durum", "İşlemler"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 120)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_users(self):
        """Kullanıcıları yükle"""
        self.table.setRowCount(0)
        
        try:
            self.db.cursor.execute("""
                SELECT kullanici_id, kullanici_adi, ad_soyad, email, rol, aktif, izinler
                FROM kullanicilar ORDER BY ad_soyad
            """)
            users = self.db.cursor.fetchall()
            
            for row_idx, user in enumerate(users):
                self.table.insertRow(row_idx)
                
                # Kullanıcı adı
                self.table.setItem(row_idx, 0, QTableWidgetItem(user['kullanici_adi']))
                
                # Ad soyad
                self.table.setItem(row_idx, 1, QTableWidgetItem(user['ad_soyad']))
                
                # E-posta
                self.table.setItem(row_idx, 2, QTableWidgetItem(user['email'] or ''))
                
                # Rol
                role_labels = {'admin': 'Yönetici', 'muhasebeci': 'Muhasebeci', 'görüntüleyici': 'Görüntüleyen'}
                self.table.setItem(row_idx, 3, QTableWidgetItem(role_labels.get(user['rol'], user['rol'])))
                
                # Durum
                status = "✅ Aktif" if user['aktif'] else "❌ Pasif"
                self.table.setItem(row_idx, 4, QTableWidgetItem(status))
                
                # İşlem butonları
                btn_widget = QWidget()
                btn_layout = QHBoxLayout()
                btn_layout.setContentsMargins(4, 4, 4, 4)
                btn_layout.setSpacing(4)
                
                edit_btn = ToolButton(FIF.EDIT)
                edit_btn.setFixedSize(28, 28)
                edit_btn.clicked.connect(lambda checked, u=dict(user): self.edit_user(u))
                btn_layout.addWidget(edit_btn)
                
                # Admin kendini silemesin
                if user['rol'] != 'admin':
                    delete_btn = ToolButton(FIF.DELETE)
                    delete_btn.setFixedSize(28, 28)
                    delete_btn.clicked.connect(lambda checked, uid=user['kullanici_id']: self.delete_user(uid))
                    btn_layout.addWidget(delete_btn)
                
                btn_widget.setLayout(btn_layout)
                self.table.setCellWidget(row_idx, 5, btn_widget)
                
        except Exception as e:
            print(f"Kullanıcı yükleme hatası: {e}")
    
    def add_user(self):
        """Yeni kullanıcı ekle"""
        dialog = TeamMemberDialog(self.db, parent=self)
        dialog.saved.connect(lambda d: self.load_users())
        dialog.exec()
    
    def edit_user(self, user_data: dict):
        """Kullanıcı düzenle"""
        dialog = TeamMemberDialog(self.db, member_data=user_data, parent=self)
        dialog.saved.connect(lambda d: self.load_users())
        dialog.exec()
    
    def delete_user(self, user_id: int):
        """Kullanıcı sil"""
        w = MessageBox(
            "Silme Onayı",
            "Bu kullanıcıyı silmek istediğinize emin misiniz?",
            self
        )
        if w.exec():
            try:
                self.db.cursor.execute("DELETE FROM kullanicilar WHERE kullanici_id = ?", (user_id,))
                self.db.commit()
                self.load_users()
                
                InfoBar.success(
                    title="Başarılı",
                    content="Kullanıcı silindi.",
                    parent=self,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000
                )
            except Exception as e:
                MessageBox("Hata", f"Silme hatası: {str(e)}", self).exec()


def has_permission(db, user_id: int, permission: str) -> bool:
    """Kullanıcının belirli bir izni var mı kontrol et"""
    try:
        db.cursor.execute("""
            SELECT rol, izinler FROM kullanicilar WHERE kullanici_id = ?
        """, (user_id,))
        result = db.cursor.fetchone()
        
        if not result:
            return False
        
        # Admin her şeyi yapabilir
        if result['rol'] == 'admin':
            return True
        
        # İzinleri kontrol et
        izinler = result['izinler']
        if izinler:
            try:
                izinler = json.loads(izinler) if isinstance(izinler, str) else izinler
                return izinler.get(permission, False)
            except:
                pass
        
        return False
    except:
        return False


def get_user_permissions(db, user_id: int) -> dict:
    """Kullanıcının tüm izinlerini al"""
    try:
        db.cursor.execute("""
            SELECT rol, izinler FROM kullanicilar WHERE kullanici_id = ?
        """, (user_id,))
        result = db.cursor.fetchone()
        
        if not result:
            return {}
        
        # Admin tüm izinlere sahip
        if result['rol'] == 'admin':
            return {k: True for k in PERMISSIONS.keys()}
        
        # İzinleri parse et
        izinler = result['izinler']
        if izinler:
            try:
                return json.loads(izinler) if isinstance(izinler, str) else izinler
            except:
                pass
        
        # Varsayılan izinler
        return {k: v['default'] for k, v in PERMISSIONS.items()}
    except:
        return {}
