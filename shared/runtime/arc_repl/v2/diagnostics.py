"""Resolve compiler-owned runtime diagnostics back to the author's source."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .compiler import CompilationResult

_RUNTIME = re.compile(r"v2:runtime:(E_[A-Z_]+) at ([0-9]+):([0-9]+) (\$(?:input|(?:\[[0-9]+\])*))")


def diagnose_runtime_error(error: object, compilation: CompilationResult) -> dict[str, object] | None:
    """Return a structured guard error, or None for an unrelated backend error.

    A None result is NOT success. Callers must retain and report that backend
    failure; this helper does not evaluate, recover, or suppress exceptions.
    """
    match = _RUNTIME.search(str(error))
    if match is None:
        return None
    code, line, column, path = match.groups()
    original = next((entry for entry in compilation.source_map if entry.path == path), None)
    result: dict[str, object] = {
        "phase": "runtime", "code": code, "path": path,
        "canonical_line": int(line), "canonical_column": int(column),
        "compiled_sha256": compilation.compiled_sha256,
    }
    if original is not None:
        result.update(line=original.line, column=original.column,
                      end_line=original.end_line, end_column=original.end_column)
    else:
        result["location_scope"] = "input" if path == "$input" else "unmapped"
    return result
