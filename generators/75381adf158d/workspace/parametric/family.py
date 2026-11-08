"""Matched-input family for enclosed-hole filling and derived-hole routing.

``canonical`` preserves the exact selected program. ``largest_escape`` first
fills every enclosed zero-region, then reads the newly created color-8
components, selects the unique largest one, and paints a straight color-8 line
from its bounding-box center to the nearest outer border.  Inputs never contain
8, so the routing trigger exists only after stage A.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

TASK_ID = "75381adf158d"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "largest_escape")

_GEN_PATH = HERE.parents[1] / "generator.py"
_GEN_SPEC = importlib.util.spec_from_file_location("_holes_base_for_family", _GEN_PATH)
if _GEN_SPEC is None or _GEN_SPEC.loader is None:
    raise ImportError(_GEN_PATH)
BASE = importlib.util.module_from_spec(_GEN_SPEC)
sys.modules[_GEN_SPEC.name] = BASE
_GEN_SPEC.loader.exec_module(BASE)

_TRAIN_PROFILES = ((12, 16), (14, 18), (16, 20), (20, 22), (24, 26), (28, 28))
_QUERY_PROFILES = ((13, 17), (18, 21), (25, 27), (30, 30))


def _validate_settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = value["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _validate_request(seed: Any, demos: Any, queries: Any) -> tuple[int, int, int]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    return seed, demos, queries


def program(settings: Any) -> str:
    mode = _validate_settings(settings)
    return (HERE / ("canonical.rkt" if mode == "canonical" else "largest_escape.rkt")).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    return BASE._validate_grid(value)


def canonical_transform(value: Any) -> list[list[int]]:
    return BASE.rule_mirror(value)


def _color_components(value: list[list[int]], color: int) -> list[dict[str, Any]]:
    h, w = len(value), len(value[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if value[r][c] == color}
    parts: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        parts.append({"cells": tuple(sorted(cells)), "size": len(cells),
                      "r1": min(rows), "r2": max(rows), "c1": min(cols), "c2": max(cols)})
    return sorted(parts, key=lambda part: (part["r1"], part["c1"]))


def _center(part: dict[str, Any]) -> tuple[int, int]:
    return ((part["r1"] + part["r2"]) // 2, (part["c1"] + part["c2"]) // 2)


def _nearest_border(point: tuple[int, int], h: int, w: int) -> tuple[int, int]:
    r, c = point
    distances = (r, c, h - 1 - r, w - 1 - c)
    choice = min(range(4), key=lambda index: (distances[index], index))
    return ((0, c), (r, 0), (h - 1, c), (r, w - 1))[choice]


def _paint_line(grid: list[list[int]], start: tuple[int, int], end: tuple[int, int]) -> None:
    r1, c1 = start
    r2, c2 = end
    if r1 == r2:
        step = 1 if c2 >= c1 else -1
        for c in range(c1, c2 + step, step):
            grid[r1][c] = 8
    elif c1 == c2:
        step = 1 if r2 >= r1 else -1
        for r in range(r1, r2 + step, step):
            grid[r][c1] = 8
    else:
        raise ValueError("escape line must be axis-aligned")


def escape_transform(value: Any, *, selection: str = "largest", route: str = "nearest") -> list[list[int]]:
    stage = canonical_transform(value)
    holes = _color_components(stage, 8)
    if not holes:
        return stage
    if selection == "largest":
        chosen = max(holes, key=lambda part: (part["size"], -part["r1"], -part["c1"]))
    elif selection == "smallest":
        chosen = min(holes, key=lambda part: (part["size"], part["r1"], part["c1"]))
    else:
        raise ValueError(selection)
    point = _center(chosen)
    target = _nearest_border(point, len(stage), len(stage[0])) if route == "nearest" else (0, point[1])
    output = deepcopy(stage)
    _paint_line(output, point, target)
    return output


def transform(value: Any, mode: Any) -> list[list[int]]:
    if mode == "canonical":
        return canonical_transform(value)
    if mode == "largest_escape":
        return escape_transform(value)
    raise ValueError(f"mode must be one of {MODES}")


def named_rivals(mode: str) -> dict[str, Callable[[Any], list[list[int]]]]:
    if mode == "canonical":
        return {
            "identity": _grid,
            "fill_every_zero": lambda g: [[8 if cell == 0 else cell for cell in row] for row in _grid(g)],
            "add_largest_escape": escape_transform,
        }
    if mode == "largest_escape":
        return {
            "canonical_only": canonical_transform,
            "route_from_smallest_hole": lambda g: escape_transform(g, selection="smallest"),
            "route_largest_only_upward": lambda g: escape_transform(g, route="top"),
        }
    raise ValueError(mode)


def teaching_audit(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain train and test lists")
    selected = next((mode for mode in MODES if episode.get("program_solution") == program({"mode": mode})), None)
    if selected is None:
        raise ValueError("episode program is not a declared mode")
    survivors = [mode for mode in MODES if all(transform(pair["input"], mode) == pair["output"] for pair in episode["train"])]
    harmful = []
    for name, rival in named_rivals(selected).items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {"declared_setting_survivors": survivors,
            "query_disagreeing_named_survivors": harmful,
            "named_rivals_checked": sorted(named_rivals(selected))}


def _scene(seed: int, split: str, index: int, dimensions: tuple[int, int]) -> list[list[int]]:
    h, w = dimensions
    digest = hashlib.sha256(f"{TASK_ID}|largest-escape-v1|{seed}|{split}|{index}".encode()).digest()
    derived_seed = int.from_bytes(digest[:8], "big") & (2**63 - 1)
    grid = BASE.generate(derived_seed, index, grid_h=h, grid_w=w, scene_profile="largest_counterexample")
    facts = analyse(grid)
    if facts["enclosed_regions"] < 3 or len(facts["enclosed_sizes"]) != len(set(facts["enclosed_sizes"])):
        raise RuntimeError("largest-hole scene lost unique enclosed sizes")
    if escape_transform(grid) in (canonical_transform(grid), escape_transform(grid, selection="smallest")):
        raise RuntimeError("scene does not separate canonical/largest/smallest rules")
    return grid


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact nonnegative integer")
    return {
        "train": [_scene(seed, "train", i, profile) for i, profile in enumerate(_TRAIN_PROFILES)],
        "test": [_scene(seed, "test", i, profile) for i, profile in enumerate(_QUERY_PROFILES)],
    }


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed, demos, queries = _validate_request(seed, demos, queries)
    mode = _validate_settings(settings)
    inputs = episode_inputs(seed)
    def pairs(split: str, count: int):
        return [{"input": deepcopy(grid), "output": transform(grid, mode)} for grid in inputs[split][:count]]
    return {"train": pairs("train", demos), "test": pairs("test", queries),
            "program_solution": program({"mode": mode})}


def analyse(value: Any) -> dict[str, Any]:
    return BASE.analyse(value)


def dependency_trace(value: Any) -> dict[str, Any]:
    source = _grid(value)
    intermediate = canonical_transform(source)
    holes = _color_components(intermediate, 8)
    largest = max(holes, key=lambda part: part["size"])
    smallest = min(holes, key=lambda part: part["size"])
    return {
        "step_a": "fill every enclosed zero-region with color 8",
        "intermediate": intermediate,
        "filled_hole_sizes": sorted(part["size"] for part in holes),
        "largest_size": largest["size"],
        "smallest_size": smallest["size"],
        "step_b": "route from the unique largest derived color-8 component to its nearest border",
        "output": escape_transform(source),
        "smallest_escape_output": escape_transform(source, selection="smallest"),
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index out of range")
    return {"train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(episode["test"][query_index]["input"])}]}
