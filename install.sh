#!/bin/bash

# BADER Derneği - Kurulum Script'i (Linux/Mac)

echo "================================================"
echo "BADER Derneği Kurulum Başlatılıyor..."
echo "================================================"
echo ""

# Python versiyonu kontrolü
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 bulunamadı! Lütfen Python 3.8 veya üzeri kurun."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
echo "✓ Python versiyon: $PYTHON_VERSION"

# pip kontrolü
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 bulunamadı! Lütfen pip kurun."
    exit 1
fi

echo "✓ pip bulundu"
echo ""

# Sanal ortam oluştur (opsiyonel ama önerilen)
read -p "Sanal ortam (virtual environment) oluşturulsun mu? (e/h): " create_venv

if [ "$create_venv" = "e" ] || [ "$create_venv" = "E" ]; then
    echo "📦 Sanal ortam oluşturuluyor..."
    python3 -m venv venv
    
    # Sanal ortamı aktifleştir
    source venv/bin/activate
    echo "✓ Sanal ortam aktifleştirildi"
fi

echo ""
echo "📦 Gerekli kütüphaneler yükleniyor..."
echo ""

# Bağımlılıkları yükle
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ Kurulum başarıyla tamamlandı!"
    echo "================================================"
    echo ""
    echo "Programı başlatmak için:"
    
    if [ "$create_venv" = "e" ] || [ "$create_venv" = "E" ]; then
        echo "  source venv/bin/activate  # (Sanal ortamı aktifleştir)"
    fi
    
    echo "  python3 main.py"
    echo ""
else
    echo ""
    echo "❌ Kurulum sırasında hata oluştu!"
    echo "Lütfen hata mesajlarını kontrol edin."
    exit 1
fi


