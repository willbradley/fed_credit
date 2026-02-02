"""Shared filter widgets for the FCS dashboard."""

from __future__ import annotations

import streamlit as st
import pandas as pd


def year_range_slider(
    label: str = "Budget Year Range",
    min_year: int = 2010,
    max_year: int = 2026,
    default: tuple[int, int] | None = None,
    key: str = "year_range",
) -> tuple[int, int]:
    """Render a year range slider and return (start, end)."""
    if default is None:
        default = (min_year, max_year)
    return st.slider(label, min_year, max_year, default, key=key)


def credit_type_filter(key: str = "credit_type") -> str | None:
    """Radio button for credit type. Returns 'direct_loan', 'loan_guarantee', or None (both)."""
    options = {"Both": None, "Direct Loans": "direct_loan", "Loan Guarantees": "loan_guarantee"}
    choice = st.radio("Credit Type", list(options.keys()), horizontal=True, key=key)
    return options[choice]


def agency_selector(agencies: pd.Series, key: str = "agency_select") -> str:
    """Selectbox for agency names."""
    sorted_agencies = sorted(agencies.dropna().unique())
    return st.selectbox("Agency", sorted_agencies, key=key)


def sector_selector(sectors: pd.DataFrame, key: str = "sector_select") -> list[str]:
    """Multiselect for sectors. Returns list of sector codes."""
    mapping = sectors.drop_duplicates(subset="sector").set_index("sector")["sector_name"].to_dict()
    selected_names = st.multiselect(
        "Sectors",
        sorted(mapping.values()),
        key=key,
    )
    name_to_code = {v: k for k, v in mapping.items()}
    return [name_to_code[n] for n in selected_names]


def apply_filters(
    df: pd.DataFrame,
    year_range: tuple[int, int] | None = None,
    credit_type: str | None = None,
    agency: str | None = None,
    sectors: list[str] | None = None,
) -> pd.DataFrame:
    """Apply common filters to a DataFrame. Returns filtered copy."""
    out = df.copy()
    if year_range is not None and "budget_year" in out.columns:
        out = out[(out["budget_year"] >= year_range[0]) & (out["budget_year"] <= year_range[1])]
    if credit_type is not None and "credit_type" in out.columns:
        out = out[out["credit_type"] == credit_type]
    if agency is not None and "agency" in out.columns:
        out = out[out["agency"] == agency]
    if sectors and "sector" in out.columns:
        out = out[out["sector"].isin(sectors)]
    return out
