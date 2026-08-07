"""Panneau d'import des données géographiques."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from models.layer import Layer
from services.data_loader import (
    DataLoaderError,
    load_uploaded_layer,
)
from services.layer_manager import LayerManager


SUPPORTED_TYPES = [
    "gpkg",
    "geojson",
    "json",
    "zip",
    "kml",
    "csv",
    "parquet",
    "geoparquet",
]


def render_import_panel(
    manager: LayerManager,
) -> None:
    """Importe une couche et l'ajoute au gestionnaire."""

    with st.container(border=True):
        st.subheader("Importer des données")

        uploaded_file = st.file_uploader(
            "Choisir une couche géographique",
            type=SUPPORTED_TYPES,
            help=(
                "Formats : GeoPackage, GeoJSON, Shapefile ZIP, "
                "KML, CSV XY et GeoParquet."
            ),
            key="layer_uploader",
        )

        if uploaded_file is None:
            st.caption(
                "Pour un Shapefile, importe une archive ZIP contenant "
                "au minimum les fichiers .shp, .shx et .dbf."
            )
            return

        extension = Path(uploaded_file.name).suffix.lower()

        x_column = None
        y_column = None
        csv_crs = "EPSG:4326"

        if extension == ".csv":
            st.info(
                "Pour un CSV, indique les colonnes de coordonnées."
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                x_column = st.text_input(
                    "Colonne X / longitude",
                    value="longitude",
                )

            with col2:
                y_column = st.text_input(
                    "Colonne Y / latitude",
                    value="latitude",
                )

            with col3:
                csv_crs = st.text_input(
                    "CRS",
                    value="EPSG:4326",
                )

        layer_name = st.text_input(
            "Nom de la couche",
            value=Path(uploaded_file.name).stem,
        )

        import_button = st.button(
            "Ajouter la couche",
            type="primary",
            use_container_width=True,
        )

        if not import_button:
            return

        if not layer_name.strip():
            st.error("Le nom de la couche est obligatoire.")
            return

        if manager.get(layer_name.strip()) is not None:
            st.error(
                f"Une couche nommée « {layer_name.strip()} » existe déjà."
            )
            return

        try:
            with st.spinner("Chargement de la couche..."):
                geodataframe = load_uploaded_layer(
                    uploaded_file,
                    x_column=x_column,
                    y_column=y_column,
                    csv_crs=csv_crs,
                )

                layer = Layer(
                    name=layer_name.strip(),
                    geodataframe=geodataframe,
                    source=uploaded_file.name,
                )

                manager.add(layer)

            st.success(
                f"Couche « {layer.name} » ajoutée : "
                f"{layer.feature_count:,} entités."
                .replace(",", " ")
            )

            st.rerun()

        except DataLoaderError as error:
            st.error(str(error))

        except Exception as error:
            st.exception(error)