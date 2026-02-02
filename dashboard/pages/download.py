"""Filtered CSV download page."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from dashboard.data_loader import load_budget_formulation, load_reestimates, load_programs
from dashboard.components.filters import year_range_slider


def _to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def render():
    st.header("Data Download")

    bf = load_budget_formulation()
    re = load_reestimates()
    programs = load_programs()

    # ===================================================================
    # Budget Formulation
    # ===================================================================
    st.subheader("Budget Formulation")

    col1, col2 = st.columns(2)
    with col1:
        bf_credit = st.multiselect(
            "Credit Type",
            ["direct_loan", "loan_guarantee"],
            default=["direct_loan", "loan_guarantee"],
            key="dl_bf_credit",
        )
        bf_agencies = st.multiselect(
            "Agency",
            sorted(bf["agency"].dropna().unique()),
            key="dl_bf_agency",
        )
    with col2:
        bf_sectors = st.multiselect(
            "Sector",
            sorted(bf["sector_name"].dropna().unique()),
            key="dl_bf_sector",
        )
        bf_cohort = st.radio(
            "Cohort Selection",
            ["Current-year only", "All cohorts"],
            key="dl_bf_cohort",
            horizontal=True,
        )

    bf_year_range = year_range_slider(label="Budget Year Range", key="dl_bf_year")

    # Apply filters
    bf_filtered = bf.copy()
    if bf_credit:
        bf_filtered = bf_filtered[bf_filtered["credit_type"].isin(bf_credit)]
    if bf_agencies:
        bf_filtered = bf_filtered[bf_filtered["agency"].isin(bf_agencies)]
    if bf_sectors:
        bf_filtered = bf_filtered[bf_filtered["sector_name"].isin(bf_sectors)]
    bf_filtered = bf_filtered[
        (bf_filtered["budget_year"] >= bf_year_range[0])
        & (bf_filtered["budget_year"] <= bf_year_range[1])
    ]
    if bf_cohort == "Current-year only":
        bf_filtered = bf_filtered[bf_filtered["cohort_type"] == "current"]

    st.caption(f"{len(bf_filtered):,} rows")
    st.dataframe(bf_filtered.head(100), use_container_width=True, hide_index=True)

    st.download_button(
        label="Download Budget Formulation CSV",
        data=_to_csv(bf_filtered),
        file_name="fcs_budget_formulation.csv",
        mime="text/csv",
        key="dl_bf_btn",
    )

    st.divider()

    # ===================================================================
    # Reestimates
    # ===================================================================
    st.subheader("Reestimates")

    col3, col4 = st.columns(2)
    with col3:
        re_credit = st.multiselect(
            "Credit Type",
            ["direct_loan", "loan_guarantee"],
            default=["direct_loan", "loan_guarantee"],
            key="dl_re_credit",
        )
        re_agencies = st.multiselect(
            "Agency",
            sorted(re["agency"].dropna().unique()),
            key="dl_re_agency",
        )
    with col4:
        re_sectors = st.multiselect(
            "Sector",
            sorted(re["sector_name"].dropna().unique()),
            key="dl_re_sector",
        )

    re_year_range = year_range_slider(label="Budget Year Range", key="dl_re_year")

    # Apply filters
    re_filtered = re.copy()
    if re_credit:
        re_filtered = re_filtered[re_filtered["credit_type"].isin(re_credit)]
    if re_agencies:
        re_filtered = re_filtered[re_filtered["agency"].isin(re_agencies)]
    if re_sectors:
        re_filtered = re_filtered[re_filtered["sector_name"].isin(re_sectors)]
    re_filtered = re_filtered[
        (re_filtered["budget_year"] >= re_year_range[0])
        & (re_filtered["budget_year"] <= re_year_range[1])
    ]

    st.caption(f"{len(re_filtered):,} rows")
    st.dataframe(re_filtered.head(100), use_container_width=True, hide_index=True)

    st.download_button(
        label="Download Reestimates CSV",
        data=_to_csv(re_filtered),
        file_name="fcs_reestimates.csv",
        mime="text/csv",
        key="dl_re_btn",
    )

    st.divider()

    # ===================================================================
    # Programs Master
    # ===================================================================
    st.subheader("Programs Master")
    st.caption(f"{len(programs):,} programs")
    st.dataframe(programs.head(100), use_container_width=True, hide_index=True)

    st.download_button(
        label="Download Programs Master CSV",
        data=_to_csv(programs),
        file_name="fcs_programs_master.csv",
        mime="text/csv",
        key="dl_prog_btn",
    )


render()
