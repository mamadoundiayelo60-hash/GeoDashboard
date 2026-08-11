"""Table attributaire de GeoDashboard."""

from __future__ import annotations

import streamlit as st

from models.layer import Layer
from models.selection import Selection
from services.selection_manager import SelectionManager


def render_attribute_table(
    layer: Layer,
    selection_manager: SelectionManager,
) -> None:
    """Affiche la table attributaire interactive d'une couche."""

    st.subheader(
        f"📊 Table attributaire : {layer.name}"
    )

    # =====================================================
    # DONNÉES
    # =====================================================

    source_gdf = (
        layer.geodataframe
        .copy()
        .reset_index(drop=True)
    )

    source_gdf["__feature_index"] = range(
        len(source_gdf)
    )

    geometry_column = (
        source_gdf.geometry.name
    )

    dataframe = source_gdf.copy()

    if geometry_column in dataframe.columns:
        dataframe = dataframe.drop(
            columns=[geometry_column]
        )

    # =====================================================
    # RECHERCHE
    # =====================================================

    search = st.text_input(
        "🔍 Rechercher",
        placeholder=(
            "Nom de commune, voie, code, valeur..."
        ),
        key=f"search_{layer.name}",
    )

    filtered_dataframe = dataframe.copy()

    if search:

        searchable_columns = [
            column
            for column
            in filtered_dataframe.columns
            if column != "__feature_index"
        ]

        mask = (
            filtered_dataframe[
                searchable_columns
            ]
            .astype(str)
            .apply(
                lambda column:
                column.str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False,
                )
            )
            .any(axis=1)
        )

        filtered_dataframe = (
            filtered_dataframe
            .loc[mask]
            .copy()
        )

    # =====================================================
    # ÉTAT DE LA SÉLECTION
    # =====================================================

    current_selection = (
        selection_manager.current
    )

    selection_for_this_layer = (
        current_selection is not None
        and current_selection.layer_name
        == layer.name
    )

    # =====================================================
    # BARRE D'INFORMATION
    # =====================================================

    info_col, selection_col = st.columns(
        [3, 2]
    )

    with info_col:
        st.caption(
            f"{len(filtered_dataframe):,} "
            "enregistrement(s)"
        )

    with selection_col:

        if selection_for_this_layer:
            st.caption(
                "1 entité sélectionnée"
            )
        else:
            st.caption(
                "Aucune sélection"
            )

    # =====================================================
    # TABLE
    # =====================================================

    display_dataframe = (
        filtered_dataframe.drop(
            columns=["__feature_index"],
            errors="ignore",
        )
    )

    event = st.dataframe(
        display_dataframe,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key=f"attribute_table_{layer.name}",
    )

    # =====================================================
    # TABLE -> SELECTION MANAGER
    # =====================================================

    selected_rows = []

    if event is not None:

        try:
            selected_rows = (
                event.selection.rows
            )
        except (
            AttributeError,
            TypeError,
        ):
            selected_rows = []

    if selected_rows:

        visible_row_index = int(
            selected_rows[0]
        )

        if (
            0 <= visible_row_index
            < len(filtered_dataframe)
        ):

            selected_record = (
                filtered_dataframe.iloc[
                    visible_row_index
                ]
            )

            feature_index = int(
                selected_record[
                    "__feature_index"
                ]
            )

            attributes = {
                column: value
                for column, value
                in selected_record.items()
                if column != "__feature_index"
            }

            current_selection = (
                selection_manager.current
            )

            selection_changed = (
                current_selection is None
                or current_selection.layer_name
                != layer.name
                or current_selection.feature_index
                != feature_index
            )

            # IMPORTANT :
            # on ne désélectionne PAS ici si
            # la ligne est déjà sélectionnée.
            #
            # st.dataframe conserve son événement
            # entre les reruns et cela provoquerait
            # une boucle sélection/désélection.
            if selection_changed:

                selection_manager.select(
                    Selection(
                        layer_name=layer.name,
                        feature_index=(
                            feature_index
                        ),
                        attributes=attributes,
                    )
                )

                st.rerun()

    # =====================================================
    # INFORMATIONS SUR LA SÉLECTION
    # =====================================================

    current_selection = (
        selection_manager.current
    )

    if (
        current_selection is not None
        and current_selection.layer_name
        == layer.name
    ):

        feature_index = (
            current_selection.feature_index
        )

        selected_values = (
            filtered_dataframe[
                "__feature_index"
            ].tolist()
        )

        if feature_index in selected_values:

            message_col, clear_col = (
                st.columns([4, 1])
            )

            with message_col:
                st.success(
                    f"Entité "
                    f"{feature_index + 1} "
                    "sélectionnée."
                )

            with clear_col:

                if st.button(
                    "Désélectionner",
                    key=(
                        f"clear_table_"
                        f"{layer.name}"
                    ),
                    use_container_width=True,
                ):
                    selection_manager.clear()

                    # On recrée la table au prochain
                    # passage pour nettoyer aussi son
                    # état de sélection visuelle.
                    table_key = (
                        f"attribute_table_"
                        f"{layer.name}"
                    )

                    if table_key in st.session_state:
                        del st.session_state[
                            table_key
                        ]

                    st.rerun()

        else:

            st.info(
                "L'entité sélectionnée "
                "est masquée par le filtre."
            )

    # =====================================================
    # EXPORT CSV
    # =====================================================

    csv_data = (
        display_dataframe
        .to_csv(
            index=False,
        )
        .encode("utf-8-sig")
    )

    st.download_button(
        "Télécharger la table en CSV",
        data=csv_data,
        file_name=(
            f"{layer.name}_attributs.csv"
        ),
        mime="text/csv",
        use_container_width=True,
        key=f"csv_{layer.name}",
    )