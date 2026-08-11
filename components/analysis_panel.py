"""Panneau central des analyses spatiales de GeoDashboard."""

from __future__ import annotations

import streamlit as st

from services.analysis.analysis_service import AnalysisService
from services.layer_manager import LayerManager


# =========================================================
# LIBELLÉS DES OUTILS
# =========================================================

OPERATION_LABELS = {
    "Buffer": "Zone tampon (Buffer)",
    "Intersection": "Intersection",
    "SpatialSelection": "Sélection par localisation",
    "Coverage": "Couverture territoriale",
}


# =========================================================
# PANNEAU BUFFER
# =========================================================

def render_buffer_parameters(
    source_name: str,
) -> dict:
    """Affiche les paramètres de l'outil Buffer."""

    st.markdown(
        "#### Paramètres"
    )

    col1, col2 = st.columns(
        [1.5, 1],
    )

    with col1:

        distance = st.number_input(
            "Distance",
            min_value=0.1,
            value=500.0,
            step=50.0,
            key="analysis_buffer_distance",
        )

    with col2:

        unit = st.selectbox(
            "Unité",
            options=[
                "mètres",
            ],
            key="analysis_buffer_unit",
        )

    distance_text = (
        int(distance)
        if float(distance).is_integer()
        else distance
    )

    default_name = (
        f"{source_name}_buffer_"
        f"{distance_text}m"
    )

    result_name = st.text_input(
        "Nom de la couche résultat",
        value=default_name,
        key="analysis_buffer_result_name",
    )

    st.caption(
        "La zone tampon est calculée en mètres. "
        "Si la couche utilise un CRS géographique, "
        "GeoDashboard la reprojette avant le calcul."
    )

    return {
        "distance": distance,
        "unit": unit,
        "result_name": result_name.strip(),
    }


# =========================================================
# PANNEAU INTERSECTION
# =========================================================

def render_intersection_parameters(
    manager: LayerManager,
    source_name: str,
) -> dict | None:
    """Affiche les paramètres de l'outil Intersection."""

    st.markdown(
        "#### Paramètres"
    )

    layer_names = [
        layer.name
        for layer in manager.list()
        if layer.name != source_name
    ]

    if not layer_names:

        st.warning(
            "L'intersection nécessite au moins "
            "deux couches dans le projet."
        )

        return None

    overlay_name = st.selectbox(
        "Couche d'intersection",
        options=layer_names,
        key="analysis_intersection_overlay",
    )

    overlay_layer = manager.get(
        overlay_name
    )

    default_name = (
        f"{source_name}_intersection_"
        f"{overlay_name}"
    )

    result_name = st.text_input(
        "Nom de la couche résultat",
        value=default_name,
        key="analysis_intersection_result_name",
    )

    if overlay_layer is not None:

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.metric(
                "Entités couche 2",
                (
                    f"{overlay_layer.feature_count:,}"
                    .replace(",", " ")
                ),
            )

        with col2:

            st.metric(
                "Géométrie couche 2",
                overlay_layer.geometry_type,
            )

        with col3:

            st.metric(
                "CRS couche 2",
                overlay_layer.crs,
            )

    st.caption(
        "L'intersection conserve uniquement "
        "les parties géométriques communes "
        "aux deux couches."
    )

    return {
        "overlay_layer": overlay_layer,
        "result_name": result_name.strip(),
    }


# =========================================================
# PANNEAU SÉLECTION PAR LOCALISATION
# =========================================================

def render_spatial_selection_parameters(
    manager: LayerManager,
    source_name: str,
) -> dict | None:
    """Affiche les paramètres de la sélection spatiale."""

    st.markdown(
        "#### Paramètres"
    )

    reference_names = [
        layer.name
        for layer in manager.list()
        if layer.name != source_name
    ]

    if not reference_names:

        st.warning(
            "Ajoute au moins une deuxième couche "
            "pour effectuer une sélection spatiale."
        )

        return None

    reference_name = st.selectbox(
        "Couche de référence",
        options=reference_names,
        key="spatial_selection_reference",
    )

    predicate_labels = {
        "intersects": "Intersecte",
        "within": "Est à l'intérieur",
        "contains": "Contient",
        "touches": "Touche",
        "crosses": "Traverse",
        "overlaps": "Chevauche",
    }

    predicate = st.selectbox(
        "Relation spatiale",
        options=list(
            predicate_labels.keys()
        ),
        format_func=lambda value: (
            predicate_labels[value]
        ),
        key="spatial_selection_predicate",
    )

    default_name = (
        f"{source_name}_selection_"
        f"{reference_name}"
    )

    result_name = st.text_input(
        "Nom de la couche résultat",
        value=default_name,
        key="spatial_selection_result_name",
    )

    reference_layer = manager.get(
        reference_name
    )

    if reference_layer is not None:

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.metric(
                "Entités couche 2",
                (
                    f"{reference_layer.feature_count:,}"
                    .replace(",", " ")
                ),
            )

        with col2:

            st.metric(
                "Géométrie couche 2",
                reference_layer.geometry_type,
            )

        with col3:

            st.metric(
                "CRS couche 2",
                reference_layer.crs,
            )

    st.caption(
        "La sélection conserve les entités complètes "
        "de la couche source qui respectent "
        "la relation spatiale choisie."
    )

    return {
        "reference_layer": reference_layer,
        "predicate": predicate,
        "result_name": result_name.strip(),
    }


# =========================================================
# PANNEAU COUVERTURE TERRITORIALE
# =========================================================

def render_coverage_parameters(
    manager: LayerManager,
    source_name: str,
) -> dict | None:
    """
    Affiche les paramètres de l'analyse
    de couverture territoriale.
    """

    st.markdown(
        "#### Paramètres"
    )

    territory_layer = manager.get(
        "territoire_analyse"
    )

    if territory_layer is None:

        st.warning(
            "Aucun territoire d'analyse actif. "
            "Sélectionne d'abord une commune "
            "dans la partie « Territoire d'analyse »."
        )

        return None

    source_layer = manager.get(
        source_name
    )

    if source_layer is None:
        return None

    # -----------------------------------------------------
    # VÉRIFIER QUE LA COUCHE SOURCE EST SURFACIQUE
    # -----------------------------------------------------

    geometry_text = (
        source_layer.geometry_type
        .lower()
    )

    if "polygon" not in geometry_text:

        st.warning(
            "La couverture territoriale nécessite "
            "une couche surfacique comme un Buffer."
        )

        st.caption(
            "Exemple : crée d'abord un Buffer de 500 m "
            "autour des écoles, puis utilise cette couche "
            "comme source."
        )

        return None

    # -----------------------------------------------------
    # MODE
    # -----------------------------------------------------

    mode_labels = {
        "covered": "Zone couverte",
        "uncovered": "Zone non couverte",
    }

    mode = st.selectbox(
        "Résultat à produire",
        options=list(
            mode_labels.keys()
        ),
        format_func=lambda value: (
            mode_labels[value]
        ),
        key="analysis_coverage_mode",
    )

    # -----------------------------------------------------
    # NOM DU RÉSULTAT
    # -----------------------------------------------------

    suffix = (
        "zone_couverte"
        if mode == "covered"
        else "zone_non_couverte"
    )

    default_name = (
        f"{source_name}_"
        f"{suffix}"
    )

    result_name = st.text_input(
        "Nom de la couche résultat",
        value=default_name,
        key=(
            f"analysis_coverage_result_name_"
            f"{mode}"
        ),
    )

    # -----------------------------------------------------
    # INFORMATIONS TERRITOIRE
    # -----------------------------------------------------

    selected_commune = (
        st.session_state.get(
            "selected_commune",
            "Territoire sélectionné",
        )
    )

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        st.metric(
            "Territoire",
            selected_commune,
        )

    with col2:

        st.metric(
            "Entités territoire",
            (
                f"{territory_layer.feature_count:,}"
                .replace(",", " ")
            ),
        )

    with col3:

        st.metric(
            "CRS territoire",
            territory_layer.crs,
        )

    st.caption(
        "GeoDashboard découpe la couche de couverture "
        "selon la limite exacte du territoire sélectionné."
    )

    return {
        "territory_layer": territory_layer,
        "mode": mode,
        "result_name": result_name.strip(),
    }


# =========================================================
# EXÉCUTION
# =========================================================

def execute_analysis(
    manager: LayerManager,
    analysis_service: AnalysisService,
    operation_name: str,
    source_name: str,
    parameters: dict,
) -> None:
    """Exécute l'analyse et ajoute son résultat au projet."""

    source_layer = manager.get(
        source_name
    )

    if source_layer is None:

        st.error(
            "La couche source est introuvable."
        )

        return

    result_name = parameters.get(
        "result_name",
        "",
    )

    if not result_name:

        st.error(
            "Le nom de la couche résultat "
            "est obligatoire."
        )

        return

    if manager.get(
        result_name
    ) is not None:

        st.error(
            f"Une couche nommée « {result_name} » "
            "existe déjà."
        )

        return

    try:

        with st.spinner(
            f"Exécution de {operation_name}..."
        ):

            result_layer = (
                analysis_service.run(
                    operation_name=operation_name,
                    layer=source_layer,
                    **parameters,
                )
            )

            manager.add(
                result_layer
            )

        # =================================================
        # MÉMORISER LE DERNIER RÉSULTAT
        # =================================================

        st.session_state[
            "last_analysis_result"
        ] = {
            "layer_name": (
                result_layer.name
            ),
            "operation": (
                operation_name
            ),
            "source_layer": (
                source_name
            ),
            "feature_count": (
                result_layer.feature_count
            ),
            "geometry_type": (
                result_layer.geometry_type
            ),
            "crs": str(
                result_layer.crs
            ),
        }

        st.session_state[
            "analysis_result_layer"
        ] = result_layer.name

        # -------------------------------------------------
        # MÉMORISER LE TYPE DE COUVERTURE
        # -------------------------------------------------

        if operation_name == "Coverage":

            st.session_state[
                "last_coverage_mode"
            ] = parameters.get(
                "mode"
            )

        st.success(
            f"Analyse terminée — "
            f"« {result_layer.name} » "
            f"a été ajoutée au projet."
        )

        st.rerun()

    except Exception as error:

        st.error(
            "L'analyse spatiale n'a pas "
            "pu être exécutée."
        )

        st.exception(
            error
        )


# =========================================================
# INTERFACE PRINCIPALE
# =========================================================

def render_analysis_panel(
    manager: LayerManager,
    analysis_service: AnalysisService,
) -> None:
    """Affiche le centre d'analyses spatiales."""

    st.subheader(
        "Analyses spatiales"
    )

    st.caption(
        "Applique des traitements géographiques "
        "aux couches du projet."
    )

    layers = manager.list()

    # =====================================================
    # AUCUNE COUCHE
    # =====================================================

    if not layers:

        st.info(
            "Importe au moins une couche "
            "pour utiliser les outils d'analyse."
        )

        return

    # =====================================================
    # OUTILS DISPONIBLES
    # =====================================================

    operations = (
        analysis_service
        .available_operations()
    )

    if not operations:

        st.warning(
            "Aucun outil d'analyse "
            "n'est actuellement disponible."
        )

        return

    # =====================================================
    # CHOIX DE L'OUTIL
    # =====================================================

    operation_name = st.selectbox(
        "Type d'analyse",
        options=operations,
        format_func=lambda name: (
            OPERATION_LABELS.get(
                name,
                name,
            )
        ),
        key="analysis_operation",
    )

    operation = (
        analysis_service
        .registry
        .get(
            operation_name
        )
    )

    st.info(
        operation.description
    )

    # =====================================================
    # COUCHES SOURCE DISPONIBLES
    # =====================================================

    if operation_name == "Coverage":

        # Coverage utilise une couche polygonale
        # différente de territoire_analyse.
        source_layers = [
            layer
            for layer in layers
            if (
                layer.name
                != "territoire_analyse"
                and "polygon"
                in layer.geometry_type.lower()
            )
        ]

        if not source_layers:

            st.warning(
                "Aucune couche surfacique disponible "
                "pour calculer la couverture."
            )

            st.caption(
                "Crée d'abord une zone tampon "
                "autour d'une couche de points."
            )

            return

    else:

        source_layers = [
            layer
            for layer in layers
            if layer.name
            != "territoire_analyse"
        ]

    layer_names = [
        layer.name
        for layer in source_layers
    ]

    if not layer_names:
        return

    # =====================================================
    # COUCHE SOURCE
    # =====================================================

    source_name = st.selectbox(
        "Couche source",
        options=layer_names,
        key=(
            f"analysis_source_layer_"
            f"{operation_name}"
        ),
    )

    source_layer = manager.get(
        source_name
    )

    # =====================================================
    # INFORMATIONS SUR LA COUCHE
    # =====================================================

    if source_layer is not None:

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.metric(
                "Entités",
                (
                    f"{source_layer.feature_count:,}"
                    .replace(",", " ")
                ),
            )

        with col2:

            st.metric(
                "Géométrie",
                source_layer.geometry_type,
            )

        with col3:

            st.metric(
                "CRS",
                source_layer.crs,
            )

    st.divider()

    # =====================================================
    # PARAMÈTRES DYNAMIQUES
    # =====================================================

    parameters: dict | None = None

    if operation_name == "Buffer":

        parameters = (
            render_buffer_parameters(
                source_name
            )
        )

    elif operation_name == "Intersection":

        parameters = (
            render_intersection_parameters(
                manager=manager,
                source_name=source_name,
            )
        )

    elif operation_name == "SpatialSelection":

        parameters = (
            render_spatial_selection_parameters(
                manager=manager,
                source_name=source_name,
            )
        )

    elif operation_name == "Coverage":

        parameters = (
            render_coverage_parameters(
                manager=manager,
                source_name=source_name,
            )
        )

    else:

        st.warning(
            "L'interface de cet outil "
            "n'est pas encore disponible."
        )

        return

    if parameters is None:
        return

    # =====================================================
    # EXÉCUTER
    # =====================================================

    st.write("")

    execute = st.button(
        "▶ Exécuter l'analyse",
        type="primary",
        use_container_width=True,
        key=(
            f"execute_spatial_analysis_"
            f"{operation_name}"
        ),
    )

    if execute:

        execute_analysis(
            manager=manager,
            analysis_service=analysis_service,
            operation_name=operation_name,
            source_name=source_name,
            parameters=parameters,
        )