"""Public-parent 8b7bacbf: propagate embedded payloads through carrier routes."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

RULE_TASK_ID = "ee_8b7bacbf"
TASK_ID = "public_eval_8b7bacbf"
GENERATOR_ID = TASK_ID
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
AXES: dict[str, object] = {}
SUMMARY = "Trace carrier-color routes from embedded payload markers and fill reached pockets."


def _model():
    base = Path(__file__).resolve().parent / "workspace/parametric"
    if not (base / "model.py").is_file():
        from reviewer_support import find_root

        base = find_root(__file__) / "generators" / TASK_ID / "workspace/parametric"
    path = base / "model.py"
    name = "_route_model_" + hashlib.sha256(str(path).encode()).hexdigest()
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    if overrides:
        raise ValueError("no overrides supported")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("unknown difficulty")
    return _model().sample_input(seed, sample_index, stress=(difficulty == "hard" and sample_index == 103))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    return _model().solve(grid, bridge_short_gaps=True)


def self_check(grid: list[list[int]], **_kwargs) -> list[str]:
    try:
        state = _model().analyze(grid, bridge_short_gaps=True)
        if not state["sources"]:
            return ["at least one embedded payload source is required"]
        if not state["assignments"]:
            return ["at least one source-reached pocket is required"]
        return []
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
