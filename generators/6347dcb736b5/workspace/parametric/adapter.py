"""Native promotion adapter for the marker-relay bounding-box family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = (_HERE / "prototype.py").resolve()
if _PROTOTYPE_PATH.parent != _HERE or not _PROTOTYPE_PATH.is_file():
    raise ImportError("missing adjacent marker-relay prototype")
_NAME = "_arc_6347dcb736b5_marker_relay_" + hashlib.sha256(str(_PROTOTYPE_PATH).encode()).hexdigest()
_PROTOTYPE = sys.modules.get(_NAME)
if _PROTOTYPE is None:
    _SPEC = importlib.util.spec_from_file_location(_NAME, _PROTOTYPE_PATH)
    if _SPEC is None or _SPEC.loader is None:
        raise ImportError("cannot load adjacent marker-relay prototype")
    _PROTOTYPE = importlib.util.module_from_spec(_SPEC)
    sys.modules[_NAME] = _PROTOTYPE
    _SPEC.loader.exec_module(_PROTOTYPE)


def _scope(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"outline_scope"}:
        raise ValueError("settings must contain exactly outline_scope")
    return _PROTOTYPE.validate_scope(settings["outline_scope"])


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program_for(_scope(settings))


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    return _PROTOTYPE.generate_episode(seed, _scope(settings), demos=demos, queries=queries)
