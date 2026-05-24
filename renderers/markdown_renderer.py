from typing import Any
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from renderers.base_renderer import BaseRenderer
from utils.exceptions import RenderError


def _make_jinja_env(template_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


class DriverMarkdownRenderer(BaseRenderer):
    """Renders a driver record using driver_template.j2."""

    def __init__(self, template_dir: str) -> None:
        self._env = _make_jinja_env(template_dir)

    def render(self, record: dict[str, Any]) -> str:
        try:
            tmpl = self._env.get_template("driver_template.j2")
            return tmpl.render(**record)
        except TemplateNotFound as exc:
            raise RenderError(f"Template not found: {exc}") from exc
        except Exception as exc:
            raise RenderError(f"Driver render failed: {exc}") from exc

    def get_entity_id(self, record: dict[str, Any]) -> str:
        return record["driver_id"]


class IncidentMarkdownRenderer(BaseRenderer):
    """Renders an incident record using incident_template.j2."""

    def __init__(self, template_dir: str) -> None:
        self._env = _make_jinja_env(template_dir)

    def render(self, record: dict[str, Any]) -> str:
        try:
            tmpl = self._env.get_template("incident_template.j2")
            return tmpl.render(**record)
        except TemplateNotFound as exc:
            raise RenderError(f"Template not found: {exc}") from exc
        except Exception as exc:
            raise RenderError(f"Incident render failed: {exc}") from exc

    def get_entity_id(self, record: dict[str, Any]) -> str:
        return record["incident_id"]
