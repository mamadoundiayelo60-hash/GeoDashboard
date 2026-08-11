"""Carte interactive de GeoDashboard."""

from __future__ import annotations

import folium
import streamlit as st

from streamlit_folium import st_folium

from models.selection import Selection
from services.layer_manager import LayerManager
from services.selection_manager import SelectionManager
from styles.renderer import add_layer_to_map


# =========================================================
# EMPRISES
# =========================================================

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


# =========================================================
# ÉTAT DE LA CARTE
# =========================================================

def get_saved_center() -> list[float]:
    """Retourne le centre initial de la carte."""

    return st.session_state.get(
        "map_center",
        [46.6, 2.5],
    )


def get_saved_zoom() -> int:
    """Retourne le zoom initial."""

    return st.session_state.get(
        "map_zoom",
        6,
    )


def get_layers_signature(
    manager: LayerManager,
) -> tuple:
    """
    Retourne une signature structurelle des couches.

    La visibilité n'est volontairement PAS utilisée :
    cocher/décocher une couche dans Leaflet ne doit pas
    provoquer une reconstruction de la carte.
    """

    return tuple(
        (
            layer.name,
            layer.feature_count,
        )
        for layer in manager.list()
    )


# =========================================================
# CARTE
# =========================================================

def render_map_panel(
    manager: LayerManager,
    selection_manager: SelectionManager,
    commune: str,
    theme: str,
    distance: int,
) -> None:
    """Affiche la carte interactive principale."""

    st.subheader(
        "Carte interactive"
    )

    # On n'affiche plus "0 m" puisque la distance
    # appartient maintenant aux outils comme Buffer.
    if distance > 0:

        st.caption(
            f"{commune} · {theme} · {distance} m"
        )

    else:

        st.caption(
            f"{commune} · {theme}"
        )

    # =====================================================
    # DÉTECTER UN VRAI CHANGEMENT DE COUCHES
    # =====================================================

    layers_signature = (
        get_layers_signature(
            manager
        )
    )

    previous_signature = (
        st.session_state.get(
            "map_layers_signature"
        )
    )

    layers_changed = (
        layers_signature
        != previous_signature
    )

    if layers_changed:

        st.session_state[
            "map_layers_signature"
        ] = layers_signature

        # Nouvelle instance uniquement quand
        # une couche est réellement ajoutée/supprimée.
        st.session_state[
            "map_instance"
        ] = (
            st.session_state.get(
                "map_instance",
                0,
            )
            + 1
        )

    # =====================================================
    # VUE INITIALE
    # =====================================================

    saved_center = (
        get_saved_center()
    )

    saved_zoom = (
        get_saved_zoom()
    )

    # Pour le filtrage des grosses couches uniquement.
    visible_bounds = (
        st.session_state.get(
            "map_bounds"
        )
    )

    # =====================================================
    # CRÉATION DE LA CARTE
    # =====================================================

    map_object = folium.Map(
        location=saved_center,
        zoom_start=saved_zoom,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    # =====================================================
    # FONDS DE CARTE
    # =====================================================

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        control=True,
        show=True,
    ).add_to(
        map_object
    )

    folium.TileLayer(
        tiles="CartoDB positron",
        name="CartoDB clair",
        control=True,
        show=False,
    ).add_to(
        map_object
    )

    folium.TileLayer(
        tiles="CartoDB dark_matter",
        name="CartoDB sombre",
        control=True,
        show=False,
    ).add_to(
        map_object
    )

    folium.TileLayer(
        tiles="OpenTopoMap",
        name="OpenTopoMap",
        control=True,
        show=False,
    ).add_to(
        map_object
    )

    # =====================================================
    # COUCHES
    # =====================================================

    global_bounds = None

    for layer in manager.list():

        current_bounds = (
            add_layer_to_map(
                map_object=map_object,
                layer=layer,
                selection=(
                    selection_manager.current
                ),
                view_bounds=visible_bounds,
                zoom=saved_zoom,
            )
        )

        global_bounds = merge_bounds(
            global_bounds,
            current_bounds,
        )

    # =====================================================
    # CADRAGE AUTOMATIQUE
    #
    # IMPORTANT :
    # uniquement lorsqu'une couche est ajoutée/supprimée.
    # Jamais pendant un zoom ou un déplacement utilisateur.
    # =====================================================

    if (
        layers_changed
        and global_bounds is not None
    ):

        map_object.fit_bounds(
            global_bounds,
            padding=(20, 20),
        )

    # =====================================================
    # CONTRÔLE DES COUCHES
    # =====================================================

    folium.LayerControl(
        collapsed=False,
    ).add_to(
        map_object
    )

    # =====================================================
    # AFFICHAGE
    # =====================================================

    map_instance = (
        st.session_state.get(
            "map_instance",
            0,
        )
    )

    map_state = st_folium(
        map_object,
        height=620,
        use_container_width=True,
        key=f"main_map_{map_instance}",

        # =================================================
        # TRÈS IMPORTANT
        #
        # On ne demande PLUS :
        # - zoom
        # - center
        # - bounds
        #
        # Donc zoomer/déplacer la carte ne déclenche plus
        # continuellement Streamlit.
        # =================================================

        returned_objects=[
            "last_active_drawing",
        ],
    )

    if not map_state:
        return

    # =====================================================
    # SÉLECTION
    # =====================================================

    clicked_feature = (
        map_state.get(
            "last_active_drawing"
        )
    )

    if not clicked_feature:
        return

    properties = (
        clicked_feature.get(
            "properties",
            {},
        )
    )

    layer_name = (
        properties.get(
            "__layer_name"
        )
    )

    feature_index = (
        properties.get(
            "__feature_index"
        )
    )

    if (
        layer_name is None
        or feature_index is None
    ):
        return

    feature_index = int(
        feature_index
    )

    attributes = {
        key: value
        for key, value
        in properties.items()
        if not key.startswith("__")
    }

    current_selection = (
        selection_manager.current
    )

    same_selection = (
        current_selection is not None
        and current_selection.layer_name
        == layer_name
        and current_selection.feature_index
        == feature_index
    )

    # =====================================================
    # DÉSÉLECTION
    # =====================================================

    if same_selection:

        selection_manager.clear()

        st.rerun()

    # =====================================================
    # NOUVELLE SÉLECTION
    # =====================================================

    selection_manager.select(
        Selection(
            layer_name=str(
                layer_name
            ),
            feature_index=feature_index,
            attributes=attributes,
        )
    )

    st.rerun()