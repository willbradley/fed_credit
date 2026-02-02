#!/usr/bin/env python3
"""
FY2026 Federal Credit Supplement - PDF Scorecard Generator
Produces a downloadable PDF with narrative, summary tables, and visualizations.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Programs to exclude (summary rows that would cause double-counting)
EXCLUDE_PROGRAMS = [
    "Weighted Average of Total Obligations",
]

# Threshold for grouping small agencies into "Other"
SMALL_AGENCY_THRESHOLD = 1e9  # $1 billion


def load_json(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def analyze_programs(programs, cohort_year="2026"):
    """Analyze programs for a given cohort year."""
    totals = {
        "obligations": 0,
        "subsidy_cost": 0,
        "program_count": 0,
    }
    by_agency = defaultdict(lambda: {
        "obligations": 0,
        "subsidy_cost": 0,
        "program_count": 0
    })
    program_details = []

    for prog in programs:
        if prog["program"] in EXCLUDE_PROGRAMS:
            continue

        cohort = prog["cohorts"].get(cohort_year, {})
        obligations = cohort.get("obligations_thousands")
        subsidy_rate = cohort.get("subsidy_rate_percent")

        if obligations is None or subsidy_rate is None:
            continue

        obligations_dollars = obligations * 1000
        subsidy_cost_dollars = (subsidy_rate / 100) * obligations_dollars

        totals["obligations"] += obligations_dollars
        totals["subsidy_cost"] += subsidy_cost_dollars
        totals["program_count"] += 1

        agency = prog["agency"]
        by_agency[agency]["obligations"] += obligations_dollars
        by_agency[agency]["subsidy_cost"] += subsidy_cost_dollars
        by_agency[agency]["program_count"] += 1

        program_details.append({
            "name": prog["program"],
            "agency": agency,
            "obligations": obligations_dollars,
            "subsidy_cost": subsidy_cost_dollars,
            "subsidy_rate": subsidy_rate,
        })

    return totals, dict(by_agency), program_details


def format_currency(amount):
    """Format amount with appropriate units (B or M)."""
    if abs(amount) >= 1e9:
        return f"${amount / 1e9:,.1f}B"
    elif abs(amount) >= 1e6:
        return f"${amount / 1e6:,.0f}M"
    elif abs(amount) >= 1e3:
        return f"${amount / 1e3:,.0f}K"
    else:
        return f"${amount:,.0f}"


def format_currency_signed(amount):
    """Format amount with sign and appropriate units."""
    if abs(amount) < 0.5e6:  # Less than $500K, show as ~$0
        return "$0"
    if amount >= 0:
        return format_currency(amount)
    else:
        # For negative, format absolute value then prepend minus
        if abs(amount) >= 1e9:
            return f"-${abs(amount) / 1e9:,.1f}B"
        elif abs(amount) >= 1e6:
            return f"-${abs(amount) / 1e6:,.0f}M"
        else:
            return f"-${abs(amount) / 1e3:,.0f}K"


def format_rate(subsidy_cost, obligations):
    """Calculate and format weighted average subsidy rate."""
    if obligations == 0:
        return "N/A"
    rate = (subsidy_cost / obligations) * 100
    return f"{rate:.1f}%"


def shorten_agency_name(name):
    """Shorten agency names for display."""
    replacements = {
        "Department of Agriculture": "Agriculture",
        "Department of Commerce": "Commerce",
        "Department of Defense--Military Programs": "Defense",
        "Department of Education": "Education",
        "Department of Energy": "Energy",
        "Department of Health and Human Services": "HHS",
        "Department of Homeland Security": "Homeland Security",
        "Department of Housing and Urban Development": "HUD",
        "Department of State": "State",
        "Department of the Interior": "Interior",
        "Department of the Treasury": "Treasury",
        "Department of Transportation": "Transportation",
        "Department of Veterans Affairs": "Veterans Affairs",
        "International Assistance Programs": "Int'l Assistance",
        "Corps of Engineers--Civil Works": "Corps of Engineers",
        "Export-Import Bank of the United States": "Ex-Im Bank",
        "Small Business Administration": "SBA",
        "Health Resources and Services Administration": "HRSA",
    }
    return replacements.get(name, name)


def create_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='Title1',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        textColor=colors.HexColor('#2c3e50'),
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=10,
        spaceBefore=0,
        spaceAfter=4,
        textColor=colors.HexColor('#2c3e50'),
    ))

    styles.add(ParagraphStyle(
        name='BodyTextCustom',
        parent=styles['BodyText'],
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceAfter=0,
    ))

    styles.add(ParagraphStyle(
        name='BoxText',
        parent=styles['BodyText'],
        fontSize=8,
        leading=11,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='TableNote',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceBefore=4,
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#95a5a6'),
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='AppendixHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=0,
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50'),
    ))

    styles.add(ParagraphStyle(
        name='AppendixBody',
        parent=styles['BodyText'],
        fontSize=9,
        leading=13,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name='DefinitionTerm',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='DefinitionBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=12,
        spaceAfter=6,
    ))

    return styles


def create_summary_line(dl_totals, lg_totals):
    """Create a single-line summary display."""
    combined_obligations = dl_totals["obligations"] + lg_totals["obligations"]
    combined_subsidy = dl_totals["subsidy_cost"] + lg_totals["subsidy_cost"]
    combined_programs = dl_totals["program_count"] + lg_totals["program_count"]
    avg_rate = format_rate(combined_subsidy, combined_obligations)

    data = [[
        f"Loan Volume: {format_currency(combined_obligations)}",
        f"Net Subsidy: {format_currency_signed(combined_subsidy)}",
        f"Avg Rate: {avg_rate}",
        f"Programs: {combined_programs}",
    ]]

    # Full width = 7 inches (letter width 8.5 - 0.75*2 margins)
    table = Table(data, colWidths=[1.85*inch, 1.85*inch, 1.6*inch, 1.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
    ]))

    return table


def create_waterfall_chart(all_programs):
    """Create a waterfall chart showing subsidy costs and revenues."""
    # Calculate totals
    cost_programs = [p for p in all_programs if p["subsidy_cost"] > 0]
    revenue_programs = [p for p in all_programs if p["subsidy_cost"] < 0]

    total_costs = sum(p["subsidy_cost"] for p in cost_programs) / 1e9
    total_revenue = sum(p["subsidy_cost"] for p in revenue_programs) / 1e9  # negative
    net_subsidy = total_costs + total_revenue

    # Create figure
    fig, ax = plt.subplots(figsize=(5.5, 2.2))

    # Waterfall data
    categories = ['Subsidy Costs\n(53 programs)', 'Subsidy Savings\n(40 programs)', 'Net Subsidy']
    values = [total_costs, total_revenue, net_subsidy]

    # Calculate bar positions for waterfall
    bar_starts = [0, total_costs, 0]  # Start positions
    bar_heights = [total_costs, total_revenue, net_subsidy]

    # Colors
    bar_colors = ['#e74c3c', '#27ae60', '#3498db']

    # Plot bars
    bars = ax.bar(categories, bar_heights, bottom=bar_starts, color=bar_colors,
                  edgecolor='white', linewidth=1.5, width=0.6)

    # Add connector line
    ax.plot([0.3, 0.7], [total_costs, total_costs], color='gray', linewidth=1, linestyle='--')
    ax.plot([1.3, 1.7], [net_subsidy, net_subsidy], color='gray', linewidth=1, linestyle='--')

    # Add value labels
    ax.annotate(f'${total_costs:.1f}B', xy=(0, total_costs/2), ha='center', va='center',
                fontsize=10, fontweight='bold', color='white')
    ax.annotate(f'-${abs(total_revenue):.1f}B', xy=(1, total_costs + total_revenue/2), ha='center', va='center',
                fontsize=10, fontweight='bold', color='white')
    ax.annotate(f'${net_subsidy:.1f}B', xy=(2, net_subsidy/2), ha='center', va='center',
                fontsize=10, fontweight='bold', color='white')

    # Formatting
    ax.set_ylabel('$ Billions', fontsize=9)
    ax.set_ylim(-5, 45)
    ax.axhline(y=0, color='black', linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)

    plt.tight_layout()

    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    buf.seek(0)

    return buf


def create_agency_table(dl_by_agency, lg_by_agency):
    """Create simplified agency table with loan volume and subsidy only."""
    # Combine agency data
    all_agencies = set(dl_by_agency.keys()) | set(lg_by_agency.keys())
    agency_data = []

    for agency in all_agencies:
        dl = dl_by_agency.get(agency, {"obligations": 0, "subsidy_cost": 0})
        lg = lg_by_agency.get(agency, {"obligations": 0, "subsidy_cost": 0})

        total_obligations = dl["obligations"] + lg["obligations"]
        total_subsidy = dl["subsidy_cost"] + lg["subsidy_cost"]

        agency_data.append({
            "agency": agency,
            "total_obligations": total_obligations,
            "total_subsidy": total_subsidy,
        })

    # Sort by total obligations
    agency_data.sort(key=lambda x: x["total_obligations"], reverse=True)

    # Group small agencies into "Other"
    main_agencies = []
    other_obligations = 0
    other_subsidy = 0

    for a in agency_data:
        if a["total_obligations"] >= SMALL_AGENCY_THRESHOLD:
            main_agencies.append(a)
        else:
            other_obligations += a["total_obligations"]
            other_subsidy += a["total_subsidy"]

    # Add "Other" row if there are small agencies
    if other_obligations > 0:
        main_agencies.append({
            "agency": "Other",
            "total_obligations": other_obligations,
            "total_subsidy": other_subsidy,
        })

    # Build table data
    header = ['Agency', 'Loan Volume', 'Credit Subsidy', 'Subsidy Rate']
    data = [header]

    total_obligations = 0
    total_subsidy = 0

    for a in main_agencies:
        row = [
            shorten_agency_name(a["agency"]),
            format_currency(a["total_obligations"]),
            format_currency_signed(a["total_subsidy"]),
            format_rate(a["total_subsidy"], a["total_obligations"]),
        ]
        data.append(row)
        total_obligations += a["total_obligations"]
        total_subsidy += a["total_subsidy"]

    # Add totals row
    data.append([
        'TOTAL',
        format_currency(total_obligations),
        format_currency_signed(total_subsidy),
        format_rate(total_subsidy, total_obligations),
    ])

    col_widths = [1.9*inch, 1.1*inch, 1.1*inch, 0.9*inch]
    table = Table(data, colWidths=col_widths)

    style_commands = [
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),

        # Totals row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),

        # Padding
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),

        # Alternating row colors (excluding totals)
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
    ]

    table.setStyle(TableStyle(style_commands))

    return table


def generate_pdf(output_path):
    """Generate the scorecard PDF."""
    # Load and analyze data
    direct_loans = load_json("table1_direct_loans.json")
    loan_guarantees = load_json("table2_loan_guarantees.json")

    dl_totals, dl_by_agency, dl_programs = analyze_programs(direct_loans["programs"], "2026")
    lg_totals, lg_by_agency, lg_programs = analyze_programs(loan_guarantees["programs"], "2026")

    # Create document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    styles = create_styles()
    story = []

    # =========================================================================
    # PAGE 1: Main Scorecard
    # =========================================================================

    # Combined Title
    story.append(Paragraph(
        "FY2026 Federal Credit Supplement — Budget Formulation Scorecard",
        styles['Title1']
    ))

    # About This Data in a colored box
    narrative = """
    <b>About This Data:</b> This scorecard summarizes the budget formulation data from the
    Federal Credit Supplement to the President's Budget for Fiscal Year 2026. The Federal
    Credit Supplement is published annually by OMB and provides detailed information on all
    federal direct loan and loan guarantee programs subject to the Federal Credit Reform Act
    of 1990. The data covers the <b>2026 cohort</b>—loans projected to be originated during FY2026.
    """

    # Create a table to hold the narrative with background color
    narrative_para = Paragraph(narrative.strip(), styles['BoxText'])
    narrative_table = Table([[narrative_para]], colWidths=[7*inch])
    narrative_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(narrative_table)

    story.append(Spacer(1, 8))

    # Summary line
    story.append(create_summary_line(dl_totals, lg_totals))

    story.append(Spacer(1, 6))

    # Combine all programs for waterfall chart
    all_programs = []
    for prog in dl_programs:
        all_programs.append({**prog, "type": "Direct"})
    for prog in lg_programs:
        all_programs.append({**prog, "type": "Guar"})

    # Create waterfall chart
    waterfall_buf = create_waterfall_chart(all_programs)
    waterfall_img = Image(waterfall_buf, width=4.2*inch, height=1.7*inch)
    story.append(waterfall_img)

    story.append(Spacer(1, 6))

    # Agency table
    story.append(create_agency_table(dl_by_agency, lg_by_agency))
    story.append(Paragraph(
        "Note: Agencies with less than $1B in loan volume grouped into \"Other.\" "
        "Negative subsidies = expected revenue to government.",
        styles['TableNote']
    ))

    # Footer
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y')} | "
        "Source: Federal Credit Supplement, FY2026",
        styles['Footer']
    ))

    # =========================================================================
    # PAGE 2: Appendix - Definitions
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("Appendix: Definitions and Methodology", styles['AppendixHeader']))

    story.append(Paragraph("Data Source", styles['DefinitionTerm']))
    story.append(Paragraph(
        "The Federal Credit Supplement is an annual publication accompanying the President's "
        "Budget. It contains detailed program-level data for all federal credit programs "
        "subject to the Federal Credit Reform Act of 1990 (FCRA). The supplement is available "
        "at <link href='https://www.govinfo.gov/app/collection/budget'>www.govinfo.gov</link>.",
        styles['DefinitionBody']
    ))

    story.append(Paragraph("Cohort Year", styles['DefinitionTerm']))
    story.append(Paragraph(
        "A cohort refers to all loans originated in a given fiscal year. This scorecard "
        "presents data for the 2026 cohort—loans expected to be made during FY2026 under "
        "the President's Budget request.",
        styles['DefinitionBody']
    ))

    story.append(Paragraph("Loan Volume (Budget Authority)", styles['DefinitionTerm']))
    story.append(Paragraph(
        "The total principal amount of loans projected to be obligated during the fiscal year. "
        "For direct loans, this is the face value of loans made directly by federal agencies. "
        "For loan guarantees, this is the face value of private-sector loans guaranteed by "
        "the federal government.",
        styles['DefinitionBody']
    ))

    story.append(Paragraph("Credit Subsidy Rate", styles['DefinitionTerm']))
    story.append(Paragraph(
        "The estimated long-term cost (or savings) to the government of a direct loan or "
        "loan guarantee, expressed as a percentage of the loan principal. The subsidy rate "
        "is calculated on a net present value basis and reflects expected cash flows over "
        "the life of the loan, including defaults, recoveries, interest subsidies, and fees.",
        styles['DefinitionBody']
    ))

    story.append(Paragraph("Credit Subsidy Cost", styles['DefinitionTerm']))
    story.append(Paragraph(
        "The dollar amount of the subsidy, calculated as:",
        styles['DefinitionBody']
    ))
    story.append(Paragraph(
        "<b>Credit Subsidy Cost = Subsidy Rate × Loan Volume</b>",
        ParagraphStyle('Formula', parent=styles['DefinitionBody'],
                       alignment=TA_CENTER, spaceBefore=4, spaceAfter=4)
    ))
    story.append(Paragraph(
        "A <b>positive subsidy</b> indicates a cost to the government—the present value of "
        "expected losses (defaults, interest subsidies) exceeds expected recoveries and fees. "
        "A <b>negative subsidy</b> indicates the program is expected to generate net revenue "
        "for the government over the life of the loans.",
        styles['DefinitionBody']
    ))

    story.append(Paragraph("Weighted Average Subsidy Rate", styles['DefinitionTerm']))
    story.append(Paragraph(
        "The portfolio-wide subsidy rate, calculated as total subsidy cost divided by "
        "total loan volume. This provides a single measure of the overall cost rate "
        "across all programs.",
        styles['DefinitionBody']
    ))

    story.append(Paragraph("Direct Loans vs. Loan Guarantees", styles['DefinitionTerm']))
    story.append(Paragraph(
        "<b>Direct loans</b> are disbursed directly by federal agencies to borrowers. "
        "<b>Loan guarantees</b> are commitments by the federal government to pay part or all "
        "of the principal and interest on a loan made by a private lender if the borrower "
        "defaults. Both types are subject to FCRA budgetary treatment.",
        styles['DefinitionBody']
    ))

    # Appendix footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "For more information on federal credit programs and budget concepts, see OMB Circular A-11, "
        "Section 185 (Federal Credit).",
        styles['Footer']
    ))

    # Build PDF
    doc.build(story)
    print(f"PDF saved to: {output_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "fy2026_fcs_scorecard.pdf"
    generate_pdf(output_path)


if __name__ == "__main__":
    main()
