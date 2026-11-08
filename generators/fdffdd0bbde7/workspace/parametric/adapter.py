"""Native adapter entry point for task ``fdffdd0bbde7``."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = _HERE / "prototype.py"
_MODULE_NAME = "parametric_fdffdd0bbde7_adapter_source"


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


def _composition_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"composition"}:
        raise ValueError("settings must contain exactly composition")
    return _PROTOTYPE.validate_composition(settings["composition"])


def program(settings: Any) -> str:
    return _PROTOTYPE.rule_text(_composition_from_settings(settings))


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    return _PROTOTYPE.generate_episode(
        seed=seed,
        composition=_composition_from_settings(settings),
        demos=demos,
        queries=queries,
    )
