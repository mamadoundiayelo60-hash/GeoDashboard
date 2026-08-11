"""Panneau de gestion des couches GeoDashboard."""

from __future__ import annotations

import streamlit as st

from services.export_service import ExportService
from services.layer_manager import LayerManager
from services.project_service import ProjectService


def render_layer_panel(
    manager: LayerManager,
) -> None:
    """Affiche les couches et leurs paramètres."""

    with st.container(border=True):

        # ==================================================
        # EN-TÊTE
        # ==================================================

        header_col, action_col = st.columns([4, 1])

        with header_col:
            st.subheader(
                f"Couches du projet ({manager.count()})"
            )

        with action_col:
            if manager.count() > 0:

                if st.button(
                    "Tout supprimer",
                    use_container_width=True,
                    key="delete_all_layers",
                ):
                    manager.clear()

                    st.session_state.pop(
                        "selected_layer",
                        None,
                    )

                    st.rerun()

        # ==================================================
        # PROJET
        # ==================================================

        st.markdown("#### Projet")

        project_col1, project_col2 = st.columns(2)

        # --------------------------------------------------
        # SAUVEGARDER
        # --------------------------------------------------

        with project_col1:

            try:
                project_data = (
                    ProjectService.save_project(
                        manager
                    )
                )

                st.download_button(
                    "💾 Sauvegarder le projet",
                    data=project_data,
                    file_name="geodashboard_project.gdp",
                    mime="application/zip",
                    use_container_width=True,
                    key="save_geodashboard_project",
                )

            except Exception as error:

                st.warning(
                    "Impossible de préparer "
                    "la sauvegarde du projet."
                )

                st.caption(
                    str(error)
                )

        # --------------------------------------------------
        # OUVRIR
        # --------------------------------------------------

        with project_col2:

            project_file = st.file_uploader(
                "📂 Ouvrir un projet",
                type=["gdp"],
                key="open_geodashboard_project",
                help=(
                    "Ouvre un projet GeoDashboard "
                    "précédemment sauvegardé."
                ),
            )

        # --------------------------------------------------
        # CHARGER LE PROJET
        # --------------------------------------------------

        if project_file is not None:

            # Empêche de recharger le même fichier
            # à chaque rerun Streamlit.
            project_signature = (
                project_file.name,
                project_file.size,
            )

            previous_signature = (
                st.session_state.get(
                    "loaded_project_signature"
                )
            )

            if (
                project_signature
                != previous_signature
            ):

                try:

                    with st.spinner(
                        "Ouverture du projet..."
                    ):

                        loaded_manager = (
                            ProjectService.load_project(
                                project_file.getvalue()
                            )
                        )

                        manager.clear()

                        for layer in (
                            loaded_manager.list()
                        ):
                            manager.add(layer)

                    st.session_state[
                        "loaded_project_signature"
                    ] = project_signature

                    # Réinitialiser l'état lié
                    # à l'ancien projet.
                    st.session_state.pop(
                        "selected_layer",
                        None,
                    )

                    st.session_state.pop(
                        "map_bounds",
                        None,
                    )

                    st.session_state.pop(
                        "map_center",
                        None,
                    )

                    st.session_state.pop(
                        "map_zoom",
                        None,
                    )

                    st.session_state.pop(
                        "map_layers_signature",
                        None,
                    )

                    st.success(
                        f"Projet chargé : "
                        f"{manager.count()} couche(s)."
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        "Impossible d'ouvrir "
                        "le projet GeoDashboard."
                    )

                    st.exception(error)

        st.divider()

        # ==================================================
        # AUCUNE COUCHE
        # ==================================================

        if manager.count() == 0:

            st.info(
                "Aucune couche chargée. "
                "Utilise le panneau d'import."
            )

            return

        # ==================================================
        # LISTE DES COUCHES
        # ==================================================

        for index, current_layer in enumerate(
            manager.list()
        ):

            title = (
                f"{'●' if current_layer.visible else '○'} "
                f"{current_layer.name}"
            )

            with st.expander(
                title,
                expanded=False,
            ):

                # ==========================================
                # VISIBILITÉ
                # ==========================================

                current_layer.visible = st.checkbox(
                    "Visible sur la carte",
                    value=current_layer.visible,
                    key=(
                        f"visible_{index}_"
                        f"{current_layer.name}"
                    ),
                )

                # ==========================================
                # MÉTADONNÉES
                # ==========================================

                summary = current_layer.summary()

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Entités :** "
                        f"{summary['Entités']:,}"
                        .replace(",", " ")
                    )

                    st.write(
                        "**Géométrie :** "
                        f"{summary['Géométrie']}"
                    )

                with col2:

                    st.write(
                        f"**CRS :** "
                        f"{summary['CRS']}"
                    )

                    st.write(
                        "**Colonnes :** "
                        f"{summary['Colonnes']}"
                    )

                st.caption(
                    f"Source : "
                    f"{current_layer.source}"
                )

                st.divider()

                # ==========================================
                # INFORMATIONS AFFICHÉES
                # ==========================================

                st.markdown(
                    "#### Informations affichées"
                )

                available_fields = [
                    column
                    for column
                    in current_layer.geodataframe.columns
                    if (
                        column
                        != current_layer
                        .geodataframe
                        .geometry
                        .name
                    )
                ]

                if available_fields:

                    default_popup = (
                        current_layer.popup_fields
                        if current_layer.popup_fields
                        else available_fields[:6]
                    )

                    default_popup = [
                        field
                        for field in default_popup
                        if field in available_fields
                    ]

                    current_layer.popup_fields = (
                        st.multiselect(
                            "Popup au clic",
                            options=available_fields,
                            default=default_popup,
                            key=(
                                f"popup_{index}_"
                                f"{current_layer.name}"
                            ),
                            help=(
                                "Choisis les champs "
                                "affichés lors du clic."
                            ),
                        )
                    )

                    default_tooltip = (
                        current_layer.tooltip_fields
                        if current_layer.tooltip_fields
                        else (
                            current_layer
                            .popup_fields[:3]
                        )
                    )

                    default_tooltip = [
                        field
                        for field in default_tooltip
                        if field in available_fields
                    ]

                    current_layer.tooltip_fields = (
                        st.multiselect(
                            "Informations au survol",
                            options=available_fields,
                            default=default_tooltip,
                            key=(
                                f"tooltip_{index}_"
                                f"{current_layer.name}"
                            ),
                            help=(
                                "Choisis les champs "
                                "affichés au survol."
                            ),
                        )
                    )

                else:

                    st.caption(
                        "Cette couche ne contient "
                        "aucun champ attributaire."
                    )

                st.divider()

                # ==========================================
                # STYLE
                # ==========================================

                st.markdown(
                    "#### Style"
                )

                current_layer.style["color"] = (
                    st.color_picker(
                        "Couleur",
                        value=(
                            current_layer
                            .style.get(
                                "color",
                                "#2563EB",
                            )
                        ),
                        key=(
                            f"color_{index}_"
                            f"{current_layer.name}"
                        ),
                    )
                )

                current_layer.style["weight"] = (
                    st.slider(
                        "Épaisseur",
                        min_value=1,
                        max_value=10,
                        value=int(
                            current_layer
                            .style.get(
                                "weight",
                                3,
                            )
                        ),
                        key=(
                            f"weight_{index}_"
                            f"{current_layer.name}"
                        ),
                    )
                )

                current_layer.style["opacity"] = (
                    st.slider(
                        "Opacité",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(
                            current_layer
                            .style.get(
                                "opacity",
                                0.85,
                            )
                        ),
                        step=0.05,
                        key=(
                            f"opacity_{index}_"
                            f"{current_layer.name}"
                        ),
                    )
                )

                current_layer.style[
                    "fillOpacity"
                ] = st.slider(
                    "Remplissage",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(
                        current_layer
                        .style.get(
                            "fillOpacity",
                            0.20,
                        )
                    ),
                    step=0.05,
                    key=(
                        f"fill_{index}_"
                        f"{current_layer.name}"
                    ),
                )

                st.divider()

                # ==========================================
                # TABLE ATTRIBUTAIRE
                # ==========================================

                if st.button(
                    "Ouvrir la table attributaire",
                    key=(
                        f"table_{index}_"
                        f"{current_layer.name}"
                    ),
                    use_container_width=True,
                ):

                    st.session_state[
                        "selected_layer"
                    ] = current_layer

                    st.rerun()

                # ==========================================
                # EXPORT
                # ==========================================

                st.markdown(
                    "#### Exporter la couche"
                )

                try:

                    gpkg_data = (
                        ExportService.to_geopackage(
                            current_layer
                        )
                    )

                    geojson_data = (
                        ExportService.to_geojson(
                            current_layer
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
                                f"{current_layer.name}"
                                ".gpkg"
                            ),
                            mime=(
                                "application/"
                                "geopackage+sqlite3"
                            ),
                            key=(
                                f"download_gpkg_"
                                f"{index}_"
                                f"{current_layer.name}"
                            ),
                            use_container_width=True,
                        )

                    with export_col2:

                        st.download_button(
                            "GeoJSON (.geojson)",
                            data=geojson_data,
                            file_name=(
                                f"{current_layer.name}"
                                ".geojson"
                            ),
                            mime=(
                                "application/geo+json"
                            ),
                            key=(
                                f"download_geojson_"
                                f"{index}_"
                                f"{current_layer.name}"
                            ),
                            use_container_width=True,
                        )

                except Exception as error:

                    st.warning(
                        "L'export de cette couche "
                        "n'est pas disponible "
                        "actuellement."
                    )

                    st.caption(
                        str(error)
                    )

                st.divider()

                # ==========================================
                # SUPPRESSION
                # ==========================================

                if st.button(
                    "Supprimer cette couche",
                    key=(
                        f"delete_{index}_"
                        f"{current_layer.name}"
                    ),
                    use_container_width=True,
                ):

                    manager.remove(
                        current_layer.name
                    )

                    selected_layer = (
                        st.session_state.get(
                            "selected_layer"
                        )
                    )

                    if (
                        selected_layer is not None
                        and selected_layer.name
                        == current_layer.name
                    ):
                        st.session_state.pop(
                            "selected_layer",
                            None,
                        )

                    st.rerun()