"""Metric card helpers for the FCS dashboard."""

from __future__ import annotations

import streamlit as st


def _fmt_dollars(value_millions: float | None, precision: int = 1) -> str:
    """Format a dollar amount in millions to a human-readable string."""
    if value_millions is None:
        return "N/A"
    abs_val = abs(value_millions)
    sign = "-" if value_millions < 0 else ""
    if abs_val >= 1_000_000:
        return f"{sign}${abs_val / 1_000_000:,.{precision}f}T"
    if abs_val >= 1_000:
        return f"{sign}${abs_val / 1_000:,.{precision}f}B"
    return f"{sign}${abs_val:,.{precision}f}M"


def _fmt_pct(value: float | None, precision: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.{precision}f}%"


def _fmt_count(value: int | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:,}"


def _compute_delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return current - previous


def display_metrics(
    metrics: list[dict],
    columns: int = 4,
) -> None:
    """Render a row of st.metric cards.

    Each dict in metrics should have:
        label: str
        value: str (pre-formatted)
        delta: str | None (pre-formatted)
        delta_color: "normal" | "inverse" | "off" (default "normal")
    """
    cols = st.columns(columns)
    for i, m in enumerate(metrics):
        with cols[i % columns]:
            st.metric(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
            )
