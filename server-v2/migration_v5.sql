-- =====================================================================
-- BADER V5.0 Migration Script - Desktop Parity
-- Masaüstü uygulaması ile tam uyumluluk için kapsamlı güncelleme
-- =====================================================================

-- ==================== 1. ÜYELER TABLOSU GENİŞLETME ====================

-- Yeni kolonlar ekleme
ALTER TABLE members ADD COLUMN IF NOT EXISTS phone2 VARCHAR(50);
ALTER TABLE members ADD COLUMN IF NOT EXISTS gender VARCHAR(20);
ALTER TABLE members ADD COLUMN IF NOT EXISTS birth_place VARCHAR(100);
ALTER TABLE members ADD COLUMN IF NOT EXISTS blood_type VARCHAR(10);
ALTER TABLE members ADD COLUMN IF NOT EXISTS marital_status VARCHAR(30);
ALTER TABLE members ADD COLUMN IF NOT EXISTS child_count INTEGER DEFAULT 0;
ALTER TABLE members ADD COLUMN IF NOT EXISTS education VARCHAR(100);
ALTER TABLE members ADD COLUMN IF NOT EXISTS occupation VARCHAR(150);
ALTER TABLE members ADD COLUMN IF NOT EXISTS workplace VARCHAR(200);
ALTER TABLE members ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE members ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE members ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(150);
ALTER TABLE members ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20);
ALTER TABLE members ADD COLUMN IF NOT EXISTS membership_type VARCHAR(30) DEFAULT 'Asil';
ALTER TABLE members ADD COLUMN IF NOT EXISTS special_fee DECIMAL(10,2);
ALTER TABLE members ADD COLUMN IF NOT EXISTS fee_discount DECIMAL(5,2) DEFAULT 0;
ALTER TABLE members ADD COLUMN IF NOT EXISTS referrer_id UUID REFERENCES members(id);
ALTER TABLE members ADD COLUMN IF NOT EXISTS leave_reason TEXT;
ALTER TABLE members ADD COLUMN IF NOT EXISTS tc_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE members ADD COLUMN IF NOT EXISTS photo_path VARCHAR(500);

-- ==================== 2. AİDAT ÖDEMELERİ TABLOSU ====================

CREATE TABLE IF NOT EXISTS due_payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    due_id UUID NOT NULL REFERENCES dues(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_type VARCHAR(50) DEFAULT 'Nakit',
    receipt_no VARCHAR(100),
    description TEXT,
    cash_account_id UUID REFERENCES cash_accounts(id),
    income_id UUID REFERENCES incomes(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_due_payments_due ON due_payments(due_id);
CREATE INDEX IF NOT EXISTS idx_due_payments_customer ON due_payments(customer_id);

-- ==================== 3. GELİR TABLOSU GENİŞLETME ====================

ALTER TABLE incomes ADD COLUMN IF NOT EXISTS due_id UUID REFERENCES dues(id);
ALTER TABLE incomes ADD COLUMN IF NOT EXISTS due_payment_id UUID REFERENCES due_payments(id);
ALTER TABLE incomes ADD COLUMN IF NOT EXISTS collected_by VARCHAR(150);
ALTER TABLE incomes ADD COLUMN IF NOT EXISTS payment_type VARCHAR(50) DEFAULT 'Nakit';
ALTER TABLE incomes ADD COLUMN IF NOT EXISTS belongs_to_year INTEGER;
ALTER TABLE incomes ADD COLUMN IF NOT EXISTS accrual_status VARCHAR(30) DEFAULT 'NORMAL';
ALTER TABLE incomes ADD COLUMN IF NOT EXISTS multi_payment_group VARCHAR(100);
ALTER TABLE incomes ADD COLUMN IF NOT EXISTS cash_account_id UUID REFERENCES cash_accounts(id);

-- ==================== 4. GİDER TABLOSU GENİŞLETME ====================

ALTER TABLE expenses ADD COLUMN IF NOT EXISTS paid_by VARCHAR(150);
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS payment_type VARCHAR(50) DEFAULT 'Nakit';
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS belongs_to_year INTEGER;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS accrual_status VARCHAR(30) DEFAULT 'NORMAL';
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS cash_account_id UUID REFERENCES cash_accounts(id);

-- ==================== 5. KASA TABLOSU GENİŞLETME ====================

ALTER TABLE cash_accounts ADD COLUMN IF NOT EXISTS opening_balance DECIMAL(12,2) DEFAULT 0;
ALTER TABLE cash_accounts ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE cash_accounts ADD COLUMN IF NOT EXISTS free_balance DECIMAL(12,2) DEFAULT 0;
ALTER TABLE cash_accounts ADD COLUMN IF NOT EXISTS accrual_total DECIMAL(12,2) DEFAULT 0;
ALTER TABLE cash_accounts ADD COLUMN IF NOT EXISTS last_carryover_date DATE;

-- ==================== 6. ALACAKLAR ====================

CREATE TABLE IF NOT EXISTS receivables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    receivable_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    person_org VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    member_id UUID REFERENCES members(id),
    total_amount DECIMAL(12,2) NOT NULL,
    collected_amount DECIMAL(12,2) DEFAULT 0,
    remaining_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TRY',
    receivable_date DATE NOT NULL,
    due_date DATE,
    status VARCHAR(30) DEFAULT 'Bekliyor',
    income_id UUID REFERENCES incomes(id),
    bond_no VARCHAR(100),
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_receivables_customer ON receivables(customer_id);
CREATE INDEX IF NOT EXISTS idx_receivables_status ON receivables(customer_id, status);

-- ==================== 7. ALACAK TAHSİLATLARI ====================

CREATE TABLE IF NOT EXISTS receivable_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    receivable_id UUID NOT NULL REFERENCES receivables(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    collection_date DATE NOT NULL,
    cash_account_id UUID REFERENCES cash_accounts(id),
    income_id UUID REFERENCES incomes(id),
    payment_method VARCHAR(50) DEFAULT 'Nakit',
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recv_collections_recv ON receivable_collections(receivable_id);

-- ==================== 8. VERECEKLER ====================

CREATE TABLE IF NOT EXISTS payables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    payable_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    person_org VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    member_id UUID REFERENCES members(id),
    total_amount DECIMAL(12,2) NOT NULL,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    remaining_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TRY',
    payable_date DATE NOT NULL,
    due_date DATE,
    status VARCHAR(30) DEFAULT 'Bekliyor',
    expense_id UUID REFERENCES expenses(id),
    bond_no VARCHAR(100),
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payables_customer ON payables(customer_id);
CREATE INDEX IF NOT EXISTS idx_payables_status ON payables(customer_id, status);

-- ==================== 9. VERECEK ÖDEMELERİ ====================

CREATE TABLE IF NOT EXISTS payable_payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    payable_id UUID NOT NULL REFERENCES payables(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    payment_date DATE NOT NULL,
    cash_account_id UUID REFERENCES cash_accounts(id),
    expense_id UUID REFERENCES expenses(id),
    payment_method VARCHAR(50) DEFAULT 'Nakit',
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pay_payments_pay ON payable_payments(payable_id);

-- ==================== 10. TAHAKKUKLAR ====================

CREATE TABLE IF NOT EXISTS accruals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER,
    accrual_type VARCHAR(30) NOT NULL, -- GELIR/GIDER
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    cash_account_id UUID REFERENCES cash_accounts(id),
    status VARCHAR(30) DEFAULT 'BEKLIYOR', -- BEKLIYOR/GERCEKLESTI/IPTAL
    realized_date DATE,
    source_type VARCHAR(50), -- dues/income/expense
    source_id UUID,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_accruals_customer ON accruals(customer_id);
CREATE INDEX IF NOT EXISTS idx_accruals_year ON accruals(customer_id, year);
CREATE INDEX IF NOT EXISTS idx_accruals_status ON accruals(customer_id, status);

-- ==================== 11. DEVİR İŞLEMLERİ ====================

CREATE TABLE IF NOT EXISTS carryover_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    carryover_date DATE NOT NULL,
    cash_account_id UUID REFERENCES cash_accounts(id),
    cash_account_name VARCHAR(100),
    previous_balance DECIMAL(12,2) DEFAULT 0,
    carryover_balance DECIMAL(12,2) DEFAULT 0,
    free_balance DECIMAL(12,2) DEFAULT 0,
    accrual_balance DECIMAL(12,2) DEFAULT 0,
    description TEXT,
    created_by VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_carryover_customer ON carryover_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_carryover_year ON carryover_transactions(customer_id, year);

-- ==================== 12. BÜTÇE PLANLARI ====================

CREATE TABLE IF NOT EXISTS budget_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER,
    category VARCHAR(100) NOT NULL,
    budget_type VARCHAR(20) NOT NULL, -- GELIR/GIDER
    planned_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    actual_amount DECIMAL(12,2) DEFAULT 0,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, year, month, category, budget_type)
);

CREATE INDEX IF NOT EXISTS idx_budget_customer ON budget_plans(customer_id);
CREATE INDEX IF NOT EXISTS idx_budget_year ON budget_plans(customer_id, year);

-- ==================== 13. ETKİNLİK KATILIMCILARI ====================

CREATE TABLE IF NOT EXISTS event_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id),
    participant_name VARCHAR(255) NOT NULL,
    participant_count INTEGER DEFAULT 1,
    attendance_status VARCHAR(30) DEFAULT 'Bekliyor',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_event_parts_event ON event_participants(event_id);

-- ==================== 14. ETKİNLİK TABLOSU GENİŞLETME ====================

ALTER TABLE events ADD COLUMN IF NOT EXISTS event_category VARCHAR(100);
ALTER TABLE events ADD COLUMN IF NOT EXISTS expected_participants INTEGER DEFAULT 0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS actual_participants INTEGER DEFAULT 0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS expected_income DECIMAL(12,2) DEFAULT 0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS expected_expense DECIMAL(12,2) DEFAULT 0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS actual_income DECIMAL(12,2) DEFAULT 0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS actual_expense DECIMAL(12,2) DEFAULT 0;
ALTER TABLE events ADD COLUMN IF NOT EXISTS responsible_member_id UUID REFERENCES members(id);
ALTER TABLE events ADD COLUMN IF NOT EXISTS end_time TIMESTAMP;

-- ==================== 15. TOPLANTI TABLOSU GENİŞLETME ====================

ALTER TABLE meetings ADD COLUMN IF NOT EXISTS meeting_type VARCHAR(100);
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS start_time TIME;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS end_time TIME;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS outcome TEXT;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS next_meeting_date DATE;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS document_path VARCHAR(500);

-- ==================== 16. İŞLEM LOGLARI ====================

CREATE TABLE IF NOT EXISTS operation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    username VARCHAR(100),
    operation_type VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    description TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_op_logs_customer ON operation_logs(customer_id);
CREATE INDEX IF NOT EXISTS idx_op_logs_date ON operation_logs(created_at);

-- ==================== 17. KULLANICI YETKİLERİ GENİŞLETME ====================

ALTER TABLE users ADD COLUMN IF NOT EXISTS detailed_permissions JSONB DEFAULT '{
    "members": {"view": true, "add": false, "edit": false, "delete": false},
    "incomes": {"view": true, "add": false, "edit": false, "delete": false},
    "expenses": {"view": true, "add": false, "edit": false, "delete": false},
    "dues": {"view": true, "add": false, "edit": false, "delete": false},
    "cash_accounts": {"view": true, "add": false, "edit": false, "delete": false},
    "reports": {"view": true, "export": false},
    "settings": {"view": false, "edit": false},
    "users": {"view": false, "add": false, "edit": false, "delete": false}
}';

-- ==================== 18. GELİR KATEGORİLERİ ====================

CREATE TABLE IF NOT EXISTS income_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, name)
);

-- Varsayılan gelir kategorileri
INSERT INTO income_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'AİDAT', true, 1 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO income_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'BAĞIŞ', true, 2 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO income_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'KİRA', true, 3 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO income_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'ETKİNLİK', true, 4 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO income_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'DİĞER', true, 10 FROM customers ON CONFLICT DO NOTHING;

-- ==================== 19. GİDER KATEGORİLERİ ====================

CREATE TABLE IF NOT EXISTS expense_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, name)
);

-- Varsayılan gider kategorileri
INSERT INTO expense_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'ELEKTRİK', true, 1 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO expense_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'SU', true, 2 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO expense_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'DOĞALGAZ', true, 3 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO expense_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'KİRA', true, 4 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO expense_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'MALZEME', true, 5 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO expense_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'PERSONEL', true, 6 FROM customers ON CONFLICT DO NOTHING;
INSERT INTO expense_categories (customer_id, name, is_system, display_order) 
SELECT customer_id, 'DİĞER', true, 10 FROM customers ON CONFLICT DO NOTHING;

-- ==================== 20. MULTI-YEAR DUES TRACKING ====================

ALTER TABLE dues ADD COLUMN IF NOT EXISTS due_type VARCHAR(30) DEFAULT 'yearly'; -- yearly/monthly
ALTER TABLE dues ADD COLUMN IF NOT EXISTS belongs_to_year INTEGER;
ALTER TABLE dues ADD COLUMN IF NOT EXISTS accrual_status VARCHAR(30) DEFAULT 'NORMAL'; -- NORMAL/PESIN/GERIYE_DONUS
ALTER TABLE dues ADD COLUMN IF NOT EXISTS income_id UUID REFERENCES incomes(id);
ALTER TABLE dues ADD COLUMN IF NOT EXISTS multi_payment_group VARCHAR(100);

-- ==================== 21. KÖY MODÜLÜ ====================

-- Köy Kasaları
CREATE TABLE IF NOT EXISTS village_cash_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(30) DEFAULT 'cash',
    currency VARCHAR(10) DEFAULT 'TRY',
    balance DECIMAL(12,2) DEFAULT 0,
    opening_balance DECIMAL(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, name)
);

-- Köy Gelirleri
CREATE TABLE IF NOT EXISTS village_incomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TRY',
    date DATE NOT NULL,
    description TEXT,
    receipt_no VARCHAR(100),
    cash_account_id UUID REFERENCES village_cash_accounts(id),
    fiscal_year INTEGER,
    collected_by VARCHAR(150),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Köy Giderleri
CREATE TABLE IF NOT EXISTS village_expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TRY',
    date DATE NOT NULL,
    description TEXT,
    invoice_no VARCHAR(100),
    vendor VARCHAR(255),
    cash_account_id UUID REFERENCES village_cash_accounts(id),
    fiscal_year INTEGER,
    paid_by VARCHAR(150),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Köy Virmanları
CREATE TABLE IF NOT EXISTS village_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    from_account_id UUID REFERENCES village_cash_accounts(id),
    to_account_id UUID REFERENCES village_cash_accounts(id),
    amount DECIMAL(12,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Köy Gelir Kategorileri
CREATE TABLE IF NOT EXISTS village_income_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, name)
);

-- Köy Gider Kategorileri
CREATE TABLE IF NOT EXISTS village_expense_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, name)
);

-- ==================== 22. YENİ İNDEKSLER ====================

CREATE INDEX IF NOT EXISTS idx_members_name ON members(customer_id, full_name);
CREATE INDEX IF NOT EXISTS idx_members_tc ON members(customer_id, tc_no);
CREATE INDEX IF NOT EXISTS idx_members_membership_type ON members(customer_id, membership_type);
CREATE INDEX IF NOT EXISTS idx_incomes_due ON incomes(due_id);
CREATE INDEX IF NOT EXISTS idx_incomes_fiscal_year ON incomes(customer_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_expenses_fiscal_year ON expenses(customer_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_dues_multi_group ON dues(multi_payment_group);

-- ==================== MIGRATION TAMAMLANDI ====================
