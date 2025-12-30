#!/usr/bin/env python3
"""
BADER Derneği - Aidat & Kasa Yönetim Sistemi
Ana Program - Polaris Design System
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont, QFontDatabase
from main_window import MainWindow
from ui_styles import MODERN_STYLESHEET


def get_resource_path(relative_path):
    """PyInstaller için doğru dosya yolunu al"""
    try:
        # PyInstaller bundle içinde
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python ortamında
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def main():
    """Ana fonksiyon"""
    # High DPI desteği - PyQt5 için
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Uygulama oluştur
    app = QApplication(sys.argv)
    
    # Uygulama bilgileri
    app.setApplicationName("BADER Derneği")
    app.setOrganizationName("BADER")
    app.setApplicationVersion("3.0.0")
    
    # Platform bazlı font seçimi
    if sys.platform == "darwin":  # macOS
        font_family = "SF Pro Text"
        fallback = "Helvetica Neue"
    elif sys.platform == "win32":  # Windows
        font_family = "Segoe UI"
        fallback = "Arial"
    else:  # Linux
        font_family = "Ubuntu"
        fallback = "DejaVu Sans"
    
    # Font ayarla
    font = QFont()
    font.setFamily(font_family)
    font.setPointSize(10)
    font.setStyleStrategy(QFont.PreferAntialias)
    
    # Eğer font bulunamazsa fallback kullan
    if not QFontDatabase().hasFamily(font_family):
        font.setFamily(fallback)
    
    app.setFont(font)
    
    # ⭐ STYLESHEET UYGULA - BU ÇOK ÖNEMLİ!
    app.setStyleSheet(MODERN_STYLESHEET)
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.showMaximized()
    
    # Uygulama döngüsü
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

