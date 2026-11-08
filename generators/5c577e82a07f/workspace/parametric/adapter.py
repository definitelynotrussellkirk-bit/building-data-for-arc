"""Native promotion adapter for the completed-border enclosure family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_5c577e82a07f_enclosure_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)

POLICIES = prototype.POLICIES


def _policy(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"enclosure_policy"}:
        raise ValueError("settings must contain exactly enclosure_policy")
    try:
        return prototype._policy(settings["enclosure_policy"])
    except ValueError as exc:
        raise ValueError("enclosure_policy must be borders_only or largest_enclosure") from exc


def program(settings: dict[str, Any]) -> str:
    return prototype.program(_policy(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    return prototype.generate_episode(seed, _policy(settings), demos, queries)


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    return prototype.public_turn(episode, query_index)
