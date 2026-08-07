from models.selection import Selection


class SelectionManager:
    """Gère la sélection active."""

    def __init__(self) -> None:
        self.current: Selection | None = None

    def clear(self) -> None:
        self.current = None

    def select(
        self,
        selection: Selection,
    ) -> None:
        self.current = selection

    def has_selection(self) -> bool:
        return self.current is not None