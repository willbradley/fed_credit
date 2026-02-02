#!/usr/bin/env python3
"""
Parser for Federal Credit Supplement Table 8: Loan Guarantee Programs
Subsidy Reestimates by Cohort Year.
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
    'Forest Service',
    'Office of the Secretary',
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
}


def _safe_col(row, col_idx):
    """Safely access a column, returning None if index doesn't exist."""
    try:
        return row[col_idx]
    except (KeyError, IndexError):
        return None


def _parse_from_df(df, known_bureaus=None):
    """Parse Table 8 data from a DataFrame."""
    if known_bureaus is None:
        known_bureaus = KNOWN_BUREAUS

    current_agency = None
    current_bureau = None
    current_account = None
    current_program = None
    prev_was_blank = True

    programs = {}
    fy_pattern = re.compile(r'^FY\s*(\d{4})')

    for idx in range(2, len(df)):
        row = df.iloc[idx]
        raw_col0 = row[0]

        if pd.isna(raw_col0):
            prev_was_blank = True
            continue

        raw_str = str(raw_col0)
        indent = get_indent(raw_col0)
        col0 = raw_str.strip()

        if not col0:
            prev_was_blank = True
            continue

        fy_match = fy_pattern.match(col0)

        if fy_match:
            cohort_year = int(fy_match.group(1))

            if current_program is None:
                prev_was_blank = False
                continue

            key = (current_agency, current_bureau, current_account, current_program)

            if key not in programs:
                programs[key] = {
                    'agency': current_agency,
                    'bureau': current_bureau,
                    'account': current_account,
                    'program': current_program,
                    'cohorts': []
                }

            cohort_data = {
                'cohort_year': cohort_year,
                'original_subsidy_rate_percent': parse_value(row[1]),
                'current_reestimated_rate_percent': parse_value(row[2]),
                'change_due_to_interest_rates_pct_pts': parse_value(row[3]),
                'change_due_to_technical_assumptions_pct_pts': parse_value(row[4]),
                'current_reestimate_amount_thousands': parse_value(row[5]),
                'net_lifetime_reestimate_thousands': parse_value(row[6]),
                'net_lifetime_reestimate_excl_interest_thousands': parse_value(row[7]),
                'total_disbursements_to_date_thousands': parse_value(row[8]),
                'outstanding_balance_thousands': parse_value(_safe_col(row, 9)),
            }
            programs[key]['cohorts'].append(cohort_data)

        elif col0.endswith(':') or col0.rstrip('0123456789').endswith(':'):
            name = col0.rstrip(':').rstrip('0123456789 ').strip()

            if indent == 0:
                if name in known_bureaus:
                    current_bureau = name
                    current_account = None
                    current_program = None
                elif current_bureau is not None:
                    # Zero-indent OLE format: colon item after bureau = account
                    current_account = name
                    current_program = None
                else:
                    current_bureau = name
                    current_account = None
                    current_program = None
            elif indent <= 3:
                current_account = name
                current_program = None
            else:
                current_program = name

        else:
            if indent >= 4:
                # Program name without colon (OOXML format with indentation)
                current_program = col0.rstrip('.').strip()
            elif indent == 0 and len(col0) > 0 and col0[0].isupper():
                skip_words = ('Agency', 'Bureau', 'Subsidy', 'Cohort')
                if any(w in col0 for w in skip_words):
                    pass
                elif prev_was_blank and current_bureau is None:
                    current_agency = col0.rstrip('0123456789 ')
                    current_bureau = None
                    current_account = None
                    current_program = None
                elif prev_was_blank and current_bureau is not None:
                    current_agency = col0.rstrip('0123456789 ')
                    current_bureau = None
                    current_account = None
                    current_program = None
                else:
                    # No blank before, within bureau context = program (OLE format)
                    current_program = col0.rstrip('.').strip()

        prev_was_blank = False

    return {
        'metadata': {
            'source': 'Federal Credit Supplement, Budget of the U.S. Government',
            'table': 'Table 8: Loan Guarantee Programs - Subsidy Reestimates',
            'description': 'Historical subsidy reestimate data by cohort year',
            'units': {
                'rates': 'percent',
                'amounts': 'thousands of dollars'
            }
        },
        'programs': list(programs.values())
    }


def parse_table8(excel_path: str, sheet_name: str = 'Table 8',
                 engine: str = None) -> dict:
    """Parse Table 8 from the Federal Credit Supplement Excel file."""
    kwargs = {'header': None}
    if engine:
        kwargs['engine'] = engine
    df = pd.read_excel(excel_path, sheet_name=sheet_name, **kwargs)
    return _parse_from_df(df)


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    excel_path = project_root / 'data' / 'raw' / 'BUDGET-2026-FCS.xlsx'
    output_path = project_root / 'data' / 'processed' / 'table8_loan_guarantee_reestimates.json'

    data = parse_table8(str(excel_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    total_cohorts = sum(len(p['cohorts']) for p in data['programs'])
    print(f"Parsed {len(data['programs'])} loan guarantee programs with {total_cohorts} cohort-year records")
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
