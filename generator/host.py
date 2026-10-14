"""Route the generated screens from their screen URLs."""

from __future__ import annotations

import re
from typing import Any

from generator.errors import GeneratorError
from generator.naming import file_slug, screen_stem
from generator.renderer import TemplateRenderer

_SEGMENT = re.compile(r":?[A-Za-z_][A-Za-z0-9_]*\Z")
_HEADER = "\n".join(
    (
        "// Generated from Screen Model schema 0.3. Phase 1 scaffold.",
        "// 画面URLをルートにする。",
        "",
    )
)


def render_host(
    documents: list[dict[str, Any]],
    renderer: TemplateRenderer | None = None,
) -> list[tuple[str, str]]:
    if not documents:
        raise GeneratorError("UNSUPPORTED_ROUTE", "host")
    active = renderer or TemplateRenderer()
    routes = _routes(documents)
    context = {"header": _HEADER, "routes": routes}
    return [
        ("app/app.component.ts", active.render("app.component.ts.j2", context)),
        ("app/app.component.html", active.render("app.component.html.j2", context)),
        ("app/app.module.ts", active.render("app.module.ts.j2", context)),
    ]


def _routes(documents: list[dict[str, Any]]) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for document in documents:
        meta = document["metadata"]
        url = str(meta["url"])
        path = _angular_path(url)
        stem = screen_stem(str(meta["screen_name"]))
        slug = file_slug(stem)
        previous = seen.get(path)
        if previous is not None:
            raise GeneratorError("UNSUPPORTED_ROUTE", path)
        seen[path] = slug
        routes.append(
            {
                "path": path,
                "slug": slug,
                "module_class": f"{stem}Module",
                "screen_class": f"{stem}ScreenComponent",
            }
        )
    return sorted(routes, key=lambda route: _order(route["path"]))


def _angular_path(url: str) -> str:
    if (
        not url.startswith("/")
        or url.endswith("/")
        or any(char.isspace() for char in url)
        or "{" in url
        or "}" in url
    ):
        raise GeneratorError("UNSUPPORTED_ROUTE", url)
    parts = url[1:].split("/")
    if not parts or any(_SEGMENT.fullmatch(part) is None for part in parts):
        raise GeneratorError("UNSUPPORTED_ROUTE", url)
    return "/".join(parts)


def _order(path: str) -> tuple[int, tuple[tuple[bool, str], ...]]:
    parts = path.split("/")
    return (-len(parts), tuple((part.startswith(":"), part) for part in parts))
