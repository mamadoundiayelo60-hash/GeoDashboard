"""Opération Intersection de GeoDashboard."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from models.layer import Layer
from services.operations.operation import Operation


class IntersectionOperation(Operation):
    """Calcule l'intersection entre deux couches."""

    @property
    def name(self) -> str:
        """Nom de l'opération."""
        return "Intersection"

    @property
    def description(self) -> str:
        """Description de l'opération."""
        return (
            "Calcule les géométries communes entre "
            "une couche source et une couche de référence."
        )

    def execute(
        self,
        layer: Layer,
        **kwargs,
    ) -> Layer:
        """Exécute l'intersection entre deux couches."""

        overlay_layer = kwargs.get(
            "overlay_layer"
        )

        if overlay_layer is None:
            raise ValueError(
                "La deuxième couche est obligatoire "
                "pour réaliser une intersection."
            )

        if not isinstance(
            overlay_layer,
            Layer,
        ):
            raise TypeError(
                "La couche de référence doit être "
                "un objet Layer."
            )

        source_gdf = (
            layer.geodataframe
            .copy()
        )

        overlay_gdf = (
            overlay_layer.geodataframe
            .copy()
        )

        if source_gdf.empty:
            raise ValueError(
                "La couche source est vide."
            )

        if overlay_gdf.empty:
            raise ValueError(
                "La couche de référence est vide."
            )

        if source_gdf.crs is None:
            raise ValueError(
                "La couche source ne possède pas de CRS."
            )

        if overlay_gdf.crs is None:
            raise ValueError(
                "La couche de référence ne possède pas de CRS."
            )

        # =================================================
        # HARMONISATION DES CRS
        # =================================================

        if source_gdf.crs != overlay_gdf.crs:

            overlay_gdf = (
                overlay_gdf.to_crs(
                    source_gdf.crs
                )
            )

        # =================================================
        # NETTOYAGE DES GÉOMÉTRIES
        # =================================================

        source_gdf = source_gdf[
            source_gdf.geometry.notna()
            & ~source_gdf.geometry.is_empty
        ].copy()

        overlay_gdf = overlay_gdf[
            overlay_gdf.geometry.notna()
            & ~overlay_gdf.geometry.is_empty
        ].copy()

        if source_gdf.empty:
            raise ValueError(
                "La couche source ne contient "
                "aucune géométrie exploitable."
            )

        if overlay_gdf.empty:
            raise ValueError(
                "La couche de référence ne contient "
                "aucune géométrie exploitable."
            )

        # =================================================
        # INTERSECTION
        # =================================================

        result_gdf = gpd.overlay(
            source_gdf,
            overlay_gdf,
            how="intersection",
            keep_geom_type=False,
        )

        result_gdf = result_gdf[
            result_gdf.geometry.notna()
            & ~result_gdf.geometry.is_empty
        ].copy()

        if result_gdf.empty:
            raise ValueError(
                "L'intersection n'a produit "
                "aucune géométrie."
            )

        # =================================================
        # NOM DU RÉSULTAT
        # =================================================

        result_name = kwargs.get(
            "result_name"
        )

        if not result_name:
            result_name = (
                f"{layer.name}_intersection_"
                f"{overlay_layer.name}"
            )

        # =================================================
        # COUCHE RÉSULTAT
        # =================================================

        result_layer = Layer(
            name=str(result_name),
            geodataframe=result_gdf,
            source=Path(
                f"analysis_intersection_"
                f"{layer.name}_"
                f"{overlay_layer.name}"
            ),
        )

        # Style par défaut du résultat
        result_layer.style["color"] = "#7C3AED"
        result_layer.style["weight"] = 2
        result_layer.style["opacity"] = 0.90
        result_layer.style["fillOpacity"] = 0.30

        return result_layer