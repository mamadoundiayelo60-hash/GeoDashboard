"""Moteur de rendu cartographique de GeoDashboard."""

from __future__ import annotations

import folium
import geopandas as gpd
import pandas as pd

from models.layer import Layer
from models.selection import Selection


# =========================================================
# PARAMÈTRES DE PERFORMANCE
# =========================================================

MAX_FEATURES_FOR_MAP = 12000

ZOOM_FULL_DETAIL = 15


# =========================================================
# PRÉPARATION FOLIUM
# =========================================================

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

    if data.crs is not None:
        data = data.to_crs(
            "EPSG:4326"
        )

    data = data[
    data.geometry.notna()
    & ~data.geometry.is_empty
    ].copy()

    geometry_column = (
        data.geometry.name
    )

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

            data[column] = (
                data[column].apply(
                    lambda value: (
                        value.isoformat()
                        if isinstance(
                            value,
                            pd.Timestamp,
                        )
                        else value
                    )
                )
            )

    return data


# =========================================================
# CHAMPS À AFFICHER
# =========================================================

def choose_display_fields(
    gdf: gpd.GeoDataFrame,
) -> list[str]:
    """
    Choisit automatiquement les champs
    les plus parlants.
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
        "__layer_name",
        "__feature_index",
    }

    selected: list[str] = []

    for preferred in preferred_fields:

        for column in columns:

            if (
                column.lower()
                == preferred.lower()
                and column not in selected
            ):
                selected.append(
                    column
                )

    for column in columns:

        if (
            column.lower()
            in ignored_fields
        ):
            continue

        if column not in selected:
            selected.append(
                column
            )

        if len(selected) >= 6:
            break

    return selected[:6]


# =========================================================
# STYLE
# =========================================================

def build_style(
    layer: Layer,
    geometry_type: str,
) -> dict:
    """
    Construit le style Folium à partir
    des paramètres de la couche.

    Le style défini dans Layer reste
    prioritaire afin que les résultats
    d'analyse puissent être clairement
    mis en évidence.
    """

    geometry_type = geometry_type.lower()

    color = layer.style.get(
        "color",
        "#2563EB",
    )

    style = {
        "color": color,
        "weight": layer.style.get(
            "weight",
            3,
        ),
        "opacity": layer.style.get(
            "opacity",
            0.85,
        ),
    }

    # =============================================
    # LIGNES
    # =============================================

    if "line" in geometry_type:

        style["weight"] = layer.style.get(
            "weight",
            2,
        )

        style["opacity"] = layer.style.get(
            "opacity",
            0.75,
        )

    # =============================================
    # POLYGONES
    # =============================================

    elif "polygon" in geometry_type:

        style["weight"] = layer.style.get(
            "weight",
            2,
        )

        style["fillColor"] = layer.style.get(
            "fillColor",
            color,
        )

        style["fillOpacity"] = layer.style.get(
            "fillOpacity",
            0.20,
        )

    return style

    # =============================================
    # LIGNES : routes, réseaux, etc.
    # =============================================

    if "line" in geometry_type:

        style["weight"] = min(
            style["weight"],
            1.5,
        )

        style["opacity"] = min(
            style["opacity"],
            0.60,
        )

    # =============================================
    # POLYGONES : bâtiments, parcelles, etc.
    # =============================================

    elif "polygon" in geometry_type:

        style["weight"] = min(
            style["weight"],
            1.5,
        )

        style["fillColor"] = color

        style["fillOpacity"] = min(
            layer.style.get(
                "fillOpacity",
                0.20,
            ),
            0.10,
        )

    return style

# =========================================================
# POPUP
# =========================================================

def build_popup(
    layer: Layer,
    gdf: gpd.GeoDataFrame,
):
    """Construit la popup au clic."""

    default_fields = (
        choose_display_fields(
            gdf
        )
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
            and not field.startswith(
                "__"
            )
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


# =========================================================
# TOOLTIP
# =========================================================

def build_tooltip(
    layer: Layer,
    gdf: gpd.GeoDataFrame,
):
    """Construit le tooltip au survol."""

    default_fields = (
        choose_display_fields(
            gdf
        )
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
            and not field.startswith(
                "__"
            )
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


# =========================================================
# FILTRAGE PAR EMPRISE
# =========================================================

def filter_by_view_bounds(
    gdf: gpd.GeoDataFrame,
    view_bounds,
) -> gpd.GeoDataFrame:
    """
    Filtre les entités selon l'emprise
    actuellement visible dans Leaflet.
    """

    if view_bounds is None:
        return gdf

    try:

        south_west = (
            view_bounds.get(
                "_southWest"
            )
        )

        north_east = (
            view_bounds.get(
                "_northEast"
            )
        )

        if (
            south_west is None
            or north_east is None
        ):
            return gdf

        min_lat = float(
            south_west["lat"]
        )

        min_lon = float(
            south_west["lng"]
        )

        max_lat = float(
            north_east["lat"]
        )

        max_lon = float(
            north_east["lng"]
        )

        visible = gdf.cx[
            min_lon:max_lon,
            min_lat:max_lat,
        ]

        if visible.empty:
            return gdf.iloc[
                0:0
            ].copy()

        return visible.copy()

    except (
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
    ):
        return gdf


# =========================================================
# LIMITATION DES GROSSES COUCHES
# =========================================================

def limit_features(
    gdf: gpd.GeoDataFrame,
    zoom: int | None,
) -> gpd.GeoDataFrame:
    """
    Limite le nombre d'entités à petite
    échelle mais conserve tous les objets
    lorsque l'utilisateur est suffisamment
    zoomé.
    """

    if len(gdf) <= MAX_FEATURES_FOR_MAP:
        return gdf

    # À fort zoom, conserver toutes
    # les entités visibles.
    if (
        zoom is not None
        and zoom >= ZOOM_FULL_DETAIL
    ):
        return gdf

    step = max(
        1,
        len(gdf)
        // MAX_FEATURES_FOR_MAP,
    )

    limited = (
        gdf.iloc[::step]
        .copy()
    )

    # Sécurité supplémentaire.
    if (
        len(limited)
        > MAX_FEATURES_FOR_MAP
    ):
        limited = (
            limited.iloc[
                :MAX_FEATURES_FOR_MAP
            ]
            .copy()
        )

    return limited


# =========================================================
# SÉLECTION
# =========================================================

def add_selection_to_map(
    map_object: folium.Map,
    layer: Layer,
    original_gdf: gpd.GeoDataFrame,
    selection: Selection | None,
) -> None:
    """
    Met en surbrillance l'entité
    sélectionnée.

    IMPORTANT :
    on utilise l'index technique stable
    et non la position actuelle dans le
    GeoDataFrame filtré.
    """

    if selection is None:
        return

    if (
        selection.layer_name
        != layer.name
    ):
        return

    if (
        "__feature_index"
        not in original_gdf.columns
    ):
        return

    selected_gdf = (
        original_gdf[
            original_gdf[
                "__feature_index"
            ]
            == selection.feature_index
        ]
        .copy()
    )

    if selected_gdf.empty:
        return

    folium.GeoJson(
        data=selected_gdf.to_json(
            drop_id=True,
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
    ).add_to(
        map_object
    )


# =========================================================
# AJOUT DE COUCHE
# =========================================================

def add_layer_to_map(
    map_object: folium.Map,
    layer: Layer,
    selection: Selection | None = None,
    view_bounds=None,
    zoom: int | None = None,
) -> list[list[float]] | None:
    """
    Ajoute une couche à la carte.

    La couche originale reste intacte.
    Le rendu peut être filtré ou limité
    pour améliorer les performances.
    """

    if not layer.visible:
        return None

    # =====================================================
    # SOURCE D'AFFICHAGE
    # =====================================================

    source_gdf = (
        layer.display_geodataframe
        if (
            layer.display_geodataframe
            is not None
        )
        else layer.geodataframe
    )

    gdf = prepare_for_folium(
        source_gdf
    )

    if gdf.empty:
        return None

    # =====================================================
    # INDEX STABLE
    # =====================================================

    gdf = gdf.reset_index(
        drop=True
    )

    gdf["__layer_name"] = (
        layer.name
    )

    gdf["__feature_index"] = (
        range(len(gdf))
    )

    # Cette version complète sert à
    # retrouver correctement la sélection.
    full_display_gdf = (
        gdf.copy()
    )

    # =====================================================
    # EMPRISE GLOBALE AVANT FILTRAGE
    # =====================================================

    minx, miny, maxx, maxy = (
        full_display_gdf.total_bounds
    )

    layer_bounds = [
        [miny, minx],
        [maxy, maxx],
    ]

    # =====================================================
    # FILTRAGE PAR ZONE VISIBLE
    # =====================================================

    if (
        view_bounds is not None
        and len(gdf)
        > MAX_FEATURES_FOR_MAP
    ):

        filtered_gdf = (
            filter_by_view_bounds(
                gdf,
                view_bounds,
            )
        )

        if not filtered_gdf.empty:
            gdf = filtered_gdf

    # =====================================================
    # LIMITATION SELON LE ZOOM
    # =====================================================

    gdf = limit_features(
        gdf,
        zoom,
    )

    if gdf.empty:
        return layer_bounds

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
            lambda feature,
            style=style: style
        ),
    }

    if popup is not None:
        geojson_options[
            "popup"
        ] = popup

    if tooltip is not None:
        geojson_options[
            "tooltip"
        ] = tooltip

    folium.GeoJson(
        **geojson_options
    ).add_to(
        map_object
    )

    # =====================================================
    # SÉLECTION
    # =====================================================

    add_selection_to_map(
        map_object=map_object,
        layer=layer,
        original_gdf=full_display_gdf,
        selection=selection,
    )

    return layer_bounds