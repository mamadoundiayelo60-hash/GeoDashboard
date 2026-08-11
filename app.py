"""Application principale de GeoDashboard."""

from __future__ import annotations

import streamlit as st

from components.analysis_panel import render_analysis_panel
from components.attribute_table import render_attribute_table
from components.header import render_header
from components.import_panel import render_import_panel
from components.layer_panel import render_layer_panel
from components.map_panel import render_map_panel
from components.results_panel import render_results_panel
from components.theme import load_theme
from components.toolbar import render_toolbar

from services.analysis.analysis_service import AnalysisService
from services.layer_manager import LayerManager
from services.selection_manager import SelectionManager


# =========================================================
# CONFIGURATION STREAMLIT
# =========================================================

st.set_page_config(
    page_title="GeoDashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# THÈME VISUEL
# =========================================================

st.markdown(
    load_theme(),
    unsafe_allow_html=True,
)


# =========================================================
# SERVICES CONSERVÉS EN SESSION
# =========================================================

def get_layer_manager() -> LayerManager:
    """Retourne le gestionnaire de couches."""

    if "layer_manager" not in st.session_state:

        st.session_state.layer_manager = (
            LayerManager()
        )

    return st.session_state.layer_manager


def get_selection_manager() -> SelectionManager:
    """Retourne le gestionnaire de sélection."""

    if "selection_manager" not in st.session_state:

        st.session_state.selection_manager = (
            SelectionManager()
        )

    return st.session_state.selection_manager


def get_analysis_service() -> AnalysisService:
    """Retourne le moteur d'analyse."""

    if "analysis_service" not in st.session_state:

        st.session_state.analysis_service = (
            AnalysisService()
        )

    return st.session_state.analysis_service


# =========================================================
# INITIALISATION
# =========================================================

manager = get_layer_manager()

selection_manager = (
    get_selection_manager()
)

analysis_service = (
    get_analysis_service()
)


# =========================================================
# EN-TÊTE
# =========================================================

render_header()


# =========================================================
# TERRITOIRE D'ANALYSE
# =========================================================

parameters = render_toolbar(
    manager
)

selected_commune = (
    parameters.get(
        "commune"
    )
)

territory_layer = (
    parameters.get(
        "territory_layer"
    )
)


# =========================================================
# ZONE PRINCIPALE
# =========================================================

left_column, right_column = (
    st.columns(
        [1.05, 2.2],
        gap="large",
    )
)


# =========================================================
# COLONNE GAUCHE
# =========================================================

with left_column:

    render_import_panel(
        manager
    )

    render_layer_panel(
        manager
    )


# =========================================================
# COLONNE DROITE
# =========================================================

with right_column:

    render_map_panel(
        manager=manager,
        selection_manager=selection_manager,
        commune=(
            selected_commune
            or "Aucun territoire"
        ),
        theme="Analyse spatiale",
        distance=0,
    )


# =========================================================
# ANALYSES SPATIALES
# =========================================================

st.divider()

render_analysis_panel(
    manager=manager,
    analysis_service=analysis_service,
)


# =========================================================
# RÉSULTATS
# =========================================================

render_results_panel(
    manager
)


# =========================================================
# TABLE ATTRIBUTAIRE
# =========================================================

selected_layer = (
    st.session_state.get(
        "selected_layer"
    )
)

if selected_layer is not None:

    st.divider()

    render_attribute_table(
        layer=selected_layer,
        selection_manager=selection_manager,
    )