"""
BADER - Windows 11 Fluent Design DEMO
Önizleme: PyQt6-Fluent-Widgets ile lüks görünüm
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from qfluentwidgets import (PushButton, PrimaryPushButton, LineEdit, 
                            CardWidget, TitleLabel, BodyLabel,
                            FluentWindow, NavigationItemPosition)
from qfluentwidgets import FluentIcon as FIF


class FluentDemo(FluentWindow):
    """Windows 11 Fluent Design Demo"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BADER - Windows 11 Fluent Design")
        self.resize(1200, 700)
        
        # Dashboard sayfası
        self.dashboard_interface = QWidget()
        self.setup_dashboard()
        
        # Navigation items ekle
        self.addSubInterface(self.dashboard_interface, FIF.HOME, 'Dashboard')
        
        # Acrylic blur effect (Windows 11)
        self.setMicaEffectEnabled(True)
        
    def setup_dashboard(self):
        """Dashboard ekranını kur"""
        # Card ile örnek
        card = CardWidget(self.dashboard_interface)
        card.setGeometry(30, 30, 300, 200)
        
        # Title
        title = TitleLabel("BADER Dernek Sistemi", card)
        title.move(20, 20)
        
        # Info
        info = BodyLabel("Windows 11 Fluent Design\nUltra Premium Görünüm", card)
        info.move(20, 60)
        
        # Primary button
        btn = PrimaryPushButton("Devam Et", card)
        btn.move(20, 130)
        btn.setFixedWidth(150)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Windows 11 tema
    from qfluentwidgets import setTheme, Theme
    setTheme(Theme.AUTO)
    
    window = FluentDemo()
    window.show()
    sys.exit(app.exec())
