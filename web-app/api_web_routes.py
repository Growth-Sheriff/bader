"""
BADER Web API Endpoints
Web uygulaması için ek endpoint'ler
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/web", tags=["Web App"])

# ==================== SCHEMAS ====================

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
    receipt_no: Optional[str] = None

class ExpenseCreate(BaseModel):
    date: str
    category: str
    amount: float
    description: Optional[str] = None
    vendor: Optional[str] = None
    cash_account: str = "Ana Kasa"
    invoice_no: Optional[str] = None

class DuePayment(BaseModel):
    due_id: str
    amount: float

class SettingsUpdate(BaseModel):
    organization_name: Optional[str] = None
    yearly_dues: Optional[float] = None

# ==================== DEPENDENCIES ====================

def get_customer_id(x_customer_id: str = Header(None), authorization: str = Header(None)):
    """Customer ID'yi header'dan al"""
    if not x_customer_id:
        raise HTTPException(status_code=401, detail="Customer ID gerekli")
    return x_customer_id

# ==================== MEMBERS ====================

@router.get("/members")
def list_members(
    customer_id: str = Depends(get_customer_id),
    status: Optional[str] = None,
    db: Session = Depends(lambda: None)  # Will be replaced with actual db
):
    """Üye listesi"""
    from main import get_db, Member
    db = next(get_db())
    
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

@router.post("/members")
def create_member(
    data: MemberCreate,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Yeni üye ekle"""
    from main import get_db, Member
    db = next(get_db())
    
    # Sonraki üye numarasını bul
    max_no = db.query(func.max(Member.member_no)).filter(
        Member.customer_id == customer_id
    ).scalar() or 0
    
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

@router.put("/members/{member_id}")
def update_member(
    member_id: str,
    data: MemberCreate,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Üye güncelle"""
    from main import get_db, Member
    db = next(get_db())
    
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.customer_id == customer_id
    ).first()
    
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

@router.delete("/members/{member_id}")
def delete_member(
    member_id: str,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Üye sil (pasif yap)"""
    from main import get_db, Member
    db = next(get_db())
    
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.customer_id == customer_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Üye bulunamadı")
    
    member.status = "Pasif"
    member.leave_date = date.today()
    db.commit()
    
    return {"success": True}

# ==================== INCOMES ====================

@router.get("/incomes")
def list_incomes(
    customer_id: str = Depends(get_customer_id),
    year: int = 2025,
    category: Optional[str] = None,
    db: Session = Depends(lambda: None)
):
    """Gelir listesi"""
    from main import get_db, Income
    db = next(get_db())
    
    query = db.query(Income).filter(
        Income.customer_id == customer_id,
        Income.fiscal_year == year
    )
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

@router.post("/incomes")
def create_income(
    data: IncomeCreate,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Yeni gelir ekle"""
    from main import get_db, Income
    db = next(get_db())
    
    income_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    
    income = Income(
        id=uuid.uuid4(),
        customer_id=customer_id,
        date=income_date,
        category=data.category,
        amount=data.amount,
        description=data.description,
        cash_account=data.cash_account,
        receipt_no=data.receipt_no,
        fiscal_year=income_date.year
    )
    
    db.add(income)
    db.commit()
    
    return {"success": True, "id": str(income.id)}

@router.put("/incomes/{income_id}")
def update_income(
    income_id: str,
    data: IncomeCreate,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Gelir güncelle"""
    from main import get_db, Income
    db = next(get_db())
    
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.customer_id == customer_id
    ).first()
    
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

@router.delete("/incomes/{income_id}")
def delete_income(
    income_id: str,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Gelir sil"""
    from main import get_db, Income
    db = next(get_db())
    
    income = db.query(Income).filter(
        Income.id == income_id,
        Income.customer_id == customer_id
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Gelir bulunamadı")
    
    db.delete(income)
    db.commit()
    
    return {"success": True}

# ==================== EXPENSES ====================

@router.get("/expenses")
def list_expenses(
    customer_id: str = Depends(get_customer_id),
    year: int = 2025,
    category: Optional[str] = None,
    db: Session = Depends(lambda: None)
):
    """Gider listesi"""
    from main import get_db, Expense
    db = next(get_db())
    
    query = db.query(Expense).filter(
        Expense.customer_id == customer_id,
        Expense.fiscal_year == year
    )
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

@router.post("/expenses")
def create_expense(
    data: ExpenseCreate,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Yeni gider ekle"""
    from main import get_db, Expense
    db = next(get_db())
    
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
        invoice_no=data.invoice_no,
        fiscal_year=expense_date.year
    )
    
    db.add(expense)
    db.commit()
    
    return {"success": True, "id": str(expense.id)}

@router.put("/expenses/{expense_id}")
def update_expense(
    expense_id: str,
    data: ExpenseCreate,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Gider güncelle"""
    from main import get_db, Expense
    db = next(get_db())
    
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.customer_id == customer_id
    ).first()
    
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

@router.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: str,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Gider sil"""
    from main import get_db, Expense
    db = next(get_db())
    
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.customer_id == customer_id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    
    db.delete(expense)
    db.commit()
    
    return {"success": True}

# ==================== DUES ====================

@router.get("/dues")
def list_dues(
    customer_id: str = Depends(get_customer_id),
    year: int = 2025,
    db: Session = Depends(lambda: None)
):
    """Aidat takip listesi"""
    from main import get_db, Due, Member
    db = next(get_db())
    
    # Üyeleri al
    members = db.query(Member).filter(
        Member.customer_id == customer_id,
        Member.status == "Aktif"
    ).all()
    
    dues_list = []
    total_expected = 0
    total_collected = 0
    
    for member in members:
        # Bu üyenin bu yıl aidatı var mı?
        due = db.query(Due).filter(
            Due.customer_id == customer_id,
            Due.member_id == member.id,
            Due.year == year
        ).first()
        
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
        "stats": {
            "expected": total_expected,
            "collected": total_collected,
            "remaining": total_expected - total_collected
        }
    }

@router.post("/dues/payment")
def pay_due(
    data: DuePayment,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Aidat ödemesi kaydet"""
    from main import get_db, Due, Income
    db = next(get_db())
    
    due = db.query(Due).filter(
        Due.id == data.due_id,
        Due.customer_id == customer_id
    ).first()
    
    if not due:
        raise HTTPException(status_code=404, detail="Aidat kaydı bulunamadı")
    
    # Aidat güncelle
    due.paid_amount = (float(due.paid_amount) if due.paid_amount else 0) + data.amount
    if due.paid_amount >= float(due.yearly_amount):
        due.status = "Tamamlandı"
    else:
        due.status = "Kısmi"
    
    # Gelir kaydı oluştur
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

# ==================== CASH ACCOUNTS ====================

@router.get("/cash-accounts")
def list_cash_accounts(
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Kasa hesapları"""
    from main import get_db, CashAccount
    db = next(get_db())
    
    accounts = db.query(CashAccount).filter(
        CashAccount.customer_id == customer_id
    ).all()
    
    return {
        "accounts": [
            {
                "id": str(a.id),
                "name": a.name,
                "type": a.account_type,
                "balance": float(a.balance) if a.balance else 0
            }
            for a in accounts
        ]
    }

# ==================== SETTINGS ====================

@router.get("/settings")
def get_settings(
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Ayarları getir"""
    from main import get_db, Setting
    db = next(get_db())
    
    settings = db.query(Setting).filter(
        Setting.customer_id == customer_id
    ).all()
    
    result = {}
    for s in settings:
        result[s.key] = s.value
    
    return result

@router.put("/settings")
def update_settings(
    data: SettingsUpdate,
    customer_id: str = Depends(get_customer_id),
    db: Session = Depends(lambda: None)
):
    """Ayarları güncelle"""
    from main import get_db, Setting
    db = next(get_db())
    
    for key, value in data.dict(exclude_none=True).items():
        setting = db.query(Setting).filter(
            Setting.customer_id == customer_id,
            Setting.key == key
        ).first()
        
        if setting:
            setting.value = str(value)
        else:
            setting = Setting(
                id=uuid.uuid4(),
                customer_id=customer_id,
                key=key,
                value=str(value)
            )
            db.add(setting)
    
    db.commit()
    
    return {"success": True}
