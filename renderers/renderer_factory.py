from renderers.base_renderer import BaseRenderer
from renderers.markdown_renderer import DriverMarkdownRenderer, IncidentMarkdownRenderer
from utils.constants import ENTITY_DRIVER, ENTITY_INCIDENT


class RendererFactory:
    """Creates the right renderer for a given entity type.

    Adding a new entity only requires registering it here — no other code changes.
    """

    def __init__(self, template_dir: str) -> None:
        self._template_dir = template_dir
        self._registry: dict[str, type[BaseRenderer]] = {
            ENTITY_DRIVER: DriverMarkdownRenderer,
            ENTITY_INCIDENT: IncidentMarkdownRenderer,
        }

    def create(self, entity_type: str) -> BaseRenderer:
        cls = self._registry.get(entity_type)
        if cls is None:
            raise ValueError(f"No renderer registered for entity type: {entity_type}")
        return cls(self._template_dir)
