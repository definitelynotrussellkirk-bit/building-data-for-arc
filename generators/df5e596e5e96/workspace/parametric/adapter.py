"""Thin native promotion adapter for the relation-matrix ordering prototype."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


def _load_prototype():
    path = Path(__file__).with_name("prototype.py")
    name = "_arcpuzzles_df5e596e5e96_matrix_order_prototype"
    cached = sys.modules.get(name)
    if cached is not None and Path(cached.__file__).resolve() == path.resolve():
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load matrix-order prototype at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_prototype()


def program(settings: dict[str, Any]) -> str:
    return PROTOTYPE.program(PROTOTYPE.normalize_settings(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    return PROTOTYPE.generate_episode(
        seed,
        PROTOTYPE.normalize_settings(settings),
        demos=demos,
        queries=queries,
    )
