"""Sector comparison page."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from dashboard.data_loader import load_budget_formulation, load_reestimates
from dashboard.components.filters import year_range_slider, credit_type_filter, apply_filters
from dashboard.components.charts import (
    sector_grouped_bar,
    sector_faceted_area,
    sector_heatmap,
    sector_reestimate_stacked,
)


def render():
    st.header("Sector Comparison")

    bf = load_budget_formulation()
    re = load_reestimates()

    # --- Controls ---
    col_a, col_b = st.columns([3, 1])
    with col_a:
        year_range = year_range_slider(key="sector_year_range")
    with col_b:
        credit_type = credit_type_filter(key="sector_credit_type")

    bf_f = apply_filters(bf, year_range=year_range, credit_type=credit_type)
    re_f = apply_filters(re, year_range=year_range, credit_type=credit_type)

    latest_year = min(int(bf["budget_year"].max()), year_range[1])

    # --- Grouped bar ---
    st.plotly_chart(sector_grouped_bar(bf_f, latest_year), use_container_width=True)

    # --- Faceted area ---
    st.plotly_chart(sector_faceted_area(bf_f, year_range), use_container_width=True)

    # --- Heatmap ---
    st.plotly_chart(sector_heatmap(bf_f, year_range), use_container_width=True)

    # --- Reestimate decomposition ---
    if len(re_f) > 0:
        st.plotly_chart(sector_reestimate_stacked(re_f), use_container_width=True)

    # --- Summary table ---
    st.subheader("Sector Summary")
    current = bf_f[bf_f["cohort_type"] == "current"]
    if len(current) > 0:
        agg = (
            current.groupby("sector_name")
            .agg(
                total_obligations_millions=("obligations_millions", "sum"),
                n_programs=("program_id", "nunique"),
                avg_subsidy_rate=("subsidy_rate_pct", "mean"),
            )
            .sort_values("total_obligations_millions", ascending=False)
            .reset_index()
        )
        agg.columns = ["Sector", "Total Obligations ($M)", "Programs", "Avg Subsidy Rate (%)"]
        st.dataframe(agg, use_container_width=True, hide_index=True)


render()
