#!/usr/bin/env python3
"""
Parser for Federal Credit Supplement Table 9: Direct Loan Programs
Disbursement Schedules - percentage of disbursements by year.
"""

import json
import pandas as pd
from pathlib import Path


def parse_value(val):
    """Parse a cell value, returning None for missing/empty values."""
    if pd.isna(val):
        return None
    if isinstance(val, str):
        val = val.strip()
        if val in ('......', '', '-', '*'):
            return None
        try:
            return float(val)
        except ValueError:
            return val
    return val


def get_indent(val):
    """Get the indentation level (number of leading spaces)."""
    if pd.isna(val):
        return 0
    val_str = str(val)
    return len(val_str) - len(val_str.lstrip())


KNOWN_BUREAUS = {
    'Farm Service Agency',
    'Rural Housing Service',
    'Rural Business-Cooperative Service',
    'Rural Utilities Service',
    'National Oceanic and Atmospheric Administration',
    'National Institute of Standards and Technology',
    'Office of Postsecondary Education',
    'Office of Federal Student Aid',
    'Energy Programs',
    'Federal Emergency Management Agency',
    'Housing Programs',
    'Administration of Foreign Affairs',
    'International Security Assistance',
    'Agency for International Development',
    'United States International Development Finance Corporation',
    'Overseas Private Investment Corporation',
    'Office of the Secretary',
    'Maritime Administration',
    'Departmental Offices',
    'Benefits Programs',
    'Corps of Engineers--Civil Works',
    'Environmental Protection Agency',
    'Small Business Administration',
    'Export-Import Bank of the United States',
    'Procurement',
}


def _parse_from_df(df, known_bureaus=None):
    """Parse Table 9 data from a DataFrame."""
    if known_bureaus is None:
        known_bureaus = KNOWN_BUREAUS

    current_agency = None
    current_bureau = None
    current_account = None
    programs = []

    for idx in range(2, len(df)):
        row = df.iloc[idx]
        raw_col0 = row[0]

        if pd.isna(raw_col0):
            continue

        raw_str = str(raw_col0)
        indent = get_indent(raw_col0)
        col0 = raw_str.strip()

        if not col0:
            continue

        has_data = pd.notna(row[1]) and str(row[1]).strip() not in ('', 'NaN')

        if has_data and ('...' in col0 or col0.endswith(':')):
            program_name = col0.split(':')[0].strip().rstrip('.')

            program_data = {
                'agency': current_agency,
                'bureau': current_bureau,
                'account': current_account,
                'program': program_name,
                'disbursement_schedule_percent': {
                    'year_1': parse_value(row[1]),
                    'year_2': parse_value(row[2]),
                    'year_3': parse_value(row[3]),
                    'year_4': parse_value(row[4]),
                    'year_5': parse_value(row[5]),
                    'year_6': parse_value(row[6]),
                    'year_7': parse_value(row[7]),
                    'year_8': parse_value(row[8]),
                    'year_9': parse_value(row[9]),
                    'year_10_plus': parse_value(row[10])
                }
            }
            programs.append(program_data)

        elif col0.endswith(':') or col0.rstrip('0123456789').endswith(':'):
            name = col0.rstrip(':').rstrip('0123456789 ').strip()

            if indent == 0:
                if name in known_bureaus:
                    current_bureau = name
                    current_account = None
                else:
                    current_bureau = name
                    current_account = None
            elif indent <= 3:
                current_account = name

        else:
            if indent == 0 and len(col0) > 0 and col0[0].isupper():
                if 'Agency' not in col0 and 'Bureau' not in col0 and 'Percentage' not in col0:
                    current_agency = col0.rstrip('0123456789 ')
                    current_bureau = None
                    current_account = None

    return {
        'metadata': {
            'source': 'Federal Credit Supplement, Budget of the U.S. Government',
            'table': 'Table 9: Direct Loan Programs - Disbursement Schedules',
            'description': 'Percentage of total disbursements made in each year after origination',
            'units': 'percent'
        },
        'programs': programs
    }


def parse_table9(excel_path: str, sheet_name: str = 'Table 9',
                 engine: str = None) -> dict:
    """Parse Table 9 from the Federal Credit Supplement Excel file."""
    kwargs = {'header': None}
    if engine:
        kwargs['engine'] = engine
    df = pd.read_excel(excel_path, sheet_name=sheet_name, **kwargs)
    return _parse_from_df(df)


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    excel_path = project_root / 'data' / 'raw' / 'BUDGET-2026-FCS.xlsx'
    output_path = project_root / 'data' / 'processed' / 'table9_direct_loan_disbursement_schedules.json'

    data = parse_table9(str(excel_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Parsed {len(data['programs'])} direct loan disbursement schedules")
    print(f"Output saved to: {output_path}")

    agencies = {}
    for p in data['programs']:
        agency = p['agency'] or 'Unknown'
        agencies[agency] = agencies.get(agency, 0) + 1

    print("\nPrograms by agency:")
    for agency, count in sorted(agencies.items()):
        print(f"  {agency}: {count}")


if __name__ == '__main__':
    main()
