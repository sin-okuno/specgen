"""Load one Screen Model JSON file and reject it unless validation passes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from generator.errors import GeneratorError

_TOOLCHAIN = Path(__file__).resolve().parents[1] / "toolchain"
_SCHEMA_PATH = _TOOLCHAIN / "screen-model.schema.json"


def _validate_model(document: dict[str, Any]) -> list[dict[str, Any]]:
    toolchain = str(_TOOLCHAIN)
    if toolchain not in sys.path:
        sys.path.insert(0, toolchain)
    from model_validator import validate_model

    return validate_model(document)


def load_model(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GeneratorError("INVALID_JSON", f"ファイルがありません: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GeneratorError("INVALID_JSON", str(exc)) from exc
    if not isinstance(document, dict):
        raise GeneratorError("SCHEMA", "Screen Model のルートはオブジェクトです")
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path))
    if errors:
        raise GeneratorError("SCHEMA", _schema_message(errors[0]))
    model_errors = _validate_model(document)
    if model_errors:
        detail = "; ".join(f"{item['code']}: {item['message']}" for item in model_errors)
        raise GeneratorError("MODEL", detail)
    return document


def _schema_message(error: ValidationError) -> str:
    location = "/".join(str(part) for part in error.absolute_path)
    if location:
        return f"{location}: {error.message}"
    return error.message
