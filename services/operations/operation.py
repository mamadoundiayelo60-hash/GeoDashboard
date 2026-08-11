"""Classe de base des opérations d'analyse spatiale."""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.layer import Layer


class Operation(ABC):
    """Classe abstraite représentant une analyse spatiale."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom de l'opération."""
        ...

    @property
    def description(self) -> str:
        """Description de l'opération."""
        return ""

    @abstractmethod
    def execute(
        self,
        layer: Layer,
        **kwargs,
    ) -> Layer:
        """
        Exécute l'opération et retourne une nouvelle couche.
        """
        ...