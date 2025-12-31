# BADER - Kurulum Rehberi

## Commit Numarası
**`0e3a9c4`**

## Hızlı Kurulum (Tek Komut)

### macOS / Linux
```bash
git clone https://github.com/Growth-Sheriff/bader.git && cd bader && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python main_fluent_full.py
```

### Windows (PowerShell)
```powershell
git clone https://github.com/Growth-Sheriff/bader.git; cd bader; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main_fluent_full.py
```

### Windows (CMD)
```cmd
git clone https://github.com/Growth-Sheriff/bader.git && cd bader && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python main_fluent_full.py
```

---

## Adım Adım Kurulum

### 1. Repo'yu İndir
```bash
git clone https://github.com/Growth-Sheriff/bader.git
cd bader
```

### 2. Virtual Environment Oluştur
```bash
python3 -m venv venv
```

### 3. Aktive Et
- **macOS/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

### 4. Bağımlılıkları Kur
```bash
pip install -r requirements.txt
```

### 5. Uygulamayı Çalıştır
```bash
python main_fluent_full.py
```

---

## Giriş Bilgileri

| Alan | Değer |
|------|-------|
| **Kullanıcı Adı** | `admin` |
| **Şifre** | `admin123` |

---

## Gereksinimler
- Python 3.10+
- PyQt5
- PyQt-Fluent-Widgets

## Dernek Bilgileri
- **Dernek:** Bader Bingöl Yardımlaşma Dayanışma Derneği
- **Lisans:** BADER-2024-DEMO-0001 (Pro, 2026'ya kadar geçerli)
