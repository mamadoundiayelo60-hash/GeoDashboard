"""Préparation des couches pour l'affichage."""

from __future__ import annotations

import geopandas as gpd


class DisplayService:
    """Prépare une version allégée des données pour la carte."""

    @staticmethod
    def simplify(
        gdf: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        """Simplifie les géométries uniquement pour l'affichage."""

        display = gdf.copy()

        if display.empty:
            return display

        geometry_types = (
            display.geometry
            .geom_type
            .dropna()
            .str.lower()
            .unique()
            .tolist()
        )

        # Les points n'ont rien à simplifier.
        if all(
            "point" in geometry_type
            for geometry_type in geometry_types
        ):
            return display

        # Simplification seulement pour les couches assez grandes.
        if len(display) <= 500:
            return display

        # On travaille dans le CRS d'origine.
        # Pour tes données EPSG:2154, la tolérance est en mètres.
        tolerance = 2.0

        display.geometry = (
            display.geometry.simplify(
                tolerance=tolerance,
                preserve_topology=True,
            )
        )

        return display