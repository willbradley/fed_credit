#!/usr/bin/env python3
"""
Historical pipeline: parse all FCS years into per-year JSON files.

Usage:
    python scripts/historical_pipeline.py [--start-year 2010] [--end-year 2026] [--tables 1,2,3]
"""

import argparse
import json
import sys
import time
import traceback
import pandas as pd
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.file_resolver import resolve, discover_available
from scripts.parse_table1 import _parse_from_df as parse_t1, KNOWN_BUREAUS as KB1
from scripts.parse_table2 import _parse_from_df as parse_t2, KNOWN_BUREAUS as KB2
from scripts.parse_table3 import _parse_from_df as parse_t3, KNOWN_BUREAUS as KB3
from scripts.parse_table4 import _parse_from_df as parse_t4, KNOWN_BUREAUS as KB4
from scripts.parse_table5 import _parse_from_df as parse_t5, KNOWN_BUREAUS as KB5
from scripts.parse_table6 import _parse_from_df as parse_t6, KNOWN_BUREAUS as KB6
from scripts.parse_table7 import _parse_from_df as parse_t7, KNOWN_BUREAUS as KB7
from scripts.parse_table8 import _parse_from_df as parse_t8, KNOWN_BUREAUS as KB8
from scripts.parse_table9 import _parse_from_df as parse_t9, KNOWN_BUREAUS as KB9
from scripts.parse_table10 import _parse_from_df as parse_t10, KNOWN_BUREAUS as KB10

# Union of all known bureaus across all parsers
MASTER_BUREAUS = KB1 | KB2 | KB3 | KB4 | KB5 | KB6 | KB7 | KB8 | KB9 | KB10

PARSERS = {
    1: parse_t1, 2: parse_t2, 3: parse_t3, 4: parse_t4, 5: parse_t5,
    6: parse_t6, 7: parse_t7, 8: parse_t8, 9: parse_t9, 10: parse_t10,
}

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "historical" / "by_year"


def _build_kwargs(table: int, budget_year: int) -> dict:
    """Build keyword arguments for the _parse_from_df call."""
    kwargs = {"known_bureaus": MASTER_BUREAUS}
    if table in (1, 2):
        kwargs["cohort_years"] = (budget_year - 1, budget_year)
    elif table in (3, 4):
        kwargs["cohort_year"] = budget_year - 1
    elif table in (5, 6):
        kwargs["cohort_year"] = budget_year
    # Tables 7-10 need no extra kwargs
    return kwargs


def parse_one(year: int, table: int) -> dict:
    """Parse a single (year, table) pair and return the result dict."""
    info = resolve(year, table)
    engine_kw = {"engine": info["engine"]} if info["engine"] else {}
    df = pd.read_excel(
        info["path"], sheet_name=info["sheet_name"], header=None, **engine_kw
    )
    kwargs = _build_kwargs(table, year)
    return PARSERS[table](df, **kwargs)


def run_pipeline(start_year: int, end_year: int, tables: list[int]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    available = discover_available(start_year=start_year, end_year=end_year)

    results = {"success": [], "failed": [], "skipped": []}
    t0 = time.time()

    for year in range(start_year, end_year + 1):
        for table in tables:
            key = (year, table)
            if key not in available:
                results["skipped"].append({"year": year, "table": table, "reason": "file not found"})
                continue

            out_path = OUTPUT_DIR / f"fy{year}_table{table}.json"
            try:
                data = parse_one(year, table)
                with open(out_path, "w") as f:
                    json.dump(data, f, indent=2)
                n = len(data.get("programs", []))
                results["success"].append({"year": year, "table": table, "programs": n})
                print(f"  FY{year} Table {table:2d}: {n:3d} programs -> {out_path.name}")
            except Exception as e:
                tb = traceback.format_exc()
                results["failed"].append({"year": year, "table": table, "error": str(e), "traceback": tb})
                print(f"  FY{year} Table {table:2d}: FAILED - {e}")

    elapsed = time.time() - t0

    # Write manifest
    manifest = {
        "run_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 1),
        "year_range": [start_year, end_year],
        "tables": tables,
        "summary": {
            "success": len(results["success"]),
            "failed": len(results["failed"]),
            "skipped": len(results["skipped"]),
        },
        "success": results["success"],
        "failed": [{"year": f["year"], "table": f["table"], "error": f["error"]} for f in results["failed"]],
        "skipped": results["skipped"],
    }
    manifest_path = OUTPUT_DIR.parent / "pipeline_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nPipeline complete in {elapsed:.1f}s")
    print(f"  Success: {manifest['summary']['success']}")
    print(f"  Failed:  {manifest['summary']['failed']}")
    print(f"  Skipped: {manifest['summary']['skipped']}")
    print(f"  Manifest: {manifest_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Parse historical FCS data")
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--tables", type=str, default="1,2,3,4,5,6,7,8,9,10",
                        help="Comma-separated table numbers")
    args = parser.parse_args()
    tables = [int(t) for t in args.tables.split(",")]
    run_pipeline(args.start_year, args.end_year, tables)


if __name__ == "__main__":
    main()
