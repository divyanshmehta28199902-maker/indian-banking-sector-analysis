-- ============================================================
-- PROJECT 3: Indian Banking Sector Financial Analysis
-- Database Schema | PostgreSQL / SQLite Compatible
-- ============================================================

-- 1. Banks master table
CREATE TABLE IF NOT EXISTS banks (
    bank_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name       TEXT NOT NULL,
    ticker          TEXT NOT NULL UNIQUE,
    bank_type       TEXT CHECK(bank_type IN ('PSU','Private','Small Finance','Payment','Foreign')),
    headquarter     TEXT,
    founded_year    INTEGER,
    listed_exchange TEXT CHECK(listed_exchange IN ('NSE','BSE','Both')),
    market_segment  TEXT CHECK(market_segment IN ('Large Cap','Mid Cap','Small Cap')),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Quarterly financial results
CREATE TABLE IF NOT EXISTS quarterly_financials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id             INTEGER NOT NULL REFERENCES banks(bank_id),
    fiscal_year         INTEGER NOT NULL,   -- e.g. 2024 = FY2024
    quarter             TEXT NOT NULL CHECK(quarter IN ('Q1','Q2','Q3','Q4')),

    -- Income Statement (in INR Crores)
    net_interest_income     REAL,   -- NII
    other_income            REAL,
    total_income            REAL,
    operating_expenses      REAL,
    provisions_contingencies REAL,
    profit_before_tax       REAL,
    tax_expense             REAL,
    net_profit              REAL,

    -- Balance Sheet (in INR Crores)
    total_assets            REAL,
    total_deposits          REAL,
    total_advances          REAL,
    total_investments       REAL,
    net_worth               REAL,
    borrowings              REAL,

    -- Asset Quality
    gross_npa_amount        REAL,
    net_npa_amount          REAL,
    gross_npa_pct           REAL,   -- %
    net_npa_pct             REAL,   -- %
    provision_coverage_ratio REAL,  -- PCR %
    slippage_ratio          REAL,   -- %

    -- Capital Adequacy
    capital_adequacy_ratio  REAL,   -- CAR / CRAR %
    tier1_capital_ratio     REAL,
    tier2_capital_ratio     REAL,

    -- Key Ratios
    return_on_assets        REAL,   -- RoA %
    return_on_equity        REAL,   -- RoE %
    net_interest_margin     REAL,   -- NIM %
    cost_to_income_ratio    REAL,   -- %
    credit_deposit_ratio    REAL,   -- CD Ratio %
    book_value_per_share    REAL,
    earnings_per_share      REAL,
    price_to_book           REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bank_id, fiscal_year, quarter)
);

-- 3. Annual financials (aggregated + extra YoY fields)
CREATE TABLE IF NOT EXISTS annual_financials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id         INTEGER NOT NULL REFERENCES banks(bank_id),
    fiscal_year     INTEGER NOT NULL,

    -- Aggregated P&L
    net_interest_income     REAL,
    total_income            REAL,
    net_profit              REAL,
    total_assets            REAL,
    total_deposits          REAL,
    total_advances          REAL,
    net_worth               REAL,

    -- Growth rates (YoY %)
    nii_growth_pct          REAL,
    profit_growth_pct       REAL,
    advances_growth_pct     REAL,
    deposit_growth_pct      REAL,

    -- Key ratios
    gross_npa_pct           REAL,
    net_npa_pct             REAL,
    capital_adequacy_ratio  REAL,
    return_on_assets        REAL,
    return_on_equity        REAL,
    net_interest_margin     REAL,
    cost_to_income_ratio    REAL,

    UNIQUE(bank_id, fiscal_year)
);

-- 4. Stock price data
CREATE TABLE IF NOT EXISTS stock_prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id     INTEGER NOT NULL REFERENCES banks(bank_id),
    price_date  DATE NOT NULL,
    open_price  REAL,
    high_price  REAL,
    low_price   REAL,
    close_price REAL,
    adj_close   REAL,
    volume      INTEGER,
    UNIQUE(bank_id, price_date)
);

-- 5. Sector aggregate benchmarks
CREATE TABLE IF NOT EXISTS sector_benchmarks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year     INTEGER NOT NULL,
    quarter         TEXT,
    bank_type       TEXT,   -- 'PSU','Private','All'
    avg_gross_npa   REAL,
    avg_net_npa     REAL,
    avg_car         REAL,
    avg_roa         REAL,
    avg_roe         REAL,
    avg_nim         REAL,
    avg_cir         REAL,
    total_credit_growth REAL,
    total_deposit_growth REAL
);

-- ============================================================
-- VIEWS for Power BI / Dashboard consumption
-- ============================================================

-- V1: Latest quarter snapshot per bank
CREATE VIEW IF NOT EXISTS v_latest_quarter AS
SELECT
    b.bank_name,
    b.ticker,
    b.bank_type,
    b.market_segment,
    q.fiscal_year,
    q.quarter,
    q.net_profit,
    q.net_interest_income,
    q.gross_npa_pct,
    q.net_npa_pct,
    q.capital_adequacy_ratio,
    q.return_on_assets,
    q.return_on_equity,
    q.net_interest_margin,
    q.cost_to_income_ratio,
    q.price_to_book
FROM quarterly_financials q
JOIN banks b ON b.bank_id = q.bank_id
WHERE (q.bank_id, q.fiscal_year, q.quarter) IN (
    SELECT bank_id, MAX(fiscal_year), quarter
    FROM quarterly_financials
    GROUP BY bank_id
);

-- V2: NPA trend view
CREATE VIEW IF NOT EXISTS v_npa_trend AS
SELECT
    b.bank_name,
    b.bank_type,
    q.fiscal_year,
    q.quarter,
    q.gross_npa_pct,
    q.net_npa_pct,
    q.provision_coverage_ratio,
    q.gross_npa_amount
FROM quarterly_financials q
JOIN banks b ON b.bank_id = q.bank_id
ORDER BY b.bank_name, q.fiscal_year, q.quarter;

-- V3: Profitability comparison
CREATE VIEW IF NOT EXISTS v_profitability AS
SELECT
    b.bank_name,
    b.bank_type,
    a.fiscal_year,
    a.net_profit,
    a.return_on_assets,
    a.return_on_equity,
    a.net_interest_margin,
    a.profit_growth_pct
FROM annual_financials a
JOIN banks b ON b.bank_id = a.bank_id
ORDER BY a.fiscal_year DESC, a.net_profit DESC;

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_qf_bank_year ON quarterly_financials(bank_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_sp_date ON stock_prices(price_date);
CREATE INDEX IF NOT EXISTS idx_banks_type ON banks(bank_type);
