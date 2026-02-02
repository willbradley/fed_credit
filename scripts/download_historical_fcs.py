#!/usr/bin/env python3
"""
Download historical Federal Credit Supplement (FCS) Excel files from
govinfo.gov and White House archive sites.

Covers FY2010 through FY2026. Files are saved to data/raw/ with
consistent naming: BUDGET-{YEAR}-FCS.xlsx (single file) or
BUDGET-{YEAR}-FCS-table{N}.xlsx (individual tables).

URL sources by administration:
  - FY2026:      whitehouse.gov / govinfo.gov (single XLSX)
  - FY2024-2025: govinfo.gov / bidenwhitehouse.archives.gov (single XLSX)
  - FY2022-2023: bidenwhitehouse.archives.gov (single or per-table)
  - FY2018-2021: trumpwhitehouse.archives.gov (10 per-table XLSX)
  - FY2010-2017: obamawhitehouse.archives.gov (10 per-table XLSX)
"""

import os
import sys
import time
import urllib.request
import urllib.error
import ssl
import json
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Number of tables in the FCS
TABLE_NUMBERS = list(range(1, 11))

# ---------------------------------------------------------------------------
# URL definitions by fiscal year
# ---------------------------------------------------------------------------

def govinfo_single(year):
    """Single consolidated XLSX on govinfo.gov (FY2024+)."""
    return f"https://www.govinfo.gov/content/pkg/BUDGET-{year}-FCS/xls/BUDGET-{year}-FCS.xlsx"


def whitehouse_current(year):
    """Current whitehouse.gov (FY2026)."""
    return f"https://www.whitehouse.gov/wp-content/uploads/2025/04/BUDGET-{year}-CREDIT.xlsx"


def biden_archive_single(year, upload_dates):
    """Biden-era single consolidated XLSX."""
    urls = []
    for ym in upload_dates:
        urls.append(
            f"https://bidenwhitehouse.archives.gov/wp-content/uploads/{ym}/cr_supp_tables_fy{year}.xlsx"
        )
    return urls


def biden_archive_tables(year, upload_dates):
    """Biden-era individual table XLSX files."""
    urls = {}
    for t in TABLE_NUMBERS:
        urls[t] = []
        for ym in upload_dates:
            urls[t].append(
                f"https://bidenwhitehouse.archives.gov/wp-content/uploads/{ym}/cr_{t}_fy{year}.xlsx"
            )
            urls[t].append(
                f"https://bidenwhitehouse.archives.gov/wp-content/uploads/{ym}/cr_{t}_fy{str(year)[-2:]}.xlsx"
            )
    return urls


def trump_archive_tables(year, upload_dates):
    """Trump-era individual table XLSX files."""
    yy = str(year)[-2:]
    urls = {}
    for t in TABLE_NUMBERS:
        urls[t] = []
        for ym in upload_dates:
            urls[t].append(
                f"https://trumpwhitehouse.archives.gov/wp-content/uploads/{ym}/cr_{t}_fy{yy}.xlsx"
            )
            # Some files may not have _fy suffix
            urls[t].append(
                f"https://trumpwhitehouse.archives.gov/wp-content/uploads/{ym}/cr_{t}.xlsx"
            )
    return urls


def obama_archive_tables(year):
    """Obama-era individual table XLSX files."""
    urls = {}
    for t in TABLE_NUMBERS:
        urls[t] = [
            f"https://obamawhitehouse.archives.gov/sites/default/files/omb/budget/fy{year}/assets/cr_{t}.xlsx",
            # Some years may use xls instead of xlsx
            f"https://obamawhitehouse.archives.gov/sites/default/files/omb/budget/fy{year}/assets/cr_{t}.xls",
        ]
    return urls


# Mapping of fiscal year -> list of candidate upload date prefixes (YYYY/MM)
# Budget is typically released in Feb-Mar of the prior fiscal year
TRUMP_UPLOAD_DATES = {
    2018: ["2017/05", "2017/02", "2017/03"],
    2019: ["2018/02", "2018/03", "2018/01"],
    2020: ["2019/03", "2019/02", "2019/04"],
    2021: ["2020/02", "2020/01", "2020/03"],
}

BIDEN_UPLOAD_DATES = {
    2022: ["2021/05", "2021/06", "2021/04", "2021/03"],
    2023: ["2022/03", "2022/04", "2022/02"],
    2024: ["2023/03", "2023/04", "2023/02"],
    2025: ["2024/03", "2024/04", "2024/02"],
}


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def create_opener():
    """Create a URL opener with appropriate headers."""
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (Federal Credit Budget Center research tool)"),
        ("Accept", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"),
    ]
    return opener


def try_download(url, dest_path, opener, timeout=30):
    """Attempt to download a file. Returns True on success, False on failure."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Federal Credit Budget Center research tool)")
        response = urllib.request.urlopen(req, timeout=timeout, context=ctx)

        content = response.read()
        if len(content) < 500:
            # Too small to be a real XLSX — likely an error page
            return False

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(content)

        size_kb = len(content) / 1024
        print(f"  -> Saved {dest_path.name} ({size_kb:.1f} KB)")
        return True

    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
        return False


def try_urls(urls, dest_path, opener):
    """Try a list of URLs in order. Return True on first success."""
    for url in urls:
        print(f"  Trying: {url}")
        if try_download(url, dest_path, opener):
            return True
        time.sleep(0.5)  # Be polite to servers
    return False


# ---------------------------------------------------------------------------
# Per-year download strategies
# ---------------------------------------------------------------------------

def download_single_file(year, opener):
    """Try to download a single consolidated XLSX for the given year."""
    dest = RAW_DIR / f"BUDGET-{year}-FCS.xlsx"
    if dest.exists():
        print(f"  Already exists: {dest.name}")
        return True

    urls = []

    # govinfo.gov (best source for FY2024+)
    urls.append(govinfo_single(year))

    # Current whitehouse.gov
    if year == 2026:
        urls.append(whitehouse_current(year))

    # Biden archive
    if year in BIDEN_UPLOAD_DATES:
        urls.extend(biden_archive_single(year, BIDEN_UPLOAD_DATES[year]))

    return try_urls(urls, dest, opener)


def download_table_files(year, opener):
    """Download individual table files and note which ones succeeded."""
    results = {}

    # Build URL candidates per table
    if year in TRUMP_UPLOAD_DATES:
        table_urls = trump_archive_tables(year, TRUMP_UPLOAD_DATES[year])
    elif year in BIDEN_UPLOAD_DATES:
        table_urls = biden_archive_tables(year, BIDEN_UPLOAD_DATES[year])
    elif 2010 <= year <= 2017:
        table_urls = obama_archive_tables(year)
    else:
        print(f"  No table URL patterns for FY{year}")
        return results

    for t in TABLE_NUMBERS:
        dest = RAW_DIR / f"BUDGET-{year}-FCS-table{t}.xlsx"
        if dest.exists():
            print(f"  Already exists: {dest.name}")
            results[t] = True
            continue

        # Also check .xls extension
        dest_xls = RAW_DIR / f"BUDGET-{year}-FCS-table{t}.xls"
        if dest_xls.exists():
            print(f"  Already exists: {dest_xls.name}")
            results[t] = True
            continue

        urls = table_urls.get(t, [])
        # Try xlsx dest first, then xls
        success = try_urls(urls, dest, opener)
        if not success:
            # For obama-era .xls files, the try_download already handles
            # saving to the xlsx path; content type doesn't change the data
            pass
        results[t] = success
        time.sleep(0.3)

    return results


def download_year(year, opener):
    """Download FCS data for a given fiscal year."""
    print(f"\n{'='*60}")
    print(f"FY{year}")
    print(f"{'='*60}")

    # FY2024-2026: try single file first (preferred)
    if year >= 2024:
        if download_single_file(year, opener):
            return {"type": "single", "success": True}

    # FY2022-2023: try single file from Biden archive, fall back to tables
    if 2022 <= year <= 2023:
        if download_single_file(year, opener):
            return {"type": "single", "success": True}
        print("  Single file not found, trying individual tables...")

    # FY2010-2023: try individual table files
    if year <= 2023:
        results = download_table_files(year, opener)
        succeeded = sum(1 for v in results.values() if v)
        total = len(TABLE_NUMBERS)
        print(f"  Tables downloaded: {succeeded}/{total}")
        return {
            "type": "tables",
            "success": succeeded > 0,
            "tables_found": succeeded,
            "tables_total": total,
            "details": results,
        }

    return {"type": "unknown", "success": False}


# ---------------------------------------------------------------------------
# Also try govinfo.gov PDF as fallback for years without XLSX
# ---------------------------------------------------------------------------

def download_pdf_fallback(year, opener):
    """Download PDF version as fallback when XLSX is unavailable."""
    dest = RAW_DIR / f"BUDGET-{year}-FCS.pdf"
    if dest.exists():
        print(f"  PDF already exists: {dest.name}")
        return True

    url = f"https://www.govinfo.gov/content/pkg/BUDGET-{year}-FCS/pdf/BUDGET-{year}-FCS.pdf"
    print(f"  Trying PDF fallback: {url}")
    return try_download(url, dest, opener, timeout=60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    start_year = 2010
    end_year = 2026

    if len(sys.argv) > 1:
        start_year = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_year = int(sys.argv[2])

    print(f"Federal Credit Supplement Historical Downloader")
    print(f"Downloading FY{start_year} through FY{end_year}")
    print(f"Destination: {RAW_DIR}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    opener = create_opener()

    summary = {}

    for year in range(start_year, end_year + 1):
        result = download_year(year, opener)
        summary[year] = result

        # If XLSX download failed entirely, try PDF fallback
        if not result.get("success"):
            print(f"  XLSX not found for FY{year}, trying PDF fallback...")
            pdf_ok = download_pdf_fallback(year, opener)
            result["pdf_fallback"] = pdf_ok

        time.sleep(1)  # Rate limiting between years

    # Print summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")

    for year in range(start_year, end_year + 1):
        r = summary[year]
        if r.get("success"):
            if r["type"] == "single":
                status = "SINGLE XLSX"
            else:
                status = f"TABLES: {r.get('tables_found', 0)}/{r.get('tables_total', 10)}"
            print(f"  FY{year}: OK - {status}")
        else:
            pdf = "PDF available" if r.get("pdf_fallback") else "NO FILES"
            print(f"  FY{year}: XLSX MISSING - {pdf}")

    # Save manifest
    manifest_path = RAW_DIR / "download_manifest.json"
    manifest = {
        "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "years": {str(y): summary[y] for y in range(start_year, end_year + 1)},
    }
    # Clean up non-serializable items
    for y_data in manifest["years"].values():
        if "details" in y_data:
            y_data["details"] = {str(k): v for k, v in y_data["details"].items()}

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
