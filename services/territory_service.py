"""Gestion du territoire d'analyse de GeoDashboard."""

from __future__ import annotations

import geopandas as gpd

from models.layer import Layer


class TerritoryService:
    """Gère la sélection d'une commune dans une couche nationale."""

    # Champs fréquemment utilisés pour le nom de commune.
    NAME_FIELDS = [
        "NOM",
        "nom",
        "NOM_COM",
        "nom_com",
        "COMMUNE",
        "commune",
        "TEX2",
        "tex2",
        "NAME",
        "name",
    ]

    @staticmethod
    def find_name_field(
        layer: Layer,
    ) -> str:
        """Détecte la colonne contenant le nom de la commune."""

        columns = (
            layer.geodataframe
            .columns
            .tolist()
        )

        for field in TerritoryService.NAME_FIELDS:

            if field in columns:
                return field

        raise ValueError(
            "Impossible de trouver une colonne "
            "contenant le nom des communes."
        )

    @staticmethod
    def commune_names(
        layer: Layer,
    ) -> list[str]:
        """Retourne les communes disponibles."""

        field = TerritoryService.find_name_field(
            layer
        )

        names = (
            layer.geodataframe[field]
            .dropna()
            .astype(str)
            .str.strip()
        )

        names = [
            name
            for name in names.unique().tolist()
            if name
        ]

        return sorted(
            names,
            key=str.casefold,
        )

    @staticmethod
    def select_commune(
        layer: Layer,
        commune_name: str,
        result_name: str = "territoire_analyse",
    ) -> Layer:
        """
        Extrait une commune depuis une couche
        contenant plusieurs communes.
        """

        if layer is None:
            raise ValueError(
                "La couche des communes est obligatoire."
            )

        gdf = (
            layer.geodataframe
            .copy()
        )

        if gdf.empty:
            raise ValueError(
                "La couche des communes est vide."
            )

        if gdf.crs is None:
            raise ValueError(
                "La couche des communes "
                "ne possède pas de CRS."
            )

        field = TerritoryService.find_name_field(
            layer
        )

        requested_name = (
            commune_name
            .strip()
            .casefold()
        )

        mask = (
            gdf[field]
            .astype(str)
            .str.strip()
            .str.casefold()
            == requested_name
        )

        selected_gdf = (
            gdf[mask]
            .copy()
            .reset_index(drop=True)
        )

        if selected_gdf.empty:
            raise ValueError(
                f"La commune « {commune_name} » "
                "n'a pas été trouvée."
            )

        # Une commune peut exceptionnellement
        # être composée de plusieurs polygones.
        # On conserve donc toutes les géométries
        # correspondant au nom recherché.

        result_layer = Layer(
            name=result_name,
            geodataframe=selected_gdf,
            source=(
                f"territory://"
                f"{layer.name}/"
                f"{commune_name}"
            ),
        )

        # Style du territoire d'analyse.
        result_layer.style["color"] = "#1D4ED8"
        result_layer.style["weight"] = 3
        result_layer.style["opacity"] = 0.90
        result_layer.style["fillOpacity"] = 0.03

        # Quelques champs utiles pour le clic.
        result_layer.popup_fields = [
            field
        ]

        result_layer.tooltip_fields = [
            field
        ]

        return result_layer

    @staticmethod
    def area_km2(
        layer: Layer,
    ) -> float:
        """Calcule la superficie du territoire en km²."""

        gdf = (
            layer.geodataframe
            .copy()
        )

        if gdf.empty:
            return 0.0

        if gdf.crs is None:
            raise ValueError(
                "Le territoire ne possède pas de CRS."
            )

        if gdf.crs.is_geographic:
            gdf = gdf.to_crs(
                "EPSG:2154"
            )

        try:
            geometry = (
                gdf.geometry.union_all()
            )

        except AttributeError:
            geometry = (
                gdf.geometry.unary_union
            )

        if geometry is None:
            return 0.0

        return float(
            geometry.area
            / 1_000_000
        )