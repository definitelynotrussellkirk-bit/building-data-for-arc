"""Thin promotion adapter for the proposed connector-color prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def _load_prototype():
    path = Path(__file__).with_name("prototype.py")
    name = "_arcpuzzles_97dd5f3c96b9_connector_color_prototype"
    module = sys.modules.get(name)
    if module is not None and Path(module.__file__).resolve() == path.resolve():
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load connector-color prototype at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_prototype()


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"connector_color"}:
        raise ValueError("settings must name exactly connector_color")
    value = settings["connector_color"]
    try:
        return PROTOTYPE._validate_connector_color(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"settings contain invalid connector_color: {value!r}") from exc


def program(settings: dict[str, Any]) -> str:
    return PROTOTYPE.program_for(_setting(settings))


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    return PROTOTYPE.generate_episode(
        seed,
        _setting(settings),
        demos=demos,
        queries=queries,
    )
