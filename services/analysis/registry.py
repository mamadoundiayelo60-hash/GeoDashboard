"""Registre des opérations d'analyse spatiale."""

from __future__ import annotations

from services.operations.operation import Operation
from services.operations.buffer_operation import BufferOperation
from services.operations.intersection_operation import (
    IntersectionOperation,
)
from services.operations.spatial_selection_operation import (
    SpatialSelectionOperation,
)
from services.operations.coverage_operation import (
    CoverageOperation,
)


class AnalysisRegistry:
    """Registre central des opérations spatiales."""

    def __init__(
        self,
    ) -> None:
        """Initialise les opérations disponibles."""

        self._operations: dict[
            str,
            Operation,
        ] = {}

        self.register(
            BufferOperation()
        )

        self.register(
            IntersectionOperation()
        )

        self.register(
            SpatialSelectionOperation()
        )

        self.register(
            CoverageOperation()
        )

    def register(
        self,
        operation: Operation,
    ) -> None:
        """Enregistre une opération."""

        self._operations[
            operation.name
        ] = operation

    def get(
        self,
        name: str,
    ) -> Operation:
        """Retourne une opération."""

        if name not in self._operations:

            raise ValueError(
                f"Opération inconnue : {name}"
            )

        return self._operations[
            name
        ]

    def names(
        self,
    ) -> list[str]:
        """Retourne les noms des opérations."""

        return list(
            self._operations.keys()
        )

    def operations(
        self,
    ) -> list[Operation]:
        """Retourne toutes les opérations."""

        return list(
            self._operations.values()
        )