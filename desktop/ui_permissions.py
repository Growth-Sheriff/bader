"""
BADER - İzin Yönetimi Modülü
Merkezi izin kontrolü ve UI bileşen gizleme
"""

from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtGui import QAction
from typing import Optional, List, Callable
from functools import wraps


# ==================== İZİN TANIMLARI ====================

PERMISSIONS = {
    # Üye İzinleri
    'uye_goruntule': 'Üyeleri görüntüle',
    'uye_ekle': 'Yeni üye ekle',
    'uye_duzenle': 'Üye bilgilerini düzenle',
    'uye_sil': 'Üye sil',
    
    # Aidat İzinleri
    'aidat_goruntule': 'Aidatları görüntüle',
    'aidat_tahsilat': 'Aidat tahsilat işlemi',
    'aidat_duzenle': 'Aidat bilgilerini düzenle',
    
    # Gelir İzinleri
    'gelir_goruntule': 'Gelirleri görüntüle',
    'gelir_ekle': 'Yeni gelir ekle',
    'gelir_duzenle': 'Gelir düzenle',
    'gelir_sil': 'Gelir sil',
    
    # Gider İzinleri
    'gider_goruntule': 'Giderleri görüntüle',
    'gider_ekle': 'Yeni gider ekle',
    'gider_duzenle': 'Gider düzenle',
    'gider_sil': 'Gider sil',
    
    # Kasa İzinleri
    'kasa_goruntule': 'Kasaları görüntüle',
    'kasa_islem': 'Kasa işlemi yap',
    'virman': 'Virman transferi',
    
    # Rapor İzinleri
    'rapor_goruntule': 'Raporları görüntüle',
    'rapor_export': 'Rapor dışa aktar',
    
    # Belge İzinleri
    'belge_goruntule': 'Belgeleri görüntüle',
    'belge_ekle': 'Belge ekle',
    'belge_sil': 'Belge sil',
    'ocr_kullan': 'OCR kullan',
    
    # Etkinlik İzinleri
    'etkinlik_goruntule': 'Etkinlikleri görüntüle',
    'etkinlik_ekle': 'Etkinlik ekle',
    'etkinlik_duzenle': 'Etkinlik düzenle',
    
    # Yönetim İzinleri
    'kullanici_yonetimi': 'Kullanıcı yönetimi',
    'ayarlar': 'Sistem ayarları',
    'yedekleme': 'Yedekleme işlemleri',
}


# ==================== ROL ŞABLONLARI ====================

ROLE_TEMPLATES = {
    'admin': {perm: True for perm in PERMISSIONS.keys()},
    
    'muhasebeci': {
        'uye_goruntule': True, 'uye_ekle': True, 'uye_duzenle': True, 'uye_sil': False,
        'aidat_goruntule': True, 'aidat_tahsilat': True, 'aidat_duzenle': True,
        'gelir_goruntule': True, 'gelir_ekle': True, 'gelir_duzenle': True, 'gelir_sil': True,
        'gider_goruntule': True, 'gider_ekle': True, 'gider_duzenle': True, 'gider_sil': True,
        'kasa_goruntule': True, 'kasa_islem': True, 'virman': True,
        'rapor_goruntule': True, 'rapor_export': True,
        'belge_goruntule': True, 'belge_ekle': True, 'belge_sil': False, 'ocr_kullan': True,
        'etkinlik_goruntule': True, 'etkinlik_ekle': False, 'etkinlik_duzenle': False,
        'kullanici_yonetimi': False, 'ayarlar': False, 'yedekleme': True,
    },
    
    'sekreter': {
        'uye_goruntule': True, 'uye_ekle': True, 'uye_duzenle': True, 'uye_sil': False,
        'aidat_goruntule': True, 'aidat_tahsilat': True, 'aidat_duzenle': False,
        'gelir_goruntule': True, 'gelir_ekle': False, 'gelir_duzenle': False, 'gelir_sil': False,
        'gider_goruntule': True, 'gider_ekle': False, 'gider_duzenle': False, 'gider_sil': False,
        'kasa_goruntule': True, 'kasa_islem': False, 'virman': False,
        'rapor_goruntule': True, 'rapor_export': True,
        'belge_goruntule': True, 'belge_ekle': True, 'belge_sil': False, 'ocr_kullan': True,
        'etkinlik_goruntule': True, 'etkinlik_ekle': True, 'etkinlik_duzenle': True,
        'kullanici_yonetimi': False, 'ayarlar': False, 'yedekleme': False,
    },
    
    'goruntuleyen': {
        'uye_goruntule': True, 'uye_ekle': False, 'uye_duzenle': False, 'uye_sil': False,
        'aidat_goruntule': True, 'aidat_tahsilat': False, 'aidat_duzenle': False,
        'gelir_goruntule': True, 'gelir_ekle': False, 'gelir_duzenle': False, 'gelir_sil': False,
        'gider_goruntule': True, 'gider_ekle': False, 'gider_duzenle': False, 'gider_sil': False,
        'kasa_goruntule': True, 'kasa_islem': False, 'virman': False,
        'rapor_goruntule': True, 'rapor_export': False,
        'belge_goruntule': True, 'belge_ekle': False, 'belge_sil': False, 'ocr_kullan': False,
        'etkinlik_goruntule': True, 'etkinlik_ekle': False, 'etkinlik_duzenle': False,
        'kullanici_yonetimi': False, 'ayarlar': False, 'yedekleme': False,
    },
}


# ==================== İZİN KONTROLÜ ====================

def check_permission(permission: str) -> bool:
    """Aktif kullanıcının iznini kontrol et"""
    from ui_login import session
    return session.has_permission(permission)


def require_permission(permission: str):
    """Dekoratör: Fonksiyon çağrılmadan önce izin kontrolü"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if check_permission(permission):
                return func(*args, **kwargs)
            else:
                from qfluentwidgets import MessageBox
                # args[0] genellikle self (widget)
                parent = args[0] if args and hasattr(args[0], 'window') else None
                MessageBox(
                    "Yetki Hatası",
                    f"Bu işlem için yetkiniz bulunmamaktadır.\nGerekli izin: {PERMISSIONS.get(permission, permission)}",
                    parent
                ).exec()
                return None
        return wrapper
    return decorator


def apply_permissions(widget: QWidget, permission_map: dict):
    """
    Widget'taki butonlara izin kontrolü uygula
    
    permission_map = {
        'ekle_btn': 'uye_ekle',
        'sil_btn': 'uye_sil',
    }
    """
    for attr_name, permission in permission_map.items():
        if hasattr(widget, attr_name):
            btn = getattr(widget, attr_name)
            if isinstance(btn, (QPushButton, QAction)):
                has_perm = check_permission(permission)
                btn.setVisible(has_perm)
                btn.setEnabled(has_perm)


def hide_if_no_permission(widget: QWidget, permission: str):
    """Widget'ı izin yoksa gizle"""
    if not check_permission(permission):
        widget.hide()


def disable_if_no_permission(widget: QWidget, permission: str):
    """Widget'ı izin yoksa devre dışı bırak"""
    if not check_permission(permission):
        widget.setEnabled(False)


# ==================== MIXIN SINIFI ====================

class PermissionMixin:
    """İzin kontrolü için mixin sınıfı"""
    
    permission_map = {}  # Alt sınıflar bunu override edecek
    
    def apply_button_permissions(self):
        """Butonlara izin kontrolü uygula"""
        apply_permissions(self, self.permission_map)
    
    def check_perm(self, permission: str) -> bool:
        """İzin kontrolü"""
        return check_permission(permission)
    
    def require_perm(self, permission: str, action_name: str = "bu işlem") -> bool:
        """
        İzin kontrolü yap, yoksa uyarı göster
        True: İzin var, devam et
        False: İzin yok, durdur
        """
        if check_permission(permission):
            return True
        
        from qfluentwidgets import MessageBox
        MessageBox(
            "Yetki Hatası",
            f"{action_name} için yetkiniz bulunmamaktadır.",
            self if isinstance(self, QWidget) else None
        ).exec()
        return False
