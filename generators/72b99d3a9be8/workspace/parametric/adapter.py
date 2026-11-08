"""Native promotion adapter for 72b99d3a9be8 reflector-color variants."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_PATH = (_HERE / "prototype.py").resolve()
_NAME = "_arc_72b99d3a9be8_reflector_color_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent reflector-color prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def _color(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"reflector_color"}:
        raise ValueError("settings must contain exactly reflector_color")
    return prototype._reflector_color(settings["reflector_color"])


def program(settings: dict[str, Any]) -> str:
    return prototype.program_for(_color(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    return prototype.generate_episode(seed, _color(settings), demos, queries)


def transform(grid: list[list[int]], reflector_color: int) -> list[list[int]]:
    return prototype.output_for(grid, reflector_color)


def dependency_intermediate(grid: list[list[int]], reflector_color: int) -> dict[str, Any]:
    return prototype.dependency_intermediate(grid, reflector_color)


def audit_episode(episode: dict[str, Any], reflector_color: int) -> dict[str, Any]:
    return prototype.audit_episode(episode, reflector_color)
