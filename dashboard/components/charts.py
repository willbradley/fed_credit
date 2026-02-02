"""Plotly chart factory functions for the FCS dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_TEMPLATE = "plotly_white"
_CREDIT_COLORS = {"direct_loan": "#1f77b4", "loan_guarantee": "#ff7f0e"}
_CREDIT_LABELS = {"direct_loan": "Direct Loans", "loan_guarantee": "Loan Guarantees"}


def _label_credit(ct: str) -> str:
    return _CREDIT_LABELS.get(ct, ct)


# ---------------------------------------------------------------------------
# Overview charts
# ---------------------------------------------------------------------------

def obligations_trend_chart(summary: pd.DataFrame) -> go.Figure:
    """Stacked area: total obligations by credit type over time ($B)."""
    df = summary.copy()
    df["credit_label"] = df["credit_type"].map(_label_credit)
    df["obligations_billions"] = df["total_obligations_millions"] / 1_000

    fig = px.area(
        df.sort_values("budget_year"),
        x="budget_year",
        y="obligations_billions",
        color="credit_label",
        color_discrete_map={_label_credit(k): v for k, v in _CREDIT_COLORS.items()},
        labels={"budget_year": "Budget Year", "obligations_billions": "Obligations ($B)", "credit_label": "Credit Type"},
        template=_TEMPLATE,
    )
    fig.update_layout(
        title="Total New Obligations by Credit Type",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def subsidy_rate_trend_chart(summary: pd.DataFrame) -> go.Figure:
    """Line chart: weighted avg subsidy rate by credit type, with 0% reference."""
    df = summary.copy()
    df["credit_label"] = df["credit_type"].map(_label_credit)

    fig = px.line(
        df.sort_values("budget_year"),
        x="budget_year",
        y="weighted_avg_subsidy_rate",
        color="credit_label",
        color_discrete_map={_label_credit(k): v for k, v in _CREDIT_COLORS.items()},
        markers=True,
        labels={"budget_year": "Budget Year", "weighted_avg_subsidy_rate": "Wtd. Avg. Subsidy Rate (%)", "credit_label": "Credit Type"},
        template=_TEMPLATE,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        title="Weighted Average Subsidy Rate",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def reestimate_bar_chart(re_df: pd.DataFrame) -> go.Figure:
    """Bar chart: total net reestimates by year, colored by sign."""
    agg = (
        re_df.groupby("budget_year")["current_reestimate_millions"]
        .sum()
        .reset_index()
    )
    agg["color"] = agg["current_reestimate_millions"].apply(
        lambda x: "Cost Increase" if x > 0 else "Savings"
    )

    fig = px.bar(
        agg,
        x="budget_year",
        y="current_reestimate_millions",
        color="color",
        color_discrete_map={"Cost Increase": "#d62728", "Savings": "#2ca02c"},
        labels={"budget_year": "Budget Year", "current_reestimate_millions": "Net Reestimates ($M)", "color": ""},
        template=_TEMPLATE,
    )
    fig.update_layout(
        title="Total Net Reestimates by Year",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def reestimate_decomposition_chart(re_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: interest-rate vs technical components by year."""
    agg = (
        re_df.groupby("budget_year")
        .agg(
            interest=("change_interest_rates_pct_pts", "mean"),
            technical=("change_technical_pct_pts", "mean"),
        )
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["budget_year"], y=agg["interest"],
        name="Interest Rate", marker_color="#1f77b4",
    ))
    fig.add_trace(go.Bar(
        x=agg["budget_year"], y=agg["technical"],
        name="Technical", marker_color="#ff7f0e",
    ))
    fig.update_layout(
        barmode="relative",
        title="Reestimate Decomposition (Avg Rate Change, pct pts)",
        xaxis_title="Budget Year",
        yaxis_title="Avg Change (pct pts)",
        template=_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def sector_obligations_chart(bf_df: pd.DataFrame, year: int) -> go.Figure:
    """Horizontal bar: obligations by sector for a given year."""
    current = bf_df[(bf_df["cohort_type"] == "current") & (bf_df["budget_year"] == year)]
    agg = (
        current.groupby("sector_name")["obligations_millions"]
        .sum()
        .sort_values()
        .reset_index()
    )
    agg["obligations_billions"] = agg["obligations_millions"] / 1_000

    fig = px.bar(
        agg,
        x="obligations_billions",
        y="sector_name",
        orientation="h",
        labels={"obligations_billions": "Obligations ($B)", "sector_name": "Sector"},
        template=_TEMPLATE,
    )
    fig.update_layout(title=f"Obligations by Sector — FY{year}")
    return fig


# ---------------------------------------------------------------------------
# Sector view charts
# ---------------------------------------------------------------------------

def sector_grouped_bar(bf_df: pd.DataFrame, year: int) -> go.Figure:
    """Grouped bar: obligations by sector and credit type for a given year."""
    current = bf_df[(bf_df["cohort_type"] == "current") & (bf_df["budget_year"] == year)]
    agg = (
        current.groupby(["sector_name", "credit_type"])["obligations_millions"]
        .sum()
        .reset_index()
    )
    agg["credit_label"] = agg["credit_type"].map(_label_credit)
    agg["obligations_billions"] = agg["obligations_millions"] / 1_000

    fig = px.bar(
        agg,
        x="sector_name",
        y="obligations_billions",
        color="credit_label",
        barmode="group",
        color_discrete_map={_label_credit(k): v for k, v in _CREDIT_COLORS.items()},
        labels={"sector_name": "Sector", "obligations_billions": "Obligations ($B)", "credit_label": "Credit Type"},
        template=_TEMPLATE,
    )
    fig.update_layout(
        title=f"Obligations by Sector — FY{year}",
        xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def sector_faceted_area(bf_df: pd.DataFrame, year_range: tuple[int, int]) -> go.Figure:
    """Small multiples: obligations trend per sector."""
    current = bf_df[
        (bf_df["cohort_type"] == "current")
        & (bf_df["budget_year"] >= year_range[0])
        & (bf_df["budget_year"] <= year_range[1])
    ]
    agg = (
        current.groupby(["budget_year", "sector_name"])["obligations_millions"]
        .sum()
        .reset_index()
    )
    agg["obligations_billions"] = agg["obligations_millions"] / 1_000

    fig = px.area(
        agg.sort_values("budget_year"),
        x="budget_year",
        y="obligations_billions",
        facet_col="sector_name",
        facet_col_wrap=4,
        labels={"budget_year": "Year", "obligations_billions": "$B"},
        template=_TEMPLATE,
        height=600,
    )
    fig.update_layout(title="Obligations Trend by Sector")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return fig


def sector_heatmap(bf_df: pd.DataFrame, year_range: tuple[int, int]) -> go.Figure:
    """Heatmap: sectors × years, color = weighted avg subsidy rate."""
    current = bf_df[
        (bf_df["cohort_type"] == "current")
        & (bf_df["budget_year"] >= year_range[0])
        & (bf_df["budget_year"] <= year_range[1])
    ].copy()

    def _wavg(g):
        mask = g["subsidy_rate_pct"].notna() & g["obligations_thousands"].notna()
        gg = g[mask]
        total = gg["obligations_thousands"].sum()
        if total == 0:
            return None
        return (gg["subsidy_rate_pct"] * gg["obligations_thousands"]).sum() / total

    pivot = (
        current.groupby(["sector_name", "budget_year"])
        .apply(_wavg, include_groups=False)
        .reset_index(name="rate")
        .pivot(index="sector_name", columns="budget_year", values="rate")
    )

    fig = px.imshow(
        pivot,
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        labels={"color": "Wtd. Avg. Subsidy Rate (%)", "x": "Budget Year", "y": "Sector"},
        aspect="auto",
        template=_TEMPLATE,
    )
    fig.update_layout(title="Subsidy Rate Heatmap by Sector & Year", height=500)
    return fig


def sector_reestimate_stacked(re_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: total reestimates by sector (interest vs technical)."""
    agg = (
        re_df.groupby("sector_name")
        .agg(
            interest=("change_interest_rates_pct_pts", "mean"),
            technical=("change_technical_pct_pts", "mean"),
        )
        .sort_values("technical")
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg["sector_name"], x=agg["interest"],
        name="Interest Rate", marker_color="#1f77b4", orientation="h",
    ))
    fig.add_trace(go.Bar(
        y=agg["sector_name"], x=agg["technical"],
        name="Technical", marker_color="#ff7f0e", orientation="h",
    ))
    fig.update_layout(
        barmode="relative",
        title="Reestimate Decomposition by Sector",
        xaxis_title="Avg Change (pct pts)",
        template=_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Agency view charts
# ---------------------------------------------------------------------------

def agency_obligations_trend(bf_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Line chart: obligations trend for top N programs by peak obligations."""
    current = bf_df[bf_df["cohort_type"] == "current"].copy()
    peaks = (
        current.groupby("canonical_name")["obligations_millions"]
        .max()
        .nlargest(top_n)
        .index
    )
    top = current[current["canonical_name"].isin(peaks)]

    fig = px.line(
        top.sort_values("budget_year"),
        x="budget_year",
        y="obligations_millions",
        color="canonical_name",
        markers=True,
        labels={"budget_year": "Budget Year", "obligations_millions": "Obligations ($M)", "canonical_name": "Program"},
        template=_TEMPLATE,
    )
    fig.update_layout(
        title=f"Top {top_n} Programs — Obligations Trend",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def agency_subsidy_scatter(bf_df: pd.DataFrame, year: int) -> go.Figure:
    """Scatter: X=obligations (log), Y=subsidy rate, size=subsidy cost."""
    current = bf_df[
        (bf_df["cohort_type"] == "current") & (bf_df["budget_year"] == year)
    ].copy()
    current = current.dropna(subset=["obligations_millions", "subsidy_rate_pct"])
    current["abs_subsidy"] = current["subsidy_amount_thousands"].abs() / 1_000
    current = current[current["obligations_millions"] > 0]

    fig = px.scatter(
        current,
        x="obligations_millions",
        y="subsidy_rate_pct",
        size="abs_subsidy",
        hover_name="canonical_name",
        log_x=True,
        labels={
            "obligations_millions": "Obligations ($M, log)",
            "subsidy_rate_pct": "Subsidy Rate (%)",
            "abs_subsidy": "Abs. Subsidy Cost ($M)",
        },
        template=_TEMPLATE,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(title=f"Subsidy Rate vs. Obligations — FY{year}")
    return fig


# ---------------------------------------------------------------------------
# Program view charts
# ---------------------------------------------------------------------------

def program_dual_axis_chart(bf_df: pd.DataFrame) -> go.Figure:
    """Dual-axis: obligations bar + subsidy rate line over time."""
    current = bf_df[bf_df["cohort_type"] == "current"].sort_values("budget_year")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=current["budget_year"],
        y=current["obligations_millions"],
        name="Obligations ($M)",
        marker_color="#1f77b4",
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=current["budget_year"],
        y=current["subsidy_rate_pct"],
        name="Subsidy Rate (%)",
        mode="lines+markers",
        line=dict(color="#d62728"),
        yaxis="y2",
    ))

    fig.update_layout(
        title="Budget Formulation History",
        xaxis_title="Budget Year",
        yaxis=dict(title="Obligations ($M)", side="left"),
        yaxis2=dict(title="Subsidy Rate (%)", overlaying="y", side="right"),
        template=_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def program_reestimate_comparison(re_df: pd.DataFrame) -> go.Figure:
    """Grouped bar: original vs reestimated rate by cohort year."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=re_df["cohort_year"],
        y=re_df["original_subsidy_rate_pct"],
        name="Original Rate",
        marker_color="#1f77b4",
    ))
    fig.add_trace(go.Bar(
        x=re_df["cohort_year"],
        y=re_df["current_reestimated_rate_pct"],
        name="Reestimated Rate",
        marker_color="#ff7f0e",
    ))

    fig.update_layout(
        barmode="group",
        title="Original vs. Reestimated Subsidy Rate by Cohort",
        xaxis_title="Cohort Year",
        yaxis_title="Subsidy Rate (%)",
        template=_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def program_reestimate_decomposition(re_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: interest vs technical by cohort year."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=re_df["cohort_year"],
        y=re_df["change_interest_rates_pct_pts"],
        name="Interest Rate",
        marker_color="#1f77b4",
    ))
    fig.add_trace(go.Bar(
        x=re_df["cohort_year"],
        y=re_df["change_technical_pct_pts"],
        name="Technical",
        marker_color="#ff7f0e",
    ))

    fig.update_layout(
        barmode="relative",
        title="Reestimate Decomposition by Cohort",
        xaxis_title="Cohort Year",
        yaxis_title="Change (pct pts)",
        template=_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
