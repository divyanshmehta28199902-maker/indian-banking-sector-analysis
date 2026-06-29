# Project 3 — Power BI Dashboard Design Guide
# Indian Banking Sector Financial Analysis
# ============================================================
# File: powerbi_mockup/DAX_MEASURES.md
# ============================================================

## Data Sources to Import into Power BI

| Table                  | Source                              |
|------------------------|-------------------------------------|
| quarterly_financials   | SQLite DB / exported CSV            |
| annual_financials      | SQLite DB / exported CSV            |
| stock_prices           | SQLite DB / exported CSV            |
| banks                  | SQLite DB / exported CSV            |
| banking_sector_summary | /reports/banking_sector_summary.csv |

---

## DAX Measures

### Core KPIs

```dax
-- Total Net Profit (Crores)
Total Net Profit = SUM(quarterly_financials[net_profit])

-- Average Gross NPA %
Avg Gross NPA % = AVERAGE(quarterly_financials[gross_npa_pct])

-- Average Net Interest Margin
Avg NIM % = AVERAGE(quarterly_financials[net_interest_margin])

-- Average Return on Equity
Avg RoE % = AVERAGE(quarterly_financials[return_on_equity])

-- Average Capital Adequacy Ratio
Avg CAR % = AVERAGE(quarterly_financials[capital_adequacy_ratio])

-- Cost-to-Income Ratio
Avg CIR % = AVERAGE(quarterly_financials[cost_to_income_ratio])
```

### Year-over-Year Growth

```dax
-- YoY NPA Change
NPA YoY Change =
VAR CurrYear = MAX(quarterly_financials[fiscal_year])
VAR CurrNPA  = CALCULATE([Avg Gross NPA %], quarterly_financials[fiscal_year] = CurrYear)
VAR PrevNPA  = CALCULATE([Avg Gross NPA %], quarterly_financials[fiscal_year] = CurrYear - 1)
RETURN IF(PrevNPA = 0, BLANK(), (CurrNPA - PrevNPA) / PrevNPA)

-- YoY Profit Growth
Profit YoY Growth =
VAR CurrYear   = MAX(quarterly_financials[fiscal_year])
VAR CurrProfit = CALCULATE([Total Net Profit], quarterly_financials[fiscal_year] = CurrYear)
VAR PrevProfit = CALCULATE([Total Net Profit], quarterly_financials[fiscal_year] = CurrYear - 1)
RETURN IF(PrevProfit = 0, BLANK(), (CurrProfit - PrevProfit) / ABS(PrevProfit))
```

### Conditional Formatting Measures

```dax
-- NPA Health Color (Red/Amber/Green)
NPA Health =
IF([Avg Gross NPA %] < 2, "Good",
   IF([Avg Gross NPA %] < 5, "Watch",
      "Stress"))

-- CAR Status
CAR Status =
IF([Avg CAR %] >= 15, "Strong",
   IF([Avg CAR %] >= 11.5, "Adequate",
      "Below Minimum"))
```

### Ranking Measures

```dax
-- Rank banks by profitability within bank type
Profit Rank =
RANKX(
    FILTER(ALL(banks), banks[bank_type] = MAX(banks[bank_type])),
    [Total Net Profit],, DESC, Dense
)
```

---

## Recommended Dashboard Pages

### Page 1: Executive Overview
- KPI Cards: Total Sector Profit | Avg NPA | Avg CAR | Avg NIM
- Bar chart: Top 10 Banks by Net Profit
- Donut: PSU vs Private share of total assets
- Line: Sector-level NPA trend FY2020–FY2024
- Slicer: Bank Type | Fiscal Year

### Page 2: Asset Quality Deep Dive
- Heatmap matrix: Bank × Year → Gross NPA %
- Clustered bar: Gross NPA vs Net NPA by bank
- KPI: Provision Coverage Ratio trend
- Table: Banks with NPA > 5% flagged in red

### Page 3: Profitability & Efficiency
- Scatter: NIM vs RoE (color = bank type, size = assets)
- Waterfall: NII → Other Income → OPEX → Provisions → Net Profit
- Line: RoA trend PSU vs Private
- Bar: Cost-to-Income Ratio comparison

### Page 4: Capital Adequacy & Stability
- Gauge: Sector average CAR vs RBI minimum (11.5%)
- Bar: Bank-wise CAR with threshold line
- Line: Tier 1 capital trend
- Card: Banks below 15% CAR

### Page 5: Stock Performance
- Line chart: Normalized price index (base 100 = Jan 2020)
- Bar: Annual return by bank
- Candlestick: Last 90 days for selected bank
- Slicer: Ticker

---

## Bookmarks & Interactivity
- Bookmark 1: PSU Banks View
- Bookmark 2: Private Banks View
- Bookmark 3: Top 5 Performers
- Cross-filter: Clicking a bank name filters all visuals
- Drill-through: From annual → quarterly detail page

---

## Color Theme (Import as JSON)
```json
{
  "name": "Banking Analysis",
  "dataColors": ["#1565C0","#2E7D32","#E65100","#6A1B9A","#00695C","#F9A825"],
  "background": "#FAFAFA",
  "foreground": "#1A1A2E",
  "tableAccent": "#1565C0"
}
```
