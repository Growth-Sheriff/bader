# 🏗️ BADER EKOSİSTEM MİMARİSİ

## 📊 Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BADER DERNEK YÖNETİM SİSTEMİ                        │
│                      Windows 11 Fluent Design + PyQt6                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   UI LAYER    │           │ BUSINESS LOGIC│           │  DATA LAYER   │
│   (PyQt6 +    │           │   (models.py) │           │  (database.py)│
│ QFluentWidgets│           │               │           │   SQLite      │
└───────────────┘           └───────────────┘           └───────────────┘
```

---

## 📁 Dosya Yapısı

### 🎯 Ana Giriş Noktaları
| Dosya | Açıklama |
|-------|----------|
| `main_fluent_new.py` | ✅ **ANA UYGULAMA** - Fluent UI ana pencere |
| `main.py` | Eski ana uygulama (artık kullanılmıyor) |

### 💾 Veri Katmanı
| Dosya | Açıklama |
|-------|----------|
| `database.py` | SQLite veritabanı bağlantısı ve tablo yönetimi |
| `models.py` | Tüm iş mantığı yöneticileri (Yöneticiler) |

### 🎨 UI Modülleri

#### Dernek Yönetimi
| Dosya | Widget | Açıklama |
|-------|--------|----------|
| `ui_dashboard.py` | DashboardWidget | Ana gösterge paneli |
| `ui_uyeler.py` | UyeWidget | Üye listesi ve yönetimi |
| `ui_uye_detay.py` | UyeDetayWidget | Üye detay sayfası |
| `ui_uye_aidat.py` | UyeAidatWidget | Üye aidat geçmişi |
| `ui_uyeler_ayrilan.py` | AyrilanUyelerWidget | Ayrılan üyeler |
| `ui_aidat.py` | AidatWidget | Aidat takip ve tahsilat |
| `ui_coklu_yil_odeme.py` | CokluYilOdemeFormWidget | Çok yıllık ödeme |

#### Mali Yönetim
| Dosya | Widget | Açıklama |
|-------|--------|----------|
| `ui_gelir.py` | GelirWidget | Gelir kayıtları |
| `ui_gider.py` | GiderWidget | Gider kayıtları |
| `ui_kasa.py` | KasaWidget | Kasa yönetimi |
| `ui_virman.py` | VirmanWidget | Kasalar arası transfer |
| `ui_devir.py` | DevirWidget | Yıl sonu devir işlemleri |
| `ui_tahakkuk_rapor.py` | TahakkukRaporWidget | Tahakkuk raporları |
| `ui_mali_tablolar.py` | MaliTablolarWidget | Bilanço, gelir-gider tablosu |
| `ui_butce.py` | ButceWidget | Bütçe planlama |
| `ui_alacak_verecek.py` | AlacakVerecekWidget | Alacak/verecek takibi |

#### Köy Modülü
| Dosya | Widget | Açıklama |
|-------|--------|----------|
| `ui_koy_dashboard.py` | KoyDashboardWidget | Köy özet dashboard |
| `ui_koy_islemler.py` | KoyGelirWidget | Köy gelir kayıtları |
| `ui_koy_islemler.py` | KoyGiderWidget | Köy gider kayıtları |
| `ui_koy_islemler.py` | KoyKasaWidget | Köy kasa yönetimi |
| `ui_koy_islemler.py` | KoyVirmanWidget | Köy kasaları arası transfer |

#### Diğer Modüller
| Dosya | Widget | Açıklama |
|-------|--------|----------|
| `ui_etkinlik.py` | EtkinlikWidget | Etkinlik takvimi |
| `ui_toplanti.py` | ToplantiWidget | Toplantı yönetimi |
| `ui_belgeler.py` | BelgelerWidget | Belge arşivi |
| `ui_kullanicilar.py` | KullanicilarWidget | Kullanıcı yönetimi |
| `ui_raporlar.py` | RaporlarWidget | Raporlama |
| `ui_export.py` | ExportWidget | Excel/PDF dışa aktarma |
| `ui_ayarlar.py` | AyarlarWidget | Sistem ayarları |

### 🛠️ Yardımcı Modüller
| Dosya | Açıklama |
|-------|----------|
| `ui_drawer.py` | Yan panel (Drawer) bileşeni |
| `ui_form_fields.py` | Form alanı fabrika fonksiyonları |
| `ui_helpers.py` | Yardımcı fonksiyonlar (Excel export vb.) |
| `ui_styles.py` | Stil sabitleri |
| `ui_sidebar.py` | Eski sidebar (kullanılmıyor) |
| `email_service.py` | E-posta gönderim servisi |
| `pdf_generator.py` | PDF oluşturma |

---

## 🗄️ Veritabanı Şeması

### Dernek Tabloları
```sql
uyeler              -- Üye bilgileri
aidat_tanimlari     -- Yıllık aidat tanımları
aidat_takip         -- Üye-yıl aidat durumu
aidat_odemeleri     -- Ödeme detayları
gelirler            -- Tüm gelir kayıtları
giderler            -- Tüm gider kayıtları
kasalar             -- Kasa hesapları
virmanlar           -- Kasalar arası transferler
tahakkuklar         -- Gelecek yıl tahakkukları
devir_islemleri     -- Yıl sonu devir logları
```

### Köy Tabloları
```sql
koy_kasalar         -- Köy kasa hesapları
koy_gelirleri       -- Köy gelir kayıtları
koy_giderleri       -- Köy gider kayıtları
koy_virmanlar       -- Köy kasaları arası transfer
koy_gelir_turleri   -- Köy gelir türleri
koy_gider_turleri   -- Köy gider türleri
```

### Yardımcı Tablolar
```sql
belgeler            -- Belge arşivi
etkinlikler         -- Etkinlik kayıtları
toplantilar         -- Toplantı kayıtları
butce_kalemleri     -- Bütçe planlaması
alacak_verecek      -- Alacak/verecek takibi
kullanicilar        -- Sistem kullanıcıları
islem_loglari       -- İşlem geçmişi
ayarlar             -- Sistem ayarları
```

---

## 🔧 İş Mantığı Yöneticileri (models.py)

| Yönetici | Açıklama |
|----------|----------|
| `UyeYoneticisi` | Üye CRUD işlemleri |
| `AidatYoneticisi` | Aidat takip ve tahsilat |
| `GelirYoneticisi` | Gelir kayıt ve raporlama |
| `GiderYoneticisi` | Gider kayıt ve raporlama |
| `KasaYoneticisi` | Kasa bakiye ve hareketler |
| `VirmanYoneticisi` | Transfer işlemleri |
| `TahakkukYoneticisi` | Tahakkuk raporları |
| `DevirYoneticisi` | Yıl sonu devir işlemleri |
| `RaporYoneticisi` | Genel raporlar |
| `KoyKasaYoneticisi` | Köy kasa yönetimi |
| `KoyGelirYoneticisi` | Köy gelir yönetimi |
| `KoyGiderYoneticisi` | Köy gider yönetimi |
| `KoyVirmanYoneticisi` | Köy virman yönetimi |

---

## 🔄 Veri Akışı

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   UI Form   │ ──▶ │  Yönetici   │ ──▶ │  Database   │
│  (Widget)   │     │ (models.py) │     │  (SQLite)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   ▼                   │
       │           ┌─────────────┐            │
       │           │ Validation  │            │
       │           │ & Business  │            │
       │           │   Rules     │            │
       │           └─────────────┘            │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────┐
│              Signal/Slot Bağlantıları           │
│    (Widget arası iletişim için PyQt signals)    │
└─────────────────────────────────────────────────┘
```

---

## 📋 YAPILAN DÜZELTMELER

### ✅ Kritik Hatalar Düzeltildi

| # | Dosya | Hata | Çözüm |
|---|-------|------|-------|
| 1 | `ui_koy_islemler.py` | 10 adet `MessageBox("Hata", str(e, self).show())` syntax hatası | `str(e), self` olarak düzeltildi |
| 2 | `ui_gelir.py` | `validate()` metodu tuple erişim hatası | `self.aciklama_edit[1].text()` olarak düzeltildi |
| 3 | `models.py` | `tahakkuk_ozet()` sadece gelecek yılları gösteriyordu | Filtre kaldırıldı, tüm yıllar gösteriliyor |
| 4 | Database | `koy_gelirleri` tablosu eksikti | Tablo oluşturuldu |
| 5 | Database | `koy_giderleri` tablosu eksikti | Tablo oluşturuldu |
| 6 | Database | `aidat_tanimlari` tablosu eksikti | Tablo oluşturuldu |
| 7 | Database | `butce_kalemleri` tablosu eksikti | Tablo oluşturuldu |
| 8 | Database | `alacak_verecek` tablosu eksikti | Tablo oluşturuldu |

---

## 📊 Mevcut Durum

### ✅ Çalışan Özellikler
- [x] Üye yönetimi (CRUD)
- [x] Aidat takip ve tahsilat
- [x] Çok yıllık ödeme
- [x] Gelir kayıt (tüm türler)
- [x] Gider kayıt
- [x] Kasa yönetimi
- [x] Virman (kasalar arası transfer)
- [x] Tahakkuk raporlama
- [x] Köy gelir/gider/kasa/virman
- [x] Excel dışa aktarma
- [x] Beta reset

### 📌 Navigasyon Menüsü (main_fluent_new.py)
```
TOP POSITION:
├── Dashboard
├── Üyeler
├── Ayrılan Üyeler
├── Aidat
├── Gelir
├── Gider
├── Kasa
├── Virman
├── Devir
├── Raporlar
├── Mali Tablolar
├── Tahakkuk Raporu
├── Alacak-Verecek
├── Etkinlikler
├── Toplantılar
├── Bütçe
├── ─── SEPARATOR ───
├── Köy Dashboard
├── Köy Gelir
├── Köy Gider
├── Köy Kasa
└── Köy Virman

BOTTOM POSITION:
├── Belgeler
├── Kullanıcılar
├── Dışa Aktar
├── Ayarlar
├── Çıkış
└── 🔴 BETA RESET
```

---

## 🚀 Uygulama Başlatma

```bash
# Virtual environment aktif et
source venv/bin/activate

# Uygulamayı başlat
python main_fluent_new.py
```

---

## 📦 Bağımlılıklar

```
PyQt6>=6.4.0
qfluentwidgets>=1.0.0
openpyxl>=3.0.0      # Excel desteği
matplotlib>=3.7.0    # Grafikler
reportlab>=3.6.0     # PDF desteği
```

---

## 🔐 Veritabanı Konumu

```
macOS: ~/Library/Application Support/BADER/bader_dernegi.db
Windows: %APPDATA%/BADER/bader_dernegi.db
```

---

## 📝 Notlar

1. **Drawer Pattern**: Tüm form işlemleri `DrawerPanel` içinde açılır (sağdan kayarak)
2. **Tuple Widget Pattern**: Form alanları `(container, widget)` tuple olarak döner
3. **Signal/Slot**: Widget'lar arası iletişim PyQt signals ile yapılır
4. **Fluent Design**: Windows 11 Mica/Acrylic efektleri aktif

---

*Son Güncelleme: 15 Aralık 2025*
