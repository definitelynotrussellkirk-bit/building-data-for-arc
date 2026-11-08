"""Native adapter for the 63784d19dd2d transform/overlap family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_PATH = _HERE / "prototype.py"
_NAME = "parametric_63784d19dd2d_native_source"


def _load():
    module = sys.modules.get(_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_NAME, _PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load parametric source from {_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_NAME] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load()


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"overlap_mode"}:
        raise ValueError("settings must contain exactly overlap_mode")
    return _PROTOTYPE._mode(settings["overlap_mode"])


def program(settings: Any) -> str:
    return _PROTOTYPE.program_for(_mode(settings))


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    return _PROTOTYPE.generate_episode(seed, _mode(settings), demos=demos, queries=queries)
