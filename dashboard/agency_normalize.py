"""Maps 144 raw agency strings from FCS data → ~18 clean department names."""

from __future__ import annotations

# Programs that leaked their name into the agency field
_PROGRAM_NAME_OVERRIDES = {
    "504 CRE Refinance—PL 116-260 Part-Year": "Small Business Administration",
    "504 Commercial Real Estate (CRE)": "Small Business Administration",
    "504 Commercial Real Estate (CRE) Refinance": "Small Business Administration",
    "504 Commercial Real Estate (CRE) Refinance Program": "Small Business Administration",
    "7(a) General Business Loan": "Small Business Administration",
    "7(a) General Business Loan Guarantees (Legislative": "Small Business Administration",
    "7(a) General Business—PL 116-260 Part-Year": "Small Business Administration",
    "Business Loans: 2": "Small Business Administration",
    "General Business Loan Programs: 2": "Small Business Administration",
    "Scale-Up Manufacturing Investment Company": "Small Business Administration",
    "Scale-Up Manufacturing Investment Funds": "Small Business Administration",
    "Secondary Market": "Small Business Administration",
    "Secondary Market 504 First Mortgage": "Small Business Administration",
    "Secondary Market 504 First Mortgage Guarantees": "Small Business Administration",
    "Secondary Market 7(a)": "Small Business Administration",
    "Secondary Market 7(a) Broker/Dealer": "Small Business Administration",
    "Section 108 Community Development Loan": "Department of Housing and Urban Development",
    "Section 108 Community Development Loan Guarantee": "Department of Housing and Urban Development",
    "Section 503: Secondary Market 504 First": "Small Business Administration",
    "Section 503: Secondary Market 504 First Mortgage": "Small Business Administration",
    "Section 503: Secondary Market 504 First Mortgage Guarantees": "Small Business Administration",
    "Section 504 Certified Development": "Small Business Administration",
    "Section 504 Certified Development Companies": "Small Business Administration",
    "Section 504 Debentures—PL 116-260 Part-Year": "Small Business Administration",
    "Section 506: ARC Bridge Loan": "Small Business Administration",
    "Section 509 Secondary Market 7(a) Broker/Dealer": "Small Business Administration",
    "Section 509: Secondary Market": "Small Business Administration",
    "Section 509: Secondary Market 7(a)": "Small Business Administration",
    "Section 523 Self-Help Housing": "Department of Agriculture",
    "Disaster Assistance - Expedited": "Small Business Administration",
    "Disaster Assistance - Immediate": "Small Business Administration",
    "Minority Business Resource Center": "Department of Commerce",
}

# Bureau or sub-agency names that appeared as agency
_BUREAU_OVERRIDES = {
    "Departmental Offices": "Department of the Treasury",
    "Community Development": "Department of Housing and Urban Development",
    "Community Development Financial Institutions (CDFI) Fund…………………": "Department of the Treasury",
    "Community Development Financial Institutions Fund": "Department of the Treasury",
    "Community Development Loan Guarantee": "Department of Housing and Urban Development",
    "Community Development Loan Guarantees": "Department of Housing and Urban Development",
    "Community Development Loan Guarantees (Section 108)": "Department of Housing and Urban Development",
    "Corps of Engineers—Civil Works": "Department of Defense",
    "Development": "International Assistance Programs",
    "Development Credit Authority (DCA)": "International Assistance Programs",
    "Family Housing Improvement Fund": "Department of Defense",
    "Farm Storage Facility Loans": "Department of Agriculture",
    "Business and Industry Loan Guarantees Distressed": "Department of Agriculture",
    "Rural Business Cooperative Service": "Department of Agriculture",
    "Rural Electrification and": "Department of Agriculture",
    "Rural Electrification and Telephone Program": "Department of Agriculture",
    "Rural Utilities Service": "Department of Agriculture",
    "Health Resources and Services": "Department of Health and Human Services",
    "Health Resources and Services Administration": "Department of Health and Human Services",
    "Consumer Operated and Oriented Plan Program": "Department of Health and Human Services",
    "Consumer Operated and Oriented Plan:": "Department of Health and Human Services",
}

# Department name variants (dash/truncation differences)
_DEPARTMENT_VARIANTS = {
    "Department of Defense--Military Programs": "Department of Defense",
    "Department of Defense-Military Programs": "Department of Defense",
    "Department of Defense—-Military Programs": "Department of Defense",
    "Department of Treasury": "Department of the Treasury",
}

# Program/sub-program names that map to specific agencies
_PROGRAM_AGENCY_MAP = {
    "FHA General and Special Risk Insurance Fund:": "Department of Housing and Urban Development",
    "Guarantees of Mortgage-Backed": "Department of Housing and Urban Development",
    "Guarantees of Mortgage-Backed Securities—": "Department of Housing and Urban Development",
    "HOPE for Homeowners": "Department of Housing and Urban Development",
    "Mutual Mortgage Insurance Program": "Department of Housing and Urban Development",
    "Mutual Mortgage Insurance Program—": "Department of Housing and Urban Development",
    "Mutual Mortgage Insurance Program—Seller-Financed": "Department of Housing and Urban Development",
    "Seller-Financed Down Payment": "Department of Housing and Urban Development",
    "Guaranteed 502 Single-Family": "Department of Agriculture",
    "Guaranteed 502 Single-Family Housing": "Department of Agriculture",
    "Guaranteed 502 Single-Family Housing,": "Department of Agriculture",
    "Guaranteed Loan Sale Securities—Vendee": "Department of Veterans Affairs",
    "Guaranteed Loan Sales Securities--": "Department of Veterans Affairs",
    "Guaranteed Loan Sales Securities--Vendee": "Department of Veterans Affairs",
    "Historically Black College and": "Department of Education",
    "Historically Black College and University": "Department of Education",
    "Historically Black College and University Capital": "Department of Education",
    "Student Loan Acquisition — Consolidation": "Department of Education",
    "Student Loan Acquisition — PLUS": "Department of Education",
    "Student Loan Acquisition — Stafford": "Department of Education",
    "Student Loan Acquisition — Unsubsidized Stafford": "Department of Education",
    "Subsidized Stafford": "Department of Education",
    "Unsubsidized Stafford": "Department of Education",
    "Unsubsidized Stafford (Legislative Proposal)": "Department of Education",
    "TEACH Grants": "Department of Education",
    "Teacher Education Assistance": "Department of Education",
    "Title 17 Innovative Technology Loan": "Department of Energy",
    "Title 17 Innovative Technology Program:": "Department of Energy",
    "Better Buildings Pilot Loan Guarantee Initiative": "Department of Energy",
    "Better Buildings Pilot Loan Guarantee Initiative for Universities, Schools,": "Department of Energy",
    "Infrastructure Initiative": "Department of Energy",
    "Infrastructure Loan Guarantees": "Department of Energy",
    "National Infrastructure Bank": "Department of Energy",
    "National Infrastructure Innovation and": "Department of Energy",
    "Railroad Rehabilitation and Improvement": "Department of Transportation",
    "Railroad Rehabilitation and Improvement Financing": "Department of Transportation",
    "Railroad Rehabilitation and Improvement Financing (RRIF)": "Department of Transportation",
    "Railroad Rehabilitation and Improvement Program": "Department of Transportation",
    "Transportation Infrastructure Finance and": "Department of Transportation",
    "Transportation Infrastructure,": "Department of Transportation",
    "Transportation Infrastructure, Finance &": "Department of Transportation",
    "Transportation Infrastructure, Finance & Innovation": "Department of Transportation",
    "Transportation Infrastructure, Finance, and Innovation": "Department of Transportation",
    "Transportation, Finance & Innovation (TIFIA)": "Department of Transportation",
    "Transportation, Infrastructure, Finance & Innovation (TIFIA)": "Department of Transportation",
    "Short, Medium, and Long Term Guarantees": "Export-Import Bank",
    "Short, Medium, and Long Term Guarantees and Insurance: 3": "Export-Import Bank",
    "Contribution to the International Bank for": "International Assistance Programs",
    "Contribution to the International Bank for Reconstruction": "International Assistance Programs",
    "Contributions to the International Monetary Fund": "International Assistance Programs",
    "International Monetary Fund: 1": "International Assistance Programs",
    "International Monetary Programs: 2": "International Assistance Programs",
    "Reconstruction and Development….........................................................................................................................................................................................................................................................................................................................................................................................................": "International Assistance Programs",
    "Reconstruction and Development…..........................................................................................................................................................................................................................................................................................................................................................................................................": "International Assistance Programs",
    "North American Development Bank": "International Assistance Programs",
    "Troubled Asset Relief Program": "Department of the Treasury",
    "Troubled Asset Relief Program, Home Affordable": "Department of the Treasury",
    "Troubled Asset Relief Program, Housing Programs": "Department of the Treasury",
    "Office Financial Stability:": "Department of the Treasury",
    "Office of Financial Stability:": "Department of the Treasury",
    "Office of Financial Stability: 1": "Department of the Treasury",
    "Office of Financial Stability:1": "Department of the Treasury",
    "Financial Stabilization Reserve:3": "Department of the Treasury",
    "Legacy Securities Public-Private": "Department of the Treasury",
}

# Section labels / aggregates to exclude
_EXCLUDE = {
    "Weighted Average of Total Commitments",
    "Weighted Average of Total Obligations",
    "Weighted Average of Total Obligations —",
    "Weighted Average of Total Obligations — Student Loan Acquisition",
}

# Agencies that are already clean
_CLEAN_AGENCIES = {
    "Department of Agriculture",
    "Department of Commerce",
    "Department of Defense",
    "Department of Education",
    "Department of Energy",
    "Department of Health and Human Services",
    "Department of Homeland Security",
    "Department of Housing and Urban Development",
    "Department of State",
    "Department of Transportation",
    "Department of Veterans Affairs",
    "Department of the Interior",
    "Department of the Treasury",
    "Export-Import Bank of the United States",
    "Federal Communications Commission",
    "International Assistance Programs",
    "Other Independent Agencies",
    "Overseas Private Investment Corporation",
    "Small Business Administration",
    "United States International Development Finance",
}

# Normalize Export-Import Bank variants
_FINAL_RENAMES = {
    "Export-Import Bank of the United States": "Export-Import Bank",
    "United States International Development Finance": "U.S. International Development Finance Corp.",
    "Overseas Private Investment Corporation": "U.S. International Development Finance Corp.",
}


def normalize_agency(raw: str) -> str | None:
    """Map a raw agency string to a clean department name.

    Returns None for section labels that should be excluded.
    """
    if raw in _EXCLUDE:
        return None

    if raw in _CLEAN_AGENCIES:
        return _FINAL_RENAMES.get(raw, raw)

    # Check each override dict in priority order
    for mapping in (
        _PROGRAM_NAME_OVERRIDES,
        _BUREAU_OVERRIDES,
        _DEPARTMENT_VARIANTS,
        _PROGRAM_AGENCY_MAP,
    ):
        if raw in mapping:
            result = mapping[raw]
            return _FINAL_RENAMES.get(result, result)

    # Fallback: return as-is
    return raw
