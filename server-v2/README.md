# BADER Server v2

Modern Docker tabanlı sunucu altyapısı.

## 🛠️ Teknoloji Stack

- **Docker & Docker Compose** - Container orchestration
- **PostgreSQL 16** - Veritabanı
- **FastAPI + SQLAlchemy** - API
- **Caddy** - Reverse proxy & otomatik SSL
- **Redis** - Cache & Session (opsiyonel)

## 📦 Kurulum

### Sunucuya Yükleme

```bash
# Dosyaları sunucuya kopyala
scp -r server-v2 user@server:/opt/bader-server-v2

# Sunucuya bağlan
ssh user@server

# Dizine git
cd /opt/bader-server-v2

# Deploy et
chmod +x deploy.sh
./deploy.sh
```

### Yerel Test

```bash
cd server-v2
docker compose up -d
```

## 🌐 URL'ler

| Servis | URL |
|--------|-----|
| Ana Sayfa | http://localhost:8080 |
| Admin Panel | http://localhost:8080/admin |
| API | http://localhost:8080/api |
| Belge Onay | http://localhost:8080/belge.html |

## 🔐 Admin Panel

İlk kurulumda `.env` dosyasındaki `ADMIN_SECRET` kullanılır.

Admin Panel'de:
- **Dashboard** - Genel istatistikler
- **Müşteriler** - Lisans yönetimi (CRUD)
- **Güncellemeler** - Versiyon yönetimi
- **Loglar** - Aktivasyon geçmişi

## 📱 Masaüstü Uygulama Entegrasyonu

Masaüstü uygulamada şu bilgiler gerekli:

```
Server URL: http://YOUR_SERVER:8080/api
Customer ID: BADER-2025-XXXXXXXX
API Key: bader_api_xxxxxxxxxxxxxxxx
```

Bu bilgiler Admin Panel → Müşteriler → Yeni Müşteri ile oluşturulur.

## 🔄 Güncelleme Yayınlama

1. Admin Panel → Güncellemeler → Yeni Versiyon
2. Versiyon numarası gir (örn: 1.0.1)
3. Changelog yaz
4. Kritik güncelleme ise işaretle
5. Oluştur
6. Dosya Yükle ile .app/.exe dosyasını yükle

Kullanıcılar uygulamayı açtığında güncelleme bildirimi görür.

## 🗄️ Veritabanı

PostgreSQL 16 kullanılır. Tablolar:

- `customers` - Müşteriler (lisans sahipleri)
- `users` - Kullanıcılar
- `members` - Üyeler
- `incomes` - Gelirler
- `expenses` - Giderler
- `cash_accounts` - Kasalar
- `transfers` - Virmanlar
- `dues` - Aidatlar
- `documents` - Belgeler (OCR)
- `app_versions` - Uygulama versiyonları
- `activation_logs` - Aktivasyon logları
- `events` - Etkinlikler
- `meetings` - Toplantılar
- `settings` - Ayarlar

## 📁 Klasör Yapısı

```
server-v2/
├── docker-compose.yml    # Container tanımları
├── Caddyfile             # Reverse proxy config
├── init.sql              # Veritabanı şeması
├── deploy.sh             # Deployment script
├── .env.example          # Örnek environment
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py           # FastAPI uygulama
└── web/
    ├── admin/
    │   └── index.html    # Admin Panel (saf HTML/JS)
    └── public/
        ├── index.html    # Ana sayfa
        └── belge.html    # Belge onay sayfası
```

## 🔧 Komutlar

```bash
# Logları izle
docker compose logs -f

# Sadece API logları
docker compose logs -f api

# Container'a bağlan
docker compose exec api bash
docker compose exec postgres psql -U bader

# Yeniden başlat
docker compose restart

# Tamamen durdur ve sil
docker compose down -v

# Güncelleme (yeni kod deploy)
docker compose pull
docker compose up -d --build
```

## 🔒 Güvenlik

Production'da:

1. `.env` dosyasındaki secret'ları değiştirin
2. Firewall kuralları ayarlayın
3. SSL için domain yapılandırın (Caddy otomatik yapar)
4. Admin Panel'e IP kısıtlaması ekleyin

## 📊 Monitoring

```bash
# Resource kullanımı
docker stats

# Disk kullanımı
docker system df
```
