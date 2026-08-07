"""Gestionnaire des couches géographiques."""

from __future__ import annotations

from models.layer import Layer


class LayerManager:
    """Stocke et manipule les couches du projet."""

    def __init__(self) -> None:
        self.layers: list[Layer] = []

    def add(self, layer: Layer) -> None:
        """Ajoute une couche."""

        if self.get(layer.name) is not None:
            raise ValueError(
                f"La couche {layer.name!r} existe déjà."
            )

        self.layers.append(layer)

    def remove(self, name: str) -> bool:
        """Supprime une couche et retourne True si elle existait."""

        initial_count = len(self.layers)

        self.layers = [
            layer
            for layer in self.layers
            if layer.name != name
        ]

        return len(self.layers) < initial_count

    def get(self, name: str) -> Layer | None:
        """Retourne une couche par son nom."""

        for layer in self.layers:
            if layer.name == name:
                return layer

        return None

    def clear(self) -> None:
        """Supprime toutes les couches."""

        self.layers.clear()

    def count(self) -> int:
        """Retourne le nombre de couches."""

        return len(self.layers)

    def list(self) -> list[Layer]:
        """Retourne une copie de la liste des couches."""

        return list(self.layers)