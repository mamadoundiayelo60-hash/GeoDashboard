"""Service d'export des couches GeoDashboard."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from models.layer import Layer


class ExportService:
    """Exporte les couches géographiques."""

    @staticmethod
    def to_geopackage(
        layer: Layer,
    ) -> bytes:
        """Exporte une couche au format GeoPackage."""

        with TemporaryDirectory() as temporary_directory:

            output_path = (
                Path(temporary_directory)
                / f"{layer.name}.gpkg"
            )

            gdf = layer.geodataframe.copy()

            # Éviter les conflits avec certains
            # noms réservés dans GeoPackage.
            reserved_names = {
                "fid",
                "id",
            }

            rename_columns = {}

            for column in gdf.columns:

                if column == gdf.geometry.name:
                    continue

                if column.lower() in reserved_names:
                    rename_columns[column] = (
                        f"source_{column}"
                    )

            if rename_columns:
                gdf = gdf.rename(
                    columns=rename_columns
                )

            gdf.to_file(
                output_path,
                layer=layer.name,
                driver="GPKG",
                index=False,
            )

            return output_path.read_bytes()

    @staticmethod
    def to_geojson(
        layer: Layer,
    ) -> bytes:
        """Exporte une couche au format GeoJSON."""

        with TemporaryDirectory() as temporary_directory:

            output_path = (
                Path(temporary_directory)
                / f"{layer.name}.geojson"
            )

            gdf = layer.geodataframe.copy()

            geometry_column = gdf.geometry.name

            for column in gdf.columns:

                if column == geometry_column:
                    continue

                if str(
                    gdf[column].dtype
                ).startswith("datetime"):

                    gdf[column] = (
                        gdf[column]
                        .astype(str)
                        .replace("NaT", "")
                    )

                elif gdf[column].dtype == "object":

                    gdf[column] = (
                        gdf[column].apply(
                            lambda value: (
                                value.isoformat()
                                if hasattr(
                                    value,
                                    "isoformat",
                                )
                                else value
                            )
                        )
                    )

            gdf.to_file(
                output_path,
                driver="GeoJSON",
                index=False,
            )

            return output_path.read_bytes()