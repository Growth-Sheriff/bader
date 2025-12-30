#!/bin/bash
# BADER Sunucu Yedekleme Script
# Günde 2 kez çalışır: 06:00 ve 18:00

set -e

BACKUP_TYPE="${1:-full}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/bader-server/data/backups"
LOG_FILE="/opt/bader-server/logs/backup.log"

# Log fonksiyonu
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Yedekleme Başladı: $BACKUP_TYPE ==="

# Ana veritabanı yedeği
DB_PATH="/opt/bader-server/data/database/bader_server.db"
if [ -f "$DB_PATH" ]; then
    BACKUP_FILE="${BACKUP_DIR}/server_db_${TIMESTAMP}.db"
    cp "$DB_PATH" "$BACKUP_FILE"
    gzip "$BACKUP_FILE"
    log "✅ Sunucu veritabanı yedeklendi: ${BACKUP_FILE}.gz"
fi

# Müşteri verileri yedeği
CUSTOMERS_DIR="/opt/bader-server/data/customers"
if [ -d "$CUSTOMERS_DIR" ]; then
    CUSTOMERS_BACKUP="${BACKUP_DIR}/customers_${TIMESTAMP}.tar.gz"
    tar -czf "$CUSTOMERS_BACKUP" -C "$CUSTOMERS_DIR" .
    log "✅ Müşteri verileri yedeklendi: $CUSTOMERS_BACKUP"
fi

# Eski yedekleri temizle (30 günden eski)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
log "✅ Eski yedekler temizlendi"

# Yedek boyutu
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "📊 Toplam yedek boyutu: $TOTAL_SIZE"

log "=== Yedekleme Tamamlandı ==="
