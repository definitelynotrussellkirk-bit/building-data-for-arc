"""Native adapter for the 4d0f228177b0 crossing-ray payload family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Any

_HOME = Path(__file__).resolve().parent


def _load_prototype():
    path = _HOME / "prototype.py"
    name = "_prototype_4d0f228177b0_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PROTO = _load_prototype()
_PROGRAMS = {
    "canonical": (_HOME / "canonical.rkt").read_text(encoding="utf-8"),
    "first_hit_payload": (_HOME / "first_hit_payload.rkt").read_text(encoding="utf-8"),
}


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    finish = settings["finish"]
    if finish not in _PROGRAMS:
        raise ValueError("unknown finish setting")
    return {"finish": finish}


def _count(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    return _PROGRAMS[_settings(settings)["finish"]]



def certificate_errors(
    episode: Any, settings: Any, *, demos: Any, queries: Any
) -> list[str]:
    errors: list[str] = []
    try:
        settings = _settings(settings)
        demos = _count("demos", demos, 2, 6)
        queries = _count("queries", queries, 1, 4)
    except Exception as exc:
        return [f"invalid request: {type(exc).__name__}: {exc}"]
    if type(episode) is not dict:
        return ["episode must be a dictionary"]
    if episode.get("program_solution") != program(settings):
        errors.append("program_solution differs from program(settings)")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or len(train) != demos:
        errors.append(f"train count must equal {demos}")
    if type(test) is not list or len(test) != queries:
        errors.append(f"test count must equal {queries}")
    if not errors:
        errors.extend(_PROTO.lesson_errors(episode, settings))
    return errors

def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2^63-1")
    settings = _settings(settings)
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    banks = _PROTO.build_banks(seed)
    train_inputs = banks["demos"][:demos]
    test_inputs = banks["queries"][:queries]
    episode = {
        "train": [
            {"input": grid, "output": _PROTO.apply(grid, settings)}
            for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": _PROTO.apply(grid, settings)}
            for grid in test_inputs
        ],
        "program_solution": program(settings),
    }
    errors = certificate_errors(episode, settings, demos=demos, queries=queries)
    if errors:
        raise ValueError("lesson construction failed: " + "; ".join(errors))
    return episode
