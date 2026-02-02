#!/usr/bin/env python3
"""
Resolves file path, sheet name, and pandas engine for any (year, table) pair.

Handles two file layouts:
  - FY2024-2026: single consolidated BUDGET-{YEAR}-FCS.xlsx with sheet "Table N"
  - FY2010-2023: per-table BUDGET-{YEAR}-FCS-table{N}.xlsx with sheet "Table N"

Auto-detects OLE (.xls) vs OOXML (.xlsx) via magic bytes to select the correct
pandas engine (xlrd vs openpyxl).
"""

from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def _detect_engine(filepath: Path) -> str:
    """Detect Excel format from magic bytes and return pandas engine name."""
    with open(filepath, "rb") as f:
        magic = f.read(4)
    if magic[:4] == b"\xd0\xcf\x11\xe0":
        return "xlrd"
    return "openpyxl"


def resolve(year: int, table: int, raw_dir: Path = None) -> dict:
    """
    Resolve file path, sheet name, and engine for a (year, table) pair.

    Returns dict with keys:
        path       – Path object to the Excel file
        sheet_name – sheet name string (e.g. "Table 1")
        engine     – "openpyxl" or "xlrd"

    Raises FileNotFoundError if no matching file exists.
    """
    if raw_dir is None:
        raw_dir = RAW_DIR

    sheet_name = f"Table {table}"

    # Try single consolidated file first (FY2024+, but also check for any year)
    single = raw_dir / f"BUDGET-{year}-FCS.xlsx"
    if single.exists():
        return {
            "path": single,
            "sheet_name": sheet_name,
            "engine": _detect_engine(single),
        }

    # Try per-table file (.xlsx)
    per_table = raw_dir / f"BUDGET-{year}-FCS-table{table}.xlsx"
    if per_table.exists():
        return {
            "path": per_table,
            "sheet_name": sheet_name,
            "engine": _detect_engine(per_table),
        }

    # Try per-table file (.xls)
    per_table_xls = raw_dir / f"BUDGET-{year}-FCS-table{table}.xls"
    if per_table_xls.exists():
        return {
            "path": per_table_xls,
            "sheet_name": sheet_name,
            "engine": "xlrd",
        }

    raise FileNotFoundError(
        f"No Excel file found for FY{year} Table {table} in {raw_dir}"
    )


def discover_available(raw_dir: Path = None,
                       start_year: int = 2010,
                       end_year: int = 2026) -> dict:
    """
    Scan raw_dir and return {(year, table): resolve_dict} for all available files.
    """
    if raw_dir is None:
        raw_dir = RAW_DIR

    available = {}
    for year in range(start_year, end_year + 1):
        for table in range(1, 11):
            try:
                info = resolve(year, table, raw_dir)
                available[(year, table)] = info
            except FileNotFoundError:
                pass
    return available
