from pathlib import Path
from typing import Any

import structlog

from renderers.base_renderer import BaseRenderer
from utils.exceptions import RenderError

log = structlog.get_logger(__name__)


class MarkdownService:
    """Renders a record to markdown and saves it to the output directory."""

    def __init__(self, renderer: BaseRenderer, output_dir: str) -> None:
        self._renderer = renderer
        self._output_dir = Path(output_dir)

    def render(self, record: dict[str, Any]) -> str:
        """Render record to a markdown string."""
        return self._renderer.render(record)

    def save(self, entity_id: str, content: str) -> Path:
        """Write markdown content to disk and return the file path."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        file_path = self._output_dir / f"{entity_id}.md"
        try:
            file_path.write_text(content, encoding="utf-8")
            log.info("markdown.saved", entity_id=entity_id, path=str(file_path))
            return file_path
        except Exception as exc:
            raise RenderError(f"Failed to write markdown for {entity_id}: {exc}") from exc
