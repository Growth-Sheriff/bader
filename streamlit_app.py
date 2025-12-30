"""
BADER Dernek Yönetim Sistemi - Web Demo
Streamlit ile online erişim
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os

# Sayfa ayarları
st.set_page_config(
    page_title="BADER - Dernek Yönetim",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Veritabanı bağlantısı
@st.cache_resource
def get_db():
    # Streamlit Cloud için data klasörü
    db_path = "bader_demo.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Demo veritabanını oluştur"""
    conn = get_db()
    cur = conn.cursor()
    
    # Üyeler tablosu
    cur.execute('''
        CREATE TABLE IF NOT EXISTS uyeler (
            uye_id INTEGER PRIMARY KEY AUTOINCREMENT,
            uye_no TEXT UNIQUE,
            ad_soyad TEXT NOT NULL,
            tc_kimlik TEXT,
            telefon TEXT,
            email TEXT,
            adres TEXT,
            dogum_tarihi DATE,
            uyelik_tarihi DATE DEFAULT CURRENT_DATE,
            durum TEXT DEFAULT 'Aktif',
            notlar TEXT
        )
    ''')
    
    # Aidat takip
    cur.execute('''
        CREATE TABLE IF NOT EXISTS aidat_takip (
            aidat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            uye_id INTEGER,
            yil INTEGER,
            yillik_aidat_tutari REAL DEFAULT 100,
            toplam_odenen REAL DEFAULT 0,
            durum TEXT DEFAULT 'Bekliyor',
            FOREIGN KEY (uye_id) REFERENCES uyeler(uye_id)
        )
    ''')
    
    # Gelirler
    cur.execute('''
        CREATE TABLE IF NOT EXISTS gelirler (
            gelir_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATE,
            gelir_turu TEXT,
            aciklama TEXT,
            tutar REAL,
            kasa TEXT DEFAULT 'Ana Kasa'
        )
    ''')
    
    # Giderler
    cur.execute('''
        CREATE TABLE IF NOT EXISTS giderler (
            gider_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATE,
            gider_turu TEXT,
            aciklama TEXT,
            tutar REAL,
            kasa TEXT DEFAULT 'Ana Kasa'
        )
    ''')
    
    # Demo veriler ekle
    cur.execute("SELECT COUNT(*) FROM uyeler")
    if cur.fetchone()[0] == 0:
        demo_uyeler = [
            ('U001', 'Ahmet Yılmaz', '12345678901', '0532 111 2233', 'ahmet@email.com', 'İstanbul', '1985-03-15', '2020-01-01', 'Aktif'),
            ('U002', 'Fatma Kaya', '23456789012', '0533 222 3344', 'fatma@email.com', 'Ankara', '1990-07-22', '2021-03-15', 'Aktif'),
            ('U003', 'Mehmet Demir', '34567890123', '0534 333 4455', 'mehmet@email.com', 'İzmir', '1978-11-08', '2019-06-20', 'Aktif'),
            ('U004', 'Ayşe Şahin', '45678901234', '0535 444 5566', 'ayse@email.com', 'Bursa', '1995-02-28', '2022-01-10', 'Aktif'),
            ('U005', 'Ali Öztürk', '56789012345', '0536 555 6677', 'ali@email.com', 'Antalya', '1982-09-12', '2018-11-05', 'Pasif'),
        ]
        cur.executemany('''
            INSERT INTO uyeler (uye_no, ad_soyad, tc_kimlik, telefon, email, adres, dogum_tarihi, uyelik_tarihi, durum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', demo_uyeler)
        
        # Demo aidat
        for uye_id in range(1, 6):
            for yil in [2023, 2024, 2025]:
                odenen = 100 if yil < 2025 else (50 if uye_id % 2 == 0 else 0)
                durum = 'Tamamlandı' if odenen >= 100 else ('Kısmi' if odenen > 0 else 'Bekliyor')
                cur.execute('''
                    INSERT INTO aidat_takip (uye_id, yil, yillik_aidat_tutari, toplam_odenen, durum)
                    VALUES (?, ?, 100, ?, ?)
                ''', (uye_id, yil, odenen, durum))
        
        # Demo gelirler
        demo_gelirler = [
            ('2025-01-15', 'AİDAT', 'Ocak ayı aidat tahsilatları', 500),
            ('2025-02-20', 'BAĞIŞ', 'Genel bağış', 1000),
            ('2025-03-10', 'KİRA', 'Salon kirası', 2500),
            ('2025-04-05', 'ETKİNLİK', 'Bahar şenliği geliri', 3500),
        ]
        cur.executemany('INSERT INTO gelirler (tarih, gelir_turu, aciklama, tutar) VALUES (?, ?, ?, ?)', demo_gelirler)
        
        # Demo giderler
        demo_giderler = [
            ('2025-01-20', 'ELEKTRİK', 'Ocak elektrik faturası', 450),
            ('2025-02-15', 'SU', 'Şubat su faturası', 120),
            ('2025-03-25', 'MALZEME', 'Temizlik malzemeleri', 350),
            ('2025-04-10', 'TAMİRAT', 'Klima bakımı', 800),
        ]
        cur.executemany('INSERT INTO giderler (tarih, gider_turu, aciklama, tutar) VALUES (?, ?, ?, ?)', demo_giderler)
    
    conn.commit()
    return conn

# Veritabanını başlat
conn = init_db()

# CSS stilleri
st.markdown("""
<style>
    /* Mobil uyumluluk */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.5rem !important;
            padding: 0.5rem 0 !important;
        }
        .stColumn {
            width: 100% !important;
            flex: 100% !important;
        }
        .stMetric {
            padding: 0.5rem !important;
        }
        .stMetric label {
            font-size: 0.8rem !important;
        }
        .stMetric [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        section[data-testid="stSidebar"] {
            width: 100% !important;
        }
        .stDataFrame {
            font-size: 0.7rem !important;
        }
        .stButton button {
            width: 100% !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
        }
        .stFileUploader {
            padding: 1rem !important;
        }
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a73e8;
        text-align: center;
        padding: 1rem 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Genel iyileştirmeler */
    .stApp {
        max-width: 100%;
    }
    
    /* Touch-friendly */
    button, input, select, textarea {
        min-height: 44px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar menü
st.sidebar.image("https://img.icons8.com/color/96/conference-call.png", width=80)
st.sidebar.title("🏛️ BADER")
st.sidebar.caption("Dernek Yönetim Sistemi")

menu = st.sidebar.radio(
    "Menü",
    ["📊 Dashboard", "👥 Üyeler", "💳 Aidat Takip", "💰 Gelirler", "💸 Giderler", "📸 Belge Tara", "📈 Raporlar"],
    label_visibility="collapsed"
)

st.sidebar.divider()
st.sidebar.info("🌐 Demo Sürümü\nVeriler örnek amaçlıdır.")

# ==================== DASHBOARD ====================
if menu == "📊 Dashboard":
    st.markdown('<h1 class="main-header">🏛️ BADER Dernek Yönetimi</h1>', unsafe_allow_html=True)
    
    # İstatistikler
    col1, col2, col3, col4 = st.columns(4)
    
    cur = conn.cursor()
    
    # Toplam üye
    cur.execute("SELECT COUNT(*) FROM uyeler WHERE durum = 'Aktif'")
    aktif_uye = cur.fetchone()[0]
    
    # Toplam gelir
    cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM gelirler WHERE strftime('%Y', tarih) = '2025'")
    toplam_gelir = cur.fetchone()[0]
    
    # Toplam gider
    cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE strftime('%Y', tarih) = '2025'")
    toplam_gider = cur.fetchone()[0]
    
    # Aidat tahsilat oranı
    cur.execute("SELECT COUNT(*) FROM aidat_takip WHERE yil = 2025 AND durum = 'Tamamlandı'")
    tamamlanan = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM aidat_takip WHERE yil = 2025")
    toplam_aidat = cur.fetchone()[0]
    tahsilat_oran = (tamamlanan / toplam_aidat * 100) if toplam_aidat > 0 else 0
    
    with col1:
        st.metric("👥 Aktif Üye", aktif_uye)
    with col2:
        st.metric("💰 Toplam Gelir", f"₺{toplam_gelir:,.0f}")
    with col3:
        st.metric("💸 Toplam Gider", f"₺{toplam_gider:,.0f}")
    with col4:
        st.metric("📊 Tahsilat Oranı", f"%{tahsilat_oran:.0f}")
    
    st.divider()
    
    # Grafikler
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Gelir-Gider Karşılaştırma")
        chart_data = pd.DataFrame({
            'Kategori': ['Gelir', 'Gider', 'Net'],
            'Tutar': [toplam_gelir, toplam_gider, toplam_gelir - toplam_gider]
        })
        st.bar_chart(chart_data.set_index('Kategori'))
    
    with col2:
        st.subheader("💳 Aidat Durumu (2025)")
        cur.execute("""
            SELECT durum, COUNT(*) as sayi 
            FROM aidat_takip WHERE yil = 2025 
            GROUP BY durum
        """)
        aidat_data = pd.DataFrame(cur.fetchall(), columns=['Durum', 'Sayı'])
        if not aidat_data.empty:
            st.bar_chart(aidat_data.set_index('Durum'))

# ==================== ÜYELER ====================
elif menu == "👥 Üyeler":
    st.header("👥 Üye Yönetimi")
    
    tab1, tab2 = st.tabs(["📋 Üye Listesi", "➕ Yeni Üye"])
    
    with tab1:
        cur = conn.cursor()
        cur.execute("SELECT * FROM uyeler ORDER BY ad_soyad")
        uyeler = cur.fetchall()
        
        if uyeler:
            df = pd.DataFrame(uyeler, columns=['ID', 'Üye No', 'Ad Soyad', 'TC', 'Telefon', 'Email', 'Adres', 'Doğum', 'Üyelik', 'Durum', 'Notlar'])
            
            # Filtre
            durum_filtre = st.selectbox("Durum Filtresi", ["Tümü", "Aktif", "Pasif"])
            if durum_filtre != "Tümü":
                df = df[df['Durum'] == durum_filtre]
            
            st.dataframe(df[['Üye No', 'Ad Soyad', 'Telefon', 'Email', 'Durum']], use_container_width=True)
            st.caption(f"Toplam: {len(df)} üye")
    
    with tab2:
        with st.form("yeni_uye"):
            col1, col2 = st.columns(2)
            with col1:
                ad_soyad = st.text_input("Ad Soyad *")
                telefon = st.text_input("Telefon")
                adres = st.text_input("Adres")
            with col2:
                tc_kimlik = st.text_input("TC Kimlik No")
                email = st.text_input("E-posta")
                dogum = st.date_input("Doğum Tarihi", value=None)
            
            if st.form_submit_button("💾 Kaydet", type="primary"):
                if ad_soyad:
                    cur = conn.cursor()
                    cur.execute("SELECT MAX(CAST(SUBSTR(uye_no, 2) AS INTEGER)) FROM uyeler")
                    max_no = cur.fetchone()[0] or 0
                    yeni_no = f"U{max_no + 1:03d}"
                    
                    cur.execute('''
                        INSERT INTO uyeler (uye_no, ad_soyad, tc_kimlik, telefon, email, adres, dogum_tarihi)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (yeni_no, ad_soyad, tc_kimlik, telefon, email, adres, dogum))
                    conn.commit()
                    st.success(f"✅ Üye eklendi: {yeni_no}")
                    st.rerun()
                else:
                    st.error("Ad Soyad zorunludur!")

# ==================== AİDAT TAKİP ====================
elif menu == "💳 Aidat Takip":
    st.header("💳 Aidat Takip")
    
    yil = st.selectbox("Yıl Seçin", [2025, 2024, 2023], index=0)
    
    cur = conn.cursor()
    cur.execute("""
        SELECT u.uye_no, u.ad_soyad, a.yillik_aidat_tutari, a.toplam_odenen, 
               a.yillik_aidat_tutari - a.toplam_odenen as kalan, a.durum
        FROM aidat_takip a
        JOIN uyeler u ON a.uye_id = u.uye_id
        WHERE a.yil = ? AND u.durum = 'Aktif'
        ORDER BY u.ad_soyad
    """, (yil,))
    
    aidatlar = cur.fetchall()
    
    if aidatlar:
        df = pd.DataFrame(aidatlar, columns=['Üye No', 'Ad Soyad', 'Aidat', 'Ödenen', 'Kalan', 'Durum'])
        
        # Renkli durum
        def color_durum(val):
            if val == 'Tamamlandı':
                return 'background-color: #d4edda'
            elif val == 'Kısmi':
                return 'background-color: #fff3cd'
            return 'background-color: #f8d7da'
        
        st.dataframe(
            df.style.applymap(color_durum, subset=['Durum']),
            use_container_width=True
        )
        
        # Özet
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Toplam Beklenen", f"₺{df['Aidat'].sum():,.0f}")
        with col2:
            st.metric("Toplam Tahsil", f"₺{df['Ödenen'].sum():,.0f}")
        with col3:
            st.metric("Kalan Alacak", f"₺{df['Kalan'].sum():,.0f}")

# ==================== GELİRLER ====================
elif menu == "💰 Gelirler":
    st.header("💰 Gelir Kayıtları")
    
    tab1, tab2 = st.tabs(["📋 Gelir Listesi", "➕ Yeni Gelir"])
    
    with tab1:
        cur = conn.cursor()
        cur.execute("SELECT * FROM gelirler ORDER BY tarih DESC")
        gelirler = cur.fetchall()
        
        if gelirler:
            df = pd.DataFrame(gelirler, columns=['ID', 'Tarih', 'Tür', 'Açıklama', 'Tutar', 'Kasa'])
            st.dataframe(df[['Tarih', 'Tür', 'Açıklama', 'Tutar']], use_container_width=True)
            st.metric("Toplam Gelir", f"₺{df['Tutar'].sum():,.0f}")
    
    with tab2:
        with st.form("yeni_gelir"):
            col1, col2 = st.columns(2)
            with col1:
                tarih = st.date_input("Tarih", value=date.today())
                tur = st.selectbox("Gelir Türü", ["AİDAT", "BAĞIŞ", "KİRA", "ETKİNLİK", "DİĞER"])
            with col2:
                tutar = st.number_input("Tutar (₺)", min_value=0.0, step=10.0)
                aciklama = st.text_input("Açıklama")
            
            if st.form_submit_button("💾 Kaydet", type="primary"):
                if tutar > 0:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO gelirler (tarih, gelir_turu, aciklama, tutar) VALUES (?, ?, ?, ?)",
                               (tarih, tur, aciklama, tutar))
                    conn.commit()
                    st.success("✅ Gelir kaydedildi!")
                    st.rerun()

# ==================== GİDERLER ====================
elif menu == "💸 Giderler":
    st.header("💸 Gider Kayıtları")
    
    tab1, tab2 = st.tabs(["📋 Gider Listesi", "➕ Yeni Gider"])
    
    with tab1:
        cur = conn.cursor()
        cur.execute("SELECT * FROM giderler ORDER BY tarih DESC")
        giderler = cur.fetchall()
        
        if giderler:
            df = pd.DataFrame(giderler, columns=['ID', 'Tarih', 'Tür', 'Açıklama', 'Tutar', 'Kasa'])
            st.dataframe(df[['Tarih', 'Tür', 'Açıklama', 'Tutar']], use_container_width=True)
            st.metric("Toplam Gider", f"₺{df['Tutar'].sum():,.0f}")
    
    with tab2:
        with st.form("yeni_gider"):
            col1, col2 = st.columns(2)
            with col1:
                tarih = st.date_input("Tarih", value=date.today())
                tur = st.selectbox("Gider Türü", ["ELEKTRİK", "SU", "DOĞALGAZ", "KİRA", "MALZEME", "TAMİRAT", "PERSONEL", "DİĞER"])
            with col2:
                tutar = st.number_input("Tutar (₺)", min_value=0.0, step=10.0)
                aciklama = st.text_input("Açıklama")
            
            if st.form_submit_button("💾 Kaydet", type="primary"):
                if tutar > 0:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO giderler (tarih, gider_turu, aciklama, tutar) VALUES (?, ?, ?, ?)",
                               (tarih, tur, aciklama, tutar))
                    conn.commit()
                    st.success("✅ Gider kaydedildi!")
                    st.rerun()

# ==================== BELGE TARA (OCR) ====================
elif menu == "📸 Belge Tara":
    st.header("📸 Belge Tarama (OCR)")
    st.info("📱 Fatura, fiş veya belge görselini yükleyin. Sunucu üzerinde OCR işlemi yapılacaktır.")
    
    import requests
    import base64
    
    SERVER_URL = "http://157.90.154.48:8080/api"
    
    # Session state for OCR results
    if 'ocr_result' not in st.session_state:
        st.session_state.ocr_result = None
    
    uploaded_file = st.file_uploader("📄 Belge Seçin", type=['png', 'jpg', 'jpeg', 'webp', 'bmp'])
    
    if uploaded_file:
        # Görsel önizleme
        st.image(uploaded_file, caption="Yüklenen Belge", use_container_width=True)
        
        # Tara butonu
        if st.button("🚀 Belgeyi Tara", type="primary", use_container_width=True):
            with st.spinner("🔍 Belge taranıyor... (Bu işlem 10-30 saniye sürebilir)"):
                try:
                    file_bytes = uploaded_file.getvalue()
                    file_base64 = base64.b64encode(file_bytes).decode()
                    
                    response = requests.post(
                        f"{SERVER_URL}/ocr/demo",
                        json={
                            "image_base64": file_base64,
                            "filename": uploaded_file.name
                        },
                        timeout=90
                    )
                    
                    if response.status_code == 200:
                        st.session_state.ocr_result = response.json()
                    else:
                        st.error(f"❌ Sunucu hatası: {response.status_code}")
                        try:
                            st.json(response.json())
                        except:
                            st.text(response.text)
                except requests.exceptions.Timeout:
                    st.error("⏰ Zaman aşımı - İşlem çok uzun sürdü, lütfen tekrar deneyin")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Bağlantı hatası - Sunucuya erişilemiyor")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        # Sonuçları göster
        if st.session_state.ocr_result:
            result = st.session_state.ocr_result
            
            st.divider()
            st.success("✅ OCR Tamamlandı!")
            
            # Çıkarılan bilgiler - mobil uyumlu
            if result.get('tutar'):
                st.metric("💰 Algılanan Tutar", f"₺{result['tutar']:,.2f}")
            if result.get('tarih'):
                st.info(f"📅 **Tarih:** {result['tarih']}")
            if result.get('aciklama'):
                st.info(f"📝 **Açıklama:** {result['aciklama']}")
            if result.get('processing_time'):
                st.caption(f"⏱️ İşlem süresi: {result['processing_time']} saniye")
            
            # Ham metin
            with st.expander("📄 Tüm Metin (Genişlet)"):
                st.text(result.get('raw_text', 'Metin bulunamadı'))
            
            # Kayıt formu
            st.divider()
            st.subheader("💾 Kayıt Oluştur")
            
            with st.form("ocr_kayit_form"):
                kayit_turu = st.radio("Kayıt Türü", ["Gelir", "Gider"], horizontal=True)
                tutar_input = st.number_input("Tutar (₺)", value=float(result.get('tutar') or 0), min_value=0.0, step=0.01)
                aciklama_input = st.text_input("Açıklama", value=result.get('aciklama') or '')
                
                if st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True):
                    if tutar_input > 0:
                        cur = conn.cursor()
                        if kayit_turu == "Gelir":
                            cur.execute(
                                "INSERT INTO gelirler (tarih, gelir_turu, aciklama, tutar) VALUES (?, ?, ?, ?)",
                                (datetime.now().strftime('%Y-%m-%d'), 'OCR', aciklama_input, tutar_input)
                            )
                        else:
                            cur.execute(
                                "INSERT INTO giderler (tarih, gider_turu, aciklama, tutar) VALUES (?, ?, ?, ?)",
                                (datetime.now().strftime('%Y-%m-%d'), 'OCR', aciklama_input, tutar_input)
                            )
                        conn.commit()
                        st.success(f"✅ {kayit_turu} olarak kaydedildi!")
                        st.session_state.ocr_result = None
                        st.rerun()
                    else:
                        st.warning("⚠️ Tutar 0'dan büyük olmalı")

# ==================== RAPORLAR ====================
elif menu == "📈 Raporlar":
    st.header("📈 Raporlar")
    
    cur = conn.cursor()
    
    # Gelir-Gider özeti
    st.subheader("💹 Gelir-Gider Özeti (2025)")
    
    cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM gelirler WHERE strftime('%Y', tarih) = '2025'")
    toplam_gelir = cur.fetchone()[0]
    
    cur.execute("SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE strftime('%Y', tarih) = '2025'")
    toplam_gider = cur.fetchone()[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Toplam Gelir", f"₺{toplam_gelir:,.0f}")
    with col2:
        st.metric("Toplam Gider", f"₺{toplam_gider:,.0f}")
    with col3:
        net = toplam_gelir - toplam_gider
        st.metric("Net Durum", f"₺{net:,.0f}", delta=f"{'Kâr' if net > 0 else 'Zarar'}")
    
    st.divider()
    
    # Gelir türü dağılımı
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Gelir Türleri")
        cur.execute("SELECT gelir_turu, SUM(tutar) FROM gelirler GROUP BY gelir_turu")
        gelir_dag = pd.DataFrame(cur.fetchall(), columns=['Tür', 'Tutar'])
        if not gelir_dag.empty:
            st.bar_chart(gelir_dag.set_index('Tür'))
    
    with col2:
        st.subheader("📊 Gider Türleri")
        cur.execute("SELECT gider_turu, SUM(tutar) FROM giderler GROUP BY gider_turu")
        gider_dag = pd.DataFrame(cur.fetchall(), columns=['Tür', 'Tutar'])
        if not gider_dag.empty:
            st.bar_chart(gider_dag.set_index('Tür'))

# Footer
st.divider()
st.caption("🏛️ BADER Dernek Yönetim Sistemi | Demo Sürümü | 2025")
