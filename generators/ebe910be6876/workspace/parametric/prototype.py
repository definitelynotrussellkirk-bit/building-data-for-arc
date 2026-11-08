"""Native parametric family for task ebe910be6876.

``expand_only`` is the exact canonical marker-to-4x4-block expansion.
``mark_largest_cluster`` first performs that expansion, then treats every
nonzero expanded cell as occupied, finds the largest 4-connected occupied
cluster (row-major first on an exact tie), and recolors that entire cluster 9.
The second step therefore consumes connectivity created by the first step.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any


TASK_ID = "ebe910be6876"
VERSION = "2.0.0"
FINISHES = ("expand_only", "mark_largest_cluster")
SETTINGS = tuple({"finish": value} for value in FINISHES)
DEFAULT = {"finish": "expand_only"}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
CANONICAL_SHA256 = "2c453a5303bbcb8a448c51fdbb03f734d935eb44cfe39d85751094749132068c"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parents[1] / "generator.py"
RIVAL_NAMES = (
    "first_input_marker",
    "smallest_cluster",
    "largest_same_color",
    "largest_8_connected",
)


def _load_generator():
    body = GENERATOR_PATH.read_bytes()
    name = "_parametric_ebe910be6876_generator_" + hashlib.sha256(
        str(GENERATOR_PATH).encode() + body
    ).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {GENERATOR_PATH}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _finish(settings: Any) -> str:
    if (
        not isinstance(settings, dict)
        or set(settings) != {"finish"}
        or type(settings["finish"]) is not str
        or settings["finish"] not in FINISHES
    ):
        raise ValueError(
            "settings must be exactly "
            "{'finish': 'expand_only|mark_largest_cluster'}"
        )
    return settings["finish"]


def _source(name: str, expected_sha256: str | None = None) -> str:
    raw = (HERE / name).read_bytes()
    if not raw.strip():
        raise ValueError(f"empty Racket source: {name}")
    observed = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and observed != expected_sha256:
        raise ValueError(f"{name} drifted: {observed}")
    return raw.decode("utf-8")


@lru_cache(maxsize=1)
def canonical_source() -> str:
    return _source("canonical.rkt", CANONICAL_SHA256)


@lru_cache(maxsize=1)
def largest_cluster_source() -> str:
    return _source("largest_cluster.rkt")


def program(settings: Any) -> str:
    finish = _finish(settings)
    return canonical_source() if finish == "expand_only" else largest_cluster_source()


def counterfactual_program() -> str:
    return _source("first_input_marker.rkt")


def rival_programs() -> dict[str, str]:
    return {
        "first_input_marker": _source("first_input_marker.rkt"),
        "smallest_cluster": _source("smallest_cluster.rkt"),
        "largest_same_color": _source("largest_same_color.rkt"),
        "largest_8_connected": _source("largest_8_connected.rkt"),
    }


def _validated_grid(grid: Any) -> list[list[int]]:
    errors = _GEN.self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    return _GEN._coerce_grid(grid)


def _components(
    grid: list[list[int]],
    *,
    connectivity: int = 4,
    same_color: bool = False,
) -> list[list[tuple[int, int]]]:
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    deltas = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        deltas = tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if dr or dc
        )
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    groups: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            value = grid[start_row][start_col]
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in deltas:
                    rr, cc = row + dr, col + dc
                    if not (0 <= rr < height and 0 <= cc < width):
                        continue
                    if (rr, cc) in seen or grid[rr][cc] == 0:
                        continue
                    if same_color and grid[rr][cc] != value:
                        continue
                    seen.add((rr, cc))
                    queue.append((rr, cc))
            groups.append(sorted(cells))
    return groups


def _paint_cells(grid: list[list[int]], cells, color: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    for row, col in cells:
        result[row][col] = color
    return result


def intermediate(grid: Any) -> dict[str, Any]:
    checked = _validated_grid(grid)
    expanded = _GEN.rule_mirror(checked)
    clusters = _components(expanded)
    if not clusters:
        raise ValueError("task input must contain at least one marker")
    target = max(clusters, key=len)
    return {
        "expanded": expanded,
        "clusters": [[list(cell) for cell in cluster] for cluster in clusters],
        "cluster_sizes": [len(cluster) for cluster in clusters],
        "target_cells": [list(cell) for cell in target],
    }


def solve(grid: Any, *, finish: str = "expand_only") -> list[list[int]]:
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    info = intermediate(grid)
    if finish == "expand_only":
        return deepcopy(info["expanded"])
    return _paint_cells(info["expanded"], info["target_cells"], 9)


def _first_marker_tile(grid: list[list[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                sr, sc = 2 * row - 2, 2 * col - 2
                return [
                    (rr, cc)
                    for rr in range(sr, sr + 4)
                    for cc in range(sc, sc + 4)
                    if 0 <= rr < 2 * height and 0 <= cc < 2 * width
                ]
    raise ValueError("task input must contain a marker")


def rival_solve(grid: Any, name: str) -> list[list[int]]:
    if name not in RIVAL_NAMES:
        raise ValueError(f"unknown rival {name!r}")
    checked = _validated_grid(grid)
    expanded = _GEN.rule_mirror(checked)
    if name == "first_input_marker":
        target = _first_marker_tile(checked)
    elif name == "smallest_cluster":
        target = min(_components(expanded), key=len)
    elif name == "largest_same_color":
        target = max(_components(expanded, same_color=True), key=len)
    else:
        target = max(_components(expanded, connectivity=8), key=len)
    return _paint_cells(expanded, target, 9)


# Logical coordinates map to odd input cells (2r+1, 2c+1). Each profile lists
# separate 4-connected clusters and one abstract color label per marker.
_DEMO_PROFILES = (
    {
        "shape": (10, 12),
        "clusters": (
            ((2, 0), (3, 0), (3, 1), (4, 1), (4, 2)),
            ((0, 0), (0, 1), (0, 2)),
            ((1, 3), (1, 4), (1, 5)),
        ),
        "labels": ((1, 2, 3, 4, 5), (0, 0, 0), (0, 0, 0)),
        "tag": "mixed_largest_vs_diagonal_same_color_decoys",
        "fixed_orientation": True,
    },
    {
        "shape": (8, 10),
        "clusters": (
            ((0, 3), (0, 4), (1, 3), (2, 3)),
            ((2, 0), (3, 0), (3, 1)),
            ((3, 4),),
        ),
        "labels": ((0, 0, 0, 0), (1, 2, 1), (3,)),
        "tag": "solid_target_with_corner_decoy",
    },
    {
        "shape": (12, 12),
        "clusters": (
            ((1, 3), (1, 4), (2, 3), (3, 3), (3, 4), (4, 4)),
            ((0, 0), (0, 1), (1, 0), (2, 0)),
            ((4, 0), (5, 0)),
        ),
        "labels": ((0, 1, 2, 3, 4, 5), (2, 2, 2, 2), (3, 4)),
        "tag": "six_tile_stair",
    },
    {
        "shape": (13, 11),
        "clusters": (
            ((0, 3), (1, 3), (2, 3), (2, 4), (3, 4)),
            ((1, 0), (2, 0), (3, 0), (3, 1)),
            ((5, 1), (5, 2), (5, 3)),
        ),
        "labels": ((0, 1, 0, 2, 3), (4, 4, 4, 4), (5, 1, 5)),
        "tag": "right_hook",
    },
    {
        "shape": (14, 15),
        "clusters": (
            ((0, 4), (1, 4), (2, 4), (2, 5), (3, 5), (4, 5), (4, 6)),
            ((0, 0), (0, 1), (1, 0), (2, 0)),
            ((5, 1), (6, 1)),
        ),
        "labels": ((0, 1, 2, 3, 4, 5, 0), (2, 2, 2, 2), (3, 4)),
        "tag": "seven_tile_edge_chain",
    },
    {
        "shape": (15, 14),
        "clusters": (
            ((3, 2), (3, 3), (3, 4), (4, 4), (5, 4), (5, 5)),
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
            ((5, 0), (6, 0), (6, 1)),
        ),
        "labels": ((0, 1, 2, 3, 4, 5), (2, 2, 2, 2, 2), (1, 3, 1)),
        "tag": "near_max_marker_count",
    },
)

_QUERY_PROFILES = (
    {
        "shape": (6, 8),
        "clusters": (
            ((0, 2), (0, 3), (1, 2), (2, 2)),
            ((0, 0), (1, 0)),
        ),
        "labels": ((0, 1, 2, 3), (4, 4)),
        "tag": "minimum_canvas",
    },
    {
        "shape": (9, 13),
        "clusters": (
            ((0, 4), (0, 5), (1, 4), (2, 4), (2, 5)),
            ((1, 0), (2, 0), (3, 0), (3, 1)),
        ),
        "labels": ((0, 1, 2, 3, 4), (5, 5, 5, 5)),
        "tag": "rectangular_medium",
    },
    {
        "shape": (14, 15),
        "clusters": (
            ((2, 4), (2, 5), (3, 4), (4, 4), (4, 5), (5, 5)),
            ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
            ((5, 0), (6, 0), (6, 1)),
        ),
        "labels": ((0, 1, 2, 3, 4, 5), (2, 2, 2, 2, 2), (3, 4, 3)),
        "tag": "thirty_column_stress",
    },
    {
        "shape": (15, 15),
        "clusters": (
            ((1, 5), (1, 6), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5)),
            ((0, 0), (0, 1), (1, 0), (2, 0)),
            ((4, 1), (5, 1), (6, 1)),
        ),
        "labels": ((0, 1, 2, 3, 4, 5, 0), (2, 2, 2, 2), (1, 3, 1)),
        "tag": "exact_30x30_full_spread",
    },
)


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _transform(point: tuple[int, int], rows: int, cols: int, code: int):
    row, col = point
    if code & 1:
        col = cols - 1 - col
    if code & 2:
        row = rows - 1 - row
    return row, col


def _build_profile(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    spec = profiles[index]
    height, width = spec["shape"]
    logical_rows, logical_cols = height // 2, width // 2
    rng = _rng(seed, split, index)
    code = 0 if spec.get("fixed_orientation") else rng.randrange(4)
    labels = sorted({value for group in spec["labels"] for value in group})
    palette = rng.sample(list(range(1, 9)), len(labels))
    color_for = dict(zip(labels, palette))
    grid = [[0] * width for _ in range(height)]
    for cluster, group_labels in zip(spec["clusters"], spec["labels"]):
        if len(cluster) != len(group_labels):
            raise AssertionError("profile color labels differ from marker count")
        for point, label in zip(cluster, group_labels):
            logical_row, logical_col = _transform(
                point, logical_rows, logical_cols, code
            )
            row, col = 2 * logical_row + 1, 2 * logical_col + 1
            if grid[row][col] != 0:
                raise AssertionError("profile transform caused a marker collision")
            grid[row][col] = color_for[label]
    errors = _GEN.self_check(grid)
    if errors:
        raise AssertionError({"tag": spec["tag"], "errors": errors})
    info = intermediate(grid)
    sizes = sorted(info["cluster_sizes"], reverse=True)
    if len(sizes) < 2 or sizes[0] == sizes[1]:
        raise AssertionError({"tag": spec["tag"], "cluster_sizes": sizes})
    return grid


@lru_cache(maxsize=1024)
def _scene_tuple(seed: int, split: str, index: int):
    return tuple(tuple(row) for row in _build_profile(seed, split, index))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _scene_tuple(seed, split, index)]


def sample_inputs(seed: Any, demos: Any = 3, queries: Any = 4) -> dict[str, list]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, *DEMO_LIMITS)
    queries = _integer("queries", queries, *QUERY_LIMITS)
    result = {
        "train": [_scene(seed, "train", index) for index in range(demos)],
        "test": [_scene(seed, "test", index) for index in range(queries)],
    }
    keys = [
        json.dumps(grid, separators=(",", ":"))
        for split in ("train", "test")
        for grid in result[split]
    ]
    if len(keys) != len(set(keys)):
        raise AssertionError("all generated inputs must be distinct")
    return result


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4):
    finish = _finish(settings)
    sampled = sample_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": deepcopy(grid), "output": solve(grid, finish=finish)}
            for grid in sampled["train"]
        ],
        "test": [
            {"input": deepcopy(grid), "output": solve(grid, finish=finish)}
            for grid in sampled["test"]
        ],
        "program_solution": program(settings),
        "settings": deepcopy(settings),
        "sampler": {
            "version": VERSION,
            "demo_profiles": [p["tag"] for p in _DEMO_PROFILES[:demos]],
            "query_profiles": [p["tag"] for p in _QUERY_PROFILES[:queries]],
        },
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, list]:
    if not isinstance(episode, dict) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain a test list")
    query_index = _integer(
        "query_index", query_index, 0, len(episode["test"]) - 1
    )
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def describe(grid: Any, settings: Any) -> dict[str, Any]:
    finish = _finish(settings)
    info = intermediate(grid)
    return {
        "finish": finish,
        "input_shape": [len(grid), len(grid[0])],
        "output_shape": [len(info["expanded"]), len(info["expanded"][0])],
        "cluster_sizes": info["cluster_sizes"],
        "target_size": len(info["target_cells"]),
    }
