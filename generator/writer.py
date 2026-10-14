"""Write generated files without leaving the output directory or overwriting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from generator.errors import GeneratorError


@dataclass(frozen=True)
class WriteResult:
    relative_path: str
    status: str
    content: str


def normalize(content: str) -> str:
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return text


class FileWriter:
    def __init__(self, output: Path) -> None:
        self.output = output

    def resolve(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or (len(relative) >= 2 and relative[1] == ":"):
            raise GeneratorError("UNSAFE_PATH", relative)
        root = self.output.resolve()
        target = (root / path).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise GeneratorError("UNSAFE_PATH", relative) from exc
        return target

    def prepare(self, files: list[tuple[str, str]]) -> list[WriteResult]:
        results: list[WriteResult] = []
        for relative, content in files:
            text = normalize(content)
            target = self.resolve(relative)
            if target.is_file() and target.read_bytes() == text.encode("utf-8"):
                status = "UNCHANGED"
            elif target.exists():
                status = "OVERWRITE"
            else:
                status = "CREATE"
            results.append(WriteResult(relative, status, text))
        return results

    def commit(self, results: list[WriteResult]) -> None:
        blocked = [item.relative_path for item in results if item.status == "OVERWRITE"]
        if blocked:
            raise GeneratorError("OVERWRITE", ", ".join(blocked))
        for item in results:
            if item.status == "UNCHANGED":
                continue
            target = self.resolve(item.relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.content.encode("utf-8"))
