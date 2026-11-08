"""Native adapter for the matched symmetry-precedence family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any


_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_symmetry_precedence_prototype_" + hashlib.sha256(_PATH.read_bytes()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling symmetry-precedence prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _precedence(settings: Any) -> str:
    return _PROTOTYPE.validate_settings(settings)


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program_for(_precedence(settings))


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return _PROTOTYPE.build_episode(seed, _precedence(settings), demos=demos, queries=queries)
