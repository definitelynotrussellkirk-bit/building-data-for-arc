"""Native adapter for the canonical/reachable-port-relay family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_adjacent_prototype() -> ModuleType:
    path = Path(__file__).with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "_f60cfd11346a_reachable_port_relay_prototype", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load task-local prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_adjacent_prototype()


def program(settings: dict[str, Any]) -> str:
    normalized = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.program_for(normalized["mode"])


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    normalized = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        mode=normalized["mode"],
        demos=demos,
        queries=queries,
    )
