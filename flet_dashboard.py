"""
🎨 BADER Flet Dashboard - Modern Analytics View
Flutter/Material 3 tasarımı ile analiz ekranı
"""

import flet as ft
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from existing models
try:
    from database import Database
    from models import RaporYoneticisi, KasaYoneticisi
    DB_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    DB_AVAILABLE = False


def get_dashboard_data(yil: int) -> dict:
    """Dashboard verilerini mevcut modeller üzerinden çek"""
    data = {
        'toplam_gelir': 0, 'toplam_gider': 0, 'net_sonuc': 0,
        'toplam_kasa': 0, 'toplam_uye': 0, 'aidat_odenen': 0,
        'aylik_gelir': [0]*12, 'aylik_gider': [0]*12,
        'gelir_dagilim': [], 'gider_dagilim': [], 'kasalar': []
    }
    
    if not DB_AVAILABLE:
        return data
    
    try:
        db = Database()
        rapor = RaporYoneticisi(db)
        kasa = KasaYoneticisi(db)
        
        # Genel özet
        ozet = rapor.genel_ozet(yil)
        data['toplam_gelir'] = ozet.get('toplam_gelir', 0)
        data['toplam_gider'] = ozet.get('toplam_gider', 0)
        data['net_sonuc'] = ozet.get('net_sonuc', 0)
        data['toplam_kasa'] = ozet.get('toplam_kasa_bakiye', 0)
        data['toplam_uye'] = ozet.get('toplam_uye', 0)
        data['aidat_odenen'] = ozet.get('aidat_odenen_uye', 0)
        
        # Aylık gelir/gider
        baslangic = f"{yil}-01-01"
        bitis = f"{yil}-12-31"
        
        for ay in range(1, 13):
            ay_baslangic = f"{yil}-{ay:02d}-01"
            if ay == 12:
                ay_bitis = f"{yil}-12-31"
            else:
                ay_bitis = f"{yil}-{ay+1:02d}-01"
            
            db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) FROM gelirler 
                WHERE tarih >= ? AND tarih < ?
            """, (ay_baslangic, ay_bitis))
            data['aylik_gelir'][ay-1] = db.cursor.fetchone()[0]
            
            db.cursor.execute("""
                SELECT COALESCE(SUM(tutar), 0) FROM giderler 
                WHERE tarih >= ? AND tarih < ?
            """, (ay_baslangic, ay_bitis))
            data['aylik_gider'][ay-1] = db.cursor.fetchone()[0]
        
        # Gelir dağılımı
        data['gelir_dagilim'] = rapor.gelir_turu_dagilimi(baslangic, bitis) or []
        
        # Gider dağılımı
        data['gider_dagilim'] = rapor.gider_turu_dagilimi(baslangic, bitis) or []
        
        # Kasalar
        kasa_ozet = kasa.tum_kasalar_ozet()
        data['kasalar'] = [{'kasa_adi': k['kasa_adi'], 'bakiye': k['net_bakiye']} 
                          for k in kasa_ozet if not k['kasa_adi'].startswith('TEST')]
        
        db.close()
    except Exception as e:
        print(f"Dashboard data error: {e}")
    
    return data


def format_currency(value: float) -> str:
    """Para formatı"""
    if abs(value) >= 1_000_000:
        return f"₺{value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"₺{value/1_000:.0f}K"
    else:
        return f"₺{value:.0f}"


def create_stat_card(title: str, value: str, icon: str, color: str) -> ft.Container:
    """Modern stat card"""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(icon, color=color, size=28),
                ft.Text(title, size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Text(value, size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
        ], spacing=8),
        padding=20,
        border_radius=16,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
        expand=True,
    )


def create_mini_bar_chart(values: list, color: str, max_val: float = None) -> ft.Container:
    """Mini bar chart (sparkline style)"""
    if not max_val:
        max_val = max(values) if values and max(values) > 0 else 1
    
    bars = []
    for val in values:
        height = max(4, (val / max_val) * 60) if max_val > 0 else 4
        bars.append(
            ft.Container(
                width=12,
                height=height,
                bgcolor=color,
                border_radius=4,
            )
        )
    
    return ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=4)


def create_progress_item(label: str, value: float, total: float, color: str) -> ft.Container:
    """Progress bar item"""
    percentage = (value / total * 100) if total > 0 else 0
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(label, size=13, color=ft.Colors.GREY_700, expand=True),
                ft.Text(format_currency(value), size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
            ]),
            ft.ProgressBar(
                value=percentage/100,
                bgcolor=ft.Colors.GREY_200,
                color=color,
                height=8,
                border_radius=4,
            ),
        ], spacing=6),
        padding=ft.padding.symmetric(vertical=6),
    )


def main(page: ft.Page):
    """Ana Flet uygulaması"""
    page.title = "BADER Analytics Dashboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#F8FAFC"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 900
    page.window.min_height = 600
    
    # Theme
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        font_family="SF Pro Display",
    )
    
    current_year = datetime.now().year
    
    def load_dashboard(yil: int):
        """Dashboard'u yükle/güncelle"""
        data = get_dashboard_data(yil)
        
        # Stat Cards
        stat_cards = ft.Row([
            create_stat_card("Toplam Gelir", format_currency(data['toplam_gelir']), 
                           ft.Icons.TRENDING_UP, ft.Colors.GREEN_600),
            create_stat_card("Toplam Gider", format_currency(data['toplam_gider']), 
                           ft.Icons.TRENDING_DOWN, ft.Colors.RED_600),
            create_stat_card("Net Sonuç", format_currency(data['net_sonuc']), 
                           ft.Icons.ACCOUNT_BALANCE, ft.Colors.BLUE_600),
            create_stat_card("Kasa Bakiyesi", format_currency(data['toplam_kasa']), 
                           ft.Icons.SAVINGS, ft.Colors.PURPLE_600),
            create_stat_card(f"Aktif Üye", f"{data['toplam_uye']}", 
                           ft.Icons.PEOPLE, ft.Colors.ORANGE_600),
        ], spacing=16, expand=True)
        
        # Aylık Trend Chart
        max_val = max(max(data['aylik_gelir']), max(data['aylik_gider'])) if data['aylik_gelir'] else 1
        aylar = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
        
        trend_chart = ft.Container(
            content=ft.Column([
                ft.Text("Aylık Gelir/Gider Trendi", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                ft.Container(height=10),
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=12, height=12, bgcolor=ft.Colors.GREEN_500, border_radius=3),
                            ft.Text("Gelir", size=12, color=ft.Colors.GREY_600),
                        ], spacing=6),
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=12, height=12, bgcolor=ft.Colors.RED_400, border_radius=3),
                            ft.Text("Gider", size=12, color=ft.Colors.GREY_600),
                        ], spacing=6),
                    ),
                ], spacing=20),
                ft.Container(height=16),
                # Bar chart
                ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Container(
                                width=20,
                                height=max(4, (g / max_val) * 100) if max_val > 0 else 4,
                                bgcolor=ft.Colors.GREEN_500,
                                border_radius=ft.BorderRadius(top_left=4, top_right=4, bottom_left=0, bottom_right=0),
                            ),
                            ft.Container(
                                width=20,
                                height=max(4, (e / max_val) * 100) if max_val > 0 else 4,
                                bgcolor=ft.Colors.RED_400,
                                border_radius=ft.BorderRadius(top_left=4, top_right=4, bottom_left=0, bottom_right=0),
                            ),
                        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.END),
                        ft.Text(ay, size=10, color=ft.Colors.GREY_500),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
                    for ay, g, e in zip(aylar, data['aylik_gelir'], data['aylik_gider'])
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=True),
            ]),
            padding=24,
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, 
                               color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            expand=2,
        )
        
        # Gelir Dağılımı
        gelir_toplam = sum(g['toplam'] for g in data['gelir_dagilim']) if data['gelir_dagilim'] else 1
        gelir_colors = [ft.Colors.GREEN_600, ft.Colors.GREEN_500, ft.Colors.GREEN_400, ft.Colors.GREEN_300, ft.Colors.GREEN_200]
        
        gelir_panel = ft.Container(
            content=ft.Column([
                ft.Text("Gelir Dağılımı", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                ft.Container(height=12),
                *[create_progress_item(g['gelir_turu'], g['toplam'], gelir_toplam, gelir_colors[i % len(gelir_colors)])
                  for i, g in enumerate(data['gelir_dagilim'][:5])],
            ] if data['gelir_dagilim'] else [
                ft.Text("Gelir Dağılımı", size=16, weight=ft.FontWeight.W_600),
                ft.Container(height=20),
                ft.Text("Veri bulunamadı", color=ft.Colors.GREY_400),
            ]),
            padding=24,
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, 
                               color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            expand=1,
        )
        
        # Gider Dağılımı
        gider_toplam = sum(g['toplam'] for g in data['gider_dagilim']) if data['gider_dagilim'] else 1
        gider_colors = [ft.Colors.RED_600, ft.Colors.RED_500, ft.Colors.RED_400, ft.Colors.ORANGE_400, ft.Colors.ORANGE_300]
        
        gider_panel = ft.Container(
            content=ft.Column([
                ft.Text("Gider Dağılımı", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                ft.Container(height=12),
                *[create_progress_item(g['gider_turu'], g['toplam'], gider_toplam, gider_colors[i % len(gider_colors)])
                  for i, g in enumerate(data['gider_dagilim'][:5])],
            ] if data['gider_dagilim'] else [
                ft.Text("Gider Dağılımı", size=16, weight=ft.FontWeight.W_600),
                ft.Container(height=20),
                ft.Text("Veri bulunamadı", color=ft.Colors.GREY_400),
            ]),
            padding=24,
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, 
                               color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            expand=1,
        )
        
        # Kasa Bakiyeleri
        kasa_panel = ft.Container(
            content=ft.Column([
                ft.Text("Kasa Bakiyeleri", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                ft.Container(height=12),
                *[ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=ft.Colors.BLUE_400, size=20),
                        ft.Text(k['kasa_adi'], size=13, color=ft.Colors.GREY_700, expand=True),
                        ft.Text(format_currency(k['bakiye']), size=14, 
                               weight=ft.FontWeight.W_600, 
                               color=ft.Colors.GREEN_600 if k['bakiye'] >= 0 else ft.Colors.RED_600),
                    ]),
                    padding=ft.Padding(left=4, right=4, top=8, bottom=8),
                    border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
                ) for k in data['kasalar'][:6]],
            ] if data['kasalar'] else [
                ft.Text("Kasa Bakiyeleri", size=16, weight=ft.FontWeight.W_600),
                ft.Container(height=20),
                ft.Text("Kasa bulunamadı", color=ft.Colors.GREY_400),
            ]),
            padding=24,
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, 
                               color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            expand=1,
        )
        
        return ft.Column([
            stat_cards,
            ft.Container(height=16),
            ft.Row([trend_chart], expand=True),
            ft.Container(height=16),
            ft.Row([gelir_panel, gider_panel, kasa_panel], spacing=16, expand=True),
        ], spacing=0, expand=True)
    
    def on_year_change(e):
        """Yıl değiştiğinde"""
        content_area.content = load_dashboard(int(year_dropdown.value))
        page.update()
    
    # Header
    year_dropdown = ft.Dropdown(
        value=str(current_year),
        options=[ft.dropdown.Option(str(y)) for y in range(2020, 2031)],
        width=100,
        height=40,
        border_radius=8,
    )
    year_dropdown.on_change = on_year_change
    
    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.BLUE_600, size=28),
                ft.Text("BADER Analytics", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
            ], spacing=12),
            ft.Row([
                ft.Text("Yıl:", size=14, color=ft.Colors.GREY_600),
                year_dropdown,
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_color=ft.Colors.BLUE_600,
                    tooltip="Yenile",
                    on_click=lambda e: on_year_change(e),
                ),
            ], spacing=12),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(left=24, right=24, top=16, bottom=16),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
    )
    
    # Content area
    content_area = ft.Container(
        content=load_dashboard(current_year),
        padding=24,
        expand=True,
    )
    
    # Main layout
    page.add(
        ft.Column([
            header,
            content_area,
        ], spacing=0, expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)
