"""Parametric frame-selection family for raw count versus occupied density.

Both settings parse exactly the same hollow color-1 frames and compute an
input-dependent table containing each frame's interior box, occupied-cell
count, and area.  The canonical setting chooses the first frame with maximum
raw count.  The alternative chooses the first frame with maximum occupied
fraction, comparing ratios exactly rather than through floating point.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "75be7448827f"
METRICS = ("raw_count", "occupied_density")
DEFAULT_SETTINGS = {"selection_metric": "raw_count"}
HERE = Path(__file__).resolve().parent

# Each frame spec is (top, left, interior-height, interior-width, color, count).
# The profile order is also the canonical reading order.
_DEMO_PROFILES = (
    (14, 18, ((1, 1, 4, 5, 4, 8), (1, 11, 3, 3, 8, 5), (8, 5, 4, 6, 2, 4))),
    (15, 18, ((1, 1, 3, 4, 3, 7), (1, 10, 2, 4, 8, 3), (8, 6, 4, 5, 7, 9))),
    (16, 20, ((1, 1, 5, 6, 2, 12), (1, 12, 4, 5, 6, 10), (10, 8, 3, 3, 4, 3))),
    (18, 22, ((1, 1, 3, 6, 7, 4), (1, 11, 6, 6, 3, 15), (11, 5, 4, 5, 8, 11))),
    (20, 24, ((1, 1, 5, 5, 5, 16), (1, 14, 7, 6, 2, 20), (13, 6, 3, 8, 8, 6))),
    (22, 26, ((1, 1, 4, 7, 6, 7), (1, 16, 5, 6, 4, 18), (12, 8, 7, 8, 7, 25))),
)
_QUERY_PROFILES = (
    (14, 16, ((1, 1, 4, 4, 4, 8), (1, 10, 3, 3, 8, 6), (9, 4, 2, 5, 2, 3))),
    (18, 20, ((1, 1, 4, 4, 3, 11), (1, 12, 5, 6, 7, 14), (12, 6, 3, 5, 8, 5))),
    (24, 26, ((1, 1, 7, 8, 2, 28), (1, 17, 6, 6, 6, 22), (15, 7, 5, 9, 4, 10))),
    (30, 30, ((1, 1, 10, 8, 4, 45), (1, 19, 7, 7, 8, 35), (21, 12, 5, 5, 2, 10))),
)


def _literal_int(name: str, value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be a literal integer in {lower}..{upper}")
    return value


def normalize_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"selection_metric"}:
        raise ValueError("settings must contain exactly selection_metric")
    metric = settings["selection_metric"]
    if type(metric) is not str or metric not in METRICS:
        raise ValueError(f"selection_metric must be one of {METRICS!r}")
    return {"selection_metric": metric}


@lru_cache(maxsize=1)
def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def density_program() -> str:
    return (HERE / "density.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    metric = normalize_settings(settings)["selection_metric"]
    return canonical_program() if metric == "raw_count" else density_program()


def validate_input(value: object) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid height must be 1..30")
    if not value or type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(value[0])
    grid: list[list[int]] = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be literal integers in 0..9")
        grid.append(row[:])
    return grid


def _component(start: tuple[int, int], remaining: set[tuple[int, int]]) -> set[tuple[int, int]]:
    queue = deque([start])
    remaining.remove(start)
    cells = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in remaining:
                remaining.remove(nxt)
                cells.add(nxt)
                queue.append(nxt)
    return cells


def parse_frames(value: object) -> list[dict[str, Any]]:
    grid = validate_input(value)
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1}
    frames: list[dict[str, Any]] = []
    while remaining:
        cells = _component(min(remaining), remaining)
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        if r1 - r0 < 2 or c1 - c0 < 2:
            raise ValueError("color-1 components must be hollow rectangles")
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if cells != border:
            raise ValueError("color-1 components must be exact hollow rectangles")
        ir0, ic0, ir1, ic1 = r0 + 1, c0 + 1, r1 - 1, c1 - 1
        crop = [row[ic0 : ic1 + 1] for row in grid[ir0 : ir1 + 1]]
        occupied = [(r, c) for r in range(ir0, ir1 + 1) for c in range(ic0, ic1 + 1) if grid[r][c] != 0]
        colors = {grid[r][c] for r, c in occupied}
        if 1 in colors:
            raise ValueError("frame interiors may not contain color 1")
        area = (ir1 - ir0 + 1) * (ic1 - ic0 + 1)
        frames.append({
            "bbox": [r0, c0, r1, c1],
            "interior_bbox": [ir0, ic0, ir1, ic1],
            "crop": crop,
            "count": len(occupied),
            "area": area,
            "perimeter": 2 * ((ir1 - ir0 + 1) + (ic1 - ic0 + 1)),
            "colors": sorted(colors),
            "color": min(colors) if colors else 0,
        })
    frames.sort(key=lambda frame: frame["bbox"])
    if not frames:
        raise ValueError("grid needs at least one hollow color-1 frame")
    return frames


def select_frame(frames: object, metric: object) -> dict[str, Any]:
    if type(frames) is not list or not frames:
        raise ValueError("frames must be a nonempty parsed-frame list")
    if type(metric) is not str or metric not in METRICS:
        raise ValueError(f"selection metric must be one of {METRICS!r}")
    best = frames[0]
    for frame in frames[1:]:
        if metric == "raw_count":
            better = frame["count"] > best["count"]
        else:
            better = frame["count"] * best["area"] > best["count"] * frame["area"]
        if better:
            best = frame
    return best


def transform(value: object, metric: object) -> list[list[int]]:
    frames = parse_frames(value)
    return deepcopy(select_frame(frames, metric)["crop"])


def _rng(seed: int, split: str, slot: int, frame_index: int) -> random.Random:
    digest = hashlib.sha256(
        f"75be-selection-metric-v1:{seed}:{split}:{slot}:{frame_index}".encode()
    ).digest()
    return random.Random(digest)


def _paint_frame(
    grid: list[list[int]],
    spec: tuple[int, int, int, int, int, int],
    rng: random.Random,
) -> None:
    r0, c0, ih, iw, color, count = spec
    r1, c1 = r0 + ih + 1, c0 + iw + 1
    if not (0 <= r0 < r1 < len(grid) and 0 <= c0 < c1 < len(grid[0])):
        raise ValueError("frame profile does not fit its grid")
    for c in range(c0, c1 + 1):
        if grid[r0][c] or grid[r1][c]:
            raise ValueError("frame profiles overlap")
        grid[r0][c] = grid[r1][c] = 1
    for r in range(r0 + 1, r1):
        if grid[r][c0] or grid[r][c1]:
            raise ValueError("frame profiles overlap")
        grid[r][c0] = grid[r][c1] = 1
    cells = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    if not 0 <= count <= len(cells):
        raise ValueError("filled-cell count exceeds frame interior")
    for r, c in rng.sample(cells, count):
        grid[r][c] = color


def _build_input(seed: int, split: str, slot: int, profile: tuple) -> list[list[int]]:
    height, width, specs = profile
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for index, spec in enumerate(specs):
        _paint_frame(grid, spec, _rng(seed, split, slot, index))
    parsed = parse_frames(grid)
    if len(parsed) != len(specs):
        raise ValueError("constructed frames merged or disappeared")
    raw = select_frame(parsed, "raw_count")
    density = select_frame(parsed, "occupied_density")
    if raw["bbox"] == density["bbox"]:
        raise ValueError("profile does not distinguish the metric family")
    return grid


def _schedule(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_build_input(seed, "demo", index, profile) for index, profile in enumerate(_DEMO_PROFILES)]
    queries = [_build_input(seed, "query", index, profile) for index, profile in enumerate(_QUERY_PROFILES)]
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(frozen) != len(set(frozen)):
        raise ValueError("parametric schedule produced duplicate inputs")
    return demos, queries


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    checked_seed = _literal_int("seed", seed, 0, 2**63 - 1)
    checked_demos = _literal_int("demos", demos, 2, 6)
    checked_queries = _literal_int("queries", queries, 1, 4)
    metric = normalize_settings(settings)["selection_metric"]
    demo_inputs, query_inputs = _schedule(checked_seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, metric)}

    train = [pair(grid) for grid in demo_inputs[:checked_demos]]
    test = [pair(grid) for grid in query_inputs[:checked_queries]]
    if setting_survivors(train) != [metric]:
        raise ValueError("demonstrations do not uniquely identify selection_metric")
    return {"train": train, "test": test, "program_solution": program({"selection_metric": metric})}


def setting_survivors(demonstrations: object) -> list[str]:
    if type(demonstrations) is not list or not demonstrations:
        raise ValueError("demonstrations must be a nonempty list")
    return [
        metric
        for metric in METRICS
        if all(transform(pair["input"], metric) == pair["output"] for pair in demonstrations)
    ]


def predict_rival(value: object, name: str) -> list[list[int]]:
    frames = parse_frames(value)
    if name == "first_frame":
        chosen = frames[0]
    elif name == "last_frame":
        chosen = frames[-1]
    elif name == "largest_area":
        chosen = max(frames, key=lambda frame: frame["area"])
    elif name == "smallest_area":
        chosen = min(frames, key=lambda frame: frame["area"])
    elif name == "largest_perimeter":
        chosen = max(frames, key=lambda frame: frame["perimeter"])
    elif name == "smallest_perimeter":
        chosen = min(frames, key=lambda frame: frame["perimeter"])
    elif name == "highest_color":
        chosen = max(frames, key=lambda frame: frame["color"])
    elif name == "lowest_color":
        chosen = min(frames, key=lambda frame: frame["color"])
    elif name == "middle_frame":
        chosen = frames[len(frames) // 2]
    else:
        raise ValueError(f"unknown rival {name!r}")
    return deepcopy(chosen["crop"])


RIVALS = (
    "first_frame",
    "last_frame",
    "largest_area",
    "smallest_area",
    "largest_perimeter",
    "smallest_perimeter",
    "highest_color",
    "lowest_color",
    "middle_frame",
)


def rival_survivors(demonstrations: object, *, selected_metric: str) -> list[str]:
    if selected_metric not in METRICS:
        raise ValueError("unknown selected metric")
    return [
        name
        for name in RIVALS
        if all(predict_rival(pair["input"], name) == pair["output"] for pair in demonstrations)
    ]


def dependency(value: object, metric: object) -> dict[str, object]:
    if type(metric) is not str or metric not in METRICS:
        raise ValueError("unknown metric")
    frames = parse_frames(value)
    chosen = select_frame(frames, metric)
    return {
        "step_a": "parse the hollow frames, compute each input-dependent interior count and area, and choose the first maximum under the requested metric",
        "frame_metrics": [
            {
                "bbox": frame["bbox"],
                "interior_bbox": frame["interior_bbox"],
                "count": frame["count"],
                "area": frame["area"],
                "density_fraction": [frame["count"], frame["area"]],
            }
            for frame in frames
        ],
        "selected_bbox": chosen["bbox"],
        "selected_interior_bbox": chosen["interior_bbox"],
        "selected_count": chosen["count"],
        "selected_area": chosen["area"],
        "step_b": "crop exactly the interior bounding box carried forward by the metric-selection stage",
        "final": deepcopy(chosen["crop"]),
    }
