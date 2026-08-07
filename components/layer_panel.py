"""Panneau de gestion des couches GeoDashboard."""

from __future__ import annotations

import streamlit as st

from services.layer_manager import LayerManager


def render_layer_panel(
    manager: LayerManager,
) -> None:
    """Affiche les couches et leurs paramètres."""

    with st.container(border=True):

        # ==================================================
        # EN-TÊTE
        # ==================================================

        header_col, action_col = st.columns([4, 1])

        with header_col:
            st.subheader(
                f"Couches du projet ({manager.count()})"
            )

        with action_col:
            if manager.count() > 0:
                if st.button(
                    "Tout supprimer",
                    use_container_width=True,
                    key="delete_all_layers",
                ):
                    manager.clear()

                    # Nettoyer aussi la couche sélectionnée
                    if "selected_layer" in st.session_state:
                        del st.session_state["selected_layer"]

                    st.rerun()

        # ==================================================
        # AUCUNE COUCHE
        # ==================================================

        if manager.count() == 0:
            st.info(
                "Aucune couche chargée. "
                "Utilise le panneau d'import."
            )
            return

        # ==================================================
        # LISTE DES COUCHES
        # ==================================================

        for index, current_layer in enumerate(
            manager.list()
        ):

            title = (
                f"{'●' if current_layer.visible else '○'} "
                f"{current_layer.name}"
            )

            with st.expander(
                title,
                expanded=False,
            ):

                # ==========================================
                # VISIBILITÉ
                # ==========================================

                current_layer.visible = st.checkbox(
                    "Visible sur la carte",
                    value=current_layer.visible,
                    key=(
                        f"visible_{index}_"
                        f"{current_layer.name}"
                    ),
                )

                # ==========================================
                # MÉTADONNÉES
                # ==========================================

                summary = current_layer.summary()

                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        "**Entités :** "
                        f"{summary['Entités']:,}"
                        .replace(",", " ")
                    )

                    st.write(
                        "**Géométrie :** "
                        f"{summary['Géométrie']}"
                    )

                with col2:
                    st.write(
                        f"**CRS :** {summary['CRS']}"
                    )

                    st.write(
                        f"**Colonnes :** "
                        f"{summary['Colonnes']}"
                    )

                st.caption(
                    f"Source : {current_layer.source}"
                )

                st.divider()

                # ==========================================
                # INFORMATIONS AFFICHÉES
                # ==========================================

                st.markdown(
                    "#### Informations affichées"
                )

                available_fields = [
                    column
                    for column
                    in current_layer.geodataframe.columns
                    if (
                        column
                        != current_layer
                        .geodataframe
                        .geometry
                        .name
                    )
                ]

                if available_fields:

                    default_popup = (
                        current_layer.popup_fields
                        if current_layer.popup_fields
                        else available_fields[:6]
                    )

                    default_popup = [
                        field
                        for field in default_popup
                        if field in available_fields
                    ]

                    current_layer.popup_fields = (
                        st.multiselect(
                            "Popup au clic",
                            options=available_fields,
                            default=default_popup,
                            key=(
                                f"popup_{index}_"
                                f"{current_layer.name}"
                            ),
                            help=(
                                "Choisis les champs affichés "
                                "quand l'utilisateur clique "
                                "sur une entité."
                            ),
                        )
                    )

                    default_tooltip = (
                        current_layer.tooltip_fields
                        if current_layer.tooltip_fields
                        else current_layer.popup_fields[:3]
                    )

                    default_tooltip = [
                        field
                        for field in default_tooltip
                        if field in available_fields
                    ]

                    current_layer.tooltip_fields = (
                        st.multiselect(
                            "Informations au survol",
                            options=available_fields,
                            default=default_tooltip,
                            key=(
                                f"tooltip_{index}_"
                                f"{current_layer.name}"
                            ),
                            help=(
                                "Choisis les champs affichés "
                                "au passage de la souris."
                            ),
                        )
                    )

                else:
                    st.caption(
                        "Cette couche ne contient "
                        "aucun champ attributaire."
                    )

                st.divider()

                # ==========================================
                # STYLE
                # ==========================================

                st.markdown("#### Style")

                current_layer.style["color"] = (
                    st.color_picker(
                        "Couleur",
                        value=(
                            current_layer
                            .style["color"]
                        ),
                        key=(
                            f"color_{index}_"
                            f"{current_layer.name}"
                        ),
                    )
                )

                current_layer.style["weight"] = (
                    st.slider(
                        "Épaisseur",
                        min_value=1,
                        max_value=10,
                        value=int(
                            current_layer
                            .style["weight"]
                        ),
                        key=(
                            f"weight_{index}_"
                            f"{current_layer.name}"
                        ),
                    )
                )

                current_layer.style["opacity"] = (
                    st.slider(
                        "Opacité",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(
                            current_layer
                            .style["opacity"]
                        ),
                        step=0.05,
                        key=(
                            f"opacity_{index}_"
                            f"{current_layer.name}"
                        ),
                    )
                )

                current_layer.style["fillOpacity"] = (
                    st.slider(
                        "Remplissage",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(
                            current_layer
                            .style["fillOpacity"]
                        ),
                        step=0.05,
                        key=(
                            f"fill_{index}_"
                            f"{current_layer.name}"
                        ),
                    )
                )

                st.divider()

                # ==========================================
                # TABLE ATTRIBUTAIRE
                # ==========================================

                if st.button(
                    "Ouvrir la table attributaire",
                    key=(
                        f"table_{index}_"
                        f"{current_layer.name}"
                    ),
                    use_container_width=True,
                ):
                    st.session_state[
                        "selected_layer"
                    ] = current_layer

                    st.rerun()

                # ==========================================
                # SUPPRESSION
                # ==========================================

                if st.button(
                    "Supprimer cette couche",
                    key=(
                        f"delete_{index}_"
                        f"{current_layer.name}"
                    ),
                    use_container_width=True,
                ):

                    manager.remove(
                        current_layer.name
                    )

                    selected_layer = (
                        st.session_state.get(
                            "selected_layer"
                        )
                    )

                    if (
                        selected_layer is not None
                        and selected_layer.name
                        == current_layer.name
                    ):
                        del st.session_state[
                            "selected_layer"
                        ]

                    st.rerun()