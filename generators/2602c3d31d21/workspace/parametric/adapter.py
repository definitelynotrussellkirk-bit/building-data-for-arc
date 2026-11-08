"""Native adapter entry point for task ``2602c3d31d21``."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = _HERE / "prototype.py"
_MODULE_NAME = "parametric_2602c3d31d21_adapter_source"


def _load_prototype():
    module = sys.modules.get(_MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype from {_PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_prototype()


def _metric_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"metric"}:
        raise ValueError("settings must contain exactly metric")
    metric = settings["metric"]
    if type(metric) is not str or metric not in _PROTOTYPE.METRICS:
        raise ValueError(f"declared metric must be one of {_PROTOTYPE.METRICS}")
    return metric


def program(settings: Any) -> str:
    return _PROTOTYPE.rule_text(_metric_from_settings(settings))


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    return _PROTOTYPE.generate_episode(
        seed=seed,
        metric=_metric_from_settings(settings),
        demos=demos,
        queries=queries,
    )
