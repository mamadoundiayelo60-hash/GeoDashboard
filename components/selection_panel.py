"""Panneau de sélection GeoDashboard."""

from __future__ import annotations

import streamlit as st

from services.selection_manager import (
    SelectionManager,
)


def render_selection_panel(
    selection_manager: SelectionManager,
) -> None:
    """Affiche les informations de l'entité sélectionnée."""

    if not selection_manager.has_selection():
        return

    selection = selection_manager.current

    with st.container(border=True):

        st.subheader("Entité sélectionnée")

        st.write(
            f"**Couche :** "
            f"{selection.layer_name}"
        )

        st.write(
            f"**Entité :** "
            f"{selection.feature_index + 1}"
        )

        st.markdown("#### Attributs")

        for field, value in (
            selection.attributes.items()
        ):
            st.write(
                f"**{field} :** {value}"
            )

        if st.button(
            "Effacer la sélection",
            use_container_width=True,
            key="clear_selection",
        ):
            selection_manager.clear()
            st.rerun()