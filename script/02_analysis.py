"""
Project 3: Indian Banking Sector Financial Analysis
====================================================
Script 02 - Core Financial Analysis & Visualizations
Outputs: /reports/ folder with charts + summary CSV

Usage:
    python scripts/02_analysis.py
"""

import sqlite3
import os
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE, "data", "banking_sector.db")
RPT_PATH = os.path.join(BASE, "reports")
os.makedirs(RPT_PATH, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────
PALETTE = {
    "PSU":     "#1565C0",   # Deep blue
    "Private": "#2E7D32",   # Deep green
    "accent":  "#E65100",   # Orange
    "bg":      "#FAFAFA",
    "grid":    "#EEEEEE",
}
plt.rcParams.update({
    "figure.facecolor": PALETTE["bg"],
    "axes.facecolor":   PALETTE["bg"],
    "axes.grid":        True,
    "grid.color":       PALETTE["grid"],
    "grid.linestyle":   "--",
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right":False,
})

TYPE_COLORS = {"PSU": PALETTE["PSU"], "Private": PALETTE["Private"]}


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


# ── 1. Load data ──────────────────────────────────────────────
def load_data():
    conn = get_conn()
    qf  = pd.read_sql("SELECT q.*, b.bank_name, b.ticker, b.bank_type, b.market_segment "
                      "FROM quarterly_financials q JOIN banks b ON b.bank_id=q.bank_id", conn)
    af  = pd.read_sql("SELECT a.*, b.bank_name, b.ticker, b.bank_type "
                      "FROM annual_financials a JOIN banks b ON b.bank_id=a.bank_id", conn)
    sp  = pd.read_sql("SELECT s.*, b.bank_name, b.ticker, b.bank_type "
                      "FROM stock_prices s JOIN banks b ON b.bank_id=b.bank_id "
                      "ORDER BY s.price_date", conn)
    conn.close()
    sp["price_date"] = pd.to_datetime(sp["price_date"])
    print("✅ Data loaded")
    return qf, af, sp


# ── 2. NPA Trend Analysis ─────────────────────────────────────
def plot_npa_trends(qf: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Asset Quality: NPA Trend Analysis (FY2020–FY2024)",
                 fontsize=15, fontweight="bold", y=1.02)

    # Gross NPA by bank type
    ax = axes[0]
    npa_type = (qf.groupby(["fiscal_year", "bank_type"])["gross_npa_pct"]
                  .mean().reset_index())
    for btype, grp in npa_type.groupby("bank_type"):
        ax.plot(grp["fiscal_year"], grp["gross_npa_pct"],
                marker="o", label=btype, color=TYPE_COLORS.get(btype, "gray"),
                linewidth=2.5)
    ax.set_title("Average Gross NPA % — PSU vs Private", fontweight="bold")
    ax.set_xlabel("Fiscal Year"); ax.set_ylabel("Gross NPA (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.legend(); ax.set_xticks(qf["fiscal_year"].unique())

    # Heatmap: bank-wise gross NPA
    ax = axes[1]
    pivot = (qf.groupby(["bank_name", "fiscal_year"])["gross_npa_pct"]
               .mean().unstack())
    sns.heatmap(pivot, ax=ax, cmap="RdYlGn_r", annot=True, fmt=".1f",
                linewidths=0.5, cbar_kws={"label": "Gross NPA %"})
    ax.set_title("Bank-wise Gross NPA Heatmap", fontweight="bold")
    ax.set_xlabel("Fiscal Year"); ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)

    plt.tight_layout()
    out = os.path.join(RPT_PATH, "01_npa_trend.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {out}")


# ── 3. Profitability Dashboard ────────────────────────────────
def plot_profitability(af: pd.DataFrame):
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle("Profitability Analysis — Indian Banking Sector", fontsize=15, fontweight="bold")
    gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

    metrics = [
        ("return_on_assets",  "RoA (%)",  "tab:blue"),
        ("return_on_equity",  "RoE (%)",  "tab:green"),
        ("net_interest_margin","NIM (%)", "tab:orange"),
        ("cost_to_income_ratio","CIR (%)", "tab:red"),
        ("net_profit",        "Net Profit (₹Cr)", "tab:purple"),
        ("profit_growth_pct", "Profit Growth YoY (%)", "tab:brown"),
    ]

    for i, (col, label, color) in enumerate(metrics):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        data = af.groupby("fiscal_year")[col].mean()
        bars = ax.bar(data.index, data.values, color=color, alpha=0.8, width=0.6)
        ax.set_title(label, fontweight="bold", fontsize=10)
        ax.set_xlabel("Fiscal Year")
        ax.set_xticks(data.index)
        # Value labels
        for bar in bars:
            h = bar.get_height()
            if pd.notna(h):
                ax.text(bar.get_x() + bar.get_width()/2, h,
                        f"{h:.1f}", ha="center", va="bottom", fontsize=8)

    out = os.path.join(RPT_PATH, "02_profitability.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {out}")


# ── 4. Capital Adequacy ───────────────────────────────────────
def plot_capital_adequacy(qf: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Capital Adequacy Ratio (CRAR) Analysis", fontsize=14, fontweight="bold")

    latest = qf[qf["fiscal_year"] == qf["fiscal_year"].max()]
    latest_avg = latest.groupby("bank_name")["capital_adequacy_ratio"].mean().sort_values()

    ax = axes[0]
    colors = [TYPE_COLORS.get(
        qf.loc[qf["bank_name"]==b, "bank_type"].iloc[0], "gray") for b in latest_avg.index]
    bars = ax.barh(latest_avg.index, latest_avg.values, color=colors, alpha=0.85)
    ax.axvline(x=11.5, color=PALETTE["accent"], linestyle="--", linewidth=1.5, label="RBI Min (11.5%)")
    ax.set_title(f"CAR by Bank (FY{qf['fiscal_year'].max()})", fontweight="bold")
    ax.set_xlabel("Capital Adequacy Ratio (%)"); ax.legend()
    for bar in bars:
        w = bar.get_width()
        ax.text(w+0.1, bar.get_y()+bar.get_height()/2, f"{w:.1f}%", va="center", fontsize=8)

    ax2 = axes[1]
    car_trend = qf.groupby(["fiscal_year", "bank_type"])["capital_adequacy_ratio"].mean().reset_index()
    for btype, grp in car_trend.groupby("bank_type"):
        ax2.plot(grp["fiscal_year"], grp["capital_adequacy_ratio"],
                 marker="s", label=btype, color=TYPE_COLORS.get(btype, "gray"),
                 linewidth=2.5)
    ax2.axhline(y=11.5, color=PALETTE["accent"], linestyle="--", label="RBI Min (11.5%)")
    ax2.set_title("CAR Trend — PSU vs Private", fontweight="bold")
    ax2.set_xlabel("Fiscal Year"); ax2.set_ylabel("CAR (%)")
    ax2.set_xticks(qf["fiscal_year"].unique()); ax2.legend()

    plt.tight_layout()
    out = os.path.join(RPT_PATH, "03_capital_adequacy.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {out}")


# ── 5. Peer Comparison Scatter ────────────────────────────────
def plot_peer_comparison(af: pd.DataFrame):
    latest = af[af["fiscal_year"] == af["fiscal_year"].max()].copy()

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("Peer Comparison — Key Ratios (Latest Year)", fontsize=14, fontweight="bold")

    ax = axes[0]
    for btype in ["PSU", "Private"]:
        grp = latest[latest["bank_type"] == btype]
        sc = ax.scatter(grp["net_interest_margin"], grp["return_on_equity"],
                   s=grp["total_assets"].fillna(1)/5000,
                   alpha=0.7, label=btype, color=TYPE_COLORS[btype])
        for _, row in grp.iterrows():
            ax.annotate(row["ticker"], (row["net_interest_margin"], row["return_on_equity"]),
                        fontsize=7, ha="left", xytext=(4, 2), textcoords="offset points")
    ax.set_xlabel("Net Interest Margin (%)"); ax.set_ylabel("Return on Equity (%)")
    ax.set_title("NIM vs RoE (bubble = Asset Size)", fontweight="bold"); ax.legend()

    ax2 = axes[1]
    for btype in ["PSU", "Private"]:
        grp = latest[latest["bank_type"] == btype]
        ax2.scatter(grp["gross_npa_pct"], grp["cost_to_income_ratio"],
                    s=120, alpha=0.8, label=btype, color=TYPE_COLORS[btype], marker="D")
        for _, row in grp.iterrows():
            ax2.annotate(row["ticker"], (row["gross_npa_pct"], row["cost_to_income_ratio"]),
                         fontsize=7, ha="left", xytext=(4, 2), textcoords="offset points")
    ax2.set_xlabel("Gross NPA (%)"); ax2.set_ylabel("Cost-to-Income Ratio (%)")
    ax2.set_title("Asset Quality vs Efficiency", fontweight="bold"); ax2.legend()

    plt.tight_layout()
    out = os.path.join(RPT_PATH, "04_peer_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {out}")


# ── 6. Credit Growth ──────────────────────────────────────────
def plot_credit_deposit_growth(af: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Credit & Deposit Growth Analysis", fontsize=14, fontweight="bold")

    for ax, col, label, color in [
        (axes[0], "advances_growth_pct", "Advances Growth YoY (%)", "tab:green"),
        (axes[1], "deposit_growth_pct",  "Deposit Growth YoY (%)",  "tab:blue"),
    ]:
        pivot = (af.groupby(["fiscal_year", "bank_type"])[col].mean().unstack().dropna())
        pivot.plot(kind="bar", ax=ax, color=[TYPE_COLORS["PSU"], TYPE_COLORS["Private"]],
                   alpha=0.85, width=0.65)
        ax.set_title(label, fontweight="bold")
        ax.set_xlabel("Fiscal Year"); ax.set_ylabel("%")
        ax.set_xticklabels(pivot.index, rotation=0); ax.legend(title="Bank Type")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())

    plt.tight_layout()
    out = os.path.join(RPT_PATH, "05_credit_deposit_growth.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {out}")


# ── 7. Summary Report CSV ─────────────────────────────────────
def generate_summary_csv(af: pd.DataFrame, qf: pd.DataFrame):
    latest_qf = qf[qf["fiscal_year"] == qf["fiscal_year"].max()]
    summary = latest_qf.groupby(["bank_name", "bank_type"]).agg(
        Net_Profit_Cr=("net_profit", "sum"),
        Total_Assets_Cr=("total_assets", "mean"),
        Total_Advances_Cr=("total_advances", "mean"),
        Total_Deposits_Cr=("total_deposits", "mean"),
        Gross_NPA_Pct=("gross_npa_pct", "mean"),
        Net_NPA_Pct=("net_npa_pct", "mean"),
        CAR_Pct=("capital_adequacy_ratio", "mean"),
        RoA_Pct=("return_on_assets", "mean"),
        RoE_Pct=("return_on_equity", "mean"),
        NIM_Pct=("net_interest_margin", "mean"),
        CIR_Pct=("cost_to_income_ratio", "mean"),
    ).reset_index().round(2)

    summary = summary.sort_values("Net_Profit_Cr", ascending=False)
    out = os.path.join(RPT_PATH, "banking_sector_summary.csv")
    summary.to_csv(out, index=False)
    print(f"  📋 Summary CSV saved: {out}")
    return summary


# ── 8. SQL-based analytical queries ──────────────────────────
def run_sql_analytics():
    conn = get_conn()
    print("\n" + "="*55)
    print("📌 SQL ANALYTICAL QUERIES")
    print("="*55)

    queries = {
        "Top 5 Banks by Net Profit (FY2024)": """
            SELECT b.bank_name, b.bank_type,
                   ROUND(SUM(q.net_profit),0) AS total_profit_cr,
                   ROUND(AVG(q.return_on_equity),2) AS avg_roe_pct
            FROM quarterly_financials q
            JOIN banks b ON b.bank_id=q.bank_id
            WHERE q.fiscal_year=2024
            GROUP BY b.bank_id
            ORDER BY total_profit_cr DESC LIMIT 5;
        """,
        "Banks with Best Asset Quality (Low NPA)": """
            SELECT b.bank_name, b.bank_type,
                   ROUND(AVG(q.gross_npa_pct),2) AS avg_gnpa,
                   ROUND(AVG(q.provision_coverage_ratio),2) AS avg_pcr
            FROM quarterly_financials q
            JOIN banks b ON b.bank_id=q.bank_id
            WHERE q.fiscal_year=2024
            GROUP BY b.bank_id
            ORDER BY avg_gnpa ASC LIMIT 5;
        """,
        "PSU vs Private: Avg Key Ratios FY2024": """
            SELECT b.bank_type,
                   ROUND(AVG(q.return_on_assets),2)   AS avg_roa,
                   ROUND(AVG(q.net_interest_margin),2) AS avg_nim,
                   ROUND(AVG(q.gross_npa_pct),2)       AS avg_gnpa,
                   ROUND(AVG(q.capital_adequacy_ratio),2) AS avg_car
            FROM quarterly_financials q
            JOIN banks b ON b.bank_id=q.bank_id
            WHERE q.fiscal_year=2024
            GROUP BY b.bank_type;
        """,
    }

    for title, sql in queries.items():
        print(f"\n🔍 {title}")
        df = pd.read_sql(sql, conn)
        print(df.to_string(index=False))

    conn.close()


def main():
    print("\n🏦  Project 3 — Indian Banking Sector Analysis")
    print("=" * 55)
    qf, af, sp = load_data()

    print("\n📊 Generating charts...")
    plot_npa_trends(qf)
    plot_profitability(af)
    plot_capital_adequacy(qf)
    plot_peer_comparison(af)
    plot_credit_deposit_growth(af)
    summary = generate_summary_csv(af, qf)
    run_sql_analytics()

    print(f"\n✅ All outputs saved to: {RPT_PATH}")
    print("\n📈 Summary Preview:")
    print(summary[["bank_name","bank_type","Net_Profit_Cr","Gross_NPA_Pct","RoE_Pct","NIM_Pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
