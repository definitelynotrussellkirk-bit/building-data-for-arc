"""Complete either axis of an input-defined local marker frame.

The default ``axis=x`` setting is the exact canonical rule.  The nearby
``axis=y`` setting uses the same marker frame and matched inputs but completes
the perpendicular local axis.  Distractor objects vary independently of the
frame, so the lesson must recover the selected marker vector before painting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "f99a33b5211f"
VERSION = "local-axis-v1"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"axis": "x"},
    {"axis": "y"},
)
AXES = tuple(setting["axis"] for setting in SETTINGS)
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
DISTRACTOR_COLORS = (1, 2, 3, 4, 9)

# Each adjacent pair changes both the x and y vector.  Therefore the minimum
# two-example lesson rejects every fixed global direction for either setting.
ORIENTATIONS = (
    ((1, 0), (0, 1)),
    ((-1, 0), (0, -1)),
    ((0, 1), (1, 0)),
    ((0, -1), (-1, 0)),
    ((1, 0), (0, -1)),
    ((-1, 0), (0, 1)),
    ((0, 1), (-1, 0)),
    ((0, -1), (1, 0)),
)

# (height, width, distractor component count, minimum component size)
DEMO_PROFILES = (
    (10, 11, 3, 3),
    (12, 13, 5, 3),
    (14, 14, 7, 3),
    (16, 17, 9, 3),
    (18, 19, 11, 4),
    (20, 20, 13, 4),
)
QUERY_PROFILES = (
    (14, 15, 7, 3),
    (18, 20, 11, 4),
    (24, 24, 16, 4),
    (30, 30, 22, 5),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"axis"}:
        raise ValueError("settings must name exactly axis")
    axis = value["axis"]
    if type(axis) is not str or axis not in AXES:
        raise ValueError(f"axis must be one of {AXES}")
    return {"axis": axis}


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not value
        or len(value) > 30
        or type(value[0]) is not list
        or not value[0]
        or len(value[0]) > 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(value)


def program(settings: Any) -> str:
    axis = _settings(settings)["axis"]
    filename = "canonical.rkt" if axis == "x" else "y_axis.rkt"
    return (HERE / filename).read_bytes().decode("utf-8")


def _single(grid: list[list[int]], color: int) -> tuple[int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if len(cells) != 1:
        raise ValueError(f"expected exactly one color-{color} marker, found {len(cells)}")
    return cells[0]


def _add(point: tuple[int, int], vector: tuple[int, int], scale: int = 1) -> tuple[int, int]:
    return point[0] + scale * vector[0], point[1] + scale * vector[1]


def _frame(grid: list[list[int]]) -> dict[str, Any]:
    h, w = len(grid), len(grid[0])
    origin = _single(grid, 5)
    x_marker = _single(grid, 6)
    y_marker = _single(grid, 7)
    x_vector = (x_marker[0] - origin[0], x_marker[1] - origin[1])
    y_vector = (y_marker[0] - origin[0], y_marker[1] - origin[1])
    if x_vector not in CARDINAL or y_vector not in CARDINAL:
        raise ValueError("marker vectors must be cardinal unit vectors")
    if x_vector[0] * y_vector[0] + x_vector[1] * y_vector[1] != 0:
        raise ValueError("x and y marker vectors must be perpendicular")
    x_tip, y_tip = _add(origin, x_vector, 2), _add(origin, y_vector, 2)
    for name, point in (("x_tip", x_tip), ("y_tip", y_tip)):
        if not (0 <= point[0] < h and 0 <= point[1] < w):
            raise ValueError(f"{name} is out of bounds")
        if grid[point[0]][point[1]] != 0:
            raise ValueError(f"{name} must be blank")
    return {
        "origin": origin,
        "x_marker": x_marker,
        "y_marker": y_marker,
        "x_vector": x_vector,
        "y_vector": y_vector,
        "x_tip": x_tip,
        "y_tip": y_tip,
    }


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in DISTRACTOR_COLORS
    }
    found: list[list[tuple[int, int]]] = []
    while cells:
        start = cells.pop()
        component = [start]
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in cells:
                    cells.remove(neighbor)
                    component.append(neighbor)
                    stack.append(neighbor)
        found.append(sorted(component))
    return found


def analyze(grid: Any) -> dict[str, Any]:
    data = _grid(grid)
    frame = _frame(data)
    components = _components(data)
    distractor_colors = sorted({data[r][c] for component in components for r, c in component})
    return {
        **frame,
        "origin_color": data[frame["origin"][0]][frame["origin"][1]],
        "x_marker_color": data[frame["x_marker"][0]][frame["x_marker"][1]],
        "y_marker_color": data[frame["y_marker"][0]][frame["y_marker"][1]],
        "distractor_components": len(components),
        "distractor_cells": sum(len(component) for component in components),
        "distractor_colors": distractor_colors,
        "nonzero_cells": sum(cell != 0 for row in data for cell in row),
    }


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    out = deepcopy(grid)
    h, w = len(out), len(out[0])
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = 8
    return out


def transform(grid: Any, settings: Any) -> list[list[int]]:
    chosen = _settings(settings)
    data = _grid(grid)
    frame = _frame(data)
    axis = chosen["axis"]
    return _paint(data, (frame["origin"], frame[f"{axis}_marker"], frame[f"{axis}_tip"]))


def paint_both_axes(grid: Any) -> list[list[int]]:
    data = _grid(grid)
    frame = _frame(data)
    return _paint(
        data,
        (frame["origin"], frame["x_marker"], frame["x_tip"], frame["y_marker"], frame["y_tip"]),
    )


def paint_origin_only(grid: Any) -> list[list[int]]:
    data = _grid(grid)
    return _paint(data, (_frame(data)["origin"],))


def paint_marker_cells_only(grid: Any) -> list[list[int]]:
    data = _grid(grid)
    frame = _frame(data)
    return _paint(data, (frame["origin"], frame["x_marker"], frame["y_marker"]))


def paint_fixed_global_direction(grid: Any, direction: tuple[int, int]) -> list[list[int]]:
    if direction not in CARDINAL:
        raise ValueError("direction must be cardinal")
    data = _grid(grid)
    origin = _frame(data)["origin"]
    return _paint(data, (origin, _add(origin, direction), _add(origin, direction, 2)))


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}:{purpose}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _profile_order(seed: int, split: str) -> list[tuple[int, int, int, int]]:
    profiles = list(DEMO_PROFILES if split == "train" else QUERY_PROFILES)
    _rng(seed, split, 0, "profile-order").shuffle(profiles)
    return profiles


def _orientation(seed: int, split: str, index: int) -> tuple[tuple[int, int], tuple[int, int]]:
    offset = 0 if split == "train" else len(DEMO_PROFILES)
    return ORIENTATIONS[(seed * 3 + offset + index) % len(ORIENTATIONS)]


def _choose_origin(
    h: int,
    w: int,
    x_vector: tuple[int, int],
    y_vector: tuple[int, int],
    rng: random.Random,
) -> tuple[int, int]:
    candidates = []
    for r in range(h):
        for c in range(w):
            origin = (r, c)
            points = (
                origin,
                _add(origin, x_vector),
                _add(origin, y_vector),
                _add(origin, x_vector, 2),
                _add(origin, y_vector, 2),
            )
            if all(1 <= pr < h - 1 and 1 <= pc < w - 1 for pr, pc in points):
                candidates.append(origin)
    if not candidates:
        raise RuntimeError("no valid frame origin")
    return rng.choice(candidates)


def _rand_blob(rng: random.Random, size: int) -> list[tuple[int, int]]:
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < size:
        candidates = []
        for r, c in frontier:
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point not in cells:
                    candidates.append(point)
        if not candidates:
            raise RuntimeError("blob growth stalled")
        point = rng.choice(candidates)
        cells.add(point)
        frontier.append(point)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _halo(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= r + dr < h and 0 <= c + dc < w
    }


def _place_blob(
    grid: list[list[int]],
    blocked: set[tuple[int, int]],
    shape: list[tuple[int, int]],
    color: int,
    rng: random.Random,
) -> bool:
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(candidates)
    for r0, c0 in candidates:
        cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
        if cells & blocked:
            continue
        for r, c in cells:
            grid[r][c] = color
        blocked.update(_halo(cells, h, w))
        return True
    return False


def _draw_profile(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, object_count, min_size = _profile_order(seed, split)[index]
    x_vector, y_vector = _orientation(seed, split, index)
    for attempt in range(128):
        rng = _rng(seed, split, index, f"scene-{attempt}")
        grid = [[0] * w for _ in range(h)]
        origin = _choose_origin(h, w, x_vector, y_vector, rng)
        x_marker, y_marker = _add(origin, x_vector), _add(origin, y_vector)
        x_tip, y_tip = _add(origin, x_vector, 2), _add(origin, y_vector, 2)
        grid[origin[0]][origin[1]] = 5
        grid[x_marker[0]][x_marker[1]] = 6
        grid[y_marker[0]][y_marker[1]] = 7
        blocked = _halo((origin, x_marker, y_marker, x_tip, y_tip), h, w)
        palette = list(DISTRACTOR_COLORS)
        rng.shuffle(palette)
        ok = True
        for object_index in range(object_count):
            size = min_size + rng.randrange(3)
            shape = _rand_blob(rng, size)
            color = palette[object_index % len(palette)]
            if not _place_blob(grid, blocked, shape, color, rng):
                ok = False
                break
        if not ok:
            continue
        report = analyze(grid)
        if (
            report["distractor_components"] == object_count
            and report["x_vector"] == x_vector
            and report["y_vector"] == y_vector
            and (h < 30 or report["distractor_cells"] >= 100)
            and (h < 30 or set(report["distractor_colors"]) == set(DISTRACTOR_COLORS))
        ):
            return grid
    raise RuntimeError(f"could not construct clean local-axis scene for {split}[{index}]")


def _pair(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    pairs = list(demos)
    survivors = []
    for candidate in SETTINGS:
        try:
            if pairs and all(
                type(pair) is dict and pair.get("output") == transform(pair.get("input"), candidate)
                for pair in pairs
            ):
                survivors.append(dict(candidate))
        except (TypeError, ValueError):
            continue
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    chosen = _settings(settings)
    train = [_pair(_draw_profile(seed, "train", index), chosen) for index in range(demos)]
    test = [_pair(_draw_profile(seed, "test", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify axis")
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serial) != len(set(serial)):
        raise RuntimeError("episode contains duplicate inputs")
    return {
        "train": train,
        "test": test,
        "settings": chosen,
        "seed": seed,
        "program_solution": program(chosen),
        "certificate": {
            "finite_rivals": [dict(setting) for setting in SETTINGS],
            "survivors": fit_settings(train),
            "racket_checked": False,
            "dependency": "recover selected local marker vector, derive its two-step tip, then paint the three-cell axis",
        },
    }
