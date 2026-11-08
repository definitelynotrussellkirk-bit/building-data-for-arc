"""Native adapter for the adjacent period/paint prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("9ee024f29fdb_parametric_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()


def program(settings: dict[str, Any] | None = None) -> str:
    selected = prototype.normalize_settings(settings)
    return prototype.render_program(**selected)


def generate(
    seed: int,
    settings: dict[str, Any] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    selected = prototype.normalize_settings(settings)
    return prototype.build_episode_python(
        seed,
        selected,
        demos=demos,
        queries=queries,
    )
