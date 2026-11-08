"""Native matched-input family for exact-blue-square recoloring and waypoint routing.

The canonical setting preserves the selected Racket rule byte-for-byte.  The
alternative first performs that recoloring, then treats the newly created
color-3 components as waypoints and connects their centers in reading order by
horizontal-then-vertical color-3 paths.  Since color 3 is absent from every
input, the waypoint set is an input-dependent intermediate produced by stage A.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "7ce16af847d6"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "bridge_centers")

_SOLID_3 = tuple((r, c) for r in range(3) for c in range(3))
_BLUE_DISTRACTORS = (
    tuple((r, c) for r in range(3) for c in range(3) if r in (0, 2) or c in (0, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)),
    tuple([(r, c) for r in range(2) for c in range(4)] + [(2, 0)]),
    tuple(list(_SOLID_3) + [(1, 3)]),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
)
_DECOR_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
)
_TRAIN_PROFILES = (
    (12, 16, 2, 3, 2),
    (14, 18, 3, 4, 3),
    (16, 20, 3, 4, 3),
    (20, 22, 4, 5, 4),
    (24, 26, 4, 5, 4),
    (28, 28, 5, 6, 5),
)
_QUERY_PROFILES = (
    (13, 17, 2, 3, 2),
    (18, 21, 3, 4, 3),
    (25, 27, 4, 5, 4),
    (30, 30, 5, 6, 6),
)


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
    name = "canonical.rkt" if mode == "canonical" else "bridge_centers.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(type(row) is not list or len(row) != len(value[0]) or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in value)
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in value]


def _components(value: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(value), len(value[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if value[r][c] != 0}
    parts: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = value[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and value[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        parts.append({
            "color": color,
            "cells": tuple(sorted(cells)),
            "r1": min(rows),
            "c1": min(cols),
            "r2": max(rows),
            "c2": max(cols),
            "size": len(cells),
        })
    return sorted(parts, key=lambda part: (part["r1"], part["c1"], part["color"]))


def _is_target(part: dict[str, Any]) -> bool:
    return (
        part["color"] == 1
        and part["size"] == 9
        and part["r2"] - part["r1"] + 1 == 3
        and part["c2"] - part["c1"] + 1 == 3
    )


def _center(part: dict[str, Any]) -> tuple[int, int]:
    return ((part["r1"] + part["r2"]) // 2, (part["c1"] + part["c2"]) // 2)


def canonical_transform(value: Any) -> list[list[int]]:
    source = _grid(value)
    output = [row[:] for row in source]
    for part in _components(source):
        if _is_target(part):
            for r, c in part["cells"]:
                output[r][c] = 3
    return output


def _paint_hv(output: list[list[int]], a: tuple[int, int], b: tuple[int, int], *, vertical_first: bool = False) -> None:
    ar, ac = a
    br, bc = b
    if vertical_first:
        step = 1 if br >= ar else -1
        for r in range(ar, br + step, step):
            output[r][ac] = 3
        step = 1 if bc >= ac else -1
        for c in range(ac, bc + step, step):
            output[br][c] = 3
    else:
        step = 1 if bc >= ac else -1
        for c in range(ac, bc + step, step):
            output[ar][c] = 3
        step = 1 if br >= ar else -1
        for r in range(ar, br + step, step):
            output[r][bc] = 3


def bridge_transform(value: Any, *, vertical_first: bool = False, first_last_only: bool = False) -> list[list[int]]:
    stage = canonical_transform(value)
    waypoints = [part for part in _components(stage) if part["color"] == 3]
    waypoints.sort(key=lambda part: (part["r1"], part["c1"]))
    output = [row[:] for row in stage]
    pairs = list(zip(waypoints, waypoints[1:]))
    if first_last_only and len(waypoints) >= 2:
        pairs = [(waypoints[0], waypoints[-1])]
    for left, right in pairs:
        _paint_hv(output, _center(left), _center(right), vertical_first=vertical_first)
    return output


def transform(value: Any, mode: Any) -> list[list[int]]:
    if mode == "canonical":
        return canonical_transform(value)
    if mode == "bridge_centers":
        return bridge_transform(value)
    raise ValueError(f"mode must be one of {MODES}")


def _rival_all_blue(value: Any) -> list[list[int]]:
    source = _grid(value)
    out = [row[:] for row in source]
    for part in _components(source):
        if part["color"] == 1:
            for r, c in part["cells"]:
                out[r][c] = 3
    return out


def _rival_any_color_3x3(value: Any) -> list[list[int]]:
    source = _grid(value)
    out = [row[:] for row in source]
    for part in _components(source):
        if part["size"] == 9 and part["r2"] - part["r1"] == 2 and part["c2"] - part["c1"] == 2:
            for r, c in part["cells"]:
                out[r][c] = 3
    return out


def _rival_bridge_all_blue(value: Any) -> list[list[int]]:
    stage = canonical_transform(value)
    source_parts = [part for part in _components(_grid(value)) if part["color"] == 1]
    source_parts.sort(key=lambda part: (part["r1"], part["c1"]))
    out = [row[:] for row in stage]
    for left, right in zip(source_parts, source_parts[1:]):
        _paint_hv(out, _center(left), _center(right))
    return out


def named_rivals(mode: str) -> dict[str, Callable[[Any], list[list[int]]]]:
    if mode == "canonical":
        return {
            "recolor_every_blue_component": _rival_all_blue,
            "recolor_any_exact_3x3": _rival_any_color_3x3,
            "add_waypoint_bridges": bridge_transform,
        }
    if mode == "bridge_centers":
        return {
            "canonical_only": canonical_transform,
            "bridge_all_blue_components": _rival_bridge_all_blue,
            "connect_only_first_and_last": lambda g: bridge_transform(g, first_last_only=True),
            "vertical_then_horizontal": lambda g: bridge_transform(g, vertical_first=True),
        }
    raise ValueError(mode)


def teaching_audit(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain train and test lists")
    selected = None
    for mode in MODES:
        if episode.get("program_solution") == program({"mode": mode}):
            selected = mode
            break
    if selected is None:
        raise ValueError("episode program is not a declared mode")
    survivors = [
        mode
        for mode in MODES
        if all(transform(pair["input"], mode) == pair["output"] for pair in episode["train"])
    ]
    harmful = []
    for name, rival in named_rivals(selected).items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {
        "declared_setting_survivors": survivors,
        "query_disagreeing_named_survivors": harmful,
        "named_rivals_checked": sorted(named_rivals(selected)),
    }


def _shape_bounds(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _place_shape(grid: list[list[int]], shape: tuple[tuple[int, int], ...], color: int, rng: random.Random) -> None:
    h, w = len(grid), len(grid[0])
    sh, sw = _shape_bounds(shape)
    candidates = [(r, c) for r in range(1, h - sh) for c in range(1, w - sw)]
    rng.shuffle(candidates)
    for r0, c0 in candidates:
        cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
        halo = {
            (r, c)
            for rr, cc in cells
            for r in range(max(0, rr - 1), min(h, rr + 2))
            for c in range(max(0, cc - 1), min(w, cc + 2))
        }
        if all(grid[r][c] == 0 for r, c in halo):
            for r, c in cells:
                grid[r][c] = color
            return
    raise RuntimeError("could not place separated shape")


def _scene(seed: int, split: str, index: int, profile: tuple[int, int, int, int, int]) -> list[list[int]]:
    h, w, target_count, distractor_count, decor_count = profile
    digest = hashlib.sha256(f"{TASK_ID}|waypoints-v1|{seed}|{split}|{index}".encode()).digest()
    rng = random.Random(digest)
    for attempt in range(64):
        local = random.Random(hashlib.sha256(digest + attempt.to_bytes(2, "big")).digest())
        grid = [[0 for _ in range(w)] for _ in range(h)]
        objects: list[tuple[tuple[tuple[int, int], ...], int]] = []
        objects.extend((_SOLID_3, 1) for _ in range(target_count))
        distractors = [local.choice(_BLUE_DISTRACTORS) for _ in range(distractor_count)]
        if distractor_count >= 3:
            distractors[:3] = [_BLUE_DISTRACTORS[0], _BLUE_DISTRACTORS[3], _BLUE_DISTRACTORS[4]]
        objects.extend((shape, 1) for shape in distractors)
        palette = [2, 4, 5, 6, 7, 8, 9]
        local.shuffle(palette)
        if decor_count:
            objects.append((_SOLID_3, palette[0]))  # color-agnostic exact-square decoy
        for i in range(1, decor_count):
            objects.append((local.choice(_DECOR_SHAPES), palette[i % len(palette)]))
        local.shuffle(objects)
        try:
            for shape, color in objects:
                _place_shape(grid, shape, color, local)
        except RuntimeError:
            continue
        if local.randrange(2):
            grid = [row[::-1] for row in grid]
        if local.randrange(2):
            grid = grid[::-1]
        facts = analyse(grid)
        if facts["targets"] != target_count or facts["blue_distractors"] < distractor_count:
            continue
        canonical = canonical_transform(grid)
        bridge = bridge_transform(grid)
        if canonical == bridge:
            continue
        if bridge == bridge_transform(grid, vertical_first=True):
            continue
        if target_count >= 3 and bridge == bridge_transform(grid, first_last_only=True):
            continue
        if bridge == _rival_bridge_all_blue(grid):
            continue
        return grid
    raise RuntimeError("could not construct a distinguishing waypoint scene")


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
    def pairs(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        return [
            {"input": deepcopy(grid), "output": transform(grid, mode)}
            for grid in inputs[split][:count]
        ]
    return {
        "train": pairs("train", demos),
        "test": pairs("test", queries),
        "program_solution": program({"mode": mode}),
    }


def analyse(value: Any) -> dict[str, Any]:
    source = _grid(value)
    parts = _components(source)
    targets = [part for part in parts if _is_target(part)]
    blue = [part for part in parts if part["color"] == 1]
    return {
        "height": len(source),
        "width": len(source[0]),
        "components": len(parts),
        "targets": len(targets),
        "blue_distractors": len(blue) - len(targets),
        "nonzero": sum(cell != 0 for row in source for cell in row),
        "palette": sorted({cell for row in source for cell in row}),
    }


def dependency_trace(value: Any) -> dict[str, Any]:
    source = _grid(value)
    intermediate = canonical_transform(source)
    waypoints = [part for part in _components(intermediate) if part["color"] == 3]
    output = bridge_transform(source)
    skip_a_output = _grid(source)  # the stage-B program sees no color-3 waypoint in an input
    return {
        "step_a": "recolor exact solid blue 3x3 components to color 3",
        "intermediate": intermediate,
        "derived_waypoints": len(waypoints),
        "step_b": "connect derived color-3 component centers in reading order",
        "output": output,
        "skip_a_output": skip_a_output,
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index out of range")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
