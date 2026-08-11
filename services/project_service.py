"""Sauvegarde et restauration des projets GeoDashboard."""

from __future__ import annotations

import json
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import geopandas as gpd

from models.layer import Layer
from services.layer_manager import LayerManager


class ProjectService:
    """Gère la sauvegarde et l'ouverture d'un projet GeoDashboard."""

    PROJECT_VERSION = "1.0"

    @staticmethod
    def save_project(
        manager: LayerManager,
    ) -> bytes:
        """
        Crée une archive projet contenant :
        - les métadonnées du projet ;
        - les styles des couches ;
        - les données de chaque couche en GeoJSON.
        """

        project_buffer = BytesIO()

        project_definition = {
            "version": ProjectService.PROJECT_VERSION,
            "layers": [],
        }

        with ZipFile(
            project_buffer,
            mode="w",
            compression=ZIP_DEFLATED,
        ) as archive:

            for index, layer in enumerate(
                manager.list()
            ):

                layer_filename = (
                    f"layers/"
                    f"{index:03d}_{layer.name}.geojson"
                )

                gdf = layer.geodataframe.copy()

                geometry_column = gdf.geometry.name

                for column in gdf.columns:

                    if column == geometry_column:
                        continue

                    if str(gdf[column].dtype).startswith("datetime"):
                        gdf[column] = (
                            gdf[column]
                            .astype(str)
                            .replace("NaT", "")
                        )

                    elif gdf[column].dtype == "object":
                        gdf[column] = gdf[column].apply(
                            lambda value: (
                                value.isoformat()
                                if hasattr(value, "isoformat")
                                else value
                            )
                        )

                geojson_text = gdf.to_json()
                archive.writestr(
                    layer_filename,
                    geojson_text,
                )

                project_definition[
                    "layers"
                ].append(
                    {
                        "name": layer.name,
                        "source": str(
                            layer.source
                        ),
                        "visible": layer.visible,
                        "style": layer.style,
                        "popup_fields": (
                            layer.popup_fields
                        ),
                        "tooltip_fields": (
                            layer.tooltip_fields
                        ),
                        "show_labels": (
                            layer.show_labels
                        ),
                        "label_field": (
                            layer.label_field
                        ),
                        "label_size": (
                            layer.label_size
                        ),
                        "label_color": (
                            layer.label_color
                        ),
                        "label_halo": (
                            layer.label_halo
                        ),
                        "label_font": (
                            layer.label_font
                        ),
                        "data_file": (
                            layer_filename
                        ),
                    }
                )

            archive.writestr(
                "project.json",
                json.dumps(
                    project_definition,
                    ensure_ascii=False,
                    indent=2,
                ),
            )

        return project_buffer.getvalue()

    @staticmethod
    def load_project(
        project_data: bytes,
    ) -> LayerManager:
        """
        Recharge un projet GeoDashboard
        depuis une archive créée par save_project().
        """

        manager = LayerManager()

        project_buffer = BytesIO(
            project_data
        )

        with ZipFile(
            project_buffer,
            mode="r",
        ) as archive:

            project_definition = (
                json.loads(
                    archive.read(
                        "project.json"
                    ).decode(
                        "utf-8"
                    )
                )
            )

            for layer_info in (
                project_definition.get(
                    "layers",
                    []
                )
            ):

                geojson_text = (
                    archive.read(
                        layer_info[
                            "data_file"
                        ]
                    ).decode(
                        "utf-8"
                    )
                )

                gdf = (
                    gpd.read_file(
                        BytesIO(
                            geojson_text.encode(
                                "utf-8"
                            )
                        )
                    )
                )

                layer = Layer(
                    name=layer_info[
                        "name"
                    ],
                    geodataframe=gdf,
                    source=layer_info.get(
                        "source",
                        "project",
                    ),
                )

                layer.visible = (
                    layer_info.get(
                        "visible",
                        True,
                    )
                )

                layer.style.update(
                    layer_info.get(
                        "style",
                        {},
                    )
                )

                layer.popup_fields = (
                    layer_info.get(
                        "popup_fields",
                        [],
                    )
                )

                layer.tooltip_fields = (
                    layer_info.get(
                        "tooltip_fields",
                        [],
                    )
                )

                layer.show_labels = (
                    layer_info.get(
                        "show_labels",
                        False,
                    )
                )

                layer.label_field = (
                    layer_info.get(
                        "label_field",
                        "",
                    )
                )

                layer.label_size = (
                    layer_info.get(
                        "label_size",
                        12,
                    )
                )

                layer.label_color = (
                    layer_info.get(
                        "label_color",
                        "#000000",
                    )
                )

                layer.label_halo = (
                    layer_info.get(
                        "label_halo",
                        True,
                    )
                )

                layer.label_font = (
                    layer_info.get(
                        "label_font",
                        "Arial",
                    )
                )

                manager.add(
                    layer
                )

        return manager