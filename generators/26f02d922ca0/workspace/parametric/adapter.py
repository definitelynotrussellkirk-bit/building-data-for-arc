"""Thin native adapter for the source/mirror match-count family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SOURCE = _HERE / "family.py"
_BODY = _SOURCE.read_bytes()
_NAME = "_26f02d922ca0_parametric_" + hashlib.sha256(_BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent family.py")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
exec(compile(_BODY, str(_SOURCE), "exec"), _FAMILY.__dict__)


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"report_mode"}:
        raise ValueError("settings must contain exactly report_mode")
    return _FAMILY.validate_mode(settings["report_mode"])


def program(settings: object) -> str:
    return _FAMILY.program_for(_mode(settings))


def generate(seed: int, settings: object, demos: int, queries: int) -> dict:
    mode = _mode(settings)
    return _FAMILY.generate_episode(seed, mode, demos=demos, queries=queries)
