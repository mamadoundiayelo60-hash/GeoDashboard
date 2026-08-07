"""Panneau des indicateurs."""

from __future__ import annotations

import streamlit as st

from .metric_card import render_metric_card


def format_number(value: int) -> str:
    """Formate un entier avec des espaces."""

    return f"{value:,}".replace(",", " ")


def render_stats_panel(
    *,
    coverage: float = 0.0,
    buildings: int = 0,
    facilities: int = 0,
    distance: int = 500,
) -> None:
    """Affiche les principaux indicateurs de l’analyse."""

    st.subheader("Indicateurs")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric_card(
            title="Couverture",
            value=f"{coverage:.2f} %".replace(".", ","),
            subtitle="Taux de couverture",
            color="#059669",
        )

    with c2:
        render_metric_card(
            title="Bâtiments",
            value=format_number(buildings),
            subtitle="Bâtiments analysés",
            color="#2563EB",
        )

    with c3:
        render_metric_card(
            title="Équipements",
            value=format_number(facilities),
            subtitle="Couches actuellement chargées",
            color="#F59E0B",
        )

    with c4:
        render_metric_card(
            title="Distance",
            value=f"{distance} m",
            subtitle="Zone d’analyse",
            color="#DC2626",
        )