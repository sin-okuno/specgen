"""Render planned files with Jinja2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def _ts(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


class TemplateRenderer:
    def __init__(self, template_dir: Path | None = None) -> None:
        directory = template_dir or Path(__file__).resolve().parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(directory),
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )
        self.env.filters["ts"] = _ts

    def render(self, template: str, context: dict[str, Any]) -> str:
        return self.env.get_template(template).render(**context)
