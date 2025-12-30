"""
BADER Dernek Yönetim Sistemi - Web Demo
Sunucu API'sine bağlı gerçek versiyon
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import base64

# Sayfa ayarları
st.set_page_config(
    page_title="BADER - Dernek Yönetim",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sunucu API
API_URL = "http://127.0.0.1:8000"
CUSTOMER_ID = "BADER-2024-DEMO-0001"

# API Helper fonksiyonları
def api_get(endpoint, params=None):
    try:
        if params is None:
            params = {}
        params['customer_id'] = CUSTOMER_ID
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def api_post(endpoint, data):
    try:
        response = requests.post(
            f"{API_URL}{endpoint}?customer_id={CUSTOMER_ID}",
            json=data,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

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
    
    /* Sync indicator */
    .sync-badge {
        background: #4CAF50;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.5rem;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar menü
st.sidebar.image("https://img.icons8.com/color/96/conference-call.png", width=80)
st.sidebar.title("🏛️ BADER")
st.sidebar.caption("Dernek Yönetim Sistemi")
st.sidebar.markdown('<span class="sync-badge">🔄 Sunucu Bağlantılı</span>', unsafe_allow_html=True)

menu = st.sidebar.radio(
    "Menü",
    ["📊 Dashboard", "👥 Üyeler", "💰 Gelirler", "💸 Giderler", "📸 Belge Tara", "📈 Raporlar"],
    label_visibility="collapsed"
)

st.sidebar.divider()
st.sidebar.success("🌐 **BADER Derneği**\nLisans: BADER-2024-DEMO-0001")

# ==================== DASHBOARD ====================
if menu == "📊 Dashboard":
    st.markdown('<h1 class="main-header">🏛️ BADER Dernek Yönetimi</h1>', unsafe_allow_html=True)
    
    # Sunucudan özet al
    ozet = api_get("/dernek/ozet")
    
    if ozet:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Aktif Üye", ozet['aktif_uye'])
        with col2:
            st.metric("💰 Toplam Gelir", f"₺{ozet['toplam_gelir']:,.0f}")
        with col3:
            st.metric("💸 Toplam Gider", f"₺{ozet['toplam_gider']:,.0f}")
        with col4:
            st.metric("💵 Net Bakiye", f"₺{ozet['net_bakiye']:,.0f}")
        
        st.divider()
        
        # Grafikler
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Gelir-Gider Karşılaştırma")
            chart_data = pd.DataFrame({
                'Kategori': ['Gelir', 'Gider', 'Net'],
                'Tutar': [ozet['toplam_gelir'], ozet['toplam_gider'], ozet['net_bakiye']]
            })
            st.bar_chart(chart_data.set_index('Kategori'))
        
        with col2:
            st.subheader("📌 Hızlı Bilgiler")
            st.info(f"**Aktif Üye Sayısı:** {ozet['aktif_uye']}")
            st.info(f"**Net Durum:** {'Kâr' if ozet['net_bakiye'] > 0 else 'Zarar'}")
    else:
        st.error("❌ Sunucuya bağlanılamadı!")

# ==================== ÜYELER ====================
elif menu == "👥 Üyeler":
    st.header("👥 Üye Yönetimi")
    
    tab1, tab2 = st.tabs(["📋 Üye Listesi", "➕ Yeni Üye"])
    
    with tab1:
        uyeler = api_get("/dernek/uyeler")
        
        if uyeler:
            df = pd.DataFrame(uyeler)
            # Görüntülenecek sütunları seç
            display_cols = ['uye_no', 'ad_soyad', 'telefon', 'email', 'durum']
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
            st.metric("Toplam Üye", len(uyeler))
        else:
            st.warning("Üye bulunamadı veya sunucu bağlantısı yok")
    
    with tab2:
        with st.form("yeni_uye_form"):
            st.subheader("Yeni Üye Ekle")
            ad_soyad = st.text_input("Ad Soyad *")
            
            col1, col2 = st.columns(2)
            with col1:
                uye_no = st.text_input("Üye No")
                telefon = st.text_input("Telefon")
            with col2:
                tc_kimlik = st.text_input("TC Kimlik")
                email = st.text_input("E-posta")
            
            adres = st.text_area("Adres")
            
            if st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True):
                if ad_soyad:
                    result = api_post("/dernek/uyeler", {
                        "uye_no": uye_no,
                        "ad_soyad": ad_soyad,
                        "tc_kimlik": tc_kimlik,
                        "telefon": telefon,
                        "email": email,
                        "adres": adres
                    })
                    if result and result.get('success'):
                        st.success("✅ Üye kaydedildi! Masaüstü uygulamada da görünecek.")
                        st.rerun()
                    else:
                        st.error("❌ Kayıt başarısız")
                else:
                    st.warning("⚠️ Ad Soyad zorunludur")

# ==================== GELİRLER ====================
elif menu == "💰 Gelirler":
    st.header("💰 Gelir Kayıtları")
    
    tab1, tab2 = st.tabs(["📋 Gelir Listesi", "➕ Yeni Gelir"])
    
    with tab1:
        gelirler = api_get("/dernek/gelirler")
        
        if gelirler:
            df = pd.DataFrame(gelirler)
            display_cols = ['tarih', 'gelir_turu', 'aciklama', 'tutar', 'kaynak']
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
            st.metric("Toplam Gelir", f"₺{df['tutar'].sum():,.0f}")
        else:
            st.info("Henüz gelir kaydı yok")
    
    with tab2:
        with st.form("yeni_gelir_form"):
            st.subheader("Yeni Gelir Ekle")
            
            col1, col2 = st.columns(2)
            with col1:
                tarih = st.date_input("Tarih", value=date.today())
                tur = st.selectbox("Gelir Türü", ["AİDAT", "BAĞIŞ", "KİRA", "ETKİNLİK", "DİĞER"])
            with col2:
                tutar = st.number_input("Tutar (₺)", min_value=0.0, step=0.01)
            
            aciklama = st.text_input("Açıklama")
            
            if st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True):
                if tutar > 0:
                    result = api_post("/dernek/gelirler", {
                        "tarih": tarih.strftime('%Y-%m-%d'),
                        "tur": tur,
                        "aciklama": aciklama,
                        "tutar": tutar,
                        "kaynak": "web"
                    })
                    if result and result.get('success'):
                        st.success("✅ Gelir kaydedildi! Masaüstü uygulamada da görünecek.")
                        st.rerun()
                    else:
                        st.error("❌ Kayıt başarısız")
                else:
                    st.warning("⚠️ Tutar 0'dan büyük olmalı")

# ==================== GİDERLER ====================
elif menu == "💸 Giderler":
    st.header("💸 Gider Kayıtları")
    
    tab1, tab2 = st.tabs(["📋 Gider Listesi", "➕ Yeni Gider"])
    
    with tab1:
        giderler = api_get("/dernek/giderler")
        
        if giderler:
            df = pd.DataFrame(giderler)
            display_cols = ['tarih', 'gider_turu', 'aciklama', 'tutar', 'kaynak']
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
            st.metric("Toplam Gider", f"₺{df['tutar'].sum():,.0f}")
        else:
            st.info("Henüz gider kaydı yok")
    
    with tab2:
        with st.form("yeni_gider_form"):
            st.subheader("Yeni Gider Ekle")
            
            col1, col2 = st.columns(2)
            with col1:
                tarih = st.date_input("Tarih", value=date.today())
                tur = st.selectbox("Gider Türü", ["ELEKTRİK", "SU", "DOĞALGAZ", "KİRA", "MALZEME", "PERSONEL", "TAMİRAT", "DİĞER"])
            with col2:
                tutar = st.number_input("Tutar (₺)", min_value=0.0, step=0.01)
            
            aciklama = st.text_input("Açıklama")
            
            if st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True):
                if tutar > 0:
                    result = api_post("/dernek/giderler", {
                        "tarih": tarih.strftime('%Y-%m-%d'),
                        "tur": tur,
                        "aciklama": aciklama,
                        "tutar": tutar,
                        "kaynak": "web"
                    })
                    if result and result.get('success'):
                        st.success("✅ Gider kaydedildi! Masaüstü uygulamada da görünecek.")
                        st.rerun()
                    else:
                        st.error("❌ Kayıt başarısız")
                else:
                    st.warning("⚠️ Tutar 0'dan büyük olmalı")

# ==================== BELGE TARA (OCR) ====================
elif menu == "📸 Belge Tara":
    st.header("📸 Belge Tarama (OCR)")
    st.info("📱 Fatura, fiş veya belge görselini yükleyin. Sunucu üzerinde OCR işlemi yapılacaktır.")
    
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
                        f"{API_URL}/ocr/demo",
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
                        endpoint = "/dernek/gelirler" if kayit_turu == "Gelir" else "/dernek/giderler"
                        api_result = api_post(endpoint, {
                            "tarih": datetime.now().strftime('%Y-%m-%d'),
                            "tur": "OCR",
                            "aciklama": aciklama_input,
                            "tutar": tutar_input,
                            "kaynak": "ocr-web"
                        })
                        if api_result and api_result.get('success'):
                            st.success(f"✅ {kayit_turu} olarak kaydedildi! Masaüstü uygulamada da görünecek.")
                            st.session_state.ocr_result = None
                            st.rerun()
                        else:
                            st.error("❌ Kayıt başarısız")
                    else:
                        st.warning("⚠️ Tutar 0'dan büyük olmalı")

# ==================== RAPORLAR ====================
elif menu == "📈 Raporlar":
    st.header("📈 Raporlar")
    
    ozet = api_get("/dernek/ozet")
    
    if ozet:
        # Gelir-Gider özeti
        st.subheader("💹 Gelir-Gider Özeti")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Toplam Gelir", f"₺{ozet['toplam_gelir']:,.0f}")
        with col2:
            st.metric("💸 Toplam Gider", f"₺{ozet['toplam_gider']:,.0f}")
        with col3:
            delta_color = "normal" if ozet['net_bakiye'] >= 0 else "inverse"
            st.metric("💵 Net Bakiye", f"₺{ozet['net_bakiye']:,.0f}")
        
        st.divider()
        
        # Grafik
        st.subheader("📊 Grafik")
        chart_data = pd.DataFrame({
            'Kategori': ['Gelir', 'Gider'],
            'Tutar': [ozet['toplam_gelir'], ozet['toplam_gider']]
        })
        st.bar_chart(chart_data.set_index('Kategori'))
        
        # Son işlemler
        st.subheader("📋 Son Gelirler")
        gelirler = api_get("/dernek/gelirler")
        if gelirler:
            df = pd.DataFrame(gelirler[:5])
            display_cols = ['tarih', 'gelir_turu', 'aciklama', 'tutar']
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
        
        st.subheader("📋 Son Giderler")
        giderler = api_get("/dernek/giderler")
        if giderler:
            df = pd.DataFrame(giderler[:5])
            display_cols = ['tarih', 'gider_turu', 'aciklama', 'tutar']
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.error("❌ Sunucuya bağlanılamadı!")

# Footer
st.sidebar.divider()
st.sidebar.caption("📱 Web'den eklenen kayıtlar\nmasaüstü uygulamaya\notomatik yansır.")
