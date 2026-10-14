"""Nested TypeScript state objects built only from declared state paths."""

from __future__ import annotations

from dataclasses import dataclass, field

from generator.errors import GeneratorError
from generator.naming import access, prop
from generator.types import TypeMapper


@dataclass
class SLeaf:
    data_type: str
    nullable: bool


@dataclass
class SBranch:
    fields: dict[str, SLeaf | SBranch] = field(default_factory=dict)


def insert_state(root: SBranch, path: str, data_type: str, *, nullable: bool) -> None:
    parts = path.split(".")
    if not parts or any(part == "" for part in parts):
        raise GeneratorError("UNSUPPORTED_STATE", path)
    node: SLeaf | SBranch = root
    for part in parts[:-1]:
        if isinstance(node, SLeaf):
            raise GeneratorError("UNSUPPORTED_STATE", path)
        child = node.fields.get(part)
        if child is None:
            child = SBranch()
            node.fields[part] = child
        elif isinstance(child, SLeaf):
            raise GeneratorError("UNSUPPORTED_STATE", path)
        node = child
    if isinstance(node, SLeaf) or parts[-1] in node.fields:
        raise GeneratorError("UNSUPPORTED_STATE", path)
    node.fields[parts[-1]] = SLeaf(data_type, nullable)


def iter_leaves(node: SBranch, prefix: list[str] | None = None) -> list[list[str]]:
    current = [] if prefix is None else prefix
    found: list[list[str]] = []
    for key, child in node.fields.items():
        path = [*current, key]
        if isinstance(child, SLeaf):
            found.append(path)
        else:
            found.extend(iter_leaves(child, path))
    return found


def render_state_type(node: SBranch | SLeaf, mapper: TypeMapper, brace_indent: int) -> str:
    if isinstance(node, SLeaf):
        return mapper.ts(node.data_type, nullable=node.nullable)
    lines = ["{"]
    inner = brace_indent + 2
    for key, child in node.fields.items():
        rendered = render_state_type(child, mapper, inner)
        lines.append(f"{' ' * inner}{prop(key)}: {rendered};")
    lines.append(f"{' ' * brace_indent}}}")
    return "\n".join(lines)


def render_state_initial(
    node: SBranch | SLeaf,
    mapper: TypeMapper,
    brace_indent: int,
    overrides: dict[str, str] | None = None,
    prefix: tuple[str, ...] = (),
) -> str:
    if isinstance(node, SLeaf):
        key = ".".join(prefix)
        if overrides and key in overrides:
            return overrides[key]
        return mapper.render_initial(node.data_type, node.nullable, brace_indent)
    lines = ["{"]
    inner = brace_indent + 2
    for key, child in node.fields.items():
        rendered = render_state_initial(child, mapper, inner, overrides, (*prefix, key))
        lines.append(f"{' ' * inner}{prop(key)}: {rendered},")
    lines.append(f"{' ' * brace_indent}}}")
    return "\n".join(lines)


def render_update(base: str, updates: list[tuple[list[str], str]], indent: int) -> str:
    if not updates:
        raise GeneratorError("UNSUPPORTED_STATE", "更新が空です")
    groups: dict[str, list[tuple[list[str], str]]] = {}
    for segments, expr in updates:
        if not segments:
            raise GeneratorError("UNSUPPORTED_STATE", "空のパス")
        groups.setdefault(segments[0], []).append((segments[1:], expr))
    inner = indent + 2
    lines = [f"{' ' * indent}{{", f"{' ' * inner}...{base},"]
    for key, group in groups.items():
        leaves = [expr for rest, expr in group if not rest]
        nested = [(rest, expr) for rest, expr in group if rest]
        if leaves and nested:
            raise GeneratorError("UNSUPPORTED_STATE", key)
        if len(leaves) > 1:
            raise GeneratorError("UNSUPPORTED_STATE", key)
        if leaves:
            lines.append(f"{' ' * inner}{prop(key)}: {leaves[0]},")
            continue
        child = render_update(access(base, key), nested, inner)
        lines.append(f"{' ' * inner}{prop(key)}: {child.lstrip()},")
    lines.append(f"{' ' * indent}}}")
    return "\n".join(lines)


def render_prop_case(
    action: str,
    state_name: str,
    action_type: str,
    updates: list[tuple[list[str], str]],
) -> str:
    rendered = render_update("state", updates, 2)
    lines = rendered.split("\n")
    lines[0] = lines[0].replace("{", "({", 1)
    lines[-1] = lines[-1] + "))"
    handler = f"  on({action}, (state: {state_name}, action: {action_type}): {state_name} =>\n"
    return handler + "\n".join(lines)


def render_success_case(
    action: str,
    state_name: str,
    response_name: str,
    updates: list[tuple[list[str], str]],
) -> str:
    rendered = render_update("state", updates, 2)
    lines = rendered.split("\n")
    lines[0] = lines[0].replace("{", "({", 1)
    lines[-1] = lines[-1] + "))"
    handler = (
        f"  on({action}, "
        f"(state: {state_name}, action: {{ body: {response_name} }}): {state_name} =>\n"
    )
    return handler + "\n".join(lines)
