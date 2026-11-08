"""Matched-input parametric family for ARC task ``61090a45e458``.

``local_seed`` is the byte-exact canonical rule: each frame's larger enclosed
object is recolored to that frame's singleton seed color.

``largest_target_seed`` adds a non-collapsing global relay. Stage A parses all
frames and selects the frame with the uniquely largest target. Its seed color is
an input-dependent intermediate. Stage B consumes that selected color to
recolor every frame's target while preserving all singleton seeds and borders.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "61090a45e458"
HERE = Path(__file__).resolve().parent
RECOLOR_POLICIES = ("local_seed", "largest_target_seed")
POSITION_RIVALS = (
    "smallest_target_seed",
    "first_frame_seed",
    "second_frame_seed",
    "third_frame_seed",
    "leftmost_seed",
    "rightmost_seed",
    "topmost_seed",
    "bottommost_seed",
    "largest_frame_seed",
    "smallest_frame_seed",
    "min_seed_color",
    "max_seed_color",
    "largest_target_color",
    "largest_target_frame_color",
    "identity",
)
CONSTANT_RIVALS = tuple(f"constant_{color}" for color in range(1, 10))
HYPOTHESES = RECOLOR_POLICIES + POSITION_RIVALS + CONSTANT_RIVALS


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"recolor_policy"}:
        raise ValueError("settings must contain only recolor_policy")
    policy = value["recolor_policy"]
    if type(policy) is not str or policy not in RECOLOR_POLICIES:
        raise ValueError(
            "recolor_policy must be local_seed or largest_target_seed"
        )
    return policy


def program(settings: Any) -> str:
    policy = _settings(settings)
    filename = "canonical.rkt" if policy == "local_seed" else "largest_target_seed.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


def _neighbors(point: tuple[int, int], height: int, width: int):
    row, col = point
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _color_components(grid: list[list[int]]) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, frozenset[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            pending = [(row, col)]
            cells = {(row, col)}
            while pending:
                point = pending.pop()
                for rr, cc in _neighbors(point, height, width):
                    if (rr, cc) not in seen and grid[rr][cc] == color:
                        seen.add((rr, cc))
                        cells.add((rr, cc))
                        pending.append((rr, cc))
            result.append((color, frozenset(cells)))
    return result


def _frame_bbox(cells: frozenset[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if height < 3 or width < 3:
        return None
    expected = 2 * height + 2 * width - 4
    if len(cells) != expected:
        return None
    perimeter = {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if row in {r1, r2} or col in {c1, c2}
    }
    return (r1, c1, r2, c2) if cells == perimeter else None


def analyze(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    components = _color_components(grid)
    frame_rows: list[dict[str, Any]] = []
    for frame_color, cells in components:
        bbox = _frame_bbox(cells)
        if bbox is None:
            continue
        r1, c1, r2, c2 = bbox
        by_color: dict[int, list[tuple[int, int]]] = {}
        for row in range(r1 + 1, r2):
            for col in range(c1 + 1, c2):
                color = grid[row][col]
                if color:
                    by_color.setdefault(color, []).append((row, col))
        if len(by_color) != 2:
            raise ValueError("each frame must contain exactly two nonzero interior colors")
        singleton = [(color, points) for color, points in by_color.items() if len(points) == 1]
        target = [(color, points) for color, points in by_color.items() if len(points) > 1]
        if len(singleton) != 1 or len(target) != 1:
            raise ValueError("each frame must contain one singleton seed and one larger target")
        seed_color, seed_cells = singleton[0]
        target_color, target_cells = target[0]
        target_set = frozenset(target_cells)
        pending = [next(iter(target_set))]
        reached = {pending[0]}
        while pending:
            point = pending.pop()
            for neighbor in _neighbors(point, len(grid), len(grid[0])):
                if neighbor in target_set and neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
        if reached != target_set:
            raise ValueError("target must be four-connected")
        frame_rows.append(
            {
                "bbox": [r1, c1, r2, c2],
                "frame_color": frame_color,
                "seed_color": seed_color,
                "seed_cell": list(seed_cells[0]),
                "target_color": target_color,
                "target_cells": [list(point) for point in sorted(target_set)],
                "target_size": len(target_set),
                "frame_area": (r2 - r1 + 1) * (c2 - c1 + 1),
            }
        )
    frame_rows.sort(key=lambda row: (row["bbox"][0], row["bbox"][1]))
    if len(frame_rows) != 3:
        raise ValueError("parametric grammar requires exactly three frames")
    nonzero = {
        (row, col)
        for row, values in enumerate(grid)
        for col, color in enumerate(values)
        if color
    }
    claimed: set[tuple[int, int]] = set()
    for frame in frame_rows:
        r1, c1, r2, c2 = frame["bbox"]
        claimed.update(
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
            if row in {r1, r2} or col in {c1, c2}
        )
        claimed.add(tuple(frame["seed_cell"]))
        claimed.update(map(tuple, frame["target_cells"]))
    if claimed != nonzero:
        raise ValueError("grid contains stray or overlapping nonzero cells")
    sizes = [frame["target_size"] for frame in frame_rows]
    if sizes.count(max(sizes)) != 1 or sizes.count(min(sizes)) != 1:
        raise ValueError("target sizes must have unique largest and smallest values")
    return {"height": len(grid), "width": len(grid[0]), "frames": frame_rows}


def _select_index(frames: list[dict[str, Any]], hypothesis: str) -> int:
    if hypothesis in {"largest_target_seed", "largest_target_color", "largest_target_frame_color"}:
        return max(range(3), key=lambda i: (frames[i]["target_size"], -i))
    if hypothesis == "smallest_target_seed":
        return min(range(3), key=lambda i: (frames[i]["target_size"], i))
    if hypothesis == "first_frame_seed":
        return 0
    if hypothesis == "second_frame_seed":
        return 1
    if hypothesis == "third_frame_seed":
        return 2
    if hypothesis == "leftmost_seed":
        return min(range(3), key=lambda i: (frames[i]["bbox"][1], frames[i]["bbox"][0], i))
    if hypothesis == "rightmost_seed":
        return max(range(3), key=lambda i: (frames[i]["bbox"][3], -frames[i]["bbox"][0], -i))
    if hypothesis == "topmost_seed":
        return min(range(3), key=lambda i: (frames[i]["bbox"][0], frames[i]["bbox"][1], i))
    if hypothesis == "bottommost_seed":
        return max(range(3), key=lambda i: (frames[i]["bbox"][2], -frames[i]["bbox"][1], -i))
    if hypothesis == "largest_frame_seed":
        return max(range(3), key=lambda i: (frames[i]["frame_area"], -i))
    if hypothesis == "smallest_frame_seed":
        return min(range(3), key=lambda i: (frames[i]["frame_area"], i))
    raise ValueError(f"hypothesis has no frame selector: {hypothesis}")


def largest_target_intermediate(value: Any) -> dict[str, Any]:
    frames = analyze(value)["frames"]
    index = _select_index(frames, "largest_target_seed")
    frame = frames[index]
    return {
        "selected_frame_index": index,
        "selected_frame_bbox": frame["bbox"],
        "target_size": frame["target_size"],
        "seed_color": frame["seed_color"],
    }


def predict(value: Any, hypothesis: Any) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError("unknown declared hypothesis")
    grid = _grid(value)
    frames = analyze(grid)["frames"]
    out = deepcopy(grid)
    if hypothesis == "identity":
        return out
    if hypothesis == "local_seed":
        colors = [frame["seed_color"] for frame in frames]
    elif hypothesis == "min_seed_color":
        colors = [min(frame["seed_color"] for frame in frames)] * 3
    elif hypothesis == "max_seed_color":
        colors = [max(frame["seed_color"] for frame in frames)] * 3
    elif hypothesis.startswith("constant_"):
        colors = [int(hypothesis.split("_", 1)[1])] * 3
    else:
        selected = _select_index(frames, hypothesis)
        if hypothesis == "largest_target_color":
            color = frames[selected]["target_color"]
        elif hypothesis == "largest_target_frame_color":
            color = frames[selected]["frame_color"]
        else:
            color = frames[selected]["seed_color"]
        colors = [color] * 3
    for frame, color in zip(frames, colors):
        for row, col in map(tuple, frame["target_cells"]):
            out[row][col] = color
    return out


def _grid_hash(value: list[list[int]]) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def teaching_certificate(train: Any, query_inputs: Any) -> dict[str, Any]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("two through six demonstrations are required")
    if type(query_inputs) is not list or not 1 <= len(query_inputs) <= 4:
        raise ValueError("one through four query inputs are required")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each demonstration must contain input and output")
        analyze(pair["input"])
        _grid(pair["output"])
    for value in query_inputs:
        analyze(value)
    survivors = [
        name
        for name in HYPOTHESES
        if all(predict(pair["input"], name) == pair["output"] for pair in train)
    ]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "predicted_query_sha256": {
            name: [_grid_hash(predict(value, name)) for value in query_inputs]
            for name in survivors
        },
        "scope": "Finite declared rivals only; no universal uniqueness claim.",
    }


def _profile(height, width, boxes, target_sizes, colors):
    return {
        "height": height,
        "width": width,
        "boxes": tuple(tuple(box) for box in boxes),
        "target_sizes": tuple(target_sizes),
        "colors": tuple(tuple(row) for row in colors),
    }


_DEMO_PROFILES = (
    _profile(
        16, 20,
        ((1, 1, 7, 7), (1, 11, 6, 18), (9, 2, 14, 9)),
        (4, 8, 2),
        ((1, 2, 3), (4, 5, 6), (7, 8, 9)),
    ),
    _profile(
        18, 19,
        ((1, 1, 6, 7), (1, 11, 8, 17), (10, 1, 17, 9)),
        (3, 5, 9),
        ((2, 1, 3), (5, 8, 6), (9, 4, 7)),
    ),
    _profile(
        18, 22,
        ((1, 1, 9, 8), (1, 13, 7, 20), (11, 5, 17, 15)),
        (10, 4, 6),
        ((6, 7, 8), (1, 4, 2), (9, 5, 3)),
    ),
    _profile(
        20, 20,
        ((0, 2, 7, 9), (2, 12, 10, 19), (12, 1, 19, 10)),
        (5, 11, 7),
        ((4, 6, 5), (1, 3, 2), (8, 7, 9)),
    ),
    _profile(
        21, 23,
        ((1, 1, 8, 8), (1, 14, 9, 22), (12, 5, 20, 15)),
        (6, 8, 13),
        ((3, 5, 4), (7, 2, 8), (1, 6, 9)),
    ),
    _profile(
        19, 24,
        ((1, 1, 10, 9), (1, 15, 7, 23), (12, 6, 18, 16)),
        (12, 4, 7),
        ((8, 2, 9), (4, 6, 5), (1, 7, 3)),
    ),
)
_QUERY_PROFILES = (
    _profile(
        17, 21,
        ((1, 1, 9, 9), (1, 13, 7, 20), (11, 4, 16, 13)),
        (11, 4, 7),
        ((7, 4, 8), (1, 6, 2), (9, 5, 3)),
    ),
    _profile(
        20, 22,
        ((1, 1, 8, 8), (1, 14, 11, 21), (13, 3, 19, 13)),
        (6, 14, 9),
        ((2, 5, 1), (8, 3, 9), (4, 7, 6)),
    ),
    _profile(
        22, 24,
        ((1, 1, 10, 9), (1, 15, 9, 23), (13, 5, 21, 16)),
        (8, 5, 16),
        ((5, 7, 6), (1, 4, 2), (9, 3, 8)),
    ),
    _profile(
        30, 30,
        ((0, 0, 12, 10), (0, 18, 10, 29), (17, 4, 29, 25)),
        (22, 35, 60),
        ((1, 5, 2), (7, 3, 8), (4, 6, 9)),
    ),
)


def _scene_rng(seed: int, kind: str, index: int, frame_index: int) -> random.Random:
    digest = hashlib.sha256(
        f"61090a45e458-largest-target-seed-v1:{seed}:{kind}:{index}:{frame_index}".encode(
            "ascii"
        )
    ).digest()
    return random.Random(digest)


def _target_and_seed(
    r1: int,
    c1: int,
    r2: int,
    c2: int,
    size: int,
    rng: random.Random,
) -> tuple[frozenset[tuple[int, int]], tuple[int, int]]:
    interior = {
        (row, col)
        for row in range(r1 + 1, r2)
        for col in range(c1 + 1, c2)
    }
    if len(interior) < size + 1:
        raise ValueError("frame interior cannot fit target plus seed")
    corners = (
        (r1 + 1, c1 + 1),
        (r1 + 1, c2 - 1),
        (r2 - 1, c1 + 1),
        (r2 - 1, c2 - 1),
    )
    seed_index = rng.randrange(4)
    seed = corners[seed_index]
    anchor = corners[3 - seed_index]
    allowed = interior - {seed}
    target = {anchor}
    while len(target) < size:
        frontier = {
            point
            for cell in target
            for point in _neighbors(cell, r2 + 1, c2 + 1)
            if point in allowed and point not in target
        }
        if not frontier:
            raise RuntimeError("connected target growth exhausted")
        ordered = sorted(frontier, key=lambda p: (
            min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in target),
            p[0], p[1],
        ))
        cutoff = min(len(ordered), max(2, len(ordered) // 2))
        target.add(rng.choice(ordered[:cutoff]))
    return frozenset(target), seed


def _scene(seed: int, kind: str, index: int, profile: dict[str, Any]) -> list[list[int]]:
    height, width = profile["height"], profile["width"]
    grid = [[0] * width for _ in range(height)]
    for frame_index, (bbox, target_size, colors) in enumerate(
        zip(profile["boxes"], profile["target_sizes"], profile["colors"])
    ):
        r1, c1, r2, c2 = bbox
        frame_color, seed_color, target_color = colors
        if not (0 <= r1 < r2 < height and 0 <= c1 < c2 < width):
            raise AssertionError("profile frame escapes canvas")
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if row in {r1, r2} or col in {c1, c2}:
                    if grid[row][col] != 0:
                        raise AssertionError("profile frames overlap")
                    grid[row][col] = frame_color
        target, seed_cell = _target_and_seed(
            r1, c1, r2, c2, target_size, _scene_rng(seed, kind, index, frame_index)
        )
        grid[seed_cell[0]][seed_cell[1]] = seed_color
        for row, col in target:
            grid[row][col] = target_color
    analysis = analyze(grid)
    if [frame["target_size"] for frame in analysis["frames"]] != list(profile["target_sizes"]):
        raise AssertionError("profile order or target sizes changed")
    return grid


@lru_cache(maxsize=128)
def _all_inputs(seed: int) -> tuple[tuple[list[list[int]], ...], tuple[list[list[int]], ...]]:
    demos = tuple(
        _scene(seed, "demo", index, profile)
        for index, profile in enumerate(_DEMO_PROFILES)
    )
    queries = tuple(
        _scene(seed, "query", index, profile)
        for index, profile in enumerate(_QUERY_PROFILES)
    )
    visible = [json.dumps(value, separators=(",", ":")) for value in demos + queries]
    if len(visible) != len(set(visible)):
        raise AssertionError("profile bank produced duplicate visible inputs")
    return demos, queries


def _pair(value: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(value), "output": predict(value, policy)}


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(episode) is not dict or not {"train", "test"} <= set(episode):
        raise ValueError("episode must contain train and test")
    query_index = _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    selected = _settings(settings)
    demo_bank, query_bank = _all_inputs(seed)
    train_inputs = list(demo_bank[:demos])
    all_query_inputs = list(query_bank)

    # The visible curriculum is setting-neutral. Its minimum two-demo prefix
    # must uniquely identify either selected rule against all declared rivals.
    for policy in RECOLOR_POLICIES:
        train = [_pair(value, policy) for value in train_inputs]
        certificate = teaching_certificate(train, all_query_inputs)
        if certificate["survivors"] != [policy]:
            raise AssertionError(
                f"teaching prefix does not uniquely identify {policy}: "
                f"{certificate['survivors']}"
            )

    return {
        "train": [_pair(value, selected) for value in train_inputs],
        "test": [_pair(value, selected) for value in all_query_inputs[:queries]],
        "program_solution": program(settings),
    }
