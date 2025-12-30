"""
BADER API Server v4.1.0
Modern PostgreSQL + SQLAlchemy Architecture
+ Web Application Endpoints
"""

from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Date, Text, Numeric, ForeignKey, JSON, func
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
    database_url: str = "postgresql://bader:bader_secure_2025@bader-db:5432/bader"
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
    license_type = Column(String(20), default="DEMO")  # LOCAL, ONLINE, HYBRID, DEMO
    license_status = Column(String(20), default="ACTIVE")  # ACTIVE, SUSPENDED, EXPIRED
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

class Member(Base):
    __tablename__ = "members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    member_no = Column(Integer)
    full_name = Column(String(255), nullable=False)
    tc_no = Column(String(20))
    phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    birth_date = Column(Date)
    join_date = Column(Date, default=date.today)
    leave_date = Column(Date)
    status = Column(String(20), default="Aktif")
    membership_fee = Column(Numeric(10, 2), default=100)
    notes = Column(Text)
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Income(Base):
    __tablename__ = "incomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    member_id = Column(UUID(as_uuid=True))
    category = Column(String(50))
    amount = Column(Numeric(12, 2))
    currency = Column(String(10), default="TRY")
    date = Column(Date)
    description = Column(Text)
    receipt_no = Column(String(50))
    cash_account = Column(String(50), default="Ana Kasa")
    document_path = Column(String(500))
    fiscal_year = Column(Integer)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    category = Column(String(50))
    amount = Column(Numeric(12, 2))
    currency = Column(String(10), default="TRY")
    date = Column(Date)
    description = Column(Text)
    invoice_no = Column(String(50))
    vendor = Column(String(255))
    cash_account = Column(String(50), default="Ana Kasa")
    document_path = Column(String(500))
    fiscal_year = Column(Integer)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Due(Base):
    __tablename__ = "dues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    member_id = Column(UUID(as_uuid=True))
    year = Column(Integer)
    yearly_amount = Column(Numeric(10, 2), default=100)
    paid_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default="Bekliyor")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CashAccount(Base):
    __tablename__ = "cash_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    name = Column(String(100))
    account_type = Column(String(50))
    balance = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    key = Column(String(100))
    value = Column(Text)

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

class DynamicMenu(Base):
    __tablename__ = "dynamic_menus"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    icon = Column(String(50))
    route_key = Column(String(50))
    position = Column(String(20))
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    required_permission = Column(String(50))
    url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== PASSWORD & AUTH ====================

import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith('$2'):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        if len(hashed_password) == 64:
            computed_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
            return computed_hash == hashed_password
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

def get_customer_id(x_customer_id: str = Header(None)):
    if not x_customer_id:
        raise HTTPException(status_code=401, detail="Customer ID gerekli")
    return x_customer_id

def verify_web_access(x_customer_id: str = Header(None), db: Session = Depends(get_db)):
    """
    Web erişim kontrolü - sadece ONLINE ve HYBRID lisanslar web kullanabilir
    LOCAL lisanslar web'e erişemez
    """
    if not x_customer_id:
        raise HTTPException(status_code=401, detail="Customer ID gerekli")
    
    customer = db.query(Customer).filter(Customer.customer_id == x_customer_id).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # Lisans durumu kontrolü
    if customer.license_status != "ACTIVE":
        raise HTTPException(status_code=403, detail=f"Lisans durumu: {customer.license_status}")
    
    # Süre kontrolü
    if customer.expires_at and customer.expires_at < date.today():
        raise HTTPException(status_code=403, detail="Lisans süresi dolmuş")
    
    # Lisans tipi kontrolü - LOCAL lisanslar web kullanamaz
    license_type = getattr(customer, 'license_type', 'DEMO')
    if license_type == "LOCAL":
        raise HTTPException(
            status_code=403, 
            detail="LOCAL lisans ile web erişimi yapılamaz. ONLINE lisansa yükseltin."
        )
    
    return x_customer_id

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

class MemberCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    tc_no: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: str = "Aktif"

class IncomeCreate(BaseModel):
    date: str
    category: str
    amount: float
    description: Optional[str] = None
    cash_account: str = "Ana Kasa"

class ExpenseCreate(BaseModel):
    date: str
    category: str
    amount: float
    description: Optional[str] = None
    vendor: Optional[str] = None
    cash_account: str = "Ana Kasa"

class DuePayment(BaseModel):
    due_id: str
    amount: float

class SettingsUpdate(BaseModel):
    organization_name: Optional[str] = None
    yearly_dues: Optional[float] = None

class TransferCreate(BaseModel):
    from_account: str
    to_account: str
    amount: float
    date: str
    description: Optional[str] = None

class EventCreate(BaseModel):
    title: str
    event_type: str = "Genel"
    description: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    budget: float = 0
    status: str = "Planlanan"

class MeetingCreate(BaseModel):
    title: str
    meeting_date: str
    location: Optional[str] = None
    agenda: Optional[List[str]] = []
    attendees: Optional[List[str]] = []
    decisions: Optional[List[str]] = []
    minutes: Optional[str] = None
    status: str = "Planlanan"

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = "member"
    permissions: Optional[List[str]] = []

class DocumentCreate(BaseModel):
    filename: str
    category: str = "Genel"
    related_to: Optional[str] = None
    related_id: Optional[str] = None

# ==================== ADDITIONAL MODELS ====================

class Transfer(Base):
    __tablename__ = "transfers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    from_account = Column(String(100))
    to_account = Column(String(100))
    amount = Column(Numeric(12, 2))
    date = Column(Date)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    event_type = Column(String(50))
    location = Column(String(255))
    status = Column(String(20), default="Planlanan")
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(Numeric(12, 2), default=0)
    actual_cost = Column(Numeric(12, 2), default=0)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    title = Column(String(255))
    meeting_date = Column(DateTime)
    location = Column(String(255))
    agenda = Column(JSON, default=[])
    minutes = Column(Text)
    attendees = Column(JSON, default=[])
    decisions = Column(JSON, default=[])
    status = Column(String(20), default="Planlanan")
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    filename = Column(String(255))
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    category = Column(String(50))
    related_to = Column(String(50))
    related_id = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== APP ====================

app = FastAPI(
    title="BADER API",
    version="4.1.0",
    description="BADER Dernek & Köy Yönetim Sistemi API + Web App"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(f"{settings.upload_dir}/updates", exist_ok=True)

# ==================== HEALTH ====================

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "4.1.0"}

# ==================== ACTIVATION ====================

@app.post("/activate")
def activate_license(request: ActivateRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(
        (Customer.customer_id == request.license_key) | 
        (Customer.api_key == request.license_key)
    ).first()
    
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
def check_version(current_version: str, platform: str = "all", db: Session = Depends(get_db)):
    latest = db.query(AppVersion).filter(
        AppVersion.is_active == True,
        (AppVersion.platform == platform) | (AppVersion.platform == "all")
    ).order_by(AppVersion.released_at.desc()).first()
    
    if not latest:
        return {"has_update": False, "current_version": current_version, "latest_version": current_version, "message": "Güncel sürümdesiniz"}
    
    def parse_version(v):
        return tuple(map(int, v.replace("v", "").split(".")))
    
    try:
        has_update = parse_version(latest.version) > parse_version(current_version)
    except:
        has_update = latest.version != current_version
    
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
    user = db.query(User).filter(
        User.customer_id == request.customer_id,
        User.username == request.username,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    
    password_valid = False
    try:
        if verify_password(request.password, user.password_hash):
            password_valid = True
    except:
        pass
    
    if not password_valid:
        plain_hash = hashlib.sha256(request.password.encode()).hexdigest()
        if plain_hash == user.password_hash:
            password_valid = True
            user.password_hash = hash_password(request.password)
    
    if not password_valid and user.password_hash == request.password:
        password_valid = True
        user.password_hash = hash_password(request.password)
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Şifre hatalı")
    
    token = create_access_token({"sub": str(user.id), "customer_id": user.customer_id})
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

# ==================== APP MENUS ====================

@app.get("/app/menus")
def get_app_menus(db: Session = Depends(get_db)):
    menus = db.query(DynamicMenu).filter(DynamicMenu.is_active == True).order_by(DynamicMenu.order_index).all()
    return {
        "menus": [
            {
                "id": str(m.id),
                "name": m.name,
                "icon": m.icon,
                "route_key": m.route_key,
                "position": m.position,
                "url": m.url,
                "required_permission": m.required_permission
            }
            for m in menus
        ]
    }

# ==================== WEB API - MEMBERS ====================

@app.get("/web/members")
def web_list_members(customer_id: str = Depends(get_customer_id), status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Member).filter(Member.customer_id == customer_id)
    if status:
        query = query.filter(Member.status == status)
    members = query.order_by(Member.member_no).all()
    
    return {
        "members": [
            {
                "id": str(m.id),
                "member_no": m.member_no,
                "full_name": m.full_name,
                "tc_no": m.tc_no,
                "phone": m.phone,
                "email": m.email,
                "address": m.address,
                "status": m.status,
                "join_date": m.join_date.isoformat() if m.join_date else None,
                "membership_fee": float(m.membership_fee) if m.membership_fee else 100
            }
            for m in members
        ]
    }

@app.post("/web/members")
def web_create_member(data: MemberCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    max_no = db.query(func.max(Member.member_no)).filter(Member.customer_id == customer_id).scalar() or 0
    
    member = Member(
        id=uuid.uuid4(),
        customer_id=customer_id,
        member_no=max_no + 1,
        full_name=data.full_name,
        phone=data.phone,
        tc_no=data.tc_no,
        email=data.email,
        address=data.address,
        status=data.status,
        join_date=date.today()
    )
    db.add(member)
    db.commit()
    
    return {"success": True, "id": str(member.id), "member_no": member.member_no}

@app.put("/web/members/{member_id}")
def web_update_member(member_id: str, data: MemberCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.customer_id == customer_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    member.full_name = data.full_name
    member.phone = data.phone
    member.tc_no = data.tc_no
    member.email = data.email
    member.address = data.address
    member.status = data.status
    db.commit()
    
    return {"success": True}

@app.delete("/web/members/{member_id}")
def web_delete_member(member_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.customer_id == customer_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    member.status = "Pasif"
    member.leave_date = date.today()
    db.commit()
    
    return {"success": True}

# ==================== WEB API - INCOMES ====================

@app.get("/web/incomes")
def web_list_incomes(customer_id: str = Depends(get_customer_id), year: int = 2025, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Income).filter(Income.customer_id == customer_id, Income.fiscal_year == year)
    if category:
        query = query.filter(Income.category == category)
    incomes = query.order_by(Income.date.desc()).all()
    
    return {
        "incomes": [
            {
                "id": str(i.id),
                "date": i.date.isoformat() if i.date else None,
                "category": i.category,
                "amount": float(i.amount) if i.amount else 0,
                "description": i.description,
                "cash_account": i.cash_account,
                "receipt_no": i.receipt_no
            }
            for i in incomes
        ]
    }

@app.post("/web/incomes")
def web_create_income(data: IncomeCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    income_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    
    income = Income(
        id=uuid.uuid4(),
        customer_id=customer_id,
        date=income_date,
        category=data.category,
        amount=data.amount,
        description=data.description,
        cash_account=data.cash_account,
        fiscal_year=income_date.year
    )
    db.add(income)
    db.commit()
    
    return {"success": True, "id": str(income.id)}

@app.put("/web/incomes/{income_id}")
def web_update_income(income_id: str, data: IncomeCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    income = db.query(Income).filter(Income.id == income_id, Income.customer_id == customer_id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Gelir bulunamadı")
    
    income_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    income.date = income_date
    income.category = data.category
    income.amount = data.amount
    income.description = data.description
    income.cash_account = data.cash_account
    income.fiscal_year = income_date.year
    db.commit()
    
    return {"success": True}

@app.delete("/web/incomes/{income_id}")
def web_delete_income(income_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    income = db.query(Income).filter(Income.id == income_id, Income.customer_id == customer_id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Gelir bulunamadı")
    
    db.delete(income)
    db.commit()
    
    return {"success": True}

# ==================== WEB API - EXPENSES ====================

@app.get("/web/expenses")
def web_list_expenses(customer_id: str = Depends(get_customer_id), year: int = 2025, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Expense).filter(Expense.customer_id == customer_id, Expense.fiscal_year == year)
    if category:
        query = query.filter(Expense.category == category)
    expenses = query.order_by(Expense.date.desc()).all()
    
    return {
        "expenses": [
            {
                "id": str(e.id),
                "date": e.date.isoformat() if e.date else None,
                "category": e.category,
                "amount": float(e.amount) if e.amount else 0,
                "description": e.description,
                "vendor": e.vendor,
                "cash_account": e.cash_account,
                "invoice_no": e.invoice_no
            }
            for e in expenses
        ]
    }

@app.post("/web/expenses")
def web_create_expense(data: ExpenseCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    expense_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    
    expense = Expense(
        id=uuid.uuid4(),
        customer_id=customer_id,
        date=expense_date,
        category=data.category,
        amount=data.amount,
        description=data.description,
        vendor=data.vendor,
        cash_account=data.cash_account,
        fiscal_year=expense_date.year
    )
    db.add(expense)
    db.commit()
    
    return {"success": True, "id": str(expense.id)}

@app.put("/web/expenses/{expense_id}")
def web_update_expense(expense_id: str, data: ExpenseCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.customer_id == customer_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    
    expense_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    expense.date = expense_date
    expense.category = data.category
    expense.amount = data.amount
    expense.description = data.description
    expense.vendor = data.vendor
    expense.cash_account = data.cash_account
    expense.fiscal_year = expense_date.year
    db.commit()
    
    return {"success": True}

@app.delete("/web/expenses/{expense_id}")
def web_delete_expense(expense_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.customer_id == customer_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    
    db.delete(expense)
    db.commit()
    
    return {"success": True}

# ==================== WEB API - DUES ====================

@app.get("/web/dues")
def web_list_dues(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    members = db.query(Member).filter(Member.customer_id == customer_id, Member.status == "Aktif").all()
    
    dues_list = []
    total_expected = 0
    total_collected = 0
    
    for member in members:
        due = db.query(Due).filter(Due.customer_id == customer_id, Due.member_id == member.id, Due.year == year).first()
        
        yearly_amount = float(member.membership_fee) if member.membership_fee else 100
        paid_amount = float(due.paid_amount) if due and due.paid_amount else 0
        remaining = yearly_amount - paid_amount
        status = "Tamamlandı" if remaining <= 0 else ("Kısmi" if paid_amount > 0 else "Bekliyor")
        
        dues_list.append({
            "id": str(due.id) if due else str(member.id),
            "member_id": str(member.id),
            "member_name": member.full_name,
            "yearly_amount": yearly_amount,
            "paid_amount": paid_amount,
            "remaining": max(0, remaining),
            "status": status
        })
        
        total_expected += yearly_amount
        total_collected += paid_amount
    
    return {
        "dues": dues_list,
        "stats": {"expected": total_expected, "collected": total_collected, "remaining": total_expected - total_collected}
    }

@app.post("/web/dues/payment")
def web_pay_due(data: DuePayment, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    due = db.query(Due).filter(Due.id == data.due_id, Due.customer_id == customer_id).first()
    
    if not due:
        raise HTTPException(status_code=404, detail="Aidat kaydı bulunamadı")
    
    due.paid_amount = (float(due.paid_amount) if due.paid_amount else 0) + data.amount
    if due.paid_amount >= float(due.yearly_amount):
        due.status = "Tamamlandı"
    else:
        due.status = "Kısmi"
    
    income = Income(
        id=uuid.uuid4(),
        customer_id=customer_id,
        member_id=due.member_id,
        date=date.today(),
        category="AİDAT",
        amount=data.amount,
        description=f"Aidat ödemesi - {due.year}",
        fiscal_year=date.today().year
    )
    db.add(income)
    db.commit()
    
    return {"success": True}

# ==================== WEB API - CASH ACCOUNTS ====================

@app.get("/web/cash-accounts")
def web_list_cash_accounts(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    accounts = db.query(CashAccount).filter(CashAccount.customer_id == customer_id).all()
    
    return {
        "accounts": [
            {"id": str(a.id), "name": a.name, "type": a.account_type, "balance": float(a.balance) if a.balance else 0}
            for a in accounts
        ]
    }

# ==================== WEB API - SETTINGS ====================

@app.get("/web/settings")
def web_get_settings(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    settings_list = db.query(Setting).filter(Setting.customer_id == customer_id).all()
    return {s.key: s.value for s in settings_list}

@app.put("/web/settings")
def web_update_settings(data: SettingsUpdate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    for key, value in data.dict(exclude_none=True).items():
        setting = db.query(Setting).filter(Setting.customer_id == customer_id, Setting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = Setting(id=uuid.uuid4(), customer_id=customer_id, key=key, value=str(value))
            db.add(setting)
    db.commit()
    return {"success": True}

# ==================== ADMIN ENDPOINTS ====================

@app.get("/admin/dashboard")
def admin_dashboard(db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    total_customers = db.query(Customer).filter(Customer.is_active == True).count()
    plan_dist = db.query(Customer.plan, func.count(Customer.id)).filter(Customer.is_active == True).group_by(Customer.plan).all()
    yesterday = datetime.utcnow() - timedelta(hours=24)
    activations_24h = db.query(ActivationLog).filter(ActivationLog.created_at > yesterday).count()
    week_ago = datetime.utcnow() - timedelta(days=7)
    activations_7d = db.query(ActivationLog).filter(ActivationLog.created_at > week_ago).count()
    latest_version = db.query(AppVersion).filter(AppVersion.is_active == True).order_by(AppVersion.released_at.desc()).first()
    
    return {
        "total_customers": total_customers,
        "plan_distribution": {plan: count for plan, count in plan_dist},
        "activations_24h": activations_24h,
        "activations_7d": activations_7d,
        "active_version": latest_version.version if latest_version else "1.0.0"
    }

@app.get("/admin/customers")
def admin_list_customers(db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
    return {
        "customers": [
            {
                "id": str(c.id), "customer_id": c.customer_id, "api_key": c.api_key, "name": c.name,
                "email": c.email, "phone": c.phone, "plan": c.plan, "max_users": c.max_users,
                "max_members": c.max_members, "is_active": c.is_active,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in customers
        ]
    }

@app.post("/admin/customers")
def admin_create_customer(data: CustomerCreate, db: Session = Depends(get_db), admin: bool = Depends(verify_admin)):
    customer_id = f"BADER-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
    api_key = f"bader_api_{secrets.token_hex(16)}"
    
    customer = Customer(
        customer_id=customer_id, api_key=api_key, name=data.name, email=data.email,
        phone=data.phone, address=data.address, plan=data.plan, max_users=data.max_users,
        max_members=data.max_members,
        expires_at=datetime.strptime(data.expires_at, "%Y-%m-%d").date() if data.expires_at else None,
        notes=data.notes
    )
    db.add(customer)
    
    # Default admin user
    admin_user = User(
        id=uuid.uuid4(), customer_id=customer_id, username="admin",
        password_hash=hash_password("admin123"), full_name="Yönetici", role="admin"
    )
    db.add(admin_user)
    db.commit()
    
    return {"success": True, "customer_id": customer_id, "api_key": api_key, "message": f"Müşteri oluşturuldu: {data.name}"}

# ==================== WEB API - TRANSFERS (VIRMAN) ====================

@app.get("/web/transfers")
def web_list_transfers(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    from sqlalchemy import extract
    query = db.query(Transfer).filter(Transfer.customer_id == customer_id)
    if year:
        query = query.filter(extract('year', Transfer.date) == year)
    transfers = query.order_by(Transfer.date.desc()).all()
    
    return {
        "transfers": [
            {
                "id": str(t.id),
                "from_account": t.from_account,
                "to_account": t.to_account,
                "amount": float(t.amount) if t.amount else 0,
                "date": t.date.isoformat() if t.date else None,
                "description": t.description
            }
            for t in transfers
        ]
    }

@app.post("/web/transfers")
def web_create_transfer(data: TransferCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    transfer_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    
    transfer = Transfer(
        id=uuid.uuid4(),
        customer_id=customer_id,
        from_account=data.from_account,
        to_account=data.to_account,
        amount=data.amount,
        date=transfer_date,
        description=data.description
    )
    db.add(transfer)
    
    # Update cash account balances
    from_acc = db.query(CashAccount).filter(CashAccount.customer_id == customer_id, CashAccount.name == data.from_account).first()
    to_acc = db.query(CashAccount).filter(CashAccount.customer_id == customer_id, CashAccount.name == data.to_account).first()
    
    if from_acc:
        from_acc.balance = float(from_acc.balance or 0) - data.amount
    if to_acc:
        to_acc.balance = float(to_acc.balance or 0) + data.amount
    
    db.commit()
    return {"success": True, "id": str(transfer.id)}

@app.delete("/web/transfers/{transfer_id}")
def web_delete_transfer(transfer_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id, Transfer.customer_id == customer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Virman bulunamadı")
    
    # Reverse balances
    from_acc = db.query(CashAccount).filter(CashAccount.customer_id == customer_id, CashAccount.name == transfer.from_account).first()
    to_acc = db.query(CashAccount).filter(CashAccount.customer_id == customer_id, CashAccount.name == transfer.to_account).first()
    
    if from_acc:
        from_acc.balance = float(from_acc.balance or 0) + float(transfer.amount or 0)
    if to_acc:
        to_acc.balance = float(to_acc.balance or 0) - float(transfer.amount or 0)
    
    db.delete(transfer)
    db.commit()
    return {"success": True}

# ==================== WEB API - EVENTS ====================

@app.get("/web/events")
def web_list_events(customer_id: str = Depends(get_customer_id), status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Event).filter(Event.customer_id == customer_id)
    if status:
        query = query.filter(Event.status == status)
    events = query.order_by(Event.start_date.desc()).all()
    
    return {
        "events": [
            {
                "id": str(e.id),
                "title": e.title,
                "event_type": e.event_type,
                "description": e.description,
                "location": e.location,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "budget": float(e.budget) if e.budget else 0,
                "actual_cost": float(e.actual_cost) if e.actual_cost else 0,
                "status": e.status
            }
            for e in events
        ]
    }

@app.post("/web/events")
def web_create_event(data: EventCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    event = Event(
        id=uuid.uuid4(),
        customer_id=customer_id,
        title=data.title,
        event_type=data.event_type,
        description=data.description,
        location=data.location,
        start_date=datetime.strptime(data.start_date, "%Y-%m-%d").date(),
        end_date=datetime.strptime(data.end_date, "%Y-%m-%d").date() if data.end_date else None,
        budget=data.budget,
        status=data.status
    )
    db.add(event)
    db.commit()
    return {"success": True, "id": str(event.id)}

@app.put("/web/events/{event_id}")
def web_update_event(event_id: str, data: EventCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.customer_id == customer_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    
    event.title = data.title
    event.event_type = data.event_type
    event.description = data.description
    event.location = data.location
    event.start_date = datetime.strptime(data.start_date, "%Y-%m-%d").date()
    event.end_date = datetime.strptime(data.end_date, "%Y-%m-%d").date() if data.end_date else None
    event.budget = data.budget
    event.status = data.status
    db.commit()
    return {"success": True}

@app.delete("/web/events/{event_id}")
def web_delete_event(event_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.customer_id == customer_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    db.delete(event)
    db.commit()
    return {"success": True}

# ==================== WEB API - MEETINGS ====================

@app.get("/web/meetings")
def web_list_meetings(customer_id: str = Depends(get_customer_id), status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Meeting).filter(Meeting.customer_id == customer_id)
    if status:
        query = query.filter(Meeting.status == status)
    meetings = query.order_by(Meeting.meeting_date.desc()).all()
    
    return {
        "meetings": [
            {
                "id": str(m.id),
                "title": m.title,
                "meeting_date": m.meeting_date.isoformat() if m.meeting_date else None,
                "location": m.location,
                "agenda": m.agenda or [],
                "attendees": m.attendees or [],
                "decisions": m.decisions or [],
                "minutes": m.minutes,
                "status": m.status
            }
            for m in meetings
        ]
    }

@app.post("/web/meetings")
def web_create_meeting(data: MeetingCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    meeting = Meeting(
        id=uuid.uuid4(),
        customer_id=customer_id,
        title=data.title,
        meeting_date=datetime.strptime(data.meeting_date, "%Y-%m-%dT%H:%M") if 'T' in data.meeting_date else datetime.strptime(data.meeting_date, "%Y-%m-%d"),
        location=data.location,
        agenda=data.agenda,
        attendees=data.attendees,
        decisions=data.decisions,
        minutes=data.minutes,
        status=data.status
    )
    db.add(meeting)
    db.commit()
    return {"success": True, "id": str(meeting.id)}

@app.put("/web/meetings/{meeting_id}")
def web_update_meeting(meeting_id: str, data: MeetingCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id, Meeting.customer_id == customer_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Toplantı bulunamadı")
    
    meeting.title = data.title
    meeting.meeting_date = datetime.strptime(data.meeting_date, "%Y-%m-%dT%H:%M") if 'T' in data.meeting_date else datetime.strptime(data.meeting_date, "%Y-%m-%d")
    meeting.location = data.location
    meeting.agenda = data.agenda
    meeting.attendees = data.attendees
    meeting.decisions = data.decisions
    meeting.minutes = data.minutes
    meeting.status = data.status
    db.commit()
    return {"success": True}

@app.delete("/web/meetings/{meeting_id}")
def web_delete_meeting(meeting_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id, Meeting.customer_id == customer_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Toplantı bulunamadı")
    db.delete(meeting)
    db.commit()
    return {"success": True}

# ==================== WEB API - USERS ====================

@app.get("/web/users")
def web_list_users(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.customer_id == customer_id).order_by(User.created_at).all()
    
    return {
        "users": [
            {
                "id": str(u.id),
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "role": u.role,
                "permissions": u.permissions or [],
                "is_active": u.is_active,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
            }
            for u in users
        ]
    }

@app.post("/web/users")
def web_create_user(data: UserCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    # Check if username exists
    existing = db.query(User).filter(User.customer_id == customer_id, User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanılıyor")
    
    user = User(
        id=uuid.uuid4(),
        customer_id=customer_id,
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        role=data.role,
        permissions=data.permissions
    )
    db.add(user)
    db.commit()
    return {"success": True, "id": str(user.id)}

@app.put("/web/users/{user_id}")
def web_update_user(user_id: str, data: UserCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.customer_id == customer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    user.full_name = data.full_name
    user.email = data.email
    user.phone = data.phone
    user.role = data.role
    user.permissions = data.permissions
    if data.password:
        user.password_hash = hash_password(data.password)
    db.commit()
    return {"success": True}

@app.delete("/web/users/{user_id}")
def web_delete_user(user_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.customer_id == customer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    user.is_active = False
    db.commit()
    return {"success": True}

# ==================== WEB API - INACTIVE MEMBERS ====================

@app.get("/web/members/inactive")
def web_list_inactive_members(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    members = db.query(Member).filter(Member.customer_id == customer_id, Member.status == "Pasif").order_by(Member.leave_date.desc()).all()
    
    return {
        "members": [
            {
                "id": str(m.id),
                "member_no": m.member_no,
                "full_name": m.full_name,
                "phone": m.phone,
                "join_date": m.join_date.isoformat() if m.join_date else None,
                "leave_date": m.leave_date.isoformat() if m.leave_date else None,
                "notes": m.notes
            }
            for m in members
        ]
    }

@app.post("/web/members/{member_id}/leave")
def web_leave_member(member_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.customer_id == customer_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    member.status = "Pasif"
    member.leave_date = date.today()
    db.commit()
    return {"success": True}

@app.post("/web/members/{member_id}/activate")
def web_activate_member(member_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.customer_id == customer_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    member.status = "Aktif"
    member.leave_date = None
    db.commit()
    return {"success": True}

# ==================== WEB API - MEMBER DETAIL ====================

@app.get("/web/members/{member_id}/detail")
def web_member_detail(member_id: str, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id, Member.customer_id == customer_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    # Get member's incomes
    incomes = db.query(Income).filter(Income.customer_id == customer_id, Income.member_id == member.id).order_by(Income.date.desc()).limit(10).all()
    
    # Get member's dues across years
    dues = db.query(Due).filter(Due.customer_id == customer_id, Due.member_id == member.id).order_by(Due.year.desc()).all()
    
    return {
        "member": {
            "id": str(member.id),
            "member_no": member.member_no,
            "full_name": member.full_name,
            "tc_no": member.tc_no,
            "phone": member.phone,
            "email": member.email,
            "address": member.address,
            "birth_date": member.birth_date.isoformat() if member.birth_date else None,
            "join_date": member.join_date.isoformat() if member.join_date else None,
            "leave_date": member.leave_date.isoformat() if member.leave_date else None,
            "status": member.status,
            "membership_fee": float(member.membership_fee) if member.membership_fee else 100
        },
        "incomes": [
            {"id": str(i.id), "date": i.date.isoformat() if i.date else None, "category": i.category, "amount": float(i.amount) if i.amount else 0}
            for i in incomes
        ],
        "dues": [
            {"year": d.year, "yearly_amount": float(d.yearly_amount) if d.yearly_amount else 100, "paid_amount": float(d.paid_amount) if d.paid_amount else 0, "status": d.status}
            for d in dues
        ]
    }

# ==================== WEB API - REPORTS ====================

@app.get("/web/reports/summary")
def web_report_summary(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    total_income = db.query(func.sum(Income.amount)).filter(Income.customer_id == customer_id, Income.fiscal_year == year).scalar() or 0
    total_expense = db.query(func.sum(Expense.amount)).filter(Expense.customer_id == customer_id, Expense.fiscal_year == year).scalar() or 0
    total_members = db.query(Member).filter(Member.customer_id == customer_id, Member.status == "Aktif").count()
    
    return {
        "year": year,
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "net": float(total_income) - float(total_expense),
        "total_members": total_members
    }

@app.get("/web/reports/monthly")
def web_report_monthly(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    from sqlalchemy import extract
    
    months = []
    for month in range(1, 13):
        income = db.query(func.sum(Income.amount)).filter(
            Income.customer_id == customer_id,
            Income.fiscal_year == year,
            extract('month', Income.date) == month
        ).scalar() or 0
        
        expense = db.query(func.sum(Expense.amount)).filter(
            Expense.customer_id == customer_id,
            Expense.fiscal_year == year,
            extract('month', Expense.date) == month
        ).scalar() or 0
        
        months.append({
            "month": month,
            "month_name": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][month-1],
            "income": float(income),
            "expense": float(expense),
            "net": float(income) - float(expense)
        })
    
    return {"year": year, "months": months}

@app.get("/web/reports/category")
def web_report_category(customer_id: str = Depends(get_customer_id), year: int = 2025, type: str = "income", db: Session = Depends(get_db)):
    if type == "income":
        data = db.query(Income.category, func.sum(Income.amount).label('total')).filter(
            Income.customer_id == customer_id,
            Income.fiscal_year == year
        ).group_by(Income.category).all()
    else:
        data = db.query(Expense.category, func.sum(Expense.amount).label('total')).filter(
            Expense.customer_id == customer_id,
            Expense.fiscal_year == year
        ).group_by(Expense.category).all()
    
    return {
        "type": type,
        "year": year,
        "categories": [{"category": cat or "Diğer", "total": float(total)} for cat, total in data]
    }

@app.get("/web/reports/dues")
def web_report_dues(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    members = db.query(Member).filter(Member.customer_id == customer_id, Member.status == "Aktif").all()
    
    stats = {"total_expected": 0, "total_collected": 0, "fully_paid": 0, "partial": 0, "unpaid": 0}
    members_data = []
    
    for member in members:
        due = db.query(Due).filter(Due.customer_id == customer_id, Due.member_id == member.id, Due.year == year).first()
        yearly = float(member.membership_fee) if member.membership_fee else 100
        paid = float(due.paid_amount) if due and due.paid_amount else 0
        
        stats["total_expected"] += yearly
        stats["total_collected"] += paid
        
        if paid >= yearly:
            stats["fully_paid"] += 1
            status = "Tamamlandı"
        elif paid > 0:
            stats["partial"] += 1
            status = "Kısmi"
        else:
            stats["unpaid"] += 1
            status = "Bekliyor"
        
        members_data.append({
            "member_no": member.member_no,
            "full_name": member.full_name,
            "yearly_amount": yearly,
            "paid_amount": paid,
            "remaining": yearly - paid,
            "status": status
        })
    
    return {"year": year, "stats": stats, "members": members_data}

# ==================== WEB API - EXPORT ====================

@app.get("/web/export/members")
def web_export_members(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    members = db.query(Member).filter(Member.customer_id == customer_id).order_by(Member.member_no).all()
    
    return {
        "filename": f"uyeler_{datetime.now().strftime('%Y%m%d')}.csv",
        "data": [
            {
                "Üye No": m.member_no,
                "Ad Soyad": m.full_name,
                "TC Kimlik": m.tc_no,
                "Telefon": m.phone,
                "E-posta": m.email,
                "Adres": m.address,
                "Durum": m.status,
                "Üyelik Tarihi": m.join_date.isoformat() if m.join_date else ""
            }
            for m in members
        ]
    }

@app.get("/web/export/incomes")
def web_export_incomes(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    incomes = db.query(Income).filter(Income.customer_id == customer_id, Income.fiscal_year == year).order_by(Income.date).all()
    
    return {
        "filename": f"gelirler_{year}_{datetime.now().strftime('%Y%m%d')}.csv",
        "data": [
            {
                "Tarih": i.date.isoformat() if i.date else "",
                "Kategori": i.category,
                "Tutar": float(i.amount) if i.amount else 0,
                "Açıklama": i.description,
                "Kasa": i.cash_account
            }
            for i in incomes
        ]
    }

@app.get("/web/export/expenses")
def web_export_expenses(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    expenses = db.query(Expense).filter(Expense.customer_id == customer_id, Expense.fiscal_year == year).order_by(Expense.date).all()
    
    return {
        "filename": f"giderler_{year}_{datetime.now().strftime('%Y%m%d')}.csv",
        "data": [
            {
                "Tarih": e.date.isoformat() if e.date else "",
                "Kategori": e.category,
                "Tutar": float(e.amount) if e.amount else 0,
                "Açıklama": e.description,
                "Firma": e.vendor,
                "Kasa": e.cash_account
            }
            for e in expenses
        ]
    }


# ==================== BUDGET ENDPOINTS ====================

class BudgetItemCreate(BaseModel):
    year: int = 2025
    category: str
    type: str = "expense"  # income / expense
    planned_amount: float
    notes: str = ""

@app.get("/web/budget")
def web_get_budget(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    # Simplified budget - just return income/expense summaries by category
    incomes = db.query(Income.category, func.sum(Income.amount).label('total')).filter(
        Income.customer_id == customer_id, Income.fiscal_year == year
    ).group_by(Income.category).all()
    
    expenses = db.query(Expense.category, func.sum(Expense.amount).label('total')).filter(
        Expense.customer_id == customer_id, Expense.fiscal_year == year
    ).group_by(Expense.category).all()
    
    return {
        "year": year,
        "items": [
            {"category": i[0], "type": "income", "actual_amount": float(i[1] or 0), "planned_amount": 0}
            for i in incomes
        ] + [
            {"category": e[0], "type": "expense", "actual_amount": float(e[1] or 0), "planned_amount": 0}
            for e in expenses
        ]
    }


# ==================== DOCUMENT ENDPOINTS ====================

@app.get("/web/documents")
def web_get_documents(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    # List files from upload directory
    upload_path = f"{settings.upload_dir}/{customer_id}"
    documents = []
    if os.path.exists(upload_path):
        for filename in os.listdir(upload_path):
            file_path = os.path.join(upload_path, filename)
            stat = os.stat(file_path)
            documents.append({
                "id": hashlib.md5(filename.encode()).hexdigest()[:8],
                "filename": filename,
                "size": stat.st_size,
                "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "category": "Genel"
            })
    return {"documents": documents}

@app.post("/web/documents/upload")
async def web_upload_document(
    file: UploadFile = File(...),
    category: str = "Genel",
    customer_id: str = Depends(get_customer_id)
):
    upload_path = f"{settings.upload_dir}/{customer_id}"
    os.makedirs(upload_path, exist_ok=True)
    
    safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(upload_path, safe_filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {"success": True, "filename": safe_filename, "size": len(content)}

@app.delete("/web/documents/{doc_id}")
def web_delete_document(doc_id: str, customer_id: str = Depends(get_customer_id)):
    upload_path = f"{settings.upload_dir}/{customer_id}"
    if os.path.exists(upload_path):
        for filename in os.listdir(upload_path):
            if hashlib.md5(filename.encode()).hexdigest()[:8] == doc_id:
                os.remove(os.path.join(upload_path, filename))
                return {"success": True}
    raise HTTPException(status_code=404, detail="Document not found")


# ==================== OCR ENDPOINTS ====================

@app.post("/web/ocr/scan")
async def web_ocr_scan(
    file: UploadFile = File(...),
    customer_id: str = Depends(get_customer_id)
):
    # Simple OCR simulation - in production use actual OCR service
    content = await file.read()
    
    # Return mock OCR result for demo
    return {
        "success": True,
        "date": date.today().isoformat(),
        "amount": 0,
        "category": "DİĞER",
        "vendor": "",
        "description": f"OCR Tarama: {file.filename}",
        "raw_text": "OCR özelliği için sunucu tarafında tesseract veya cloud OCR servisi gerekli."
    }


# ==================== DEVIR ENDPOINTS ====================

@app.get("/web/devir/calculate")
def web_calculate_devir(customer_id: str = Depends(get_customer_id), year: int = 2024, db: Session = Depends(get_db)):
    total_income = db.query(func.sum(Income.amount)).filter(
        Income.customer_id == customer_id, Income.fiscal_year == year
    ).scalar() or 0
    
    total_expense = db.query(func.sum(Expense.amount)).filter(
        Expense.customer_id == customer_id, Expense.fiscal_year == year
    ).scalar() or 0
    
    previous_balance = float(total_income) - float(total_expense)
    
    return {
        "year": year,
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "previous_balance": previous_balance,
        "current_year": year + 1
    }

@app.post("/web/devir")
def web_create_devir(
    data: dict,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(get_db)
):
    # Create income record for next year as carryover
    year = data.get("year", 2024)
    amount = data.get("amount", 0)
    
    devir_income = Income(
        customer_id=customer_id,
        fiscal_year=year + 1,
        date=date(year + 1, 1, 1),
        amount=amount,
        category="DEVİR",
        description=f"{year} yılından devir",
        payer="Önceki Yıl Devri",
        cash_account="Ana Kasa"
    )
    db.add(devir_income)
    db.commit()
    
    return {"success": True, "message": f"{year} yılı devri oluşturuldu", "amount": amount}


# ==================== VILLAGE (KÖY) ENDPOINTS ====================

# Village has separate accounts - using fiscal_year = 0 to mark village transactions

@app.get("/web/village/incomes")
def web_get_village_incomes(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    # Village incomes - filter by cash_account containing 'Köy'
    incomes = db.query(Income).filter(
        Income.customer_id == customer_id,
        Income.fiscal_year == year,
        Income.cash_account.ilike('%köy%')
    ).order_by(Income.date.desc()).all()
    
    return {
        "incomes": [
            {
                "id": str(i.id),
                "date": i.date.isoformat() if i.date else "",
                "amount": float(i.amount) if i.amount else 0,
                "category": i.category,
                "description": i.description,
                "payer": i.payer,
                "cash_account": i.cash_account
            }
            for i in incomes
        ]
    }

@app.post("/web/village/incomes")
def web_create_village_income(income: IncomeCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    new_income = Income(
        customer_id=customer_id,
        fiscal_year=2025,
        date=income.date,
        amount=income.amount,
        category=income.category,
        description=income.description,
        payer=income.payer,
        cash_account=income.cash_account or "Köy Kasası"
    )
    db.add(new_income)
    db.commit()
    return {"success": True, "id": str(new_income.id)}

@app.get("/web/village/expenses")
def web_get_village_expenses(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    expenses = db.query(Expense).filter(
        Expense.customer_id == customer_id,
        Expense.fiscal_year == year,
        Expense.cash_account.ilike('%köy%')
    ).order_by(Expense.date.desc()).all()
    
    return {
        "expenses": [
            {
                "id": str(e.id),
                "date": e.date.isoformat() if e.date else "",
                "amount": float(e.amount) if e.amount else 0,
                "category": e.category,
                "description": e.description,
                "vendor": e.vendor,
                "cash_account": e.cash_account
            }
            for e in expenses
        ]
    }

@app.post("/web/village/expenses")
def web_create_village_expense(expense: ExpenseCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    new_expense = Expense(
        customer_id=customer_id,
        fiscal_year=2025,
        date=expense.date,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        vendor=expense.vendor,
        cash_account=expense.cash_account or "Köy Kasası"
    )
    db.add(new_expense)
    db.commit()
    return {"success": True, "id": str(new_expense.id)}

@app.get("/web/village/cash-accounts")
def web_get_village_cash_accounts(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    # Return village cash accounts with balances
    village_incomes = db.query(func.sum(Income.amount)).filter(
        Income.customer_id == customer_id,
        Income.cash_account.ilike('%köy%')
    ).scalar() or 0
    
    village_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.customer_id == customer_id,
        Expense.cash_account.ilike('%köy%')
    ).scalar() or 0
    
    return {
        "accounts": [
            {
                "name": "Köy Kasası",
                "balance": float(village_incomes) - float(village_expenses),
                "type": "cash"
            }
        ]
    }

@app.get("/web/village/transfers")
def web_get_village_transfers(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    transfers = db.query(Transfer).filter(
        Transfer.customer_id == customer_id,
        (Transfer.from_account.ilike('%köy%') | Transfer.to_account.ilike('%köy%'))
    ).order_by(Transfer.date.desc()).all()
    
    return {
        "transfers": [
            {
                "id": str(t.id),
                "date": t.date.isoformat() if t.date else "",
                "from_account": t.from_account,
                "to_account": t.to_account,
                "amount": float(t.amount) if t.amount else 0,
                "description": t.description
            }
            for t in transfers
        ]
    }

@app.post("/web/village/transfers")
def web_create_village_transfer(transfer: TransferCreate, customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    new_transfer = Transfer(
        customer_id=customer_id,
        date=transfer.date,
        from_account=transfer.from_account,
        to_account=transfer.to_account,
        amount=transfer.amount,
        description=transfer.description
    )
    db.add(new_transfer)
    db.commit()
    return {"success": True, "id": str(new_transfer.id)}

# ==================== WEB API - TAHAKKUK REPORT ====================

@app.get("/web/reports/tahakkuk")
def web_report_tahakkuk(customer_id: str = Depends(get_customer_id), year: int = 2025, db: Session = Depends(get_db)):
    members = db.query(Member).filter(Member.customer_id == customer_id, Member.status == "Aktif").order_by(Member.member_no).all()
    
    tahakkuk_list = []
    total_tahakkuk = 0
    total_tahsilat = 0
    
    for member in members:
        due = db.query(Due).filter(Due.customer_id == customer_id, Due.member_id == member.id, Due.year == year).first()
        yearly = float(member.membership_fee) if member.membership_fee else 100
        paid = float(due.paid_amount) if due and due.paid_amount else 0
        
        total_tahakkuk += yearly
        total_tahsilat += paid
        
        tahakkuk_list.append({
            "member_no": member.member_no,
            "full_name": member.full_name,
            "phone": member.phone,
            "tahakkuk": yearly,
            "tahsilat": paid,
            "bakiye": yearly - paid,
            "durum": "Ödendi" if paid >= yearly else ("Kısmi" if paid > 0 else "Ödenmedi")
        })
    
    return {
        "year": year,
        "summary": {
            "total_tahakkuk": total_tahakkuk,
            "total_tahsilat": total_tahsilat,
            "total_alacak": total_tahakkuk - total_tahsilat,
            "member_count": len(members),
            "paid_count": len([m for m in tahakkuk_list if m["durum"] == "Ödendi"]),
            "partial_count": len([m for m in tahakkuk_list if m["durum"] == "Kısmi"]),
            "unpaid_count": len([m for m in tahakkuk_list if m["durum"] == "Ödenmedi"])
        },
        "members": tahakkuk_list
    }

# ==================== WEB API - DEVIR (CARRYOVER) ====================

@app.get("/web/carryover")
def web_list_carryover(customer_id: str = Depends(get_customer_id), db: Session = Depends(get_db)):
    # Get all years with data
    years = db.query(Income.fiscal_year).filter(Income.customer_id == customer_id).distinct().all()
    years = sorted([y[0] for y in years if y[0]], reverse=True)
    
    carryovers = []
    for year in years:
        income = db.query(func.sum(Income.amount)).filter(Income.customer_id == customer_id, Income.fiscal_year == year).scalar() or 0
        expense = db.query(func.sum(Expense.amount)).filter(Expense.customer_id == customer_id, Expense.fiscal_year == year).scalar() or 0
        
        carryovers.append({
            "year": year,
            "total_income": float(income),
            "total_expense": float(expense),
            "balance": float(income) - float(expense)
        })
    
    return {"carryovers": carryovers}

@app.get("/web/carryover/calculate")
def web_calculate_carryover(customer_id: str = Depends(get_customer_id), year: int = 2024, db: Session = Depends(get_db)):
    income = db.query(func.sum(Income.amount)).filter(Income.customer_id == customer_id, Income.fiscal_year == year).scalar() or 0
    expense = db.query(func.sum(Expense.amount)).filter(Expense.customer_id == customer_id, Expense.fiscal_year == year).scalar() or 0
    balance = float(income) - float(expense)
    
    return {
        "year": year,
        "next_year": year + 1,
        "total_income": float(income),
        "total_expense": float(expense),
        "carryover_amount": balance
    }

@app.post("/web/carryover/create")
def web_create_carryover(customer_id: str = Depends(get_customer_id), from_year: int = 2024, db: Session = Depends(get_db)):
    # Calculate balance from previous year
    income = db.query(func.sum(Income.amount)).filter(Income.customer_id == customer_id, Income.fiscal_year == from_year).scalar() or 0
    expense = db.query(func.sum(Expense.amount)).filter(Expense.customer_id == customer_id, Expense.fiscal_year == from_year).scalar() or 0
    balance = float(income) - float(expense)
    
    if balance <= 0:
        return {"success": False, "message": "Devredilebilecek bakiye yok"}
    
    # Create carryover income in new year
    carryover = Income(
        id=uuid.uuid4(),
        customer_id=customer_id,
        date=date(from_year + 1, 1, 1),
        category="DEVİR",
        amount=balance,
        description=f"{from_year} yılı devir bakiyesi",
        cash_account="Ana Kasa",
        fiscal_year=from_year + 1
    )
    db.add(carryover)
    db.commit()
    
    return {"success": True, "amount": balance, "message": f"₺{balance:,.0f} tutarında devir oluşturuldu"}


# ==================== SUPER ADMIN API ====================
# Süper Admin paneli için endpoint'ler

import bcrypt

class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    role = Column(String(20), default="admin")  # superadmin, admin, viewer
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class LicenseLog(Base):
    __tablename__ = "license_logs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), index=True)
    action = Column(String(50))  # ACTIVATE, DEACTIVATE, LOGIN, SYNC, UPDATE, VERIFY
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)


class AppVersion(Base):
    __tablename__ = "app_versions"
    __table_args__ = {'extend_existing': True}
    
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


# Admin tabloları oluştur
Base.metadata.create_all(bind=engine)

# Varsayılan super admin oluştur
def ensure_superadmin():
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == "superadmin").first()
        if not admin:
            hashed = bcrypt.hashpw("Bader2025!".encode(), bcrypt.gensalt()).decode()
            admin = AdminUser(
                username="superadmin",
                password_hash=hashed,
                full_name="Süper Admin",
                email="admin@bader.com.tr",
                role="superadmin"
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

try:
    ensure_superadmin()
except:
    pass

# Admin auth helpers
def verify_password_admin(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_admin_jwt(admin_id: int, username: str, role: str) -> str:
    payload = {
        "admin_id": admin_id,
        "username": username,
        "role": role,
        "type": "admin",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def verify_admin_jwt(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Admin token gerekli")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "admin":
            raise HTTPException(status_code=401, detail="Geçersiz admin token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token doğrulanamadı")

def generate_license_key(license_type: str) -> str:
    """Benzersiz lisans kodu oluştur"""
    year = datetime.now().year
    unique_id = secrets.token_hex(4).upper()
    return f"BADER-{license_type}-{year}-{unique_id}"

# ==================== ADMIN AUTH ====================

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@app.post("/admin/api/auth/login")
def admin_login(data: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == data.username, AdminUser.is_active == True).first()
    if not admin or not verify_password_admin(data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre")
    
    admin.last_login = datetime.utcnow()
    db.commit()
    
    token = create_admin_jwt(admin.id, admin.username, admin.role)
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

@app.get("/admin/api/auth/me")
def admin_me(admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
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

# ==================== ADMIN DASHBOARD ====================

@app.get("/admin/api/dashboard")
def admin_dashboard(admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    total_customers = db.query(Customer).count()
    active_licenses = db.query(Customer).filter(Customer.license_status == "ACTIVE").count()
    demo_licenses = db.query(Customer).filter(Customer.license_type == "DEMO").count()
    expired_licenses = db.query(Customer).filter(Customer.license_status == "EXPIRED").count()
    
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
            "monthly_revenue": 0,
            "active_last_week": 0,
            "expiring_soon": 0
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

# ==================== ADMIN CUSTOMERS ====================

@app.get("/admin/api/customers")
def admin_list_customers(
    admin: dict = Depends(verify_admin_jwt),
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
            (Customer.name.ilike(search_pattern)) |
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
                "organization_name": c.name,
                "contact_name": c.name,
                "contact_email": c.email,
                "contact_phone": c.phone,
                "license_type": c.license_type,
                "license_status": c.license_status,
                "license_end": c.expires_at.isoformat() if c.expires_at else None,
                "max_users": c.max_users,
                "max_members": c.max_members,
                "last_seen": c.last_seen_at.isoformat() if c.last_seen_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None
            } for c in customers
        ]
    }

@app.get("/admin/api/customers/{customer_id}")
def admin_get_customer(customer_id: str, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # Son loglar
    logs = db.query(LicenseLog).filter(LicenseLog.customer_id == customer_id).order_by(LicenseLog.created_at.desc()).limit(50).all()
    
    return {
        "customer": {
            "id": str(customer.id),
            "customer_id": customer.customer_id,
            "organization_name": customer.name,
            "contact_name": customer.name,
            "contact_email": customer.email,
            "contact_phone": customer.phone,
            "address": customer.address,
            "license_type": customer.license_type,
            "license_status": customer.license_status,
            "license_end": customer.expires_at.isoformat() if customer.expires_at else None,
            "max_users": customer.max_users,
            "max_members": customer.max_members,
            "features": customer.features,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "last_seen": customer.last_seen_at.isoformat() if customer.last_seen_at else None,
            "notes": customer.notes
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

class CustomerCreateRequest(BaseModel):
    organization_name: str
    contact_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    license_type: str = "DEMO"
    license_days: int = 365
    max_users: int = 5
    max_members: int = 500
    notes: Optional[str] = None

@app.post("/admin/api/customers")
def admin_create_customer(data: CustomerCreateRequest, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    customer_id = generate_license_key(data.license_type)
    api_key = secrets.token_urlsafe(32)
    
    customer = Customer(
        id=uuid.uuid4(),
        customer_id=customer_id,
        api_key=api_key,
        name=data.organization_name,
        email=data.contact_email,
        phone=data.contact_phone,
        address=data.address,
        license_type=data.license_type,
        license_status="ACTIVE",
        max_users=data.max_users,
        max_members=data.max_members,
        expires_at=date.today() + timedelta(days=data.license_days),
        notes=data.notes
    )
    db.add(customer)
    
    # Varsayılan admin kullanıcı
    admin_user = User(
        id=uuid.uuid4(),
        customer_id=customer_id,
        username="admin",
        password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
        full_name=data.contact_name,
        email=data.contact_email,
        role="admin"
    )
    db.add(admin_user)
    
    # Log
    log = LicenseLog(
        customer_id=customer_id,
        action="CREATE",
        details={"created_by": admin["username"], "license_type": data.license_type}
    )
    db.add(log)
    
    db.commit()
    
    return {
        "success": True,
        "customer": {
            "customer_id": customer_id,
            "api_key": api_key,
            "organization_name": data.organization_name,
            "license_type": data.license_type,
            "expires_at": customer.expires_at.isoformat()
        }
    }

class CustomerUpdateRequest(BaseModel):
    organization_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    license_type: Optional[str] = None
    license_status: Optional[str] = None
    max_users: Optional[int] = None
    max_members: Optional[int] = None
    notes: Optional[str] = None

@app.put("/admin/api/customers/{customer_id}")
def admin_update_customer(customer_id: str, data: CustomerUpdateRequest, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    if data.organization_name:
        customer.name = data.organization_name
    if data.contact_email:
        customer.email = data.contact_email
    if data.contact_phone:
        customer.phone = data.contact_phone
    if data.address:
        customer.address = data.address
    if data.license_type:
        customer.license_type = data.license_type
    if data.license_status:
        customer.license_status = data.license_status
    if data.max_users:
        customer.max_users = data.max_users
    if data.max_members:
        customer.max_members = data.max_members
    if data.notes:
        customer.notes = data.notes
    
    # Log
    log = LicenseLog(customer_id=customer_id, action="UPDATE", details={"updated_by": admin["username"]})
    db.add(log)
    
    db.commit()
    return {"success": True, "message": "Müşteri güncellendi"}

@app.delete("/admin/api/customers/{customer_id}")
def admin_delete_customer(customer_id: str, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    # Log
    log = LicenseLog(customer_id=customer_id, action="DELETE", details={"deleted_by": admin["username"]})
    db.add(log)
    
    db.delete(customer)
    db.commit()
    return {"success": True, "message": "Müşteri silindi"}

# ==================== LICENSE OPERATIONS ====================

@app.post("/admin/api/licenses/{customer_id}/suspend")
def admin_suspend_license(customer_id: str, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    customer.license_status = "SUSPENDED"
    db.add(LicenseLog(customer_id=customer_id, action="SUSPEND", details={"by": admin["username"]}))
    db.commit()
    return {"success": True, "message": "Lisans askıya alındı"}

@app.post("/admin/api/licenses/{customer_id}/activate")
def admin_activate_license(customer_id: str, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    customer.license_status = "ACTIVE"
    db.add(LicenseLog(customer_id=customer_id, action="ACTIVATE", details={"by": admin["username"]}))
    db.commit()
    return {"success": True, "message": "Lisans aktifleştirildi"}

class ExtendLicenseRequest(BaseModel):
    days: int = 365

@app.post("/admin/api/licenses/{customer_id}/extend")
def admin_extend_license(customer_id: str, data: ExtendLicenseRequest, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    if customer.expires_at and customer.expires_at > date.today():
        customer.expires_at = customer.expires_at + timedelta(days=data.days)
    else:
        customer.expires_at = date.today() + timedelta(days=data.days)
    
    db.add(LicenseLog(customer_id=customer_id, action="EXTEND", details={"days": data.days, "by": admin["username"]}))
    db.commit()
    return {"success": True, "new_expires_at": customer.expires_at.isoformat()}

# ==================== VERSION MANAGEMENT ====================

@app.get("/admin/api/versions")
def admin_list_versions(admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    versions = db.query(AppVersion).order_by(AppVersion.created_at.desc()).all()
    return {
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "platform": v.platform,
                "download_url": v.download_url,
                "file_size": v.file_size,
                "checksum": v.checksum,
                "release_notes": v.release_notes,
                "is_mandatory": v.is_mandatory,
                "is_active": v.is_active,
                "created_at": v.created_at.isoformat() if v.created_at else None
            } for v in versions
        ]
    }

class VersionCreateRequest(BaseModel):
    version: str
    platform: str = "all"
    download_url: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    release_notes: Optional[str] = None
    is_mandatory: bool = False

@app.post("/admin/api/versions")
def admin_create_version(data: VersionCreateRequest, admin: dict = Depends(verify_admin_jwt), db: Session = Depends(get_db)):
    version = AppVersion(
        version=data.version,
        platform=data.platform,
        download_url=data.download_url,
        file_size=data.file_size,
        checksum=data.checksum,
        release_notes=data.release_notes,
        is_mandatory=data.is_mandatory,
        is_active=True
    )
    db.add(version)
    db.commit()
    return {"success": True, "version_id": version.id}

# ==================== PUBLIC LICENSE VERIFICATION ====================

class LicenseVerifyRequest(BaseModel):
    customer_id: str
    app_version: Optional[str] = None
    os_info: Optional[str] = None

@app.post("/license/verify")
def verify_license(data: LicenseVerifyRequest, db: Session = Depends(get_db)):
    """Masaüstü uygulama için lisans doğrulama"""
    customer = db.query(Customer).filter(Customer.customer_id == data.customer_id).first()
    
    if not customer:
        return {"valid": False, "error": "Müşteri bulunamadı"}
    
    if customer.license_status == "SUSPENDED":
        return {"valid": False, "error": "Lisans askıya alındı"}
    
    if customer.expires_at and customer.expires_at < date.today():
        customer.license_status = "EXPIRED"
        db.commit()
        return {"valid": False, "error": "Lisans süresi doldu"}
    
    # Son görülme güncelle
    customer.last_seen_at = datetime.utcnow()
    if data.app_version:
        customer.device_info = {"app_version": data.app_version, "os_info": data.os_info}
    
    # Log
    db.add(LicenseLog(customer_id=data.customer_id, action="VERIFY", details={"version": data.app_version}))
    db.commit()
    
    return {
        "valid": True,
        "license": {
            "type": customer.license_type,
            "status": customer.license_status,
            "expires_at": customer.expires_at.isoformat() if customer.expires_at else None,
            "max_users": customer.max_users,
            "max_members": customer.max_members,
            "features": customer.features
        }
    }

@app.get("/version/latest")
def check_version(platform: str = "all", current_version: Optional[str] = None, db: Session = Depends(get_db)):
    """Masaüstü uygulama için versiyon kontrolü"""
    query = db.query(AppVersion).filter(AppVersion.is_active == True)
    if platform != "all":
        query = query.filter((AppVersion.platform == platform) | (AppVersion.platform == "all"))
    
    latest = query.order_by(AppVersion.created_at.desc()).first()
    
    if not latest:
        return {"update_available": False}
    
    return {
        "update_available": latest.version != current_version if current_version else True,
        "latest_version": latest.version,
        "download_url": latest.download_url,
        "is_mandatory": latest.is_mandatory,
        "release_notes": latest.release_notes
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
