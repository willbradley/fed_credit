"""Agency drill-down page."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from dashboard.data_loader import load_budget_formulation, load_reestimates, load_programs
from dashboard.components.metrics import display_metrics, _fmt_dollars, _fmt_pct, _fmt_count
from dashboard.components.filters import year_range_slider, credit_type_filter, agency_selector, apply_filters
from dashboard.components.charts import agency_obligations_trend, agency_subsidy_scatter


def render():
    st.header("Agency Drill-Down")

    bf = load_budget_formulation()
    re = load_reestimates()
    programs = load_programs()

    # --- Controls ---
    col_a, col_b, col_c = st.columns([2, 2, 1])
    with col_a:
        agency = agency_selector(programs["agency"], key="agency_page_select")
    with col_b:
        year_range = year_range_slider(key="agency_year_range")
    with col_c:
        credit_type = credit_type_filter(key="agency_credit_type")

    # Filter data
    bf_f = apply_filters(bf, year_range=year_range, credit_type=credit_type, agency=agency)
    re_f = apply_filters(re, year_range=year_range, credit_type=credit_type, agency=agency)

    # --- Summary metrics ---
    latest_year = int(bf_f["budget_year"].max()) if len(bf_f) > 0 else year_range[1]
    prior_year = latest_year - 1

    current_bf = bf_f[bf_f["cohort_type"] == "current"]
    cy = current_bf[current_bf["budget_year"] == latest_year]
    py = current_bf[current_bf["budget_year"] == prior_year]

    total_oblig = cy["obligations_millions"].sum()
    prev_oblig = py["obligations_millions"].sum()
    n_prog = cy["program_id"].nunique()
    prev_n = py["program_id"].nunique()

    mask = cy["subsidy_rate_pct"].notna() & cy["obligations_thousands"].notna()
    g = cy[mask]
    t = g["obligations_thousands"].sum()
    wavg = (g["subsidy_rate_pct"] * g["obligations_thousands"]).sum() / t if t else None

    mask_p = py["subsidy_rate_pct"].notna() & py["obligations_thousands"].notna()
    gp = py[mask_p]
    tp = gp["obligations_thousands"].sum()
    wavg_p = (gp["subsidy_rate_pct"] * gp["obligations_thousands"]).sum() / tp if tp else None

    display_metrics([
        {
            "label": f"Total Obligations FY{latest_year}",
            "value": _fmt_dollars(total_oblig),
            "delta": _fmt_dollars(total_oblig - prev_oblig) if prev_oblig else None,
        },
        {
            "label": "Active Programs",
            "value": _fmt_count(n_prog),
            "delta": f"{n_prog - prev_n:+d}" if prev_n else None,
        },
        {
            "label": "Wtd. Avg. Subsidy Rate",
            "value": _fmt_pct(wavg),
            "delta": f"{wavg - wavg_p:+.2f} pp" if wavg and wavg_p else None,
            "delta_color": "inverse",
        },
        {
            "label": "Net Reestimates",
            "value": _fmt_dollars(re_f[re_f["budget_year"] == latest_year]["current_reestimate_millions"].sum()),
        },
    ])

    # --- Programs table ---
    st.subheader("Programs")
    if len(current_bf) > 0:
        latest_data = current_bf[current_bf["budget_year"] == latest_year]
        prog_table = (
            latest_data.groupby(["canonical_name", "credit_type", "sector_name"])
            .agg(
                obligations_millions=("obligations_millions", "sum"),
                subsidy_rate_pct=("subsidy_rate_pct", "first"),
            )
            .reset_index()
        )
        # Add years active
        years_active = (
            current_bf.groupby("canonical_name")["budget_year"]
            .agg(["min", "max", "count"])
            .reset_index()
            .rename(columns={"min": "first_year", "max": "last_year", "count": "years"})
        )
        prog_table = prog_table.merge(years_active, on="canonical_name", how="left")
        prog_table = prog_table.sort_values("obligations_millions", ascending=False)
        prog_table.columns = ["Program", "Credit Type", "Sector", "Obligations ($M)", "Subsidy Rate (%)", "First Year", "Last Year", "Years"]
        st.dataframe(prog_table, use_container_width=True, hide_index=True)
    else:
        st.info("No data available for this selection.")

    # --- Charts ---
    col1, col2 = st.columns(2)
    with col1:
        if len(bf_f) > 0:
            st.plotly_chart(agency_obligations_trend(bf_f), use_container_width=True)
    with col2:
        if len(bf_f) > 0:
            st.plotly_chart(agency_subsidy_scatter(bf_f, latest_year), use_container_width=True)

    # --- Reestimate summary ---
    st.subheader("Reestimate Summary by Program")
    if len(re_f) > 0:
        re_summary = (
            re_f.groupby("canonical_name")
            .agg(
                avg_original_rate=("original_subsidy_rate_pct", "mean"),
                avg_reestimated_rate=("current_reestimated_rate_pct", "mean"),
                total_reestimate_millions=("current_reestimate_millions", "sum"),
                n_cohorts=("cohort_year", "nunique"),
            )
            .sort_values("total_reestimate_millions")
            .reset_index()
        )
        re_summary.columns = ["Program", "Avg Original Rate (%)", "Avg Reestimated Rate (%)", "Total Reestimates ($M)", "Cohorts"]
        st.dataframe(re_summary, use_container_width=True, hide_index=True)
    else:
        st.info("No reestimate data available for this selection.")
