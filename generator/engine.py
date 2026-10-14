"""Load, plan, render, and write a screen."""

from __future__ import annotations

from pathlib import Path

from generator.host import render_host
from generator.loader import load_model
from generator.planner import GenerationPlan, build_plan
from generator.renderer import TemplateRenderer
from generator.writer import FileWriter, WriteResult


def load_plan(path: Path) -> GenerationPlan:
    return build_plan(load_model(path))


def render_plan(
    plan: GenerationPlan,
    renderer: TemplateRenderer | None = None,
) -> list[tuple[str, str]]:
    active = renderer or TemplateRenderer()
    return [(item.relative_path, active.render(item.template, item.context)) for item in plan.files]


def generate_to(model: Path, output: Path, *, dry_run: bool = False) -> list[WriteResult]:
    return _write(render_plan(load_plan(model)), output, dry_run=dry_run)


def host_to(models: list[Path], output: Path, *, dry_run: bool = False) -> list[WriteResult]:
    documents = [load_model(path) for path in models]
    return _write(render_host(documents), output, dry_run=dry_run)


def _write(rendered: list[tuple[str, str]], output: Path, *, dry_run: bool) -> list[WriteResult]:
    writer = FileWriter(output)
    prepared = writer.prepare(rendered)
    if not dry_run:
        writer.commit(prepared)
    return prepared
