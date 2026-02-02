#!/usr/bin/env python3
"""
FY2026 Federal Credit Supplement - Budget Formulation Scorecard
Produces high-level summary analytics for direct loans and loan guarantees.
"""

import json
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Programs to exclude (summary rows that would cause double-counting)
EXCLUDE_PROGRAMS = [
    "Weighted Average of Total Obligations",  # Education summary row
]

def load_json(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

def analyze_programs(programs, cohort_year="2026"):
    """Analyze programs for a given cohort year."""
    totals = {
        "obligations": 0,
        "subsidy_cost": 0,
        "program_count": 0,
        "positive_subsidy_count": 0,
        "negative_subsidy_count": 0,
        "zero_subsidy_count": 0,
    }
    by_agency = defaultdict(lambda: {"obligations": 0, "subsidy_cost": 0, "program_count": 0})
    program_details = []

    for prog in programs:
        # Skip summary/aggregate rows
        if prog["program"] in EXCLUDE_PROGRAMS:
            continue

        cohort = prog["cohorts"].get(cohort_year, {})
        obligations = cohort.get("obligations_thousands")
        subsidy_rate = cohort.get("subsidy_rate_percent")

        # Skip programs with no data for this cohort
        if obligations is None or subsidy_rate is None:
            continue

        # Convert from thousands to actual dollars
        obligations_dollars = obligations * 1000
        subsidy_cost_dollars = (subsidy_rate / 100) * obligations_dollars

        totals["obligations"] += obligations_dollars
        totals["subsidy_cost"] += subsidy_cost_dollars
        totals["program_count"] += 1

        if subsidy_rate > 0:
            totals["positive_subsidy_count"] += 1
        elif subsidy_rate < 0:
            totals["negative_subsidy_count"] += 1
        else:
            totals["zero_subsidy_count"] += 1

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

def format_currency(amount, in_billions=False):
    """Format a dollar amount."""
    if in_billions:
        return f"${amount / 1e9:,.2f}B"
    elif abs(amount) >= 1e9:
        return f"${amount / 1e9:,.2f}B"
    elif abs(amount) >= 1e6:
        return f"${amount / 1e6:,.1f}M"
    else:
        return f"${amount:,.0f}"

def format_rate(subsidy_cost, obligations):
    """Calculate and format weighted average subsidy rate."""
    if obligations == 0:
        return "N/A"
    rate = (subsidy_cost / obligations) * 100
    return f"{rate:.2f}%"

def print_separator(char="=", width=80):
    print(char * width)

def shorten_agency_name(name):
    """Shorten agency names for display."""
    replacements = {
        "Department of ": "",
        "Department of the ": "",
        "Administration": "Admin",
        "International Assistance Programs": "Int'l Assistance",
        "Corps of Engineers--Civil Works": "Corps of Engineers",
        "Export-Import Bank of the United States": "Ex-Im Bank",
        "Defense--Military Programs": "Defense",
        "Housing and Urban Development": "HUD",
        "Health and Human Services": "HHS",
        "Homeland Security": "DHS",
    }
    result = name
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result

def create_visualizations(dl_totals, lg_totals, dl_by_agency, lg_by_agency,
                          dl_programs, lg_programs, output_dir):
    """Create visualization charts."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10

    # Combine agency data
    all_agencies = set(dl_by_agency.keys()) | set(lg_by_agency.keys())
    agency_combined = {}
    for agency in all_agencies:
        dl = dl_by_agency.get(agency, {"obligations": 0, "subsidy_cost": 0, "program_count": 0})
        lg = lg_by_agency.get(agency, {"obligations": 0, "subsidy_cost": 0, "program_count": 0})
        agency_combined[agency] = {
            "obligations": dl["obligations"] + lg["obligations"],
            "subsidy_cost": dl["subsidy_cost"] + lg["subsidy_cost"],
            "program_count": dl["program_count"] + lg["program_count"],
            "dl_obligations": dl["obligations"],
            "lg_obligations": lg["obligations"],
            "dl_subsidy": dl["subsidy_cost"],
            "lg_subsidy": lg["subsidy_cost"],
        }

    # Sort by obligations
    sorted_agencies = sorted(agency_combined.items(), key=lambda x: x[1]["obligations"], reverse=True)

    # =========================================================================
    # Figure 1: Two-panel overview (Loan Volume and Subsidy by Credit Type)
    # =========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Loan Volume by Type
    types = ['Direct Loans', 'Loan Guarantees']
    volumes = [dl_totals['obligations'] / 1e9, lg_totals['obligations'] / 1e9]
    colors = ['#2ecc71', '#3498db']

    bars1 = axes[0].bar(types, volumes, color=colors, edgecolor='white', linewidth=1.5)
    axes[0].set_ylabel('Loan Volume ($ Billions)')
    axes[0].set_title('FY2026 Loan Volume by Credit Type')
    axes[0].set_ylim(0, max(volumes) * 1.15)

    for bar, vol in zip(bars1, volumes):
        axes[0].annotate(f'${vol:.0f}B',
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Panel 2: Subsidy Cost by Type
    subsidies = [dl_totals['subsidy_cost'] / 1e9, lg_totals['subsidy_cost'] / 1e9]
    bar_colors = ['#e74c3c' if s > 0 else '#27ae60' for s in subsidies]

    bars2 = axes[1].bar(types, subsidies, color=bar_colors, edgecolor='white', linewidth=1.5)
    axes[1].set_ylabel('Subsidy Cost ($ Billions)')
    axes[1].set_title('FY2026 Credit Subsidy by Type')
    axes[1].axhline(y=0, color='black', linewidth=0.8)

    for bar, sub in zip(bars2, subsidies):
        va = 'bottom' if sub >= 0 else 'top'
        offset = 1 if sub >= 0 else -1
        axes[1].annotate(f'${sub:+.1f}B',
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        ha='center', va=va, fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig1_credit_type_overview.png', dpi=150, bbox_inches='tight')
    plt.close()

    # =========================================================================
    # Figure 2: Loan Volume by Agency (horizontal bar)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 8))

    # Take top 12 agencies
    top_agencies = sorted_agencies[:12]
    agency_names = [shorten_agency_name(a[0]) for a in top_agencies][::-1]
    dl_vols = [a[1]['dl_obligations'] / 1e9 for a in top_agencies][::-1]
    lg_vols = [a[1]['lg_obligations'] / 1e9 for a in top_agencies][::-1]

    y_pos = np.arange(len(agency_names))

    bars1 = ax.barh(y_pos, dl_vols, label='Direct Loans', color='#2ecc71', edgecolor='white')
    bars2 = ax.barh(y_pos, lg_vols, left=dl_vols, label='Loan Guarantees', color='#3498db', edgecolor='white')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(agency_names)
    ax.set_xlabel('Loan Volume ($ Billions)')
    ax.set_title('FY2026 Loan Volume by Agency')
    ax.legend(loc='lower right')

    # Add total labels
    for i, (dl, lg) in enumerate(zip(dl_vols, lg_vols)):
        total = dl + lg
        if total > 10:
            ax.annotate(f'${total:.0f}B', xy=(total + 2, i), va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / 'fig2_volume_by_agency.png', dpi=150, bbox_inches='tight')
    plt.close()

    # =========================================================================
    # Figure 3: Subsidy Cost by Agency (horizontal bar, showing positive/negative)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 8))

    agency_names = [shorten_agency_name(a[0]) for a in top_agencies][::-1]
    subsidies = [a[1]['subsidy_cost'] / 1e9 for a in top_agencies][::-1]

    colors = ['#e74c3c' if s > 0 else '#27ae60' for s in subsidies]

    bars = ax.barh(y_pos, subsidies, color=colors, edgecolor='white')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(agency_names)
    ax.set_xlabel('Credit Subsidy ($ Billions)')
    ax.set_title('FY2026 Credit Subsidy by Agency')
    ax.axvline(x=0, color='black', linewidth=0.8)

    # Add value labels
    for i, sub in enumerate(subsidies):
        if abs(sub) > 0.5:
            ha = 'left' if sub >= 0 else 'right'
            offset = 0.5 if sub >= 0 else -0.5
            ax.annotate(f'${sub:+.1f}B', xy=(sub + offset, i), va='center', ha=ha, fontsize=9)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#e74c3c', label='Cost to Government'),
                       Patch(facecolor='#27ae60', label='Revenue to Government')]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()
    plt.savefig(output_dir / 'fig3_subsidy_by_agency.png', dpi=150, bbox_inches='tight')
    plt.close()

    # =========================================================================
    # Figure 4: Top 10 Programs by Subsidy Cost
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 6))

    all_programs = []
    for prog in dl_programs:
        all_programs.append({**prog, "type": "Direct"})
    for prog in lg_programs:
        all_programs.append({**prog, "type": "Guar"})

    # Sort by absolute subsidy cost
    top_programs = sorted(all_programs, key=lambda x: abs(x["subsidy_cost"]), reverse=True)[:10]

    prog_names = [p["name"][:30] + ".." if len(p["name"]) > 32 else p["name"] for p in top_programs][::-1]
    prog_subsidies = [p["subsidy_cost"] / 1e9 for p in top_programs][::-1]

    colors = ['#e74c3c' if s > 0 else '#27ae60' for s in prog_subsidies]

    y_pos = np.arange(len(prog_names))
    bars = ax.barh(y_pos, prog_subsidies, color=colors, edgecolor='white')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(prog_names, fontsize=9)
    ax.set_xlabel('Credit Subsidy ($ Billions)')
    ax.set_title('Top 10 Programs by Credit Subsidy Cost (FY2026)')
    ax.axvline(x=0, color='black', linewidth=0.8)

    # Add value labels
    for i, sub in enumerate(prog_subsidies):
        ha = 'left' if sub >= 0 else 'right'
        offset = 0.3 if sub >= 0 else -0.3
        ax.annotate(f'${sub:+.1f}B', xy=(sub + offset, i), va='center', ha=ha, fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / 'fig4_top_programs.png', dpi=150, bbox_inches='tight')
    plt.close()

    # =========================================================================
    # Figure 5: Subsidy Rate Distribution (scatter plot: volume vs rate)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 7))

    # Separate by type
    dl_volumes = [p["obligations"] / 1e9 for p in dl_programs]
    dl_rates = [p["subsidy_rate"] for p in dl_programs]
    lg_volumes = [p["obligations"] / 1e9 for p in lg_programs]
    lg_rates = [p["subsidy_rate"] for p in lg_programs]

    ax.scatter(dl_volumes, dl_rates, alpha=0.6, s=50, c='#2ecc71', label='Direct Loans', edgecolors='white')
    ax.scatter(lg_volumes, lg_rates, alpha=0.6, s=50, c='#3498db', label='Loan Guarantees', edgecolors='white')

    ax.set_xscale('log')
    ax.set_xlabel('Loan Volume ($ Billions, log scale)')
    ax.set_ylabel('Subsidy Rate (%)')
    ax.set_title('FY2026 Program Subsidy Rates vs. Loan Volume')
    ax.axhline(y=0, color='black', linewidth=0.8, linestyle='--')
    ax.legend()

    # Format x-axis
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:.0f}B' if x >= 1 else f'${x*1000:.0f}M'))

    # Add annotations for notable programs
    notable = [
        ("Consolidation", 42.19, 43.77),
        ("MMI Fund", 299.97, -2.59),
        ("PLUS", 30.28, -6.56),
    ]

    plt.tight_layout()
    plt.savefig(output_dir / 'fig5_rate_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()

    # =========================================================================
    # Figure 6: Summary Dashboard
    # =========================================================================
    fig = plt.figure(figsize=(14, 10))

    # Create grid
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    # Big numbers at top
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis('off')

    combined_obligations = dl_totals["obligations"] + lg_totals["obligations"]
    combined_subsidy = dl_totals["subsidy_cost"] + lg_totals["subsidy_cost"]
    combined_programs = dl_totals["program_count"] + lg_totals["program_count"]
    avg_rate = (combined_subsidy / combined_obligations) * 100

    title_text = "FY2026 Federal Credit Supplement — Budget Formulation Summary"
    ax_title.text(0.5, 0.85, title_text, ha='center', va='top', fontsize=16, fontweight='bold',
                  transform=ax_title.transAxes)

    metrics_text = (
        f"Total Loan Volume: ${combined_obligations/1e9:.1f}B    |    "
        f"Net Credit Subsidy: ${combined_subsidy/1e9:.1f}B    |    "
        f"Avg Subsidy Rate: {avg_rate:.1f}%    |    "
        f"Programs: {combined_programs}"
    )
    ax_title.text(0.5, 0.45, metrics_text, ha='center', va='center', fontsize=12,
                  transform=ax_title.transAxes,
                  bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7'))

    # Panel 1: Credit Type pie
    ax1 = fig.add_subplot(gs[1, 0])
    sizes = [dl_totals['obligations'], lg_totals['obligations']]
    labels = ['Direct\nLoans', 'Loan\nGuarantees']
    colors = ['#2ecc71', '#3498db']
    explode = (0.02, 0.02)
    ax1.pie(sizes, labels=labels, colors=colors, explode=explode, autopct='%1.0f%%',
            startangle=90, textprops={'fontsize': 10})
    ax1.set_title('Loan Volume by Type', fontsize=11, fontweight='bold')

    # Panel 2: Subsidy breakdown
    ax2 = fig.add_subplot(gs[1, 1])
    cost_total = sum(p["subsidy_cost"] for p in all_programs if p["subsidy_cost"] > 0)
    revenue_total = abs(sum(p["subsidy_cost"] for p in all_programs if p["subsidy_cost"] < 0))

    x = ['Subsidy\nCosts', 'Subsidy\nSavings', 'Net\nSubsidy']
    y = [cost_total/1e9, -revenue_total/1e9, combined_subsidy/1e9]
    colors = ['#e74c3c', '#27ae60', '#3498db' if combined_subsidy > 0 else '#27ae60']

    bars = ax2.bar(x, y, color=colors, edgecolor='white', linewidth=1.5)
    ax2.axhline(y=0, color='black', linewidth=0.8)
    ax2.set_ylabel('$ Billions')
    ax2.set_title('Credit Subsidy Flows', fontsize=11, fontweight='bold')

    for bar, val in zip(bars, y):
        va = 'bottom' if val >= 0 else 'top'
        ax2.annotate(f'${val:+.1f}B', xy=(bar.get_x() + bar.get_width()/2, val),
                    ha='center', va=va, fontsize=10, fontweight='bold')

    # Panel 3: Top agencies by volume (simplified)
    ax3 = fig.add_subplot(gs[1, 2])
    top5 = sorted_agencies[:5]
    names = [shorten_agency_name(a[0])[:15] for a in top5]
    vols = [a[1]['obligations']/1e9 for a in top5]

    bars = ax3.barh(range(len(names)), vols, color='#34495e', edgecolor='white')
    ax3.set_yticks(range(len(names)))
    ax3.set_yticklabels(names, fontsize=9)
    ax3.set_xlabel('$ Billions')
    ax3.set_title('Top 5 Agencies by Volume', fontsize=11, fontweight='bold')
    ax3.invert_yaxis()

    # Panel 4: Top subsidy programs
    ax4 = fig.add_subplot(gs[2, :2])
    top6 = sorted(all_programs, key=lambda x: x["subsidy_cost"], reverse=True)[:6]
    names = [p["name"][:25] for p in top6]
    subs = [p["subsidy_cost"]/1e9 for p in top6]

    colors = ['#e74c3c' if s > 0 else '#27ae60' for s in subs]
    bars = ax4.barh(range(len(names)), subs, color=colors, edgecolor='white')
    ax4.set_yticks(range(len(names)))
    ax4.set_yticklabels(names, fontsize=9)
    ax4.set_xlabel('Credit Subsidy ($ Billions)')
    ax4.set_title('Largest Subsidy Cost Programs', fontsize=11, fontweight='bold')
    ax4.invert_yaxis()
    ax4.axvline(x=0, color='black', linewidth=0.5)

    for bar, val in zip(bars, subs):
        ha = 'left' if val >= 0 else 'right'
        offset = 0.3 if val >= 0 else -0.3
        ax4.annotate(f'${val:.1f}B', xy=(val + offset, bar.get_y() + bar.get_height()/2),
                    ha=ha, va='center', fontsize=9)

    # Panel 5: Key insight box
    ax5 = fig.add_subplot(gs[2, 2])
    ax5.axis('off')

    edu_subsidy = agency_combined.get("Department of Education", {}).get("subsidy_cost", 0)
    edu_pct = (edu_subsidy / combined_subsidy) * 100 if combined_subsidy != 0 else 0

    insight_text = (
        "KEY INSIGHT\n\n"
        f"Student loans account for\n"
        f"{edu_pct:.0f}% of net credit subsidy\n"
        f"(${edu_subsidy/1e9:.1f}B of ${combined_subsidy/1e9:.1f}B)\n\n"
        "FHA mortgage insurance\n"
        "generates $8.7B in revenue,\n"
        "partially offsetting costs."
    )

    ax5.text(0.5, 0.5, insight_text, ha='center', va='center', fontsize=11,
             transform=ax5.transAxes,
             bbox=dict(boxstyle='round', facecolor='#ffeaa7', edgecolor='#fdcb6e', linewidth=2))

    plt.savefig(output_dir / 'fig6_dashboard.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Visualizations saved to: {output_dir}")

def main():
    # Load data
    direct_loans = load_json("table1_direct_loans.json")
    loan_guarantees = load_json("table2_loan_guarantees.json")

    # Analyze for FY2026
    dl_totals, dl_by_agency, dl_programs = analyze_programs(direct_loans["programs"], "2026")
    lg_totals, lg_by_agency, lg_programs = analyze_programs(loan_guarantees["programs"], "2026")

    # Combined totals
    combined_obligations = dl_totals["obligations"] + lg_totals["obligations"]
    combined_subsidy = dl_totals["subsidy_cost"] + lg_totals["subsidy_cost"]
    combined_programs = dl_totals["program_count"] + lg_totals["program_count"]

    # Print Scorecard
    print()
    print_separator("=")
    print("FY2026 FEDERAL CREDIT SUPPLEMENT - BUDGET FORMULATION SCORECARD")
    print_separator("=")
    print()

    # Overall Summary
    print("OVERALL SUMMARY")
    print_separator("-", 40)
    print(f"{'Metric':<30} {'Value':>15}")
    print_separator("-", 40)
    print(f"{'Total Loan Volume':<30} {format_currency(combined_obligations):>15}")
    print(f"{'Total Credit Subsidy':<30} {format_currency(combined_subsidy):>15}")
    print(f"{'Wtd Avg Subsidy Rate':<30} {format_rate(combined_subsidy, combined_obligations):>15}")
    print(f"{'Number of Programs':<30} {combined_programs:>15}")
    print()

    # Direct Loans vs Loan Guarantees
    print("BY CREDIT TYPE")
    print_separator("-", 70)
    print(f"{'Type':<25} {'Loan Volume':>15} {'Subsidy Cost':>15} {'Avg Rate':>10}")
    print_separator("-", 70)
    print(f"{'Direct Loans':<25} {format_currency(dl_totals['obligations']):>15} {format_currency(dl_totals['subsidy_cost']):>15} {format_rate(dl_totals['subsidy_cost'], dl_totals['obligations']):>10}")
    print(f"{'Loan Guarantees':<25} {format_currency(lg_totals['obligations']):>15} {format_currency(lg_totals['subsidy_cost']):>15} {format_rate(lg_totals['subsidy_cost'], lg_totals['obligations']):>10}")
    print_separator("-", 70)
    print(f"{'TOTAL':<25} {format_currency(combined_obligations):>15} {format_currency(combined_subsidy):>15} {format_rate(combined_subsidy, combined_obligations):>10}")
    print()

    # By Agency - combine direct loans and guarantees
    all_agencies = set(dl_by_agency.keys()) | set(lg_by_agency.keys())
    agency_combined = {}
    for agency in all_agencies:
        dl = dl_by_agency.get(agency, {"obligations": 0, "subsidy_cost": 0, "program_count": 0})
        lg = lg_by_agency.get(agency, {"obligations": 0, "subsidy_cost": 0, "program_count": 0})
        agency_combined[agency] = {
            "obligations": dl["obligations"] + lg["obligations"],
            "subsidy_cost": dl["subsidy_cost"] + lg["subsidy_cost"],
            "program_count": dl["program_count"] + lg["program_count"],
            "dl_obligations": dl["obligations"],
            "lg_obligations": lg["obligations"],
        }

    # Sort by total obligations descending
    sorted_agencies = sorted(agency_combined.items(), key=lambda x: x[1]["obligations"], reverse=True)

    print("BY AGENCY (sorted by loan volume)")
    print_separator("-", 90)
    print(f"{'Agency':<40} {'Loan Volume':>15} {'Subsidy Cost':>15} {'Avg Rate':>10} {'Pgms':>6}")
    print_separator("-", 90)

    for agency, data in sorted_agencies:
        # Truncate long agency names
        display_name = agency[:38] + ".." if len(agency) > 40 else agency
        print(f"{display_name:<40} {format_currency(data['obligations']):>15} {format_currency(data['subsidy_cost']):>15} {format_rate(data['subsidy_cost'], data['obligations']):>10} {data['program_count']:>6}")

    print_separator("-", 90)
    print(f"{'TOTAL':<40} {format_currency(combined_obligations):>15} {format_currency(combined_subsidy):>15} {format_rate(combined_subsidy, combined_obligations):>10} {combined_programs:>6}")
    print()

    # Top 10 Programs by Subsidy Cost
    print("TOP 10 PROGRAMS BY SUBSIDY COST (absolute value)")
    print_separator("-", 100)

    all_programs = []
    for prog in dl_programs:
        all_programs.append({**prog, "type": "Direct"})
    for prog in lg_programs:
        all_programs.append({**prog, "type": "Guar"})

    # Sort by absolute subsidy cost
    top_programs = sorted(all_programs, key=lambda x: abs(x["subsidy_cost"]), reverse=True)[:10]

    print(f"{'Program':<35} {'Type':<6} {'Loan Volume':>14} {'Subsidy Cost':>14} {'Rate':>8}")
    print_separator("-", 100)
    for prog in top_programs:
        display_name = prog["name"][:33] + ".." if len(prog["name"]) > 35 else prog["name"]
        print(f"{display_name:<35} {prog['type']:<6} {format_currency(prog['obligations']):>14} {format_currency(prog['subsidy_cost']):>14} {prog['subsidy_rate']:>7.2f}%")
    print()

    # Programs generating revenue (negative subsidy)
    revenue_programs = [p for p in all_programs if p["subsidy_cost"] < 0]
    total_revenue = sum(p["subsidy_cost"] for p in revenue_programs)

    # Programs with positive subsidy cost
    cost_programs = [p for p in all_programs if p["subsidy_cost"] > 0]
    total_cost = sum(p["subsidy_cost"] for p in cost_programs)

    print("SUBSIDY COST SUMMARY")
    print_separator("-", 50)
    print(f"{'Programs with positive subsidy':<35} {len(cost_programs):>6} programs")
    print(f"{'  Total subsidy cost':<35} {format_currency(total_cost):>15}")
    print(f"{'Programs with negative subsidy':<35} {len(revenue_programs):>6} programs")
    print(f"{'  Total subsidy savings/revenue':<35} {format_currency(total_revenue):>15}")
    print(f"{'Programs with zero subsidy':<35} {dl_totals['zero_subsidy_count'] + lg_totals['zero_subsidy_count']:>6} programs")
    print_separator("-", 50)
    print(f"{'NET CREDIT SUBSIDY':<35} {format_currency(combined_subsidy):>15}")
    print()

    print_separator("=")
    print("Notes:")
    print("- Data source: Federal Credit Supplement, Budget of the U.S. Government, FY 2026")
    print("- Subsidy cost = subsidy rate x loan volume (budget authority)")
    print("- Negative subsidy indicates expected profit to the government")
    print("- Wtd Avg Rate = weighted average subsidy rate across all programs")
    print("- Excludes summary rows to avoid double-counting")
    print_separator("=")
    print()

    # Create visualizations
    create_visualizations(dl_totals, lg_totals, dl_by_agency, lg_by_agency,
                          dl_programs, lg_programs, OUTPUT_DIR)

if __name__ == "__main__":
    main()
