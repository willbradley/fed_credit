"""JSON → cached DataFrames for the FCS dashboard."""

from __future__ import annotations

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from dashboard.agency_normalize import normalize_agency

DATA_DIR = Path(__file__).parent.parent / "data" / "processed" / "historical" / "unified"


def _safe_float(val) -> float | None:
    """Coerce a value to float, returning None for unparseable strings."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    # Handle strings like '1 96,767' or '10.74 4' or '…..'
    try:
        cleaned = str(val).replace(",", "").replace(" ", "")
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _is_aggregate_row(name: str) -> bool:
    """Return True for rows that are section totals / weighted averages, not real programs."""
    lower = name.lower()
    return lower.startswith("weighted average") or lower == "(legislative proposal)"


# ---------------------------------------------------------------------------
# Sector name lookup
# ---------------------------------------------------------------------------

@st.cache_data
def _load_sector_names() -> dict[str, str]:
    with open(DATA_DIR / "sector_taxonomy.json") as f:
        tax = json.load(f)
    return {k: v["name"] for k, v in tax["sectors"].items()}


# ---------------------------------------------------------------------------
# Programs master
# ---------------------------------------------------------------------------

@st.cache_data
def load_programs() -> pd.DataFrame:
    """Load the programs master list (1,253 rows)."""
    with open(DATA_DIR / "programs_master.json") as f:
        raw = json.load(f)

    sector_names = _load_sector_names()
    rows = []
    for prog in raw.values():
        agency = normalize_agency(prog["agency"])
        if agency is None:
            continue
        if _is_aggregate_row(prog["canonical_name"]):
            continue
        years = prog.get("budget_years_seen", [])
        rows.append({
            "program_id": prog["program_id"],
            "canonical_name": prog["canonical_name"],
            "agency": agency,
            "bureau": prog.get("bureau", ""),
            "account": prog.get("account", ""),
            "sector": prog.get("sector", ""),
            "sector_name": sector_names.get(prog.get("sector", ""), ""),
            "n_budget_years": len(years),
            "first_year": min(years) if years else None,
            "last_year": max(years) if years else None,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Budget formulation (tables 1 + 2)
# ---------------------------------------------------------------------------

def _flatten_budget_table(path: Path, sector_names: dict[str, str]) -> list[dict]:
    """Flatten a single budget formulation JSON file into row dicts."""
    with open(path) as f:
        data = json.load(f)

    rows = []
    for prog in data["programs"].values():
        agency = normalize_agency(prog["agency"])
        if agency is None:
            continue
        if _is_aggregate_row(prog["canonical_name"]):
            continue

        pid = prog["program_id"]
        name = prog["canonical_name"]
        bureau = prog.get("bureau", "")
        sector = prog.get("sector", "")
        sector_name = sector_names.get(sector, "")
        credit_type = prog.get("credit_type", "")

        for by_str, by_data in prog.get("budget_years", {}).items():
            budget_year = int(by_str)
            bea = by_data.get("bea_category", "")
            for cohort_str, cohort in by_data.get("cohorts", {}).items():
                cohort_year = int(cohort_str)
                rate = _safe_float(cohort.get("subsidy_rate_percent"))
                oblig = _safe_float(cohort.get("obligations_thousands"))
                oblig_m = oblig / 1_000 if oblig is not None else None
                avg_loan = _safe_float(cohort.get("average_loan_size_thousands"))
                subsidy_amt = (
                    rate / 100 * oblig if rate is not None and oblig is not None else None
                )
                rows.append({
                    "program_id": pid,
                    "canonical_name": name,
                    "agency": agency,
                    "bureau": bureau,
                    "sector": sector,
                    "sector_name": sector_name,
                    "credit_type": credit_type,
                    "budget_year": budget_year,
                    "cohort_year": cohort_year,
                    "cohort_type": "current" if cohort_year == budget_year else "prior",
                    "bea_category": bea,
                    "subsidy_rate_pct": rate,
                    "obligations_thousands": oblig,
                    "obligations_millions": oblig_m,
                    "avg_loan_size_thousands": avg_loan,
                    "subsidy_amount_thousands": subsidy_amt,
                })
    return rows


@st.cache_data
def load_budget_formulation() -> pd.DataFrame:
    """Load and flatten budget formulation data from tables 1 and 2."""
    sector_names = _load_sector_names()
    rows = _flatten_budget_table(DATA_DIR / "table1_historical.json", sector_names)
    rows += _flatten_budget_table(DATA_DIR / "table2_historical.json", sector_names)
    df = pd.DataFrame(rows)
    return df


# ---------------------------------------------------------------------------
# Reestimates (table 7 + 8)
# ---------------------------------------------------------------------------

@st.cache_data
def load_reestimates() -> pd.DataFrame:
    """Load and flatten the reestimates data (~30K rows)."""
    with open(DATA_DIR / "table7_8_reestimates.json") as f:
        data = json.load(f)

    sector_names = _load_sector_names()
    rows = []
    for prog in data["programs"].values():
        agency = normalize_agency(prog["agency"])
        if agency is None:
            continue
        if _is_aggregate_row(prog["canonical_name"]):
            continue

        pid = prog["program_id"]
        name = prog["canonical_name"]
        bureau = prog.get("bureau", "")
        sector = prog.get("sector", "")
        sector_name = sector_names.get(sector, "")
        credit_type = prog.get("credit_type", "")

        for by_str, by_data in prog.get("budget_years", {}).items():
            budget_year = int(by_str)
            for cohort in by_data.get("cohorts", []):
                cohort_year = cohort.get("cohort_year")
                orig_rate = _safe_float(cohort.get("original_subsidy_rate_percent"))
                reest_rate = _safe_float(cohort.get("current_reestimated_rate_percent"))
                chg_int = _safe_float(cohort.get("change_due_to_interest_rates_pct_pts"))
                chg_tech = _safe_float(cohort.get("change_due_to_technical_assumptions_pct_pts"))
                cur_re = _safe_float(cohort.get("current_reestimate_amount_thousands"))
                cur_re_m = cur_re / 1_000 if cur_re is not None else None
                net_lt = _safe_float(cohort.get("net_lifetime_reestimate_thousands"))
                net_lt_m = net_lt / 1_000 if net_lt is not None else None
                net_lt_ex = _safe_float(cohort.get("net_lifetime_reestimate_excl_interest_thousands"))
                disb = _safe_float(cohort.get("total_disbursements_to_date_thousands"))
                bal = _safe_float(cohort.get("outstanding_balance_thousands"))
                rows.append({
                    "program_id": pid,
                    "canonical_name": name,
                    "agency": agency,
                    "bureau": bureau,
                    "sector": sector,
                    "sector_name": sector_name,
                    "credit_type": credit_type,
                    "budget_year": budget_year,
                    "cohort_year": cohort_year,
                    "cohort_age": budget_year - cohort_year if cohort_year else None,
                    "original_subsidy_rate_pct": orig_rate,
                    "current_reestimated_rate_pct": reest_rate,
                    "rate_change_pct_pts": (
                        reest_rate - orig_rate
                        if reest_rate is not None and orig_rate is not None
                        else None
                    ),
                    "change_interest_rates_pct_pts": chg_int,
                    "change_technical_pct_pts": chg_tech,
                    "current_reestimate_thousands": cur_re,
                    "current_reestimate_millions": cur_re_m,
                    "net_lifetime_reestimate_thousands": net_lt,
                    "net_lifetime_reestimate_millions": net_lt_m,
                    "net_lifetime_excl_interest_thousands": net_lt_ex,
                    "total_disbursements_thousands": disb,
                    "outstanding_balance_thousands": bal,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Annual summary (aggregation from budget formulation)
# ---------------------------------------------------------------------------

@st.cache_data
def compute_annual_summary(bf_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate budget formulation (current-year cohort) per budget_year × credit_type."""
    current = bf_df[bf_df["cohort_type"] == "current"].copy()

    grouped = current.groupby(["budget_year", "credit_type"]).agg(
        total_obligations_millions=("obligations_millions", "sum"),
        n_programs=("program_id", "nunique"),
        total_subsidy_cost_millions=("subsidy_amount_thousands", lambda x: x.sum() / 1_000),
    ).reset_index()

    # Weighted average subsidy rate
    def _wavg(group):
        mask = group["subsidy_rate_pct"].notna() & group["obligations_thousands"].notna()
        g = group[mask]
        if g["obligations_thousands"].sum() == 0:
            return None
        return (g["subsidy_rate_pct"] * g["obligations_thousands"]).sum() / g["obligations_thousands"].sum()

    wavg = (
        current.groupby(["budget_year", "credit_type"])
        .apply(_wavg, include_groups=False)
        .reset_index(name="weighted_avg_subsidy_rate")
    )

    return grouped.merge(wavg, on=["budget_year", "credit_type"], how="left")
