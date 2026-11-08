"""Native promotion adapter for the room-graph tie-marker family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SOURCE = _HERE / "family.py"
_BODY = _SOURCE.read_bytes()
_NAME = "_arc_1b2b9283b4ab_family_" + hashlib.sha256(_BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent tie-marker family")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
exec(compile(_BODY, str(_SOURCE), "exec"), _FAMILY.__dict__)


def _marker(settings: object) -> int:
    if type(settings) is not dict or set(settings) != {"tie_marker"}:
        raise ValueError("settings must contain exactly tie_marker")
    return _FAMILY.validate_marker(settings["tie_marker"])


def program(settings: object) -> str:
    marker = _marker(settings)
    name = "canonical.rkt" if marker == 8 else "tie-marker-6.rkt"
    return (_HERE / name).read_text(encoding="utf-8")


def generate(seed: int, settings: object, demos: int, queries: int) -> dict:
    marker = _marker(settings)
    selected = program({"tie_marker": marker})
    return _FAMILY.generate_episode(seed, tie_marker=marker, demos=demos, queries=queries,
                                    program_solution=selected)
