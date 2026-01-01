"""
BADER API Server v5.0.0
Desktop ve Web Entegrasyonu için Tam API
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional, List, Any, Dict
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Date, Text, Numeric, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import secrets
import bcrypt
from jose import JWTError, jwt
import os


# ==================== CONFIGURATION ====================

class Settings(BaseSettings):
    database_url: str = "postgresql://bader:bader_secure_2025@localhost:5432/bader"
    secret_key: str = "bader_secret_key_change_in_production"
    admin_secret: str = "BADER_ADMIN_2025_SUPER_SECRET"
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
    plan = Column(String(20), default="basic")
    # LİSANS MODU: 'local' = sadece SQLite, 'internet' = sadece PostgreSQL, 'hybrid' = ikisi birden
    license_mode = Column(String(20), default="local")
    max_users = Column(Integer, default=5)
    max_members = Column(Integer, default=500)
    is_active = Column(Boolean, default=True)
    expires_at = Column(Date)
    features = Column(JSONB, default=["ocr", "sync", "backup"])
    last_seen_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(20), default="member")
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Member(Base):
    __tablename__ = "members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    member_no = Column(String(50))
    full_name = Column(String(255), nullable=False)
    tc_no = Column(String(11))
    phone = Column(String(50))
    phone2 = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    district = Column(String(100))
    birth_date = Column(Date)
    gender = Column(String(20))
    occupation = Column(String(150))
    membership_type = Column(String(30), default='Asil')
    membership_fee = Column(Numeric(10,2), default=0)
    join_date = Column(Date, default=date.today)
    leave_date = Column(Date)
    status = Column(String(20), default='active')
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Income(Base):
    __tablename__ = "incomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"))
    category = Column(String(50), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    receipt_no = Column(String(50))
    cash_account = Column(String(100), default='Ana Kasa')
    fiscal_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    invoice_no = Column(String(50))
    vendor = Column(String(255))
    cash_account = Column(String(100), default='Ana Kasa')
    fiscal_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class CashAccount(Base):
    __tablename__ = "cash_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), default='cash')
    balance = Column(Numeric(12,2), default=0)
    bank_name = Column(String(100))
    iban = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Due(Base):
    __tablename__ = "dues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    paid_amount = Column(Numeric(10,2), default=0)
    paid_date = Column(Date)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    """Bütçe modeli"""
    __tablename__ = "budgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)
    budget_type = Column(String(20), default='expense')  # income/expense
    planned_amount = Column(Numeric(12,2), nullable=False)
    actual_amount = Column(Numeric(12,2), default=0)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    """Belge modeli"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255))
    file_path = Column(Text)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    category = Column(String(100))
    description = Column(Text)
    tags = Column(JSONB, default=[])
    uploaded_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class Meeting(Base):
    """Toplantı modeli"""
    __tablename__ = "meetings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    meeting_type = Column(String(50), default='Yönetim')
    date = Column(Date, nullable=False)
    time = Column(String(10))
    location = Column(String(255))
    agenda = Column(Text)
    minutes = Column(Text)
    decisions = Column(Text)
    attendees = Column(JSONB, default=[])
    status = Column(String(20), default='planned')  # planned, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Event(Base):
    """Etkinlik modeli"""
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    event_type = Column(String(50))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    start_time = Column(String(10))
    end_time = Column(String(10))
    location = Column(String(255))
    description = Column(Text)
    organizer = Column(String(255))
    budget = Column(Numeric(12,2), default=0)
    actual_cost = Column(Numeric(12,2), default=0)
    max_participants = Column(Integer)
    participants = Column(JSONB, default=[])
    status = Column(String(20), default='planned')  # planned, ongoing, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transfer(Base):
    """Virman modeli"""
    __tablename__ = "transfers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    from_account = Column(String(100), nullable=False)
    to_account = Column(String(100), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class FamilyMember(Base):
    """Aile üyesi modeli"""
    __tablename__ = "family_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    relationship = Column(String(50))  # Eş, Çocuk, Anne, Baba, vb.
    birth_date = Column(Date)
    gender = Column(String(20))
    phone = Column(String(50))
    email = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class YearlyCarryover(Base):
    """Yıl devir modeli"""
    __tablename__ = "yearly_carryovers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    from_year = Column(Integer, nullable=False)
    to_year = Column(Integer, nullable=False)
    total_income = Column(Numeric(12,2), default=0)
    total_expense = Column(Numeric(12,2), default=0)
    balance = Column(Numeric(12,2), default=0)
    carried_balance = Column(Numeric(12,2), default=0)
    status = Column(String(20), default='pending')  # pending, completed
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssessmentReport(Base):
    """Tahakkuk raporu modeli"""
    __tablename__ = "assessment_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    report_date = Column(Date, nullable=False)
    total_assessed = Column(Numeric(12,2), default=0)
    total_collected = Column(Numeric(12,2), default=0)
    total_remaining = Column(Numeric(12,2), default=0)
    member_count = Column(Integer, default=0)
    collection_rate = Column(Numeric(5,2), default=0)
    details = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== SCHEMAS ====================

class MemberCreate(BaseModel):
    member_no: Optional[str] = None
    full_name: str
    tc_no: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    membership_type: str = "Asil"
    membership_fee: float = 0
    status: str = "active"
    notes: Optional[str] = None

class MemberResponse(BaseModel):
    id: str
    member_no: Optional[str]
    full_name: str
    tc_no: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    status: str
    membership_type: str
    join_date: Optional[date]
    
    class Config:
        from_attributes = True

class IncomeCreate(BaseModel):
    member_id: Optional[str] = None
    category: str
    amount: float
    date: date
    description: Optional[str] = None
    receipt_no: Optional[str] = None
    cash_account: str = "Ana Kasa"
    fiscal_year: Optional[int] = None

class ExpenseCreate(BaseModel):
    category: str
    amount: float
    date: date
    description: Optional[str] = None
    invoice_no: Optional[str] = None
    vendor: Optional[str] = None
    cash_account: str = "Ana Kasa"
    fiscal_year: Optional[int] = None

class DuePayment(BaseModel):
    year: int
    month: int
    amount: float

class LoginRequest(BaseModel):
    customer_id: str
    username: str
    password: str

class ActivateRequest(BaseModel):
    license_key: str
    device_info: Optional[dict] = None
    # İlk aktivasyonda admin kullanıcısı oluştur
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None
    admin_name: Optional[str] = None


# ==================== AUTH ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith('$2'):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        import hashlib
        if len(hashed_password) == 64:
            return hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == hashed_password
        return plain_password == hashed_password
    except:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_api_key(x_api_key: str = Header(None), authorization: str = Header(None)):
    api_key = x_api_key or (authorization.replace("Bearer ", "") if authorization else None)
    if not api_key:
        raise HTTPException(status_code=401, detail="API key gerekli")
    return api_key

def get_customer_by_api_key(api_key: str, db: Session) -> Customer:
    customer = db.query(Customer).filter(Customer.api_key == api_key).first()
    if not customer:
        raise HTTPException(status_code=401, detail="Geçersiz API key")
    if not customer.is_active:
        raise HTTPException(status_code=401, detail="Hesap devre dışı")
    return customer


# ==================== APP ====================

app = FastAPI(
    title="BADER API",
    version="5.0.0",
    description="BADER Dernek Yönetim Sistemi - Desktop & Web Entegrasyon API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files (Web App ve Admin Panel)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ==================== WEB PAGES ====================

@app.get("/", response_class=HTMLResponse)
def serve_index():
    """Ana sayfa - Web App"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse("<h1>BADER API v5.0.0</h1><p>Web App için /static/index.html dosyası bulunamadı.</p>")

@app.get("/admin", response_class=HTMLResponse)
def serve_admin():
    """Super Admin Panel"""
    admin_path = os.path.join(STATIC_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path, media_type="text/html")
    return HTMLResponse("<h1>Admin Panel</h1><p>/static/admin.html dosyası bulunamadı.</p>")


# ==================== HEALTH & AUTH ====================

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "5.0.0"}

@app.post("/activate")
def activate_license(request: ActivateRequest, db: Session = Depends(get_db)):
    """Desktop uygulama lisans aktivasyonu"""
    customer = db.query(Customer).filter(
        (Customer.customer_id == request.license_key) | 
        (Customer.api_key == request.license_key)
    ).first()
    
    if not customer:
        raise HTTPException(status_code=401, detail="Geçersiz lisans anahtarı")
    if not customer.is_active:
        raise HTTPException(status_code=401, detail="Lisans devre dışı")
    if customer.expires_at and customer.expires_at < date.today():
        raise HTTPException(status_code=401, detail="Lisans süresi dolmuş")
    
    # Eğer admin bilgileri verilmişse ve bu müşterinin kullanıcısı yoksa, oluştur
    if request.admin_username and request.admin_password:
        existing_user = db.query(User).filter(
            User.customer_id == customer.customer_id,
            User.username == request.admin_username
        ).first()
        
        if not existing_user:
            new_user = User(
                customer_id=customer.customer_id,
                username=request.admin_username,
                password_hash=hash_password(request.admin_password),
                full_name=request.admin_name or request.admin_username,
                role="admin"
            )
            db.add(new_user)
    
    customer.last_seen_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "customer_id": customer.customer_id,
        "api_key": customer.api_key,
        "name": customer.name,
        "plan": customer.plan,
        "license_mode": customer.license_mode,
        "expires": customer.expires_at.isoformat() if customer.expires_at else None,
        "features": customer.features
    }

@app.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Kullanıcı girişi"""
    # Önce müşteriyi bul
    customer = db.query(Customer).filter(Customer.customer_id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=401, detail="Geçersiz müşteri kodu")
    if not customer.is_active:
        raise HTTPException(status_code=401, detail="Müşteri hesabı devre dışı")
    if customer.expires_at and customer.expires_at < date.today():
        raise HTTPException(status_code=401, detail="Lisans süresi dolmuş")
    
    # Kullanıcıyı bul
    user = db.query(User).filter(
        User.customer_id == request.customer_id,
        User.username == request.username
    ).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Hesap devre dışı")
    
    user.last_login_at = datetime.utcnow()
    customer.last_seen_at = datetime.utcnow()
    db.commit()
    
    token = create_access_token({
        "sub": str(user.id),
        "customer_id": user.customer_id,
        "username": user.username,
        "role": user.role
    })
    
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "api_key": customer.api_key,
        "license_mode": customer.license_mode,
        "customer": {
            "id": customer.customer_id,
            "name": customer.name,
            "plan": customer.plan,
            "license_mode": customer.license_mode,
            "expires_at": customer.expires_at.isoformat() if customer.expires_at else None,
            "features": customer.features
        },
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }


# ==================== WEB API - MEMBERS ====================

@app.get("/web/members")
def get_members(
    status: str = "active",
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üye listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Member).filter(Member.customer_id == customer.customer_id)
    if status != "all":
        query = query.filter(Member.status == status)
    
    members = query.order_by(Member.full_name).all()
    
    return {
        "members": [
            {
                "id": str(m.id),
                "member_no": m.member_no,
                "full_name": m.full_name,
                "tc_no": m.tc_no,
                "phone": m.phone,
                "email": m.email,
                "status": m.status,
                "membership_type": m.membership_type,
                "join_date": m.join_date.isoformat() if m.join_date else None
            }
            for m in members
        ],
        "count": len(members)
    }

@app.get("/web/members/{member_id}")
def get_member(
    member_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üye detayı"""
    customer = get_customer_by_api_key(api_key, db)
    
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.customer_id == customer.customer_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    return {
        "member": {
            "id": str(member.id),
            "member_no": member.member_no,
            "full_name": member.full_name,
            "tc_no": member.tc_no,
            "phone": member.phone,
            "phone2": member.phone2,
            "email": member.email,
            "address": member.address,
            "city": member.city,
            "district": member.district,
            "birth_date": member.birth_date.isoformat() if member.birth_date else None,
            "gender": member.gender,
            "occupation": member.occupation,
            "membership_type": member.membership_type,
            "membership_fee": float(member.membership_fee) if member.membership_fee else 0,
            "join_date": member.join_date.isoformat() if member.join_date else None,
            "leave_date": member.leave_date.isoformat() if member.leave_date else None,
            "status": member.status,
            "notes": member.notes
        }
    }

@app.post("/web/members")
def create_member(
    data: MemberCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Yeni üye ekle"""
    customer = get_customer_by_api_key(api_key, db)
    
    # Üye limiti kontrolü
    member_count = db.query(Member).filter(Member.customer_id == customer.customer_id).count()
    if member_count >= customer.max_members:
        raise HTTPException(status_code=403, detail=f"Üye limiti aşıldı ({customer.max_members})")
    
    member = Member(
        customer_id=customer.customer_id,
        member_no=data.member_no,
        full_name=data.full_name,
        tc_no=data.tc_no,
        phone=data.phone,
        phone2=data.phone2,
        email=data.email,
        address=data.address,
        city=data.city,
        district=data.district,
        birth_date=data.birth_date,
        gender=data.gender,
        occupation=data.occupation,
        membership_type=data.membership_type,
        membership_fee=data.membership_fee,
        status=data.status,
        notes=data.notes
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return {"success": True, "id": str(member.id), "message": "Üye eklendi"}

@app.put("/web/members/{member_id}")
def update_member(
    member_id: str,
    data: MemberCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üye güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.customer_id == customer.customer_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(member, key, value)
    
    db.commit()
    
    return {"success": True, "message": "Üye güncellendi"}

@app.delete("/web/members/{member_id}")
def delete_member(
    member_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üye sil"""
    customer = get_customer_by_api_key(api_key, db)
    
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.customer_id == customer.customer_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    db.delete(member)
    db.commit()
    
    return {"success": True, "message": "Üye silindi"}


# ==================== WEB API - INCOMES ====================

@app.get("/web/incomes")
def get_incomes(
    year: Optional[int] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gelir listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Income).filter(Income.customer_id == customer.customer_id)
    if year:
        query = query.filter(Income.fiscal_year == year)
    
    incomes = query.order_by(Income.date.desc()).all()
    
    return {
        "incomes": [
            {
                "id": str(i.id),
                "category": i.category,
                "amount": float(i.amount),
                "date": i.date.isoformat(),
                "description": i.description,
                "receipt_no": i.receipt_no,
                "cash_account": i.cash_account,
                "member_id": str(i.member_id) if i.member_id else None
            }
            for i in incomes
        ],
        "count": len(incomes),
        "total": sum(float(i.amount) for i in incomes)
    }

@app.post("/web/incomes")
def create_income(
    data: IncomeCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Yeni gelir ekle"""
    customer = get_customer_by_api_key(api_key, db)
    
    income = Income(
        customer_id=customer.customer_id,
        member_id=data.member_id if data.member_id else None,
        category=data.category,
        amount=data.amount,
        date=data.date,
        description=data.description,
        receipt_no=data.receipt_no,
        cash_account=data.cash_account,
        fiscal_year=data.fiscal_year or data.date.year
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    
    return {"success": True, "id": str(income.id), "message": "Gelir eklendi"}


# ==================== WEB API - EXPENSES ====================

@app.get("/web/expenses")
def get_expenses(
    year: Optional[int] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gider listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Expense).filter(Expense.customer_id == customer.customer_id)
    if year:
        query = query.filter(Expense.fiscal_year == year)
    
    expenses = query.order_by(Expense.date.desc()).all()
    
    return {
        "expenses": [
            {
                "id": str(e.id),
                "category": e.category,
                "amount": float(e.amount),
                "date": e.date.isoformat(),
                "description": e.description,
                "invoice_no": e.invoice_no,
                "vendor": e.vendor,
                "cash_account": e.cash_account
            }
            for e in expenses
        ],
        "count": len(expenses),
        "total": sum(float(e.amount) for e in expenses)
    }

@app.post("/web/expenses")
def create_expense(
    data: ExpenseCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Yeni gider ekle"""
    customer = get_customer_by_api_key(api_key, db)
    
    expense = Expense(
        customer_id=customer.customer_id,
        category=data.category,
        amount=data.amount,
        date=data.date,
        description=data.description,
        invoice_no=data.invoice_no,
        vendor=data.vendor,
        cash_account=data.cash_account,
        fiscal_year=data.fiscal_year or data.date.year
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    return {"success": True, "id": str(expense.id), "message": "Gider eklendi"}


# ==================== WEB API - CASH ACCOUNTS ====================

@app.get("/web/cash-accounts")
def get_cash_accounts(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kasa listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    accounts = db.query(CashAccount).filter(
        CashAccount.customer_id == customer.customer_id,
        CashAccount.is_active == True
    ).all()
    
    return {
        "accounts": [
            {
                "id": str(a.id),
                "name": a.name,
                "type": a.type,
                "balance": float(a.balance) if a.balance else 0,
                "bank_name": a.bank_name,
                "iban": a.iban
            }
            for a in accounts
        ]
    }


# ==================== WEB API - DUES ====================

@app.get("/web/dues")
def get_dues(
    year: Optional[int] = None,
    member_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Aidat listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Due).filter(Due.customer_id == customer.customer_id)
    if year:
        query = query.filter(Due.year == year)
    if member_id:
        query = query.filter(Due.member_id == member_id)
    
    dues = query.order_by(Due.year.desc(), Due.month.desc()).all()
    
    return {
        "dues": [
            {
                "id": str(d.id),
                "member_id": str(d.member_id),
                "year": d.year,
                "month": d.month,
                "amount": float(d.amount),
                "paid_amount": float(d.paid_amount) if d.paid_amount else 0,
                "status": d.status,
                "paid_date": d.paid_date.isoformat() if d.paid_date else None
            }
            for d in dues
        ],
        "count": len(dues)
    }

@app.post("/web/dues/{member_id}/pay")
def pay_due(
    member_id: str,
    payment: DuePayment,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Aidat ödemesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    due = db.query(Due).filter(
        Due.customer_id == customer.customer_id,
        Due.member_id == member_id,
        Due.year == payment.year,
        Due.month == payment.month
    ).first()
    
    if not due:
        raise HTTPException(status_code=404, detail="Aidat kaydı bulunamadı")
    
    due.paid_amount = (due.paid_amount or 0) + payment.amount
    due.paid_date = date.today()
    
    if due.paid_amount >= due.amount:
        due.status = 'paid'
    elif due.paid_amount > 0:
        due.status = 'partial'
    
    db.commit()
    
    return {"success": True, "message": "Ödeme kaydedildi", "status": due.status}


# ==================== WEB API - DASHBOARD ====================

@app.get("/web/dashboard")
def get_dashboard(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Dashboard özet verileri"""
    customer = get_customer_by_api_key(api_key, db)
    cid = customer.customer_id
    
    # İstatistikler
    total_members = db.query(Member).filter(Member.customer_id == cid, Member.status == 'active').count()
    
    current_year = date.today().year
    total_income = db.query(Income).filter(
        Income.customer_id == cid, 
        Income.fiscal_year == current_year
    ).with_entities(func.sum(Income.amount)).scalar() or 0
    
    total_expense = db.query(Expense).filter(
        Expense.customer_id == cid,
        Expense.fiscal_year == current_year
    ).with_entities(func.sum(Expense.amount)).scalar() or 0
    
    pending_dues = db.query(Due).filter(
        Due.customer_id == cid,
        Due.status.in_(['pending', 'partial'])
    ).count()
    
    return {
        "stats": {
            "total_members": total_members,
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "balance": float(total_income - total_expense),
            "pending_dues": pending_dues,
            "year": current_year
        },
        "organization": {
            "name": customer.name,
            "plan": customer.plan,
            "expires_at": customer.expires_at.isoformat() if customer.expires_at else None
        }
    }


# ==================== SYNC API ====================

@app.post("/sync/upload")
def sync_upload(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop'tan sunucuya veri senkronizasyonu"""
    customer = get_customer_by_api_key(api_key, db)
    
    synced = {"members": 0, "incomes": 0, "expenses": 0}
    
    # Üyeler
    for member_data in data.get("members", []):
        existing = db.query(Member).filter(
            Member.customer_id == customer.customer_id,
            Member.member_no == member_data.get("member_no")
        ).first()
        
        if existing:
            for key, value in member_data.items():
                if key not in ["id", "customer_id"]:
                    setattr(existing, key, value)
        else:
            member = Member(customer_id=customer.customer_id, **member_data)
            db.add(member)
        synced["members"] += 1
    
    # Gelirler
    for income_data in data.get("incomes", []):
        income = Income(customer_id=customer.customer_id, **income_data)
        db.add(income)
        synced["incomes"] += 1
    
    # Giderler
    for expense_data in data.get("expenses", []):
        expense = Expense(customer_id=customer.customer_id, **expense_data)
        db.add(expense)
        synced["expenses"] += 1
    
    db.commit()
    
    return {"success": True, "synced": synced}

@app.get("/sync/download")
def sync_download(
    since: Optional[datetime] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Sunucudan desktop'a veri indirme"""
    customer = get_customer_by_api_key(api_key, db)
    cid = customer.customer_id
    
    # Filtre: son güncellemeden sonraki veriler
    members_query = db.query(Member).filter(Member.customer_id == cid)
    incomes_query = db.query(Income).filter(Income.customer_id == cid)
    expenses_query = db.query(Expense).filter(Expense.customer_id == cid)
    
    if since:
        members_query = members_query.filter(Member.updated_at >= since)
        incomes_query = incomes_query.filter(Income.created_at >= since)
        expenses_query = expenses_query.filter(Expense.created_at >= since)
    
    return {
        "members": [
            {
                "id": str(m.id),
                "member_no": m.member_no,
                "full_name": m.full_name,
                "tc_no": m.tc_no,
                "phone": m.phone,
                "email": m.email,
                "status": m.status,
                "membership_type": m.membership_type
            }
            for m in members_query.all()
        ],
        "incomes": [
            {
                "id": str(i.id),
                "category": i.category,
                "amount": float(i.amount),
                "date": i.date.isoformat(),
                "description": i.description
            }
            for i in incomes_query.all()
        ],
        "expenses": [
            {
                "id": str(e.id),
                "category": e.category,
                "amount": float(e.amount),
                "date": e.date.isoformat(),
                "description": e.description
            }
            for e in expenses_query.all()
        ],
        "sync_time": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ==================== DB API - DESKTOP İÇİN TAM CRUD ====================

@app.get("/db/uyeler")
def db_get_members(
    durum: str = "Aktif",
    dahil_ayrilan: bool = False,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için üye listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Member).filter(Member.customer_id == customer.customer_id)
    if durum and not dahil_ayrilan:
        query = query.filter(Member.status == durum.lower())
    
    members = query.order_by(Member.full_name).all()
    
    return {
        "success": True,
        "data": [
            {
                "uye_id": str(m.id),
                "uye_no": m.member_no,
                "ad_soyad": m.full_name,
                "tc_kimlik": m.tc_no,
                "telefon": m.phone,
                "telefon2": m.phone2,
                "email": m.email,
                "adres": m.address,
                "il": m.city,
                "ilce": m.district,
                "dogum_tarihi": m.birth_date.isoformat() if m.birth_date else None,
                "cinsiyet": m.gender,
                "meslek": m.occupation,
                "uyelik_tipi": m.membership_type,
                "ozel_aidat_tutari": float(m.membership_fee) if m.membership_fee else 0,
                "durum": m.status.capitalize() if m.status else 'Aktif',
                "notlar": m.notes
            }
            for m in members
        ]
    }

@app.get("/db/uyeler/{uye_id}")
def db_get_member(
    uye_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için üye detayı"""
    customer = get_customer_by_api_key(api_key, db)
    
    member = db.query(Member).filter(
        Member.id == uye_id,
        Member.customer_id == customer.customer_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    return {
        "success": True,
        "data": {
            "uye_id": str(member.id),
            "uye_no": member.member_no,
            "ad_soyad": member.full_name,
            "tc_kimlik": member.tc_no,
            "telefon": member.phone,
            "telefon2": member.phone2,
            "email": member.email,
            "adres": member.address,
            "il": member.city,
            "ilce": member.district,
            "dogum_tarihi": member.birth_date.isoformat() if member.birth_date else None,
            "cinsiyet": member.gender,
            "meslek": member.occupation,
            "uyelik_tipi": member.membership_type,
            "ozel_aidat_tutari": float(member.membership_fee) if member.membership_fee else 0,
            "durum": member.status.capitalize() if member.status else 'Aktif',
            "notlar": member.notes
        }
    }

@app.post("/db/uyeler")
def db_create_member(
    data: MemberCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için üye ekle"""
    customer = get_customer_by_api_key(api_key, db)
    
    member = Member(
        customer_id=customer.customer_id,
        member_no=data.member_no,
        full_name=data.full_name,
        tc_no=data.tc_no,
        phone=data.phone,
        phone2=data.phone2,
        email=data.email,
        address=data.address,
        city=data.city,
        district=data.district,
        birth_date=data.birth_date,
        gender=data.gender,
        occupation=data.occupation,
        membership_type=data.membership_type,
        membership_fee=data.membership_fee,
        status=data.status.lower() if data.status else 'active',
        notes=data.notes
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return {"success": True, "uye_id": str(member.id)}

@app.put("/db/uyeler/{uye_id}")
def db_update_member(
    uye_id: str,
    data: MemberCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için üye güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    
    member = db.query(Member).filter(
        Member.id == uye_id,
        Member.customer_id == customer.customer_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(member, key, value)
    
    db.commit()
    return {"success": True}

@app.delete("/db/uyeler/{uye_id}")
def db_delete_member(
    uye_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için üye sil"""
    customer = get_customer_by_api_key(api_key, db)
    
    member = db.query(Member).filter(
        Member.id == uye_id,
        Member.customer_id == customer.customer_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    db.delete(member)
    db.commit()
    return {"success": True}


@app.get("/db/kasalar")
def db_get_cash_accounts(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için kasa listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    accounts = db.query(CashAccount).filter(
        CashAccount.customer_id == customer.customer_id,
        CashAccount.is_active == True
    ).all()
    
    return {
        "success": True,
        "kasalar": [
            {
                "kasa_id": str(a.id),
                "kasa_adi": a.name,
                "para_birimi": "TL" if a.type == "cash" else a.type.upper(),
                "devir_bakiye": float(a.balance) if a.balance else 0,
                "banka_adi": a.bank_name,
                "iban": a.iban,
                "aktif": a.is_active
            }
            for a in accounts
        ]
    }

@app.post("/db/kasalar")
def db_create_cash_account(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için kasa ekle"""
    customer = get_customer_by_api_key(api_key, db)
    
    account = CashAccount(
        customer_id=customer.customer_id,
        name=data.get('kasa_adi'),
        type=data.get('para_birimi', 'TL').lower(),
        balance=data.get('devir_bakiye', 0),
        bank_name=data.get('banka_adi'),
        iban=data.get('iban')
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return {"success": True, "kasa_id": str(account.id)}


@app.get("/db/gelirler")
def db_get_incomes(
    baslangic_tarih: Optional[str] = None,
    bitis_tarih: Optional[str] = None,
    gelir_turu: Optional[str] = None,
    kasa_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için gelir listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Income).filter(Income.customer_id == customer.customer_id)
    
    if baslangic_tarih:
        query = query.filter(Income.date >= baslangic_tarih)
    if bitis_tarih:
        query = query.filter(Income.date <= bitis_tarih)
    if gelir_turu:
        query = query.filter(Income.category == gelir_turu)
    
    incomes = query.order_by(Income.date.desc()).all()
    
    return {
        "success": True,
        "gelirler": [
            {
                "gelir_id": str(i.id),
                "tarih": i.date.isoformat(),
                "gelir_turu": i.category,
                "aciklama": i.description,
                "tutar": float(i.amount),
                "kasa_id": str(i.cash_account),
                "dekont_no": i.receipt_no
            }
            for i in incomes
        ]
    }

@app.post("/db/gelirler")
def db_create_income(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için gelir ekle"""
    customer = get_customer_by_api_key(api_key, db)
    
    income = Income(
        customer_id=customer.customer_id,
        category=data.get('gelir_turu'),
        amount=data.get('tutar'),
        date=data.get('tarih'),
        description=data.get('aciklama'),
        receipt_no=data.get('dekont_no'),
        cash_account=data.get('kasa_id', 'Ana Kasa'),
        fiscal_year=data.get('ait_oldugu_yil')
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    
    return {"success": True, "gelir_id": str(income.id)}


@app.get("/db/giderler")
def db_get_expenses(
    baslangic_tarih: Optional[str] = None,
    bitis_tarih: Optional[str] = None,
    gider_turu: Optional[str] = None,
    kasa_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için gider listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Expense).filter(Expense.customer_id == customer.customer_id)
    
    if baslangic_tarih:
        query = query.filter(Expense.date >= baslangic_tarih)
    if bitis_tarih:
        query = query.filter(Expense.date <= bitis_tarih)
    if gider_turu:
        query = query.filter(Expense.category == gider_turu)
    
    expenses = query.order_by(Expense.date.desc()).all()
    
    return {
        "success": True,
        "giderler": [
            {
                "gider_id": str(e.id),
                "tarih": e.date.isoformat(),
                "gider_turu": e.category,
                "aciklama": e.description,
                "tutar": float(e.amount),
                "kasa_id": str(e.cash_account),
                "fatura_no": e.invoice_no
            }
            for e in expenses
        ]
    }

@app.post("/db/giderler")
def db_create_expense(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için gider ekle"""
    customer = get_customer_by_api_key(api_key, db)
    
    expense = Expense(
        customer_id=customer.customer_id,
        category=data.get('gider_turu'),
        amount=data.get('tutar'),
        date=data.get('tarih'),
        description=data.get('aciklama'),
        invoice_no=data.get('fatura_no'),
        vendor=data.get('odeyen'),
        cash_account=data.get('kasa_id', 'Ana Kasa'),
        fiscal_year=data.get('ait_oldugu_yil')
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    return {"success": True, "gider_id": str(expense.id)}


@app.get("/db/aidat_takip")
def db_get_dues(
    uye_id: Optional[str] = None,
    yil: Optional[int] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için aidat listesi"""
    customer = get_customer_by_api_key(api_key, db)
    
    query = db.query(Due).filter(Due.customer_id == customer.customer_id)
    
    if uye_id:
        query = query.filter(Due.member_id == uye_id)
    if yil:
        query = query.filter(Due.year == yil)
    
    dues = query.order_by(Due.year.desc()).all()
    
    return {
        "success": True,
        "data": [
            {
                "aidat_id": str(d.id),
                "uye_id": str(d.member_id),
                "yil": d.year,
                "ay": d.month,
                "yillik_aidat_tutari": float(d.amount),
                "odenecek_tutar": float(d.amount) - float(d.paid_amount or 0),
                "durum": "Tamamlandı" if d.status == "paid" else "Eksik" if d.status == "pending" else "Kısmi"
            }
            for d in dues
        ]
    }

@app.post("/db/aidat_takip")
def db_create_due(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için aidat kaydı oluştur"""
    customer = get_customer_by_api_key(api_key, db)
    
    due = Due(
        customer_id=customer.customer_id,
        member_id=data.get('uye_id'),
        year=data.get('yil'),
        month=data.get('ay', 1),
        amount=data.get('yillik_aidat_tutari'),
        status='pending'
    )
    db.add(due)
    db.commit()
    db.refresh(due)
    
    return {"success": True, "aidat_id": str(due.id)}


@app.get("/db/virmanlar")
def db_get_transfers(
    baslangic_tarih: Optional[str] = None,
    bitis_tarih: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için virman listesi"""
    customer = get_customer_by_api_key(api_key, db)
    # Virman tablosu PostgreSQL'de yok, boş döndür
    return {"success": True, "virmanlar": []}

@app.post("/db/virmanlar")
def db_create_transfer(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Desktop için virman ekle"""
    customer = get_customer_by_api_key(api_key, db)
    # PostgreSQL'de virman tablosu şimdilik yok
    return {"success": True, "virman_id": 0, "message": "Virman kaydı sunucu tarafında desteklenmiyor"}


# ==================== SUPER ADMIN API ====================

class SuperAdminAuth:
    """Super Admin yetkilendirme"""
    
    @staticmethod
    def verify(admin_key: str = Header(None, alias="X-Admin-Key")):
        if admin_key != settings.admin_secret:
            raise HTTPException(status_code=403, detail="Yetkisiz erişim")
        return True


@app.get("/admin/customers")
def admin_list_customers(
    _: bool = Depends(SuperAdminAuth.verify),
    db: Session = Depends(get_db)
):
    """Tüm müşterileri listele"""
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
                "license_mode": c.license_mode,
                "max_users": c.max_users,
                "max_members": c.max_members,
                "is_active": c.is_active,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "features": c.features,
                "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in customers
        ],
        "total": len(customers)
    }

@app.post("/admin/customers")
def admin_create_customer(
    data: Dict[str, Any],
    _: bool = Depends(SuperAdminAuth.verify),
    db: Session = Depends(get_db)
):
    """Yeni müşteri oluştur"""
    customer_id = data.get('customer_id', f"BADER-{secrets.token_hex(4).upper()}")
    api_key = data.get('api_key', f"bader_{secrets.token_hex(16)}")
    
    customer = Customer(
        customer_id=customer_id,
        api_key=api_key,
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        plan=data.get('plan', 'basic'),
        license_mode=data.get('license_mode', 'local'),
        max_users=data.get('max_users', 5),
        max_members=data.get('max_members', 500),
        is_active=True,
        expires_at=data.get('expires_at'),
        features=data.get('features', ["ocr", "sync", "backup"])
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return {
        "success": True,
        "customer": {
            "id": str(customer.id),
            "customer_id": customer.customer_id,
            "api_key": customer.api_key,
            "name": customer.name
        }
    }

@app.put("/admin/customers/{customer_id}")
def admin_update_customer(
    customer_id: str,
    data: Dict[str, Any],
    _: bool = Depends(SuperAdminAuth.verify),
    db: Session = Depends(get_db)
):
    """Müşteri bilgilerini güncelle"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    for key, value in data.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    
    db.commit()
    return {"success": True}

@app.delete("/admin/customers/{customer_id}")
def admin_delete_customer(
    customer_id: str,
    _: bool = Depends(SuperAdminAuth.verify),
    db: Session = Depends(get_db)
):
    """Müşteri sil"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    db.delete(customer)
    db.commit()
    return {"success": True}

@app.get("/admin/stats")
def admin_stats(
    _: bool = Depends(SuperAdminAuth.verify),
    db: Session = Depends(get_db)
):
    """Admin istatistikleri"""
    total_customers = db.query(Customer).count()
    active_customers = db.query(Customer).filter(Customer.is_active == True).count()
    total_members = db.query(Member).count()
    total_incomes = db.query(Income).count()
    total_expenses = db.query(Expense).count()
    
    # Mod istatistikleri
    local_mode = db.query(Customer).filter(Customer.license_mode == 'local').count()
    internet_mode = db.query(Customer).filter(Customer.license_mode == 'internet').count()
    hybrid_mode = db.query(Customer).filter(Customer.license_mode == 'hybrid').count()
    
    return {
        "stats": {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_members": total_members,
            "total_incomes": total_incomes,
            "total_expenses": total_expenses,
            "license_modes": {
                "local": local_mode,
                "internet": internet_mode,
                "hybrid": hybrid_mode
            }
        }
    }

@app.put("/admin/customers/{customer_id}/mode")
def admin_set_customer_mode(
    customer_id: str,
    data: Dict[str, Any],
    _: bool = Depends(SuperAdminAuth.verify),
    db: Session = Depends(get_db)
):
    """Müşteri lisans modunu değiştir (local/internet/hybrid)"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    mode = data.get('license_mode', 'local')
    if mode not in ['local', 'internet', 'hybrid']:
        raise HTTPException(status_code=400, detail="Geçersiz mod. Geçerli modlar: local, internet, hybrid")
    
    customer.license_mode = mode
    db.commit()
    
    return {
        "success": True, 
        "customer_id": customer_id, 
        "license_mode": mode,
        "message": f"Lisans modu '{mode}' olarak güncellendi"
    }

@app.post("/admin/customers/{customer_id}/reset-api-key")
def admin_reset_api_key(
    customer_id: str,
    _: bool = Depends(SuperAdminAuth.verify),
    db: Session = Depends(get_db)
):
    """Müşteri API anahtarını sıfırla"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    new_api_key = f"bader_{secrets.token_hex(16)}"
    customer.api_key = new_api_key
    db.commit()
    
    return {"success": True, "new_api_key": new_api_key}


# ==================== WEB APP API ====================

@app.get("/api/health")
def api_health():
    """API Health Check"""
    return {
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "web": "/web/*",
            "db": "/db/*",
            "admin": "/admin/*",
            "sync": "/sync/*"
        }
    }

@app.get("/api/docs")
def api_docs():
    """API Dökümantasyonu"""
    return {
        "title": "BADER API",
        "version": "5.0.0",
        "description": "BADER Dernek Yönetim Sistemi API",
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Sistem sağlık kontrolü"},
            {"method": "POST", "path": "/activate", "description": "Lisans aktivasyonu"},
            {"method": "POST", "path": "/auth/login", "description": "Kullanıcı girişi"},
            {"method": "GET", "path": "/web/members", "description": "Üye listesi"},
            {"method": "POST", "path": "/web/members", "description": "Üye ekle"},
            {"method": "GET", "path": "/web/incomes", "description": "Gelir listesi"},
            {"method": "POST", "path": "/web/incomes", "description": "Gelir ekle"},
            {"method": "GET", "path": "/web/expenses", "description": "Gider listesi"},
            {"method": "POST", "path": "/web/expenses", "description": "Gider ekle"},
            {"method": "GET", "path": "/web/dashboard", "description": "Dashboard özeti"},
            {"method": "GET", "path": "/db/uyeler", "description": "Desktop - Üye listesi"},
            {"method": "GET", "path": "/db/kasalar", "description": "Desktop - Kasa listesi"},
            {"method": "GET", "path": "/db/gelirler", "description": "Desktop - Gelir listesi"},
            {"method": "GET", "path": "/db/giderler", "description": "Desktop - Gider listesi"},
            {"method": "GET", "path": "/admin/customers", "description": "Admin - Müşteri listesi"},
            {"method": "POST", "path": "/admin/customers", "description": "Admin - Müşteri ekle"},
            {"method": "GET", "path": "/admin/stats", "description": "Admin - İstatistikler"}
        ]
    }


# ==================== BUDGET (BÜTÇE) API ====================

@app.get("/web/budgets")
def web_get_budgets(
    year: Optional[int] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Bütçe listesi"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(Budget).filter(Budget.customer_id == customer.customer_id)
    if year:
        query = query.filter(Budget.year == year)
    budgets = query.order_by(Budget.year.desc(), Budget.category).all()
    
    return {
        "budgets": [
            {
                "id": str(b.id),
                "year": b.year,
                "category": b.category,
                "budget_type": b.budget_type,
                "planned_amount": float(b.planned_amount or 0),
                "actual_amount": float(b.actual_amount or 0),
                "variance": float((b.planned_amount or 0) - (b.actual_amount or 0)),
                "description": b.description,
                "created_at": b.created_at.isoformat() if b.created_at else None
            }
            for b in budgets
        ],
        "total": len(budgets)
    }

@app.post("/web/budgets")
def web_create_budget(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Bütçe kalemi ekle"""
    customer = get_customer_by_api_key(api_key, db)
    budget = Budget(
        customer_id=customer.customer_id,
        year=data.get("year", datetime.now().year),
        category=data["category"],
        budget_type=data.get("budget_type", "expense"),
        planned_amount=data["planned_amount"],
        actual_amount=data.get("actual_amount", 0),
        description=data.get("description")
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    
    return {"success": True, "budget_id": str(budget.id)}

@app.put("/web/budgets/{budget_id}")
def web_update_budget(
    budget_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Bütçe güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.customer_id == customer.customer_id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Bütçe bulunamadı")
    
    for key in ["year", "category", "budget_type", "planned_amount", "actual_amount", "description"]:
        if key in data:
            setattr(budget, key, data[key])
    
    db.commit()
    return {"success": True}

@app.delete("/web/budgets/{budget_id}")
def web_delete_budget(
    budget_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Bütçe sil"""
    customer = get_customer_by_api_key(api_key, db)
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.customer_id == customer.customer_id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Bütçe bulunamadı")
    
    db.delete(budget)
    db.commit()
    return {"success": True}


# ==================== DOCUMENTS (BELGELER) API ====================

@app.get("/web/documents")
def web_get_documents(
    category: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Belge listesi"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(Document).filter(Document.customer_id == customer.customer_id)
    if category:
        query = query.filter(Document.category == category)
    documents = query.order_by(Document.created_at.desc()).all()
    
    return {
        "documents": [
            {
                "id": str(d.id),
                "title": d.title,
                "file_name": d.file_name,
                "file_size": d.file_size,
                "mime_type": d.mime_type,
                "category": d.category,
                "description": d.description,
                "tags": d.tags or [],
                "uploaded_by": d.uploaded_by,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in documents
        ],
        "total": len(documents)
    }

@app.post("/web/documents")
def web_create_document(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Belge ekle"""
    customer = get_customer_by_api_key(api_key, db)
    document = Document(
        customer_id=customer.customer_id,
        title=data["title"],
        file_name=data.get("file_name"),
        file_path=data.get("file_path"),
        file_size=data.get("file_size"),
        mime_type=data.get("mime_type"),
        category=data.get("category"),
        description=data.get("description"),
        tags=data.get("tags", []),
        uploaded_by=data.get("uploaded_by")
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {"success": True, "document_id": str(document.id)}

@app.delete("/web/documents/{document_id}")
def web_delete_document(
    document_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Belge sil"""
    customer = get_customer_by_api_key(api_key, db)
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.customer_id == customer.customer_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")
    
    db.delete(document)
    db.commit()
    return {"success": True}


# ==================== MEETINGS (TOPLANTILAR) API ====================

@app.get("/web/meetings")
def web_get_meetings(
    status: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Toplantı listesi"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(Meeting).filter(Meeting.customer_id == customer.customer_id)
    if status:
        query = query.filter(Meeting.status == status)
    meetings = query.order_by(Meeting.date.desc()).all()
    
    return {
        "meetings": [
            {
                "id": str(m.id),
                "title": m.title,
                "meeting_type": m.meeting_type,
                "date": m.date.isoformat() if m.date else None,
                "time": m.time,
                "location": m.location,
                "agenda": m.agenda,
                "minutes": m.minutes,
                "decisions": m.decisions,
                "attendees": m.attendees or [],
                "status": m.status,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in meetings
        ],
        "total": len(meetings)
    }

@app.post("/web/meetings")
def web_create_meeting(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Toplantı ekle"""
    customer = get_customer_by_api_key(api_key, db)
    meeting = Meeting(
        customer_id=customer.customer_id,
        title=data["title"],
        meeting_type=data.get("meeting_type", "Yönetim"),
        date=data["date"],
        time=data.get("time"),
        location=data.get("location"),
        agenda=data.get("agenda"),
        minutes=data.get("minutes"),
        decisions=data.get("decisions"),
        attendees=data.get("attendees", []),
        status=data.get("status", "planned")
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    
    return {"success": True, "meeting_id": str(meeting.id)}

@app.put("/web/meetings/{meeting_id}")
def web_update_meeting(
    meeting_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Toplantı güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.customer_id == customer.customer_id
    ).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Toplantı bulunamadı")
    
    for key in ["title", "meeting_type", "date", "time", "location", "agenda", "minutes", "decisions", "attendees", "status"]:
        if key in data:
            setattr(meeting, key, data[key])
    
    db.commit()
    return {"success": True}

@app.delete("/web/meetings/{meeting_id}")
def web_delete_meeting(
    meeting_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Toplantı sil"""
    customer = get_customer_by_api_key(api_key, db)
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.customer_id == customer.customer_id
    ).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Toplantı bulunamadı")
    
    db.delete(meeting)
    db.commit()
    return {"success": True}


# ==================== EVENTS (ETKİNLİKLER) API ====================

@app.get("/web/events")
def web_get_events(
    status: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Etkinlik listesi"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(Event).filter(Event.customer_id == customer.customer_id)
    if status:
        query = query.filter(Event.status == status)
    events = query.order_by(Event.start_date.desc()).all()
    
    return {
        "events": [
            {
                "id": str(e.id),
                "title": e.title,
                "event_type": e.event_type,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "start_time": e.start_time,
                "end_time": e.end_time,
                "location": e.location,
                "description": e.description,
                "organizer": e.organizer,
                "budget": float(e.budget or 0),
                "actual_cost": float(e.actual_cost or 0),
                "max_participants": e.max_participants,
                "participants": e.participants or [],
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in events
        ],
        "total": len(events)
    }

@app.post("/web/events")
def web_create_event(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Etkinlik ekle"""
    customer = get_customer_by_api_key(api_key, db)
    event = Event(
        customer_id=customer.customer_id,
        title=data["title"],
        event_type=data.get("event_type"),
        start_date=data["start_date"],
        end_date=data.get("end_date"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        location=data.get("location"),
        description=data.get("description"),
        organizer=data.get("organizer"),
        budget=data.get("budget", 0),
        actual_cost=data.get("actual_cost", 0),
        max_participants=data.get("max_participants"),
        participants=data.get("participants", []),
        status=data.get("status", "planned")
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return {"success": True, "event_id": str(event.id)}

@app.put("/web/events/{event_id}")
def web_update_event(
    event_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Etkinlik güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.customer_id == customer.customer_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    
    for key in ["title", "event_type", "start_date", "end_date", "start_time", "end_time", 
                "location", "description", "organizer", "budget", "actual_cost", 
                "max_participants", "participants", "status"]:
        if key in data:
            setattr(event, key, data[key])
    
    db.commit()
    return {"success": True}

@app.delete("/web/events/{event_id}")
def web_delete_event(
    event_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Etkinlik sil"""
    customer = get_customer_by_api_key(api_key, db)
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.customer_id == customer.customer_id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı")
    
    db.delete(event)
    db.commit()
    return {"success": True}


# ==================== TRANSFERS (VİRMAN) API ====================

@app.get("/web/transfers")
def web_get_transfers(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Virman listesi"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(Transfer).filter(Transfer.customer_id == customer.customer_id)
    if start_date:
        query = query.filter(Transfer.date >= start_date)
    if end_date:
        query = query.filter(Transfer.date <= end_date)
    transfers = query.order_by(Transfer.date.desc()).all()
    
    return {
        "transfers": [
            {
                "id": str(t.id),
                "from_account": t.from_account,
                "to_account": t.to_account,
                "amount": float(t.amount or 0),
                "date": t.date.isoformat() if t.date else None,
                "description": t.description,
                "created_by": t.created_by,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transfers
        ],
        "total": len(transfers)
    }

@app.post("/web/transfers")
def web_create_transfer(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Virman ekle"""
    customer = get_customer_by_api_key(api_key, db)
    transfer = Transfer(
        customer_id=customer.customer_id,
        from_account=data["from_account"],
        to_account=data["to_account"],
        amount=data["amount"],
        date=data.get("date", date.today().isoformat()),
        description=data.get("description"),
        created_by=data.get("created_by")
    )
    db.add(transfer)
    
    # Kasa bakiyelerini güncelle
    from_account = db.query(CashAccount).filter(
        CashAccount.customer_id == customer.customer_id,
        CashAccount.name == data["from_account"]
    ).first()
    if from_account:
        from_account.balance = float(from_account.balance or 0) - float(data["amount"])
    
    to_account = db.query(CashAccount).filter(
        CashAccount.customer_id == customer.customer_id,
        CashAccount.name == data["to_account"]
    ).first()
    if to_account:
        to_account.balance = float(to_account.balance or 0) + float(data["amount"])
    
    db.commit()
    db.refresh(transfer)
    
    return {"success": True, "transfer_id": str(transfer.id)}

@app.delete("/web/transfers/{transfer_id}")
def web_delete_transfer(
    transfer_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Virman sil"""
    customer = get_customer_by_api_key(api_key, db)
    transfer = db.query(Transfer).filter(
        Transfer.id == transfer_id,
        Transfer.customer_id == customer.customer_id
    ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Virman bulunamadı")
    
    # Kasa bakiyelerini geri al
    from_account = db.query(CashAccount).filter(
        CashAccount.customer_id == customer.customer_id,
        CashAccount.name == transfer.from_account
    ).first()
    if from_account:
        from_account.balance = float(from_account.balance or 0) + float(transfer.amount)
    
    to_account = db.query(CashAccount).filter(
        CashAccount.customer_id == customer.customer_id,
        CashAccount.name == transfer.to_account
    ).first()
    if to_account:
        to_account.balance = float(to_account.balance or 0) - float(transfer.amount)
    
    db.delete(transfer)
    db.commit()
    return {"success": True}


# ==================== FAMILY MEMBERS (AİLE ÜYELERİ) API ====================

@app.get("/web/members/{member_id}/family")
def web_get_family_members(
    member_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üyenin aile üyeleri"""
    customer = get_customer_by_api_key(api_key, db)
    family = db.query(FamilyMember).filter(
        FamilyMember.member_id == member_id,
        FamilyMember.customer_id == customer.customer_id
    ).all()
    
    return {
        "family_members": [
            {
                "id": str(f.id),
                "member_id": str(f.member_id),
                "full_name": f.full_name,
                "relationship": f.relationship,
                "birth_date": f.birth_date.isoformat() if f.birth_date else None,
                "gender": f.gender,
                "phone": f.phone,
                "email": f.email,
                "notes": f.notes
            }
            for f in family
        ],
        "total": len(family)
    }

@app.post("/web/members/{member_id}/family")
def web_add_family_member(
    member_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Aile üyesi ekle"""
    customer = get_customer_by_api_key(api_key, db)
    family_member = FamilyMember(
        customer_id=customer.customer_id,
        member_id=member_id,
        full_name=data["full_name"],
        relationship=data.get("relationship"),
        birth_date=data.get("birth_date"),
        gender=data.get("gender"),
        phone=data.get("phone"),
        email=data.get("email"),
        notes=data.get("notes")
    )
    db.add(family_member)
    db.commit()
    db.refresh(family_member)
    
    return {"success": True, "family_member_id": str(family_member.id)}

@app.delete("/web/family/{family_id}")
def web_delete_family_member(
    family_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Aile üyesi sil"""
    customer = get_customer_by_api_key(api_key, db)
    family = db.query(FamilyMember).filter(
        FamilyMember.id == family_id,
        FamilyMember.customer_id == customer.customer_id
    ).first()
    if not family:
        raise HTTPException(status_code=404, detail="Aile üyesi bulunamadı")
    
    db.delete(family)
    db.commit()
    return {"success": True}


# ==================== YEARLY CARRYOVER (DEVİR) API ====================

@app.get("/web/carryovers")
def web_get_carryovers(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Devir listesi"""
    customer = get_customer_by_api_key(api_key, db)
    carryovers = db.query(YearlyCarryover).filter(
        YearlyCarryover.customer_id == customer.customer_id
    ).order_by(YearlyCarryover.from_year.desc()).all()
    
    return {
        "carryovers": [
            {
                "id": str(c.id),
                "from_year": c.from_year,
                "to_year": c.to_year,
                "total_income": float(c.total_income or 0),
                "total_expense": float(c.total_expense or 0),
                "balance": float(c.balance or 0),
                "carried_balance": float(c.carried_balance or 0),
                "status": c.status,
                "approved_by": c.approved_by,
                "approved_at": c.approved_at.isoformat() if c.approved_at else None,
                "notes": c.notes,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in carryovers
        ],
        "total": len(carryovers)
    }

@app.post("/web/carryovers")
def web_create_carryover(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Yıl devri oluştur"""
    customer = get_customer_by_api_key(api_key, db)
    from_year = data.get("from_year", datetime.now().year - 1)
    to_year = data.get("to_year", datetime.now().year)
    
    # Yıl gelir/gider hesapla
    total_income = db.query(Income).filter(
        Income.customer_id == customer.customer_id,
        Income.fiscal_year == from_year
    ).with_entities(func.sum(Income.amount)).scalar() or 0
    
    total_expense = db.query(Expense).filter(
        Expense.customer_id == customer.customer_id,
        Expense.fiscal_year == from_year
    ).with_entities(func.sum(Expense.amount)).scalar() or 0
    
    balance = float(total_income) - float(total_expense)
    
    carryover = YearlyCarryover(
        customer_id=customer.customer_id,
        from_year=from_year,
        to_year=to_year,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        carried_balance=balance,
        status="pending",
        notes=data.get("notes")
    )
    db.add(carryover)
    db.commit()
    db.refresh(carryover)
    
    return {"success": True, "carryover_id": str(carryover.id), "balance": balance}

@app.put("/web/carryovers/{carryover_id}/approve")
def web_approve_carryover(
    carryover_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Devir onayla"""
    customer = get_customer_by_api_key(api_key, db)
    carryover = db.query(YearlyCarryover).filter(
        YearlyCarryover.id == carryover_id,
        YearlyCarryover.customer_id == customer.customer_id
    ).first()
    if not carryover:
        raise HTTPException(status_code=404, detail="Devir bulunamadı")
    
    carryover.status = "completed"
    carryover.approved_by = data.get("approved_by", token.get("username"))
    carryover.approved_at = datetime.utcnow()
    
    # Yeni yıla devir geliri ekle
    if carryover.carried_balance > 0:
        income = Income(
            customer_id=customer.customer_id,
            category="DEVİR",
            amount=carryover.carried_balance,
            date=date(carryover.to_year, 1, 1),
            description=f"{carryover.from_year} yılından devir",
            fiscal_year=carryover.to_year,
            cash_account="Ana Kasa"
        )
        db.add(income)
    
    db.commit()
    return {"success": True}


# ==================== ASSESSMENT REPORT (TAHAKKUK RAPORU) API ====================

@app.get("/web/assessment-reports")
def web_get_assessment_reports(
    year: Optional[int] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Tahakkuk raporları"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(AssessmentReport).filter(
        AssessmentReport.customer_id == customer.customer_id
    )
    if year:
        query = query.filter(AssessmentReport.year == year)
    reports = query.order_by(AssessmentReport.report_date.desc()).all()
    
    return {
        "reports": [
            {
                "id": str(r.id),
                "year": r.year,
                "report_date": r.report_date.isoformat() if r.report_date else None,
                "total_assessed": float(r.total_assessed or 0),
                "total_collected": float(r.total_collected or 0),
                "total_remaining": float(r.total_remaining or 0),
                "member_count": r.member_count,
                "collection_rate": float(r.collection_rate or 0),
                "details": r.details or {},
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reports
        ],
        "total": len(reports)
    }

@app.post("/web/assessment-reports/generate")
def web_generate_assessment_report(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Tahakkuk raporu oluştur"""
    customer = get_customer_by_api_key(api_key, db)
    year = data.get("year", datetime.now().year)
    
    # Üye sayısı
    members = db.query(Member).filter(
        Member.customer_id == customer.customer_id,
        Member.status == 'active'
    ).all()
    member_count = len(members)
    
    # Tahakkuk hesapla
    total_assessed = sum([float(m.membership_fee or 0) * 12 for m in members])
    
    # Tahsilat hesapla
    total_collected = db.query(Due).filter(
        Due.customer_id == customer.customer_id,
        Due.year == year
    ).with_entities(func.sum(Due.paid_amount)).scalar() or 0
    
    total_remaining = total_assessed - float(total_collected)
    collection_rate = (float(total_collected) / total_assessed * 100) if total_assessed > 0 else 0
    
    report = AssessmentReport(
        customer_id=customer.customer_id,
        year=year,
        report_date=date.today(),
        total_assessed=total_assessed,
        total_collected=total_collected,
        total_remaining=total_remaining,
        member_count=member_count,
        collection_rate=collection_rate,
        details={"generated_at": datetime.now().isoformat()}
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return {
        "success": True,
        "report_id": str(report.id),
        "summary": {
            "year": year,
            "member_count": member_count,
            "total_assessed": float(total_assessed),
            "total_collected": float(total_collected),
            "total_remaining": float(total_remaining),
            "collection_rate": round(collection_rate, 2)
        }
    }


# ==================== LEFT MEMBERS (AYRILAN ÜYELER) API ====================

@app.get("/web/left-members")
def web_get_left_members(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Ayrılan üyeler listesi"""
    customer = get_customer_by_api_key(api_key, db)
    members = db.query(Member).filter(
        Member.customer_id == customer.customer_id,
        Member.status == 'inactive'
    ).order_by(Member.leave_date.desc()).all()
    
    return {
        "members": [
            {
                "id": str(m.id),
                "member_no": m.member_no,
                "full_name": m.full_name,
                "phone": m.phone,
                "email": m.email,
                "join_date": m.join_date.isoformat() if m.join_date else None,
                "leave_date": m.leave_date.isoformat() if m.leave_date else None,
                "notes": m.notes
            }
            for m in members
        ],
        "total": len(members)
    }

@app.put("/web/members/{member_id}/leave")
def web_member_leave(
    member_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üyeyi ayrılmış olarak işaretle"""
    customer = get_customer_by_api_key(api_key, db)
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.customer_id == customer.customer_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    member.status = 'inactive'
    member.leave_date = data.get("leave_date", date.today())
    member.notes = (member.notes or "") + f"\n[Ayrılış: {data.get('reason', 'Belirtilmedi')}]"
    
    db.commit()
    return {"success": True}

@app.put("/web/members/{member_id}/reactivate")
def web_member_reactivate(
    member_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Ayrılan üyeyi tekrar aktifleştir"""
    customer = get_customer_by_api_key(api_key, db)
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.customer_id == customer.customer_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    member.status = 'active'
    member.leave_date = None
    
    db.commit()
    return {"success": True}


# ==================== INCOME/EXPENSE CRUD ====================

@app.put("/web/incomes/{income_id}")
def web_update_income(
    income_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gelir güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.customer_id == customer.customer_id
    ).first()
    if not income:
        raise HTTPException(status_code=404, detail="Gelir bulunamadı")
    
    for key in ["category", "amount", "date", "description", "receipt_no", "cash_account"]:
        if key in data:
            setattr(income, key, data[key])
    
    db.commit()
    return {"success": True}

@app.delete("/web/incomes/{income_id}")
def web_delete_income(
    income_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gelir sil"""
    customer = get_customer_by_api_key(api_key, db)
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.customer_id == customer.customer_id
    ).first()
    if not income:
        raise HTTPException(status_code=404, detail="Gelir bulunamadı")
    
    db.delete(income)
    db.commit()
    return {"success": True}

@app.put("/web/expenses/{expense_id}")
def web_update_expense(
    expense_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gider güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.customer_id == customer.customer_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    
    for key in ["category", "amount", "date", "description", "invoice_no", "vendor", "cash_account"]:
        if key in data:
            setattr(expense, key, data[key])
    
    db.commit()
    return {"success": True}

@app.delete("/web/expenses/{expense_id}")
def web_delete_expense(
    expense_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gider sil"""
    customer = get_customer_by_api_key(api_key, db)
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.customer_id == customer.customer_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    
    db.delete(expense)
    db.commit()
    return {"success": True}


# ==================== CASH ACCOUNT CRUD ====================

@app.post("/web/cash-accounts")
def web_create_cash_account(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kasa ekle"""
    customer = get_customer_by_api_key(api_key, db)
    account = CashAccount(
        customer_id=customer.customer_id,
        name=data["name"],
        type=data.get("type", "cash"),
        balance=data.get("balance", 0),
        bank_name=data.get("bank_name"),
        iban=data.get("iban"),
        is_active=True
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return {"success": True, "account_id": str(account.id)}

@app.put("/web/cash-accounts/{account_id}")
def web_update_cash_account(
    account_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kasa güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    account = db.query(CashAccount).filter(
        CashAccount.id == account_id,
        CashAccount.customer_id == customer.customer_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Kasa bulunamadı")
    
    for key in ["name", "type", "balance", "bank_name", "iban", "is_active"]:
        if key in data:
            setattr(account, key, data[key])
    
    db.commit()
    return {"success": True}

@app.delete("/web/cash-accounts/{account_id}")
def web_delete_cash_account(
    account_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kasa sil"""
    customer = get_customer_by_api_key(api_key, db)
    account = db.query(CashAccount).filter(
        CashAccount.id == account_id,
        CashAccount.customer_id == customer.customer_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Kasa bulunamadı")
    
    db.delete(account)
    db.commit()
    return {"success": True}


# ==================== SEARCH (ARAMA) API ====================

@app.get("/web/search")
def web_search(
    q: str,
    type: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Genel arama"""
    customer = get_customer_by_api_key(api_key, db)
    results = {"members": [], "incomes": [], "expenses": [], "total": 0}
    search_term = f"%{q}%"
    
    if not type or type == "members":
        members = db.query(Member).filter(
            Member.customer_id == customer.customer_id,
            (Member.full_name.ilike(search_term) | 
             Member.member_no.ilike(search_term) |
             Member.tc_no.ilike(search_term) |
             Member.phone.ilike(search_term) |
             Member.email.ilike(search_term))
        ).limit(50).all()
        results["members"] = [{"id": str(m.id), "full_name": m.full_name, "member_no": m.member_no, "phone": m.phone} for m in members]
    
    if not type or type == "incomes":
        incomes = db.query(Income).filter(
            Income.customer_id == customer.customer_id,
            (Income.category.ilike(search_term) | 
             Income.description.ilike(search_term) |
             Income.receipt_no.ilike(search_term))
        ).limit(50).all()
        results["incomes"] = [{"id": str(i.id), "category": i.category, "amount": float(i.amount), "date": i.date.isoformat() if i.date else None} for i in incomes]
    
    if not type or type == "expenses":
        expenses = db.query(Expense).filter(
            Expense.customer_id == customer.customer_id,
            (Expense.category.ilike(search_term) | 
             Expense.description.ilike(search_term) |
             Expense.vendor.ilike(search_term) |
             Expense.invoice_no.ilike(search_term))
        ).limit(50).all()
        results["expenses"] = [{"id": str(e.id), "category": e.category, "amount": float(e.amount), "date": e.date.isoformat() if e.date else None} for e in expenses]
    
    results["total"] = len(results["members"]) + len(results["incomes"]) + len(results["expenses"])
    return results


# ==================== REPORTS (RAPORLAR) API ====================

@app.get("/web/reports/income-expense")
def web_report_income_expense(
    year: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gelir-Gider raporu"""
    customer = get_customer_by_api_key(api_key, db)
    year = year or datetime.now().year
    
    incomes = db.query(Income).filter(
        Income.customer_id == customer.customer_id,
        Income.fiscal_year == year
    ).all()
    
    expenses = db.query(Expense).filter(
        Expense.customer_id == customer.customer_id,
        Expense.fiscal_year == year
    ).all()
    
    income_by_category = {}
    for i in incomes:
        cat = i.category or "Diğer"
        income_by_category[cat] = income_by_category.get(cat, 0) + float(i.amount or 0)
    
    expense_by_category = {}
    for e in expenses:
        cat = e.category or "Diğer"
        expense_by_category[cat] = expense_by_category.get(cat, 0) + float(e.amount or 0)
    
    total_income = sum(income_by_category.values())
    total_expense = sum(expense_by_category.values())
    
    return {
        "year": year,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
        "income_count": len(incomes),
        "expense_count": len(expenses)
    }

@app.get("/web/reports/members")
def web_report_members(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üye raporu"""
    customer = get_customer_by_api_key(api_key, db)
    members = db.query(Member).filter(
        Member.customer_id == customer.customer_id
    ).all()
    
    active = len([m for m in members if m.status == 'active'])
    inactive = len([m for m in members if m.status == 'inactive'])
    
    by_type = {}
    for m in members:
        t = m.membership_type or "Belirsiz"
        by_type[t] = by_type.get(t, 0) + 1
    
    by_gender = {}
    for m in members:
        g = m.gender or "Belirsiz"
        by_gender[g] = by_gender.get(g, 0) + 1
    
    total_fees = sum([float(m.membership_fee or 0) for m in members if m.status == 'active'])
    
    return {
        "total": len(members),
        "active": active,
        "inactive": inactive,
        "by_type": by_type,
        "by_gender": by_gender,
        "total_monthly_fees": total_fees,
        "total_yearly_fees": total_fees * 12
    }

@app.get("/web/reports/dues")
def web_report_dues(
    year: Optional[int] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Aidat raporu"""
    customer = get_customer_by_api_key(api_key, db)
    year = year or datetime.now().year
    
    dues = db.query(Due).filter(
        Due.customer_id == customer.customer_id,
        Due.year == year
    ).all()
    
    total_amount = sum([float(d.amount or 0) for d in dues])
    total_paid = sum([float(d.paid_amount or 0) for d in dues])
    total_remaining = total_amount - total_paid
    
    paid_count = len([d for d in dues if d.status == 'paid'])
    pending_count = len([d for d in dues if d.status == 'pending'])
    
    by_month = {}
    for d in dues:
        by_month[d.month] = by_month.get(d.month, {"amount": 0, "paid": 0})
        by_month[d.month]["amount"] += float(d.amount or 0)
        by_month[d.month]["paid"] += float(d.paid_amount or 0)
    
    return {
        "year": year,
        "total_amount": total_amount,
        "total_paid": total_paid,
        "total_remaining": total_remaining,
        "collection_rate": round((total_paid / total_amount * 100) if total_amount > 0 else 0, 2),
        "paid_count": paid_count,
        "pending_count": pending_count,
        "by_month": by_month
    }

@app.get("/web/reports/cash")
def web_report_cash(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kasa raporu"""
    customer = get_customer_by_api_key(api_key, db)
    accounts = db.query(CashAccount).filter(
        CashAccount.customer_id == customer.customer_id
    ).all()
    
    total_balance = sum([float(a.balance or 0) for a in accounts])
    
    return {
        "accounts": [
            {
                "name": a.name,
                "type": a.type,
                "balance": float(a.balance or 0),
                "is_active": a.is_active
            }
            for a in accounts
        ],
        "total_balance": total_balance,
        "account_count": len(accounts)
    }

@app.get("/web/reports/yearly")
def web_report_yearly(
    year: Optional[int] = None,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Yıllık özet rapor"""
    customer = get_customer_by_api_key(api_key, db)
    year = year or datetime.now().year
    
    # Üye istatistikleri
    members = db.query(Member).filter(
        Member.customer_id == customer.customer_id,
        Member.status == 'active'
    ).count()
    
    # Gelir
    total_income = db.query(Income).filter(
        Income.customer_id == customer.customer_id,
        Income.fiscal_year == year
    ).with_entities(func.sum(Income.amount)).scalar() or 0
    
    # Gider
    total_expense = db.query(Expense).filter(
        Expense.customer_id == customer.customer_id,
        Expense.fiscal_year == year
    ).with_entities(func.sum(Expense.amount)).scalar() or 0
    
    # Aidat
    dues_data = db.query(Due).filter(
        Due.customer_id == customer.customer_id,
        Due.year == year
    ).with_entities(
        func.sum(Due.amount).label('total'),
        func.sum(Due.paid_amount).label('paid')
    ).first()
    
    # Toplantı ve etkinlik
    meeting_count = db.query(Meeting).filter(
        Meeting.customer_id == customer.customer_id
    ).count()
    
    event_count = db.query(Event).filter(
        Event.customer_id == customer.customer_id
    ).count()
    
    return {
        "year": year,
        "summary": {
            "active_members": members,
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "balance": float(total_income) - float(total_expense),
            "dues_assessed": float(dues_data.total or 0) if dues_data else 0,
            "dues_collected": float(dues_data.paid or 0) if dues_data else 0,
            "meeting_count": meeting_count,
            "event_count": event_count
        }
    }


# ==================== EXPORT (DIŞA AKTARMA) API ====================

@app.get("/web/export/members")
def web_export_members(
    format: str = "json",
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Üye listesi dışa aktar"""
    customer = get_customer_by_api_key(api_key, db)
    members = db.query(Member).filter(
        Member.customer_id == customer.customer_id
    ).order_by(Member.full_name).all()
    
    data = [
        {
            "uye_no": m.member_no,
            "ad_soyad": m.full_name,
            "tc_no": m.tc_no,
            "telefon": m.phone,
            "email": m.email,
            "adres": m.address,
            "sehir": m.city,
            "ilce": m.district,
            "uyelik_tipi": m.membership_type,
            "aidat": float(m.membership_fee or 0),
            "giris_tarihi": m.join_date.isoformat() if m.join_date else None,
            "durum": "Aktif" if m.status == 'active' else "Pasif"
        }
        for m in members
    ]
    
    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return {"csv": output.getvalue(), "filename": f"uyeler_{date.today()}.csv"}
    
    return {"data": data, "count": len(data)}

@app.get("/web/export/incomes")
def web_export_incomes(
    year: Optional[int] = None,
    format: str = "json",
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gelir listesi dışa aktar"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(Income).filter(Income.customer_id == customer.customer_id)
    if year:
        query = query.filter(Income.fiscal_year == year)
    incomes = query.order_by(Income.date.desc()).all()
    
    data = [
        {
            "tarih": i.date.isoformat() if i.date else None,
            "kategori": i.category,
            "aciklama": i.description,
            "tutar": float(i.amount or 0),
            "kasa": i.cash_account,
            "makbuz_no": i.receipt_no
        }
        for i in incomes
    ]
    
    return {"data": data, "count": len(data), "total": sum([d["tutar"] for d in data])}

@app.get("/web/export/expenses")
def web_export_expenses(
    year: Optional[int] = None,
    format: str = "json",
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Gider listesi dışa aktar"""
    customer = get_customer_by_api_key(api_key, db)
    query = db.query(Expense).filter(Expense.customer_id == customer.customer_id)
    if year:
        query = query.filter(Expense.fiscal_year == year)
    expenses = query.order_by(Expense.date.desc()).all()
    
    data = [
        {
            "tarih": e.date.isoformat() if e.date else None,
            "kategori": e.category,
            "aciklama": e.description,
            "tutar": float(e.amount or 0),
            "firma": e.vendor,
            "fatura_no": e.invoice_no,
            "kasa": e.cash_account
        }
        for e in expenses
    ]
    
    return {"data": data, "count": len(data), "total": sum([d["tutar"] for d in data])}


# ==================== MULTI-YEAR DUES (ÇOKLU YIL ÖDEME) API ====================

@app.post("/web/dues/multi-year")
def web_multi_year_dues_payment(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Çoklu yıl aidat ödemesi"""
    customer = get_customer_by_api_key(api_key, db)
    member_id = data["member_id"]
    years = data["years"]  # [2024, 2025, 2026]
    months = data.get("months", list(range(1, 13)))  # default tüm aylar
    amount_per_month = data["amount_per_month"]
    payment_date = data.get("payment_date", date.today().isoformat())
    
    paid_dues = []
    total_paid = 0
    
    for year in years:
        for month in months:
            # Mevcut aidat kaydını bul veya oluştur
            due = db.query(Due).filter(
                Due.customer_id == customer.customer_id,
                Due.member_id == member_id,
                Due.year == year,
                Due.month == month
            ).first()
            
            if not due:
                due = Due(
                    customer_id=customer.customer_id,
                    member_id=member_id,
                    year=year,
                    month=month,
                    amount=amount_per_month,
                    paid_amount=amount_per_month,
                    paid_date=payment_date,
                    status='paid'
                )
                db.add(due)
            else:
                due.paid_amount = amount_per_month
                due.paid_date = payment_date
                due.status = 'paid'
            
            paid_dues.append({"year": year, "month": month})
            total_paid += amount_per_month
    
    # Gelir kaydı oluştur
    income = Income(
        customer_id=customer.customer_id,
        member_id=member_id,
        category="AİDAT",
        amount=total_paid,
        date=payment_date,
        description=f"Çoklu yıl aidat ödemesi: {years}",
        cash_account=data.get("cash_account", "Ana Kasa"),
        fiscal_year=datetime.now().year
    )
    db.add(income)
    
    db.commit()
    
    return {
        "success": True,
        "paid_dues": paid_dues,
        "total_paid": total_paid,
        "years": years,
        "months": months
    }


# ==================== USERS (KULLANICILAR) API ====================

@app.get("/web/users")
def web_get_users(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kullanıcı listesi"""
    customer = get_customer_by_api_key(api_key, db)
    users = db.query(User).filter(
        User.customer_id == customer.customer_id
    ).order_by(User.created_at.desc()).all()
    
    return {
        "users": [
            {
                "id": str(u.id),
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ],
        "total": len(users)
    }

@app.post("/web/users")
def web_create_user(
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kullanıcı ekle"""
    customer = get_customer_by_api_key(api_key, db)
    # Şifre hash'le
    password_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    
    user = User(
        customer_id=customer.customer_id,
        username=data["username"],
        password_hash=password_hash,
        full_name=data["full_name"],
        email=data.get("email"),
        role=data.get("role", "member"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"success": True, "user_id": str(user.id)}

@app.put("/web/users/{user_id}")
def web_update_user(
    user_id: str,
    data: Dict[str, Any],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kullanıcı güncelle"""
    customer = get_customer_by_api_key(api_key, db)
    user = db.query(User).filter(
        User.id == user_id,
        User.customer_id == customer.customer_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    for key in ["username", "full_name", "email", "role", "is_active"]:
        if key in data:
            setattr(user, key, data[key])
    
    if "password" in data and data["password"]:
        user.password_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    
    db.commit()
    return {"success": True}

@app.delete("/web/users/{user_id}")
def web_delete_user(
    user_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Kullanıcı sil"""
    customer = get_customer_by_api_key(api_key, db)
    user = db.query(User).filter(
        User.id == user_id,
        User.customer_id == customer.customer_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    db.delete(user)
    db.commit()
    return {"success": True}

