"""Command line for the phase 1 screen generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generator.engine import generate_to, host_to, load_plan
from generator.errors import GeneratorError
from generator.writer import WriteResult


def main(argv: list[str] | None = None) -> int:
    _utf8_stdio()
    parser = argparse.ArgumentParser(prog="generator.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="list files that would be generated")
    plan.add_argument("--model", required=True, type=Path)

    generate = sub.add_parser("generate", help="render Angular files from a Screen Model")
    generate.add_argument("--model", required=True, type=Path)
    generate.add_argument("--output", required=True, type=Path)
    generate.add_argument("--dry-run", action="store_true")

    host = sub.add_parser("host", help="route generated screens from their URLs")
    host.add_argument("--model", required=True, action="append", type=Path)
    host.add_argument("--output", required=True, type=Path)
    host.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            _print_plan(args.model)
        elif args.command == "host":
            _print_results(
                host_to(args.model, args.output, dry_run=args.dry_run),
                args.output,
                dry_run=args.dry_run,
            )
        else:
            _print_generate(args.model, args.output, dry_run=args.dry_run)
    except GeneratorError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _print_plan(model: Path) -> None:
    planned = load_plan(model)
    print(f"screen_id: {planned.screen_id}")
    print(f"screen_name: {planned.screen_name}")
    for item in planned.files:
        depends = ", ".join(item.depends) if item.depends else "-"
        print(item.relative_path)
        print(f"  template: {item.template}")
        print(f"  depends: {depends}")


def _print_generate(model: Path, output: Path, *, dry_run: bool) -> None:
    _print_results(generate_to(model, output, dry_run=dry_run), output, dry_run=dry_run)


def _print_results(results: list[WriteResult], output: Path, *, dry_run: bool = False) -> None:
    for item in results:
        display = (output / item.relative_path).as_posix()
        print(f"{item.status} {display}")
        if dry_run:
            print(item.content, end="" if item.content.endswith("\n") else "\n")
            print("---")
    print(f"files: {len(results)}")


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            return


if __name__ == "__main__":
    raise SystemExit(main())
