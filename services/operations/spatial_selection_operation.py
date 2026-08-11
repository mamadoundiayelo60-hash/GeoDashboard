"""Sélection par localisation de GeoDashboard."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from models.layer import Layer
from services.operations.operation import Operation


class SpatialSelectionOperation(Operation):
    """Sélectionne des entités selon une relation spatiale."""

    @property
    def name(self) -> str:
        return "SpatialSelection"

    @property
    def description(self) -> str:
        return (
            "Sélectionne les entités complètes d'une couche "
            "selon leur relation spatiale avec une autre couche."
        )

    def execute(
        self,
        layer: Layer,
        **kwargs,
    ) -> Layer:
        """Exécute une sélection par localisation."""

        reference_layer = kwargs.get(
            "reference_layer"
        )

        predicate = kwargs.get(
            "predicate",
            "intersects",
        )

        result_name = kwargs.get(
            "result_name"
        )

        # =============================================
        # VALIDATION
        # =============================================

        if reference_layer is None:
            raise ValueError(
                "Une couche de référence est obligatoire."
            )

        source_gdf = (
            layer.geodataframe.copy()
        )

        reference_gdf = (
            reference_layer.geodataframe.copy()
        )

        if source_gdf.empty:
            raise ValueError(
                "La couche source est vide."
            )

        if reference_gdf.empty:
            raise ValueError(
                "La couche de référence est vide."
            )

        if source_gdf.crs is None:
            raise ValueError(
                "La couche source ne possède pas de CRS."
            )

        if reference_gdf.crs is None:
            raise ValueError(
                "La couche de référence ne possède pas de CRS."
            )

        # =============================================
        # HARMONISER LES CRS
        # =============================================

        if source_gdf.crs != reference_gdf.crs:

            reference_gdf = (
                reference_gdf.to_crs(
                    source_gdf.crs
                )
            )

        # =============================================
        # RELATIONS AUTORISÉES
        # =============================================

        allowed_predicates = {
            "intersects",
            "within",
            "contains",
            "touches",
            "crosses",
            "overlaps",
        }

        if predicate not in allowed_predicates:
            raise ValueError(
                f"Relation spatiale inconnue : "
                f"{predicate}"
            )

        # =============================================
        # INDEX TEMPORAIRE
        # =============================================

        source_gdf = (
            source_gdf.reset_index(
                drop=False
            )
        )

        source_gdf = source_gdf.rename(
            columns={
                "index": "__source_index"
            }
        )

        # =============================================
        # JOINTURE SPATIALE
        # =============================================

        joined = gpd.sjoin(
            source_gdf,
            reference_gdf[
                ["geometry"]
            ],
            how="inner",
            predicate=predicate,
        )

        if joined.empty:
            raise ValueError(
                "Aucune entité ne respecte "
                "la relation spatiale demandée."
            )

        # =============================================
        # SUPPRIMER LES DOUBLONS
        # =============================================
        #
        # Un bâtiment peut intersecter plusieurs
        # buffers. On ne veut le conserver qu'une fois.
        # =============================================

        selected_indices = (
            joined["__source_index"]
            .drop_duplicates()
            .tolist()
        )

        result_gdf = (
            layer.geodataframe.loc[
                selected_indices
            ]
            .copy()
            .reset_index(drop=True)
        )

        # =============================================
        # NETTOYAGE
        # =============================================

        result_gdf = result_gdf[
            result_gdf.geometry.notna()
            & ~result_gdf.geometry.is_empty
        ].copy()

        if result_gdf.empty:
            raise ValueError(
                "La sélection n'a produit "
                "aucune géométrie exploitable."
            )

        # =============================================
        # NOM
        # =============================================

        if not result_name:

            result_name = (
                f"{layer.name}_selection_"
                f"{reference_layer.name}"
            )

        # =============================================
        # COUCHE RÉSULTAT
        # =============================================

        result_layer = Layer(
            name=str(result_name),
            geodataframe=result_gdf,
            source=Path(
                f"analysis://spatial-selection/"
                f"{layer.name}"
            ),
        )

        # Style du résultat
        result_layer.style["color"] = "#16A34A"
        result_layer.style["weight"] = 2
        result_layer.style["opacity"] = 0.90
        result_layer.style["fillOpacity"] = 0.30

        return result_layer