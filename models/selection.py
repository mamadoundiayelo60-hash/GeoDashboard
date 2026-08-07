from dataclasses import dataclass
from typing import Any


@dataclass
class Selection:
    """Représente une entité sélectionnée."""

    layer_name: str
    feature_index: int
    attributes: dict[str, Any]