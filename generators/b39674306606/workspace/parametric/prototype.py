"""Source-bound exact-shape frequency family for ARC task b39674306606.

The canonical setting paints the sole translation-normalized shape occurring
once.  The alternative paints every object belonging to the unique most
frequent exact shape class.  Inputs are matched across settings and contain one
singleton, one pair, and one triple of exact shapes.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

from reviewer_support import public_challenge_bytes

TASK_ID = "b39674306606"
VERSION = "exact-shape-frequency-target-v1"
FREQUENCY_TARGETS = ("singleton", "most_frequent")
DEFAULT_FREQUENCY_TARGET = "singleton"
HERE = Path(__file__).resolve().parent
Shape = frozenset[tuple[int, int]]


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"frequency_target"}:
        raise ValueError("settings must contain exactly frequency_target")
    value = settings["frequency_target"]
    if type(value) is not str or value not in FREQUENCY_TARGETS:
        raise ValueError("frequency_target must be singleton or most_frequent")
    return value


def _count(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _seed(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    return value


def program_for(frequency_target: str) -> str:
    if frequency_target not in FREQUENCY_TARGETS:
        raise ValueError(f"unsupported frequency_target: {frequency_target!r}")
    filename = "canonical.rkt" if frequency_target == "singleton" else "most_frequent.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def program(settings: Any) -> str:
    return program_for(validate_settings(settings))


def _strict_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return deepcopy(grid)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _shape(pattern: tuple[str, ...]) -> Shape:
    cells = frozenset((r, c) for r, row in enumerate(pattern)
                      for c, value in enumerate(row) if value == "#")
    if not cells:
        raise ValueError("shape cannot be empty")
    return frozenset(_normalize(cells))


def _bbox_size(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _rotate_cw(shape: Shape) -> Shape:
    height, _ = _bbox_size(shape)
    return frozenset(_normalize((c, height - 1 - r) for r, c in shape))


def _flip_lr(shape: Shape) -> Shape:
    _, width = _bbox_size(shape)
    return frozenset(_normalize((r, width - 1 - c) for r, c in shape))


def _d4_variants(shape: Shape) -> tuple[Shape, ...]:
    variants: set[Shape] = set()
    current = shape
    for _ in range(4):
        variants.add(current)
        variants.add(_flip_lr(current))
        current = _rotate_cw(current)
    return tuple(sorted(variants, key=lambda value: tuple(sorted(value))))


def _d4_key(shape_key: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    variants = _d4_variants(frozenset(shape_key))
    return min(tuple(sorted(value)) for value in variants)


# Each pair has equal cell count and equal bounding-box area, but belongs to a
# different D4 orbit.  The singleton is a rotated/reflected instance of the pair
# shape, making size-only and D4-invariant shortcuts visibly wrong.
SHAPE_FAMILIES: tuple[tuple[Shape, Shape], ...] = (
    (_shape(("#.", "#.", "##")), _shape((".##", "##."))),
    (_shape(("#.#", "###")), _shape(("##", "##", "#."))),
    (_shape(("##.", "###", "..#")), _shape(("#..", "##.", "###"))),
    (_shape(("###", "##.", "##.")), _shape(("##.", "###", ".##"))),
    (_shape(("###", "###", "##.")), _shape(("###", "#.#", "###"))),
    (
        _shape(("#####", "#...#", "###.#", "#.#.#", "####.")),
        _shape(("#####", "###..", "..###", "###..", "####.")),
    ),
)
for _pair_shape, _most_shape in SHAPE_FAMILIES:
    if len(_pair_shape) != len(_most_shape):
        raise AssertionError("shape family areas differ")
    if _d4_key(tuple(sorted(_pair_shape))) == _d4_key(tuple(sorted(_most_shape))):
        raise AssertionError("shape family must use distinct D4 classes")
    if len(_d4_variants(_pair_shape)) < 2:
        raise AssertionError("pair shape needs a non-identical D4 variant")
    if _bbox_size(_pair_shape)[0] * _bbox_size(_pair_shape)[1] != (
            _bbox_size(_most_shape)[0] * _bbox_size(_most_shape)[1]):
        raise AssertionError("shape family bounding-box areas differ")


DEMO_SPECS = (
    ((12, 15), 0),
    ((13, 17), 1),
    ((14, 19), 2),
    ((16, 20), 3),
    ((18, 22), 4),
    ((20, 24), 2),
)
QUERY_SPECS = (
    ((15, 16), 1),
    ((19, 23), 3),
    ((24, 27), 4),
    ((30, 30), 5),
)
ROLE_PATTERNS = (
    ("pair", "most", "pair", "most", "singleton", "most"),
    ("most", "singleton", "pair", "most", "pair", "most"),
    ("pair", "most", "singleton", "pair", "most", "most"),
    ("most", "pair", "most", "singleton", "most", "pair"),
)


def _rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}/{VERSION}/{seed}/{role}/{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells_tuple = tuple(sorted(cells))
            key = _normalize(cells_tuple)
            top = min(r for r, _ in cells_tuple)
            left = min(c for _, c in cells_tuple)
            bottom = max(r for r, _ in cells_tuple)
            right = max(c for _, c in cells_tuple)
            result.append({
                "color": color,
                "cells": cells_tuple,
                "shape": key,
                "area": len(cells_tuple),
                "bbox": (top, left, bottom, right),
                "bbox_area": (bottom - top + 1) * (right - left + 1),
                "top_left": (top, left),
            })
    result.sort(key=lambda obj: obj["top_left"])
    return result


def analyze(grid: Any) -> dict[str, Any]:
    source = _strict_grid(grid)
    components = _components(source)
    if len(components) != 6:
        raise ValueError("prototype inputs require exactly six components")
    frequencies = Counter(obj["shape"] for obj in components)
    values = sorted(frequencies.values())
    if values != [1, 2, 3]:
        raise ValueError(f"shape frequencies must be 1,2,3; got {values}")
    singleton_keys = [key for key, count in frequencies.items() if count == 1]
    max_count = max(frequencies.values())
    max_keys = [key for key, count in frequencies.items() if count == max_count]
    if len(singleton_keys) != 1 or len(max_keys) != 1:
        raise ValueError("frequency targets must be unique")
    return {
        "height": len(source),
        "width": len(source[0]),
        "components": components,
        "frequencies": frequencies,
        "frequency_values": sorted(set(frequencies.values())),
        "singleton_key": singleton_keys[0],
        "most_frequent_key": max_keys[0],
        "max_frequency": max_count,
    }


def _paint(height: int, width: int, components: Iterable[dict[str, Any]]) -> list[list[int]]:
    output = [[0] * width for _ in range(height)]
    for obj in components:
        for row, col in obj["cells"]:
            output[row][col] = 8
    return output


def _select(info: dict[str, Any], policy: str) -> list[dict[str, Any]]:
    objects = info["components"]
    frequencies = info["frequencies"]
    if policy == "singleton":
        return [obj for obj in objects if frequencies[obj["shape"]] == 1]
    if policy == "most_frequent":
        return [obj for obj in objects if frequencies[obj["shape"]] == info["max_frequency"]]
    if policy == "leftmost":
        return [min(objects, key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))]
    if policy == "rightmost":
        return [max(objects, key=lambda obj: (obj["bbox"][3], obj["bbox"][2]))]
    if policy == "frequency_two":
        return [obj for obj in objects if frequencies[obj["shape"]] == 2]
    if policy == "all_repeated":
        return [obj for obj in objects if frequencies[obj["shape"]] > 1]
    if policy == "first_most_instance":
        return [next(obj for obj in objects if frequencies[obj["shape"]] == info["max_frequency"])]
    if policy in {"d4_singleton", "d4_most_frequent"}:
        d4_counts = Counter(_d4_key(obj["shape"]) for obj in objects)
        if policy == "d4_singleton":
            return [obj for obj in objects if d4_counts[_d4_key(obj["shape"])] == 1]
        maximum = max(d4_counts.values())
        return [obj for obj in objects if d4_counts[_d4_key(obj["shape"])] == maximum]
    if policy == "all_components":
        return list(objects)
    if policy in {"color_rarest", "color_most"}:
        counts = Counter(obj["color"] for obj in objects)
        target = min(counts.values()) if policy == "color_rarest" else max(counts.values())
        return [obj for obj in objects if counts[obj["color"]] == target]
    if policy in {"bbox_smallest", "bbox_largest"}:
        target = (min(obj["bbox_area"] for obj in objects) if policy == "bbox_smallest"
                  else max(obj["bbox_area"] for obj in objects))
        return [obj for obj in objects if obj["bbox_area"] == target]
    raise ValueError(f"unknown policy: {policy}")


RIVAL_POLICIES = (
    "leftmost",
    "rightmost",
    "frequency_two",
    "all_repeated",
    "first_most_instance",
    "d4_singleton",
    "d4_most_frequent",
    "all_components",
    "color_rarest",
    "color_most",
    "bbox_smallest",
    "bbox_largest",
)


def solve_python(grid: Any, policy: str) -> list[list[int]]:
    if policy not in FREQUENCY_TARGETS and policy not in RIVAL_POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    info = analyze(grid)
    return _paint(info["height"], info["width"], _select(info, policy))


def _anchor(height: int, width: int, shape: Shape, slot: int) -> tuple[int, int]:
    shape_h, shape_w = _bbox_size(shape)
    row_band, col_band = divmod(slot, 3)
    top = 0 if row_band == 0 else height - shape_h
    if col_band == 0:
        left = 0
    elif col_band == 1:
        left = (width - shape_w) // 2
    else:
        left = width - shape_w
    return top, left


def _scene(seed: int, role: str, index: int) -> list[list[int]]:
    specs = DEMO_SPECS if role == "demo" else QUERY_SPECS
    (height, width), family_index = specs[index]
    rng = _rng(seed, role, index)
    pair_base, most_base = SHAPE_FAMILIES[family_index]
    pair_shape = rng.choice(_d4_variants(pair_base))
    singleton_options = [shape for shape in _d4_variants(pair_base) if shape != pair_shape]
    singleton_shape = rng.choice(singleton_options)
    most_shape = rng.choice(_d4_variants(most_base))
    shapes = {"pair": pair_shape, "singleton": singleton_shape, "most": most_shape}
    roles = ROLE_PATTERNS[index % len(ROLE_PATTERNS)]
    colors = rng.sample((1, 2, 3, 4, 5, 6, 7, 9), 6)
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for slot, (kind, color) in enumerate(zip(roles, colors, strict=True)):
        shape = shapes[kind]
        top, left = _anchor(height, width, shape, slot)
        cells = {(top + r, left + c) for r, c in shape}
        if cells & occupied:
            raise RuntimeError("shape placement overlap")
        for row, col in cells:
            grid[row][col] = color
        occupied |= cells
    info = analyze(grid)
    if sorted(info["frequencies"].values()) != [1, 2, 3]:
        raise RuntimeError("constructed frequency profile changed")
    if solve_python(grid, "singleton") == solve_python(grid, "most_frequent"):
        raise RuntimeError("settings failed to separate")
    return grid


def _candidate_policies(frequency_target: str) -> tuple[str, ...]:
    other = "most_frequent" if frequency_target == "singleton" else "singleton"
    return (other, *RIVAL_POLICIES)


def teaching_check(episode: dict[str, Any], frequency_target: str) -> dict[str, Any]:
    if frequency_target not in FREQUENCY_TARGETS:
        raise ValueError("unknown frequency target")
    rows = []
    for policy in _candidate_policies(frequency_target):
        demo_differences = [
            index for index, pair in enumerate(episode["train"])
            if solve_python(pair["input"], policy) != pair["output"]
        ]
        query_differences = []
        if not demo_differences:
            query_differences = [
                index for index, pair in enumerate(episode["test"])
                if solve_python(pair["input"], policy) != pair["output"]
            ]
        rows.append({
            "policy": policy,
            "demo_differences": demo_differences,
            "demo_survives": not demo_differences,
            "query_differences": query_differences,
            "harmful": not demo_differences and bool(query_differences),
        })
    other = "most_frequent" if frequency_target == "singleton" else "singleton"
    return {
        "frequency_target": frequency_target,
        "rival_count": len(rows),
        "rivals": rows,
        "settings_disagree_on_demos": any(
            solve_python(pair["input"], other) != pair["output"] for pair in episode["train"]
        ),
        "demo_survivors": [row["policy"] for row in rows if row["demo_survives"]],
        "harmful_survivors": [row["policy"] for row in rows if row["harmful"]],
    }


def generate_episode(seed: int, *, frequency_target: str, demos: int = 3,
                     queries: int = 4) -> dict[str, Any]:
    _seed(seed)
    if frequency_target not in FREQUENCY_TARGETS:
        raise ValueError("unsupported frequency_target")
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    demo_inputs = [_scene(seed, "demo", index) for index in range(6)]
    query_inputs = [_scene(seed, "query", index) for index in range(4)]
    episode = {
        "train": [{"input": grid, "output": solve_python(grid, frequency_target)}
                  for grid in demo_inputs[:demos]],
        "test": [{"input": grid, "output": solve_python(grid, frequency_target)}
                 for grid in query_inputs[:queries]],
        "program_solution": program_for(frequency_target),
        "settings": {"frequency_target": frequency_target},
        "seed": seed,
    }
    review = teaching_check(episode, frequency_target)
    if review["demo_survivors"] or review["harmful_survivors"]:
        raise AssertionError(f"teaching hole: {review}")
    return episode


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    target = validate_settings(settings)
    episode = generate_episode(seed, frequency_target=target, demos=demos, queries=queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index outside retained test range")
    value = {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
    return json.loads(public_challenge_bytes(value))


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return public_challenge_bytes(public_view(episode, query_index))


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def derived_frequency_table(grid: Any) -> list[dict[str, Any]]:
    """Compact A-stage intermediate retained for the causal witness."""
    info = analyze(grid)
    rows = []
    for key, count in sorted(info["frequencies"].items()):
        rows.append({"shape": [list(cell) for cell in key], "count": count})
    return rows
