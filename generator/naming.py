"""Angular identifier rules. Screen names in Japanese are never used as code names."""

from __future__ import annotations

import json
import re

from generator.errors import GeneratorError

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_TOKEN = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
_PURPOSE_ROLE = {
    "一覧取得": "List",
    "状態候補取得": "StatusOptions",
    "製品登録": "Registration",
    "詳細取得": "Detail",
    "製品更新": "Update",
}


def pascal(value: str) -> str:
    parts = _TOKEN.findall(value)
    if not parts:
        raise GeneratorError("UNSUPPORTED_NAME", value)
    chunks: list[str] = []
    for part in parts:
        if part.isdigit():
            chunks.append(part)
        else:
            chunks.append(part[:1].upper() + part[1:].lower())
    result = "".join(chunks)
    if not IDENT.fullmatch(result):
        raise GeneratorError("UNSUPPORTED_NAME", value)
    return result


def camel(value: str) -> str:
    text = pascal(value)
    return text[:1].lower() + text[1:]


_SCREEN_STEM = {
    "製品一覧": "ProductList",
    "製品登録": "ProductRegistration",
    "製品更新": "ProductUpdate",
    "製品詳細": "ProductDetail",
}


def screen_stem(screen_name: str) -> str:
    stem = _SCREEN_STEM.get(screen_name)
    if stem is None:
        raise GeneratorError("UNSUPPORTED_NAME", f"未対応の画面名: {screen_name}")
    return stem


def action_label(stem: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", stem)


def api_type_stem(endpoint: str, purpose: str) -> str:
    role = _PURPOSE_ROLE.get(purpose)
    if role is None:
        raise GeneratorError("UNSUPPORTED_NAME", f"未対応のAPI用途: {purpose}")
    return f"{_resource_name(endpoint)}{role}"


def _resource_name(endpoint: str) -> str:
    parts = [
        part
        for part in endpoint.strip("/").split("/")
        if part and not (part.startswith("{") and part.endswith("}"))
    ]
    if parts and parts[0].lower() == "api":
        parts = parts[1:]
    if not parts:
        raise GeneratorError("UNSUPPORTED_NAME", endpoint)
    word = parts[0]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        word = word[:-1]
    return pascal(word)


def file_slug(value: str) -> str:
    text = pascal(value)
    slug = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)
    slug = re.sub(r"([A-Za-z])(\d)", r"\1-\2", slug)
    return slug.lower()


def prop(name: str) -> str:
    if IDENT.fullmatch(name):
        return name
    return json.dumps(name, ensure_ascii=False)


def member(name: str) -> str:
    if IDENT.fullmatch(name):
        return f".{name}"
    return f"[{json.dumps(name, ensure_ascii=False)}]"


def access(base: str, name: str) -> str:
    if IDENT.fullmatch(name):
        return f"{base}.{name}"
    return f"{base}[{json.dumps(name, ensure_ascii=False)}]"


def field_decl(name: str, ts_type: str, *, optional: bool) -> str:
    mark = "?" if optional else ""
    return f"{prop(name)}{mark}: {ts_type};"
