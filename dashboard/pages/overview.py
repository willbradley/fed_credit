"""Government-wide overview — landing page."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from dashboard.data_loader import load_budget_formulation, load_reestimates, compute_annual_summary
from dashboard.components.metrics import display_metrics, _fmt_dollars, _fmt_pct, _fmt_count
from dashboard.components.filters import year_range_slider
from dashboard.components.charts import (
    obligations_trend_chart,
    subsidy_rate_trend_chart,
    reestimate_bar_chart,
    reestimate_decomposition_chart,
    sector_obligations_chart,
)


def render():
    st.header("Government-Wide Overview")

    bf = load_budget_formulation()
    re = load_reestimates()
    summary = compute_annual_summary(bf)

    # --- Top metrics (latest year) ---
    latest_year = int(bf["budget_year"].max())
    prior_year = latest_year - 1

    current_bf = bf[bf["cohort_type"] == "current"]

    def _year_agg(year):
        ydf = current_bf[current_bf["budget_year"] == year]
        total_oblig_m = ydf["obligations_millions"].sum()
        n_prog = ydf["program_id"].nunique()
        mask = ydf["subsidy_rate_pct"].notna() & ydf["obligations_thousands"].notna()
        g = ydf[mask]
        total_o = g["obligations_thousands"].sum()
        wavg_rate = (g["subsidy_rate_pct"] * g["obligations_thousands"]).sum() / total_o if total_o else None
        return total_oblig_m, n_prog, wavg_rate

    curr_oblig, curr_n, curr_rate = _year_agg(latest_year)
    prev_oblig, prev_n, prev_rate = _year_agg(prior_year)

    re_curr = re[re["budget_year"] == latest_year]["current_reestimate_millions"].sum()
    re_prev = re[re["budget_year"] == prior_year]["current_reestimate_millions"].sum()

    display_metrics([
        {
            "label": f"Total Obligations FY{latest_year}",
            "value": _fmt_dollars(curr_oblig),
            "delta": _fmt_dollars(curr_oblig - prev_oblig) if prev_oblig else None,
        },
        {
            "label": "Active Programs",
            "value": _fmt_count(curr_n),
            "delta": f"{curr_n - prev_n:+d}" if prev_n else None,
        },
        {
            "label": "Wtd. Avg. Subsidy Rate",
            "value": _fmt_pct(curr_rate),
            "delta": f"{curr_rate - prev_rate:+.2f} pp" if curr_rate and prev_rate else None,
            "delta_color": "inverse",
        },
        {
            "label": "Total Net Reestimates",
            "value": _fmt_dollars(re_curr),
            "delta": _fmt_dollars(re_curr - re_prev) if re_prev else None,
            "delta_color": "inverse",
        },
    ])

    # --- Year range slider ---
    year_range = year_range_slider(key="overview_year_range")
    summary_f = summary[
        (summary["budget_year"] >= year_range[0]) & (summary["budget_year"] <= year_range[1])
    ]
    re_f = re[(re["budget_year"] >= year_range[0]) & (re["budget_year"] <= year_range[1])]
    bf_f = bf[(bf["budget_year"] >= year_range[0]) & (bf["budget_year"] <= year_range[1])]

    # --- Row 2: Obligations & Subsidy Rate ---
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(obligations_trend_chart(summary_f), use_container_width=True)
    with col2:
        st.plotly_chart(subsidy_rate_trend_chart(summary_f), use_container_width=True)

    # --- Row 3: Reestimates ---
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(reestimate_bar_chart(re_f), use_container_width=True)
    with col4:
        st.plotly_chart(reestimate_decomposition_chart(re_f), use_container_width=True)

    # --- Row 4: Sector bar ---
    chart_year = min(latest_year, year_range[1])
    st.plotly_chart(sector_obligations_chart(bf_f, chart_year), use_container_width=True)


render()
