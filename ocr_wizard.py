"""
BADER OCR Wizard - Streamlit Multi-Step Belge Tarama
====================================================

Bu modül belge tarama işlemi için adım adım wizard arayüzü sağlar.
Streamlit session state kullanarak adımlar arası geçiş yapar.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

# OCR servisi import
try:
    from ocr_service import (
        get_ocr_service, 
        OCRResult, 
        OCRMode, 
        load_ocr_config,
        configure_server
    )
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def init_ocr_session():
    """OCR wizard için session state başlat"""
    if 'ocr_step' not in st.session_state:
        st.session_state.ocr_step = 1
    if 'ocr_result' not in st.session_state:
        st.session_state.ocr_result = None
    if 'ocr_image' not in st.session_state:
        st.session_state.ocr_image = None
    if 'ocr_document_type' not in st.session_state:
        st.session_state.ocr_document_type = None
    if 'ocr_fields' not in st.session_state:
        st.session_state.ocr_fields = {}
    if 'ocr_transaction_type' not in st.session_state:
        st.session_state.ocr_transaction_type = None


def reset_ocr_wizard():
    """Wizard'ı sıfırla"""
    st.session_state.ocr_step = 1
    st.session_state.ocr_result = None
    st.session_state.ocr_image = None
    st.session_state.ocr_document_type = None
    st.session_state.ocr_fields = {}
    st.session_state.ocr_transaction_type = None


def go_to_step(step: int):
    """Belirli adıma git"""
    st.session_state.ocr_step = step


def render_progress_bar():
    """İlerleme çubuğu göster"""
    steps = ["📤 Yükle", "🔍 Tara", "📋 Tip Seç", "✏️ Detaylar", "✅ Onayla", "💾 Kaydet"]
    current = st.session_state.ocr_step
    
    # Progress bar
    progress = (current - 1) / (len(steps) - 1)
    st.progress(progress)
    
    # Step indicators
    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps), 1):
        if i < current:
            col.markdown(f"<div style='text-align:center;color:#28a745'>✓ {step_name}</div>", 
                        unsafe_allow_html=True)
        elif i == current:
            col.markdown(f"<div style='text-align:center;color:#007bff;font-weight:bold'>{step_name}</div>", 
                        unsafe_allow_html=True)
        else:
            col.markdown(f"<div style='text-align:center;color:#6c757d'>{step_name}</div>", 
                        unsafe_allow_html=True)
    
    st.markdown("---")


def render_step_1_upload():
    """Adım 1: Görsel Yükleme"""
    st.subheader("📤 Adım 1: Belge Yükle")
    
    st.info("""
    **Desteklenen Belgeler:**
    - 📄 Fatura (e-fatura, kağıt fatura)
    - 🧾 Fiş (yazar kasa, POS)
    - 🏦 Banka Dekontu (havale, EFT)
    - 📝 Makbuz (tahsilat, ödeme)
    - 💳 Aidat Makbuzu
    """)
    
    uploaded_file = st.file_uploader(
        "Belge görselini yükleyin",
        type=['png', 'jpg', 'jpeg', 'pdf', 'webp'],
        help="PNG, JPG veya PDF formatında belge yükleyebilirsiniz"
    )
    
    if uploaded_file:
        # Görseli göster
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(uploaded_file, caption="Yüklenen Belge", use_container_width=True)
        
        with col2:
            st.markdown("**Dosya Bilgileri:**")
            st.write(f"📁 Ad: {uploaded_file.name}")
            st.write(f"📊 Boyut: {uploaded_file.size / 1024:.1f} KB")
            st.write(f"🖼️ Tip: {uploaded_file.type}")
        
        # Session'a kaydet
        st.session_state.ocr_image = uploaded_file.getvalue()
        st.session_state.ocr_filename = uploaded_file.name
        
        col1, col2 = st.columns(2)
        with col2:
            if st.button("▶️ Belgeyi Tara", type="primary", use_container_width=True):
                go_to_step(2)
                st.rerun()


def render_step_2_scan():
    """Adım 2: OCR Tarama"""
    st.subheader("🔍 Adım 2: Belge Taranıyor")
    
    if not OCR_AVAILABLE:
        st.error("""
        ⚠️ **OCR Servisi Kullanılamıyor**
        
        PaddleOCR yüklü değil. Yüklemek için:
        ```bash
        pip install paddlepaddle paddleocr
        ```
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Geri", use_container_width=True):
                go_to_step(1)
                st.rerun()
        return
    
    # OCR işlemi
    with st.spinner("🔄 Belge taranıyor... Bu işlem birkaç saniye sürebilir."):
        try:
            service = get_ocr_service()
            config = load_ocr_config()
            
            # Mod bilgisi
            if config.mode == OCRMode.SERVER:
                st.info(f"🌐 Sunucu modu: {config.server_url}")
            else:
                st.info("💻 Yerel mod: PaddleOCR")
            
            # OCR işle
            result = service.process_image_bytes(st.session_state.ocr_image)
            
            if result.success:
                st.session_state.ocr_result = result
                st.success(f"✅ Tarama başarılı! ({result.processing_time:.2f} saniye)")
                
                # Sonuçları göster
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**📝 Çıkarılan Metin:**")
                    st.text_area("Ham Metin", result.raw_text, height=200, disabled=True)
                
                with col2:
                    st.markdown("**📊 İstatistikler:**")
                    st.metric("Satır Sayısı", len(result.lines))
                    st.metric("Güven Skoru", f"{result.confidence * 100:.1f}%")
                    
                    if result.document_type:
                        st.info(f"🏷️ Tespit: **{result.document_type.upper()}**")
                    
                    if result.fields:
                        st.markdown("**Bulunan Alanlar:**")
                        for field in result.fields:
                            st.write(f"• {field.field_name}: {field.value}")
                
                # Devam butonu
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⬅️ Tekrar Yükle", use_container_width=True):
                        go_to_step(1)
                        st.rerun()
                with col2:
                    if st.button("▶️ Devam Et", type="primary", use_container_width=True):
                        go_to_step(3)
                        st.rerun()
            else:
                st.error(f"❌ Tarama hatası: {result.error_message}")
                
                if st.button("⬅️ Geri Dön"):
                    go_to_step(1)
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
            
            if st.button("⬅️ Geri Dön"):
                go_to_step(1)
                st.rerun()


def render_step_3_type_select():
    """Adım 3: Belge Tipi Seçimi"""
    st.subheader("📋 Adım 3: Belge Tipi")
    
    result = st.session_state.ocr_result
    
    # Otomatik tespit
    detected_type = result.document_type if result else None
    
    st.markdown("**Belge tipini seçin veya otomatik tespiti onaylayın:**")
    
    document_types = {
        'fatura': ('📄 Fatura', 'Satın alınan mal veya hizmet faturası'),
        'fiş': ('🧾 Fiş', 'Yazar kasa fişi, POS slibi'),
        'dekont': ('🏦 Dekont', 'Banka havalesi, EFT dekontu'),
        'makbuz': ('📝 Makbuz', 'Tahsilat veya ödeme makbuzu'),
        'aidat': ('💳 Aidat', 'Üyelik aidatı makbuzu'),
    }
    
    # Tip seçimi
    cols = st.columns(len(document_types))
    
    selected_type = st.session_state.ocr_document_type or detected_type
    
    for (key, (icon_name, desc)), col in zip(document_types.items(), cols):
        with col:
            is_detected = key == detected_type
            is_selected = key == selected_type
            
            button_label = icon_name
            if is_detected:
                button_label += " ✓"
            
            if st.button(
                button_label, 
                key=f"type_{key}",
                type="primary" if is_selected else "secondary",
                use_container_width=True
            ):
                st.session_state.ocr_document_type = key
                st.rerun()
            
            st.caption(desc)
    
    if selected_type:
        st.success(f"Seçilen tip: **{document_types[selected_type][0]}**")
    
    # İşlem tipi
    st.markdown("---")
    st.markdown("**Bu belge hangi işlem için?**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 GELİR", 
                    type="primary" if st.session_state.ocr_transaction_type == 'gelir' else "secondary",
                    use_container_width=True):
            st.session_state.ocr_transaction_type = 'gelir'
            st.rerun()
        st.caption("Derneğe gelen para")
    
    with col2:
        if st.button("📤 GİDER", 
                    type="primary" if st.session_state.ocr_transaction_type == 'gider' else "secondary",
                    use_container_width=True):
            st.session_state.ocr_transaction_type = 'gider'
            st.rerun()
        st.caption("Dernekten çıkan para")
    
    with col3:
        if st.button("💳 AİDAT", 
                    type="primary" if st.session_state.ocr_transaction_type == 'aidat' else "secondary",
                    use_container_width=True):
            st.session_state.ocr_transaction_type = 'aidat'
            st.rerun()
        st.caption("Üye aidat ödemesi")
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Geri", use_container_width=True):
            go_to_step(2)
            st.rerun()
    
    with col2:
        can_continue = selected_type and st.session_state.ocr_transaction_type
        if st.button("▶️ Devam Et", type="primary", disabled=not can_continue, use_container_width=True):
            go_to_step(4)
            st.rerun()
        
        if not can_continue:
            st.caption("Belge tipi ve işlem tipini seçin")


def render_step_4_details():
    """Adım 4: Detay Düzenleme"""
    st.subheader("✏️ Adım 4: Detayları Düzenle")
    
    result = st.session_state.ocr_result
    doc_type = st.session_state.ocr_document_type
    trans_type = st.session_state.ocr_transaction_type
    
    # OCR'dan çıkarılan değerleri al
    ocr_fields = {f.field_name: f.parsed_value for f in result.fields} if result else {}
    
    st.info(f"🏷️ **{doc_type.upper()}** → **{trans_type.upper()}** işlemi")
    
    # Form alanları
    col1, col2 = st.columns(2)
    
    with col1:
        # Tarih
        ocr_date = ocr_fields.get('tarih', datetime.now().strftime('%Y-%m-%d'))
        try:
            default_date = datetime.strptime(ocr_date, '%Y-%m-%d').date()
        except:
            default_date = datetime.now().date()
        
        tarih = st.date_input(
            "📅 Tarih *",
            value=default_date,
            help="İşlem tarihi"
        )
        st.session_state.ocr_fields['tarih'] = tarih.strftime('%Y-%m-%d')
        
        # Tutar
        ocr_amount = ocr_fields.get('tutar', 0.0)
        tutar = st.number_input(
            "💰 Tutar (TL) *",
            value=float(ocr_amount) if ocr_amount else 0.0,
            min_value=0.0,
            step=0.01,
            format="%.2f",
            help="İşlem tutarı"
        )
        st.session_state.ocr_fields['tutar'] = tutar
    
    with col2:
        # Açıklama
        default_desc = f"{doc_type} - {result.lines[0] if result and result.lines else ''}"[:100]
        aciklama = st.text_input(
            "📝 Açıklama *",
            value=default_desc,
            help="İşlem açıklaması"
        )
        st.session_state.ocr_fields['aciklama'] = aciklama
        
        # Belge No
        belge_no = ocr_fields.get('belge_no', '')
        belge_no = st.text_input(
            "🔢 Belge No",
            value=belge_no,
            help="Fatura/Fiş numarası (opsiyonel)"
        )
        st.session_state.ocr_fields['belge_no'] = belge_no
    
    # İşlem tipine göre ek alanlar
    if trans_type == 'gelir':
        st.markdown("---")
        st.markdown("**Gelir Detayları**")
        
        col1, col2 = st.columns(2)
        with col1:
            gelir_tipleri = ['Bağış', 'Aidat', 'Etkinlik Geliri', 'Faiz Geliri', 'Diğer']
            gelir_tipi = st.selectbox("Gelir Tipi", gelir_tipleri)
            st.session_state.ocr_fields['gelir_tipi'] = gelir_tipi
        
        with col2:
            odeme_yontemleri = ['Nakit', 'Banka', 'Kredi Kartı', 'Havale/EFT']
            odeme_yontemi = st.selectbox("Ödeme Yöntemi", odeme_yontemleri)
            st.session_state.ocr_fields['odeme_yontemi'] = odeme_yontemi
    
    elif trans_type == 'gider':
        st.markdown("---")
        st.markdown("**Gider Detayları**")
        
        col1, col2 = st.columns(2)
        with col1:
            gider_tipleri = ['Kira', 'Fatura', 'Malzeme', 'Personel', 'Etkinlik', 'Diğer']
            gider_tipi = st.selectbox("Gider Tipi", gider_tipleri)
            st.session_state.ocr_fields['gider_tipi'] = gider_tipi
        
        with col2:
            odeme_yontemleri = ['Nakit', 'Banka', 'Kredi Kartı', 'Havale/EFT']
            odeme_yontemi = st.selectbox("Ödeme Yöntemi", odeme_yontemleri)
            st.session_state.ocr_fields['odeme_yontemi'] = odeme_yontemi
    
    elif trans_type == 'aidat':
        st.markdown("---")
        st.markdown("**Aidat Detayları**")
        
        col1, col2 = st.columns(2)
        with col1:
            # Üye seçimi (demo verilerden)
            uyeler = ['Ahmet Yılmaz', 'Mehmet Demir', 'Ayşe Kaya', 'Fatma Şahin', 'Ali Öztürk']
            uye = st.selectbox("Üye Seçin", uyeler)
            st.session_state.ocr_fields['uye'] = uye
        
        with col2:
            yil = st.number_input("Yıl", value=datetime.now().year, min_value=2020, max_value=2030)
            st.session_state.ocr_fields['yil'] = yil
    
    # IBAN varsa göster
    if ocr_fields.get('iban'):
        st.markdown("---")
        iban = st.text_input("🏦 IBAN", value=ocr_fields['iban'], disabled=True)
        st.session_state.ocr_fields['iban'] = iban
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Geri", use_container_width=True):
            go_to_step(3)
            st.rerun()
    
    with col2:
        can_continue = tutar > 0 and aciklama
        if st.button("▶️ Önizleme", type="primary", disabled=not can_continue, use_container_width=True):
            go_to_step(5)
            st.rerun()
        
        if not can_continue:
            st.caption("Tutar ve açıklama zorunludur")


def render_step_5_confirm():
    """Adım 5: Onay"""
    st.subheader("✅ Adım 5: İşlemi Onaylayın")
    
    fields = st.session_state.ocr_fields
    doc_type = st.session_state.ocr_document_type
    trans_type = st.session_state.ocr_transaction_type
    
    # Özet kartı
    st.markdown("### 📋 İşlem Özeti")
    
    # Tip badge
    type_colors = {'gelir': '🟢', 'gider': '🔴', 'aidat': '🔵'}
    type_names = {'gelir': 'GELİR', 'gider': 'GİDER', 'aidat': 'AİDAT'}
    
    st.markdown(f"""
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid {'#28a745' if trans_type == 'gelir' else '#dc3545' if trans_type == 'gider' else '#007bff'}">
        <h3>{type_colors.get(trans_type, '⚪')} {type_names.get(trans_type, 'İŞLEM')}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Temel Bilgiler:**")
        st.write(f"📅 Tarih: **{fields.get('tarih', '-')}**")
        st.write(f"💰 Tutar: **{fields.get('tutar', 0):.2f} TL**")
        st.write(f"📝 Açıklama: {fields.get('aciklama', '-')}")
        st.write(f"🏷️ Belge Tipi: {doc_type}")
    
    with col2:
        st.markdown("**Ek Bilgiler:**")
        if fields.get('belge_no'):
            st.write(f"🔢 Belge No: {fields['belge_no']}")
        if fields.get('gelir_tipi'):
            st.write(f"📥 Gelir Tipi: {fields['gelir_tipi']}")
        if fields.get('gider_tipi'):
            st.write(f"📤 Gider Tipi: {fields['gider_tipi']}")
        if fields.get('odeme_yontemi'):
            st.write(f"💳 Ödeme: {fields['odeme_yontemi']}")
        if fields.get('uye'):
            st.write(f"👤 Üye: {fields['uye']}")
        if fields.get('yil'):
            st.write(f"📆 Yıl: {fields['yil']}")
    
    # Orijinal görsel
    st.markdown("---")
    with st.expander("🖼️ Orijinal Belge Görseli"):
        if st.session_state.ocr_image:
            st.image(st.session_state.ocr_image, caption="Taranan Belge", width=400)
    
    # OCR metni
    with st.expander("📝 OCR Çıktısı"):
        if st.session_state.ocr_result:
            st.text(st.session_state.ocr_result.raw_text)
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⬅️ Düzenle", use_container_width=True):
            go_to_step(4)
            st.rerun()
    
    with col2:
        if st.button("💾 KAYDET", type="primary", use_container_width=True):
            go_to_step(6)
            st.rerun()


def render_step_6_save():
    """Adım 6: Kaydetme"""
    st.subheader("💾 Adım 6: Kayıt Tamamlandı")
    
    fields = st.session_state.ocr_fields
    trans_type = st.session_state.ocr_transaction_type
    
    # Kayıt simülasyonu
    with st.spinner("Kaydediliyor..."):
        import time
        time.sleep(1)  # Simülasyon
    
    # Başarı mesajı
    st.balloons()
    
    st.success(f"""
    ✅ **İşlem Başarıyla Kaydedildi!**
    
    - 📅 Tarih: {fields.get('tarih')}
    - 💰 Tutar: {fields.get('tutar', 0):.2f} TL
    - 📝 Açıklama: {fields.get('aciklama')}
    - 🏷️ Tip: {trans_type.upper()}
    """)
    
    # İşlem ID (simülasyon)
    import random
    islem_id = random.randint(10000, 99999)
    st.info(f"📋 İşlem No: **#{islem_id}**")
    
    # Sonraki adımlar
    st.markdown("---")
    st.markdown("### Sonraki Adımlar")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Yeni Belge Tara", type="primary", use_container_width=True):
            reset_ocr_wizard()
            st.rerun()
    
    with col2:
        if st.button("📋 İşlemlere Git", use_container_width=True):
            st.session_state.menu = "Gelirler" if trans_type == 'gelir' else "Giderler"
            reset_ocr_wizard()
            st.rerun()
    
    with col3:
        if st.button("🏠 Ana Sayfa", use_container_width=True):
            st.session_state.menu = "Dashboard"
            reset_ocr_wizard()
            st.rerun()


def render_ocr_settings():
    """OCR Ayarları"""
    st.markdown("### ⚙️ OCR Ayarları")
    
    config = load_ocr_config() if OCR_AVAILABLE else None
    
    with st.expander("Sunucu Yapılandırması", expanded=False):
        st.markdown("""
        **Not:** Sunucu bilgileri henüz yapılandırılmamış.
        Sunucu URL ve API anahtarı daha sonra eklenecektir.
        """)
        
        # Mod seçimi
        mode = st.radio(
            "OCR Modu",
            ["Yerel (PaddleOCR)", "Sunucu (API)"],
            index=0 if not config or config.mode == OCRMode.LOCAL else 1
        )
        
        if mode == "Sunucu (API)":
            st.warning("⚠️ Sunucu bilgileri henüz yapılandırılmamış.")
            
            server_url = st.text_input(
                "Sunucu URL",
                value=config.server_url if config else "",
                placeholder="http://192.168.1.100:8000"
            )
            
            api_key = st.text_input(
                "API Anahtarı",
                value=config.server_api_key if config else "",
                type="password",
                placeholder="your-api-key"
            )
            
            if st.button("Sunucu Ayarlarını Kaydet"):
                if server_url:
                    configure_server(server_url, api_key)
                    st.success("✅ Sunucu ayarları kaydedildi!")
                else:
                    st.error("Sunucu URL gereklidir")
        else:
            st.info("💻 Yerel mod: PaddleOCR kullanılıyor")
            
            if not OCR_AVAILABLE:
                st.error("""
                PaddleOCR yüklü değil. Yüklemek için:
                ```bash
                pip install paddlepaddle paddleocr
                ```
                """)


def render_ocr_page():
    """
    Ana OCR sayfası - Streamlit'e entegre edilecek
    """
    st.title("📸 Belge Tarama (OCR)")
    
    # Session başlat
    init_ocr_session()
    
    # Ayarlar sidebar'ında göster
    with st.sidebar:
        render_ocr_settings()
    
    # Progress bar
    render_progress_bar()
    
    # Adıma göre içerik göster
    step = st.session_state.ocr_step
    
    if step == 1:
        render_step_1_upload()
    elif step == 2:
        render_step_2_scan()
    elif step == 3:
        render_step_3_type_select()
    elif step == 4:
        render_step_4_details()
    elif step == 5:
        render_step_5_confirm()
    elif step == 6:
        render_step_6_save()


# Test için
if __name__ == "__main__":
    st.set_page_config(
        page_title="BADER OCR Test",
        page_icon="📸",
        layout="wide"
    )
    render_ocr_page()
