"""Moteur de rendu cartographique de GeoDashboard."""

from __future__ import annotations

import folium
import geopandas as gpd
import pandas as pd

from models.layer import Layer
from models.selection import Selection


def prepare_for_folium(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Prépare une couche pour Leaflet/Folium.

    - reprojection en EPSG:4326
    - suppression des géométries nulles
    - conversion des dates en texte
    """

    data = gdf.copy()

    # Leaflet/Folium travaille en latitude / longitude.
    if data.crs is not None:
        data = data.to_crs("EPSG:4326")

    # Supprimer les géométries nulles.
    data = data[
        data.geometry.notna()
    ].copy()

    geometry_column = data.geometry.name

    # Rendre les attributs compatibles JSON.
    for column in data.columns:

        if column == geometry_column:
            continue

        if pd.api.types.is_datetime64_any_dtype(
            data[column]
        ):
            data[column] = (
                data[column]
                .astype(str)
                .replace("NaT", "")
            )

        elif data[column].dtype == "object":

            data[column] = data[column].apply(
                lambda value: (
                    value.isoformat()
                    if isinstance(value, pd.Timestamp)
                    else value
                )
            )

    return data


def choose_display_fields(
    gdf: gpd.GeoDataFrame,
) -> list[str]:
    """
    Choisit automatiquement les champs les plus parlants
    et ignore les champs techniques.
    """

    columns = [
        column
        for column in gdf.columns
        if column != gdf.geometry.name
    ]

    preferred_fields = [
        "nom",
        "name",
        "libelle",
        "libellé",
        "voie",
        "rue",
        "adresse",
        "tex2",
        "commune",
        "ville",
        "code_insee",
        "insee",
        "ccocom",
        "type",
        "categorie",
        "catégorie",
        "sens_unique",
        "date_creation",
        "date_maj",
    ]

    ignored_fields = {
        "fid",
        "gid",
        "id",
        "idu",
        "id_nomvoie",
        "id_typevoi",
        "id_troncon",
        "fk_voie",
        "id_troncon_pere",
        "numdg",
        "numdd",
        "numfg",
        "numfd",

        # Champs techniques GeoDashboard
        "__layer_name",
        "__feature_index",
    }

    selected: list[str] = []

    # Champs importants en priorité.
    for preferred in preferred_fields:

        for column in columns:

            if (
                column.lower() == preferred.lower()
                and column not in selected
            ):
                selected.append(column)

    # Compléter avec d'autres champs non techniques.
    for column in columns:

        if column.lower() in ignored_fields:
            continue

        if column not in selected:
            selected.append(column)

        if len(selected) >= 6:
            break

    return selected[:6]


def build_style(
    layer: Layer,
    geometry_type: str,
) -> dict:
    """
    Construit le style Folium à partir
    des paramètres de la couche.
    """

    geometry_type = geometry_type.lower()

    style = {
        "color": layer.style.get(
            "color",
            "#2563EB",
        ),
        "weight": layer.style.get(
            "weight",
            3,
        ),
        "opacity": layer.style.get(
            "opacity",
            0.85,
        ),
    }

    if "polygon" in geometry_type:

        style["fillColor"] = layer.style.get(
            "color",
            "#2563EB",
        )

        style["fillOpacity"] = layer.style.get(
            "fillOpacity",
            0.20,
        )

    return style


def build_popup(
    layer: Layer,
    gdf: gpd.GeoDataFrame,
):
    """Construit la popup au clic."""

    default_fields = choose_display_fields(
        gdf
    )

    fields = (
        layer.popup_fields
        if layer.popup_fields
        else default_fields
    )

    fields = [
        field
        for field in fields
        if (
            field in gdf.columns
            and not field.startswith("__")
        )
    ]

    if not fields:
        return None

    return folium.GeoJsonPopup(
        fields=fields,
        aliases=[
            f"{field} :"
            for field in fields
        ],
        labels=True,
        localize=True,
        max_width=450,
    )


def build_tooltip(
    layer: Layer,
    gdf: gpd.GeoDataFrame,
):
    """Construit le tooltip au survol."""

    default_fields = choose_display_fields(
        gdf
    )

    fields = (
        layer.tooltip_fields
        if layer.tooltip_fields
        else default_fields[:3]
    )

    fields = [
        field
        for field in fields
        if (
            field in gdf.columns
            and not field.startswith("__")
        )
    ]

    if not fields:
        return None

    return folium.GeoJsonTooltip(
        fields=fields,
        aliases=[
            f"{field} :"
            for field in fields
        ],
        labels=True,
        sticky=False,
    )


def add_selection_to_map(
    map_object: folium.Map,
    layer: Layer,
    gdf: gpd.GeoDataFrame,
    selection: Selection | None,
) -> None:
    """
    Met en surbrillance l'entité sélectionnée.
    """

    if selection is None:
        return

    if selection.layer_name != layer.name:
        return

    feature_index = (
        selection.feature_index
    )

    if feature_index < 0:
        return

    if feature_index >= len(gdf):
        return

    selected_gdf = gdf.iloc[
        [feature_index]
    ].copy()

    folium.GeoJson(
        data=selected_gdf.to_json(
            drop_id=True
        ),
        name="Sélection",
        style_function=lambda feature: {
            "color": "#DC2626",
            "weight": 6,
            "opacity": 1.0,
            "fillColor": "#FACC15",
            "fillOpacity": 0.45,
        },
        highlight_function=lambda feature: {
            "color": "#DC2626",
            "weight": 7,
            "fillColor": "#FDE047",
            "fillOpacity": 0.55,
        },
        control=False,
    ).add_to(map_object)


def add_layer_to_map(
    map_object: folium.Map,
    layer: Layer,
    selection: Selection | None = None,
) -> list[list[float]] | None:
    """
    Ajoute une couche à la carte.

    Retourne l'emprise Leaflet :

    [
        [min_latitude, min_longitude],
        [max_latitude, max_longitude],
    ]
    """

    if not layer.visible:
        return None

    # =====================================================
    # PRÉPARATION DES DONNÉES
    # =====================================================

    gdf = prepare_for_folium(
        layer.geodataframe
    )

    if gdf.empty:
        return None

    # Important :
    # l'index doit être stable pour la sélection.
    gdf = gdf.reset_index(
        drop=True
    )

    # Informations techniques utilisées
    # pour identifier l'entité cliquée.
    gdf["__layer_name"] = (
        layer.name
    )

    gdf["__feature_index"] = (
        range(len(gdf))
    )

    # =====================================================
    # TYPE DE GÉOMÉTRIE
    # =====================================================

    geometry_types = (
        gdf.geometry
        .geom_type
        .dropna()
        .unique()
        .tolist()
    )

    geometry_type = (
        geometry_types[0]
        if geometry_types
        else ""
    )

    # =====================================================
    # STYLE
    # =====================================================

    style = build_style(
        layer,
        geometry_type,
    )

    # =====================================================
    # POPUP / TOOLTIP
    # =====================================================

    popup = build_popup(
        layer,
        gdf,
    )

    tooltip = build_tooltip(
        layer,
        gdf,
    )

    # =====================================================
    # GEOJSON
    # =====================================================

    geojson_options = {
        "data": gdf.to_json(
            drop_id=True,
        ),
        "name": layer.name,
        "style_function": (
            lambda feature, style=style: style
        ),
    }

    if popup is not None:
        geojson_options["popup"] = (
            popup
        )

    if tooltip is not None:
        geojson_options["tooltip"] = (
            tooltip
        )

    folium.GeoJson(
        **geojson_options
    ).add_to(map_object)

    # =====================================================
    # SÉLECTION
    # =====================================================

    add_selection_to_map(
        map_object=map_object,
        layer=layer,
        gdf=gdf,
        selection=selection,
    )

    # =====================================================
    # EMPRISE
    # =====================================================

    minx, miny, maxx, maxy = (
        gdf.total_bounds
    )

    bounds = [
        [miny, minx],
        [maxy, maxx],
    ]

    return bounds