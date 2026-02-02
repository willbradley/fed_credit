#!/usr/bin/env python3
"""
Merge per-year JSON files into unified historical datasets with
program IDs and sector classifications.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.program_matcher import ProgramRegistry
from scripts.sector_taxonomy import classify_program, export_taxonomy

BY_YEAR_DIR = PROJECT_ROOT / "data" / "processed" / "historical" / "by_year"
UNIFIED_DIR = PROJECT_ROOT / "data" / "processed" / "historical" / "unified"

# Table groupings for unified output files
TABLE_GROUPS = {
    "table1_historical.json": {
        "tables": [1],
        "description": "Direct Loan Programs - Budget Formulation, all years",
        "credit_type": "direct_loan",
    },
    "table2_historical.json": {
        "tables": [2],
        "description": "Loan Guarantee Programs - Budget Formulation, all years",
        "credit_type": "loan_guarantee",
    },
    "table3_4_characteristics.json": {
        "tables": [3, 4],
        "description": "Subsidy Estimates and Loan Characteristics (prior-year cohort), all years",
    },
    "table5_6_characteristics.json": {
        "tables": [5, 6],
        "description": "Subsidy Estimates and Loan Characteristics (budget-year cohort), all years",
    },
    "table7_8_reestimates.json": {
        "tables": [7, 8],
        "description": "Subsidy Reestimates, all years",
    },
    "table9_10_disbursements.json": {
        "tables": [9, 10],
        "description": "Disbursement Schedules, all years",
    },
}


def _load_by_year():
    """Load all by_year JSON files, return dict of {(year,table): data}."""
    all_data = {}
    for f in sorted(BY_YEAR_DIR.glob("fy*_table*.json")):
        parts = f.stem.split("_")  # fy2026_table1
        year = int(parts[0][2:])
        table = int(parts[1].replace("table", ""))
        with open(f) as fh:
            all_data[(year, table)] = json.load(fh)
    return all_data


def _program_key_from_record(rec):
    return (rec.get("agency") or "", rec.get("bureau") or "",
            rec.get("account") or "", rec.get("program") or "")


def _extract_subsidy_rates(all_data, registry):
    """
    Extract original subsidy rates from Tables 7/8 by program_id and cohort_year.

    Returns: {program_id: {cohort_year_int: original_rate_float}}
    """
    rates = {}
    for (year, table), data in all_data.items():
        if table not in (7, 8):
            continue
        for rec in data.get("programs", []):
            a, b, c, p = _program_key_from_record(rec)
            pid = registry.get_id(a, b, c, p)
            if pid is None:
                continue
            for cohort in rec.get("cohorts", []):
                cy = cohort.get("cohort_year")
                rate = cohort.get("original_subsidy_rate_percent")
                if cy is None or rate is None:
                    continue
                if not isinstance(rate, (int, float)):
                    continue
                pid_rates = rates.setdefault(pid, {})
                # Keep the first observation (earliest budget year report)
                if cy not in pid_rates:
                    pid_rates[cy] = rate
    return rates


def build():
    UNIFIED_DIR.mkdir(parents=True, exist_ok=True)
    all_data = _load_by_year()
    if not all_data:
        print("No by_year data found. Run historical_pipeline.py first.")
        return

    years_found = sorted(set(y for y, t in all_data))
    print(f"Loaded {len(all_data)} (year, table) files spanning FY{years_found[0]}-FY{years_found[-1]}")

    registry = ProgramRegistry()

    # Pass 1: register all programs across all tables/years
    for (year, table), data in sorted(all_data.items()):
        for rec in data.get("programs", []):
            a, b, c, p = _program_key_from_record(rec)
            registry.register(a, b, c, p, year)

    pre_reconcile = len(registry.all_programs())
    print(f"Registered {pre_reconcile} unique programs (before reconciliation)")

    # Extract original subsidy rates from Tables 7/8 for merge validation
    subsidy_rates = _extract_subsidy_rates(all_data, registry)
    print(f"Extracted subsidy rates for {len(subsidy_rates)} programs "
          f"({sum(len(v) for v in subsidy_rates.values())} cohort-year observations)")

    # Pass 2: fuzzy reconciliation
    stats = registry.reconcile(subsidy_rates=subsidy_rates, rate_tolerance=0.5)
    print(f"Reconciliation: {stats['merges']} merges, "
          f"{stats['blocked_by_rates']} blocked by rate mismatch, "
          f"{stats['programs_after']} programs remain")

    # Set canonical names from most recent budget year (FY2026 preferred)
    registry.finalize_canonical_names()

    all_programs = registry.all_programs()

    # Classify sectors
    for pid, meta in all_programs.items():
        meta["sector"] = classify_program(
            meta["agency"], meta["bureau"], meta["account"], meta["canonical_name"]
        )

    # Write programs_master.json
    master = {}
    for pid, meta in sorted(all_programs.items()):
        master[pid] = {
            "program_id": pid,
            "canonical_name": meta["canonical_name"],
            "agency": meta["agency"],
            "bureau": meta["bureau"],
            "account": meta["account"],
            "sector": meta["sector"],
            "name_variants": sorted(set(meta["name_variants"])),
            "budget_years_seen": sorted(meta["budget_years_seen"]),
        }
    with open(UNIFIED_DIR / "programs_master.json", "w") as f:
        json.dump(master, f, indent=2)
    print(f"Wrote programs_master.json ({len(master)} programs)")

    # Write sector_taxonomy.json
    export_taxonomy(UNIFIED_DIR / "sector_taxonomy.json")

    # Pass 2: build unified output files
    for out_name, group in TABLE_GROUPS.items():
        table_nums = group["tables"]
        programs_out = {}

        for (year, table), data in sorted(all_data.items()):
            if table not in table_nums:
                continue
            for rec in data.get("programs", []):
                a, b, c, p = _program_key_from_record(rec)
                pid = registry.get_id(a, b, c, p)
                if pid is None:
                    continue

                if pid not in programs_out:
                    meta = all_programs[pid]
                    programs_out[pid] = {
                        "program_id": pid,
                        "canonical_name": meta["canonical_name"],
                        "agency": meta["agency"],
                        "bureau": meta["bureau"],
                        "sector": meta["sector"],
                        "credit_type": group.get("credit_type", _infer_credit_type(table)),
                        "budget_years": {},
                    }

                # Store per-year data
                year_key = str(year)
                # Strip hierarchy fields, keep only data
                rec_data = {k: v for k, v in rec.items()
                            if k not in ("agency", "bureau", "account", "program")}
                # For tables with multiple tables merged (3+4, etc.), tag the table
                if len(table_nums) > 1:
                    rec_data["_table"] = table
                programs_out[pid]["budget_years"][year_key] = rec_data

        unified = {
            "metadata": {
                "description": group["description"],
                "budget_years": sorted(set(
                    y for y, t in all_data if t in table_nums
                )),
                "tables_included": table_nums,
            },
            "programs": programs_out,
        }
        with open(UNIFIED_DIR / out_name, "w") as f:
            json.dump(unified, f, indent=2)
        print(f"Wrote {out_name} ({len(programs_out)} programs)")

    print(f"\nAll unified files written to {UNIFIED_DIR}")


def _infer_credit_type(table):
    if table in (1, 3, 5, 7, 9):
        return "direct_loan"
    return "loan_guarantee"


if __name__ == "__main__":
    build()
