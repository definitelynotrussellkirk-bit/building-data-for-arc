"""Native parametric family for ARC task ``2602c3d31d21``.

The default setting is the exact canonical sum-of-squared-pairwise-distances
rule.  The nearby setting keeps the whole program fixed and substitutes
Manhattan distance in the per-shape signature.  Input construction is metric-
independent so paired settings receive exactly matched lessons.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root


TASK_ID = "2602c3d31d21"
PARAMETER_NAME = "metric"
METRICS = ("squared_euclidean", "manhattan")
DEFAULT_METRIC = "squared_euclidean"
CANONICAL_SHA256 = "a99125d5b90022542887f6e79b1b36dd0a976abd38724b2d59f766eddf5a1c5d"
PROTOTYPE_VERSION = "pairwise-metric-v1"
HERE = Path(__file__).resolve().parent

_SQUARED_EXPRESSION = """(+ (* (- (first c1) (first c2))
                                               (- (first c1) (first c2)))
                                            (* (- (second c1) (second c2))
                                               (- (second c1) (second c2))))"""
_MANHATTAN_EXPRESSION = """(+ (abs (- (first c1) (first c2)))
                                            (abs (- (second c1) (second c2))))"""


def _load_local_module(module_name: str, filename: str):
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load local module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ORACLE = _load_local_module("parametric_2602c3d31d21_oracle", "oracle.py")


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a plain integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_metric(metric: Any) -> str:
    return _ORACLE.validate_metric(metric)


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    if type(demos) is not int:
        raise TypeError("demos must be a plain integer (not bool)")
    if not 2 <= demos <= 6:
        raise ValueError("demos must lie in 2..6")
    if type(queries) is not int:
        raise TypeError("queries must be a plain integer (not bool)")
    if not 1 <= queries <= 4:
        raise ValueError("queries must lie in 1..4")
    return demos, queries


def canonical_program() -> str:
    """Return the exact canonical Racket source, guarded by its byte hash."""
    programs = {
        row["program_solution"]
        for line in canonical_path(find_root(__file__)).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise RuntimeError(f"expected one unique canonical program, found {len(programs)}")
    source = programs.pop()
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if digest != CANONICAL_SHA256:
        raise RuntimeError(
            f"canonical source hash changed: expected {CANONICAL_SHA256}, got {digest}"
        )
    if source.count(_SQUARED_EXPRESSION) != 1:
        raise RuntimeError("canonical distance expression is not uniquely replaceable")
    return source


def rule_text(metric: Any) -> str:
    """Return exact Racket source for one declared metric."""
    selected = _validate_metric(metric)
    source = canonical_program()
    if selected == DEFAULT_METRIC:
        return source
    return source.replace(_SQUARED_EXPRESSION, _MANHATTAN_EXPRESSION, 1)


def restore_canonical(source: Any) -> str:
    """Reverse the one guarded Manhattan substitution and verify exact bytes."""
    if type(source) is not str:
        raise TypeError("source must be a string")
    if source.count(_MANHATTAN_EXPRESSION) != 1:
        raise ValueError("alternate source does not contain exactly one Manhattan expression")
    restored = source.replace(_MANHATTAN_EXPRESSION, _SQUARED_EXPRESSION, 1)
    canonical = canonical_program()
    if restored != canonical:
        raise ValueError("alternate source differs from canonical outside the guarded expression")
    return restored


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    materialized = tuple(cells)
    top = min(row for row, _col in materialized)
    left = min(col for _row, col in materialized)
    return tuple(sorted((row - top, col - left) for row, col in materialized))


def _transform(
    cells: tuple[tuple[int, int], ...], transform: int
) -> tuple[tuple[int, int], ...]:
    points: list[tuple[int, int]] = []
    for row, col in cells:
        x, y = row, -col if transform >= 4 else col
        for _ in range(transform % 4):
            x, y = y, -x
        points.append((x, y))
    return _normalize(points)


def _large_l() -> tuple[tuple[int, int], ...]:
    return tuple(sorted({*((row, 0) for row in range(8)), *((7, col) for col in range(7))}))


_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "l3": ((0, 0), (0, 1), (1, 0)),
    "i3": ((0, 0), (0, 1), (0, 2)),
    "o4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "i4": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "x5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "p5": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    "hook5": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    "zig5": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    "big_l14": _large_l(),
    "rect16": tuple((row, col) for row in range(4) for col in range(4)),
}

_DEMO_PROFILES: tuple[tuple[str, int, int, tuple[str, ...]], ...] = (
    ("dual-collision", 12, 16, ("l3", "i3", "hook5", "zig5")),
    ("line-cross-collision", 11, 15, ("i4", "x5", "o4")),
    ("mixed-six", 18, 20, ("l3", "i3", "o4", "t4", "i4", "x5")),
    ("late-collision", 13, 17, ("hook5", "zig5", "l3")),
    ("three-way-squared", 15, 19, ("i4", "x5", "p5", "o4")),
    ("mixed-seven", 22, 24, ("l3", "i3", "hook5", "zig5", "i4", "x5", "o4")),
)
_QUERY_PROFILES: tuple[tuple[str, int, int, tuple[str, ...]], ...] = (
    ("novel-five", 14, 18, ("l3", "i3", "o4", "hook5", "zig5")),
    ("novel-four", 16, 21, ("i4", "x5", "t4", "l3")),
    ("novel-six", 20, 23, ("hook5", "zig5", "p5", "i4", "x5", "o4")),
)


def _stream_rng(seed: int, stream: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{stream}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _palette(seed: int, profile: str, count: int) -> list[int]:
    values = list(range(1, 10))
    _stream_rng(seed, f"{profile}:palette").shuffle(values)
    return values[:count]


def _place_random_profile(
    seed: int,
    profile: str,
    height: int,
    width: int,
    shape_names: tuple[str, ...],
) -> list[list[int]]:
    if len(shape_names) > 7:
        raise ValueError("canonical matrix construction supports at most seven shapes")
    grid = _blank(height, width)
    occupied: set[tuple[int, int]] = set()
    colors = _palette(seed, profile, len(shape_names))

    for index, (color, shape_name) in enumerate(zip(colors, shape_names)):
        rng = _stream_rng(seed, f"{profile}:shape:{index}")
        variants = sorted({_transform(_SHAPES[shape_name], transform) for transform in range(8)})
        candidates = [
            cells
            for cells in variants
            if max(row for row, _col in cells) < height
            and max(col for _row, col in cells) <= width - 3
        ]
        if not candidates:
            raise RuntimeError(f"shape {shape_name} cannot fit profile {profile}")
        cells = candidates[rng.randrange(len(candidates))]
        shape_height = max(row for row, _col in cells) + 1
        shape_width = max(col for _row, col in cells) + 1
        anchors = [
            (row, col)
            for row in range(height - shape_height + 1)
            for col in range((width - 2) - shape_width + 1)
        ]
        rng.shuffle(anchors)
        for anchor_row, anchor_col in anchors:
            absolute = {
                (anchor_row + row, anchor_col + col) for row, col in cells
            }
            if absolute.isdisjoint(occupied):
                occupied.update(absolute)
                for row, col in absolute:
                    grid[row][col] = color
                break
        else:
            raise RuntimeError(f"could not place shape {shape_name} in profile {profile}")

    key_rng = _stream_rng(seed, f"{profile}:keys")
    key_rows = sorted(key_rng.sample(range(height), len(colors)))
    for row, color in zip(key_rows, colors):
        grid[row][width - 1] = color
    _ORACLE.analyze_input(grid)
    return grid


def _place(
    grid: list[list[int]],
    cells: tuple[tuple[int, int], ...],
    anchor: tuple[int, int],
    color: int,
) -> None:
    height, width = len(grid), len(grid[0])
    for dr, dc in cells:
        row, col = anchor[0] + dr, anchor[1] + dc
        if not (0 <= row < height and 0 <= col < width - 1):
            raise RuntimeError("fixed stress shape escaped the body canvas")
        if grid[row][col] != 0:
            raise RuntimeError("fixed stress shapes overlap")
        grid[row][col] = color


def _large_profile(seed: int) -> list[list[int]]:
    profile = "exact-30x30-seven"
    grid = _blank(30, 30)
    colors = _palette(seed, profile, 7)
    placements = (
        (_SHAPES["l3"], (0, 0)),
        (_SHAPES["i3"], (0, 24)),
        (_SHAPES["hook5"], (28, 0)),
        (_SHAPES["zig5"], (27, 25)),
        (_SHAPES["big_l14"], (7, 2)),
        (_transform(_SHAPES["big_l14"], 1), (9, 18)),
        (_SHAPES["rect16"], (19, 11)),
    )
    for color, (cells, anchor) in zip(colors, placements):
        _place(grid, cells, anchor, color)
    for row, color in zip((1, 4, 8, 12, 17, 23, 28), colors):
        grid[row][29] = color
    _ORACLE.analyze_input(grid)
    return grid


def select_inputs(seed: Any, *, demos: Any, queries: Any) -> dict[str, list[dict[str, Any]]]:
    """Select distinct matched inputs without consulting the hidden metric."""
    selected_seed = _validate_seed(seed)
    demo_count, query_count = _validate_counts(demos, queries)
    train = [
        {
            "profile": profile,
            "input": _place_random_profile(
                selected_seed, f"demo:{profile}", height, width, shapes
            ),
        }
        for profile, height, width, shapes in _DEMO_PROFILES[:demo_count]
    ]
    ordinary_query_rows = [
        {
            "profile": profile,
            "input": _place_random_profile(
                selected_seed, f"query:{profile}", height, width, shapes
            ),
        }
        for profile, height, width, shapes in _QUERY_PROFILES
    ]
    all_queries = ordinary_query_rows + [
        {"profile": "exact-30x30-seven", "input": _large_profile(selected_seed)}
    ]
    test = all_queries[:query_count]
    keys = [
        json.dumps(row["input"], separators=(",", ":"), allow_nan=False)
        for row in train + test
    ]
    if len(set(keys)) != len(keys):
        raise RuntimeError("selected demonstration/query inputs are not distinct")
    return {"train": train, "test": test}


def analyze_input(grid: Any) -> dict[str, Any]:
    return _ORACLE.analyze_input(grid)


def output_for(grid: Any, metric: Any) -> list[list[int]]:
    return _ORACLE.output_for(grid, metric)


def generate_episode(
    seed: Any,
    *,
    metric: Any,
    demos: Any,
    queries: Any,
) -> dict[str, Any]:
    """Build one fixed-rule episode under the native adapter contract."""
    selected_seed = _validate_seed(seed)
    selected_metric = _validate_metric(metric)
    demo_count, query_count = _validate_counts(demos, queries)
    selected = select_inputs(selected_seed, demos=demo_count, queries=query_count)

    def label(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "input": copy.deepcopy(row["input"]),
                "output": output_for(row["input"], selected_metric),
            }
            for row in rows
        ]

    episode = {
        "train": label(selected["train"]),
        "test": label(selected["test"]),
        "program_solution": rule_text(selected_metric),
    }
    rival = next(metric_name for metric_name in METRICS if metric_name != selected_metric)
    if not any(
        output_for(pair["input"], rival) != pair["output"] for pair in episode["train"]
    ):
        raise RuntimeError("demonstrations do not identify the selected metric")
    return episode
