# BADER - Dernek & Köy Yönetim Sistemi

Modern, kapsamlı dernek ve köy yönetim çözümü.

## � Sistem Gereksinimleri

### Masaüstü Uygulama

| Gereksinim | Minimum | Önerilen |
|------------|---------|----------|
| **İşletim Sistemi** | Windows 10 / macOS 10.14 | Windows 11 / macOS 12+ |
| **Python** | 3.9 | 3.11+ |
| **RAM** | 4 GB | 8 GB |
| **Disk Alanı** | 500 MB | 1 GB |
| **Ekran Çözünürlüğü** | 1280x720 | 1920x1080 |

### Bağımlılıklar

- PyQt5 / PyQt6
- QFluentWidgets
- SQLite3
- Pillow (OCR için)
- ReportLab (PDF için)

---

## 🚀 Kurulum Adımları

### 1. Python Kurulumu

**Windows:**
```
https://www.python.org/downloads/ adresinden Python 3.11+ indirin
Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin
```

**macOS:**
```bash
brew install python@3.11
```

### 2. Proje Dosyalarını İndirin

```bash
git clone https://github.com/Growth-Sheriff/bader.git
cd bader/desktop
```

### 3. Sanal Ortam Oluşturun

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 5. Uygulamayı Başlatın

**Windows:**
```cmd
python main.py
```

**macOS / Linux:**
```bash
python3 main.py
```

---

## ⚡ Hızlı Kurulum (Tek Komut)

**macOS / Linux:**
```bash
cd desktop && chmod +x install.sh && ./install.sh
```

**Windows:**
```cmd
cd desktop && install.bat
```

---

## 📁 Proje Yapısı

```
bader/
├── desktop/          # Masaüstü Uygulama
│   ├── main.py       # Ana giriş noktası
│   ├── models.py     # İş mantığı
│   ├── database.py   # SQLite veritabanı
│   ├── ui_*.py       # Arayüz modülleri
│   └── core/         # Lisans, Güncelleme
│
├── server-v2/        # Sunucu (Docker)
└── web-app/          # Web Arayüzü
```

---

## ✨ Özellikler

- **Üye Yönetimi** - 26+ alan, tam profil
- **Aidat Takibi** - Otomatik gelir kaydı
- **Gelir/Gider** - Kategorili muhasebe
- **Kasa Yönetimi** - Çoklu kasa desteği
- **Virman** - Kasalar arası transfer
- **Etkinlikler** - Katılımcı takibi
- **Toplantılar** - Gündem ve kararlar
- **Belgeler** - OCR ile otomatik okuma
- **Raporlar** - 10+ detaylı rapor
- **Alacak-Verecek** - Borç takibi
- **Köy İşlemleri** - Ayrı muhasebe modülü

---

## 🔧 Sorun Giderme

### "PyQt5 bulunamadı" hatası
```bash
pip install PyQt5 PyQt5-Qt5 PyQt5-sip
```

### "QFluentWidgets bulunamadı" hatası
```bash
pip install PySide6-Fluent-Widgets
```

### macOS'ta izin hatası
```bash
chmod +x run.sh
./run.sh
```

---

## 📄 Lisans

Tüm hakları saklıdır. © 2025 Growth Sheriff
