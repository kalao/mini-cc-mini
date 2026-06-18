from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .tool import ToolResult


_read_files: set[str] = set()


def _abs_path(file_path: str) -> tuple[Path | None, ToolResult | None]:
    path = Path(file_path).expanduser()
    if not path.is_absolute():
        return None, ToolResult(f"Error: file_path must be absolute: {file_path}", True)
    return path, None


class ReadTool:
    name = "Read"
    description = "Read a UTF-8 text file. file_path must be an absolute path."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "offset": {"type": "integer", "default": 0},
            "limit": {"type": "integer", "default": 2000},
        },
        "required": ["file_path"],
    }

    def is_read_only(self) -> bool:
        return True

    def to_schema(self) -> dict[str, Any]:
        return _tool_schema(self)

    def execute(self, file_path: str, offset: int = 0, limit: int = 2000) -> ToolResult:
        path, error = _abs_path(file_path)
        if error:
            return error
        assert path is not None
        if not path.exists():
            return ToolResult(f"Error: file not found: {file_path}", True)
        if not path.is_file():
            return ToolResult(f"Error: not a file: {file_path}", True)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return ToolResult(f"Error reading file: {exc}", True)

        _read_files.add(str(path))
        _read_files.add(str(path.resolve()))

        lines = content.splitlines(keepends=True)
        sliced = lines[offset : offset + limit]
        numbered = "".join(f"{offset + idx + 1}\t{line}" for idx, line in enumerate(sliced))
        if len(lines) > offset + limit:
            numbered += f"\n... ({len(lines) - offset - limit} more lines)"
        return ToolResult(numbered or "(empty file)")


class EditTool:
    name = "Edit"
    description = "Replace an exact string in an existing file. Read the file first."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "old_string": {"type": "string"},
            "new_string": {"type": "string"},
            "replace_all": {"type": "boolean", "default": False},
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def is_read_only(self) -> bool:
        return False

    def to_schema(self) -> dict[str, Any]:
        return _tool_schema(self)

    def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> ToolResult:
        path, error = _abs_path(file_path)
        if error:
            return error
        assert path is not None
        if not path.exists():
            return ToolResult(f"Error: file not found: {file_path}", True)
        if str(path) not in _read_files and str(path.resolve()) not in _read_files:
            return ToolResult(f"Error: read {file_path} before editing it", True)

        content = path.read_text(encoding="utf-8")
        count = content.count(old_string)
        if count == 0:
            return ToolResult("Error: old_string not found", True)
        if count > 1 and not replace_all:
            return ToolResult(
                f"Error: old_string found {count} times; add context or set replace_all=true",
                True,
            )
        updated = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
        path.write_text(updated, encoding="utf-8")
        return ToolResult(f"Replaced {count if replace_all else 1} occurrence(s) in {file_path}")


class BashTool:
    name = "Bash"
    description = "Run a shell command and return stdout/stderr. Requires user approval."
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "timeout": {"type": "integer", "default": 120},
        },
        "required": ["command"],
    }

    def is_read_only(self) -> bool:
        return False

    def to_schema(self) -> dict[str, Any]:
        return _tool_schema(self)

    def execute(self, command: str, timeout: int = 120) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(f"Error: command timed out after {timeout}s", True)
        except Exception as exc:
            return ToolResult(f"Error: {exc}", True)

        parts: list[str] = []
        if result.stdout:
            parts.append(result.stdout.rstrip())
        if result.stderr:
            parts.append("[stderr]\n" + result.stderr.rstrip())
        if result.returncode != 0:
            parts.append(f"[exit code: {result.returncode}]")
        return ToolResult("\n".join(parts) if parts else "(no output)", result.returncode != 0)


def default_tools() -> list[Any]:
    return [ReadTool(), EditTool(), BashTool()]


def _tool_schema(tool: Any) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }
