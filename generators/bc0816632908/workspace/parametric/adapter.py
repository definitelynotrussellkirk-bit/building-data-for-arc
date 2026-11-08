"""Native period/phase component-selection family for ``bc0816632908``.

Every setting discovers non-background 4-connected components, orders them by
leftmost column, and recolors the components whose ordered index satisfies
``index % period == phase``.  The default ``period=3, phase=0`` program is the
byte-exact selected canonical rule.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "bc0816632908"
HERE = Path(__file__).resolve().parent
SETTINGS = ((2, 0), (2, 1), (3, 0), (3, 1))
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PROFILE_ORDER = (
    "row_order_trap",
    "shape_mix",
    "canonical_zigzag",
    "row_order_trap",
    "shape_mix",
    "canonical_zigzag",
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, int]:
    if type(value) is not dict or set(value) != {"period", "phase"}:
        raise ValueError("settings must contain exactly period and phase")
    period, phase = value["period"], value["phase"]
    if type(period) is not int or type(phase) is not int:
        raise TypeError("period and phase must be literal integers")
    if (period, phase) not in SETTINGS:
        raise ValueError(f"unsupported setting {(period, phase)!r}; allowed={SETTINGS!r}")
    return {"period": period, "phase": phase}


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


def _rng(seed: int, role: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:native-period-phase-v1:{seed}:{role}".encode()).digest()
    return random.Random(digest)


def _derived_seed(seed: int, role: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{TASK_ID}:{seed}:{role}".encode()).digest()[:8], "big") >> 1


def _load_generator():
    path = HERE.parents[1] / "generator.py"
    name = "_bc0816632908_selected_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("selected generator loader missing")
    spec.loader.exec_module(module)
    return module


def _program_path(period: int, phase: int) -> Path:
    return HERE / "racket" / f"period{period}_phase{phase}.rkt"


def program(settings: object) -> str:
    selected = _settings(settings)
    return _program_path(selected["period"], selected["phase"]).read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "wrong_order.rkt").read_text(encoding="utf-8")


def _components(value: object, *, order: str = "left") -> list[tuple[tuple[int, int], ...]]:
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 2 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in _NEIGHBORS:
                    ny, nx = y + dy, x + dx
                    point = (ny, nx)
                    if (
                        0 <= ny < h
                        and 0 <= nx < w
                        and point not in seen
                        and grid[ny][nx] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(tuple(sorted(cells)))
    if order == "left":
        key = lambda cells: (min(c for _r, c in cells), min(r for r, _c in cells))
    elif order == "top":
        key = lambda cells: (min(r for r, _c in cells), min(c for _r, c in cells))
    else:
        raise ValueError("order must be left or top")
    return sorted(result, key=key)


def _paint(value: object, settings: object, *, order: str) -> list[list[int]]:
    grid = _copy(_grid(value))
    selected = _settings(settings)
    for index, cells in enumerate(_components(grid, order=order)):
        if index % selected["period"] == selected["phase"]:
            for r, c in cells:
                grid[r][c] = 4
    return grid


def predict(value: object, settings: object) -> list[list[int]]:
    return _paint(value, settings, order="left")


def predict_wrong_order(value: object, settings: object) -> list[list[int]]:
    return _paint(value, settings, order="top")


def _production_scene(seed: int, index: int, *, split: str) -> list[list[int]]:
    generator = _load_generator()
    profile = _PROFILE_ORDER[index % len(_PROFILE_ORDER)]
    difficulty = ("medium", "hard", "easy")[(index + (1 if split == "query" else 0)) % 3]
    return generator.generate(
        _derived_seed(seed, f"{split}:{index}:{profile}"),
        index,
        difficulty=difficulty,
        scene_profile=profile,
    )


def _stress_30(seed: int) -> list[list[int]]:
    """Dense lawful 30x30 scene with twelve independently ordered components."""
    rng = _rng(seed, "stress-30")
    grid = [[2] * 30 for _ in range(30)]
    tops = [0, 18, 2, 16, 4, 14, 6, 12, 8, 10, 1, 15]
    for index, (col, top) in enumerate(zip(range(0, 24, 2), tops)):
        if index == 0:
            length = 13
        elif index == 1:
            length = 12
        else:
            length = min(30 - top, 9 + rng.randrange(6))
        for row in range(top, top + length):
            grid[row][col] = 0
    return grid


def _demo_bank(seed: int) -> list[list[list[int]]]:
    return [_production_scene(seed, index, split="demo") for index in range(6)]


def _query_bank(seed: int) -> tuple[list[list[list[int]]], list[int]]:
    source = [_production_scene(seed, index + 6, split="query") for index in range(3)]
    source.append(_stress_30(seed))
    order = list(range(4))
    _rng(seed, "query-permutation").shuffle(order)
    return [source[index] for index in order], order


def query_source_order(seed: object) -> list[int]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    return _query_bank(seed)[1]


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", *QUERY_LIMITS)
    demo_inputs = _demo_bank(seed)[:demos]
    query_inputs = _query_bank(seed)[0][:queries]
    all_inputs = demo_inputs + query_inputs
    keys = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("deterministic sampler produced duplicate inputs")
    pair = lambda grid: {"input": _copy(grid), "output": predict(grid, selected)}
    return {
        "train": [pair(grid) for grid in demo_inputs],
        "test": [pair(grid) for grid in query_inputs],
        "program_solution": program(selected),
    }


def surviving_settings(demos: Iterable[dict[str, object]]) -> list[dict[str, int]]:
    pairs = list(demos)
    survivors = []
    for period, phase in SETTINGS:
        setting = {"period": period, "phase": phase}
        if all(predict(pair["input"], setting) == pair["output"] for pair in pairs):
            survivors.append(setting)
    return survivors


def observe(value: object) -> dict[str, object]:
    grid = _grid(value)
    left = _components(grid, order="left")
    top = _components(grid, order="top")
    h, w = len(grid), len(grid[0])
    foreground = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 2]
    touches = []
    if any(r == 0 for r, _c in foreground):
        touches.append("top")
    if any(r == h - 1 for r, _c in foreground):
        touches.append("bottom")
    if any(c == 0 for _r, c in foreground):
        touches.append("left")
    if any(c == w - 1 for _r, c in foreground):
        touches.append("right")
    signature = lambda cells: (min(r for r, _c in cells), min(c for _r, c in cells), len(cells))
    return {
        "height": h,
        "width": w,
        "component_count": len(left),
        "foreground_cells": len(foreground),
        "left_to_right": [signature(cells) for cells in left],
        "top_to_bottom": [signature(cells) for cells in top],
        "row_order_differs": left != top,
        "touches": touches,
    }


def explain_dependency(value: object, settings: object) -> dict[str, object]:
    selected = _settings(settings)
    info = observe(value)
    return {
        "step_a": "Discover every non-background 4-connected component and sort the components by their input-derived leftmost column.",
        "intermediate": "The ordered component list, represented here by each component's top row, left column, and area.",
        "step_b": f"Select ordered indices i with i mod {selected['period']} = {selected['phase']} and recolor every cell of those components to 4.",
        "why_b_depends_on_a": "The periodic positions are positions in the ordered component list. Changing the discovered order changes which whole objects occupy those positions and therefore changes the final grid.",
        "left_to_right_order": info["left_to_right"],
        "top_to_bottom_order": info["top_to_bottom"],
    }


def dependency_case(seed: object = 0, settings: object = None) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings({"period": 3, "phase": 0} if settings is None else settings)
    grid = _stress_30(seed)
    output = predict(grid, selected)
    alternate = predict_wrong_order(grid, selected)
    if alternate == output:
        raise RuntimeError("dependency witness unexpectedly collapsed")
    explanation = explain_dependency(grid, selected)
    return {
        "input": grid,
        "settings": selected,
        "intermediate_value": {
            "left_to_right_order": explanation["left_to_right_order"],
            "top_to_bottom_order": explanation["top_to_bottom_order"],
        },
        "program": program(selected),
        "output": output,
        "counterfactual_program": counterfactual_program(),
        "counterfactual_output": alternate,
        "ablation": "wrong_order",
    }
