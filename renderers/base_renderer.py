from abc import ABC, abstractmethod
from typing import Any


class BaseRenderer(ABC):
    """Contract for all markdown renderers.

    Each renderer knows how to turn a record dict into a markdown string.
    """

    @abstractmethod
    def render(self, record: dict[str, Any]) -> str:
        """Render a record dict into a markdown string."""

    @abstractmethod
    def get_entity_id(self, record: dict[str, Any]) -> str:
        """Extract the unique entity ID from a record."""
