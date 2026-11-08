"""Native promotion adapter for the reviewed path-policy family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_adjacent_prototype() -> ModuleType:
    path = Path(__file__).with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "_db63430eeffa_parametric_prototype_for_adapter", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load task-local prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_adjacent_prototype()


def _path_policy(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"path_policy"}:
        raise ValueError("settings must contain exactly path_policy")
    value = settings["path_policy"]
    if type(value) is not str or value not in _PROTOTYPE.PATH_POLICIES:
        raise ValueError(
            f"path_policy must be one of {_PROTOTYPE.PATH_POLICIES}, got {value!r}"
        )
    return value


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket bytes for one declared setting."""
    return _PROTOTYPE.program_for(_path_policy(settings))


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Generate one private episode for protected native qualification."""
    policy = _path_policy(settings)
    episode = _PROTOTYPE.build_episode(
        seed,
        policy,
        demonstration_count=demos,
        query_count=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }
