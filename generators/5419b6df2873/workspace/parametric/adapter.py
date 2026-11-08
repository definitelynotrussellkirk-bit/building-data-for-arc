"""Native promotion adapter for the contact-color relay family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_PATH = (_HERE / "prototype.py").resolve()
_NAME = "_arc_5419b6df2873_contact_relay_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent contact-relay prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"relay_mode"}:
        raise ValueError("settings must contain exactly relay_mode")
    return prototype._mode(settings["relay_mode"])


def program(settings: dict[str, Any]) -> str:
    return prototype.program_for(_mode(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    return prototype.generate_episode(seed, _mode(settings), demos=demos, queries=queries)
