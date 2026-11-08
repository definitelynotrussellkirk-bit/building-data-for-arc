"""Native adapter for the b6c499e1fa78 matched-area family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_b6c499e1fa78_parametric_prototype", HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("unable to load parametric prototype")
_prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _prototype
_SPEC.loader.exec_module(_prototype)


def program(settings: Any) -> str:
    return _prototype.program(settings)


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    episode = _prototype.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
