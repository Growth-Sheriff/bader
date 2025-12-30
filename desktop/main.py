#!/usr/bin/env python3
"""
BADER Derneği - Aidat & Kasa Yönetim Sistemi
Ana Program - QFluentWidgets + Polaris Design
"""

import sys
import os

# PyQt5 import
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont, QFontDatabase

# QFluentWidgets tema
from qfluentwidgets import setTheme, Theme, setThemeColor
from qfluentwidgets import FluentWindow

from main_window import MainWindow


def get_resource_path(relative_path):
    """PyInstaller için doğru dosya yolunu al"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    """Ana fonksiyon"""
    # High DPI desteği
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Uygulama oluştur
    app = QApplication(sys.argv)
    
    # Uygulama bilgileri
    app.setApplicationName("BADER Derneği")
    app.setOrganizationName("BADER")
    app.setApplicationVersion("3.0.0")
    
    # QFluentWidgets tema ayarları
    setTheme(Theme.LIGHT)
    setThemeColor("#303030")  # Polaris primary color
    
    # Platform bazlı font
    if sys.platform == "darwin":
        font_family = "SF Pro Text"
    elif sys.platform == "win32":
        font_family = "Segoe UI"
    else:
        font_family = "Ubuntu"
    
    font = QFont(font_family, 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.showMaximized()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

