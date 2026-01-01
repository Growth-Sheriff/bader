"""
BADER Derneği - Dashboard & Raporlama UI
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QScrollArea, QFrame,
                             QGridLayout, QSizePolicy, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Matplotlib için güvenli import
MATPLOTLIB_AVAILABLE = False
FigureCanvas = None

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except Exception as e:
    print(f"Matplotlib yüklenemedi: {e}")
    # Mock FigureCanvas - grafik gösterilemediğinde basit placeholder
    class FigureCanvas(QFrame):
        def __init__(self, figure=None):
            super().__init__()
            layout = QVBoxLayout(self)
            label = QLabel("📊 Grafik yüklenemedi")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        def draw(self):
            pass

from qfluentwidgets import (PushButton, PrimaryPushButton, ComboBox, 
                            SpinBox, TitleLabel, SubtitleLabel, BodyLabel)
from database import Database
from models import RaporYoneticisi, KasaYoneticisi, AidatYoneticisi, EtkinlikYoneticisi
from datetime import datetime


class StatCard(QFrame):
    """🎨 POLARIS STAT CARD - Premium Shopify Style"""
    
    def __init__(self, baslik: str, deger: str, border_color: str = "#303030"):
        super().__init__()
        self.setup_ui(baslik, deger, border_color)
        
    def setup_ui(self, baslik, deger, border_color):
        # Polaris Card - Clean borders, subtle shadow
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E3E3E3;
                border-left: 4px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        # Ana layout - Polaris spacing
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)
        
        # Başlık (üstte, Fluent typography)
        baslik_label = BodyLabel(baslik.upper())
        baslik_label.setStyleSheet("""
            color: #616161;
            font-size: 11px;
            font-weight: 650;
            letter-spacing: 0.8px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(baslik_label)
        
        # Değer (büyük, Fluent bold)
        deger_label = TitleLabel(deger)
        deger_label.setStyleSheet("""
            color: #1A1A1A;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.8px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(deger_label)
        
        self.setLayout(layout)
        self.setFixedSize(220, 100)  # Polaris proportions


class ChartWidget(QWidget):
    """Grafik widget (Matplotlib) - KOMPAKT Vuexy Style"""
    
    def __init__(self, parent=None, chart_type="bar"):
        super().__init__(parent)
        
        # Matplotlib yoksa placeholder göster
        if not MATPLOTLIB_AVAILABLE:
            layout = QVBoxLayout(self)
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #E3E3E3;
                    border-radius: 12px;
                    min-height: 150px;
                }
            """)
            frame_layout = QVBoxLayout(frame)
            label = QLabel("📊 Grafik için matplotlib gerekli")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 12px;")
            frame_layout.addWidget(label)
            layout.addWidget(frame)
            return
        
        # Chart tipine göre KOMPAKT boyutlandırma
        if chart_type == "bar_compact":
            figsize = (5, 2.8)
        elif chart_type == "horizontal_bar_compact":
            figsize = (12, 2.5)
        elif chart_type == "donut_compact":
            figsize = (3.5, 2.8)
        else:
            figsize = (5, 3)
            
        self.figure = Figure(figsize=figsize, dpi=100, facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Grafik container frame - Polaris Card
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E3E3E3;
                border-radius: 12px;
                border: 1px solid rgba(47, 43, 61, 0.08);
            }
        """)
        
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.addWidget(self.canvas)
        frame.setLayout(frame_layout)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(frame)
        self.setLayout(layout)
        
    def plot_gelir_gider(self, aylar, gelirler, giderler):
        """Gelir-Gider karşılaştırma grafiği - KOMPAKT"""
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'figure'):
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        x = range(len(aylar))
        width = 0.32
        
        # Bar'lar - KOMPAKT
        bars1 = ax.bar([i - width/2 for i in x], gelirler, width, label='Gelir', 
                       color='#28c76f', alpha=0.9, edgecolor='none')
        bars2 = ax.bar([i + width/2 for i in x], giderler, width, label='Gider', 
                       color='#ff4c51', alpha=0.9, edgecolor='none')
        
        # Başlık - KÜÇÜK
        ax.set_title('Aylık Gelir-Gider', fontsize=10, 
                     fontweight='600', color='#444050', pad=6)
        
        # X ekseni - KÜÇÜK
        ax.set_xticks(x)
        ax.set_xticklabels(aylar, rotation=0, fontsize=7, color='#6d6b77')
        
        # Y ekseni formatı
        def format_func(value, tick_number):
            if value >= 1000000:
                return f'{value/1000000:.0f}M'
            elif value >= 1000:
                return f'{value/1000:.0f}K'
            else:
                return ''
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(format_func))
        ax.tick_params(axis='y', labelsize=7, colors='#6d6b77', pad=2)
        ax.tick_params(axis='x', labelsize=7, colors='#6d6b77', pad=2)
        
        # Legend - MINI
        ax.legend(frameon=False, fontsize=7, loc='upper left')
        
        # Grid - MINIMAL
        ax.grid(True, alpha=0.1, linestyle='-', linewidth=0.5, axis='y')
        ax.set_axisbelow(True)
        
        # Spine'lar
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e6e6e8')
        ax.spines['bottom'].set_color('#e6e6e8')
        ax.spines['left'].set_linewidth(0.8)
        ax.spines['bottom'].set_linewidth(0.8)
        
        ax.set_facecolor('white')
        self.figure.patch.set_facecolor('white')
        
        self.figure.tight_layout(pad=0.3)
        self.canvas.draw()
        
    def plot_gelir_dagilim(self, turler, tutarlar):
        """Gelir türleri dağılım grafiği - KOMPAKT Donut"""
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'figure'):
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Vuexy renk paleti
        colors = ['#7367f0', '#28c76f', '#00bad1', '#ff9f43', '#ff4c51', 
                  '#ea5455', '#e83e8c', '#00cfe8']
        
        # KOMPAKT donut - label'sız, sadece legend
        wedges, texts, autotexts = ax.pie(tutarlar, labels=None, autopct='%1.0f%%', 
                                           colors=colors, startangle=90,
                                           wedgeprops={'edgecolor': 'white', 'linewidth': 1},
                                           textprops={'fontsize': 7})
        
        # Yüzde metinleri
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('700')
            autotext.set_fontsize(7)
        
        # Donut hole
        centre_circle = plt.Circle((0, 0), 0.60, fc='white', linewidth=0)
        ax.add_artist(centre_circle)
        
        # Başlık - KÜÇÜK
        ax.set_title('Gelir Türleri', fontsize=9, 
                     fontweight='600', color='#444050', pad=4)
        
        # Legend - KOMPAKT, label'ları kısa tut
        short_labels = [t[:8] + '..' if len(t) > 8 else t for t in turler]
        ax.legend(short_labels, fontsize=6, loc='center left', 
                 bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
        
        ax.axis('equal')
        self.figure.patch.set_facecolor('white')
        
        self.figure.tight_layout(pad=0.2)
        self.canvas.draw()
        
    def plot_gider_dagilim(self, turler, tutarlar):
        """Gider türleri dağılım grafiği - KOMPAKT Donut"""
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'figure'):
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Vuexy renk paleti (giderler için)
        colors = ['#ff4c51', '#ff9f43', '#ff6b6b', '#fd7e14', '#e83e8c', 
                  '#ea5455', '#ff8a65', '#ff7f7f']
        
        # KOMPAKT donut - label'sız
        wedges, texts, autotexts = ax.pie(tutarlar, labels=None, autopct='%1.0f%%', 
                                           colors=colors, startangle=90,
                                           wedgeprops={'edgecolor': 'white', 'linewidth': 1},
                                           textprops={'fontsize': 7})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('700')
            autotext.set_fontsize(7)
        
        # Donut hole
        centre_circle = plt.Circle((0, 0), 0.60, fc='white', linewidth=0)
        ax.add_artist(centre_circle)
            
        # Başlık - KÜÇÜK
        ax.set_title('Gider Türleri', fontsize=9, 
                     fontweight='600', color='#444050', pad=4)
        
        # Legend - KOMPAKT
        short_labels = [t[:8] + '..' if len(t) > 8 else t for t in turler]
        ax.legend(short_labels, fontsize=6, loc='center left', 
                 bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
        
        ax.axis('equal')
        self.figure.patch.set_facecolor('white')
        
        self.figure.tight_layout(pad=0.2)
        self.canvas.draw()
        
    def plot_kasa_dagilim(self, kasalar, bakiyeler):
        """Kasa bakiyeleri grafiği - KOMPAKT Horizontal Bar"""
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'figure'):
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Vuexy success/danger colors
        colors = ['#28c76f' if b >= 0 else '#ff4c51' for b in bakiyeler]
        
        # KOMPAKT horizontal bar
        bars = ax.barh(kasalar, bakiyeler, color=colors, alpha=0.9, 
                       edgecolor='none', height=0.4)
        
        # Değerleri bar içine yaz - KÜÇÜK
        for i, (bar, bakiye) in enumerate(zip(bars, bakiyeler)):
            width = bar.get_width()
            # Bakiye formatı - KISA
            if abs(bakiye) >= 1000000:
                label = f'{bakiye/1000000:.1f}M'
            elif abs(bakiye) >= 1000:
                label = f'{bakiye/1000:.0f}K'
            else:
                label = f'{bakiye:.0f}'
            
            # Bar içine yaz
            ax.text(width/2, bar.get_y() + bar.get_height()/2, label,
                   ha='center', va='center',
                   fontsize=7, fontweight='700', color='white')
        
        # Başlık - KÜÇÜK
        ax.set_title('Kasa Bakiyeleri', fontsize=10, 
                     fontweight='600', color='#444050', pad=6)
        
        # Sıfır çizgisi
        ax.axvline(x=0, color='#6d6b77', linestyle='-', linewidth=1, alpha=0.3)
        
        # Grid - MINIMAL
        ax.grid(True, alpha=0.1, linestyle='-', linewidth=0.5, axis='x')
        ax.set_axisbelow(True)
        
        # X ekseni formatı
        def format_func(value, tick_number):
            if abs(value) >= 1000000:
                return f'{value/1000000:.0f}M'
            elif abs(value) >= 1000:
                return f'{value/1000:.0f}K'
            else:
                return ''
        
        ax.xaxis.set_major_formatter(plt.FuncFormatter(format_func))
        
        # Tick ayarları - KÜÇÜK
        ax.tick_params(axis='y', labelsize=7, colors='#444050', length=0, pad=4)
        ax.tick_params(axis='x', labelsize=7, colors='#6d6b77', pad=2)
        
        # Spine'lar
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#e6e6e8')
        ax.spines['bottom'].set_linewidth(0.8)
        
        ax.set_facecolor('white')
        self.figure.patch.set_facecolor('white')
        
        self.figure.tight_layout(pad=0.3)
        self.canvas.draw()


class DashboardWidget(QWidget):
    """Dashboard ana widget"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.rapor_yoneticisi = RaporYoneticisi(db)
        self.kasa_yoneticisi = KasaYoneticisi(db)
        self.aidat_yoneticisi = AidatYoneticisi(db)
        try:
            self.etkinlik_yoneticisi = EtkinlikYoneticisi(db)
        except:
            self.etkinlik_yoneticisi = None
        self.setup_ui()
        self.load_dashboard()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        
        # Üst toolbar - KOMPAKT (Fluent Widgets)
        header_layout = QHBoxLayout()
        
        yil_label = BodyLabel("Yıl:")
        yil_label.setStyleSheet("color: #6d6b77; font-size: 14px; font-weight: 500;")
        header_layout.addWidget(yil_label)
        
        self.yil_spin = SpinBox()
        self.yil_spin.setMinimum(2020)
        self.yil_spin.setMaximum(2050)
        self.yil_spin.setValue(datetime.now().year)
        self.yil_spin.setFixedWidth(90)
        self.yil_spin.valueChanged.connect(self.load_dashboard)
        header_layout.addWidget(self.yil_spin)
        
        header_layout.addStretch()
        
        # Modern Analytics butonu
        self.analytics_btn = PushButton("🚀 Modern Analytics")
        self.analytics_btn.setFixedHeight(32)
        self.analytics_btn.clicked.connect(self.open_flet_dashboard)
        self.analytics_btn.setStyleSheet("""
            QPushButton {
                background-color: #7367f0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5e50e6;
            }
        """)
        header_layout.addWidget(self.analytics_btn)
        
        self.yenile_btn = PushButton("🔄 Yenile")
        self.yenile_btn.setFixedHeight(32)
        self.yenile_btn.clicked.connect(self.load_dashboard)
        header_layout.addWidget(self.yenile_btn)
        
        main_layout.addLayout(header_layout)
        
        # ANA CONTAINER - NO SCROLL, FİXED LAYOUT
        content_widget = QWidget()
        content_widget.setStyleSheet("QWidget { background-color: transparent; }")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # İstatistik Kartları - TEK SATIR (5 kart yan yana)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cards_layout = cards_layout
        content_layout.addLayout(cards_layout)
        
        # Grafikler - 2 SATIR KOMPAKT
        charts_layout = QGridLayout()
        charts_layout.setSpacing(12)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        
        # Üst satır: 3 grafik yan yana
        self.gelir_gider_chart = ChartWidget(chart_type="bar_compact")
        charts_layout.addWidget(self.gelir_gider_chart, 0, 0)
        
        self.gelir_dagilim_chart = ChartWidget(chart_type="donut_compact")
        charts_layout.addWidget(self.gelir_dagilim_chart, 0, 1)
        
        self.gider_dagilim_chart = ChartWidget(chart_type="donut_compact")
        charts_layout.addWidget(self.gider_dagilim_chart, 0, 2)
        
        # Alt satır: Kasa grafiği (tam genişlik)
        self.kasa_chart = ChartWidget(chart_type="horizontal_bar_compact")
        charts_layout.addWidget(self.kasa_chart, 1, 0, 1, 3)
        
        content_layout.addLayout(charts_layout)
        content_widget.setLayout(content_layout)
        
        main_layout.addWidget(content_widget)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def open_flet_dashboard(self):
        """Flet ile modern analytics dashboard aç"""
        import subprocess
        import sys
        import os
        
        script_path = os.path.join(os.path.dirname(__file__), 'flet_dashboard.py')
        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])
        else:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning(
                title='Uyarı',
                content='Modern Analytics modülü bulunamadı.',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        
    def load_dashboard(self):
        """Dashboard verilerini yükle ve göster"""
        yil = self.yil_spin.value()
        
        # Genel özet
        ozet = self.rapor_yoneticisi.genel_ozet(yil)
        
        # Kartları temizle
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # İstatistik kartları - TEK SATIR (5 kart, MİNİMAL TASARIM)
        
        # Gelir Kartı - Yeşil
        gelir_deger = f"₺{ozet['toplam_gelir']/1000:.0f}K" if ozet['toplam_gelir'] >= 1000 else f"₺{ozet['toplam_gelir']:.0f}"
        gelir_card = StatCard("Gelir", gelir_deger, "#28c76f")
        self.cards_layout.addWidget(gelir_card)
        
        # Gider Kartı - Kırmızı
        gider_deger = f"₺{ozet['toplam_gider']/1000:.0f}K" if ozet['toplam_gider'] >= 1000 else f"₺{ozet['toplam_gider']:.0f}"
        gider_card = StatCard("Gider", gider_deger, "#ff4c51")
        self.cards_layout.addWidget(gider_card)
        
        # Net Sonuç Kartı - Mor veya Kırmızı
        net_deger = f"₺{abs(ozet['net_sonuc'])/1000:.0f}K" if abs(ozet['net_sonuc']) >= 1000 else f"₺{ozet['net_sonuc']:.0f}"
        net_renk = "#7367f0" if ozet['net_sonuc'] >= 0 else "#ff4c51"
        net_card = StatCard("Net", net_deger, net_renk)
        self.cards_layout.addWidget(net_card)
        
        # Kasa Kartı - Mavi
        kasa_deger = f"₺{ozet['toplam_kasa_bakiye']/1000:.0f}K" if ozet['toplam_kasa_bakiye'] >= 1000 else f"₺{ozet['toplam_kasa_bakiye']:.0f}"
        kasa_card = StatCard("Kasa", kasa_deger, "#00bad1")
        self.cards_layout.addWidget(kasa_card)
        
        # Aidat Kartı - Turuncu
        aidat_orani = (ozet['aidat_odenen_uye'] / ozet['toplam_uye'] * 100) if ozet['toplam_uye'] > 0 else 0
        aidat_card = StatCard("Aidat", f"{ozet['aidat_odenen_uye']}/{ozet['toplam_uye']}", "#ff9f43")
        self.cards_layout.addWidget(aidat_card)
        
        # Tahakkuk Kartı - Açık Kırmızı (Gelecek yıl tahakkuku)
        try:
            from models import TahakkukYoneticisi
            tahakkuk_yoneticisi = TahakkukYoneticisi(self.db)
            tahakkuk_ozet = tahakkuk_yoneticisi.tahakkuk_ozet()  # Parametre almayan versiyon
            toplam_tahakkuk = sum(t.get('tutar', 0) for t in tahakkuk_ozet) if tahakkuk_ozet else 0
            tahakkuk_deger = f"₺{toplam_tahakkuk/1000:.0f}K" if toplam_tahakkuk >= 1000 else f"₺{toplam_tahakkuk:.0f}"
            tahakkuk_card = StatCard("Tahakkuk", tahakkuk_deger, "#ea5455")
            self.cards_layout.addWidget(tahakkuk_card)
        except Exception as e:
            # Tahakkuk sistemi yoksa skip
            print(f"Tahakkuk kartı yüklenemedi: {e}")
        
        # Grafikler
        self.load_charts(yil)
        
    def load_charts(self, yil):
        """Grafikleri yükle"""
        # 1. Aylık Gelir-Gider (son 12 ay)
        # Basitleştirilmiş - sadece yıllık toplam
        baslangic = f"{yil}-01-01"
        bitis = f"{yil}-12-31"
        
        # Ay bazında gelir-gider hesapla
        aylar = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
        gelirler = []
        giderler = []
        
        for ay in range(1, 13):
            ay_baslangic = f"{yil}-{ay:02d}-01"
            if ay == 12:
                ay_bitis = f"{yil}-12-31"
            else:
                ay_bitis = f"{yil}-{ay+1:02d}-01"
                
            # Gelir
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) FROM gelirler 
                WHERE tarih >= ? AND tarih < ?
            """, (ay_baslangic, ay_bitis))
            gelir = self.db.cursor.fetchone()[0]
            gelirler.append(gelir)
            
            # Gider
            self.db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) FROM giderler 
                WHERE tarih >= ? AND tarih < ?
            """, (ay_baslangic, ay_bitis))
            gider = self.db.cursor.fetchone()[0]
            giderler.append(gider)
        
        self.gelir_gider_chart.plot_gelir_gider(aylar, gelirler, giderler)
        
        # 2. Gelir Dağılımı
        gelir_dagilim = self.rapor_yoneticisi.gelir_turu_dagilimi(baslangic, bitis)
        if gelir_dagilim:
            turler = [g['gelir_turu'] for g in gelir_dagilim]
            tutarlar = [g['toplam'] for g in gelir_dagilim]
            self.gelir_dagilim_chart.plot_gelir_dagilim(turler, tutarlar)
        
        # 3. Gider Dağılımı
        gider_dagilim = self.rapor_yoneticisi.gider_turu_dagilimi(baslangic, bitis)
        if gider_dagilim:
            turler = [g['gider_turu'] for g in gider_dagilim[:8]]  # İlk 8 tür
            tutarlar = [g['toplam'] for g in gider_dagilim[:8]]
            self.gider_dagilim_chart.plot_gider_dagilim(turler, tutarlar)
        
        # 4. Kasa Bakiyeleri
        kasa_ozet = self.kasa_yoneticisi.tum_kasalar_ozet()
        if kasa_ozet:
            kasalar = [k['kasa_adi'] for k in kasa_ozet]
            bakiyeler = [k['net_bakiye'] for k in kasa_ozet]
            self.kasa_chart.plot_kasa_dagilim(kasalar, bakiyeler)

