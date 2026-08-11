"""Panneau de résultats des analyses GeoDashboard."""

from __future__ import annotations

import re

import streamlit as st

from services.export_service import ExportService
from services.layer_manager import LayerManager
from services.report_service import ReportService


# =========================================================
# FORMATAGE
# =========================================================

def format_number(
    value: float,
    decimals: int = 2,
) -> str:
    """Formate un nombre au format français."""

    return (
        f"{value:,.{decimals}f}"
        .replace(",", " ")
        .replace(".", ",")
    )


# =========================================================
# DISTANCE
# =========================================================

def get_distance_from_layer_name(
    layer_name: str,
) -> int | None:
    """Extrait une distance comme 500m depuis un nom."""

    if not layer_name:
        return None

    match = re.search(
        r"_buffer_(\d+(?:\.\d+)?)m",
        layer_name,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return int(
            float(
                match.group(1)
            )
        )
    except ValueError:
        return None


# =========================================================
# GÉOMÉTRIES
# =========================================================

def union_geometry(gdf):
    """Fusionne les géométries."""

    try:
        return gdf.geometry.union_all()
    except AttributeError:
        return gdf.geometry.unary_union


def is_point_layer(layer) -> bool:
    """Indique si une couche contient des points."""

    if layer is None:
        return False

    geometry_type = (
        layer.geometry_type
        .lower()
    )

    return (
        "point" in geometry_type
    )


# =========================================================
# SURFACE
# =========================================================

def calculate_surface_km2(
    layer,
) -> float | None:
    """Calcule une surface unique en km²."""

    if layer is None:
        return None

    gdf = (
        layer.geodataframe
        .copy()
    )

    if (
        gdf.empty
        or gdf.crs is None
    ):
        return None

    geometry_types = (
        gdf.geometry
        .geom_type
        .dropna()
        .str.lower()
        .tolist()
    )

    if not any(
        "polygon" in value
        for value in geometry_types
    ):
        return None

    gdf = gdf.to_crs(
        "EPSG:2154"
    )

    geometry = union_geometry(
        gdf
    )

    if (
        geometry is None
        or geometry.is_empty
    ):
        return None

    return float(
        geometry.area
        / 1_000_000
    )


# =========================================================
# LONGUEUR
# =========================================================

def calculate_length_km(
    layer,
) -> float | None:
    """Calcule une longueur totale en km."""

    if layer is None:
        return None

    gdf = (
        layer.geodataframe
        .copy()
    )

    if (
        gdf.empty
        or gdf.crs is None
    ):
        return None

    geometry_types = (
        gdf.geometry
        .geom_type
        .dropna()
        .str.lower()
        .tolist()
    )

    if not any(
        "line" in value
        for value in geometry_types
    ):
        return None

    gdf = gdf.to_crs(
        "EPSG:2154"
    )

    return float(
        gdf.geometry.length.sum()
        / 1000
    )


# =========================================================
# COUVERTURE
# =========================================================

def calculate_coverage_rate(
    coverage_layer,
    manager: LayerManager,
) -> dict | None:
    """
    Calcule la couverture réelle.

    coverage_layer = couche Buffer originale.
    """

    territory_layer = manager.get(
        "territoire_analyse"
    )

    if (
        territory_layer is None
        or coverage_layer is None
    ):
        return None

    territory_gdf = (
        territory_layer.geodataframe
        .copy()
    )

    coverage_gdf = (
        coverage_layer.geodataframe
        .copy()
    )

    if (
        territory_gdf.empty
        or coverage_gdf.empty
        or territory_gdf.crs is None
        or coverage_gdf.crs is None
    ):
        return None

    territory_gdf = (
        territory_gdf.to_crs(
            "EPSG:2154"
        )
    )

    coverage_gdf = (
        coverage_gdf.to_crs(
            "EPSG:2154"
        )
    )

    territory_geometry = (
        union_geometry(
            territory_gdf
        )
    )

    coverage_geometry = (
        union_geometry(
            coverage_gdf
        )
    )

    if (
        territory_geometry is None
        or coverage_geometry is None
        or territory_geometry.is_empty
    ):
        return None

    covered_geometry = (
        territory_geometry.intersection(
            coverage_geometry
        )
    )

    uncovered_geometry = (
        territory_geometry.difference(
            covered_geometry
        )
    )

    territory_area = float(
        territory_geometry.area
        / 1_000_000
    )

    covered_area = float(
        covered_geometry.area
        / 1_000_000
    )

    uncovered_area = float(
        uncovered_geometry.area
        / 1_000_000
    )

    coverage_rate = (
        covered_area
        / territory_area
        * 100
        if territory_area > 0
        else 0.0
    )

    return {
        "territory_area_km2": territory_area,
        "covered_area_km2": covered_area,
        "uncovered_area_km2": uncovered_area,
        "coverage_rate": coverage_rate,
    }


# =========================================================
# RECHERCHE DES COUCHES POUR LE RAPPORT
# =========================================================

def strip_analysis_suffix(
    name: str,
) -> str:
    """Retire les suffixes d'analyse."""

    value = re.sub(
        r"_zone_non_couverte.*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"_zone_couverte.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return value


def find_original_source_layer(
    manager: LayerManager,
    coverage_layer,
):
    """
    Retrouve la couche originale derrière un Buffer.

    Exemple :
    ecole_primaire_buffer_500m
    -> ecole_primaire
    """

    if coverage_layer is None:
        return None

    source_name = coverage_layer.name

    original_name = re.sub(
        r"_buffer_\d+(?:\.\d+)?m.*$",
        "",
        source_name,
        flags=re.IGNORECASE,
    )

    original_layer = manager.get(
        original_name
    )

    if original_layer is not None:
        return original_layer

    return None


def find_point_layer_for_report(
    manager: LayerManager,
    coverage_layer,
):
    """
    Trouve la meilleure couche ponctuelle
    à afficher dans le rapport.
    """

    # 1. Source exacte du buffer
    original_layer = (
        find_original_source_layer(
            manager,
            coverage_layer,
        )
    )

    if is_point_layer(
        original_layer
    ):
        return original_layer

    # 2. Chercher les couches ponctuelles du projet
    point_layers = [
        layer
        for layer in manager.list()
        if is_point_layer(layer)
    ]

    if not point_layers:
        return None

    # Si une seule couche ponctuelle existe,
    # elle est la meilleure candidate.
    if len(point_layers) == 1:
        return point_layers[0]

    # 3. Essayer de faire correspondre le nom
    coverage_name = (
        coverage_layer.name.lower()
        if coverage_layer is not None
        else ""
    )

    scored = []

    for layer in point_layers:

        score = 0

        layer_name = (
            layer.name.lower()
        )

        tokens = [
            token
            for token in re.split(
                r"[_\-\s]+",
                layer_name,
            )
            if len(token) >= 3
        ]

        for token in tokens:
            if token in coverage_name:
                score += 1

        # Priorités métier utiles
        if "ecole" in layer_name:
            score += 1

        if "culture" in layer_name:
            score += 1

        if "equip" in layer_name:
            score += 1

        scored.append(
            (
                score,
                layer,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return scored[0][1]


def find_coverage_result_layer(
    manager: LayerManager,
    coverage_layer,
    kind: str,
):
    """
    Recherche zone_couverte ou zone_non_couverte
    correspondant au Buffer courant.
    """

    if coverage_layer is None:
        return None

    base_name = (
        coverage_layer.name.lower()
    )

    target_suffix = (
        "zone_couverte"
        if kind == "covered"
        else "zone_non_couverte"
    )

    exact_name = (
        f"{coverage_layer.name}_"
        f"{target_suffix}"
    )

    exact = manager.get(
        exact_name
    )

    if exact is not None:
        return exact

    candidates = []

    for layer in manager.list():

        name = (
            layer.name.lower()
        )

        if target_suffix not in name:
            continue

        score = 0

        if base_name in name:
            score += 10

        base_without_analysis = (
            strip_analysis_suffix(
                name
            )
        )

        if (
            base_without_analysis
            == base_name
        ):
            score += 10

        candidates.append(
            (
                score,
                layer,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]


def find_boundary_style_layer(
    manager: LayerManager,
):
    """
    Cherche la couche de commune utilisée
    pour récupérer son style cartographique.
    """

    selected_commune = (
        st.session_state.get(
            "selected_commune",
            ""
        )
    )

    selected_lower = (
        str(selected_commune)
        .lower()
    )

    candidates = []

    for layer in manager.list():

        name = (
            layer.name.lower()
        )

        if layer.name == "territoire_analyse":
            continue

        geometry_type = (
            layer.geometry_type.lower()
        )

        if "polygon" not in geometry_type:
            continue

        score = 0

        if selected_lower and selected_lower in name:
            score += 5

        if "commune" in name:
            score += 3

        if "buffer" in name:
            score -= 5

        if "zone_" in name:
            score -= 5

        candidates.append(
            (
                score,
                layer,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]


# =========================================================
# RAPPORT
# =========================================================

def build_report_info(
    result_info: dict,
    source_layer,
    result_layer,
    buffer_distance: int | None,
) -> dict:
    """Prépare les métadonnées du PDF."""

    report_info = dict(
        result_info
    )

    report_info[
        "territory_name"
    ] = st.session_state.get(
        "selected_commune",
        "Territoire",
    )

    if buffer_distance is not None:
        report_info[
            "distance"
        ] = buffer_distance

    if source_layer is not None:
        report_info[
            "source_feature_count"
        ] = source_layer.feature_count

    report_info[
        "result_layer"
    ] = result_layer.name

    return report_info


def make_safe_filename(
    value: str,
) -> str:
    """Prépare un nom de fichier."""

    safe_value = (
        str(value)
        .strip()
        .lower()
    )

    safe_value = re.sub(
        r"[^a-z0-9_-]+",
        "_",
        safe_value,
    )

    return (
        safe_value.strip("_")
        or "territoire"
    )


# =========================================================
# PANNEAU
# =========================================================

def render_results_panel(
    manager: LayerManager,
) -> None:
    """Affiche le dernier résultat."""

    result_info = st.session_state.get(
        "last_analysis_result"
    )

    if not result_info:
        return

    layer_name = result_info.get(
        "layer_name"
    )

    if not layer_name:
        return

    result_layer = manager.get(
        layer_name
    )

    if result_layer is None:
        return

    operation = result_info.get(
        "operation",
        "Analyse",
    )

    source_name = result_info.get(
        "source_layer",
        "",
    )

    source_layer = manager.get(
        source_name
    )

    territory_layer = manager.get(
        "territoire_analyse"
    )

    # =====================================================
    # COUCHE DE COUVERTURE
    # =====================================================

    if (
        operation == "Coverage"
        and source_layer is not None
    ):
        coverage_layer = source_layer
    else:
        coverage_layer = result_layer

    # =====================================================
    # CALCULS
    # =====================================================

    surface_km2 = (
        calculate_surface_km2(
            result_layer
        )
    )

    length_km = (
        calculate_length_km(
            result_layer
        )
    )

    buffer_distance = (
        get_distance_from_layer_name(
            source_name
        )
    )

    if buffer_distance is None:
        buffer_distance = (
            get_distance_from_layer_name(
                result_layer.name
            )
        )

    coverage = (
        calculate_coverage_rate(
            coverage_layer,
            manager,
        )
    )

    source_count = (
        source_layer.feature_count
        if source_layer is not None
        else None
    )

    # =====================================================
    # TITRE
    # =====================================================

    st.divider()

    st.subheader(
        "Résultat de l'analyse"
    )

    st.caption(
        f"{operation} · "
        f"Couche source : {source_name}"
    )

    # =====================================================
    # INDICATEURS
    # =====================================================

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Entités résultat",
            f"{result_layer.feature_count:,}"
            .replace(",", " "),
        )

    with col2:

        if source_count is not None:
            st.metric(
                "Entités source",
                f"{source_count:,}"
                .replace(",", " "),
            )
        else:
            st.metric(
                "Géométrie",
                result_layer.geometry_type,
            )

    with col3:

        if surface_km2 is not None:
            st.metric(
                (
                    "Surface totale des buffers"
                    if operation == "Buffer"
                    else "Surface du résultat"
                ),
                (
                    f"{format_number(surface_km2)} "
                    f"km²"
                ),
            )

        elif length_km is not None:
            st.metric(
                "Longueur totale",
                (
                    f"{format_number(length_km)} "
                    f"km"
                ),
            )

        else:
            st.metric(
                "Géométrie",
                result_layer.geometry_type,
            )

    with col4:

        if buffer_distance is not None:
            st.metric(
                "Distance",
                f"{buffer_distance} m",
            )
        else:
            st.metric(
                "CRS",
                result_layer.crs,
            )

    # =====================================================
    # COUVERTURE
    # =====================================================

    if coverage is not None:

        st.write("")

        st.markdown(
            "### Couverture territoriale"
        )

        selected_commune = (
            st.session_state.get(
                "selected_commune",
                "Territoire sélectionné",
            )
        )

        st.caption(
            "Couverture calculée uniquement "
            f"à l'intérieur de {selected_commune}."
        )

        c1, c2, c3, c4 = (
            st.columns(4)
        )

        with c1:
            st.metric(
                "Surface du territoire",
                (
                    f"{format_number(
                        coverage['territory_area_km2']
                    )} km²"
                ),
            )

        with c2:
            st.metric(
                "Surface couverte",
                (
                    f"{format_number(
                        coverage['covered_area_km2']
                    )} km²"
                ),
            )

        with c3:
            st.metric(
                "Surface non couverte",
                (
                    f"{format_number(
                        coverage['uncovered_area_km2']
                    )} km²"
                ),
            )

        with c4:
            st.metric(
                "Taux de couverture",
                (
                    f"{format_number(
                        coverage['coverage_rate'],
                        1,
                    )} %"
                ),
            )

    st.write("")

    # =====================================================
    # RÉSULTAT
    # =====================================================

    with st.container(
        border=True
    ):

        st.markdown(
            f"### {result_layer.name}"
        )

        st.caption(
            "Cette couche correspond au dernier "
            "résultat produit par GeoDashboard."
        )

        action_col1, action_col2 = (
            st.columns(2)
        )

        with action_col1:

            if st.button(
                "📊 Voir la table attributaire",
                use_container_width=True,
                key="result_open_table",
            ):
                st.session_state[
                    "selected_layer"
                ] = result_layer

                st.rerun()

        with action_col2:

            if st.button(
                "🗺️ Mettre en avant sur la carte",
                use_container_width=True,
                key="result_focus_map",
            ):

                for layer in manager.list():
                    layer.visible = (
                        layer.name
                        == result_layer.name
                    )

                st.session_state.pop(
                    "map_layers_signature",
                    None,
                )

                st.session_state[
                    "map_instance"
                ] = (
                    st.session_state.get(
                        "map_instance",
                        0,
                    )
                    + 1
                )

                st.rerun()

        st.divider()

        # =================================================
        # EXPORT
        # =================================================

        st.markdown(
            "#### Exporter le résultat"
        )

        try:

            gpkg_data = (
                ExportService.to_geopackage(
                    result_layer
                )
            )

            geojson_data = (
                ExportService.to_geojson(
                    result_layer
                )
            )

            export_col1, export_col2 = (
                st.columns(2)
            )

            with export_col1:
                st.download_button(
                    "GeoPackage (.gpkg)",
                    data=gpkg_data,
                    file_name=(
                        f"{result_layer.name}.gpkg"
                    ),
                    mime=(
                        "application/"
                        "geopackage+sqlite3"
                    ),
                    use_container_width=True,
                    key="result_export_gpkg",
                )

            with export_col2:
                st.download_button(
                    "GeoJSON (.geojson)",
                    data=geojson_data,
                    file_name=(
                        f"{result_layer.name}.geojson"
                    ),
                    mime="application/geo+json",
                    use_container_width=True,
                    key="result_export_geojson",
                )

        except Exception as error:

            st.warning(
                "L'export SIG n'est pas disponible."
            )

            st.caption(
                str(error)
            )

        # =================================================
        # RAPPORT
        # =================================================

        st.divider()

        st.markdown(
            "#### Rapport d'analyse"
        )

        if territory_layer is None:

            st.info(
                "Sélectionne un territoire "
                "pour générer le PDF."
            )

            return

        try:

            report_info = (
                build_report_info(
                    result_info=result_info,
                    source_layer=source_layer,
                    result_layer=result_layer,
                    buffer_distance=buffer_distance,
                )
            )

            equipment_layer = (
                find_point_layer_for_report(
                    manager,
                    coverage_layer,
                )
            )

            covered_style_layer = (
                find_coverage_result_layer(
                    manager,
                    coverage_layer,
                    "covered",
                )
            )

            uncovered_style_layer = (
                find_coverage_result_layer(
                    manager,
                    coverage_layer,
                    "uncovered",
                )
            )

            boundary_style_layer = (
                find_boundary_style_layer(
                    manager
                )
            )

            pdf_data = (
                ReportService
                .generate_analysis_report(
                    territory_layer=territory_layer,
                    result_layer=result_layer,
                    result_info=report_info,
                    coverage_layer=coverage_layer,
                    equipment_layer=equipment_layer,
                    covered_style_layer=(
                        covered_style_layer
                    ),
                    uncovered_style_layer=(
                        uncovered_style_layer
                    ),
                    boundary_style_layer=(
                        boundary_style_layer
                    ),
                )
            )

            commune_name = (
                st.session_state.get(
                    "selected_commune",
                    "territoire",
                )
            )

            safe_commune = (
                make_safe_filename(
                    commune_name
                )
            )

            st.download_button(
                "📄 Générer le rapport PDF",
                data=pdf_data,
                file_name=(
                    f"rapport_geodashboard_"
                    f"{safe_commune}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
                key="result_export_pdf",
            )

            if equipment_layer is not None:
                st.caption(
                    "Couche d'équipements utilisée "
                    f"dans le rapport : "
                    f"{equipment_layer.name}"
                )

        except Exception as error:

            st.warning(
                "Le rapport PDF n'a pas "
                "pu être généré."
            )

            st.caption(
                str(error)
            )