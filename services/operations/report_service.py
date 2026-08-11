"""Service de génération des rapports GeoDashboard."""

from __future__ import annotations

from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from models.layer import Layer


class ReportService:
    """Génère les rapports PDF de GeoDashboard."""

    # =====================================================
    # OUTILS
    # =====================================================

    @staticmethod
    def _format_number(
        value: float,
        decimals: int = 2,
    ) -> str:
        """Formate un nombre au format français."""

        return (
            f"{value:,.{decimals}f}"
            .replace(",", " ")
            .replace(".", ",")
        )

    @staticmethod
    def _surface_km2(
        layer: Layer,
    ) -> float:
        """
        Calcule la surface d'une couche en km².

        La couche est reprojetée en Lambert-93
        avant le calcul.
        """

        gdf = layer.geodataframe

        if (
            gdf is None
            or gdf.empty
            or gdf.crs is None
        ):
            return 0.0

        metric_gdf = gdf.to_crs(
            "EPSG:2154"
        )

        return float(
            metric_gdf.geometry.area.sum()
            / 1_000_000
        )

    # =====================================================
    # RAPPORT
    # =====================================================

    @staticmethod
    def generate_analysis_report(
        territory_layer: Layer,
        result_layer: Layer,
        result_info: dict,
    ) -> bytes:
        """
        Génère un rapport PDF à partir du dernier
        résultat d'analyse GeoDashboard.
        """

        if territory_layer is None:
            raise ValueError(
                "Le territoire d'analyse est obligatoire."
            )

        if result_layer is None:
            raise ValueError(
                "La couche résultat est obligatoire."
            )

        # =================================================
        # INFORMATIONS
        # =================================================

        territory_name = (
            result_info.get("territory_name")
            or result_info.get("commune")
            or territory_layer.name
        )

        operation = result_info.get(
            "operation",
            "Analyse spatiale",
        )

        source_layer_name = result_info.get(
            "source_layer",
            "Non renseignée",
        )

        distance = result_info.get(
            "distance"
        )

        source_count = result_info.get(
            "source_feature_count"
        )

        if source_count is None:
            source_count = result_info.get(
                "source_count",
                result_layer.feature_count,
            )

        # =================================================
        # SURFACES
        # =================================================

        territory_area = (
            ReportService._surface_km2(
                territory_layer
            )
        )

        # Pour un buffer, la surface brute peut dépasser
        # le territoire. Pour le rapport territorial,
        # on calcule l'intersection avec le territoire.
        result_gdf = (
            result_layer.geodataframe
            .copy()
        )

        territory_gdf = (
            territory_layer.geodataframe
            .copy()
        )

        covered_area = 0.0

        if (
            not result_gdf.empty
            and not territory_gdf.empty
            and result_gdf.crs is not None
            and territory_gdf.crs is not None
        ):

            result_metric = (
                result_gdf.to_crs(
                    "EPSG:2154"
                )
            )

            territory_metric = (
                territory_gdf.to_crs(
                    "EPSG:2154"
                )
            )

            try:
                result_geometry = (
                    result_metric.geometry
                    .union_all()
                )
            except AttributeError:
                result_geometry = (
                    result_metric.geometry
                    .unary_union
                )

            try:
                territory_geometry = (
                    territory_metric.geometry
                    .union_all()
                )
            except AttributeError:
                territory_geometry = (
                    territory_metric.geometry
                    .unary_union
                )

            intersection = (
                territory_geometry.intersection(
                    result_geometry
                )
            )

            if not intersection.is_empty:
                covered_area = (
                    intersection.area
                    / 1_000_000
                )

        uncovered_area = max(
            territory_area - covered_area,
            0.0,
        )

        if territory_area > 0:
            coverage_rate = (
                covered_area
                / territory_area
                * 100
            )
        else:
            coverage_rate = 0.0

        # =================================================
        # BUFFER PDF
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

        # =================================================
        # STYLES
        # =================================================

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
            leading=16,
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
            .strftime("%d/%m/%Y à %H:%M")
        )

        story.append(
            Paragraph(
                f"Rapport généré le "
                f"{generation_date}",
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                14,
            )
        )

        # =================================================
        # 1. TERRITOIRE
        # =================================================

        story.append(
            Paragraph(
                "1. Territoire étudié",
                heading_style,
            )
        )

        territory_data = [
            [
                "Territoire",
                str(territory_name).upper(),
            ],
            [
                "Surface",
                (
                    f"{ReportService._format_number(territory_area)} "
                    f"km²"
                ),
            ],
            [
                "CRS",
                territory_layer.crs,
            ],
        ]

        territory_table = Table(
            territory_data,
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
            Spacer(
                1,
                18,
            )
        )

        # =================================================
        # 2. ANALYSE
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
                "Couche source",
                str(source_layer_name),
            ],
            [
                "Entités analysées",
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
            Spacer(
                1,
                18,
            )
        )

        # =================================================
        # 3. INDICATEURS
        # =================================================

        story.append(
            Paragraph(
                "3. Indicateurs territoriaux",
                heading_style,
            )
        )

        indicators = [
            [
                "Surface du territoire",
                "Surface couverte",
                "Surface non couverte",
                "Taux de couverture",
            ],
            [
                (
                    f"{ReportService._format_number(territory_area)} "
                    f"km²"
                ),
                (
                    f"{ReportService._format_number(covered_area)} "
                    f"km²"
                ),
                (
                    f"{ReportService._format_number(uncovered_area)} "
                    f"km²"
                ),
                (
                    f"{ReportService._format_number(coverage_rate, 1)} %"
                ),
            ],
        ]

        indicators_table = Table(
            indicators,
            colWidths=[
                4.1 * cm,
                4.1 * cm,
                4.1 * cm,
                4.1 * cm,
            ],
        )

        indicators_table.setStyle(
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
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#334155"
                        ),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (0, 1),
                        (-1, 1),
                        "Helvetica-Bold",
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
            indicators_table
        )

        story.append(
            Spacer(
                1,
                20,
            )
        )

        # =================================================
        # 4. INTERPRÉTATION
        # =================================================

        story.append(
            Paragraph(
                "4. Interprétation",
                heading_style,
            )
        )

        if distance is not None:

            interpretation = (
                f"À une distance de "
                f"<b>{distance} mètres</b>, "
                f"la zone étudiée couvre "
                f"<b>{ReportService._format_number(covered_area)} km²</b> "
                f"sur les "
                f"<b>{ReportService._format_number(territory_area)} km²</b> "
                f"du territoire de "
                f"<b>{str(territory_name).upper()}</b>. "
                f"Le taux de couverture territorial est donc de "
                f"<b>{ReportService._format_number(coverage_rate, 1)} %</b>."
            )

        else:

            interpretation = (
                f"La surface couverte représente "
                f"<b>{ReportService._format_number(covered_area)} km²</b> "
                f"sur les "
                f"<b>{ReportService._format_number(territory_area)} km²</b> "
                f"du territoire étudié, soit "
                f"<b>{ReportService._format_number(coverage_rate, 1)} %</b>."
            )

        story.append(
            Paragraph(
                interpretation,
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                10,
            )
        )

        story.append(
            Paragraph(
                (
                    f"La surface non couverte représente "
                    f"<b>{ReportService._format_number(uncovered_area)} "
                    f"km²</b>."
                ),
                body_style,
            )
        )

        # =================================================
        # PAGE MÉTHODOLOGIE
        # =================================================

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "Méthodologie",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                (
                    "Les calculs surfaciques sont réalisés dans "
                    "le système de coordonnées projeté "
                    "Lambert-93 (EPSG:2154). "
                    "La couverture territoriale correspond à "
                    "l'intersection entre la zone produite par "
                    "l'analyse spatiale et le territoire sélectionné."
                ),
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                20,
            )
        )

        story.append(
            Paragraph(
                (
                    "Ce rapport a été généré automatiquement "
                    "par GeoDashboard."
                ),
                small_style,
            )
        )

        story.append(
            Paragraph(
                "Version 0.1.0",
                small_style,
            )
        )

        # =================================================
        # GÉNÉRATION
        # =================================================

        document.build(
            story
        )

        pdf_buffer.seek(0)

        return pdf_buffer.getvalue()

    # =====================================================
    # STYLE TABLEAUX
    # =====================================================

    @staticmethod
    def _table_style() -> TableStyle:
        """Style commun aux tableaux du rapport."""

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
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#334155"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
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