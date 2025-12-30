"""
BADER API Server v4.0.0
Modern PostgreSQL + SQLAlchemy Architecture
"""

from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Date, Text, Numeric, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional, List, Any
from datetime import datetime, date, timedelta
from jose import JWTError, jwt
import uuid
import secrets
import os
import hashlib

# ==================== CONFIGURATION ====================

class Settings(BaseSettings):
    database_url: str = "postgresql://bader:bader_secure_2025@localhost:5432/bader"
    secret_key: str = "bader_secret_key_change_in_production"
    admin_secret: str = "BADER_ADMIN_2025_SUPER_SECRET"
    upload_dir: str = "/app/uploads"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    
    class Config:
        env_file = ".env"

settings = Settings()

# ==================== DATABASE ====================

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== MODELS ====================

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), unique=True, nullable=False)
    api_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    plan = Column(String(20), default="basic")
    max_users = Column(Integer, default=5)
    max_members = Column(Integer, default=500)
    is_active = Column(Boolean, default=True)
    expires_at = Column(Date)
    features = Column(JSON, default=["ocr", "sync", "backup"])
    settings = Column(JSON, default={})
    last_seen_at = Column(DateTime)
    device_info = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    role = Column(String(20), default="member")
    permissions = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    auth_token = Column(String(255))
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AppVersion(Base):
    __tablename__ = "app_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(20), unique=True, nullable=False)
    platform = Column(String(20), default="all")
    download_url = Column(String(500))
    file_path = Column(String(500))
    file_size = Column(Integer)
    changelog = Column(Text)
    min_required_version = Column(String(20))
    is_critical = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    released_at = Column(DateTime, default=datetime.utcnow)

class ActivationLog(Base):
    __tablename__ = "activation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50))
    device_info = Column(JSON)
    ip_address = Column(String(50))
    success = Column(Boolean)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== PASSWORD & AUTH ====================

import bcrypt

def hash_password(password: str) -> str:
    """Şifreyi bcrypt ile hashle"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifreyi doğrula"""
    try:
        # Eğer bcrypt hash ise ($2a$, $2b$, $2y$ ile başlar)
        if hashed_password.startswith('$2'):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        
        # SHA256 hash ise (64 karakter hex)
        if len(hashed_password) == 64:
            import hashlib
            computed_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
            return computed_hash == hashed_password
        
        # Plain text ise doğrudan karşılaştır
        return plain_password == hashed_password
    except:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

# ==================== DEPENDENCIES ====================

def verify_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    return True

def verify_api_key(x_api_key: str = Header(None), authorization: str = Header(None)):
    api_key = x_api_key or (authorization.replace("Bearer ", "") if authorization else None)
    if not api_key:
        raise HTTPException(status_code=401, detail="API key gerekli")
    return api_key

# ==================== SCHEMAS ====================

class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    plan: str = "basic"
    max_users: int = 5
    max_members: int = 500
    expires_at: Optional[str] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    id: str
    customer_id: str
    api_key: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    plan: str
    max_users: int
    max_members: int
    is_active: bool
    expires_at: Optional[str]
    last_seen_at: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True

class VersionCreate(BaseModel):
    version: str
    platform: str = "all"
    changelog: str = ""
    min_required_version: Optional[str] = None
    is_critical: bool = False

class LoginRequest(BaseModel):
    customer_id: str
    username: str
    password: str

class ActivateRequest(BaseModel):
    license_key: str
    device_info: Optional[dict] = None

# ==================== APP ====================

app = FastAPI(
    title="BADER API",
    version="4.0.0",
    description="BADER Dernek & Köy Yönetim Sistemi API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(f"{settings.upload_dir}/updates", exist_ok=True)

# ==================== HEALTH ====================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0"
    }

# ==================== ACTIVATION ====================

@app.post("/activate")
def activate_license(request: ActivateRequest, db: Session = Depends(get_db)):
    """Masaüstü uygulama lisans aktivasyonu"""
    
    # Lisans bul
    customer = db.query(Customer).filter(
        (Customer.customer_id == request.license_key) | 
        (Customer.api_key == request.license_key)
    ).first()
    
    # Log kaydet
    log = ActivationLog(
        customer_id=request.license_key,
        device_info=request.device_info,
        success=customer is not None,
        message="Aktivasyon başarılı" if customer else "Geçersiz lisans"
    )
    db.add(log)
    db.commit()
    
    if not customer:
        raise HTTPException(status_code=401, detail="Geçersiz lisans anahtarı")
    
    if not customer.is_active:
        raise HTTPException(status_code=401, detail="Lisans devre dışı")
    
    if customer.expires_at and customer.expires_at < date.today():
        raise HTTPException(status_code=401, detail="Lisans süresi dolmuş")
    
    # Son görülme güncelle
    customer.last_seen_at = datetime.utcnow()
    customer.device_info = request.device_info
    db.commit()
    
    return {
        "success": True,
        "customer_id": customer.customer_id,
        "api_key": customer.api_key,
        "name": customer.name,
        "plan": customer.plan,
        "expires": customer.expires_at.isoformat() if customer.expires_at else None,
        "features": customer.features
    }

# ==================== VERSION CHECK ====================

@app.get("/version/check")
def check_version(
    current_version: str,
    platform: str = "all",
    db: Session = Depends(get_db)
):
    """Güncelleme kontrolü"""
    
    # En son aktif versiyonu bul
    latest = db.query(AppVersion).filter(
        AppVersion.is_active == True,
        (AppVersion.platform == platform) | (AppVersion.platform == "all")
    ).order_by(AppVersion.released_at.desc()).first()
    
    if not latest:
        return {
            "has_update": False,
            "current_version": current_version,
            "latest_version": current_version,
            "message": "Güncel sürümdesiniz"
        }
    
    # Versiyon karşılaştır
    def parse_version(v):
        return tuple(map(int, v.replace("v", "").split(".")))
    
    try:
        has_update = parse_version(latest.version) > parse_version(current_version)
    except:
        has_update = latest.version != current_version
    
    # Kritik güncelleme kontrolü
    force_update = False
    if latest.min_required_version:
        try:
            force_update = parse_version(current_version) < parse_version(latest.min_required_version)
        except:
            pass
    
    return {
        "has_update": has_update,
        "current_version": current_version,
        "latest_version": latest.version,
        "download_url": latest.download_url,
        "changelog": latest.changelog,
        "is_critical": latest.is_critical,
        "force_update": force_update or latest.is_critical,
        "file_size": latest.file_size,
        "message": f"Yeni sürüm mevcut: {latest.version}" if has_update else "Güncel sürümdesiniz"
    }

# ==================== AUTH ====================

@app.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Kullanıcı girişi"""
    
    user = db.query(User).filter(
        User.customer_id == request.customer_id,
        User.username == request.username,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    
    # Şifre kontrolü
    password_valid = False
    
    # 1. Bcrypt hash kontrolü
    try:
        if verify_password(request.password, user.password_hash):
            password_valid = True
    except:
        pass
    
    # 2. Plain text kontrolü (ilk giriş veya migrasyon)
    if not password_valid:
        plain_hash = hashlib.sha256(request.password.encode()).hexdigest()
        if plain_hash == user.password_hash:
            password_valid = True
            # Şifreyi bcrypt'e yükselt
            user.password_hash = hash_password(request.password)
    
    # 3. Eğer hala geçersizse direkt karşılaştır (demo amaçlı)
    if not password_valid and user.password_hash == request.password:
        password_valid = True
        user.password_hash = hash_password(request.password)
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Şifre hatalı")
    
    # Token oluştur
    token = create_access_token({"sub": str(user.id), "customer_id": user.customer_id})
    
    # Güncelle
    user.auth_token = token
    user.last_login_at = datetime.utcnow()
    user.token_expires_at = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
    db.commit()
    
    return {
        "success": True,
        "token": token,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "permissions": user.permissions
        }
    }

# ==================== ADMIN - CUSTOMERS ====================

@app.get("/admin/dashboard")
def admin_dashboard(db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Admin dashboard istatistikleri"""
    
    total_customers = db.query(Customer).filter(Customer.is_active == True).count()
    
    # Plan dağılımı
    from sqlalchemy import func
    plan_dist = db.query(Customer.plan, func.count(Customer.id)).filter(
        Customer.is_active == True
    ).group_by(Customer.plan).all()
    
    # Son 24 saat aktivasyon
    yesterday = datetime.utcnow() - timedelta(hours=24)
    activations_24h = db.query(ActivationLog).filter(
        ActivationLog.created_at > yesterday
    ).count()
    
    # Son 7 gün aktivasyon
    week_ago = datetime.utcnow() - timedelta(days=7)
    activations_7d = db.query(ActivationLog).filter(
        ActivationLog.created_at > week_ago
    ).count()
    
    # Aktif versiyon
    latest_version = db.query(AppVersion).filter(
        AppVersion.is_active == True
    ).order_by(AppVersion.released_at.desc()).first()
    
    return {
        "total_customers": total_customers,
        "plan_distribution": {plan: count for plan, count in plan_dist},
        "activations_24h": activations_24h,
        "activations_7d": activations_7d,
        "active_version": latest_version.version if latest_version else "1.0.0"
    }

@app.get("/admin/customers")
def admin_list_customers(db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Müşteri listesi"""
    customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
    
    return {
        "customers": [
            {
                "id": str(c.id),
                "customer_id": c.customer_id,
                "api_key": c.api_key,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "plan": c.plan,
                "max_users": c.max_users,
                "max_members": c.max_members,
                "is_active": c.is_active,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in customers
        ]
    }

@app.post("/admin/customers")
def admin_create_customer(data: CustomerCreate, db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Yeni müşteri oluştur"""
    
    customer_id = f"BADER-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
    api_key = f"bader_api_{secrets.token_hex(16)}"
    
    customer = Customer(
        customer_id=customer_id,
        api_key=api_key,
        name=data.name,
        email=data.email,
        phone=data.phone,
        address=data.address,
        plan=data.plan,
        max_users=data.max_users,
        max_members=data.max_members,
        expires_at=datetime.strptime(data.expires_at, "%Y-%m-%d").date() if data.expires_at else None,
        notes=data.notes
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return {
        "success": True,
        "customer_id": customer.customer_id,
        "api_key": customer.api_key,
        "message": f"Müşteri oluşturuldu: {data.name}"
    }

@app.get("/admin/customers/{customer_id}")
def admin_get_customer(customer_id: str, db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Müşteri detayı"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    return {
        "id": str(customer.id),
        "customer_id": customer.customer_id,
        "api_key": customer.api_key,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "plan": customer.plan,
        "max_users": customer.max_users,
        "max_members": customer.max_members,
        "is_active": customer.is_active,
        "expires_at": customer.expires_at.isoformat() if customer.expires_at else None,
        "features": customer.features,
        "last_seen_at": customer.last_seen_at.isoformat() if customer.last_seen_at else None,
        "device_info": customer.device_info,
        "notes": customer.notes,
        "created_at": customer.created_at.isoformat() if customer.created_at else None
    }

@app.put("/admin/customers/{customer_id}")
def admin_update_customer(customer_id: str, data: CustomerCreate, db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Müşteri güncelle"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    customer.name = data.name
    customer.email = data.email
    customer.phone = data.phone
    customer.address = data.address
    customer.plan = data.plan
    customer.max_users = data.max_users
    customer.max_members = data.max_members
    customer.expires_at = datetime.strptime(data.expires_at, "%Y-%m-%d").date() if data.expires_at else None
    customer.notes = data.notes
    
    db.commit()
    
    return {"success": True, "message": "Müşteri güncellendi"}

@app.delete("/admin/customers/{customer_id}")
def admin_delete_customer(customer_id: str, db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Müşteri devre dışı bırak"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    customer.is_active = False
    db.commit()
    
    return {"success": True, "message": "Müşteri devre dışı bırakıldı"}

@app.post("/admin/customers/{customer_id}/regenerate-key")
def admin_regenerate_api_key(customer_id: str, db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """API key yenile"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    customer.api_key = f"bader_api_{secrets.token_hex(16)}"
    db.commit()
    
    return {"success": True, "api_key": customer.api_key}

# ==================== ADMIN - VERSIONS ====================

@app.get("/admin/versions")
def admin_list_versions(db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Versiyon listesi"""
    versions = db.query(AppVersion).order_by(AppVersion.released_at.desc()).all()
    
    return {
        "versions": [
            {
                "id": str(v.id),
                "version": v.version,
                "platform": v.platform,
                "download_url": v.download_url,
                "file_size": v.file_size,
                "changelog": v.changelog,
                "min_required_version": v.min_required_version,
                "is_critical": v.is_critical,
                "is_active": v.is_active,
                "released_at": v.released_at.isoformat() if v.released_at else None
            }
            for v in versions
        ]
    }

@app.post("/admin/versions")
def admin_create_version(data: VersionCreate, db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Yeni versiyon oluştur"""
    
    version = AppVersion(
        version=data.version,
        platform=data.platform,
        changelog=data.changelog,
        min_required_version=data.min_required_version,
        is_critical=data.is_critical
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    return {"success": True, "id": str(version.id), "version": data.version}

@app.post("/admin/versions/{version}/upload")
async def admin_upload_version(version: str, file: UploadFile = File(...), db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    """Güncelleme dosyası yükle"""
    
    ver = db.query(AppVersion).filter(AppVersion.version == version).first()
    if not ver:
        raise HTTPException(status_code=404, detail="Versiyon bulunamadı")
    
    # Dosya kaydet
    ext = os.path.splitext(file.filename)[1]
    file_path = f"{settings.upload_dir}/updates/BADER-{version}{ext}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Veritabanı güncelle
    ver.file_path = file_path
    ver.file_size = len(content)
    ver.download_url = f"/uploads/updates/BADER-{version}{ext}"
    ver.is_active = True
    db.commit()
    
    return {
        "success": True,
        "message": f"Dosya yüklendi: {file.filename}",
        "size": len(content),
        "download_url": ver.download_url
    }

# ==================== ADMIN - LOGS ====================

@app.get("/admin/activation-logs")
def admin_activation_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: bool = Depends(verify_admin)
):
    """Aktivasyon logları"""
    logs = db.query(ActivationLog).order_by(ActivationLog.created_at.desc()).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "customer_id": log.customer_id,
                "device_info": log.device_info,
                "ip_address": log.ip_address,
                "success": log.success,
                "message": log.message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    }

# ==================== OCR ====================

@app.post("/ocr")
async def ocr_process(image: UploadFile = File(...)):
    """OCR işlemi"""
    import tempfile
    from PIL import Image
    import pytesseract
    import time
    import re
    
    start_time = time.time()
    
    # Dosyayı geçici olarak kaydet
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # OCR
        img = Image.open(tmp_path)
        raw_text = pytesseract.image_to_string(img, lang="tur")
        ocr_time = round(time.time() - start_time, 2)
        
        # Satırları ayıkla
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Tutarları bul
        amount_pattern = r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))\s*(?:TL|₺|tl)?'
        amounts = re.findall(amount_pattern, raw_text)
        amounts = [float(a.replace('.', '').replace(',', '.')) for a in amounts]
        
        # Tarihleri bul
        date_pattern = r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})'
        dates = re.findall(date_pattern, raw_text)
        
        # Kategori tahmin
        text_lower = raw_text.lower()
        if any(word in text_lower for word in ['elektrik', 'enerji', 'kwh']):
            category = 'ELEKTRİK'
        elif any(word in text_lower for word in ['su', 'iski', 'aski']):
            category = 'SU'
        elif any(word in text_lower for word in ['doğalgaz', 'igdaş', 'gaz']):
            category = 'DOĞALGAZ'
        elif any(word in text_lower for word in ['internet', 'fiber', 'ttnet', 'türk telekom']):
            category = 'İNTERNET'
        elif any(word in text_lower for word in ['market', 'migros', 'bim', 'a101', 'şok']):
            category = 'ALIŞVERİŞ'
        else:
            category = 'DİĞER'
        
        return {
            "success": True,
            "ocr_time": ocr_time,
            "raw_text": raw_text,
            "lines": lines,
            "amounts": amounts,
            "dates": dates,
            "suggested_category": category,
            "suggested_amount": max(amounts) if amounts else None,
            "suggested_date": dates[0] if dates else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
