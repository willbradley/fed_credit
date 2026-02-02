"""Federal Credit Supplement — Budget Formulation Scorecard."""

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `from dashboard.*` imports work
# regardless of where Streamlit launches the script from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.data_loader import load_budget_formulation
from dashboard.components.metrics import display_metrics, _fmt_dollars, _fmt_pct, _fmt_count

st.set_page_config(
    page_title="Federal Credit Budget Center",
    page_icon=":classical_building:",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AGENCY_SHORT = {
    "Department of Agriculture": "Agriculture",
    "Department of Commerce": "Commerce",
    "Department of Defense": "Defense",
    "Department of Education": "Education",
    "Department of Energy": "Energy",
    "Department of Health and Human Services": "HHS",
    "Department of Homeland Security": "DHS",
    "Department of Housing and Urban Development": "HUD",
    "Department of State": "State",
    "Department of Transportation": "Transportation",
    "Department of Veterans Affairs": "Veterans Affairs",
    "Department of the Interior": "Interior",
    "Department of the Treasury": "Treasury",
    "Export-Import Bank": "Ex-Im Bank",
    "Federal Communications Commission": "FCC",
    "International Assistance Programs": "Int'l Assistance",
    "Other Independent Agencies": "Other Agencies",
    "Small Business Administration": "SBA",
    "U.S. International Development Finance Corp.": "DFC",
}

_CREDIT_LABELS = {"direct_loan": "Direct Loans", "loan_guarantee": "Loan Guarantees"}
_CREDIT_COLORS = {"direct_loan": "#1f77b4", "loan_guarantee": "#ff7f0e"}
_SECTOR_COLORS = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6"]
_TREND_WINDOW = 5  # years of context


def _fmt_dollars_table(val_millions: float) -> str:
    """Format millions to human-readable string (for table cells)."""
    abs_v = abs(val_millions)
    sign = "-" if val_millions < 0 else ""
    if abs_v >= 1_000_000:
        return f"{sign}${abs_v / 1_000_000:,.1f}T"
    if abs_v >= 1_000:
        return f"{sign}${abs_v / 1_000:,.1f}B"
    if abs_v >= 1:
        return f"{sign}${abs_v:,.0f}M"
    if abs_v >= 0.001:
        return f"{sign}${abs_v * 1_000:,.0f}K"
    return "$0"


def _fmt_rate_table(subsidy_m: float, volume_m: float) -> str:
    """Compute and format subsidy rate from dollar amounts."""
    if volume_m == 0:
        return "N/A"
    rate = (subsidy_m / volume_m) * 100
    return f"{rate:.1f}%"


def _year_stats(df: pd.DataFrame):
    """Return (volume_millions, n_programs, subsidy_millions, wavg_rate) for a cohort."""
    vol = df["obligations_millions"].sum()
    n = int(df["program_id"].nunique())
    sub = df["subsidy_amount_thousands"].sum() / 1_000  # → millions
    mask = df["subsidy_rate_pct"].notna() & df["obligations_thousands"].notna()
    g = df[mask]
    total_o = g["obligations_thousands"].sum()
    wavg = (
        (g["subsidy_rate_pct"] * g["obligations_thousands"]).sum() / total_o
        if total_o > 0
        else None
    )
    return vol, n, sub, wavg


def _make_trend_chart(budget_year: int, yaxis_title: str) -> go.Figure:
    """Return a compact, pre-configured Plotly figure for a trend sparkline."""
    fig = go.Figure()
    fig.add_vline(x=budget_year, line_dash="dot", line_color="gray", opacity=0.4)
    fig.update_layout(
        template="plotly_white",
        height=240,
        margin=dict(t=10, b=30, l=50, r=10),
        yaxis_title=yaxis_title,
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

bf = load_budget_formulation()
available_years = sorted(bf["budget_year"].unique(), reverse=True)
current_bf = bf[bf["cohort_type"] == "current"].copy()

# ---------------------------------------------------------------------------
# Header + year picker
# ---------------------------------------------------------------------------

st.title("Federal Credit Budget Center")

budget_year = st.selectbox(
    "Budget Year",
    available_years,
    index=0,
    key="budget_year",
)

st.caption(
    f"Budget formulation data for the **FY{budget_year} cohort** "
    f"(loans projected to be originated during FY{budget_year})."
)

cohort = current_bf[current_bf["budget_year"] == budget_year].copy()
prior_year = budget_year - 1
prior_cohort = current_bf[current_bf["budget_year"] == prior_year]

# ---------------------------------------------------------------------------
# Metric cards with YoY deltas
# ---------------------------------------------------------------------------

curr_vol, curr_n, curr_sub, curr_rate = _year_stats(cohort)
has_prior = len(prior_cohort) > 0
if has_prior:
    prev_vol, prev_n, prev_sub, prev_rate = _year_stats(prior_cohort)
else:
    prev_vol = prev_n = prev_sub = prev_rate = None

display_metrics([
    {
        "label": "Total Loan Volume",
        "value": _fmt_dollars(curr_vol),
        "delta": _fmt_dollars(curr_vol - prev_vol) if prev_vol is not None else None,
    },
    {
        "label": "Active Programs",
        "value": _fmt_count(curr_n),
        "delta": f"{curr_n - prev_n:+d}" if prev_n is not None else None,
    },
    {
        "label": "Net Credit Subsidy",
        "value": _fmt_dollars(curr_sub),
        "delta": _fmt_dollars(curr_sub - prev_sub) if prev_sub is not None else None,
        "delta_color": "inverse",
    },
    {
        "label": "Wtd. Avg. Subsidy Rate",
        "value": _fmt_pct(curr_rate),
        "delta": (
            f"{curr_rate - prev_rate:+.2f} pp"
            if curr_rate is not None and prev_rate is not None
            else None
        ),
        "delta_color": "inverse",
    },
])

# ---------------------------------------------------------------------------
# 2x2 trend chart matrix
# ---------------------------------------------------------------------------

st.markdown("---")

min_trend_year = budget_year - _TREND_WINDOW + 1
trend_data = current_bf[
    (current_bf["budget_year"] >= min_trend_year)
    & (current_bf["budget_year"] <= budget_year)
]

# --- Aggregation by credit type ---
type_agg = (
    trend_data.groupby(["budget_year", "credit_type"])
    .agg(
        volume_b=("obligations_millions", lambda x: x.sum() / 1_000),
        subsidy_b=("subsidy_amount_thousands", lambda x: x.sum() / 1_000_000),
    )
    .reset_index()
)

# --- Top 4 sectors (by volume in the selected year) ---
top_sectors = (
    cohort.groupby("sector_name")["obligations_millions"]
    .sum()
    .nlargest(4)
    .index.tolist()
)

sector_agg = (
    trend_data[trend_data["sector_name"].isin(top_sectors)]
    .groupby(["budget_year", "sector_name"])
    .agg(
        volume_b=("obligations_millions", lambda x: x.sum() / 1_000),
        subsidy_b=("subsidy_amount_thousands", lambda x: x.sum() / 1_000_000),
    )
    .reset_index()
)

# Row 1: Volume and subsidy by credit type
row1_left, row1_right = st.columns(2)

with row1_left:
    st.markdown("**Loan Volume by Credit Type**")
    fig = _make_trend_chart(budget_year, "$ Billions")
    for ct in ["direct_loan", "loan_guarantee"]:
        d = type_agg[type_agg["credit_type"] == ct].sort_values("budget_year")
        fig.add_trace(go.Scatter(
            x=d["budget_year"], y=d["volume_b"],
            name=_CREDIT_LABELS[ct],
            line=dict(color=_CREDIT_COLORS[ct]),
            mode="lines+markers",
            marker=dict(size=6),
        ))
    st.plotly_chart(fig, use_container_width=True)

with row1_right:
    st.markdown("**Credit Subsidy by Credit Type**")
    fig = _make_trend_chart(budget_year, "$ Billions")
    for ct in ["direct_loan", "loan_guarantee"]:
        d = type_agg[type_agg["credit_type"] == ct].sort_values("budget_year")
        fig.add_trace(go.Scatter(
            x=d["budget_year"], y=d["subsidy_b"],
            name=_CREDIT_LABELS[ct],
            line=dict(color=_CREDIT_COLORS[ct]),
            mode="lines+markers",
            marker=dict(size=6),
        ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
    st.plotly_chart(fig, use_container_width=True)

# Row 2: Volume and subsidy by top sectors
row2_left, row2_right = st.columns(2)

with row2_left:
    st.markdown("**Loan Volume — Top Sectors**")
    fig = _make_trend_chart(budget_year, "$ Billions")
    for i, sector in enumerate(top_sectors):
        d = sector_agg[sector_agg["sector_name"] == sector].sort_values("budget_year")
        fig.add_trace(go.Scatter(
            x=d["budget_year"], y=d["volume_b"],
            name=sector,
            line=dict(color=_SECTOR_COLORS[i]),
            mode="lines+markers",
            marker=dict(size=6),
        ))
    st.plotly_chart(fig, use_container_width=True)

with row2_right:
    st.markdown("**Credit Subsidy — Top Sectors**")
    fig = _make_trend_chart(budget_year, "$ Billions")
    for i, sector in enumerate(top_sectors):
        d = sector_agg[sector_agg["sector_name"] == sector].sort_values("budget_year")
        fig.add_trace(go.Scatter(
            x=d["budget_year"], y=d["subsidy_b"],
            name=sector,
            line=dict(color=_SECTOR_COLORS[i]),
            mode="lines+markers",
            marker=dict(size=6),
        ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Agency table (matching PDF scorecard format)
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader(f"FY{budget_year} Budget by Agency")

cohort["subsidy_cost_millions"] = cohort["subsidy_amount_thousands"] / 1_000

agency_agg = (
    cohort.groupby("agency")
    .agg(
        volume_m=("obligations_millions", "sum"),
        subsidy_m=("subsidy_cost_millions", "sum"),
    )
    .sort_values("volume_m", ascending=False)
    .reset_index()
)

# Group small agencies into "Other"
big = agency_agg[agency_agg["volume_m"] >= 1_000].copy()   # >= $1B
small = agency_agg[agency_agg["volume_m"] < 1_000]

if len(small) > 0:
    other = pd.DataFrame([{
        "agency": "Other",
        "volume_m": small["volume_m"].sum(),
        "subsidy_m": small["subsidy_m"].sum(),
    }])
    table_df = pd.concat([big, other], ignore_index=True)
else:
    table_df = big.copy()

# Totals row
totals = pd.DataFrame([{
    "agency": "TOTAL",
    "volume_m": table_df["volume_m"].sum(),
    "subsidy_m": table_df["subsidy_m"].sum(),
}])
table_df = pd.concat([table_df, totals], ignore_index=True)

# Build HTML table matching PDF styling
_HDR_BG = "#2c3e50"
_ALT_BG = "#f8f9fa"
_TOT_BG = "#ecf0f1"
_BORDER = "#bdc3c7"

html_rows = []
for i, row in table_df.iterrows():
    is_total = row["agency"] == "TOTAL"
    if is_total:
        bg, fw = _TOT_BG, "font-weight:bold;"
    elif i % 2 == 1:
        bg, fw = _ALT_BG, ""
    else:
        bg, fw = "white", ""

    name = AGENCY_SHORT.get(row["agency"], row["agency"])
    vol = _fmt_dollars_table(row["volume_m"])
    sub = _fmt_dollars_table(row["subsidy_m"])
    rate = _fmt_rate_table(row["subsidy_m"], row["volume_m"])

    td = f'<td style="padding:6px 12px;border-bottom:1px solid {_BORDER};'
    html_rows.append(
        f'<tr style="background:{bg};{fw}">'
        f'{td}text-align:left;">{name}</td>'
        f'{td}text-align:right;">{vol}</td>'
        f'{td}text-align:right;">{sub}</td>'
        f'{td}text-align:right;">{rate}</td>'
        f'</tr>'
    )

html = (
    f'<table style="width:100%;border-collapse:collapse;font-size:14px;">'
    f'<tr style="background:{_HDR_BG};color:white;font-weight:bold;">'
    f'<th style="padding:8px 12px;text-align:left;">Agency</th>'
    f'<th style="padding:8px 12px;text-align:right;">Loan Volume</th>'
    f'<th style="padding:8px 12px;text-align:right;">Credit Subsidy</th>'
    f'<th style="padding:8px 12px;text-align:right;">Subsidy Rate</th>'
    f'</tr>'
    + "".join(html_rows)
    + '</table>'
)

st.markdown(html, unsafe_allow_html=True)
st.caption(
    'Agencies with less than $1B in loan volume grouped into "Other." '
    "Negative subsidies = expected revenue to government."
)
