"""Service de génération des rapports GeoDashboard."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

import geopandas as gpd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.layer import Layer


class ReportService:
    """Génère les rapports PDF de GeoDashboard."""

    # =====================================================
    # FORMAT
    # =====================================================

    @staticmethod
    def _format_number(
        value: float,
        decimals: int = 2,
    ) -> str:

        return (
            f"{value:,.{decimals}f}"
            .replace(",", " ")
            .replace(".", ",")
        )

    # =====================================================
    # GÉOMÉTRIES
    # =====================================================

    @staticmethod
    def _union_geometry(gdf):

        try:
            return gdf.geometry.union_all()
        except AttributeError:
            return gdf.geometry.unary_union

    # =====================================================
    # STYLE
    # =====================================================

    @staticmethod
    def _style_value(
        layer: Layer | None,
        key: str,
        default,
    ):
        """Lit un style GeoDashboard."""

        if (
            layer is None
            or layer.style is None
        ):
            return default

        return layer.style.get(
            key,
            default,
        )

    @staticmethod
    def _alpha(
        layer: Layer | None,
        key: str,
        default: float,
    ) -> float:

        value = (
            ReportService._style_value(
                layer,
                key,
                default,
            )
        )

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    # =====================================================
    # CALCUL UNIQUE
    # =====================================================

    @staticmethod
    def _calculate_coverage(
        territory_layer: Layer,
        coverage_layer: Layer,
    ) -> dict:

        territory_gdf = (
            territory_layer.geodataframe
            .copy()
            .to_crs("EPSG:2154")
        )

        coverage_gdf = (
            coverage_layer.geodataframe
            .copy()
            .to_crs("EPSG:2154")
        )

        territory_geometry = (
            ReportService._union_geometry(
                territory_gdf
            )
        )

        coverage_geometry = (
            ReportService._union_geometry(
                coverage_gdf
            )
        )

        covered_geometry = (
            territory_geometry.intersection(
                coverage_geometry
            )
        )

        uncovered_geometry = (
            territory_geometry.difference(
                covered_geometry
            )
        )

        territory_area = float(
            territory_geometry.area
            / 1_000_000
        )

        covered_area = float(
            covered_geometry.area
            / 1_000_000
        )

        uncovered_area = float(
            uncovered_geometry.area
            / 1_000_000
        )

        coverage_rate = (
            covered_area
            / territory_area
            * 100
            if territory_area > 0
            else 0.0
        )

        return {
            "territory_gdf": territory_gdf,
            "covered_geometry": covered_geometry,
            "uncovered_geometry": uncovered_geometry,
            "territory_area": territory_area,
            "covered_area": covered_area,
            "uncovered_area": uncovered_area,
            "coverage_rate": coverage_rate,
        }

    # =====================================================
    # CARTE
    # =====================================================

    @staticmethod
    def _generate_map(
        territory_layer: Layer,
        coverage_layer: Layer,
        equipment_layer: Layer | None = None,
        covered_style_layer: Layer | None = None,
        uncovered_style_layer: Layer | None = None,
        boundary_style_layer: Layer | None = None,
    ) -> BytesIO:

        analysis = (
            ReportService._calculate_coverage(
                territory_layer,
                coverage_layer,
            )
        )

        territory_gdf = analysis[
            "territory_gdf"
        ]

        covered_geometry = analysis[
            "covered_geometry"
        ]

        uncovered_geometry = analysis[
            "uncovered_geometry"
        ]

        covered_gdf = gpd.GeoDataFrame(
            {"type": ["Zone couverte"]},
            geometry=[covered_geometry],
            crs="EPSG:2154",
        )

        uncovered_gdf = gpd.GeoDataFrame(
            {"type": ["Zone non couverte"]},
            geometry=[uncovered_geometry],
            crs="EPSG:2154",
        )

        # =================================================
        # STYLES RÉELS DE GEODASHBOARD
        # =================================================

        covered_color = (
            ReportService._style_value(
                covered_style_layer,
                "color",
                ReportService._style_value(
                    coverage_layer,
                    "color",
                    "#16A34A",
                ),
            )
        )

        covered_fill = (
            ReportService._style_value(
                covered_style_layer,
                "fillColor",
                covered_color,
            )
        )

        covered_alpha = (
            ReportService._alpha(
                covered_style_layer,
                "fillOpacity",
                0.55,
            )
        )

        uncovered_color = (
            ReportService._style_value(
                uncovered_style_layer,
                "color",
                "#DC2626",
            )
        )

        uncovered_fill = (
            ReportService._style_value(
                uncovered_style_layer,
                "fillColor",
                uncovered_color,
            )
        )

        uncovered_alpha = (
            ReportService._alpha(
                uncovered_style_layer,
                "fillOpacity",
                0.25,
            )
        )

        boundary_color = (
            ReportService._style_value(
                boundary_style_layer,
                "color",
                "#2563EB",
            )
        )

        boundary_width = (
            ReportService._style_value(
                boundary_style_layer,
                "weight",
                2.2,
            )
        )

        try:
            boundary_width = float(
                boundary_width
            )
        except (TypeError, ValueError):
            boundary_width = 2.2

        # =================================================
        # FIGURE
        # =================================================

        fig, ax = plt.subplots(
            figsize=(10, 7)
        )

        # =================================================
        # NON COUVERT
        # =================================================

        uncovered_gdf.plot(
            ax=ax,
            facecolor=uncovered_fill,
            edgecolor=uncovered_color,
            alpha=uncovered_alpha,
            linewidth=1.0,
            label="Zone non couverte",
            zorder=1,
        )

        # =================================================
        # COUVERT
        # =================================================

        if not covered_geometry.is_empty:

            covered_gdf.plot(
                ax=ax,
                facecolor=covered_fill,
                edgecolor=covered_color,
                alpha=covered_alpha,
                linewidth=1.2,
                label="Zone couverte",
                zorder=2,
            )

        # =================================================
        # LIMITE
        # =================================================

        territory_gdf.boundary.plot(
            ax=ax,
            color=boundary_color,
            linewidth=boundary_width,
            label="Limite du territoire",
            zorder=4,
        )

        # =================================================
        # ÉQUIPEMENTS
        # =================================================

        if (
            equipment_layer is not None
            and equipment_layer.geodataframe is not None
            and not equipment_layer.geodataframe.empty
            and equipment_layer.geodataframe.crs is not None
        ):

            equipment_gdf = (
                equipment_layer.geodataframe
                .copy()
                .to_crs(
                    "EPSG:2154"
                )
            )

            geometry_types = set(
                equipment_gdf.geometry
                .geom_type
                .dropna()
                .tolist()
            )

            if geometry_types.intersection(
                {
                    "Point",
                    "MultiPoint",
                }
            ):

                equipment_color = (
                    ReportService._style_value(
                        equipment_layer,
                        "color",
                        "#2563EB",
                    )
                )

                equipment_gdf.plot(
                    ax=ax,
                    marker="o",
                    markersize=32,
                    color=equipment_color,
                    edgecolor="white",
                    linewidth=0.9,
                    zorder=10,
                    label="Équipements",
                )

        # =================================================
        # EMPRISE
        # =================================================

        minx, miny, maxx, maxy = (
            territory_gdf.total_bounds
        )

        width = maxx - minx
        height = maxy - miny

        ax.set_xlim(
            minx - width * 0.05,
            maxx + width * 0.05,
        )

        ax.set_ylim(
            miny - height * 0.05,
            maxy + height * 0.05,
        )

        ax.set_title(
            "Carte de la couverture territoriale",
            fontsize=15,
            fontweight="bold",
            pad=15,
        )

        ax.set_xlabel("")
        ax.set_ylabel("")

        ax.tick_params(
            left=False,
            bottom=False,
            labelleft=False,
            labelbottom=False,
        )

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_aspect(
            "equal",
            adjustable="box",
        )

        # =================================================
        # LÉGENDE
        # =================================================

        handles, labels = (
            ax.get_legend_handles_labels()
        )

        legend_order = [
            "Équipements",
            "Zone couverte",
            "Zone non couverte",
            "Limite du territoire",
        ]

        sorted_handles = []
        sorted_labels = []

        for label in legend_order:

            if label in labels:

                index = labels.index(
                    label
                )

                sorted_handles.append(
                    handles[index]
                )

                sorted_labels.append(
                    labels[index]
                )

        ax.legend(
            sorted_handles,
            sorted_labels,
            loc="upper left",
            bbox_to_anchor=(
                1.02,
                1.0,
            ),
            frameon=True,
            framealpha=0.96,
            fontsize=9,
            title="Légende",
            title_fontsize=10,
            borderpad=0.8,
            labelspacing=0.6,
        )

        fig.subplots_adjust(
            right=0.76
        )

        # =================================================
        # IMAGE
        # =================================================

        image_buffer = BytesIO()

        fig.savefig(
            image_buffer,
            format="png",
            dpi=180,
            bbox_inches="tight",
        )

        plt.close(fig)

        image_buffer.seek(0)

        return image_buffer

    # =====================================================
    # RAPPORT PDF
    # =====================================================

    @staticmethod
    def generate_analysis_report(
        territory_layer: Layer,
        result_layer: Layer,
        result_info: dict,
        coverage_layer: Layer,
        equipment_layer: Layer | None = None,
        covered_style_layer: Layer | None = None,
        uncovered_style_layer: Layer | None = None,
        boundary_style_layer: Layer | None = None,
    ) -> bytes:

        if territory_layer is None:
            raise ValueError(
                "Le territoire est obligatoire."
            )

        if coverage_layer is None:
            raise ValueError(
                "La couche de couverture est obligatoire."
            )

        analysis = (
            ReportService._calculate_coverage(
                territory_layer,
                coverage_layer,
            )
        )

        territory_area = analysis[
            "territory_area"
        ]

        covered_area = analysis[
            "covered_area"
        ]

        uncovered_area = analysis[
            "uncovered_area"
        ]

        coverage_rate = analysis[
            "coverage_rate"
        ]

        territory_name = (
            result_info.get(
                "territory_name"
            )
            or territory_layer.name
        )

        distance = result_info.get(
            "distance"
        )

        operation = result_info.get(
            "operation",
            "Analyse spatiale",
        )

        source_count = (
            equipment_layer.feature_count
            if equipment_layer is not None
            else result_info.get(
                "source_feature_count",
                coverage_layer.feature_count,
            )
        )

        map_buffer = (
            ReportService._generate_map(
                territory_layer=territory_layer,
                coverage_layer=coverage_layer,
                equipment_layer=equipment_layer,
                covered_style_layer=(
                    covered_style_layer
                ),
                uncovered_style_layer=(
                    uncovered_style_layer
                ),
                boundary_style_layer=(
                    boundary_style_layer
                ),
            )
        )

        # =================================================
        # DOCUMENT
        # =================================================

        pdf_buffer = BytesIO()

        document = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=1.7 * cm,
            leftMargin=1.7 * cm,
            topMargin=1.7 * cm,
            bottomMargin=1.7 * cm,
            title=(
                f"Rapport GeoDashboard - "
                f"{territory_name}"
            ),
            author="GeoDashboard",
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "GeoDashboardTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=colors.HexColor(
                "#102A43"
            ),
            alignment=TA_CENTER,
            spaceAfter=8,
        )

        subtitle_style = ParagraphStyle(
            "GeoDashboardSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=colors.HexColor(
                "#64748B"
            ),
            alignment=TA_CENTER,
            spaceAfter=20,
        )

        heading_style = ParagraphStyle(
            "GeoDashboardHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            textColor=colors.HexColor(
                "#102A43"
            ),
            spaceBefore=10,
            spaceAfter=10,
        )

        body_style = ParagraphStyle(
            "GeoDashboardBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=16,
            textColor=colors.HexColor(
                "#334155"
            ),
        )

        small_style = ParagraphStyle(
            "GeoDashboardSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=12,
            textColor=colors.HexColor(
                "#64748B"
            ),
            alignment=TA_CENTER,
        )

        story = []

        # =================================================
        # EN-TÊTE
        # =================================================

        story.append(
            Paragraph(
                "GeoDashboard",
                title_style,
            )
        )

        story.append(
            Paragraph(
                "Rapport d'analyse territoriale",
                subtitle_style,
            )
        )

        story.append(
            Paragraph(
                str(territory_name).upper(),
                heading_style,
            )
        )

        generation_date = (
            datetime.now()
            .strftime(
                "%d/%m/%Y à %H:%M"
            )
        )

        story.append(
            Paragraph(
                f"Rapport généré le {generation_date}",
                body_style,
            )
        )

        story.append(
            Spacer(1, 14)
        )

        # =================================================
        # TERRITOIRE
        # =================================================

        story.append(
            Paragraph(
                "1. Territoire étudié",
                heading_style,
            )
        )

        territory_table = Table(
            [
                [
                    "Territoire",
                    str(
                        territory_name
                    ).upper(),
                ],
                [
                    "Surface",
                    (
                        f"{ReportService._format_number(
                            territory_area
                        )} km²"
                    ),
                ],
                [
                    "CRS",
                    str(
                        territory_layer.crs
                    ),
                ],
            ],
            colWidths=[
                5.5 * cm,
                11 * cm,
            ],
        )

        territory_table.setStyle(
            ReportService._table_style()
        )

        story.append(
            territory_table
        )

        story.append(
            Spacer(1, 18)
        )

        # =================================================
        # ANALYSE
        # =================================================

        story.append(
            Paragraph(
                "2. Analyse spatiale",
                heading_style,
            )
        )

        analysis_data = [
            [
                "Opération",
                str(operation),
            ],
            [
                "Couche de couverture",
                coverage_layer.name,
            ],
            [
                "Équipements analysés",
                str(source_count),
            ],
            [
                "Couche résultat",
                result_layer.name,
            ],
        ]

        if distance is not None:
            analysis_data.append(
                [
                    "Distance",
                    f"{distance} m",
                ]
            )

        analysis_table = Table(
            analysis_data,
            colWidths=[
                5.5 * cm,
                11 * cm,
            ],
        )

        analysis_table.setStyle(
            ReportService._table_style()
        )

        story.append(
            analysis_table
        )

        story.append(
            Spacer(1, 18)
        )

        # =================================================
        # INDICATEURS
        # =================================================

        story.append(
            Paragraph(
                "3. Indicateurs territoriaux",
                heading_style,
            )
        )

        indicators = Table(
            [
                [
                    "Surface du territoire",
                    "Surface couverte",
                    "Surface non couverte",
                    "Taux de couverture",
                ],
                [
                    (
                        f"{ReportService._format_number(
                            territory_area
                        )} km²"
                    ),
                    (
                        f"{ReportService._format_number(
                            covered_area
                        )} km²"
                    ),
                    (
                        f"{ReportService._format_number(
                            uncovered_area
                        )} km²"
                    ),
                    (
                        f"{ReportService._format_number(
                            coverage_rate,
                            1,
                        )} %"
                    ),
                ],
            ],
            colWidths=[
                4.1 * cm,
                4.1 * cm,
                4.1 * cm,
                4.1 * cm,
            ],
        )

        indicators.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#E2E8F0"
                        ),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, 0),
                        8,
                    ),
                    (
                        "FONTSIZE",
                        (0, 1),
                        (-1, 1),
                        12,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor(
                            "#CBD5E1"
                        ),
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                ]
            )
        )

        story.append(
            indicators
        )

        # =================================================
        # CARTE
        # =================================================

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "4. Carte de la couverture territoriale",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                (
                    "Les couleurs de la carte reprennent "
                    "les styles définis dans GeoDashboard. "
                    "Les équipements sont représentés "
                    "au-dessus des zones d'analyse."
                ),
                body_style,
            )
        )

        story.append(
            Spacer(1, 12)
        )

        story.append(
            Image(
                map_buffer,
                width=17 * cm,
                height=11.5 * cm,
            )
        )

        # =================================================
        # INTERPRÉTATION
        # =================================================

        story.append(
            Spacer(1, 18)
        )

        story.append(
            Paragraph(
                "5. Interprétation",
                heading_style,
            )
        )

        if distance is not None:

            interpretation = (
                f"À une distance de "
                f"<b>{distance} mètres</b>, "
                f"la couverture représente "
                f"<b>{ReportService._format_number(
                    covered_area
                )} km²</b> sur les "
                f"<b>{ReportService._format_number(
                    territory_area
                )} km²</b> du territoire de "
                f"<b>{str(territory_name).upper()}</b>. "
                f"Le taux de couverture est de "
                f"<b>{ReportService._format_number(
                    coverage_rate,
                    1,
                )} %</b>."
            )

        else:

            interpretation = (
                f"La surface couverte représente "
                f"<b>{ReportService._format_number(
                    covered_area
                )} km²</b>, soit "
                f"<b>{ReportService._format_number(
                    coverage_rate,
                    1,
                )} %</b> du territoire."
            )

        story.append(
            Paragraph(
                interpretation,
                body_style,
            )
        )

        story.append(
            Spacer(1, 10)
        )

        story.append(
            Paragraph(
                (
                    "La surface non couverte représente "
                    f"<b>{ReportService._format_number(
                        uncovered_area
                    )} km²</b>."
                ),
                body_style,
            )
        )

        # =================================================
        # MÉTHODOLOGIE
        # =================================================

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "6. Méthodologie",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                (
                    "Les calculs sont réalisés en Lambert-93 "
                    "(EPSG:2154). La zone couverte correspond "
                    "à l'intersection entre l'union des buffers "
                    "et le territoire sélectionné. La zone "
                    "non couverte correspond à la différence "
                    "entre le territoire et la zone couverte."
                ),
                body_style,
            )
        )

        story.append(
            Spacer(1, 20)
        )

        story.append(
            Paragraph(
                (
                    "Rapport généré automatiquement "
                    "par GeoDashboard — Version 0.1.0"
                ),
                small_style,
            )
        )

        document.build(
            story
        )

        pdf_buffer.seek(0)

        return pdf_buffer.getvalue()

    # =====================================================
    # STYLE TABLEAU
    # =====================================================

    @staticmethod
    def _table_style() -> TableStyle:

        return TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F1F5F9"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor(
                        "#CBD5E1"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor(
                        "#E2E8F0"
                    ),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )