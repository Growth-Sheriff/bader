# BADER Mimari Refactor Planı

## 📋 Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SÜPER ADMIN PANELİ                                │
│  (admin.bfrdernek.com)                                                      │
│  • Tüm müşteriler • Lisanslar • Kullanım istatistikleri • Versiyon yönetimi │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANA SUNUCU (API Gateway)                            │
│  (api.bfrdernek.com)                                                        │
│  • Lisans doğrulama • Versiyon kontrolü • Online kullanıcı verileri        │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
        ┌───────────┴───────────┐            ┌───────────┴───────────┐
        ▼                       ▼            ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  ONLINE       │    │  ONLINE       │    │  LOCAL        │    │  LOCAL        │
│  Müşteri A    │    │  Müşteri B    │    │  Müşteri C    │    │  Müşteri D    │
│  (Web+Desktop)│    │  (Web Only)   │    │  (Desktop)    │    │  (Desktop)    │
│  PostgreSQL   │    │  PostgreSQL   │    │  SQLite       │    │  SQLite       │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

---

## 🔑 Lisans Tipleri

| Tip | Kod Prefix | Özellikler | Veritabanı | Fiyat |
|-----|------------|------------|------------|-------|
| **LOCAL** | `BADER-LOCAL-XXXX` | Tek bilgisayar, offline | SQLite (lokal) | Düşük |
| **ONLINE** | `BADER-ONLINE-XXXX` | Web + Desktop, senkron | PostgreSQL (sunucu) | Yüksek |
| **HYBRID** | `BADER-HYBRID-XXXX` | Offline + sync | SQLite + PostgreSQL | Orta |
| **DEMO** | `BADER-DEMO-XXXX` | 30 gün deneme | SQLite/PostgreSQL | Ücretsiz |

### Lisans Kodu Yapısı
```
BADER-[TİP]-[YIL]-[UNIQ_ID]
Örnek: BADER-ONLINE-2025-A1B2C3
```

---

## 📦 Veritabanı Mimarisi

### 1. Merkezi Veritabanı (Sunucu)

```sql
-- Süper Admin için merkezi tablolar
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,  -- BADER-ONLINE-2025-XXXX
    organization_name VARCHAR(200),
    contact_name VARCHAR(100),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    license_type VARCHAR(20),  -- LOCAL, ONLINE, HYBRID, DEMO
    license_status VARCHAR(20), -- ACTIVE, SUSPENDED, EXPIRED, TRIAL
    license_start DATE,
    license_end DATE,
    max_users INT DEFAULT 5,
    max_members INT DEFAULT 500,
    features JSONB,  -- Enabled features
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP,
    app_version VARCHAR(20),
    os_info VARCHAR(100)
);

CREATE TABLE license_logs (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50),
    action VARCHAR(50),  -- ACTIVATE, DEACTIVATE, LOGIN, SYNC, UPDATE
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE app_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL,
    platform VARCHAR(20),  -- windows, macos, linux
    download_url TEXT,
    release_notes TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    min_supported_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Online müşteri verileri (her müşteri için ayrı schema veya customer_id ile filtreleme)
-- members, incomes, expenses, dues, etc.
```

### 2. Lokal Veritabanı (SQLite)

```sql
-- Local lisanslı kullanıcılar için
-- Mevcut yapı korunur, ek olarak:
CREATE TABLE sync_status (
    id INTEGER PRIMARY KEY,
    last_sync DATETIME,
    sync_type TEXT,  -- FULL, INCREMENTAL
    status TEXT,     -- SUCCESS, FAILED, PENDING
    error_message TEXT
);

CREATE TABLE license_cache (
    id INTEGER PRIMARY KEY,
    customer_id TEXT,
    license_type TEXT,
    license_status TEXT,
    license_end DATE,
    last_verified DATETIME,
    offline_days_allowed INTEGER DEFAULT 30
);
```

---

## 🔄 Senaryolar ve Akışlar

### Senaryo 1: ONLINE Kullanıcı (Web + Desktop)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Desktop    │────▶│   Sunucu     │◀────│     Web      │
│   App        │     │   API        │     │   App        │
│              │     │  PostgreSQL  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     Gerçek zamanlı
                     senkronizasyon
```

**Akış:**
1. Desktop açılır → Lisans kontrol edilir (API)
2. Lisans ONLINE ise → Tüm veriler API'den
3. Web'de değişiklik → Desktop'ta anında görünür
4. İnternet yoksa → Hata mesajı (çalışmaz)

### Senaryo 2: LOCAL Kullanıcı (Sadece Desktop)

```
┌──────────────┐     ┌──────────────┐
│   Desktop    │────▶│   Sunucu     │
│   App        │     │   (Sadece    │
│   SQLite     │     │   lisans)    │
└──────────────┘     └──────────────┘
       │
       ▼
   Lokal veri
   (tek bilgisayar)
```

**Akış:**
1. Desktop açılır → Lisans kontrol edilir (API, cache'li)
2. Lisans LOCAL ise → Tüm veriler SQLite'tan
3. İnternet yoksa → Cache'li lisans ile 30 gün çalışır
4. Web erişimi YOK

### Senaryo 3: HYBRID Kullanıcı (Offline + Sync)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Desktop    │◀───▶│   Sunucu     │◀────│     Web      │
│   App        │sync │   API        │     │   App        │
│   SQLite     │     │  PostgreSQL  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       ▼
   Offline da
   çalışır
```

**Akış:**
1. Desktop açılır → Lisans kontrol (online/offline)
2. Online ise → Sunucuyla senkronize et
3. Offline ise → Lokal SQLite kullan
4. Tekrar online olunca → Değişiklikleri senkronize et
5. Çakışma yönetimi gerekli

### Senaryo 4: LOCAL → ONLINE Geçişi

```
1. Süper Admin yeni ONLINE lisans oluşturur
2. Kullanıcı desktop'tan "Lisans Yükselt" seçer
3. Mevcut SQLite verileri sunucuya migrate edilir
4. Artık ONLINE olarak çalışır
5. Web erişimi aktif olur
```

### Senaryo 5: Demo → Ücretli Geçiş

```
1. 30 gün demo süresi dolar
2. Kullanıcı ödeme yapar
3. Süper Admin lisansı aktifleştirir
4. Lisans tipi güncellenir (LOCAL/ONLINE)
5. Mevcut veriler korunur
```

---

## 🛡️ Süper Admin Paneli

### Özellikler

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BADER SÜPER ADMIN                                        [admin@bader.com] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📊 DASHBOARD                                                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │ Toplam     │ │ Aktif      │ │ Demo       │ │ Bu Ay      │               │
│  │ Müşteri    │ │ Lisans     │ │ Deneme     │ │ Gelir      │               │
│  │    156     │ │    142     │ │     8      │ │  ₺45.600   │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
│                                                                              │
│  📋 MENÜ                                                                    │
│  ├── Müşteriler                                                             │
│  │   ├── Tüm Müşteriler                                                     │
│  │   ├── Aktif Lisanslar                                                    │
│  │   ├── Süresi Dolanlar                                                    │
│  │   └── Demo Kullanıcılar                                                  │
│  ├── Lisans Yönetimi                                                        │
│  │   ├── Yeni Lisans Oluştur                                                │
│  │   ├── Lisans Yükselt/Düşür                                               │
│  │   └── Lisans İptal                                                       │
│  ├── Versiyon Yönetimi                                                      │
│  │   ├── Güncel Versiyon                                                    │
│  │   ├── Yeni Versiyon Yükle                                                │
│  │   └── Güncelleme Logları                                                 │
│  ├── İstatistikler                                                          │
│  │   ├── Kullanım Raporları                                                 │
│  │   ├── Gelir Raporları                                                    │
│  │   └── Hata Logları                                                       │
│  └── Ayarlar                                                                │
│      ├── Admin Kullanıcıları                                                │
│      ├── E-posta Şablonları                                                 │
│      └── API Anahtarları                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Endpoints

```
# Süper Admin API
POST   /admin/auth/login          # Admin girişi
GET    /admin/dashboard           # Özet istatistikler

# Müşteri Yönetimi
GET    /admin/customers           # Tüm müşteriler
POST   /admin/customers           # Yeni müşteri
GET    /admin/customers/{id}      # Müşteri detay
PUT    /admin/customers/{id}      # Müşteri güncelle
DELETE /admin/customers/{id}      # Müşteri sil

# Lisans Yönetimi
POST   /admin/licenses/generate   # Yeni lisans oluştur
PUT    /admin/licenses/{id}/activate    # Lisans aktifle
PUT    /admin/licenses/{id}/suspend     # Lisans askıya al
PUT    /admin/licenses/{id}/upgrade     # Lisans yükselt
GET    /admin/licenses/expiring         # Süresi dolacaklar

# Versiyon Yönetimi
GET    /admin/versions            # Tüm versiyonlar
POST   /admin/versions            # Yeni versiyon
PUT    /admin/versions/{id}       # Versiyon güncelle
POST   /admin/versions/{id}/upload # Dosya yükle

# İstatistikler
GET    /admin/stats/usage         # Kullanım istatistikleri
GET    /admin/stats/revenue       # Gelir istatistikleri
GET    /admin/logs                # Aktivite logları
```

---

## 📱 Desktop App Değişiklikleri

### 1. Lisans Kontrolü (Uygulama Açılışı)

```python
# license_manager.py
class LicenseManager:
    def __init__(self):
        self.api_url = "https://api.bfrdernek.com"
        self.cache_file = "license_cache.json"
    
    def check_license(self, license_key: str) -> LicenseResult:
        # 1. Online kontrol dene
        try:
            result = self.verify_online(license_key)
            self.cache_license(result)
            return result
        except NetworkError:
            # 2. Offline ise cache kontrol
            cached = self.get_cached_license()
            if cached and cached.is_valid_offline():
                return cached
            raise LicenseError("Lisans doğrulanamadı")
    
    def get_license_type(self) -> str:
        # LOCAL, ONLINE, HYBRID, DEMO
        return self.current_license.type
    
    def get_database_mode(self) -> str:
        if self.get_license_type() in ["LOCAL", "DEMO"]:
            return "sqlite"
        elif self.get_license_type() == "ONLINE":
            return "api"
        else:  # HYBRID
            return "hybrid"
```

### 2. Database Adapter (Tek Interface, Çift Backend)

```python
# database_adapter.py
class DatabaseAdapter:
    def __init__(self, mode: str, license_key: str):
        self.mode = mode
        if mode == "sqlite":
            self.backend = SQLiteBackend()
        elif mode == "api":
            self.backend = APIBackend(license_key)
        else:  # hybrid
            self.backend = HybridBackend(license_key)
    
    # Tüm mevcut metodlar aynı interface ile
    def get_members(self):
        return self.backend.get_members()
    
    def add_member(self, data):
        return self.backend.add_member(data)
    
    # ... diğer metodlar
```

### 3. Auto Update Sistemi

```python
# auto_updater.py
class AutoUpdater:
    def check_for_updates(self):
        current = self.get_current_version()
        latest = self.api.get_latest_version()
        
        if latest.version > current:
            if latest.is_mandatory:
                self.force_update(latest)
            else:
                self.prompt_update(latest)
    
    def download_and_install(self, version):
        # Platform'a göre doğru dosyayı indir
        url = version.get_download_url(platform=sys.platform)
        self.download(url)
        self.install()
```

---

## 🌐 Web App Değişiklikleri

### 1. Multi-tenant Yapısı

```python
# Her müşteri kendi customer_id ile izole
# Mevcut yapı zaten bunu destekliyor

@app.get("/web/members")
def get_members(customer_id: str = Depends(get_customer_id)):
    return db.query(Member).filter(Member.customer_id == customer_id).all()
```

### 2. Lisans Tipi Kontrolü

```python
# Online lisanslı kullanıcılar için web erişimi
@app.middleware("http")
async def check_license_type(request: Request, call_next):
    customer_id = request.headers.get("X-Customer-ID")
    if customer_id:
        customer = get_customer(customer_id)
        if customer.license_type == "LOCAL":
            return JSONResponse(
                status_code=403,
                content={"error": "Web erişimi için ONLINE lisans gerekli"}
            )
    return await call_next(request)
```

---

## 🚀 Uygulama Planı

### Faz 1: Altyapı (1 hafta)
- [ ] Merkezi customers tablosu oluştur
- [ ] Lisans doğrulama API'si yaz
- [ ] Süper Admin API endpoints
- [ ] Versiyon kontrol API'si

### Faz 2: Süper Admin Paneli (1 hafta)
- [ ] Admin login sayfası
- [ ] Dashboard
- [ ] Müşteri listesi ve yönetimi
- [ ] Lisans oluşturma/düzenleme
- [ ] Versiyon yükleme

### Faz 3: Desktop Entegrasyonu (1 hafta)
- [ ] LicenseManager sınıfı
- [ ] DatabaseAdapter (SQLite/API switch)
- [ ] Auto-update sistemi
- [ ] Offline mod desteği

### Faz 4: Web Entegrasyonu (3 gün)
- [ ] Lisans tipi kontrolü
- [ ] Multi-tenant güvenlik
- [ ] LOCAL lisans engelleme

### Faz 5: Test ve Deploy (3 gün)
- [ ] Tüm senaryoları test et
- [ ] Production deploy
- [ ] Dokümantasyon

---

## 📁 Yeni Dosya Yapısı

```
bader/
├── core/
│   ├── license_manager.py      # Lisans yönetimi
│   ├── database_adapter.py     # SQLite/API adapter
│   ├── auto_updater.py         # Otomatik güncelleme
│   └── sync_manager.py         # Hybrid senkronizasyon
├── database.py                 # SQLite backend
├── api_client.py               # API backend (yeni)
├── main_fluent_new.py          # Ana uygulama
└── ...

server-v2/
├── api/
│   ├── main.py                 # Ana API (mevcut)
│   ├── admin_api.py            # Süper Admin API (yeni)
│   └── license_api.py          # Lisans API (yeni)
├── admin-panel/
│   ├── index.html              # Süper Admin frontend
│   ├── app.js
│   └── styles.css
└── web-app/
    ├── index.html              # Müşteri web app (mevcut)
    ├── app.js
    └── main_api.py
```

---

## ✅ Onay Bekleniyor

Bu mimari planı onaylıyor musun? Onaylarsan hangi fazdan başlayalım:

1. **Faz 1: Altyapı** - Lisans sistemi ve API'ler
2. **Faz 2: Süper Admin** - Admin paneli
3. **Faz 3: Desktop** - Uygulama entegrasyonu

Veya değişiklik önerilerin varsa belirt.
