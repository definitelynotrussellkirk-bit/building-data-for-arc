"""Native adapter for the ``df74e338b4f5`` recoloring-scope family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HOME = Path(__file__).resolve().parent
_PATH = (_HOME / "prototype.py").resolve()
_NAME = "_arc_df74e338b4f5_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"recolor_scope"}:
        raise ValueError("settings must contain exactly recolor_scope")
    value = settings["recolor_scope"]
    if type(value) is not str or value not in _PROTOTYPE.SCOPES:
        raise ValueError(f"recolor_scope must be one of {_PROTOTYPE.SCOPES}")
    return value


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for one declared setting."""
    return _PROTOTYPE.rule_text(_settings(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict:
    """Generate matched inputs and deterministic setting-specific label claims."""
    return _PROTOTYPE.generate_episode(
        seed,
        recolor_scope=_settings(settings),
        demos=demos,
        queries=queries,
    )
