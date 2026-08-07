"""Modèle représentant une couche SIG."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd


@dataclass
class Layer:
    """Représente une couche géographique."""

    name: str

    geodataframe: gpd.GeoDataFrame

    source: str | Path

    visible: bool = True

    style: dict = field(
    default_factory=lambda: {
        "color": "#2563EB",
        "weight": 3,
        "opacity": 0.85,
        "fillOpacity": 0.20,
    }
)

    popup_fields: list[str] = field(
        default_factory=list
    )

    tooltip_fields: list[str] = field(
        default_factory=list
    )

    show_labels: bool = False

    label_field: str = ""

    label_size: int = 12

    label_color: str = "#000000"

    label_halo: bool = True

    label_font: str = "Arial"
    @property
    def feature_count(self) -> int:
        return len(self.geodataframe)

    @property
    def crs(self) -> str:
        if self.geodataframe.crs:
            return self.geodataframe.crs.to_string()
        return "Non défini"

    @property
    def geometry_type(self) -> str:

        types = (
            self.geodataframe.geometry
            .geom_type
            .unique()
            .tolist()
        )

        return ", ".join(types)

    @property
    def bounds(self):

        xmin, ymin, xmax, ymax = (
            self.geodataframe.total_bounds
        )

        return {
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax,
        }

    @property
    def columns(self):

        return list(self.geodataframe.columns)

    def summary(self) -> dict:
        """Résumé de la couche."""

        return {

            "Nom": self.name,

            "Entités": self.feature_count,

            "CRS": self.crs,

            "Géométrie": self.geometry_type,

            "Colonnes": len(self.columns),

            "Visible": self.visible,
        }