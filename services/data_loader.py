"""Chargement et inspection des données géographiques."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import BadZipFile, ZipFile

import geopandas as gpd
import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".gpkg",
    ".geojson",
    ".json",
    ".kml",
    ".parquet",
    ".geoparquet",
    ".csv",
    ".zip",
    ".shp",
}


class DataLoaderError(Exception):
    """Erreur levée lorsqu'une couche ne peut pas être chargée."""


def _save_uploaded_file(
    uploaded_file: Any,
    destination: Path,
) -> Path:
    """Enregistre temporairement un fichier Streamlit."""

    destination.write_bytes(uploaded_file.getbuffer())
    return destination


def _load_zipped_shapefile(zip_path: Path) -> gpd.GeoDataFrame:
    """Charge un Shapefile contenu dans une archive ZIP."""

    try:
        with TemporaryDirectory() as extraction_directory:
            extraction_path = Path(extraction_directory)

            with ZipFile(zip_path, "r") as archive:
                archive.extractall(extraction_path)

            shapefiles = list(
                extraction_path.rglob("*.shp")
            )

            if not shapefiles:
                raise DataLoaderError(
                    "L’archive ZIP ne contient aucun fichier .shp."
                )

            if len(shapefiles) > 1:
                names = ", ".join(
                    shapefile.name
                    for shapefile in shapefiles
                )

                raise DataLoaderError(
                    "L’archive contient plusieurs Shapefiles : "
                    f"{names}. Place une seule couche par archive."
                )

            return gpd.read_file(shapefiles[0])

    except BadZipFile as error:
        raise DataLoaderError(
            "Le fichier ZIP est invalide ou endommagé."
        ) from error


def _load_csv(
    csv_path: Path,
    *,
    x_column: str | None,
    y_column: str | None,
    csv_crs: str,
) -> gpd.GeoDataFrame:
    """Transforme un CSV avec coordonnées en GeoDataFrame."""

    dataframe = pd.read_csv(csv_path)

    if not x_column or not y_column:
        raise DataLoaderError(
            "Pour un CSV, précise les colonnes X et Y."
        )

    missing_columns = [
        column
        for column in (x_column, y_column)
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise DataLoaderError(
            "Colonnes absentes du CSV : "
            + ", ".join(missing_columns)
        )

    dataframe[x_column] = pd.to_numeric(
        dataframe[x_column],
        errors="coerce",
    )

    dataframe[y_column] = pd.to_numeric(
        dataframe[y_column],
        errors="coerce",
    )

    dataframe = dataframe.dropna(
        subset=[x_column, y_column]
    ).copy()

    if dataframe.empty:
        raise DataLoaderError(
            "Aucune coordonnée valide n’a été trouvée."
        )

    geometry = gpd.points_from_xy(
        dataframe[x_column],
        dataframe[y_column],
    )

    return gpd.GeoDataFrame(
        dataframe,
        geometry=geometry,
        crs=csv_crs,
    )


def load_vector_file(
    file_path: str | Path,
    *,
    layer: str | None = None,
    x_column: str | None = None,
    y_column: str | None = None,
    csv_crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """Charge une couche vectorielle depuis le disque."""

    path = Path(file_path)

    if not path.exists():
        raise DataLoaderError(
            f"Fichier introuvable : {path}"
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DataLoaderError(
            f"Format non pris en charge : {extension}"
        )

    try:
        if extension == ".zip":
            geodataframe = _load_zipped_shapefile(path)

        elif extension in {".parquet", ".geoparquet"}:
            geodataframe = gpd.read_parquet(path)

        elif extension == ".csv":
            geodataframe = _load_csv(
                path,
                x_column=x_column,
                y_column=y_column,
                csv_crs=csv_crs,
            )

        elif extension == ".gpkg" and layer:
            geodataframe = gpd.read_file(
                path,
                layer=layer,
            )

        else:
            geodataframe = gpd.read_file(path)

    except DataLoaderError:
        raise

    except Exception as error:
        raise DataLoaderError(
            f"Impossible de charger {path.name} : {error}"
        ) from error

    if geodataframe.empty:
        raise DataLoaderError(
            "La couche chargée ne contient aucune entité."
        )

    if geodataframe.geometry.name not in geodataframe.columns:
        raise DataLoaderError(
            "Aucune colonne géométrique n’a été détectée."
        )

    geodataframe = geodataframe[
    geodataframe.geometry.notna()
    & ~geodataframe.geometry.is_empty
    ].copy()

    if geodataframe.empty:
        raise DataLoaderError(
            "Toutes les géométries de la couche sont nulles."
        )

    return geodataframe


def load_uploaded_layer(
    uploaded_file: Any,
    *,
    layer: str | None = None,
    x_column: str | None = None,
    y_column: str | None = None,
    csv_crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """Charge un fichier transmis avec st.file_uploader."""

    if uploaded_file is None:
        raise DataLoaderError(
            "Aucun fichier n’a été sélectionné."
        )

    filename = Path(uploaded_file.name)
    extension = filename.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DataLoaderError(
            f"Format non pris en charge : {extension}"
        )

    with TemporaryDirectory() as temporary_directory:
        temporary_path = (
            Path(temporary_directory)
            / filename.name
        )

        _save_uploaded_file(
            uploaded_file,
            temporary_path,
        )

        return load_vector_file(
            temporary_path,
            layer=layer,
            x_column=x_column,
            y_column=y_column,
            csv_crs=csv_crs,
        )


def inspect_layer(
    geodataframe: gpd.GeoDataFrame,
) -> dict[str, Any]:
    """Retourne les principales métadonnées d'une couche."""

    geometry_types = sorted(
        geodataframe.geometry
        .geom_type
        .dropna()
        .unique()
        .tolist()
    )

    bounds = geodataframe.total_bounds

    return {
        "feature_count": len(geodataframe),
        "column_count": len(geodataframe.columns),
        "columns": geodataframe.columns.tolist(),
        "geometry_types": geometry_types,
        "crs": (
            geodataframe.crs.to_string()
            if geodataframe.crs
            else "Non défini"
        ),
        "bounds": {
            "xmin": float(bounds[0]),
            "ymin": float(bounds[1]),
            "xmax": float(bounds[2]),
            "ymax": float(bounds[3]),
        },
        "has_invalid_geometries": bool(
            (~geodataframe.geometry.is_valid).any()
        ),
        "invalid_geometry_count": int(
            (~geodataframe.geometry.is_valid).sum()
        ),
    }