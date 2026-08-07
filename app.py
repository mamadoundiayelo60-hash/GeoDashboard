from __future__ import annotations

import streamlit as st

from components.attribute_table import render_attribute_table
from components.header import render_header
from components.import_panel import render_import_panel
from components.layer_panel import render_layer_panel
from components.map_panel import render_map_panel
from components.selection_panel import render_selection_panel
from components.stats_panel import render_stats_panel
from components.theme import load_theme
from components.toolbar import render_toolbar

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
# THÈME
# =========================================================

st.markdown(
    load_theme(),
    unsafe_allow_html=True,
)


# =========================================================
# GESTIONNAIRE DE COUCHES
# =========================================================

def get_layer_manager() -> LayerManager:
    """Retourne le gestionnaire de couches conservé en session."""

    if "layer_manager" not in st.session_state:
        st.session_state.layer_manager = LayerManager()

    return st.session_state.layer_manager


# =========================================================
# GESTIONNAIRE DE SÉLECTION
# =========================================================

def get_selection_manager() -> SelectionManager:
    """Retourne le gestionnaire de sélection conservé en session."""

    if "selection_manager" not in st.session_state:
        st.session_state.selection_manager = SelectionManager()

    return st.session_state.selection_manager


# =========================================================
# INITIALISATION DES SERVICES
# =========================================================

manager = get_layer_manager()
selection_manager = get_selection_manager()


# =========================================================
# EN-TÊTE
# =========================================================

render_header()


# =========================================================
# BARRE DE PARAMÈTRES
# =========================================================

parameters = render_toolbar()


# =========================================================
# ZONE PRINCIPALE
# =========================================================

left_column, right_column = st.columns(
    [1.05, 2.2],
    gap="large",
)


# ---------------------------------------------------------
# COLONNE GAUCHE
# ---------------------------------------------------------

with left_column:
    render_import_panel(manager)
    render_layer_panel(manager)


# ---------------------------------------------------------
# COLONNE DROITE
# ---------------------------------------------------------

with right_column:
    render_map_panel(
        manager=manager,
        selection_manager=selection_manager,
        commune=parameters["commune"],
        theme=parameters["theme"],
        distance=parameters["distance"],
    )


# =========================================================
# PANNEAU DE SÉLECTION
# =========================================================

render_selection_panel(
    selection_manager
)


# =========================================================
# INDICATEURS
# =========================================================

render_stats_panel(
    coverage=0.0,
    buildings=0,
    facilities=manager.count(),
    distance=parameters["distance"],
)


# =========================================================
# TABLE ATTRIBUTAIRE
# =========================================================

selected_layer = st.session_state.get(
    "selected_layer"
)

if selected_layer is not None:

    st.divider()

    render_attribute_table(
        selected_layer
    )


# =========================================================
# BOUTON GÉNÉRER
# =========================================================

if parameters["generate"]:

    if manager.count() == 0:

        st.warning(
            "Importe au moins une couche "
            "avant de lancer l'analyse."
        )

    else:

        st.success(
            f"{manager.count()} couche(s) prête(s) "
            "pour l'analyse."
        )