-- BADER PostgreSQL Database Schema v5.0
-- Desktop ve Web Entegrasyonu için Tam Şema

-- UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== MÜŞTERİLER ====================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    api_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    plan VARCHAR(20) DEFAULT 'basic' CHECK (plan IN ('demo', 'basic', 'pro', 'enterprise')),
    max_users INTEGER DEFAULT 5,
    max_members INTEGER DEFAULT 500,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at DATE,
    features JSONB DEFAULT '["ocr", "sync", "backup"]',
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== KULLANICILAR ====================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('member', 'staff', 'accountant', 'manager', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, username)
);

-- ==================== ÜYELER ====================
CREATE TABLE IF NOT EXISTS members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    member_no VARCHAR(50),
    full_name VARCHAR(255) NOT NULL,
    tc_no VARCHAR(11),
    phone VARCHAR(50),
    phone2 VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    district VARCHAR(100),
    birth_date DATE,
    gender VARCHAR(20),
    occupation VARCHAR(150),
    membership_type VARCHAR(30) DEFAULT 'Asil',
    membership_fee DECIMAL(10,2) DEFAULT 0,
    join_date DATE DEFAULT CURRENT_DATE,
    leave_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'passive', 'left', 'deceased')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, member_no)
);

-- ==================== GELİRLER ====================
CREATE TABLE IF NOT EXISTS incomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE SET NULL,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    receipt_no VARCHAR(50),
    cash_account VARCHAR(100) DEFAULT 'Ana Kasa',
    fiscal_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== GİDERLER ====================
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    invoice_no VARCHAR(50),
    vendor VARCHAR(255),
    cash_account VARCHAR(100) DEFAULT 'Ana Kasa',
    fiscal_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== KASALAR ====================
CREATE TABLE IF NOT EXISTS cash_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) DEFAULT 'cash' CHECK (type IN ('cash', 'bank', 'pos')),
    balance DECIMAL(12,2) DEFAULT 0,
    bank_name VARCHAR(100),
    iban VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, name)
);

-- ==================== AİDATLAR ====================
CREATE TABLE IF NOT EXISTS dues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    amount DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    paid_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'partial', 'paid', 'waived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, member_id, year, month)
);

-- ==================== İNDEKSLER ====================
CREATE INDEX IF NOT EXISTS idx_members_customer ON members(customer_id);
CREATE INDEX IF NOT EXISTS idx_members_status ON members(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_incomes_customer ON incomes(customer_id);
CREATE INDEX IF NOT EXISTS idx_incomes_year ON incomes(customer_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_expenses_customer ON expenses(customer_id);
CREATE INDEX IF NOT EXISTS idx_expenses_year ON expenses(customer_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_dues_customer ON dues(customer_id);
CREATE INDEX IF NOT EXISTS idx_dues_member ON dues(member_id);

-- ==================== DEMO VERİ ====================
INSERT INTO customers (customer_id, api_key, name, email, plan, max_users, max_members, expires_at, features)
VALUES (
    'BADER-2024-DEMO-0001',
    'bader_api_key_2024_secure_demo',
    'Bader Bingöl Yardımlaşma Dayanışma Derneği',
    'info@baderbingol.org',
    'pro',
    10,
    1000,
    '2026-12-31',
    '["ocr", "sync", "backup", "reports", "multi_user"]'
) ON CONFLICT (customer_id) DO NOTHING;

-- Admin kullanıcı (şifre: admin123 - sha256)
INSERT INTO users (customer_id, username, password_hash, full_name, role)
VALUES (
    'BADER-2024-DEMO-0001',
    'admin',
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
    'Sistem Yöneticisi',
    'admin'
) ON CONFLICT (customer_id, username) DO NOTHING;

-- Ana Kasa
INSERT INTO cash_accounts (customer_id, name, type, balance)
VALUES ('BADER-2024-DEMO-0001', 'Ana Kasa', 'cash', 0)
ON CONFLICT (customer_id, name) DO NOTHING;
