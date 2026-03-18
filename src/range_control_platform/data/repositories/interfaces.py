from typing import Protocol


class ReferenceDataRepository(Protocol):
    def load_reference_data(self) -> dict:
        """Return reference data in the shape expected by the app."""
