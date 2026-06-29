"""
Project 3: Indian Banking Sector Financial Analysis
====================================================
Script 01 - Database Setup & Sample Data Generation
Generates realistic synthetic data for 10 major Indian banks (FY2020–FY2024)

Usage:
    python scripts/01_setup_database.py
"""

import sqlite3
import random
import math
import os
from datetime import date, timedelta

random.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'banking_sector.db')
SQL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'sql', 'schema.sql')

# ── Bank master data ─────────────────────────────────────────
BANKS = [
    # (name, ticker, type, HQ, founded, exchange, segment)
    ("State Bank of India",      "SBIN",    "PSU",     "Mumbai",    1955, "Both",  "Large Cap"),
    ("HDFC Bank",                "HDFCBANK","Private", "Mumbai",    1994, "Both",  "Large Cap"),
    ("ICICI Bank",               "ICICIBANK","Private","Mumbai",    1994, "Both",  "Large Cap"),
    ("Punjab National Bank",     "PNB",     "PSU",     "New Delhi", 1894, "Both",  "Large Cap"),
    ("Axis Bank",                "AXISBANK","Private", "Mumbai",    1993, "Both",  "Large Cap"),
    ("Kotak Mahindra Bank",      "KOTAKBANK","Private","Mumbai",    2003, "Both",  "Large Cap"),
    ("Bank of Baroda",           "BANKBARODA","PSU",   "Vadodara",  1908, "Both",  "Large Cap"),
    ("IndusInd Bank",            "INDUSINDBK","Private","Pune",     1994, "Both",  "Mid Cap"),
    ("Yes Bank",                 "YESBANK", "Private", "Mumbai",    2004, "Both",  "Mid Cap"),
    ("Federal Bank",             "FEDERALBNK","Private","Aluva",   1931, "Both",  "Mid Cap"),
]

# ── Realistic baseline parameters per bank ───────────────────
# Keys: base_assets(Cr), nim_base, roa_base, gnpa_base, car_base, profit_margin
BANK_PARAMS = {
    "SBIN":       dict(assets=5_000_000, nim=2.7, roa=0.55, gnpa=6.5, car=13.5, profit_margin=0.10),
    "HDFCBANK":   dict(assets=2_200_000, nim=4.1, roa=1.9,  gnpa=1.2, car=18.5, profit_margin=0.25),
    "ICICIBANK":  dict(assets=1_700_000, nim=3.7, roa=1.6,  gnpa=3.8, car=17.0, profit_margin=0.20),
    "PNB":        dict(assets=1_100_000, nim=2.9, roa=0.30, gnpa=12.0,car=13.0, profit_margin=0.05),
    "AXISBANK":   dict(assets=1_000_000, nim=3.5, roa=1.2,  gnpa=3.2, car=16.5, profit_margin=0.18),
    "KOTAKBANK":  dict(assets=600_000,   nim=4.5, roa=2.1,  gnpa=1.1, car=22.0, profit_margin=0.28),
    "BANKBARODA": dict(assets=1_300_000, nim=2.8, roa=0.40, gnpa=9.0, car=14.5, profit_margin=0.06),
    "INDUSINDBK": dict(assets=420_000,   nim=4.1, roa=1.5,  gnpa=2.4, car=17.5, profit_margin=0.20),
    "YESBANK":    dict(assets=250_000,   nim=2.5, roa=-0.5, gnpa=15.0,car=12.0, profit_margin=-0.05),
    "FEDERALBNK": dict(assets=230_000,   nim=3.2, roa=1.1,  gnpa=2.7, car=15.5, profit_margin=0.16),
}

FISCAL_YEARS = [2020, 2021, 2022, 2023, 2024]
QUARTERS     = ["Q1", "Q2", "Q3", "Q4"]


def noise(value: float, pct: float = 0.05) -> float:
    """Add ±pct% random noise to a value."""
    return value * (1 + random.uniform(-pct, pct))


def trend(base: float, fy: int, growth: float = 0.08) -> float:
    """Apply compounding growth from FY2020."""
    years = fy - 2020
    return base * math.pow(1 + growth, years)


def setup_database() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    with open(SQL_PATH) as f:
        conn.executescript(f.read())

    conn.commit()
    print(f"✅ Database created at {DB_PATH}")
    return conn


def insert_banks(conn: sqlite3.Connection) -> dict:
    """Insert bank master data. Returns {ticker: bank_id}."""
    cur = conn.cursor()
    bank_ids = {}
    for row in BANKS:
        cur.execute("""
            INSERT OR IGNORE INTO banks
                (bank_name, ticker, bank_type, headquarter, founded_year, listed_exchange, market_segment)
            VALUES (?,?,?,?,?,?,?)
        """, row)
        cur.execute("SELECT bank_id FROM banks WHERE ticker=?", (row[1],))
        bank_ids[row[1]] = cur.fetchone()[0]
    conn.commit()
    print(f"✅ Inserted {len(bank_ids)} banks")
    return bank_ids


def insert_quarterly_data(conn: sqlite3.Connection, bank_ids: dict):
    cur = conn.cursor()
    rows = 0

    for ticker, bank_id in bank_ids.items():
        p = BANK_PARAMS[ticker]

        for fy in FISCAL_YEARS:
            # Improve gradually (NPA falls, profitability rises post-2021)
            fy_offset    = fy - 2020
            npa_adj      = max(0.5, p["gnpa"] - fy_offset * 0.8) if ticker != "YESBANK" else p["gnpa"] + fy_offset * 0.5
            roa_adj      = p["roa"] + fy_offset * 0.05
            nim_adj      = p["nim"] + fy_offset * 0.03
            assets_trend = trend(p["assets"], fy)

            for q in QUARTERS:
                q_assets     = noise(assets_trend * 0.98)
                deposits     = noise(q_assets * 0.80)
                advances     = noise(q_assets * 0.65)
                investments  = noise(q_assets * 0.22)
                net_worth    = noise(q_assets * 0.08)

                nii          = noise(advances * nim_adj / 100 / 4)
                other_income = noise(nii * 0.25)
                total_income = nii + other_income
                opex         = noise(total_income * 0.45)
                gross_npa    = noise(advances * npa_adj / 100)
                provisions   = noise(gross_npa * 0.45)
                pbt          = total_income - opex - provisions
                tax          = max(0, pbt * 0.25)
                net_profit   = pbt - tax

                gnpa_pct     = noise(npa_adj, 0.02)
                nnpa_pct     = noise(gnpa_pct * 0.40, 0.05)
                pcr          = noise(70 if ticker not in ["YESBANK","PNB"] else 55, 0.03)

                cur.execute("""
                    INSERT OR IGNORE INTO quarterly_financials (
                        bank_id, fiscal_year, quarter,
                        net_interest_income, other_income, total_income,
                        operating_expenses, provisions_contingencies,
                        profit_before_tax, tax_expense, net_profit,
                        total_assets, total_deposits, total_advances,
                        total_investments, net_worth,
                        gross_npa_amount, net_npa_amount,
                        gross_npa_pct, net_npa_pct, provision_coverage_ratio,
                        capital_adequacy_ratio, tier1_capital_ratio,
                        return_on_assets, return_on_equity, net_interest_margin,
                        cost_to_income_ratio, credit_deposit_ratio,
                        book_value_per_share, earnings_per_share
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    bank_id, fy, q,
                    round(nii/1e2,2), round(other_income/1e2,2), round(total_income/1e2,2),
                    round(opex/1e2,2), round(provisions/1e2,2),
                    round(pbt/1e2,2), round(tax/1e2,2), round(net_profit/1e2,2),
                    round(q_assets/1e2,2), round(deposits/1e2,2), round(advances/1e2,2),
                    round(investments/1e2,2), round(net_worth/1e2,2),
                    round(gross_npa/1e2,2), round(gross_npa*0.40/1e2,2),
                    round(gnpa_pct,2), round(nnpa_pct,2), round(pcr,2),
                    round(noise(p["car"],0.03),2), round(noise(p["car"]*0.82,0.03),2),
                    round(roa_adj,2), round(noise(roa_adj*8,0.05),2), round(nim_adj,2),
                    round(opex/total_income*100,2), round(advances/deposits*100,2),
                    round(net_worth/1e4,2), round(net_profit/1e4,2),
                ))
                rows += 1

    conn.commit()
    print(f"✅ Inserted {rows} quarterly records")


def insert_annual_data(conn: sqlite3.Connection, bank_ids: dict):
    """Aggregate quarterly → annual and compute YoY growth."""
    cur = conn.cursor()

    for ticker, bank_id in bank_ids.items():
        prev = {}
        for fy in FISCAL_YEARS:
            cur.execute("""
                SELECT
                    SUM(net_interest_income), SUM(total_income), SUM(net_profit),
                    AVG(total_assets), AVG(total_deposits), AVG(total_advances), AVG(net_worth),
                    AVG(gross_npa_pct), AVG(net_npa_pct), AVG(capital_adequacy_ratio),
                    AVG(return_on_assets), AVG(return_on_equity),
                    AVG(net_interest_margin), AVG(cost_to_income_ratio)
                FROM quarterly_financials
                WHERE bank_id=? AND fiscal_year=?
            """, (bank_id, fy))
            row = cur.fetchone()
            if not row[0]:
                continue

            nii, tot_inc, profit, assets, dep, adv, nw, gnpa, nnpa, car, roa, roe, nim, cir = row

            def pct_growth(curr, key):
                if key in prev and prev[key] and prev[key] != 0:
                    return round((curr - prev[key]) / abs(prev[key]) * 100, 2)
                return None

            cur.execute("""
                INSERT OR IGNORE INTO annual_financials (
                    bank_id, fiscal_year,
                    net_interest_income, total_income, net_profit,
                    total_assets, total_deposits, total_advances, net_worth,
                    nii_growth_pct, profit_growth_pct, advances_growth_pct, deposit_growth_pct,
                    gross_npa_pct, net_npa_pct, capital_adequacy_ratio,
                    return_on_assets, return_on_equity, net_interest_margin, cost_to_income_ratio
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                bank_id, fy,
                round(nii,2), round(tot_inc,2), round(profit,2),
                round(assets,2), round(dep,2), round(adv,2), round(nw,2),
                pct_growth(nii,"nii"), pct_growth(profit,"profit"),
                pct_growth(adv,"adv"), pct_growth(dep,"dep"),
                round(gnpa,2), round(nnpa,2), round(car,2),
                round(roa,2), round(roe,2), round(nim,2), round(cir,2),
            ))
            prev = {"nii": nii, "profit": profit, "adv": adv, "dep": dep}

    conn.commit()
    print("✅ Annual data aggregated")


def insert_stock_prices(conn: sqlite3.Connection, bank_ids: dict):
    """Generate synthetic daily stock price data (2020-01-01 to 2024-12-31)."""
    BASE_PRICES = {
        "SBIN":500, "HDFCBANK":1400, "ICICIBANK":700, "PNB":50,
        "AXISBANK":700, "KOTAKBANK":1700, "BANKBARODA":150,
        "INDUSINDBK":1000, "YESBANK":15, "FEDERALBNK":130,
    }
    cur = conn.cursor()
    total = 0

    for ticker, bank_id in bank_ids.items():
        price = BASE_PRICES[ticker]
        d = date(2020, 1, 1)
        end = date(2024, 12, 31)

        while d <= end:
            if d.weekday() < 5:  # Mon-Fri only
                daily_ret = random.gauss(0.0004, 0.018)
                price = max(price * (1 + daily_ret), 1)
                high  = price * noise(1.01, 0.005)
                low   = price * noise(0.99, 0.005)
                vol   = int(random.randint(500_000, 10_000_000))

                cur.execute("""
                    INSERT OR IGNORE INTO stock_prices
                        (bank_id, price_date, open_price, high_price, low_price, close_price, adj_close, volume)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (bank_id, d.isoformat(), round(price,2), round(high,2),
                      round(low,2), round(price,2), round(price,2), vol))
                total += 1
            d += timedelta(days=1)

    conn.commit()
    print(f"✅ Inserted {total:,} stock price records")


def main():
    print("\n🏦 Project 3 – Indian Banking Sector Financial Analysis")
    print("=" * 55)
    conn = setup_database()
    bank_ids = insert_banks(conn)
    insert_quarterly_data(conn, bank_ids)
    insert_annual_data(conn, bank_ids)
    insert_stock_prices(conn, bank_ids)

    # Quick validation
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM quarterly_financials")
    print(f"\n📊 Total quarterly records : {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM stock_prices")
    print(f"📈 Total stock price rows  : {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM annual_financials")
    print(f"📋 Total annual records    : {cur.fetchone()[0]}")
    conn.close()
    print("\n✅ Setup complete. Run 02_analysis.py next.\n")


if __name__ == "__main__":
    main()
