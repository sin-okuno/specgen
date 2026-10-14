"""Map specification data types to TypeScript. Unknown types are rejected."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from generator.errors import GeneratorError
from generator.naming import field_decl, pascal, prop

PRIMITIVES = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "date": "string",
    "datetime": "string",
}
_ZEROS = {"string": '""', "number": "0", "boolean": "false"}


def split_type(data_type: str) -> tuple[str, bool]:
    if data_type.endswith("[]"):
        inner = data_type[:-2]
        if not inner or inner.endswith("[]"):
            raise GeneratorError("UNSUPPORTED_TYPE", data_type)
        return inner, True
    return data_type, False


class TypeMapper:
    def __init__(self, catalog: Sequence[str], fields: Sequence[Mapping[str, str]]) -> None:
        self.names = set(catalog)
        self.fields: dict[str, list[Mapping[str, str]]] = {name: [] for name in catalog}
        for row in fields:
            owner = row["type_name"]
            if owner not in self.fields:
                raise GeneratorError("UNSUPPORTED_TYPE", owner)
            self.fields[owner].append(row)

    def ts(self, data_type: str, *, nullable: bool = False) -> str:
        base, is_array = split_type(data_type)
        if base in PRIMITIVES:
            rendered = PRIMITIVES[base]
        elif base in self.names:
            rendered = pascal(base)
        else:
            raise GeneratorError("UNSUPPORTED_TYPE", data_type)
        if is_array:
            rendered += "[]"
        if nullable:
            rendered += " | null"
        return rendered

    def render_initial(
        self,
        data_type: str,
        nullable: bool,
        brace_indent: int,
        stack: tuple[str, ...] = (),
    ) -> str:
        if nullable:
            return "null"
        base, is_array = split_type(data_type)
        if is_array:
            self.ts(data_type)
            return "[]"
        if base in PRIMITIVES:
            return _ZEROS[PRIMITIVES[base]]
        if base not in self.names:
            raise GeneratorError("UNSUPPORTED_TYPE", data_type)
        if base in stack:
            raise GeneratorError("UNSUPPORTED_TYPE", f"循環型: {data_type}")
        lines = ["{"]
        inner = brace_indent + 2
        for row in self.fields[base]:
            if row["required"] == "No":
                continue
            if row["nullable"] == "Yes":
                value = "null"
            else:
                value = self.render_initial(
                    row["data_type"],
                    False,
                    inner,
                    stack + (base,),
                )
            lines.append(f"{' ' * inner}{prop(row['field'])}: {value},")
        lines.append(f"{' ' * brace_indent}}}")
        return "\n".join(lines)

    def interface_fields(self, type_name: str) -> list[str]:
        blocks: list[str] = []
        for row in self.fields[type_name]:
            optional = row["required"] == "No"
            nullable = row["nullable"] == "Yes"
            rendered = self.ts(row["data_type"], nullable=nullable)
            blocks.append(f"  {field_decl(row['field'], rendered, optional=optional)}")
        return blocks
