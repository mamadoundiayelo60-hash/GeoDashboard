"""Moteur de rendu cartographique de GeoDashboard."""

from __future__ import annotations

import folium
import geopandas as gpd
import pandas as pd

from models.layer import Layer


def prepare_for_folium(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Prépare une couche pour Leaflet/Folium."""

    data = gdf.copy()

    if data.crs is not None:
        data = data.to_crs("EPSG:4326")

    data = data[
        data.geometry.notna()
    ].copy()

    geometry_column = data.geometry.name

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
    """Choisit des champs pertinents par défaut."""

    columns = [
        column
        for column in gdf.columns
        if column != gdf.geometry.name
    ]

    preferred = [
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

    ignored = {
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
    }

    selected: list[str] = []

    for wanted in preferred:
        for column in columns:
            if (
                column.lower() == wanted.lower()
                and column not in selected
            ):
                selected.append(column)

    for column in columns:
        if column.lower() in ignored:
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
    """Construit le style Folium à partir du style de la couche."""

    geometry_type = geometry_type.lower()

    style = {
        "color": layer.style["color"],
        "weight": layer.style["weight"],
        "opacity": layer.style["opacity"],
    }

    if "polygon" in geometry_type:
        style["fillColor"] = layer.style["color"]
        style["fillOpacity"] = layer.style[
            "fillOpacity"
        ]

    return style


def build_popup(
    layer: Layer,
    gdf: gpd.GeoDataFrame,
):
    """Crée la popup de la couche."""

    default_fields = choose_display_fields(gdf)

    fields = (
        layer.popup_fields
        if layer.popup_fields
        else default_fields
    )

    fields = [
        field
        for field in fields
        if field in gdf.columns
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
    """Crée le tooltip de la couche."""

    default_fields = choose_display_fields(gdf)

    fields = (
        layer.tooltip_fields
        if layer.tooltip_fields
        else default_fields[:3]
    )

    fields = [
        field
        for field in fields
        if field in gdf.columns
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


def add_layer_to_map(
    map_object: folium.Map,
    layer: Layer,
) -> list[list[float]] | None:
    """
    Ajoute une couche à la carte.

    Retourne l'emprise Leaflet :
    [[min_lat, min_lon], [max_lat, max_lon]]
    """

    if not layer.visible:
        return None

    gdf = prepare_for_folium(
        layer.geodataframe
    )

    if gdf.empty:
        return None

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

    style = build_style(
        layer,
        geometry_type,
    )

    popup = build_popup(
        layer,
        gdf,
    )

    tooltip = build_tooltip(
        layer,
        gdf,
    )

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
        geojson_options["popup"] = popup

    if tooltip is not None:
        geojson_options["tooltip"] = tooltip

    folium.GeoJson(
        **geojson_options
    ).add_to(map_object)

    minx, miny, maxx, maxy = (
        gdf.total_bounds
    )

    return [
        [miny, minx],
        [maxy, maxx],
    ]