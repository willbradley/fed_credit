"""Single-program deep dive page."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd

from dashboard.data_loader import load_budget_formulation, load_reestimates, load_programs
from dashboard.components.metrics import display_metrics, _fmt_dollars, _fmt_pct, _fmt_count
from dashboard.components.charts import (
    program_dual_axis_chart,
    program_reestimate_comparison,
    program_reestimate_decomposition,
)


def render():
    st.header("Program Deep Dive")

    bf = load_budget_formulation()
    re = load_reestimates()
    programs = load_programs()

    # --- Program selector ---
    prog_options = (
        programs[["program_id", "canonical_name", "agency"]]
        .drop_duplicates()
        .sort_values("canonical_name")
    )
    prog_options["label"] = prog_options["canonical_name"] + " (" + prog_options["agency"] + ")"
    labels = prog_options["label"].tolist()

    selected_label = st.selectbox("Select Program", labels, key="program_select")
    selected_row = prog_options[prog_options["label"] == selected_label].iloc[0]
    pid = selected_row["program_id"]

    # --- Identity card ---
    prog_info = programs[programs["program_id"] == pid].iloc[0]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Agency:** {prog_info['agency']}")
        st.markdown(f"**Bureau:** {prog_info['bureau']}")
    with col2:
        st.markdown(f"**Sector:** {prog_info['sector_name']}")
        st.markdown(f"**Account:** {prog_info['account']}")
    with col3:
        bf_prog = bf[bf["program_id"] == pid]
        credit_types = bf_prog["credit_type"].unique()
        ct_label = ", ".join(
            {"direct_loan": "Direct Loan", "loan_guarantee": "Loan Guarantee"}.get(c, c)
            for c in credit_types
        )
        st.markdown(f"**Credit Type:** {ct_label}")
        st.markdown(f"**Years Active:** {prog_info['first_year']}–{prog_info['last_year']}")

    # --- Latest year metrics ---
    current_bf = bf_prog[bf_prog["cohort_type"] == "current"]
    if len(current_bf) > 0:
        latest_year = int(current_bf["budget_year"].max())
        prior_year = latest_year - 1

        cy = current_bf[current_bf["budget_year"] == latest_year]
        py = current_bf[current_bf["budget_year"] == prior_year]

        oblig = cy["obligations_millions"].sum()
        prev_oblig = py["obligations_millions"].sum() if len(py) > 0 else None
        rate = cy["subsidy_rate_pct"].iloc[0] if len(cy) > 0 and cy["subsidy_rate_pct"].notna().any() else None
        prev_rate = py["subsidy_rate_pct"].iloc[0] if len(py) > 0 and py["subsidy_rate_pct"].notna().any() else None
        subsidy_cost = cy["subsidy_amount_thousands"].sum() / 1_000 if len(cy) > 0 else None
        avg_loan = cy["avg_loan_size_thousands"].iloc[0] if len(cy) > 0 and cy["avg_loan_size_thousands"].notna().any() else None

        display_metrics([
            {
                "label": f"Obligations FY{latest_year}",
                "value": _fmt_dollars(oblig),
                "delta": _fmt_dollars(oblig - prev_oblig) if prev_oblig else None,
            },
            {
                "label": "Subsidy Rate",
                "value": _fmt_pct(rate),
                "delta": f"{rate - prev_rate:+.2f} pp" if rate is not None and prev_rate is not None else None,
                "delta_color": "inverse",
            },
            {
                "label": "Subsidy Cost",
                "value": _fmt_dollars(subsidy_cost),
            },
            {
                "label": "Avg Loan Size ($K)",
                "value": f"${avg_loan:,.0f}K" if avg_loan else "N/A",
            },
        ])

        # --- Budget formulation history ---
        st.plotly_chart(program_dual_axis_chart(bf_prog), use_container_width=True)
    else:
        st.info("No budget formulation data available for this program.")

    # --- Reestimate analysis ---
    re_prog = re[re["program_id"] == pid]
    if len(re_prog) > 0:
        # Pick latest budget year for cohort analysis
        re_latest = int(re_prog["budget_year"].max())
        re_cohorts = re_prog[re_prog["budget_year"] == re_latest].sort_values("cohort_year")

        st.subheader(f"Reestimate Cohort Analysis (FY{re_latest} Budget)")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(program_reestimate_comparison(re_cohorts), use_container_width=True)
        with col2:
            st.plotly_chart(program_reestimate_decomposition(re_cohorts), use_container_width=True)
    else:
        st.info("No reestimate data available for this program.")

    # --- Raw data tabs ---
    st.subheader("Raw Data")
    tab1, tab2 = st.tabs(["Budget Formulation", "Reestimates"])
    with tab1:
        if len(bf_prog) > 0:
            st.dataframe(bf_prog.drop(columns=["program_id"]), use_container_width=True, hide_index=True)
        else:
            st.info("No budget formulation data.")
    with tab2:
        if len(re_prog) > 0:
            st.dataframe(re_prog.drop(columns=["program_id"]), use_container_width=True, hide_index=True)
        else:
            st.info("No reestimate data.")


render()
