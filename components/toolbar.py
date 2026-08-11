"""Barre du territoire d'analyse de GeoDashboard."""

from __future__ import annotations

import streamlit as st

from services.layer_manager import LayerManager
from services.territory_service import TerritoryService


TERRITORY_LAYER_NAME = "territoire_analyse"


def render_toolbar(
    manager: LayerManager,
) -> dict:
    """Affiche et prépare le territoire d'analyse."""

    with st.container(border=True):

        st.subheader(
            "Territoire d'analyse"
        )

        # =================================================
        # COUCHES CANDIDATES
        # =================================================

        candidate_layers = []

        for layer in manager.list():

            # Ne jamais proposer la couche technique
            # comme référentiel de communes.
            if layer.name == TERRITORY_LAYER_NAME:
                continue

            try:

                TerritoryService.find_name_field(
                    layer
                )

                candidate_layers.append(
                    layer
                )

            except ValueError:
                continue

        # =================================================
        # AUCUNE COUCHE DE COMMUNES
        # =================================================

        if not candidate_layers:

            st.info(
                "Importe une couche contenant "
                "les communes pour définir "
                "le territoire d'analyse."
            )

            return {
                "commune": None,
                "territory_layer": None,
            }

        # =================================================
        # COUCHE DE RÉFÉRENCE
        # =================================================

        col1, col2 = st.columns(
            [1, 2]
        )

        with col1:

            reference_layer_name = (
                st.selectbox(
                    "Couche des communes",
                    options=[
                        layer.name
                        for layer
                        in candidate_layers
                    ],
                    key="territory_reference_layer",
                )
            )

        reference_layer = manager.get(
            reference_layer_name
        )

        if reference_layer is None:

            return {
                "commune": None,
                "territory_layer": None,
            }

        # =================================================
        # COMMUNES DISPONIBLES
        # =================================================

        try:

            commune_names = (
                TerritoryService.commune_names(
                    reference_layer
                )
            )

        except ValueError as error:

            st.error(
                str(error)
            )

            return {
                "commune": None,
                "territory_layer": None,
            }

        if not commune_names:

            st.warning(
                "Aucune commune détectée "
                "dans cette couche."
            )

            return {
                "commune": None,
                "territory_layer": None,
            }

        # =================================================
        # COMMUNE SÉLECTIONNÉE
        # =================================================

        with col2:

            saved_commune = (
                st.session_state.get(
                    "selected_commune"
                )
            )

            default_index = 0

            if saved_commune in commune_names:

                default_index = (
                    commune_names.index(
                        saved_commune
                    )
                )

            commune = st.selectbox(
                "Commune",
                options=commune_names,
                index=default_index,
                key="territory_commune",
            )

        # =================================================
        # SIGNATURE DU TERRITOIRE
        # =================================================

        territory_signature = (
            reference_layer.name,
            commune,
        )

        previous_signature = (
            st.session_state.get(
                "territory_signature"
            )
        )

        # =================================================
        # CRÉER / METTRE À JOUR LE TERRITOIRE
        # =================================================

        if (
            territory_signature
            != previous_signature
            or manager.get(
                TERRITORY_LAYER_NAME
            ) is None
        ):

            territory_layer = (
                TerritoryService.select_commune(
                    layer=reference_layer,
                    commune_name=commune,
                    result_name=TERRITORY_LAYER_NAME,
                )
            )

            # Retirer l'ancien territoire.
            manager.remove(
                TERRITORY_LAYER_NAME
            )

            # Ajouter le nouveau.
            manager.add(
                territory_layer
            )

            st.session_state[
                "territory_signature"
            ] = territory_signature

            # Réinitialiser le cadrage cartographique.
            st.session_state.pop(
                "map_bounds",
                None,
            )

            st.session_state.pop(
                "map_layers_signature",
                None,
            )

        else:

            territory_layer = manager.get(
                TERRITORY_LAYER_NAME
            )

        # =================================================
        # MÉMORISATION
        # =================================================

        st.session_state[
            "selected_commune"
        ] = commune

        st.session_state[
            "territory_layer"
        ] = territory_layer

        # =================================================
        # INFORMATIONS
        # =================================================

        area_km2 = (
            TerritoryService.area_km2(
                territory_layer
            )
            if territory_layer is not None
            else 0.0
        )

        info1, info2 = st.columns(2)

        with info1:

            st.metric(
                "Commune sélectionnée",
                commune,
            )

        with info2:

            st.metric(
                "Surface",
                (
                    f"{area_km2:.2f} km²"
                    .replace(".", ",")
                ),
            )

        return {
            "commune": commune,
            "territory_layer": territory_layer,
        }