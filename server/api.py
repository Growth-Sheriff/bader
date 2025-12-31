"""
BADER API Server v5.0.0
Desktop ve Web Entegrasyonu için Tam API
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional, List, Any, Dict
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Date, Text, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import secrets
import bcrypt
from jose import JWTError, jwt


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
    
    customer.last_seen_at = datetime.utcnow()
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

@app.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Kullanıcı girişi"""
    user = db.query(User).filter(
        User.customer_id == request.customer_id,
        User.username == request.username
    ).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Hesap devre dışı")
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    token = create_access_token({
        "sub": str(user.id),
        "customer_id": user.customer_id,
        "username": user.username,
        "role": user.role
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
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
    ).with_entities(db.func.sum(Income.amount)).scalar() or 0
    
    total_expense = db.query(Expense).filter(
        Expense.customer_id == cid,
        Expense.fiscal_year == current_year
    ).with_entities(db.func.sum(Expense.amount)).scalar() or 0
    
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
