# BADER Sunucu Mimarisi
## Desktop App + Server API Sistemi

### 📋 Genel Bakış

```
┌─────────────────────────────────────────────────────────────────┐
│                    MÜŞTERI TARAFI (Desktop)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  BADER Desktop App                        │  │
│  │                     (PyQt6 + QFluentWidgets)              │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  • Üye Yönetimi        • Aidat Takibi                     │  │
│  │  • Gelir/Gider         • Kasa İşlemleri                   │  │
│  │  • Mali Tablolar       • Raporlama                        │  │
│  │  • OCR (Server)        • Belge Tarama                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                       ServerClient                              │
│                              │                                  │
│                    (API Key ile bağlantı)                       │
│                              ▼                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                          HTTPS/REST
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUNUCU TARAFI (Ubuntu 24.04)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Nginx      │───▶│  FastAPI     │───▶│  PaddleOCR   │      │
│  │   Reverse    │    │  API Server  │    │  Engine      │      │
│  │   Proxy      │    │  (Multi-     │    │  (TR)        │      │
│  │   + SSL      │    │   Tenant)    │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                                   │
│  ┌──────▼──────┐     ┌──────┴──────┐                           │
│  │   UFW       │     │   SQLite    │                           │
│  │   Firewall  │     │   Database  │                           │
│  │   fail2ban  │     └─────────────┘                           │
│  └─────────────┘                                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Servisler                             │   │
│  ├─────────────┬─────────────┬──────────────┬─────────────┤   │
│  │ Aktivasyon  │  Yedekleme  │  Güncelleme  │    OCR      │   │
│  │ & Doğrulama │  (2x/gün)   │  Dağıtımı    │  İşleme     │   │
│  └─────────────┴─────────────┴──────────────┴─────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Sunucu Bilgileri

| Özellik | Değer |
|---------|-------|
| **IP Adresi** | 157.90.154.48 |
| **OS** | Ubuntu 24.04.3 LTS (ARM64) |
| **API URL** | http://157.90.154.48 |
| **API Docs** | http://157.90.154.48/docs |

---

## 📡 API Endpoint'leri

### Auth & Aktivasyon
| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/health` | GET | Server durumu |
| `/activate` | POST | Lisans aktivasyonu |
| `/validate` | GET | API key doğrulama |
| `/stats` | GET | Kullanım istatistikleri |

### OCR
| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/ocr` | POST | Görüntüden OCR işlemi |

### Yedekleme
| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/backup` | POST | Veritabanı yedeği yükle |
| `/backup/list` | GET | Yedekleri listele |
| `/backup/history` | GET | Yedek geçmişi |
| `/backup/{id}/download` | GET | Yedek indir |

### Güncelleme
| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/update/check` | GET/POST | Güncelleme kontrolü |
| `/update/download/{id}` | GET | Güncelleme indir |

### Admin (X-Admin-Key gerekli)
| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/admin/customers` | POST | Yeni müşteri oluştur |
| `/admin/customers` | GET | Müşterileri listele |
| `/admin/customers/{id}` | GET | Müşteri detayı |
| `/admin/customers/{id}` | PATCH | Müşteri güncelle |
| `/admin/customers/{id}/backups` | GET | Müşteri yedekleri |
| `/admin/customers/{id}/update-status` | GET | Güncelleme durumu |
| `/admin/customers/{id}/push-update` | POST | Güncelleme gönder |

---

## 🔐 Kimlik Doğrulama

### Müşteri Aktivasyonu
```bash
# Lisans anahtarı ile aktivasyon
curl -X POST "http://157.90.154.48/activate" \
  -H "Content-Type: application/json" \
  -d '{"license_key": "BADER-XXXX-XXXX"}'

# Yanıt
{
  "success": true,
  "customer_id": "BADER-XXXX-XXXX",
  "api_key": "sk_live_xxx...",
  "name": "Dernek Adı",
  "plan": "pro"
}
```

### API Key Kullanımı
```bash
# Her istekte header olarak
curl "http://157.90.154.48/stats" \
  -H "X-API-Key: sk_live_xxx..."
```

---

## 📁 Desktop App Dosyaları

### Yeni Eklenen Modüller
```
/Users/adiguzel/Desktop/bader/
├── server_client.py      # Server iletişim modülü
├── ui_server.py          # Server ayarları UI
└── bader_config.json     # Müşteri yapılandırma (otomatik oluşur)
```

### server_client.py Özellikleri
- Aktivasyon ve lisans doğrulama
- Otomatik yedekleme gönderimi
- Güncelleme kontrolü
- OCR istekleri
- Yapılandırma yönetimi

### ui_server.py Widget'ları
- `ActivationDialog` - Lisans aktivasyon dialogu
- `ServerSettingsWidget` - Server ayarları paneli

---

## 📦 Müşteri Kurulumu

### 1. Yeni Müşteri Oluşturma (Admin)
```bash
curl -X POST "http://157.90.154.48/admin/customers" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: YOUR_ADMIN_KEY" \
  -d '{"name": "Yeni Dernek", "email": "info@dernek.com", "plan": "pro"}'
```

### 2. Desktop App'te Aktivasyon
1. Uygulama ilk açılışta aktivasyon ekranı gösterir
2. Müşteri ID veya API key girilir
3. Bağlantı kurulur ve ayarlar kaydedilir

### 3. Otomatik İşlemler
- **Yedekleme**: Uygulama kapatılırken otomatik
- **Güncelleme**: Her açılışta kontrol
- **OCR**: Server üzerinden işlenir

---

## ⏰ Yedekleme Sistemi

### Otomatik Yedekleme (Server Cron)
```cron
# Sabah 06:00 - Tam yedek
0 6 * * * /opt/bader-server/backup/run_backup.sh full

# Akşam 18:00 - Artımlı yedek
0 18 * * * /opt/bader-server/backup/run_backup.sh incremental
```

### Müşteri Tarafı Yedekleme
- Desktop app, veritabanını server'a yükler
- Son 30 gün yedekler saklanır
- İstenildiğinde geri yüklenebilir

---

## 🔄 Güncelleme Akışı

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Admin     │────▶│  Versiyon   │────▶│  Desktop    │
│   Yükler    │     │  Yayınlanır │     │  Kontrol    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌──────────────────────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
  ┌──────▼────┐ ┌───▼───┐ ┌───▼───┐
  │ Otomatik  │ │ Manuel│ │ Sonra │
  │ Güncelle  │ │ İndir │ │       │
  └───────────┘ └───────┘ └───────┘
```

---

## 🛡️ Güvenlik

### Server Tarafı
- **Firewall (UFW)**: 22, 80, 443 portları açık
- **fail2ban**: Brute force koruması
- **API Key**: Müşteri bazlı kimlik doğrulama
- **Admin Key**: Yönetim işlemleri için
- **Rate Limiting**: Günlük 50 OCR limiti (plan bazlı)

### Desktop Tarafı
- API key güvenli saklanır
- HTTPS kullanımı önerilir
- Yedekler şifrelenebilir

---

## 📊 Test Müşterisi

| Alan | Değer |
|------|-------|
| **Customer ID** | BADER-DEMO-XXXX |
| **API Key** | YOUR_API_KEY_HERE |
| **Plan** | pro |
| **Günlük OCR** | 50 |

---

## 🚀 Hızlı Başlangıç

### Server Test
```bash
# Health check
curl http://157.90.154.48/health

# Aktivasyon test
curl -X POST http://157.90.154.48/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "BADER-7975FD46"}'
```

### Desktop App
1. `ui_server.py` import edin
2. Ayarlara `ServerSettingsWidget` ekleyin
3. Uygulama başlangıcında aktivasyon kontrolü yapın

---

## 📝 Yapılacaklar

- [ ] SSL sertifikası (Let's Encrypt)
- [ ] Admin key değiştirme
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Remote backup (S3/B2)
- [ ] Desktop app'e tam entegrasyon
