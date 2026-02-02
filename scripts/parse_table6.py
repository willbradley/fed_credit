#!/usr/bin/env python3
"""
Parser for Federal Credit Supplement Table 6: Loan Guarantee Programs
Subsidy Estimates and Loan Characteristics (budget-year cohort).
"""

import json
import re
import pandas as pd
from pathlib import Path


def parse_value(val):
    """Parse a cell value, returning None for missing/empty values."""
    if pd.isna(val):
        return None
    if isinstance(val, str):
        val = val.strip()
        if val in ('......', '', '-'):
            return None
        val = val.lstrip('0123456789 ')
        if not val or val in ('......', '', '-'):
            return None
        try:
            return float(val)
        except ValueError:
            return val
    return val


KNOWN_BUREAUS = {
    'Farm Service Agency',
    'Rural Housing Service',
    'Rural Business-Cooperative Service',
    'Rural Utilities Service',
    'Forest Service',
    'Energy Programs',
    'Health Resources and Services Administration',
    'Administration for a Healthy America',
    'Public and Indian Housing Programs',
    'Community Planning and Development',
    'Housing Programs',
    'Government National Mortgage Association',
    'Bureau of Indian Affairs',
    'International Security Assistance',
    'Multilateral Assistance',
    'Agency for International Development',
    'United States International Development Finance Corporation',
    'Overseas Private Investment Corporation',
    'Benefits Programs',
    'Small Business Administration',
    'Export-Import Bank of the United States',
    'Office of the Secretary',
}


def _detect_cohort_year(df):
    """Detect the single cohort year from header rows."""
    year_re = re.compile(r'20\d{2}')
    years = set()
    for idx in range(min(5, len(df))):
        val = df.iloc[idx, 0]
        if pd.notna(val):
            for m in year_re.finditer(str(val)):
                y = int(m.group())
                if 2005 <= y <= 2035:
                    years.add(y)
    if years:
        return max(years)
    return None


def _parse_from_df(df, cohort_year=None, known_bureaus=None):
    """Parse Table 6 data from a DataFrame."""
    if known_bureaus is None:
        known_bureaus = KNOWN_BUREAUS
    if cohort_year is None:
        cohort_year = _detect_cohort_year(df)

    current_agency = None
    current_bureau = None
    current_account = None
    programs = []

    for idx in range(2, len(df)):
        row = df.iloc[idx]
        col0 = str(row[0]).strip() if pd.notna(row[0]) else ''
        if not col0:
            continue

        is_program = '......' in col0 or ('...' in col0 and ':' in col0)
        is_bureau_or_account = (col0.endswith(':') or
                                (col0.rstrip('0123456789').endswith(':') and not is_program))

        if is_program:
            program_name = col0.split(':')[0].strip().rstrip('.').rstrip('0123456789 ')

            subsidy_rate = parse_value(row[1])
            if subsidy_rate is None:
                continue

            program_data = {
                'agency': current_agency,
                'bureau': current_bureau,
                'account': current_account,
                'program': program_name,
                'cohort_year': cohort_year,
                'subsidy_rate_percent': subsidy_rate,
                'subsidy_composition': {
                    'defaults_net_of_recoveries': parse_value(row[2]),
                    'interest': parse_value(row[3]),
                    'fees': parse_value(row[4]),
                    'other': parse_value(row[5])
                },
                'loan_characteristics': {
                    'maturity_years': parse_value(row[6]),
                    'borrower_rate_percent': parse_value(row[7]),
                    'grace_period_years': parse_value(row[8]),
                    'upfront_fees_percent': parse_value(row[9]),
                    'annual_fees_percent': parse_value(row[10]),
                    'other_fees_percent': parse_value(row[11]),
                    'default_rate_percent': parse_value(row[12]),
                    'recovery_rate_percent': parse_value(row[13]),
                    'guarantee_percent': parse_value(row[14])
                }
            }
            programs.append(program_data)

        elif is_bureau_or_account:
            name = col0.rstrip('0123456789').rstrip(':').strip()
            if name in known_bureaus:
                current_bureau = name
                current_account = None
            else:
                current_account = name
        else:
            if 'Agency' not in col0 and 'BEA' not in col0 and 'Subsidy' not in col0:
                current_agency = col0.rstrip('0123456789 ')
                current_bureau = None
                current_account = None

    return {
        'metadata': {
            'source': f'Federal Credit Supplement, Budget of the U.S. Government, FY {cohort_year or ""}',
            'table': 'Table 6: Loan Guarantee Programs - Subsidy Estimates and Loan Characteristics',
            'cohort_year': cohort_year,
            'units': {
                'rates': 'percent',
                'maturity': 'years',
                'grace_period': 'years',
                'guarantee': 'percent of loan'
            }
        },
        'programs': programs
    }


def parse_table6(excel_path: str, sheet_name: str = 'Table 6',
                 engine: str = None) -> dict:
    """Parse Table 6 from the Federal Credit Supplement Excel file."""
    kwargs = {'header': None}
    if engine:
        kwargs['engine'] = engine
    df = pd.read_excel(excel_path, sheet_name=sheet_name, **kwargs)
    return _parse_from_df(df)


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    excel_path = project_root / 'data' / 'raw' / 'BUDGET-2026-FCS.xlsx'
    output_path = project_root / 'data' / 'processed' / 'table6_loan_guarantee_characteristics_2026.json'

    data = parse_table6(str(excel_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Parsed {len(data['programs'])} loan guarantee programs (budget-year cohort)")
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
