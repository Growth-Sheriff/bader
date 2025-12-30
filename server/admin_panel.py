"""
BADER Admin Panel - Lisans ve Güncelleme Yönetimi
Streamlit Web Uygulaması
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json

# Konfigürasyon
API_URL = "http://127.0.0.1:8000"  # Sunucuda localhost
ADMIN_SECRET = "BADER_ADMIN_2024_SUPER_SECRET"

st.set_page_config(
    page_title="BADER Admin Panel",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 8px;
        padding: 1rem;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


def api_request(method: str, endpoint: str, data: dict = None, files: dict = None):
    """API isteği gönder"""
    headers = {"X-Admin-Key": ADMIN_SECRET}
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=data, timeout=30)
        elif method == "POST":
            if files:
                resp = requests.post(url, headers=headers, files=files, timeout=120)
            else:
                resp = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return None, "Geçersiz method"
        
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, f"HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return None, str(e)


def show_dashboard():
    """Ana Dashboard"""
    st.markdown('<p class="main-header">📊 Admin Dashboard</p>', unsafe_allow_html=True)
    
    data, error = api_request("GET", "/admin/dashboard")
    
    if error:
        st.error(f"Dashboard yüklenemedi: {error}")
        return
    
    # Metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Toplam Müşteri", data.get("toplam_musteri", 0))
    
    with col2:
        st.metric("📱 24s Aktivasyon", data.get("aktivasyon_24h", 0))
    
    with col3:
        st.metric("📦 Aktif Versiyon", data.get("aktif_versiyon", "1.0.0"))
    
    with col4:
        st.metric("📄 Bekleyen Belge", data.get("bekleyen_belge", 0))
    
    st.divider()
    
    # Plan dağılımı
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Plan Dağılımı")
        plan_dagilim = data.get("plan_dagilim", {})
        if plan_dagilim:
            df = pd.DataFrame(list(plan_dagilim.items()), columns=["Plan", "Sayı"])
            st.bar_chart(df.set_index("Plan"))
        else:
            st.info("Henüz müşteri yok")
    
    with col2:
        st.subheader("📈 Haftalık Aktivasyon")
        st.metric("Son 7 Gün", data.get("aktivasyon_7d", 0))


def show_musteriler():
    """Müşteri/Lisans Yönetimi"""
    st.markdown('<p class="main-header">👥 Müşteri & Lisans Yönetimi</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Müşteri Listesi", "➕ Yeni Müşteri"])
    
    with tab1:
        data, error = api_request("GET", "/admin/musteriler")
        
        if error:
            st.error(f"Müşteriler yüklenemedi: {error}")
            return
        
        musteriler = data.get("musteriler", [])
        
        if not musteriler:
            st.info("Henüz müşteri eklenmemiş. Yeni müşteri oluşturmak için 'Yeni Müşteri' sekmesini kullanın.")
            return
        
        # Tablo
        df = pd.DataFrame(musteriler)
        
        # Sütun seçimi
        columns_to_show = ["customer_id", "name", "email", "plan", "aktif", "expires", "last_seen"]
        df_display = df[[col for col in columns_to_show if col in df.columns]]
        
        st.dataframe(df_display, use_container_width=True)
        
        # Detay görüntüleme
        st.divider()
        st.subheader("🔍 Müşteri Detay")
        
        selected_customer = st.selectbox(
            "Müşteri Seç",
            options=[m["customer_id"] for m in musteriler],
            format_func=lambda x: f"{x} - {next((m['name'] for m in musteriler if m['customer_id'] == x), '')}"
        )
        
        if selected_customer:
            musteri = next((m for m in musteriler if m["customer_id"] == selected_customer), None)
            if musteri:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("Customer ID", value=musteri["customer_id"], disabled=True)
                    st.text_input("API Key", value=musteri.get("api_key", ""), disabled=True)
                    st.text_input("İsim", value=musteri.get("name", ""))
                    st.text_input("E-posta", value=musteri.get("email", ""))
                
                with col2:
                    st.text_input("Plan", value=musteri.get("plan", ""))
                    st.text_input("Bitiş Tarihi", value=musteri.get("expires", ""))
                    st.text_input("Son Görülme", value=musteri.get("last_seen", "Henüz yok"))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 API Key Yenile", type="secondary"):
                        resp, err = api_request("POST", f"/admin/musteriler/{selected_customer}/yenile-api-key")
                        if err:
                            st.error(err)
                        else:
                            st.success(f"Yeni API Key: {resp.get('api_key')}")
                            st.rerun()
                
                with col2:
                    if st.button("🗑️ Devre Dışı Bırak", type="secondary"):
                        resp, err = api_request("DELETE", f"/admin/musteriler/{selected_customer}")
                        if err:
                            st.error(err)
                        else:
                            st.success("Müşteri devre dışı bırakıldı")
                            st.rerun()
    
    with tab2:
        st.subheader("➕ Yeni Müşteri Oluştur")
        
        with st.form("new_customer_form"):
            name = st.text_input("Dernek/Kuruluş Adı *")
            email = st.text_input("E-posta")
            telefon = st.text_input("Telefon")
            adres = st.text_area("Adres")
            
            col1, col2 = st.columns(2)
            with col1:
                plan = st.selectbox("Plan", ["demo", "basic", "pro", "enterprise"])
                max_kullanici = st.number_input("Max Kullanıcı", min_value=1, max_value=100, value=5)
            
            with col2:
                max_uye = st.number_input("Max Üye", min_value=10, max_value=10000, value=500)
                expires = st.date_input("Bitiş Tarihi", value=datetime.now() + timedelta(days=365))
            
            notes = st.text_area("Notlar")
            
            submitted = st.form_submit_button("✅ Müşteri Oluştur", type="primary")
            
            if submitted:
                if not name:
                    st.error("Dernek/Kuruluş adı zorunludur")
                else:
                    data = {
                        "name": name,
                        "email": email,
                        "telefon": telefon,
                        "adres": adres,
                        "plan": plan,
                        "max_kullanici": max_kullanici,
                        "max_uye": max_uye,
                        "expires": expires.strftime("%Y-%m-%d"),
                        "notes": notes
                    }
                    
                    resp, err = api_request("POST", "/admin/musteriler", data)
                    
                    if err:
                        st.error(f"Hata: {err}")
                    else:
                        st.success("✅ Müşteri başarıyla oluşturuldu!")
                        st.markdown(f"""
                        <div class="success-box">
                            <strong>Customer ID:</strong> {resp.get('customer_id')}<br>
                            <strong>API Key:</strong> {resp.get('api_key')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Kopyalanabilir bilgi
                        st.code(f"""
Lisans Bilgileri
================
Customer ID: {resp.get('customer_id')}
API Key: {resp.get('api_key')}
                        """)


def show_versions():
    """Güncelleme Yönetimi"""
    st.markdown('<p class="main-header">📦 Güncelleme Yönetimi</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Versiyon Listesi", "➕ Yeni Versiyon"])
    
    with tab1:
        data, error = api_request("GET", "/admin/versions")
        
        if error:
            st.error(f"Versiyonlar yüklenemedi: {error}")
            return
        
        versions = data.get("versions", [])
        
        if not versions:
            st.info("Henüz versiyon eklenmemiş")
        else:
            for v in versions:
                with st.expander(f"📦 v{v['version']} - {'🟢 Aktif' if v.get('is_active') else '⚪ Pasif'}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Platform:** {v.get('platform', 'all')}")
                        st.write(f"**Kritik:** {'✅ Evet' if v.get('is_critical') else '❌ Hayır'}")
                        st.write(f"**Boyut:** {v.get('file_size', 0) / 1024 / 1024:.2f} MB" if v.get('file_size') else "Dosya yüklenmedi")
                    
                    with col2:
                        st.write(f"**Yayın Tarihi:** {v.get('released_at', '')}")
                        st.write(f"**Min. Versiyon:** {v.get('min_required_version', '-')}")
                        if v.get('download_url'):
                            st.write(f"**Download:** `{v.get('download_url')}`")
                    
                    if v.get('changelog'):
                        st.markdown("**Değişiklikler:**")
                        st.markdown(v.get('changelog'))
    
    with tab2:
        st.subheader("➕ Yeni Versiyon Yayınla")
        
        with st.form("new_version_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                version = st.text_input("Versiyon *", placeholder="1.0.1")
                platform = st.selectbox("Platform", ["all", "macos", "windows", "linux"])
            
            with col2:
                min_required = st.text_input("Minimum Gerekli Versiyon", placeholder="1.0.0")
                is_critical = st.checkbox("Kritik Güncelleme (Zorla)")
            
            changelog = st.text_area("Değişiklik Notları (Markdown)", height=150, placeholder="""
## Yenilikler
- Yeni özellik 1
- Yeni özellik 2

## Düzeltmeler
- Bug fix 1
- Bug fix 2
            """)
            
            submitted = st.form_submit_button("📝 Versiyon Kaydı Oluştur", type="primary")
            
            if submitted:
                if not version:
                    st.error("Versiyon numarası zorunludur")
                else:
                    data = {
                        "version": version,
                        "platform": platform,
                        "changelog": changelog,
                        "min_required_version": min_required if min_required else None,
                        "is_critical": is_critical
                    }
                    
                    resp, err = api_request("POST", "/admin/versions", data)
                    
                    if err:
                        st.error(f"Hata: {err}")
                    else:
                        st.success(f"✅ Versiyon {version} kaydı oluşturuldu!")
                        st.session_state["new_version"] = version
        
        # Dosya yükleme (form dışında)
        st.divider()
        st.subheader("📤 Güncelleme Dosyası Yükle")
        
        version_to_upload = st.text_input("Versiyon", value=st.session_state.get("new_version", ""))
        uploaded_file = st.file_uploader("Uygulama Dosyası (.app, .exe, .dmg, .zip)", 
                                         type=["app", "exe", "dmg", "zip", "pkg"])
        
        if uploaded_file and version_to_upload:
            if st.button("📤 Dosyayı Yükle", type="primary"):
                with st.spinner("Yükleniyor..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    resp, err = api_request("POST", f"/admin/versions/{version_to_upload}/upload", files=files)
                    
                    if err:
                        st.error(f"Yükleme hatası: {err}")
                    else:
                        st.success(f"✅ Dosya yüklendi! {resp.get('size', 0) / 1024 / 1024:.2f} MB")
                        st.write(f"**Download URL:** `{resp.get('download_url')}`")


def show_logs():
    """Aktivasyon Logları"""
    st.markdown('<p class="main-header">📜 Aktivasyon Logları</p>', unsafe_allow_html=True)
    
    data, error = api_request("GET", "/admin/aktivasyon-loglari", {"limit": 100})
    
    if error:
        st.error(f"Loglar yüklenemedi: {error}")
        return
    
    logs = data.get("logs", [])
    
    if not logs:
        st.info("Henüz aktivasyon logu yok")
        return
    
    # Filtreler
    col1, col2 = st.columns(2)
    with col1:
        filter_success = st.selectbox("Durum", ["Tümü", "Başarılı", "Başarısız"])
    with col2:
        filter_customer = st.text_input("Customer ID Filtre")
    
    # Filtreleme
    filtered_logs = logs
    if filter_success == "Başarılı":
        filtered_logs = [l for l in filtered_logs if l.get("success")]
    elif filter_success == "Başarısız":
        filtered_logs = [l for l in filtered_logs if not l.get("success")]
    
    if filter_customer:
        filtered_logs = [l for l in filtered_logs if filter_customer.lower() in (l.get("customer_id") or "").lower()]
    
    # Tablo
    if filtered_logs:
        df = pd.DataFrame(filtered_logs)
        columns = ["created_at", "customer_id", "success", "message", "ip_address"]
        df_display = df[[col for col in columns if col in df.columns]]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Filtre kriterlerine uygun log bulunamadı")


def show_settings():
    """Ayarlar"""
    st.markdown('<p class="main-header">⚙️ Ayarlar</p>', unsafe_allow_html=True)
    
    st.subheader("🔑 Admin Ayarları")
    
    st.warning("⚠️ Bu ayarlar sunucu restart gerektirir")
    
    current_secret = st.text_input("Mevcut Admin Secret", type="password")
    new_secret = st.text_input("Yeni Admin Secret", type="password")
    confirm_secret = st.text_input("Yeni Secret (Tekrar)", type="password")
    
    if st.button("🔄 Secret Güncelle"):
        if current_secret != ADMIN_SECRET:
            st.error("Mevcut secret yanlış")
        elif new_secret != confirm_secret:
            st.error("Yeni secret'lar eşleşmiyor")
        elif len(new_secret) < 16:
            st.error("Secret en az 16 karakter olmalı")
        else:
            st.info("Secret'ı güncellemek için sunucu kodunda ADMIN_SECRET değişkenini değiştirin")
            st.code(f'ADMIN_SECRET = "{new_secret}"')
    
    st.divider()
    st.subheader("📊 API Durumu")
    
    resp, err = api_request("GET", "/health")
    if err:
        st.error(f"API bağlantı hatası: {err}")
    else:
        st.success(f"✅ API Aktif - Versiyon: {resp.get('version', 'N/A')}")


# Sidebar menü
def main():
    st.sidebar.image("https://via.placeholder.com/150x50?text=BADER", width=150)
    st.sidebar.title("Admin Panel")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Menü",
        ["📊 Dashboard", "👥 Müşteriler", "📦 Güncellemeler", "📜 Loglar", "⚙️ Ayarlar"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if menu == "📊 Dashboard":
        show_dashboard()
    elif menu == "👥 Müşteriler":
        show_musteriler()
    elif menu == "📦 Güncellemeler":
        show_versions()
    elif menu == "📜 Loglar":
        show_logs()
    elif menu == "⚙️ Ayarlar":
        show_settings()


if __name__ == "__main__":
    main()
