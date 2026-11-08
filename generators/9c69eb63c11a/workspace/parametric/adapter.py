"""Native finite selection-rank family for ARC task 9c69eb63c11a."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any


TASK_ID = "9c69eb63c11a"
MODES = ("median", "second_largest")
_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_CANONICAL = (_HOME / "canonical.rkt").read_text(encoding="utf-8")


def _load_generator():
    path = _TASK_HOME / "generator.py"
    name = "_parametric_source_9c69eb63c11a"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load task generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()


def _mode(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"selection_mode"}:
        raise ValueError("settings must name exactly selection_mode")
    value = settings["selection_mode"]
    if type(value) is not str or value not in MODES:
        raise ValueError("selection_mode must be 'median' or 'second_largest'")
    return value


def program(settings: dict[str, Any]) -> str:
    """Preserve canonical median bytes or change only the ranked-list index."""
    mode = _mode(settings)
    if mode == "median":
        return _CANONICAL
    old = "(quotient (length ranked) 2)"
    if _CANONICAL.count(old) != 1:
        raise RuntimeError("canonical median index changed; refusing unsafe rewrite")
    return _CANONICAL.replace(old, "(- (length ranked) 2)")


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _rng(seed: int, phase: str, slot: int, attempt: int) -> random.Random:
    payload = f"{TASK_ID}|rank-family-v1|{seed}|{phase}|{slot}|{attempt}".encode()
    value = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return random.Random(value)


def _predict(grid: list[list[int]], mode: str) -> list[list[int]]:
    reasons = _GENERATOR.self_check(grid)
    if reasons:
        raise ValueError("invalid rank-family input: " + "; ".join(reasons))
    ranked = sorted(_GENERATOR._components(grid), key=lambda component: len(component["cells"]))
    index = len(ranked) // 2 if mode == "median" else len(ranked) - 2
    return _GENERATOR._paint_component(grid, ranked[index])


# All examples have five components, so median (rank 2) and second-largest
# (rank 3) differ on every demonstration rather than only collectively.
_DEMO_PROFILES = (
    (14, 14, (1, 4, 7, 10, 13)),
    (13, 14, (2, 5, 8, 11, 14)),
    (14, 13, (3, 6, 9, 12, 15)),
    (12, 14, (1, 5, 9, 13, 17)),
    (14, 12, (2, 6, 10, 14, 18)),
    (14, 14, (4, 8, 12, 16, 20)),
)

_QUERY_PROFILES = (
    (30, 30, (17, 31, 47, 63, 79)),
    (8, 8, (1, 2, 3, 4, 5)),
    (18, 24, (4, 9, 15, 22, 30)),
    (27, 17, (3, 8, 14, 21, 29)),
)


def _spans(grid: list[list[int]]) -> tuple[int, int]:
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return (
        max(r for r, _ in occupied) - min(r for r, _ in occupied),
        max(c for _, c in occupied) - min(c for _, c in occupied),
    )


def _accepted_input(
    *, seed: int, phase: str, slot: int, profile: tuple[int, int, tuple[int, ...]], seen: set[str]
) -> list[list[int]]:
    height, width, sizes = profile
    for attempt in range(512):
        rng = _rng(seed, phase, slot, attempt)
        colors = [1, 3, 5, 7, 9]
        rng.shuffle(colors)
        try:
            grid = _GENERATOR._layout(height, width, list(sizes), colors, rng)
        except RuntimeError:
            continue
        if _GENERATOR.self_check(grid):
            continue
        if sorted(len(component["cells"]) for component in _GENERATOR._components(grid)) != list(sizes):
            continue
        if (height, width) == (30, 30) and min(_spans(grid)) < 20:
            continue
        digest = _digest(grid)
        if digest in seen:
            continue
        seen.add(digest)
        return grid
    raise RuntimeError(f"bounded {phase} sampling exhausted for slot {slot}")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Build deterministic setting-independent inputs and rank-selected labels."""
    mode = _mode(settings)
    _validate_request(seed, demos, queries)
    seen: set[str] = set()
    train = []
    for slot, profile in enumerate(_DEMO_PROFILES[:demos]):
        grid = _accepted_input(seed=seed, phase="demo", slot=slot, profile=profile, seen=seen)
        train.append({"input": copy.deepcopy(grid), "output": _predict(grid, mode)})
    test = []
    for slot, profile in enumerate(_QUERY_PROFILES):
        grid = _accepted_input(seed=seed, phase="query", slot=slot, profile=profile, seen=seen)
        test.append({"input": copy.deepcopy(grid), "output": _predict(grid, mode)})
    return {"train": train, "test": test, "program_solution": program(settings)}
