#!/bin/bash
# BADER API Sunucu Deploy Script
# Kullanım: ./deploy.sh

set -e

echo "🚀 BADER API Deploy Başlatılıyor..."
echo "=================================="

# Dizin kontrolü
cd /opt/bader 2>/dev/null || {
    echo "📁 /opt/bader dizini oluşturuluyor..."
    sudo mkdir -p /opt/bader
    cd /opt/bader
}

# Git pull (eğer repo varsa)
if [ -d ".git" ]; then
    echo "📥 Kod güncelleniyor..."
    git pull origin main
else
    echo "📥 Repo klonlanıyor..."
    git clone https://github.com/Growth-Sheriff/bader.git .
fi

# Server dizinine geç
cd server

# Environment dosyası kontrolü
if [ ! -f ".env" ]; then
    echo "📝 .env dosyası oluşturuluyor..."
    cat > .env << 'EOF'
DATABASE_URL=postgresql://bader:bader_secure_2025@db:5432/bader
SECRET_KEY=bader_production_secret_key_2026_change_this
ADMIN_SECRET=BADER_ADMIN_2025_SUPER_SECRET
EOF
fi

# Docker Compose işlemleri
echo "🐳 Docker servisleri durduruluyor..."
docker-compose down 2>/dev/null || true

echo "🐳 Docker image yeniden build ediliyor..."
docker-compose build --no-cache

echo "🐳 Docker servisleri başlatılıyor..."
docker-compose up -d

# Veritabanı hazır olana kadar bekle
echo "⏳ Veritabanı başlatılıyor..."
sleep 10

# Veritabanı şemasını güncelle
echo "🗄️ Veritabanı şeması güncelleniyor..."
docker exec bader-db psql -U bader -d bader -f /docker-entrypoint-initdb.d/init.sql 2>/dev/null || true

# Servis durumunu kontrol et
echo ""
echo "✅ Deploy tamamlandı!"
echo "=================================="
echo ""

# API durumu
echo "📊 Servis Durumu:"
docker-compose ps

echo ""
echo "🔗 API Endpoints:"
echo "   Health: http://localhost:8080/health"
echo "   Docs:   http://localhost:8080/docs"
echo "   API:    http://localhost:8080/api/health"
echo ""

# Health check
echo "🏥 Health Check:"
sleep 2
curl -s http://localhost:8080/health 2>/dev/null || echo "API henüz hazır değil, birkaç saniye bekleyin"
echo ""
