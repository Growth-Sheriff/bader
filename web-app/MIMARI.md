# BADER Sistem Mimarisi

## 🏗️ Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BADER EKOSİSTEMİ                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  WEB APP     │    │  MASAÜSTÜ    │    │  MOBİL APP   │              │
│  │  (Vue 3)     │    │  (PyQt5)     │    │  (Gelecek)   │              │
│  │              │    │              │    │              │              │
│  │ - Online     │    │ - Offline OK │    │ - Hybrid     │              │
│  │ - Tarayıcı   │    │ - SQLite     │    │              │              │
│  │ - Responsive │    │ - Sync       │    │              │              │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘              │
│         │                   │                                           │
│         └─────────┬─────────┘                                           │
│                   │                                                     │
│                   ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      SUNUCU (157.90.154.48)                      │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │   CADDY     │  │  FastAPI    │  │ PostgreSQL  │              │   │
│  │  │  (Reverse   │──│  (API)      │──│ (Database)  │              │   │
│  │  │   Proxy)    │  │             │  │             │              │   │
│  │  │  :8080      │  │  :8000      │  │  :5432      │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  │         │                                                         │   │
│  │         ▼                                                         │   │
│  │  ┌─────────────────────────────────────────────────────────┐     │   │
│  │  │                    STATIC FILES                          │     │   │
│  │  │  /web     → Vue SPA (index.html, assets)                │     │   │
│  │  │  /uploads → DMG, güncellemeler, belgeler                │     │   │
│  │  │  /admin   → Admin panel                                  │     │   │
│  │  └─────────────────────────────────────────────────────────┘     │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📱 Kullanım Senaryoları

### 1. Web Kullanıcısı (Online)
- Tarayıcıdan `http://157.90.154.48:8080` adresine girer
- Lisans ID + kullanıcı adı/şifre ile giriş yapar
- Tüm veriler sunucuda tutulur
- Her işlem anlık kaydedilir

### 2. Masaüstü Kullanıcısı (Hybrid)
- Uygulama açılışta sunucuya bağlanmaya çalışır
- **Online mod:** Veriler sunucu ile senkronize
- **Offline mod:** Lokal SQLite kullanır, internet gelince sync

### 3. Lisanslama Akışı
```
1. Müşteri lisans satın alır
2. Admin panel'den müşteri oluşturulur → Lisans ID + API Key üretilir
3. Müşteriye Lisans ID verilir
4. Masaüstü/Web'de bu ID ile aktivasyon yapılır
5. Sunucu aktivasyonu doğrular ve kullanıcı oluşturur
```

### 4. Güncelleme Akışı
```
1. Yeni versiyon build edilir (PyInstaller)
2. DMG/EXE sunucuya yüklenir
3. Admin panelden versiyon aktif edilir
4. Uygulama açılışta /version/check endpoint'ini kontrol eder
5. Güncelleme varsa kullanıcıya bildirilir
6. İndirme linki verilir
```

## 🗄️ Veritabanı Şeması

### Multi-Tenant Yapı
- Her müşterinin `customer_id` si var
- Tüm tablolarda `customer_id` foreign key
- Bir müşteri sadece kendi verilerini görür

### Ana Tablolar
| Tablo | Açıklama |
|-------|----------|
| customers | Lisanslı müşteriler (dernekler) |
| users | Kullanıcılar (her müşterinin altında) |
| members | Dernek üyeleri |
| incomes | Gelir kayıtları |
| expenses | Gider kayıtları |
| dues | Aidat takibi |
| cash_accounts | Kasa hesapları |
| transfers | Virman işlemleri |
| events | Etkinlikler |
| meetings | Toplantılar |
| documents | Belgeler |
| settings | Ayarlar |
| app_versions | Uygulama versiyonları |
| activation_logs | Aktivasyon logları |
| dynamic_menus | Dinamik menüler |

## 🔐 Güvenlik

### Kimlik Doğrulama
- JWT token based auth
- Token 24 saat geçerli
- Refresh token ile yenileme

### Yetkilendirme
- Role-based: admin, manager, member
- Permission-based: read, write, delete per module

### API Güvenliği
- CORS ayarları
- Rate limiting (gelecek)
- API key validation

## 📁 Dosya Yapısı

```
sunucu/
├── docker-compose.yml
├── Caddyfile
├── api/
│   └── main.py              # FastAPI backend
├── web/
│   ├── index.html           # Vue SPA entry
│   ├── assets/
│   │   ├── app.js           # Vue application
│   │   └── style.css        # Tailwind CSS
│   └── favicon.ico
└── uploads/
    ├── updates/             # DMG/EXE dosyaları
    └── documents/           # Kullanıcı belgeleri

masaüstü/
├── main_fluent_full.py      # Ana uygulama
├── database.py              # SQLite + Sync
├── server_client.py         # API iletişimi
├── ui_*.py                  # UI modülleri
└── ...
```

## 🚀 URL Yapısı

| URL | Açıklama |
|-----|----------|
| http://157.90.154.48:8080/ | Web uygulaması |
| http://157.90.154.48:8080/api/* | API endpoints |
| http://157.90.154.48:8080/admin | Admin panel |
| http://157.90.154.48:8080/uploads/* | Static dosyalar |

## 🔄 Sync Mekanizması (Masaüstü)

```python
# Offline → Online geçiş
1. Son sync timestamp kontrol
2. Lokal değişiklikleri topla (created_at > last_sync)
3. Sunucuya POST /sync/upload
4. Sunucudan değişiklikleri al GET /sync/download?since=timestamp
5. Lokal veritabanını güncelle
6. Çakışma varsa → en son değişen kazanır
```
