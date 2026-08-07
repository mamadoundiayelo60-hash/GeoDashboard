"""Table attributaire."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.layer import Layer


def render_attribute_table(
    layer: Layer,
) -> None:
    """Affiche la table attributaire d'une couche."""

    st.subheader(
        f"📊 Table attributaire : {layer.name}"
    )

    df = layer.geodataframe.copy()

    # La géométrie est masquée
    geometry_column = df.geometry.name

    if geometry_column in df.columns:
        df = df.drop(
            columns=[geometry_column]
        )

    search = st.text_input(
        "🔍 Rechercher",
        placeholder="Tape un texte...",
        key=f"search_{layer.name}",
    )

    if search:

        mask = (
            df.astype(str)
            .apply(
                lambda col:
                col.str.contains(
                    search,
                    case=False,
                    na=False,
                )
            )
            .any(axis=1)
        )

        df = df.loc[mask]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"{len(df)} enregistrement(s)"
    )