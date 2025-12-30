"""
BADER Süper Admin API
Merkezi lisans yönetimi, müşteri kontrolü ve versiyon yönetimi
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Date, Text, Float, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid
import hashlib
import secrets
import jwt
import bcrypt
import os

# ==================== CONFIG ====================

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://bader:bader_secure_2025@bader-db:5432/bader")
    secret_key: str = os.getenv("SECRET_KEY", "bader-super-admin-secret-key-2025")
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "bader-admin-api-key-secure")

settings = Settings()

# ==================== DATABASE ====================

engine = create_engine(settings.database_url)
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
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), unique=True, nullable=False, index=True)
    organization_name = Column(String(200))
    contact_name = Column(String(100))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    address = Column(Text)
    
    # Lisans bilgileri
    license_type = Column(String(20), default="DEMO")  # LOCAL, ONLINE, HYBRID, DEMO
    license_status = Column(String(20), default="ACTIVE")  # ACTIVE, SUSPENDED, EXPIRED, TRIAL
    license_start = Column(Date, default=date.today)
    license_end = Column(Date)
    
    # Limitler
    max_users = Column(Integer, default=5)
    max_members = Column(Integer, default=500)
    features = Column(JSON, default={})
    
    # Takip
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime)
    app_version = Column(String(20))
    os_info = Column(String(100))
    ip_address = Column(String(45))
    
    # Ödeme
    monthly_fee = Column(Float, default=0)
    total_paid = Column(Float, default=0)
    notes = Column(Text)


class LicenseLog(Base):
    __tablename__ = "license_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), index=True)
    action = Column(String(50))  # ACTIVATE, DEACTIVATE, LOGIN, SYNC, UPDATE, VERIFY
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)


class AppVersion(Base):
    __tablename__ = "app_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), nullable=False)
    platform = Column(String(20))  # windows, macos, linux, all
    download_url = Column(Text)
    file_size = Column(Integer)
    checksum = Column(String(64))
    release_notes = Column(Text)
    is_mandatory = Column(Boolean, default=False)
    min_supported_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    role = Column(String(20), default="admin")  # superadmin, admin, viewer
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# Tabloları oluştur
Base.metadata.create_all(bind=engine)

# ==================== SCHEMAS ====================

class AdminLogin(BaseModel):
    username: str
    password: str

class CustomerCreate(BaseModel):
    organization_name: str
    contact_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    license_type: str = "DEMO"
    license_days: int = 365
    max_users: int = 5
    max_members: int = 500
    monthly_fee: float = 0
    notes: Optional[str] = None

class CustomerUpdate(BaseModel):
    organization_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    license_type: Optional[str] = None
    license_status: Optional[str] = None
    license_end: Optional[date] = None
    max_users: Optional[int] = None
    max_members: Optional[int] = None
    monthly_fee: Optional[float] = None
    notes: Optional[str] = None

class LicenseGenerate(BaseModel):
    license_type: str = "LOCAL"
    organization_name: str
    contact_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    license_days: int = 365
    max_users: int = 5
    max_members: int = 500

class VersionCreate(BaseModel):
    version: str
    platform: str = "all"
    download_url: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    release_notes: Optional[str] = None
    is_mandatory: bool = False
    min_supported_version: Optional[str] = None

class LicenseVerifyRequest(BaseModel):
    customer_id: str
    app_version: Optional[str] = None
    os_info: Optional[str] = None

# ==================== APP ====================

app = FastAPI(
    title="BADER Süper Admin API",
    description="Merkezi lisans ve müşteri yönetimi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ==================== AUTH ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_admin_token(admin_id: int, username: str, role: str) -> str:
    payload = {
        "admin_id": admin_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi dolmuş")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

def generate_license_key(license_type: str) -> str:
    """Benzersiz lisans kodu oluştur"""
    year = datetime.now().year
    unique_id = secrets.token_hex(4).upper()
    return f"BADER-{license_type}-{year}-{unique_id}"

# ==================== ADMIN AUTH ENDPOINTS ====================

@app.post("/admin/auth/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == data.username, AdminUser.is_active == True).first()
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre")
    
    admin.last_login = datetime.utcnow()
    db.commit()
    
    token = create_admin_token(admin.id, admin.username, admin.role)
    return {
        "success": True,
        "token": token,
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "full_name": admin.full_name,
            "role": admin.role
        }
    }

@app.get("/admin/auth/me")
def admin_me(admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    admin_user = db.query(AdminUser).filter(AdminUser.id == admin["admin_id"]).first()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin bulunamadı")
    return {
        "id": admin_user.id,
        "username": admin_user.username,
        "full_name": admin_user.full_name,
        "role": admin_user.role,
        "email": admin_user.email
    }

# ==================== DASHBOARD ====================

@app.get("/admin/dashboard")
def admin_dashboard(admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    total_customers = db.query(Customer).count()
    active_licenses = db.query(Customer).filter(Customer.license_status == "ACTIVE").count()
    demo_licenses = db.query(Customer).filter(Customer.license_type == "DEMO").count()
    expired_licenses = db.query(Customer).filter(Customer.license_status == "EXPIRED").count()
    
    # Bu ay gelir
    this_month = datetime.now().replace(day=1)
    monthly_revenue = db.query(func.sum(Customer.monthly_fee)).filter(
        Customer.license_status == "ACTIVE"
    ).scalar() or 0
    
    # Son 7 gün aktivite
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_last_week = db.query(Customer).filter(Customer.last_seen >= week_ago).count()
    
    # Süresi yakında dolacaklar
    next_month = date.today() + timedelta(days=30)
    expiring_soon = db.query(Customer).filter(
        Customer.license_end <= next_month,
        Customer.license_end >= date.today(),
        Customer.license_status == "ACTIVE"
    ).count()
    
    # Lisans tipi dağılımı
    license_distribution = {}
    for lt in ["LOCAL", "ONLINE", "HYBRID", "DEMO"]:
        count = db.query(Customer).filter(Customer.license_type == lt).count()
        license_distribution[lt] = count
    
    # Son aktiviteler
    recent_logs = db.query(LicenseLog).order_by(LicenseLog.created_at.desc()).limit(10).all()
    
    return {
        "stats": {
            "total_customers": total_customers,
            "active_licenses": active_licenses,
            "demo_licenses": demo_licenses,
            "expired_licenses": expired_licenses,
            "monthly_revenue": monthly_revenue,
            "active_last_week": active_last_week,
            "expiring_soon": expiring_soon
        },
        "license_distribution": license_distribution,
        "recent_activity": [
            {
                "customer_id": log.customer_id,
                "action": log.action,
                "created_at": log.created_at.isoformat() if log.created_at else None
            } for log in recent_logs
        ]
    }

# ==================== CUSTOMER MANAGEMENT ====================

@app.get("/admin/customers")
def list_customers(
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
    license_type: Optional[str] = None,
    license_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    query = db.query(Customer)
    
    if license_type:
        query = query.filter(Customer.license_type == license_type)
    if license_status:
        query = query.filter(Customer.license_status == license_status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Customer.organization_name.ilike(search_pattern)) |
            (Customer.contact_name.ilike(search_pattern)) |
            (Customer.customer_id.ilike(search_pattern))
        )
    
    total = query.count()
    customers = query.order_by(Customer.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "customers": [
            {
                "id": str(c.id),
                "customer_id": c.customer_id,
                "organization_name": c.organization_name,
                "contact_name": c.contact_name,
                "contact_email": c.contact_email,
                "contact_phone": c.contact_phone,
                "license_type": c.license_type,
                "license_status": c.license_status,
                "license_start": c.license_start.isoformat() if c.license_start else None,
                "license_end": c.license_end.isoformat() if c.license_end else None,
                "max_users": c.max_users,
                "max_members": c.max_members,
                "monthly_fee": c.monthly_fee,
                "last_seen": c.last_seen.isoformat() if c.last_seen else None,
                "app_version": c.app_version,
                "created_at": c.created_at.isoformat() if c.created_at else None
            } for c in customers
        ]
    }

@app.get("/admin/customers/{customer_id}")
def get_customer(customer_id: str, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # Son loglar
    logs = db.query(LicenseLog).filter(
        LicenseLog.customer_id == customer_id
    ).order_by(LicenseLog.created_at.desc()).limit(50).all()
    
    return {
        "customer": {
            "id": str(customer.id),
            "customer_id": customer.customer_id,
            "organization_name": customer.organization_name,
            "contact_name": customer.contact_name,
            "contact_email": customer.contact_email,
            "contact_phone": customer.contact_phone,
            "address": customer.address,
            "license_type": customer.license_type,
            "license_status": customer.license_status,
            "license_start": customer.license_start.isoformat() if customer.license_start else None,
            "license_end": customer.license_end.isoformat() if customer.license_end else None,
            "max_users": customer.max_users,
            "max_members": customer.max_members,
            "features": customer.features,
            "monthly_fee": customer.monthly_fee,
            "total_paid": customer.total_paid,
            "notes": customer.notes,
            "last_seen": customer.last_seen.isoformat() if customer.last_seen else None,
            "app_version": customer.app_version,
            "os_info": customer.os_info,
            "ip_address": customer.ip_address,
            "created_at": customer.created_at.isoformat() if customer.created_at else None
        },
        "logs": [
            {
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            } for log in logs
        ]
    }

@app.post("/admin/customers")
def create_customer(data: CustomerCreate, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer_id = generate_license_key(data.license_type)
    
    customer = Customer(
        customer_id=customer_id,
        organization_name=data.organization_name,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        address=data.address,
        license_type=data.license_type,
        license_status="ACTIVE",
        license_start=date.today(),
        license_end=date.today() + timedelta(days=data.license_days),
        max_users=data.max_users,
        max_members=data.max_members,
        monthly_fee=data.monthly_fee,
        notes=data.notes
    )
    db.add(customer)
    
    # Log
    log = LicenseLog(
        customer_id=customer_id,
        action="CREATE",
        details={"created_by": admin["username"], "license_type": data.license_type}
    )
    db.add(log)
    
    db.commit()
    
    return {"success": True, "customer_id": customer_id, "message": "Müşteri oluşturuldu"}

@app.put("/admin/customers/{customer_id}")
def update_customer(customer_id: str, data: CustomerUpdate, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)
    
    # Log
    log = LicenseLog(
        customer_id=customer_id,
        action="UPDATE",
        details={"updated_by": admin["username"], "changes": update_data}
    )
    db.add(log)
    
    db.commit()
    
    return {"success": True, "message": "Müşteri güncellendi"}

@app.delete("/admin/customers/{customer_id}")
def delete_customer(customer_id: str, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # Log before delete
    log = LicenseLog(
        customer_id=customer_id,
        action="DELETE",
        details={"deleted_by": admin["username"]}
    )
    db.add(log)
    
    db.delete(customer)
    db.commit()
    
    return {"success": True, "message": "Müşteri silindi"}

# ==================== LICENSE MANAGEMENT ====================

@app.post("/admin/licenses/generate")
def generate_license(data: LicenseGenerate, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer_id = generate_license_key(data.license_type)
    
    customer = Customer(
        customer_id=customer_id,
        organization_name=data.organization_name,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        license_type=data.license_type,
        license_status="ACTIVE",
        license_start=date.today(),
        license_end=date.today() + timedelta(days=data.license_days),
        max_users=data.max_users,
        max_members=data.max_members
    )
    db.add(customer)
    
    log = LicenseLog(
        customer_id=customer_id,
        action="GENERATE",
        details={"generated_by": admin["username"], "type": data.license_type}
    )
    db.add(log)
    
    db.commit()
    
    return {
        "success": True,
        "license": {
            "customer_id": customer_id,
            "license_type": data.license_type,
            "license_end": (date.today() + timedelta(days=data.license_days)).isoformat(),
            "max_users": data.max_users,
            "max_members": data.max_members
        }
    }

@app.put("/admin/licenses/{customer_id}/activate")
def activate_license(customer_id: str, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Lisans bulunamadı")
    
    customer.license_status = "ACTIVE"
    
    log = LicenseLog(
        customer_id=customer_id,
        action="ACTIVATE",
        details={"activated_by": admin["username"]}
    )
    db.add(log)
    db.commit()
    
    return {"success": True, "message": "Lisans aktifleştirildi"}

@app.put("/admin/licenses/{customer_id}/suspend")
def suspend_license(customer_id: str, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Lisans bulunamadı")
    
    customer.license_status = "SUSPENDED"
    
    log = LicenseLog(
        customer_id=customer_id,
        action="SUSPEND",
        details={"suspended_by": admin["username"]}
    )
    db.add(log)
    db.commit()
    
    return {"success": True, "message": "Lisans askıya alındı"}

@app.put("/admin/licenses/{customer_id}/extend")
def extend_license(customer_id: str, days: int = 365, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Lisans bulunamadı")
    
    if customer.license_end:
        new_end = customer.license_end + timedelta(days=days)
    else:
        new_end = date.today() + timedelta(days=days)
    
    customer.license_end = new_end
    customer.license_status = "ACTIVE"
    
    log = LicenseLog(
        customer_id=customer_id,
        action="EXTEND",
        details={"extended_by": admin["username"], "days": days, "new_end": new_end.isoformat()}
    )
    db.add(log)
    db.commit()
    
    return {"success": True, "message": f"Lisans {days} gün uzatıldı", "new_end": new_end.isoformat()}

@app.put("/admin/licenses/{customer_id}/upgrade")
def upgrade_license(customer_id: str, new_type: str, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Lisans bulunamadı")
    
    old_type = customer.license_type
    
    # Yeni lisans kodu oluştur
    new_customer_id = generate_license_key(new_type)
    customer.customer_id = new_customer_id
    customer.license_type = new_type
    
    log = LicenseLog(
        customer_id=new_customer_id,
        action="UPGRADE",
        details={
            "upgraded_by": admin["username"],
            "old_type": old_type,
            "new_type": new_type,
            "old_customer_id": customer_id
        }
    )
    db.add(log)
    db.commit()
    
    return {"success": True, "message": f"Lisans {old_type} → {new_type} yükseltildi", "new_customer_id": new_customer_id}

@app.get("/admin/licenses/expiring")
def get_expiring_licenses(days: int = 30, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    cutoff = date.today() + timedelta(days=days)
    customers = db.query(Customer).filter(
        Customer.license_end <= cutoff,
        Customer.license_end >= date.today(),
        Customer.license_status == "ACTIVE"
    ).order_by(Customer.license_end).all()
    
    return {
        "count": len(customers),
        "customers": [
            {
                "customer_id": c.customer_id,
                "organization_name": c.organization_name,
                "contact_name": c.contact_name,
                "contact_email": c.contact_email,
                "license_type": c.license_type,
                "license_end": c.license_end.isoformat() if c.license_end else None,
                "days_remaining": (c.license_end - date.today()).days if c.license_end else 0
            } for c in customers
        ]
    }

# ==================== VERSION MANAGEMENT ====================

@app.get("/admin/versions")
def list_versions(admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    versions = db.query(AppVersion).order_by(AppVersion.created_at.desc()).all()
    return {
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "platform": v.platform,
                "download_url": v.download_url,
                "file_size": v.file_size,
                "release_notes": v.release_notes,
                "is_mandatory": v.is_mandatory,
                "min_supported_version": v.min_supported_version,
                "is_active": v.is_active,
                "created_at": v.created_at.isoformat() if v.created_at else None
            } for v in versions
        ]
    }

@app.post("/admin/versions")
def create_version(data: VersionCreate, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    version = AppVersion(
        version=data.version,
        platform=data.platform,
        download_url=data.download_url,
        file_size=data.file_size,
        checksum=data.checksum,
        release_notes=data.release_notes,
        is_mandatory=data.is_mandatory,
        min_supported_version=data.min_supported_version
    )
    db.add(version)
    db.commit()
    
    return {"success": True, "id": version.id, "message": "Versiyon eklendi"}

@app.put("/admin/versions/{version_id}")
def update_version(version_id: int, data: VersionCreate, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Versiyon bulunamadı")
    
    for key, value in data.dict().items():
        setattr(version, key, value)
    
    db.commit()
    
    return {"success": True, "message": "Versiyon güncellendi"}

@app.delete("/admin/versions/{version_id}")
def delete_version(version_id: int, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Versiyon bulunamadı")
    
    db.delete(version)
    db.commit()
    
    return {"success": True, "message": "Versiyon silindi"}

# ==================== LICENSE VERIFICATION (Public API) ====================

@app.post("/license/verify")
def verify_license(data: LicenseVerifyRequest, db: Session = Depends(get_db)):
    """Desktop uygulaması tarafından çağrılır - lisans doğrulama"""
    customer = db.query(Customer).filter(Customer.customer_id == data.customer_id).first()
    
    if not customer:
        return {
            "valid": False,
            "error": "LICENSE_NOT_FOUND",
            "message": "Lisans bulunamadı"
        }
    
    # Süre kontrolü
    if customer.license_end and customer.license_end < date.today():
        customer.license_status = "EXPIRED"
        db.commit()
        return {
            "valid": False,
            "error": "LICENSE_EXPIRED",
            "message": "Lisans süresi dolmuş",
            "expired_at": customer.license_end.isoformat()
        }
    
    # Durum kontrolü
    if customer.license_status != "ACTIVE":
        return {
            "valid": False,
            "error": f"LICENSE_{customer.license_status}",
            "message": f"Lisans durumu: {customer.license_status}"
        }
    
    # Güncelle
    customer.last_seen = datetime.utcnow()
    if data.app_version:
        customer.app_version = data.app_version
    if data.os_info:
        customer.os_info = data.os_info
    
    # Log
    log = LicenseLog(
        customer_id=data.customer_id,
        action="VERIFY",
        details={"app_version": data.app_version, "os_info": data.os_info}
    )
    db.add(log)
    db.commit()
    
    return {
        "valid": True,
        "license": {
            "customer_id": customer.customer_id,
            "organization_name": customer.organization_name,
            "license_type": customer.license_type,
            "license_status": customer.license_status,
            "license_end": customer.license_end.isoformat() if customer.license_end else None,
            "days_remaining": (customer.license_end - date.today()).days if customer.license_end else 999,
            "max_users": customer.max_users,
            "max_members": customer.max_members,
            "features": customer.features or {}
        }
    }

@app.get("/license/check-update")
def check_update(current_version: str, platform: str = "all", db: Session = Depends(get_db)):
    """Desktop uygulaması tarafından çağrılır - güncelleme kontrolü"""
    latest = db.query(AppVersion).filter(
        AppVersion.is_active == True,
        (AppVersion.platform == platform) | (AppVersion.platform == "all")
    ).order_by(AppVersion.created_at.desc()).first()
    
    if not latest:
        return {"update_available": False}
    
    # Basit versiyon karşılaştırma
    def parse_version(v):
        try:
            return tuple(map(int, v.split('.')))
        except:
            return (0, 0, 0)
    
    current = parse_version(current_version)
    latest_ver = parse_version(latest.version)
    
    if latest_ver > current:
        return {
            "update_available": True,
            "version": latest.version,
            "download_url": latest.download_url,
            "file_size": latest.file_size,
            "release_notes": latest.release_notes,
            "is_mandatory": latest.is_mandatory
        }
    
    return {"update_available": False}

# ==================== STATS ====================

@app.get("/admin/stats/usage")
def usage_stats(days: int = 30, admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Günlük aktif kullanıcılar
    daily_active = db.query(
        func.date(LicenseLog.created_at).label('date'),
        func.count(func.distinct(LicenseLog.customer_id)).label('count')
    ).filter(
        LicenseLog.created_at >= cutoff,
        LicenseLog.action == "VERIFY"
    ).group_by(func.date(LicenseLog.created_at)).all()
    
    # En aktif müşteriler
    top_customers = db.query(
        LicenseLog.customer_id,
        func.count(LicenseLog.id).label('activity_count')
    ).filter(
        LicenseLog.created_at >= cutoff
    ).group_by(LicenseLog.customer_id).order_by(func.count(LicenseLog.id).desc()).limit(10).all()
    
    return {
        "daily_active": [{"date": str(d.date), "count": d.count} for d in daily_active],
        "top_customers": [{"customer_id": c.customer_id, "activity_count": c.activity_count} for c in top_customers]
    }

@app.get("/admin/stats/revenue")
def revenue_stats(admin: dict = Depends(verify_admin_token), db: Session = Depends(get_db)):
    # Lisans tipine göre gelir
    by_type = {}
    for lt in ["LOCAL", "ONLINE", "HYBRID"]:
        total = db.query(func.sum(Customer.monthly_fee)).filter(
            Customer.license_type == lt,
            Customer.license_status == "ACTIVE"
        ).scalar() or 0
        count = db.query(Customer).filter(
            Customer.license_type == lt,
            Customer.license_status == "ACTIVE"
        ).count()
        by_type[lt] = {"monthly_revenue": float(total), "customer_count": count}
    
    total_monthly = sum(t["monthly_revenue"] for t in by_type.values())
    
    return {
        "by_license_type": by_type,
        "total_monthly_revenue": total_monthly,
        "total_yearly_revenue": total_monthly * 12
    }

@app.get("/admin/logs")
def get_logs(
    admin: dict = Depends(verify_admin_token),
    db: Session = Depends(get_db),
    customer_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
):
    query = db.query(LicenseLog)
    
    if customer_id:
        query = query.filter(LicenseLog.customer_id == customer_id)
    if action:
        query = query.filter(LicenseLog.action == action)
    
    logs = query.order_by(LicenseLog.created_at.desc()).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "customer_id": log.customer_id,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            } for log in logs
        ]
    }

# ==================== SETUP ====================

@app.on_event("startup")
def startup():
    """İlk başlatmada admin kullanıcı oluştur"""
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == "superadmin").first()
        if not admin:
            admin = AdminUser(
                username="superadmin",
                password_hash=hash_password("Bader2025!"),
                full_name="Süper Admin",
                email="admin@bfrdernek.com",
                role="superadmin"
            )
            db.add(admin)
            db.commit()
            print("✅ Süper Admin kullanıcısı oluşturuldu: superadmin / Bader2025!")
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "healthy", "service": "admin-api", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
