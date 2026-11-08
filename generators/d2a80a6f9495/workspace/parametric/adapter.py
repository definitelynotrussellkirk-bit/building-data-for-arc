"""Native promotion adapter for the d2a80a6f9495 swap-scope family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_PATH = (_HERE / "prototype.py").resolve()
_NAME = "_arc_d2a80a6f9495_swap_scope_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling swap-scope prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"swap_scope"}:
        raise ValueError("settings must contain exactly swap_scope")
    return _PROTOTYPE._validate_scope(settings["swap_scope"])


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program_for(_settings(settings))


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return _PROTOTYPE.generate_episode(seed, _settings(settings), demos, queries)
