"""Carte interactive de GeoDashboard."""

from __future__ import annotations

import folium
import streamlit as st

from streamlit_folium import st_folium

from services.layer_manager import LayerManager
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
    commune: str,
    theme: str,
    distance: int,
) -> None:
    """Affiche la carte interactive principale."""

    st.subheader("Carte interactive")

    st.caption(
        f"{commune} · {theme} · {distance} m"
    )

    map_object = folium.Map(
        location=[46.6, 2.5],
        zoom_start=6,
        tiles=None,
        control_scale=True,
    )

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

    global_bounds = None

    for layer in manager.list():

        current_bounds = add_layer_to_map(
            map_object,
            layer,
        )

        global_bounds = merge_bounds(
            global_bounds,
            current_bounds,
        )

    if global_bounds is not None:
        map_object.fit_bounds(
            global_bounds,
            padding=(20, 20),
        )

    folium.LayerControl(
        collapsed=False,
    ).add_to(map_object)

    st_folium(
        map_object,
        height=620,
        use_container_width=True,
        key="main_map",
    )