"""Barre de paramètres de GeoDashboard."""

from __future__ import annotations

import streamlit as st


def render_toolbar() -> dict:
    """Affiche les paramètres et retourne les choix de l’utilisateur."""

    with st.container(border=True):
        st.subheader("Paramètres de l’analyse")

        col1, col2, col3, col4 = st.columns(
            [1.4, 1.4, 1.2, 1]
        )

        with col1:
            commune = st.selectbox(
                "Commune",
                [
                    "Calais",
                    "Lille",
                    "Dunkerque",
                    "Arras",
                    "Autre",
                ],
                key="commune",
            )

        with col2:
            theme = st.selectbox(
                "Thème",
                [
                    "Santé",
                    "Culture",
                    "Administration",
                    "Éducation",
                    "Environnement",
                    "Justice",
                    "Loisirs",
                    "Patrimoine",
                    "Social",
                    "Sport",
                    "Tourisme",
                ],
                key="theme",
            )

        with col3:
            distance = st.selectbox(
                "Distance",
                [
                    300,
                    500,
                    600,
                    700,
                    800,
                    1000,
                ],
                index=1,
                format_func=lambda value: f"{value} m",
                key="distance",
            )

        with col4:
            st.write("")
            st.write("")

            generate = st.button(
                "Générer",
                type="primary",
                use_container_width=True,
            )

        
    return {
    "commune": commune,
    "theme": theme,
    "distance": distance,
    "generate": generate,
}