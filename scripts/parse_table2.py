#!/usr/bin/env python3
"""
Parser for Federal Credit Supplement Table 2: Loan Guarantee Programs
Extracts budget formulation estimates for two cohort years.
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


def _detect_cohort_years(df):
    """Detect the two cohort years from header rows."""
    year_re = re.compile(r'20\d{2}')
    years = set()
    for idx in range(min(5, len(df))):
        for col_idx in range(min(10, len(df.columns))):
            val = df.iloc[idx, col_idx]
            if pd.notna(val):
                for m in year_re.finditer(str(val)):
                    y = int(m.group())
                    if 2005 <= y <= 2035:
                        years.add(y)
    years = sorted(years)
    if len(years) >= 2:
        return years[-2], years[-1]
    if len(years) == 1:
        return years[0] - 1, years[0]
    return None, None


def _parse_from_df(df, cohort_years=None, known_bureaus=None):
    """Parse Table 2 data from a DataFrame."""
    if known_bureaus is None:
        known_bureaus = KNOWN_BUREAUS
    if cohort_years is None:
        cohort_years = _detect_cohort_years(df)
    year1, year2 = cohort_years

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

        if is_program:
            program_name = col0.split(':')[0].strip().rstrip('.')
            bea_category = parse_value(row[1])
            subsidy_rate_y1 = parse_value(row[2])
            obligations_y1 = parse_value(row[3])
            subsidy_rate_y2 = parse_value(row[5])
            obligations_y2 = parse_value(row[6])

            if all(v is None for v in [subsidy_rate_y1, obligations_y1,
                                        subsidy_rate_y2, obligations_y2]):
                continue

            avg_loan_size_y1 = parse_value(row[4])
            avg_loan_size_y2 = parse_value(row[7])

            program_data = {
                'agency': current_agency,
                'bureau': current_bureau,
                'account': current_account,
                'program': program_name,
                'bea_category': bea_category,
                'cohorts': {
                    str(year1): {
                        'subsidy_rate_percent': subsidy_rate_y1,
                        'obligations_thousands': obligations_y1,
                        'average_loan_size_thousands': avg_loan_size_y1
                    },
                    str(year2): {
                        'subsidy_rate_percent': subsidy_rate_y2,
                        'obligations_thousands': obligations_y2,
                        'average_loan_size_thousands': avg_loan_size_y2
                    }
                }
            }
            programs.append(program_data)

        elif col0.endswith(':'):
            name = col0[:-1].strip()
            if name in known_bureaus:
                current_bureau = name
                current_account = None
            else:
                current_account = name
        else:
            if 'Agency' not in col0 and 'BEA' not in col0:
                current_agency = col0
                current_bureau = None
                current_account = None

    return {
        'metadata': {
            'source': f'Federal Credit Supplement, Budget of the U.S. Government, FY {year2}',
            'table': 'Table 2: Loan Guarantee Programs - Budget Formulation Estimates',
            'cohort_years': [year1, year2],
            'units': {
                'subsidy_rate': 'percent',
                'obligations': 'thousands of dollars',
                'average_loan_size': 'thousands of dollars'
            }
        },
        'programs': programs
    }


def parse_table2(excel_path: str, sheet_name: str = 'Table 2',
                 engine: str = None) -> dict:
    """Parse Table 2 from the Federal Credit Supplement Excel file."""
    kwargs = {'header': None}
    if engine:
        kwargs['engine'] = engine
    df = pd.read_excel(excel_path, sheet_name=sheet_name, **kwargs)
    return _parse_from_df(df)


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    excel_path = project_root / 'data' / 'raw' / 'BUDGET-2026-FCS.xlsx'
    output_path = project_root / 'data' / 'processed' / 'table2_loan_guarantees.json'

    data = parse_table2(str(excel_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Parsed {len(data['programs'])} loan guarantee programs")
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
