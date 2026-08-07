"""Carte interactive de GeoDashboard."""

from __future__ import annotations

import folium
import streamlit as st

from streamlit_folium import st_folium

from models.selection import Selection
from services.layer_manager import LayerManager
from services.selection_manager import SelectionManager
from styles.renderer import add_layer_to_map


def merge_bounds(
    global_bounds,
    current_bounds,
):
    """Fusionne deux emprises Leaflet."""

    if current_bounds is None:
        return global_bounds

    if global_bounds is None:
        return current_bounds

    return [
        [
            min(
                global_bounds[0][0],
                current_bounds[0][0],
            ),
            min(
                global_bounds[0][1],
                current_bounds[0][1],
            ),
        ],
        [
            max(
                global_bounds[1][0],
                current_bounds[1][0],
            ),
            max(
                global_bounds[1][1],
                current_bounds[1][1],
            ),
        ],
    ]


def render_map_panel(
    manager: LayerManager,
    selection_manager: SelectionManager,
    commune: str,
    theme: str,
    distance: int,
) -> None:
    """Affiche la carte interactive principale."""

    st.subheader("Carte interactive")

    st.caption(
        f"{commune} · {theme} · {distance} m"
    )

    # =====================================================
    # CRÉATION DE LA CARTE
    # =====================================================

    map_object = folium.Map(
        location=[46.6, 2.5],
        zoom_start=6,
        tiles=None,
        control_scale=True,
    )

    # =====================================================
    # FONDS DE CARTE
    # =====================================================

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        control=True,
    ).add_to(map_object)

    folium.TileLayer(
        tiles="CartoDB positron",
        name="CartoDB clair",
        control=True,
    ).add_to(map_object)

    # =====================================================
    # COUCHES
    # =====================================================

    global_bounds = None

    for layer in manager.list():

        current_bounds = add_layer_to_map(
            map_object=map_object,
            layer=layer,
            selection=selection_manager.current,
        )

        global_bounds = merge_bounds(
            global_bounds,
            current_bounds,
        )

    # =====================================================
    # ZOOM AUTOMATIQUE
    # =====================================================

    if global_bounds is not None:

        map_object.fit_bounds(
            global_bounds,
            padding=(20, 20),
        )

    # =====================================================
    # CONTRÔLE DES COUCHES
    # =====================================================

    folium.LayerControl(
        collapsed=False,
    ).add_to(map_object)

    # =====================================================
    # AFFICHAGE DE LA CARTE
    # =====================================================

    map_state = st_folium(
        map_object,
        height=620,
        use_container_width=True,
        key="main_map",
    )

    # =====================================================
    # SÉLECTION D'UNE ENTITÉ
    # =====================================================

    if not map_state:
        return

    clicked_feature = map_state.get(
        "last_active_drawing"
    )

    if not clicked_feature:
        return

    properties = clicked_feature.get(
        "properties",
        {},
    )

    layer_name = properties.get(
        "__layer_name"
    )

    feature_index = properties.get(
        "__feature_index"
    )

    # Si les champs techniques ne sont pas présents,
    # le clic ne peut pas encore être associé à une couche.
    if (
        layer_name is None
        or feature_index is None
    ):
        return

    # =====================================================
    # ATTRIBUTS MÉTIER
    # =====================================================

    attributes = {
        key: value
        for key, value in properties.items()
        if not key.startswith("__")
    }

    # =====================================================
    # ÉVITER LES RERUN INUTILES
    # =====================================================

    current_selection = (
        selection_manager.current
    )

    selection_changed = (
        current_selection is None
        or current_selection.layer_name
        != layer_name
        or current_selection.feature_index
        != int(feature_index)
    )

    if not selection_changed:
        return

    # =====================================================
    # ENREGISTRER LA SÉLECTION
    # =====================================================

    selection_manager.select(
        Selection(
            layer_name=str(layer_name),
            feature_index=int(
                feature_index
            ),
            attributes=attributes,
        )
    )

    st.rerun()