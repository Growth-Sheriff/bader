#!/bin/bash
# BADER Server v2 Deployment Script

set -e

echo "🚀 BADER Server v2 Deployment"
echo "=============================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker bulunamadı. Kurulum yapılıyor..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "✅ Docker kuruldu. Lütfen logout/login yapıp tekrar çalıştırın."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose bulunamadı."
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 .env dosyası oluşturuluyor..."
    cp .env.example .env
    
    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32)
    ADMIN_SECRET="BADER_ADMIN_$(openssl rand -hex 8 | tr '[:lower:]' '[:upper:]')"
    DB_PASSWORD="bader_$(openssl rand -hex 12)"
    
    sed -i "s/bader_secret_key_change_in_production_use_openssl_rand_hex_32/$SECRET_KEY/" .env
    sed -i "s/BADER_ADMIN_2025_SUPER_SECRET/$ADMIN_SECRET/" .env
    sed -i "s/bader_secure_2025/$DB_PASSWORD/" .env
    
    echo "✅ .env oluşturuldu"
    echo ""
    echo "⚠️  ÖNEMLİ: Aşağıdaki Admin Secret'ı kaydedin!"
    echo "    ADMIN_SECRET: $ADMIN_SECRET"
    echo ""
fi

# Build and start
echo "🔨 Container'lar build ediliyor..."
docker compose build

echo "🚀 Servisler başlatılıyor..."
docker compose up -d

echo ""
echo "⏳ Veritabanının hazır olması bekleniyor..."
sleep 10

# Health check
echo "🔍 Sağlık kontrolü..."
for i in {1..30}; do
    if curl -s http://localhost:8080/api/health > /dev/null; then
        echo "✅ API hazır!"
        break
    fi
    echo "   Bekleniyor... ($i/30)"
    sleep 2
done

echo ""
echo "=============================="
echo "✅ BADER Server v2 Hazır!"
echo ""
echo "📍 URL'ler:"
echo "   Ana Sayfa:    http://localhost:8080"
echo "   Admin Panel:  http://localhost:8080/admin"
echo "   API:          http://localhost:8080/api"
echo "   Belge Onay:   http://localhost:8080/belge.html"
echo ""
echo "📊 Durumu görmek için:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""
echo "🛑 Durdurmak için:"
echo "   docker compose down"
echo ""
