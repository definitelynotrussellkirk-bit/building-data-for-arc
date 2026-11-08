"""Canonical cyan stamping with an optional post-stamp component relay.

``stamp_only`` is the exact selected canonical program. The alternate first
executes that rule, isolates cells newly changed to cyan, then recolors every
maximum-size four-connected component of that intermediate mask red (2).
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

TASK_ID = "d3575d4206d7"
HERE = Path(__file__).resolve().parent
FINISHES = ("stamp_only", "mark_largest_new_components")
POLICIES = (
    "stamp_only",
    "mark_largest_new_components",
    "mark_all_new",
    "mark_smallest_new_components",
    "mark_first_new_component",
    "mark_largest_original_cyan",
    "mark_largest_all_cyan",
    "mark_new_components_size_at_least_2",
)
DEMO_LAYOUTS = (
    "canonical_17", "canonical_21", "canonical_23",
    "canonical_27", "canonical_17", "canonical_21",
)
QUERY_LAYOUTS = ("canonical_17", "canonical_21", "canonical_23", "canonical_27")


def _load_source_generator():
    source = HERE.parents[1] / "generator.py"
    name = "_arc_d357_source_" + hashlib.sha256(str(source).encode()).hexdigest()
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_SOURCE = _load_source_generator()


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _finish(value: Any) -> str:
    if type(value) is not str or value not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return value


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    return _finish(settings["finish"])


def program_for(finish: str) -> str:
    finish = _finish(finish)
    name = "canonical.rkt" if finish == "stamp_only" else "mark_largest_new_components.rkt"
    return (HERE / name).read_text()


def counterfactual_program() -> str:
    return (HERE / "wrong_original_cyan_intermediate.rkt").read_text()


def program(settings: dict[str, Any]) -> str:
    return program_for(_settings(settings))


def _derived(seed: int, role: str, index: int, attempt: int = 0) -> tuple[int, int]:
    digest = hashlib.sha256(
        f"d357-parametric-v1:{seed}:{role}:{index}:{attempt}".encode()
    ).digest()
    source_seed = int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)
    sample_index = int.from_bytes(digest[8:12], "big")
    return source_seed, sample_index


def _components(cells: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(cells)
    result: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for neighbor in ((r - 1, c), (r, c - 1), (r, c + 1), (r + 1, c)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        component.sort()
        result.append(component)
    result.sort(key=lambda component: component[0])
    return result


def _max_components(components: list[list[tuple[int, int]]]) -> list[list[tuple[int, int]]]:
    if not components:
        return []
    maximum = max(map(len, components))
    return [component for component in components if len(component) == maximum]


def _min_components(components: list[list[tuple[int, int]]]) -> list[list[tuple[int, int]]]:
    if not components:
        return []
    minimum = min(map(len, components))
    return [component for component in components if len(component) == minimum]


def _flatten(components: Iterable[Iterable[tuple[int, int]]]) -> list[tuple[int, int]]:
    return [cell for component in components for cell in component]


def _recolor(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int = 2) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for r, c in cells:
        out[r][c] = color
    return out


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    stage = _SOURCE.rule_mirror(grid)
    new_cells = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if stage[r][c] == 8 and grid[r][c] != 8
    ]
    new_components = _components(new_cells)
    original_cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    all_stage_cyan = [(r, c) for r, row in enumerate(stage) for c, value in enumerate(row) if value == 8]
    selected = _flatten(_max_components(new_components))
    return {
        "stage": stage,
        "new_cyan_cells": new_cells,
        "new_components": new_components,
        "selected_new_cells": selected,
        "original_cyan_components": _components(original_cyan),
        "all_stage_cyan_components": _components(all_stage_cyan),
    }


def solve_policy(grid: list[list[int]], policy: str) -> list[list[int]]:
    info = analyze(grid)
    stage = info["stage"]
    new_components = info["new_components"]
    if policy == "stamp_only":
        return copy.deepcopy(stage)
    if policy == "mark_largest_new_components":
        cells = info["selected_new_cells"]
    elif policy == "mark_all_new":
        cells = info["new_cyan_cells"]
    elif policy == "mark_smallest_new_components":
        cells = _flatten(_min_components(new_components))
    elif policy == "mark_first_new_component":
        cells = new_components[0] if new_components else []
    elif policy == "mark_largest_original_cyan":
        cells = _flatten(_max_components(info["original_cyan_components"]))
    elif policy == "mark_largest_all_cyan":
        cells = _flatten(_max_components(info["all_stage_cyan_components"]))
    elif policy == "mark_new_components_size_at_least_2":
        cells = _flatten(component for component in new_components if len(component) >= 2)
    else:
        raise ValueError(f"unknown policy {policy!r}")
    return _recolor(stage, cells)


def solve(grid: list[list[int]], finish: str) -> list[list[int]]:
    return solve_policy(grid, _finish(finish))


def _extend_to_30(grid: list[list[int]]) -> list[list[int]]:
    analysis = _SOURCE._analysis(grid)
    if analysis["errors"] or len(grid) != 27 or len(grid[0]) != 27:
        raise ValueError("30x30 extension requires a valid canonical_27 scene")
    divider = analysis["divider_color"]
    if divider is None:
        raise ValueError("scene has no unique divider color")
    return [row[:] + [divider] * 3 for row in grid] + [[divider] * 30 for _ in range(3)]


def _valid_scene(grid: list[list[int]], *, strong: bool) -> bool:
    source_analysis = _SOURCE._analysis(grid)
    if source_analysis["errors"]:
        return False
    info = analyze(grid)
    sizes = [len(component) for component in info["new_components"]]
    if len(sizes) < 2 or len(set(sizes)) < 2 or not info["selected_new_cells"]:
        return False
    if solve(grid, "stamp_only") == solve(grid, "mark_largest_new_components"):
        return False
    if strong:
        target = solve(grid, "mark_largest_new_components")
        if any(solve_policy(grid, policy) == target
               for policy in POLICIES if policy != "mark_largest_new_components"):
            return False
    return True


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    if split == "train":
        if type(index) is not int or not 0 <= index < len(DEMO_LAYOUTS):
            raise ValueError("demo index out of range")
        layout = DEMO_LAYOUTS[index]
    elif split == "test":
        if type(index) is not int or not 0 <= index < len(QUERY_LAYOUTS):
            raise ValueError("query index out of range")
        layout = QUERY_LAYOUTS[index]
    else:
        raise ValueError("split must be train or test")

    for attempt in range(128):
        source_seed, sample_index = _derived(seed, split, index, attempt)
        kwargs: dict[str, Any] = {"layout": layout, "scene_mode": "mixed"}
        if split == "test" and index == 3:
            kwargs["divider_color"] = 9
        grid = _SOURCE.generate(source_seed, sample_index, difficulty="hard", **kwargs)
        if split == "test" and index == 3:
            grid = _extend_to_30(grid)
        if _valid_scene(grid, strong=(split == "train" and index < 2)):
            return grid
    raise RuntimeError(f"unable to construct {split} scene {index} for seed {seed}")


def generate_episode(seed: int, finish: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    finish = _finish(finish)
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    train = [{"input": sample_input(seed, "train", i), "output": None} for i in range(demos)]
    test = [{"input": sample_input(seed, "test", i), "output": None} for i in range(queries)]
    for pair in train + test:
        pair["output"] = solve(pair["input"], finish)
    return {"train": train, "test": test, "program_solution": program_for(finish)}


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return generate_episode(seed, _settings(settings), demos=demos, queries=queries)


def teaching_survivors(demos: list[dict[str, Any]]) -> list[str]:
    return [
        policy
        for policy in POLICIES
        if all(solve_policy(pair["input"], policy) == pair["output"] for pair in demos)
    ]
