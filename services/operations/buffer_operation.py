"""Opération Buffer de GeoDashboard."""

from __future__ import annotations

from pathlib import Path

from models.layer import Layer
from services.operations.operation import Operation


class BufferOperation(Operation):
    """Crée une zone tampon autour des géométries."""

    @property
    def name(self) -> str:
        """Nom de l'opération."""
        return "Buffer"

    @property
    def description(self) -> str:
        """Description de l'opération."""
        return (
            "Crée une zone tampon autour des entités "
            "d'une couche selon une distance donnée."
        )

    def execute(
        self,
        layer: Layer,
        **kwargs,
    ) -> Layer:
        """Exécute le buffer et retourne une nouvelle couche."""

        # =================================================
        # DISTANCE
        # =================================================

        distance = kwargs.get(
            "distance"
        )

        if distance is None:
            raise ValueError(
                "La distance du buffer est obligatoire."
            )

        distance = float(distance)

        if distance <= 0:
            raise ValueError(
                "La distance doit être supérieure à 0."
            )

        # =================================================
        # COUCHE SOURCE
        # =================================================

        source_gdf = (
            layer.geodataframe.copy()
        )

        if source_gdf.empty:
            raise ValueError(
                "La couche source est vide."
            )

        if source_gdf.crs is None:
            raise ValueError(
                "La couche source ne possède pas de CRS."
            )

        # =================================================
        # CRS DE TRAVAIL
        # =================================================

        working_gdf = (
            source_gdf.copy()
        )

        # Un buffer ne doit pas être calculé directement
        # sur un CRS géographique comme EPSG:4326.
        if working_gdf.crs.is_geographic:

            working_gdf = (
                working_gdf.to_crs(
                    "EPSG:2154"
                )
            )

        # =================================================
        # BUFFER
        # =================================================

        result_gdf = (
            working_gdf.copy()
        )

        result_gdf.geometry = (
            working_gdf.geometry.buffer(
                distance
            )
        )

        # Supprimer les géométries invalides pour le résultat.
        result_gdf = result_gdf[
            result_gdf.geometry.notna()
            & ~result_gdf.geometry.is_empty
        ].copy()

        if result_gdf.empty:
            raise ValueError(
                "Le buffer n'a produit aucune géométrie."
            )

        # =================================================
        # NOM DU RÉSULTAT
        # =================================================

        result_name = kwargs.get(
            "result_name"
        )

        if not result_name:

            distance_text = (
                int(distance)
                if distance.is_integer()
                else distance
            )

            result_name = (
                f"{layer.name}_buffer_"
                f"{distance_text}m"
            )

        # =================================================
        # CRÉATION DE LA NOUVELLE COUCHE
        # =================================================

        result_layer = Layer(
            name=str(result_name),
            geodataframe=result_gdf,
            source=Path(
                f"analysis_buffer_{layer.name}"
            ),
        )

        # =================================================
        # STYLE PAR DÉFAUT
        # =================================================

        result_layer.style[
            "color"
        ] = "#DC2626"

        result_layer.style[
            "weight"
        ] = 2

        result_layer.style[
            "opacity"
        ] = 0.90

        result_layer.style[
            "fillOpacity"
        ] = 0.20

        return result_layer