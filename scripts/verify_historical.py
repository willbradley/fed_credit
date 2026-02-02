#!/usr/bin/env python3
"""
Validation and quality checks for the unified historical dataset.
"""

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UNIFIED_DIR = PROJECT_ROOT / "data" / "processed" / "historical" / "unified"
BY_YEAR_DIR = PROJECT_ROOT / "data" / "processed" / "historical" / "by_year"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def check_unclassified(master):
    """No programs should be unclassified."""
    issues = []
    for pid, m in master.items():
        if not m.get("sector"):
            issues.append(f"{pid} ({m['canonical_name']}): no sector")
    return issues


def check_sector_distribution(master):
    """Report sector distribution."""
    counts = Counter(m["sector"] for m in master.values())
    return dict(counts.most_common())


def check_short_lived_programs(master, threshold=2):
    """Flag programs appearing in very few years (may need aliases)."""
    flagged = []
    for pid, m in master.items():
        years = m.get("budget_years_seen", [])
        if len(years) <= threshold:
            flagged.append(f"{pid} {m['canonical_name']}: only in {years}")
    return flagged


def check_cross_table_consistency(unified_dir):
    """Check that Table 1 programs appear in Tables 3/5/7/9 for overlapping years."""
    issues = []
    t1_path = unified_dir / "table1_historical.json"
    if not t1_path.exists():
        return ["table1_historical.json not found"]

    t1 = load_json(t1_path)
    t1_pids = set(t1.get("programs", {}).keys())

    for fname in ["table3_4_characteristics.json", "table7_8_reestimates.json",
                   "table9_10_disbursements.json"]:
        path = unified_dir / fname
        if not path.exists():
            continue
        other = load_json(path)
        other_pids = set(other.get("programs", {}).keys())
        missing = t1_pids - other_pids
        if len(missing) > len(t1_pids) * 0.5:
            issues.append(f"{fname}: {len(missing)}/{len(t1_pids)} Table 1 programs missing (expected for some tables)")
    return issues


def check_subsidy_rate_jumps(unified_dir, threshold_pct=20):
    """Flag >threshold pct pt subsidy rate jumps year-over-year."""
    issues = []
    for fname in ["table1_historical.json", "table2_historical.json"]:
        path = unified_dir / fname
        if not path.exists():
            continue
        data = load_json(path)
        for pid, prog in data.get("programs", {}).items():
            years = sorted(prog.get("budget_years", {}).keys())
            prev_rate = None
            for yr in years:
                yr_data = prog["budget_years"][yr]
                cohorts = yr_data.get("cohorts", {})
                # Get the budget-year cohort rate
                rates = [c.get("subsidy_rate_percent") for c in cohorts.values()
                         if isinstance(c, dict) and c.get("subsidy_rate_percent") is not None]
                if not rates:
                    prev_rate = None
                    continue
                rate = rates[-1]
                if isinstance(rate, (int, float)) and prev_rate is not None:
                    jump = abs(rate - prev_rate)
                    if jump > threshold_pct:
                        issues.append(f"{pid} ({prog['canonical_name']}): {prev_rate:.1f}% -> {rate:.1f}% ({yr})")
                prev_rate = rate if isinstance(rate, (int, float)) else None
    return issues


def check_year_coverage(by_year_dir):
    """Report coverage matrix."""
    files = sorted(by_year_dir.glob("fy*_table*.json"))
    coverage = {}
    for f in files:
        parts = f.stem.split("_")
        year = int(parts[0][2:])
        table = int(parts[1].replace("table", ""))
        coverage.setdefault(year, set()).add(table)
    return coverage


def run_all():
    print("=" * 60)
    print("HISTORICAL DATASET VERIFICATION")
    print("=" * 60)

    all_passed = True

    # 1. Coverage
    print("\n--- Year/Table Coverage ---")
    coverage = check_year_coverage(BY_YEAR_DIR)
    if not coverage:
        print("  NO DATA FOUND. Run historical_pipeline.py first.")
        return
    for year in sorted(coverage):
        tables = sorted(coverage[year])
        print(f"  FY{year}: Tables {tables}")
    total_pairs = sum(len(v) for v in coverage.values())
    print(f"  Total: {total_pairs} (year, table) pairs across {len(coverage)} years")

    # 2. Programs master
    master_path = UNIFIED_DIR / "programs_master.json"
    if not master_path.exists():
        print("\n  programs_master.json not found. Run build_unified_dataset.py first.")
        return
    master = load_json(master_path)
    print(f"\n--- Programs Master: {len(master)} programs ---")

    # 3. Unclassified
    print("\n--- Sector Classification ---")
    unclassified = check_unclassified(master)
    if unclassified:
        print(f"  FAIL: {len(unclassified)} unclassified programs:")
        for u in unclassified[:10]:
            print(f"    {u}")
        all_passed = False
    else:
        print("  PASS: All programs classified")

    # 4. Sector distribution
    print("\n--- Sector Distribution ---")
    dist = check_sector_distribution(master)
    for sector, count in dist.items():
        print(f"  {sector:25s}: {count}")

    # 5. Short-lived programs
    print("\n--- Short-Lived Programs (<=2 years) ---")
    short = check_short_lived_programs(master)
    if short:
        print(f"  {len(short)} programs in <=2 years (may need aliases):")
        for s in short[:15]:
            print(f"    {s}")
    else:
        print("  None found")

    # 6. Cross-table consistency
    print("\n--- Cross-Table Consistency ---")
    cross = check_cross_table_consistency(UNIFIED_DIR)
    if cross:
        for c in cross:
            print(f"  NOTE: {c}")
    else:
        print("  PASS: Cross-table consistency OK")

    # 7. Subsidy rate jumps
    print("\n--- Subsidy Rate Jumps (>20 pct pts) ---")
    jumps = check_subsidy_rate_jumps(UNIFIED_DIR)
    if jumps:
        print(f"  {len(jumps)} large jumps found:")
        for j in jumps[:15]:
            print(f"    {j}")
    else:
        print("  None found")

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED - review above")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
