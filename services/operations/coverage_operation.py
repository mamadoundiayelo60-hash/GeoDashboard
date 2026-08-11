"""Opération de couverture territoriale de GeoDashboard."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from models.layer import Layer
from services.operations.operation import Operation


class CoverageOperation(Operation):
    """
    Produit une couche représentant la partie
    couverte ou non couverte d'un territoire.
    """

    @property
    def name(self) -> str:
        """Nom de l'opération."""

        return "Coverage"

    @property
    def description(self) -> str:
        """Description de l'opération."""

        return (
            "Calcule la partie couverte ou non couverte "
            "d'un territoire à partir d'une couche "
            "surfacique de référence."
        )

    def execute(
        self,
        layer: Layer,
        **kwargs,
    ) -> Layer:
        """Exécute l'analyse de couverture territoriale."""

        territory_layer = kwargs.get(
            "territory_layer"
        )

        mode = kwargs.get(
            "mode",
            "covered",
        )

        result_name = kwargs.get(
            "result_name"
        )

        # =================================================
        # VALIDATION
        # =================================================

        if territory_layer is None:
            raise ValueError(
                "Le territoire d'analyse est obligatoire."
            )

        # Ne pas utiliser isinstance() ici.
        # On vérifie seulement que l'objet possède
        # bien les données géographiques nécessaires.
        if not hasattr(
            territory_layer,
            "geodataframe",
        ):
            raise TypeError(
                "Le territoire fourni ne contient "
                "pas de GeoDataFrame."
            )

        if not hasattr(
            layer,
            "geodataframe",
        ):
            raise TypeError(
                "La couche de couverture ne contient "
                "pas de GeoDataFrame."
            )

        if mode not in {
            "covered",
            "uncovered",
        }:
            raise ValueError(
                "Le mode doit être "
                "'covered' ou 'uncovered'."
            )

        # =================================================
        # DONNÉES
        # =================================================

        coverage_gdf = (
            layer
            .geodataframe
            .copy()
        )

        territory_gdf = (
            territory_layer
            .geodataframe
            .copy()
        )

        if coverage_gdf.empty:
            raise ValueError(
                "La couche de couverture est vide."
            )

        if territory_gdf.empty:
            raise ValueError(
                "Le territoire d'analyse est vide."
            )

        if coverage_gdf.crs is None:
            raise ValueError(
                "La couche de couverture "
                "ne possède pas de CRS."
            )

        if territory_gdf.crs is None:
            raise ValueError(
                "Le territoire d'analyse "
                "ne possède pas de CRS."
            )

        # =================================================
        # NETTOYAGE
        # =================================================

        coverage_gdf = coverage_gdf[
            coverage_gdf.geometry.notna()
            & ~coverage_gdf.geometry.is_empty
        ].copy()

        territory_gdf = territory_gdf[
            territory_gdf.geometry.notna()
            & ~territory_gdf.geometry.is_empty
        ].copy()

        if coverage_gdf.empty:
            raise ValueError(
                "Aucune géométrie exploitable "
                "dans la couche de couverture."
            )

        if territory_gdf.empty:
            raise ValueError(
                "Aucune géométrie exploitable "
                "dans le territoire."
            )

        # =================================================
        # VÉRIFIER QUE LA COUVERTURE EST SURFACIQUE
        # =================================================

        geometry_types = (
            coverage_gdf
            .geometry
            .geom_type
            .dropna()
            .str.lower()
            .tolist()
        )

        if not any(
            "polygon" in geometry_type
            for geometry_type in geometry_types
        ):
            raise ValueError(
                "La couche de couverture doit "
                "contenir des polygones."
            )

        # =================================================
        # CRS MÉTRIQUE
        # =================================================

        metric_crs = "EPSG:2154"

        coverage_gdf = (
            coverage_gdf.to_crs(
                metric_crs
            )
        )

        territory_gdf = (
            territory_gdf.to_crs(
                metric_crs
            )
        )

        # =================================================
        # FUSION DES GÉOMÉTRIES
        # =================================================

        try:

            coverage_geometry = (
                coverage_gdf
                .geometry
                .union_all()
            )

        except AttributeError:

            coverage_geometry = (
                coverage_gdf
                .geometry
                .unary_union
            )

        try:

            territory_geometry = (
                territory_gdf
                .geometry
                .union_all()
            )

        except AttributeError:

            territory_geometry = (
                territory_gdf
                .geometry
                .unary_union
            )

        if (
            coverage_geometry is None
            or coverage_geometry.is_empty
        ):
            raise ValueError(
                "Impossible de fusionner "
                "les zones de couverture."
            )

        if (
            territory_geometry is None
            or territory_geometry.is_empty
        ):
            raise ValueError(
                "Impossible de fusionner "
                "le territoire."
            )

        # =================================================
        # ZONE COUVERTE
        # =================================================

        covered_geometry = (
            territory_geometry
            .intersection(
                coverage_geometry
            )
        )

        # =================================================
        # ZONE NON COUVERTE
        # =================================================

        if mode == "covered":

            result_geometry = (
                covered_geometry
            )

            analysis_label = (
                "Zone couverte"
            )

        else:

            result_geometry = (
                territory_geometry
                .difference(
                    coverage_geometry
                )
            )

            analysis_label = (
                "Zone non couverte"
            )

        if (
            result_geometry is None
            or result_geometry.is_empty
        ):
            raise ValueError(
                "L'analyse n'a produit "
                "aucune géométrie."
            )

        # =================================================
        # SURFACE
        # =================================================

        area_km2 = float(
            result_geometry.area
            / 1_000_000
        )

        # =================================================
        # GEODATAFRAME RÉSULTAT
        # =================================================

        result_gdf = gpd.GeoDataFrame(
            {
                "analyse": [
                    analysis_label
                ],
                "surface_km2": [
                    area_km2
                ],
            },
            geometry=[
                result_geometry
            ],
            crs=metric_crs,
        )

        # =================================================
        # NOM
        # =================================================

        if not result_name:

            suffix = (
                "zone_couverte"
                if mode == "covered"
                else "zone_non_couverte"
            )

            result_name = (
                f"{layer.name}_"
                f"{suffix}"
            )

        # =================================================
        # COUCHE RÉSULTAT
        # =================================================

        result_layer = Layer(
            name=str(
                result_name
            ),
            geodataframe=result_gdf,
            source=Path(
                f"analysis_coverage_"
                f"{layer.name}_"
                f"{mode}"
            ),
        )

        result_layer.popup_fields = [
            "analyse",
            "surface_km2",
        ]

        result_layer.tooltip_fields = [
            "analyse",
        ]

        # =================================================
        # STYLE
        # =================================================

        if mode == "covered":

            # Vert = territoire couvert
            result_layer.style[
                "color"
            ] = "#16A34A"

            result_layer.style[
                "weight"
            ] = 2

            result_layer.style[
                "opacity"
            ] = 0.90

            result_layer.style[
                "fillOpacity"
            ] = 0.30

        else:

            # Rouge = territoire non couvert
            result_layer.style[
                "color"
            ] = "#DC2626"

            result_layer.style[
                "weight"
            ] = 2

            result_layer.style[
                "opacity"
            ] = 0.85

            result_layer.style[
                "fillOpacity"
            ] = 0.20

        return result_layer