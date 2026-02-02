# Federal Credit Supplement Data Hub - Next Steps

## Project Status (as of January 25, 2026)

Successfully parsed all 10 tables from the FY2026 Federal Credit Supplement:

| Table | Description | Output File |
|-------|-------------|-------------|
| 1 | Direct Loans - Obligations (2025/2026) | `table1_direct_loans.json` |
| 2 | Loan Guarantees - Obligations (2025/2026) | `table2_loan_guarantees.json` |
| 3 | Direct Loans - Characteristics (2025 cohort) | `table3_direct_loan_characteristics.json` |
| 4 | Loan Guarantees - Characteristics (2025 cohort) | `table4_loan_guarantee_characteristics.json` |
| 5 | Direct Loans - Characteristics (2026 cohort) | `table5_direct_loan_characteristics_2026.json` |
| 6 | Loan Guarantees - Characteristics (2026 cohort) | `table6_loan_guarantee_characteristics_2026.json` |
| 7 | Direct Loans - Reestimates (129 programs, 1,268 cohort-years) | `table7_direct_loan_reestimates.json` + `.csv` |
| 8 | Loan Guarantees - Reestimates (93 programs, 1,084 cohort-years) | `table8_loan_guarantee_reestimates.json` + `.csv` |
| 9 | Direct Loans - Disbursement Schedules | `table9_direct_loan_disbursement_schedules.json` |
| 10 | Loan Guarantees - Disbursement Schedules | `table10_loan_guarantee_disbursement_schedules.json` |

All parsed data is in: `data/processed/`

---

## Questions to Answer Before Building the Dashboard

### 1. Historical Data Scope
- How many years of FCS data do you want to include? (FY2020-2026? Further back?)
- Do you have access to older FCS Excel files, or would we need to source them from govinfo.gov?

### 2. Primary Use Cases
What should users be able to do? Examples:
- Compare a program's subsidy rates across budget years
- See which programs have the largest reestimate variances
- Download data for a specific agency or program
- Analyze portfolio-level trends
- Track changes in loan characteristics over time

### 3. Technical Preferences
- Continue with the existing React app (`src/`), or start fresh?
- Any hosting constraints (static site vs. server)?
- Public or restricted access?

### 4. Priority Features
- Search/filter (by agency, program, year)
- Visualizations (trends, comparisons, portfolio breakdowns)
- Data downloads (CSV, Excel, JSON)
- API access for programmatic queries?
- Something else?

---

## Suggested Next Steps (Pick One)

### Option A: User Research Light
Define 2-3 user personas and their top tasks before building anything. Good if you want to ensure the tool meets real needs.

### Option B: Data Foundation
Collect FCS files for multiple budget years (available at govinfo.gov) and build a unified data schema that handles year-over-year comparisons. Good if historical analysis is a priority.

### Option C: Rapid Prototype
Build a minimal interactive prototype with just the FY2026 data to validate the concept and gather feedback. Good for quick iteration.

---

## Project Structure

```
fed_credit/
├── data/
│   ├── raw/                  # Source Excel files
│   │   └── BUDGET-2026-FCS.xlsx
│   └── processed/            # Parsed JSON/CSV files
├── scripts/                  # Python parsers for each table
│   ├── parse_table1.py
│   ├── parse_table2.py
│   ├── ...
│   └── parse_table10.py
├── src/                      # Existing React app (from earlier work)
└── NEXT_STEPS.md            # This file
```

---

## Quick Reference: Data Sources

- **Federal Credit Supplement**: https://www.govinfo.gov/app/collection/budget
- **USAspending.gov API**: https://api.usaspending.gov (not currently used, but available)
- **OMB Budget Materials**: https://www.whitehouse.gov/omb/supplemental-materials/
