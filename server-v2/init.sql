-- BADER PostgreSQL Initial Schema
-- Otomatik olarak container başlatıldığında çalışır

-- UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== MÜŞTERİLER (LİSANS SAHİPLERİ) ====================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    api_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    plan VARCHAR(20) DEFAULT 'basic' CHECK (plan IN ('demo', 'basic', 'pro', 'enterprise')),
    max_users INTEGER DEFAULT 5,
    max_members INTEGER DEFAULT 500,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at DATE,
    features JSONB DEFAULT '["ocr", "sync", "backup"]',
    settings JSONB DEFAULT '{}',
    last_seen_at TIMESTAMP,
    device_info JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== KULLANICILAR (HER MÜŞTERİ İÇİN) ====================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('member', 'staff', 'accountant', 'manager', 'admin')),
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    auth_token VARCHAR(255),
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, username)
);

-- ==================== ÜYELER ====================
CREATE TABLE IF NOT EXISTS members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    member_no INTEGER,
    full_name VARCHAR(255) NOT NULL,
    tc_no VARCHAR(11),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    birth_date DATE,
    join_date DATE DEFAULT CURRENT_DATE,
    leave_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'passive', 'left', 'deceased')),
    membership_fee DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    extra_data JSONB DEFAULT '{}',
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
    currency VARCHAR(3) DEFAULT 'TRY',
    date DATE NOT NULL,
    description TEXT,
    receipt_no VARCHAR(50),
    cash_account VARCHAR(100) DEFAULT 'Ana Kasa',
    document_path VARCHAR(500),
    fiscal_year INTEGER,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== GİDERLER ====================
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'TRY',
    date DATE NOT NULL,
    description TEXT,
    invoice_no VARCHAR(50),
    vendor VARCHAR(255),
    cash_account VARCHAR(100) DEFAULT 'Ana Kasa',
    document_path VARCHAR(500),
    fiscal_year INTEGER,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== KASALAR ====================
CREATE TABLE IF NOT EXISTS cash_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) DEFAULT 'cash' CHECK (type IN ('cash', 'bank', 'pos')),
    currency VARCHAR(3) DEFAULT 'TRY',
    balance DECIMAL(12,2) DEFAULT 0,
    bank_name VARCHAR(100),
    iban VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, name)
);

-- ==================== VİRMANLAR ====================
CREATE TABLE IF NOT EXISTS transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    from_account VARCHAR(100) NOT NULL,
    to_account VARCHAR(100) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    receipt_no VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, member_id, year, month)
);

-- ==================== BELGELER (OCR) ====================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    submitted_by UUID NOT NULL REFERENCES users(id),
    document_type VARCHAR(50) DEFAULT 'invoice',
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    ocr_text TEXT,
    ocr_data JSONB,
    suggested_type VARCHAR(20),
    suggested_category VARCHAR(50),
    suggested_amount DECIMAL(12,2),
    suggested_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewing', 'approved', 'rejected', 'deleted')),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    approved_data JSONB,
    linked_record_type VARCHAR(20),
    linked_record_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== UYGULAMA VERSİYONLARI ====================
CREATE TABLE IF NOT EXISTS app_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(20) UNIQUE NOT NULL,
    platform VARCHAR(20) DEFAULT 'all' CHECK (platform IN ('all', 'macos', 'windows', 'linux')),
    download_url VARCHAR(500),
    file_path VARCHAR(500),
    file_size BIGINT,
    changelog TEXT,
    min_required_version VARCHAR(20),
    is_critical BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== AKTİVASYON LOGLARI ====================
CREATE TABLE IF NOT EXISTS activation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50),
    device_info JSONB,
    ip_address VARCHAR(50),
    success BOOLEAN,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== ETKİNLİKLER ====================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(50),
    location VARCHAR(255),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    budget DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'ongoing', 'completed', 'cancelled')),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== TOPLANTILAR ====================
CREATE TABLE IF NOT EXISTS meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    meeting_date TIMESTAMP NOT NULL,
    location VARCHAR(255),
    agenda TEXT,
    minutes TEXT,
    attendees JSONB DEFAULT '[]',
    decisions JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== AYARLAR ====================
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, key)
);

-- ==================== İNDEKSLER ====================
CREATE INDEX IF NOT EXISTS idx_members_customer ON members(customer_id);
CREATE INDEX IF NOT EXISTS idx_members_status ON members(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_incomes_customer ON incomes(customer_id);
CREATE INDEX IF NOT EXISTS idx_incomes_date ON incomes(customer_id, date);
CREATE INDEX IF NOT EXISTS idx_incomes_year ON incomes(customer_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_expenses_customer ON expenses(customer_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(customer_id, date);
CREATE INDEX IF NOT EXISTS idx_dues_member ON dues(member_id);
CREATE INDEX IF NOT EXISTS idx_dues_status ON dues(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_users_customer ON users(customer_id);

-- ==================== DEMO VERİLER ====================
-- Demo Müşteri 1 - Aktif Pro
INSERT INTO customers (customer_id, api_key, name, email, phone, plan, max_users, max_members, expires_at, features, address)
VALUES (
    'BADER-2024-DEMO-0001',
    'bader_api_key_2024_secure_demo',
    'Ankara Yazılımcılar Derneği',
    'info@ankarayazilimcilar.org',
    '0312 555 1234',
    'pro',
    20,
    2000,
    '2026-12-31',
    '["ocr", "sync", "backup", "reports", "multi_user"]',
    'Çankaya, Ankara'
) ON CONFLICT (customer_id) DO NOTHING;

-- Demo Müşteri 2 - Basic
INSERT INTO customers (customer_id, api_key, name, email, phone, plan, max_users, max_members, expires_at, features)
VALUES (
    'BADER-2024-DEMO-0002',
    'bader_api_key_basic_test_2024',
    'İstanbul Spor Kulübü Derneği',
    'iletisim@istanbulspor.org',
    '0212 444 5678',
    'basic',
    5,
    500,
    '2025-06-30',
    '["ocr", "sync"]'
) ON CONFLICT (customer_id) DO NOTHING;

-- Demo Müşteri 3 - Enterprise
INSERT INTO customers (customer_id, api_key, name, email, phone, plan, max_users, max_members, expires_at, features, address)
VALUES (
    'BADER-2024-DEMO-0003',
    'bader_api_key_enterprise_2024',
    'Türkiye Doğa Koruma Vakfı',
    'bilgi@dogakoruma.org.tr',
    '0216 333 9999',
    'enterprise',
    100,
    10000,
    '2027-12-31',
    '["ocr", "sync", "backup", "reports", "multi_user", "api_access", "white_label"]',
    'Kadıköy, İstanbul'
) ON CONFLICT (customer_id) DO NOTHING;

-- Demo Kullanıcılar (şifreler plain text olarak girilecek, ilk login'de bcrypt'e dönecek)
INSERT INTO users (customer_id, username, password_hash, full_name, email, role, permissions)
VALUES 
    -- Dernek 1 kullanıcıları
    ('BADER-2024-DEMO-0001', 'admin', 'admin123', 'Ali Yönetici', 'ali@ankarayazilimcilar.org', 'admin', '["*"]'),
    ('BADER-2024-DEMO-0001', 'muhasebe', 'muhasebe123', 'Fatma Sayman', 'fatma@ankarayazilimcilar.org', 'accountant', '["income", "expense", "reports"]'),
    ('BADER-2024-DEMO-0001', 'yonetici', 'yonetici123', 'Mehmet Yazıcı', 'mehmet@ankarayazilimcilar.org', 'manager', '["members", "events"]'),
    ('BADER-2024-DEMO-0001', 'uye', 'uye123', 'Ayşe Üye', 'ayse@gmail.com', 'member', '["view_own"]'),
    
    -- Dernek 2 kullanıcıları
    ('BADER-2024-DEMO-0002', 'admin', 'admin123', 'Hasan Başkan', 'hasan@istanbulspor.org', 'admin', '["*"]'),
    
    -- Dernek 3 kullanıcıları
    ('BADER-2024-DEMO-0003', 'admin', 'admin123', 'Zeynep Müdür', 'zeynep@dogakoruma.org.tr', 'admin', '["*"]')
ON CONFLICT (customer_id, username) DO NOTHING;

-- Demo Kasalar
INSERT INTO cash_accounts (customer_id, name, type, currency, balance)
VALUES 
    ('BADER-2024-DEMO-0001', 'Ana Kasa', 'cash', 'TRY', 15420.50),
    ('BADER-2024-DEMO-0001', 'Vakıfbank TL', 'bank', 'TRY', 84350.00),
    ('BADER-2024-DEMO-0001', 'Vakıfbank USD', 'bank', 'USD', 1250.00),
    ('BADER-2024-DEMO-0002', 'Kasa', 'cash', 'TRY', 5200.00),
    ('BADER-2024-DEMO-0002', 'Ziraat Bankası', 'bank', 'TRY', 22000.00),
    ('BADER-2024-DEMO-0003', 'Merkez Kasa', 'cash', 'TRY', 125000.00),
    ('BADER-2024-DEMO-0003', 'İş Bankası', 'bank', 'TRY', 850000.00)
ON CONFLICT (customer_id, name) DO NOTHING;

-- Demo Üyeler
INSERT INTO members (customer_id, member_no, full_name, email, phone, status, membership_fee)
VALUES
    ('BADER-2024-DEMO-0001', 1, 'Ahmet Kaya', 'ahmet@email.com', '0532 111 2233', 'active', 250.00),
    ('BADER-2024-DEMO-0001', 2, 'Elif Demir', 'elif@email.com', '0533 222 3344', 'active', 500.00),
    ('BADER-2024-DEMO-0001', 3, 'Can Öztürk', 'can@email.com', '0534 333 4455', 'active', 100.00),
    ('BADER-2024-DEMO-0001', 4, 'Deniz Yılmaz', 'deniz@email.com', '0535 444 5566', 'passive', 250.00)
ON CONFLICT (customer_id, member_no) DO NOTHING;

-- Uygulama Versiyonları
INSERT INTO app_versions (version, platform, changelog, is_active, is_critical, min_required_version)
VALUES 
    ('1.0.0', 'all', 'İlk kararlı sürüm', TRUE, FALSE, NULL),
    ('1.0.1', 'all', 'Hata düzeltmeleri ve performans iyileştirmeleri', TRUE, FALSE, '1.0.0'),
    ('1.1.0', 'all', 'Yeni özellikler: OCR iyileştirmesi, Raporlar, Çoklu dil desteği', TRUE, FALSE, '1.0.0')
ON CONFLICT (version) DO NOTHING;

-- Trigger: updated_at otomatik güncelleme
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger'ları tablolara ekle
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', t, t);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;
