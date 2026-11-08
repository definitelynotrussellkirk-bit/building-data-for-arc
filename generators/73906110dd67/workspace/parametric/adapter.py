"""Native promotion adapter for 73906110dd67 order-metric variants."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_PATH = (_HERE / "prototype.py").resolve()
_NAME = "_arc_73906110dd67_order_metric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent order-metric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def _metric(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"order_metric"}:
        raise ValueError("settings must contain exactly order_metric")
    return prototype._metric(settings["order_metric"])


def program(settings: dict[str, Any]) -> str:
    return prototype.program_for(_metric(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    return prototype.generate_episode(seed, _metric(settings), demos, queries)


def transform(grid: list[list[int]], metric: str) -> list[list[int]]:
    return prototype.output_for(grid, metric)


def render_order(grid: list[list[int]], order, **kwargs):
    return prototype.render_order(grid, order, **kwargs)


def dependency_intermediate(grid: list[list[int]], metric: str) -> dict[str, Any]:
    return prototype.dependency_intermediate(grid, metric)


def audit_episode(episode: dict[str, Any], metric: str) -> dict[str, Any]:
    return prototype.audit_episode(episode, metric)
