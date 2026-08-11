"""Service principal des analyses spatiales."""

from __future__ import annotations

from models.layer import Layer
from services.analysis.registry import AnalysisRegistry


class AnalysisService:
    """Exécute les opérations spatiales enregistrées."""

    def __init__(
        self,
        registry: AnalysisRegistry | None = None,
    ) -> None:
        """Initialise le service d'analyse."""

        self.registry = (
            registry
            if registry is not None
            else AnalysisRegistry()
        )

    def available_operations(
        self,
    ) -> list[str]:
        """Retourne les opérations disponibles."""

        return self.registry.names()

    def run(
        self,
        operation_name: str,
        layer: Layer,
        **kwargs,
    ) -> Layer:
        """
        Exécute une opération spatiale enregistrée.

        Parameters
        ----------
        operation_name:
            Nom de l'opération.

        layer:
            Couche source.

        **kwargs:
            Paramètres propres à l'opération.

        Returns
        -------
        Layer
            Couche résultat.
        """

        if layer is None:
            raise ValueError(
                "Une couche source est obligatoire."
            )

        operation = self.registry.get(
            operation_name
        )

        result_layer = operation.execute(
            layer=layer,
            **kwargs,
        )

        if not isinstance(
            result_layer,
            Layer,
        ):
            raise TypeError(
                "Une opération d'analyse doit "
                "retourner un objet Layer."
            )

        return result_layer