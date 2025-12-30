# BADER - Dernek & Köy Yönetim Sistemi

Modern, kapsamlı dernek ve köy yönetim çözümü.

## 📁 Proje Yapısı

```
bader/
├── desktop/          # Masaüstü Uygulama (PyQt5/QFluentWidgets)
│   ├── main.py       # Ana giriş noktası
│   ├── models.py     # İş mantığı (2700+ satır)
│   ├── database.py   # SQLite veritabanı
│   ├── ui_*.py       # UI modülleri
│   └── core/         # License, AutoUpdate, DatabaseAdapter
│
├── server-v2/        # Sunucu (Docker + Caddy + PostgreSQL)
│   ├── api/          # FastAPI backend
│   ├── admin-panel/  # Super Admin paneli
│   ├── web/          # Web frontend
│   └── docker-compose.yml
│
├── web-app/          # Web Uygulaması (Alpine.js + Tailwind)
│   ├── index.html    # Ana sayfa
│   └── main_api.py   # Web API
│
└── docs/             # Dokümantasyon
    ├── README.md
    └── *.md
```

## 🚀 Hızlı Başlangıç

### Masaüstü Uygulama
```bash
cd desktop
pip install -r requirements.txt
python main.py
```

### Web Sunucu
```bash
cd server-v2
docker-compose up -d
```

## ✨ Özellikler

| Modül | Açıklama |
|-------|----------|
| **Üye Yönetimi** | 26+ alan, tam profil, referans sistemi |
| **Aidat Sistemi** | Otomatik gelir kaydı, çok yıllık ödeme |
| **Gelir/Gider** | Kategorili, kasa entegreli |
| **Kasa Yönetimi** | Çoklu kasa, para birimi desteği |
| **Virman** | Kasalar arası transfer |
| **Etkinlikler** | Katılımcı takibi, bütçe |
| **Toplantılar** | Gündem, kararlar, tutanak |
| **Belgeler** | OCR, otomatik kategorizasyon |
| **Raporlar** | 10+ detaylı rapor |
| **Mali Tablolar** | Bilanço, gelir tablosu |
| **Alacak-Verecek** | Tahsilat takibi |
| **Köy İşlemleri** | Ayrı muhasebe modülü |

## 🔐 Demo Erişim

- **Web:** http://157.90.154.48:8080
- **Lisans ID:** `BADER-2024-DEMO-0001`
- **Kullanıcı:** `admin`
- **Şifre:** `admin123`

## 📄 Lisans

Tüm hakları saklıdır. © 2025 Growth Sheriff
