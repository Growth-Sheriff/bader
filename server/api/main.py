"""
BADER API Server - Multi-Tenant OCR + Yedekleme + Güncelleme Sistemi
====================================================================

FastAPI tabanlı merkezi sunucu.
- Multi-tenant müşteri yönetimi
- PaddleOCR entegrasyonu
- Otomatik yedekleme
- Yazılım güncelleme dağıtımı
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import hashlib
import secrets
import os
import json
import shutil
from pathlib import Path

# ==================== CONFIGURATION ====================

BASE_DIR = Path("/opt/bader-server")
DATA_DIR = BASE_DIR / "data"
CUSTOMERS_DIR = DATA_DIR / "customers"
DATABASE_DIR = DATA_DIR / "database"
UPLOADS_DIR = DATA_DIR / "uploads"
BACKUPS_DIR = DATA_DIR / "backups"
UPDATES_DIR = BASE_DIR / "updates"
VERSIONS_DIR = UPDATES_DIR / "versions"
LOGS_DIR = BASE_DIR / "logs"

# Database
DB_PATH = DATABASE_DIR / "bader_server.db"

# ==================== DATABASE ====================

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Veritabanını başlat"""
    conn = get_db()
    cur = conn.cursor()
    
    # Müşteriler tablosu
    cur.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            email TEXT,
            plan TEXT DEFAULT 'free',
            max_ocr_daily INTEGER DEFAULT 50,
            backup_enabled INTEGER DEFAULT 1,
            auto_update INTEGER DEFAULT 1,
            current_version TEXT DEFAULT '1.0.0',
            update_channel TEXT DEFAULT 'stable',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # OCR kullanım logları
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ocr_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_size INTEGER,
            processing_time REAL,
            success INTEGER,
            error_message TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')
    
    # Yedekleme logları
    cur.execute('''
        CREATE TABLE IF NOT EXISTS backup_logs (
            backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            backup_type TEXT,
            file_size INTEGER,
            status TEXT,
            file_path TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')
    
    # Güncelleme logları
    cur.execute('''
        CREATE TABLE IF NOT EXISTS update_logs (
            update_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            from_version TEXT,
            to_version TEXT,
            status TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')
    
    # Sürümler tablosu
    cur.execute('''
        CREATE TABLE IF NOT EXISTS versions (
            version_id TEXT PRIMARY KEY,
            version_name TEXT NOT NULL,
            release_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            channel TEXT DEFAULT 'stable',
            changelog TEXT,
            min_required_version TEXT,
            file_path TEXT,
            file_hash TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

# ==================== MODELS ====================

class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    plan: str = "free"

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    plan: Optional[str] = None
    max_ocr_daily: Optional[int] = None
    backup_enabled: Optional[bool] = None
    auto_update: Optional[bool] = None
    update_channel: Optional[str] = None

class BackupRequest(BaseModel):
    database_content: str  # Base64 encoded
    timestamp: str

class UpdateCheck(BaseModel):
    current_version: str
    platform: str = "macos"

class VersionCreate(BaseModel):
    version_name: str
    channel: str = "stable"
    changelog: str = ""
    min_required_version: str = "1.0.0"

class ActivationRequest(BaseModel):
    license_key: str
    device_info: Optional[Dict[str, Any]] = None

class UpdateCheckRequest(BaseModel):
    current_version: str
    platform: str = "macos"
    arch: str = "arm64"

# ==================== AUTH ====================

async def verify_api_key(x_api_key: str = Header(...)):
    """API key doğrulama"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE api_key = ? AND is_active = 1", (x_api_key,))
    customer = cur.fetchone()
    conn.close()
    
    if not customer:
        raise HTTPException(status_code=401, detail="Geçersiz API anahtarı")
    
    return dict(customer)

async def verify_admin_key(x_admin_key: str = Header(...)):
    """Admin key doğrulama"""
    admin_key = os.environ.get("BADER_ADMIN_KEY", "bader-admin-secret-key")
    if x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    return True

# ==================== APP ====================

app = FastAPI(
    title="BADER API Server",
    description="Multi-Tenant OCR, Yedekleme ve Güncelleme Sistemi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Dizinleri oluştur
    for dir_path in [DATA_DIR, CUSTOMERS_DIR, DATABASE_DIR, UPLOADS_DIR, BACKUPS_DIR, VERSIONS_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Veritabanını başlat
    init_db()

# ==================== HEALTH ====================

@app.get("/")
async def root():
    return {"status": "ok", "service": "BADER API Server", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================== ACTIVATION & VALIDATION ====================

@app.post("/activate", tags=["Auth"])
async def activate_license(request: ActivationRequest):
    """
    Lisans anahtarı ile aktivasyon.
    Lisans anahtarı formatı: BADER-XXXX-XXXX-XXXX (customer_id)
    veya önceden oluşturulmuş api_key
    """
    conn = get_db()
    cur = conn.cursor()
    
    license_key = request.license_key.strip()
    
    # Önce customer_id olarak ara
    cur.execute("""
        SELECT customer_id, api_key, name, plan 
        FROM customers 
        WHERE customer_id = ? AND is_active = 1
    """, (license_key,))
    customer = cur.fetchone()
    
    # Bulunamadıysa api_key olarak ara
    if not customer:
        cur.execute("""
            SELECT customer_id, api_key, name, plan 
            FROM customers 
            WHERE api_key = ? AND is_active = 1
        """, (license_key,))
        customer = cur.fetchone()
    
    if not customer:
        conn.close()
        raise HTTPException(status_code=401, detail="Geçersiz lisans anahtarı")
    
    # Device info kaydet (opsiyonel)
    device_info = json.dumps(request.device_info) if request.device_info else None
    
    # Last seen güncelle
    cur.execute("""
        UPDATE customers 
        SET last_seen = CURRENT_TIMESTAMP 
        WHERE customer_id = ?
    """, (customer['customer_id'],))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "customer_id": customer['customer_id'],
        "api_key": customer['api_key'],
        "name": customer['name'],
        "plan": customer['plan'],
        "message": "Aktivasyon başarılı"
    }

@app.get("/validate", tags=["Auth"])
async def validate_api_key_endpoint(customer: dict = Depends(verify_api_key)):
    """API anahtarını doğrula ve müşteri bilgilerini döndür"""
    # Last seen güncelle
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE customers 
        SET last_seen = CURRENT_TIMESTAMP 
        WHERE customer_id = ?
    """, (customer['customer_id'],))
    conn.commit()
    conn.close()
    
    return {
        "valid": True,
        "customer_id": customer['customer_id'],
        "name": customer['name'],
        "plan": customer['plan'],
        "backup_enabled": bool(customer['backup_enabled']),
        "auto_update": bool(customer['auto_update'])
    }

@app.get("/stats", tags=["Stats"])
async def get_customer_stats(customer: dict = Depends(verify_api_key)):
    """Müşteri kullanım istatistikleri"""
    conn = get_db()
    cur = conn.cursor()
    
    # Bugünkü OCR kullanımı
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        SELECT COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
        FROM ocr_logs 
        WHERE customer_id = ? AND DATE(timestamp) = ?
    """, (customer['customer_id'], today))
    ocr_today = cur.fetchone()
    
    # Toplam OCR kullanımı
    cur.execute("""
        SELECT COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
        FROM ocr_logs 
        WHERE customer_id = ?
    """, (customer['customer_id'],))
    ocr_total = cur.fetchone()
    
    # Yedekleme sayısı
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM backup_logs 
        WHERE customer_id = ? AND status = 'success'
    """, (customer['customer_id'],))
    backup_count = cur.fetchone()['count']
    
    conn.close()
    
    return {
        "customer_id": customer['customer_id'],
        "ocr": {
            "today": {
                "total": ocr_today['total'] or 0,
                "successful": ocr_today['successful'] or 0,
                "remaining": customer['max_ocr_daily'] - (ocr_today['total'] or 0)
            },
            "all_time": {
                "total": ocr_total['total'] or 0,
                "successful": ocr_total['successful'] or 0
            },
            "daily_limit": customer['max_ocr_daily']
        },
        "backups": {
            "total_count": backup_count
        },
        "plan": customer['plan']
    }

# ==================== CUSTOMER MANAGEMENT ====================

@app.post("/admin/customers", tags=["Admin"])
async def create_customer(customer: CustomerCreate, _: bool = Depends(verify_admin_key)):
    """Yeni müşteri oluştur"""
    conn = get_db()
    cur = conn.cursor()
    
    # Customer ID ve API key oluştur
    customer_id = f"BADER-{secrets.token_hex(4).upper()}"
    api_key = f"sk_live_{secrets.token_hex(24)}"
    
    try:
        cur.execute('''
            INSERT INTO customers (customer_id, name, email, plan, api_key)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, customer.name, customer.email, customer.plan, api_key))
        conn.commit()
        
        # Müşteri klasörü oluştur
        customer_dir = CUSTOMERS_DIR / customer_id
        customer_dir.mkdir(parents=True, exist_ok=True)
        (customer_dir / "backups").mkdir(exist_ok=True)
        (customer_dir / "uploads").mkdir(exist_ok=True)
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Müşteri zaten mevcut")
    finally:
        conn.close()
    
    return {
        "customer_id": customer_id,
        "api_key": api_key,
        "message": "Müşteri başarıyla oluşturuldu"
    }

@app.get("/admin/customers", tags=["Admin"])
async def list_customers(_: bool = Depends(verify_admin_key)):
    """Tüm müşterileri listele"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT customer_id, name, email, plan, current_version, last_seen, is_active FROM customers")
    customers = [dict(row) for row in cur.fetchall()]
    conn.close()
    return customers

@app.get("/admin/customers/{customer_id}", tags=["Admin"])
async def get_customer(customer_id: str, _: bool = Depends(verify_admin_key)):
    """Müşteri detaylarını getir"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    customer = cur.fetchone()
    conn.close()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    return dict(customer)

@app.patch("/admin/customers/{customer_id}", tags=["Admin"])
async def update_customer(customer_id: str, update: CustomerUpdate, _: bool = Depends(verify_admin_key)):
    """Müşteri bilgilerini güncelle"""
    conn = get_db()
    cur = conn.cursor()
    
    updates = []
    values = []
    
    if update.name:
        updates.append("name = ?")
        values.append(update.name)
    if update.email:
        updates.append("email = ?")
        values.append(update.email)
    if update.plan:
        updates.append("plan = ?")
        values.append(update.plan)
    if update.max_ocr_daily is not None:
        updates.append("max_ocr_daily = ?")
        values.append(update.max_ocr_daily)
    if update.backup_enabled is not None:
        updates.append("backup_enabled = ?")
        values.append(1 if update.backup_enabled else 0)
    if update.auto_update is not None:
        updates.append("auto_update = ?")
        values.append(1 if update.auto_update else 0)
    if update.update_channel:
        updates.append("update_channel = ?")
        values.append(update.update_channel)
    
    if updates:
        values.append(customer_id)
        cur.execute(f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = ?", values)
        conn.commit()
    
    conn.close()
    return {"message": "Müşteri güncellendi"}

# ==================== OCR ====================

@app.post("/ocr", tags=["OCR"])
async def process_ocr(
    image: UploadFile = File(...),
    customer: dict = Depends(verify_api_key)
):
    """OCR işlemi"""
    import time
    start_time = time.time()
    
    # Günlük limit kontrolü
    conn = get_db()
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute('''
        SELECT COUNT(*) FROM ocr_logs 
        WHERE customer_id = ? AND DATE(timestamp) = ? AND success = 1
    ''', (customer['customer_id'], today))
    daily_count = cur.fetchone()[0]
    
    if daily_count >= customer['max_ocr_daily']:
        conn.close()
        raise HTTPException(status_code=429, detail="Günlük OCR limiti aşıldı")
    
    # Dosyayı kaydet
    upload_path = UPLOADS_DIR / f"{customer['customer_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    
    try:
        contents = await image.read()
        with open(upload_path, "wb") as f:
            f.write(contents)
        
        # PaddleOCR işlemi
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='tr', use_gpu=False, show_log=False)
            result = ocr.ocr(str(upload_path), cls=True)
            
            lines = []
            confidences = []
            
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    conf = line[1][1]
                    lines.append(text)
                    confidences.append(conf)
            
            raw_text = '\n'.join(lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            # Log kaydet
            cur.execute('''
                INSERT INTO ocr_logs (customer_id, image_size, processing_time, success)
                VALUES (?, ?, ?, 1)
            ''', (customer['customer_id'], len(contents), processing_time))
            
            # Last seen güncelle
            cur.execute("UPDATE customers SET last_seen = CURRENT_TIMESTAMP WHERE customer_id = ?",
                       (customer['customer_id'],))
            conn.commit()
            
            return {
                "success": True,
                "text": raw_text,
                "lines": lines,
                "confidence": avg_confidence,
                "processing_time": processing_time
            }
            
        except ImportError:
            raise HTTPException(status_code=500, detail="PaddleOCR yüklü değil")
            
    except Exception as e:
        # Hata logu
        cur.execute('''
            INSERT INTO ocr_logs (customer_id, image_size, processing_time, success, error_message)
            VALUES (?, ?, ?, 0, ?)
        ''', (customer['customer_id'], 0, time.time() - start_time, str(e)))
        conn.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        # Geçici dosyayı sil
        if upload_path.exists():
            upload_path.unlink()

# ==================== BACKUP ====================

@app.post("/backup", tags=["Backup"])
async def create_backup_file(
    file: UploadFile = File(...),
    customer: dict = Depends(verify_api_key)
):
    """Müşteri veritabanı yedeği yükle (file upload)"""
    if not customer['backup_enabled']:
        raise HTTPException(status_code=403, detail="Yedekleme devre dışı")
    
    customer_backup_dir = CUSTOMERS_DIR / customer['customer_id'] / "backups"
    customer_backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Dosya adı
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = customer_backup_dir / backup_filename
    
    try:
        # Dosyayı oku ve kaydet
        contents = await file.read()
        
        # Hash hesapla
        file_hash = hashlib.sha256(contents).hexdigest()
        
        with open(backup_path, "wb") as f:
            f.write(contents)
        
        # Log kaydet
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO backup_logs (customer_id, backup_type, file_size, status, file_path)
            VALUES (?, 'full', ?, 'success', ?)
        ''', (customer['customer_id'], len(contents), str(backup_path)))
        
        # Last seen güncelle
        cur.execute("UPDATE customers SET last_seen = CURRENT_TIMESTAMP WHERE customer_id = ?",
                   (customer['customer_id'],))
        conn.commit()
        conn.close()
        
        # Eski yedekleri temizle (son 30 günden eski)
        cleanup_old_backups(customer_backup_dir, days=30)
        
        return {
            "success": True,
            "backup_id": backup_filename,
            "size": len(contents),
            "hash": file_hash,
            "timestamp": timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backup/base64", tags=["Backup"])
async def create_backup_base64(
    backup: BackupRequest,
    customer: dict = Depends(verify_api_key)
):
    """Müşteri yedeklemesi al (base64 encoded)"""
    import base64
    
    if not customer['backup_enabled']:
        raise HTTPException(status_code=403, detail="Yedekleme devre dışı")
    
    customer_backup_dir = CUSTOMERS_DIR / customer['customer_id'] / "backups"
    customer_backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Dosya adı
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = customer_backup_dir / backup_filename
    
    try:
        # Base64 decode ve kaydet
        db_content = base64.b64decode(backup.database_content)
        with open(backup_path, "wb") as f:
            f.write(db_content)
        
        # Log kaydet
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO backup_logs (customer_id, backup_type, file_size, status, file_path)
            VALUES (?, 'full', ?, 'success', ?)
        ''', (customer['customer_id'], len(db_content), str(backup_path)))
        conn.commit()
        conn.close()
        
        # Eski yedekleri temizle (son 30 günden eski)
        cleanup_old_backups(customer_backup_dir, days=30)
        
        return {
            "success": True,
            "backup_id": backup_filename,
            "size": len(db_content),
            "timestamp": timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backup/list", tags=["Backup"])
async def list_backups(customer: dict = Depends(verify_api_key)):
    """Müşteri yedeklerini listele"""
    customer_backup_dir = CUSTOMERS_DIR / customer['customer_id'] / "backups"
    
    if not customer_backup_dir.exists():
        return {"backups": []}
    
    backups = []
    for f in sorted(customer_backup_dir.glob("*.db"), reverse=True):
        backups.append({
            "id": f.stem,
            "filename": f.name,
            "size": f.stat().st_size,
            "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    return {"backups": backups}

@app.get("/backup/history", tags=["Backup"])
async def backup_history(customer: dict = Depends(verify_api_key)):
    """Müşteri yedek geçmişini getir (alias for /backup/list)"""
    return await list_backups(customer)

@app.get("/backup/{backup_id}/download", tags=["Backup"])
async def download_backup_by_id(backup_id: str, customer: dict = Depends(verify_api_key)):
    """Yedek indir (by backup_id)"""
    # backup_id = filename without extension
    backup_path = CUSTOMERS_DIR / customer['customer_id'] / "backups" / f"{backup_id}.db"
    
    if not backup_path.exists():
        # Try with .db extension already included
        backup_path = CUSTOMERS_DIR / customer['customer_id'] / "backups" / backup_id
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Yedek bulunamadı")
    
    return FileResponse(
        path=str(backup_path),
        filename=backup_path.name,
        media_type="application/octet-stream"
    )

@app.get("/backup/download/{filename}", tags=["Backup"])
async def download_backup(filename: str, customer: dict = Depends(verify_api_key)):
    """Yedek indir"""
    backup_path = CUSTOMERS_DIR / customer['customer_id'] / "backups" / filename
    
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="Yedek bulunamadı")
    
    return FileResponse(
        path=str(backup_path),
        filename=filename,
        media_type="application/octet-stream"
    )

def cleanup_old_backups(backup_dir: Path, days: int = 30):
    """Eski yedekleri temizle"""
    cutoff = datetime.now() - timedelta(days=days)
    
    for f in backup_dir.glob("*.db"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()

# ==================== UPDATE ====================

@app.get("/update/check", tags=["Update"])
async def check_update(customer: dict = Depends(verify_api_key)):
    """Güncelleme kontrolü (GET)"""
    return await _check_update_internal(customer, customer['current_version'])

@app.post("/update/check", tags=["Update"])
async def check_update_post(
    request: UpdateCheckRequest,
    customer: dict = Depends(verify_api_key)
):
    """Güncelleme kontrolü (POST with version info)"""
    return await _check_update_internal(customer, request.current_version)

async def _check_update_internal(customer: dict, current_version: str):
    """Internal güncelleme kontrolü"""
    if not customer['auto_update']:
        return {"update_available": False, "message": "Otomatik güncelleme devre dışı"}
    
    conn = get_db()
    cur = conn.cursor()
    
    # Müşterinin kanalına göre en son sürümü bul
    cur.execute('''
        SELECT * FROM versions 
        WHERE channel = ? AND is_active = 1
        ORDER BY release_date DESC LIMIT 1
    ''', (customer['update_channel'],))
    
    latest = cur.fetchone()
    conn.close()
    
    if not latest:
        return {"update_available": False, "current_version": current_version}
    
    latest_version = latest['version_name']
    
    # Sürüm karşılaştırma
    def version_tuple(v):
        try:
            return tuple(map(int, v.split('.')))
        except:
            return (0, 0, 0)
    
    if version_tuple(latest_version) > version_tuple(current_version):
        return {
            "update_available": True,
            "current_version": current_version,
            "latest_version": latest_version,
            "changelog": latest['changelog'],
            "download_url": f"/update/download/{latest['version_id']}"
        }
    
    return {"update_available": False, "current_version": current_version}

@app.get("/update/download/{version_id}", tags=["Update"])
async def download_update(version_id: str, customer: dict = Depends(verify_api_key)):
    """Güncelleme dosyasını indir"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM versions WHERE version_id = ?", (version_id,))
    version = cur.fetchone()
    conn.close()
    
    if not version or not version['file_path']:
        raise HTTPException(status_code=404, detail="Güncelleme bulunamadı")
    
    file_path = Path(version['file_path'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Güncelleme dosyası bulunamadı")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )

@app.post("/update/confirm", tags=["Update"])
async def confirm_update(
    new_version: str,
    customer: dict = Depends(verify_api_key)
):
    """Güncelleme tamamlandığını bildir"""
    conn = get_db()
    cur = conn.cursor()
    
    # Güncelleme logu
    cur.execute('''
        INSERT INTO update_logs (customer_id, from_version, to_version, status)
        VALUES (?, ?, ?, 'success')
    ''', (customer['customer_id'], customer['current_version'], new_version))
    
    # Müşteri sürümünü güncelle
    cur.execute('''
        UPDATE customers SET current_version = ?, last_seen = CURRENT_TIMESTAMP
        WHERE customer_id = ?
    ''', (new_version, customer['customer_id']))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "version": new_version}

# ==================== ADMIN: VERSION MANAGEMENT ====================

@app.post("/admin/versions", tags=["Admin"])
async def create_version(
    version: VersionCreate,
    file: UploadFile = File(...),
    _: bool = Depends(verify_admin_key)
):
    """Yeni sürüm yükle"""
    version_id = f"v{version.version_name.replace('.', '-')}"
    version_dir = VERSIONS_DIR / version_id
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Dosyayı kaydet
    file_path = version_dir / file.filename
    contents = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Hash hesapla
    file_hash = hashlib.sha256(contents).hexdigest()
    
    # Veritabanına ekle
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO versions (version_id, version_name, channel, changelog, min_required_version, file_path, file_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (version_id, version.version_name, version.channel, version.changelog, 
          version.min_required_version, str(file_path), file_hash))
    conn.commit()
    conn.close()
    
    return {
        "version_id": version_id,
        "version_name": version.version_name,
        "file_hash": file_hash
    }

@app.get("/admin/versions", tags=["Admin"])
async def list_versions(_: bool = Depends(verify_admin_key)):
    """Tüm sürümleri listele"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT version_id, version_name, channel, release_date, is_active FROM versions ORDER BY release_date DESC")
    versions = [dict(row) for row in cur.fetchall()]
    conn.close()
    return versions

@app.get("/admin/stats", tags=["Admin"])
async def get_stats(_: bool = Depends(verify_admin_key)):
    """İstatistikler"""
    conn = get_db()
    cur = conn.cursor()
    
    # Toplam müşteri
    cur.execute("SELECT COUNT(*) FROM customers WHERE is_active = 1")
    total_customers = cur.fetchone()[0]
    
    # Bugünkü OCR işlemleri
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT COUNT(*) FROM ocr_logs WHERE DATE(timestamp) = ?", (today,))
    today_ocr = cur.fetchone()[0]
    
    # Toplam yedek
    cur.execute("SELECT COUNT(*) FROM backup_logs WHERE status = 'success'")
    total_backups = cur.fetchone()[0]
    
    # Sürüm dağılımı
    cur.execute("SELECT current_version, COUNT(*) as count FROM customers GROUP BY current_version")
    version_dist = {row[0]: row[1] for row in cur.fetchall()}
    
    conn.close()
    
    return {
        "total_customers": total_customers,
        "today_ocr_requests": today_ocr,
        "total_backups": total_backups,
        "version_distribution": version_dist
    }

# ==================== ADMIN: CUSTOMER BACKUP MANAGEMENT ====================

@app.get("/admin/customers/{customer_id}/backups", tags=["Admin"])
async def admin_list_customer_backups(customer_id: str, _: bool = Depends(verify_admin_key)):
    """Müşterinin tüm yedeklerini listele"""
    customer_backup_dir = CUSTOMERS_DIR / customer_id / "backups"
    
    if not customer_backup_dir.exists():
        return {"customer_id": customer_id, "backups": [], "message": "Yedek bulunamadı"}
    
    backups = []
    for f in sorted(customer_backup_dir.glob("*.db"), reverse=True):
        backups.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    # Backup loglarından da çek
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT backup_id, timestamp, backup_type, file_size, status, file_path
        FROM backup_logs WHERE customer_id = ? ORDER BY timestamp DESC LIMIT 50
    ''', (customer_id,))
    logs = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return {
        "customer_id": customer_id,
        "backups": backups,
        "backup_logs": logs,
        "total_count": len(backups)
    }

@app.get("/admin/customers/{customer_id}/backups/{filename}", tags=["Admin"])
async def admin_download_customer_backup(
    customer_id: str, 
    filename: str, 
    _: bool = Depends(verify_admin_key)
):
    """Müşterinin yedeğini indir"""
    backup_path = CUSTOMERS_DIR / customer_id / "backups" / filename
    
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="Yedek bulunamadı")
    
    return FileResponse(
        path=str(backup_path),
        filename=f"{customer_id}_{filename}",
        media_type="application/octet-stream"
    )

@app.delete("/admin/customers/{customer_id}/backups/{filename}", tags=["Admin"])
async def admin_delete_customer_backup(
    customer_id: str, 
    filename: str, 
    _: bool = Depends(verify_admin_key)
):
    """Müşterinin yedeğini sil"""
    backup_path = CUSTOMERS_DIR / customer_id / "backups" / filename
    
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="Yedek bulunamadı")
    
    backup_path.unlink()
    return {"message": f"Yedek silindi: {filename}"}

# ==================== ADMIN: PUSH UPDATE TO CUSTOMER ====================

@app.post("/admin/customers/{customer_id}/push-update", tags=["Admin"])
async def admin_push_update_to_customer(
    customer_id: str,
    version_id: str,
    force: bool = False,
    _: bool = Depends(verify_admin_key)
):
    """Belirli müşteriye güncelleme gönder (zorunlu güncelleme)"""
    conn = get_db()
    cur = conn.cursor()
    
    # Müşteriyi kontrol et
    cur.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    customer = cur.fetchone()
    if not customer:
        conn.close()
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # Sürümü kontrol et
    cur.execute("SELECT * FROM versions WHERE version_id = ?", (version_id,))
    version = cur.fetchone()
    if not version:
        conn.close()
        raise HTTPException(status_code=404, detail="Sürüm bulunamadı")
    
    # Müşterinin güncelleme kanalını ve sürümünü güncelle
    cur.execute('''
        UPDATE customers 
        SET update_channel = ?, auto_update = 1
        WHERE customer_id = ?
    ''', (version['channel'], customer_id))
    
    # Zorunlu güncelleme bildirimi kaydet
    cur.execute('''
        INSERT INTO update_logs (customer_id, from_version, to_version, status)
        VALUES (?, ?, ?, 'pending_push')
    ''', (customer_id, customer['current_version'], version['version_name']))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "customer_id": customer_id,
        "target_version": version['version_name'],
        "message": f"Güncelleme push edildi. Müşteri bir sonraki bağlantıda güncellenecek.",
        "force": force
    }

@app.post("/admin/push-update-all", tags=["Admin"])
async def admin_push_update_to_all(
    version_id: str,
    channel: str = "stable",
    _: bool = Depends(verify_admin_key)
):
    """Tüm müşterilere güncelleme gönder"""
    conn = get_db()
    cur = conn.cursor()
    
    # Sürümü kontrol et
    cur.execute("SELECT * FROM versions WHERE version_id = ?", (version_id,))
    version = cur.fetchone()
    if not version:
        conn.close()
        raise HTTPException(status_code=404, detail="Sürüm bulunamadı")
    
    # Belirtilen kanaldaki tüm müşterileri güncelle
    cur.execute('''
        SELECT customer_id, current_version FROM customers 
        WHERE update_channel = ? AND is_active = 1 AND auto_update = 1
    ''', (channel,))
    customers = cur.fetchall()
    
    updated_count = 0
    for customer in customers:
        if customer['current_version'] != version['version_name']:
            cur.execute('''
                INSERT INTO update_logs (customer_id, from_version, to_version, status)
                VALUES (?, ?, ?, 'pending_push')
            ''', (customer['customer_id'], customer['current_version'], version['version_name']))
            updated_count += 1
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "version": version['version_name'],
        "channel": channel,
        "customers_notified": updated_count
    }

@app.get("/admin/customers/{customer_id}/update-status", tags=["Admin"])
async def admin_get_customer_update_status(
    customer_id: str,
    _: bool = Depends(verify_admin_key)
):
    """Müşterinin güncelleme durumunu kontrol et"""
    conn = get_db()
    cur = conn.cursor()
    
    # Müşteri bilgisi
    cur.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    customer = cur.fetchone()
    if not customer:
        conn.close()
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # Son güncelleme logları
    cur.execute('''
        SELECT * FROM update_logs 
        WHERE customer_id = ? 
        ORDER BY timestamp DESC LIMIT 10
    ''', (customer_id,))
    logs = [dict(row) for row in cur.fetchall()]
    
    # En son sürüm
    cur.execute('''
        SELECT version_name FROM versions 
        WHERE channel = ? AND is_active = 1
        ORDER BY release_date DESC LIMIT 1
    ''', (customer['update_channel'],))
    latest = cur.fetchone()
    
    conn.close()
    
    is_up_to_date = latest and customer['current_version'] == latest['version_name']
    
    return {
        "customer_id": customer_id,
        "current_version": customer['current_version'],
        "latest_version": latest['version_name'] if latest else None,
        "update_channel": customer['update_channel'],
        "auto_update": bool(customer['auto_update']),
        "is_up_to_date": is_up_to_date,
        "last_seen": customer['last_seen'],
        "update_logs": logs
    }

# ==================== ADMIN: CUSTOMER DATA EXPORT ====================

@app.get("/admin/customers/{customer_id}/export", tags=["Admin"])
async def admin_export_customer_data(
    customer_id: str,
    _: bool = Depends(verify_admin_key)
):
    """Müşterinin tüm verilerini dışa aktar"""
    conn = get_db()
    cur = conn.cursor()
    
    # Müşteri bilgisi
    cur.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    customer = cur.fetchone()
    if not customer:
        conn.close()
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # OCR logları
    cur.execute('''
        SELECT * FROM ocr_logs WHERE customer_id = ? ORDER BY timestamp DESC
    ''', (customer_id,))
    ocr_logs = [dict(row) for row in cur.fetchall()]
    
    # Backup logları
    cur.execute('''
        SELECT * FROM backup_logs WHERE customer_id = ? ORDER BY timestamp DESC
    ''', (customer_id,))
    backup_logs = [dict(row) for row in cur.fetchall()]
    
    # Update logları
    cur.execute('''
        SELECT * FROM update_logs WHERE customer_id = ? ORDER BY timestamp DESC
    ''', (customer_id,))
    update_logs = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    # Yedek dosyaları
    customer_backup_dir = CUSTOMERS_DIR / customer_id / "backups"
    backup_files = []
    if customer_backup_dir.exists():
        for f in customer_backup_dir.glob("*.db"):
            backup_files.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    
    return {
        "customer": dict(customer),
        "ocr_logs": ocr_logs,
        "backup_logs": backup_logs,
        "update_logs": update_logs,
        "backup_files": backup_files,
        "export_date": datetime.now().isoformat()
    }

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
