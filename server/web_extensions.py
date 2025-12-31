"""
BADER Web API Extensions v5.0
Desktop senkronizasyonu için ek endpoint'ler
Bu dosya main.py'nin sonuna eklenir
"""

# ==================== MEMBER MODEL (if not exists) ====================

# Check if Member model exists, if not create
try:
    Member
except NameError:
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

try:
    Income
except NameError:
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

try:
    Expense
except NameError:
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

try:
    CashAccount
except NameError:
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

try:
    Due
except NameError:
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


# ==================== HELPER ====================

def get_customer_by_api_key(api_key: str, db: Session) -> Customer:
    customer = db.query(Customer).filter(Customer.api_key == api_key).first()
    if not customer:
        raise HTTPException(status_code=401, detail="Geçersiz API key")
    if not customer.is_active:
        raise HTTPException(status_code=401, detail="Hesap devre dışı")
    return customer


# ==================== WEB API - MEMBERS ====================

@app.get("/web/members")
def web_get_members(
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
def web_get_member(
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
def web_create_member(
    data: MemberCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Yeni üye ekle"""
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
        status=data.status,
        notes=data.notes
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return {"success": True, "id": str(member.id), "message": "Üye eklendi"}

@app.put("/web/members/{member_id}")
def web_update_member(
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
def web_delete_member(
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
def web_get_incomes(
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
def web_create_income(
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
def web_get_expenses(
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
def web_create_expense(
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
def web_get_cash_accounts(
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
def web_get_dues(
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
def web_pay_due(
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
def web_get_dashboard(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Dashboard özet verileri"""
    customer = get_customer_by_api_key(api_key, db)
    cid = customer.customer_id
    
    from sqlalchemy import func
    
    # İstatistikler
    total_members = db.query(Member).filter(Member.customer_id == cid, Member.status == 'active').count()
    
    current_year = date.today().year
    total_income = db.query(func.sum(Income.amount)).filter(
        Income.customer_id == cid, 
        Income.fiscal_year == current_year
    ).scalar() or 0
    
    total_expense = db.query(func.sum(Expense.amount)).filter(
        Expense.customer_id == cid,
        Expense.fiscal_year == current_year
    ).scalar() or 0
    
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
    data: dict,
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
            member_data.pop("id", None)
            member_data.pop("customer_id", None)
            member = Member(customer_id=customer.customer_id, **member_data)
            db.add(member)
        synced["members"] += 1
    
    # Gelirler
    for income_data in data.get("incomes", []):
        income_data.pop("id", None)
        income_data.pop("customer_id", None)
        income = Income(customer_id=customer.customer_id, **income_data)
        db.add(income)
        synced["incomes"] += 1
    
    # Giderler
    for expense_data in data.get("expenses", []):
        expense_data.pop("id", None)
        expense_data.pop("customer_id", None)
        expense = Expense(customer_id=customer.customer_id, **expense_data)
        db.add(expense)
        synced["expenses"] += 1
    
    db.commit()
    
    return {"success": True, "synced": synced}

@app.get("/sync/download")
def sync_download(
    since: Optional[str] = None,
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
        since_dt = datetime.fromisoformat(since)
        members_query = members_query.filter(Member.updated_at >= since_dt)
        incomes_query = incomes_query.filter(Income.created_at >= since_dt)
        expenses_query = expenses_query.filter(Expense.created_at >= since_dt)
    
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
