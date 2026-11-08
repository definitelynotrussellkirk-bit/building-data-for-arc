"""Native composed family for 2e0d26e28a50.

A connected color-3 key object has one through four cells.  Step A counts
those cells and maps 1, 2, 3, 4 to the reference motif's top-left, top-right,
bottom-left, and bottom-right corners.  Step B translates the motif so the
selected corner lands on the unique color-1 marker and paints it color 8 on a
fresh grid.  The canonical setting always selects bottom-right.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "2e0d26e28a50"
HERE = Path(__file__).resolve().parent
POLICIES = ("bottom_right", "key_count_corner")
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DISTRACTOR_COLORS = (4, 5, 6, 7, 9)

# height, width, motif cells, key cells, distractor cells
_DEMO_PROFILES = (
    (11, 13, 5, 1, 3),
    (13, 15, 6, 2, 5),
    (15, 17, 7, 3, 8),
    (17, 19, 8, 4, 10),
    (20, 22, 10, 1, 14),
    (23, 25, 11, 2, 18),
)
_QUERY_PROFILES = (
    (16, 18, 9, 4, 10),
    (21, 23, 10, 1, 15),
    (26, 28, 11, 2, 20),
    (30, 30, 12, 3, 24),
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"anchor_policy"}:
        raise ValueError("settings must contain exactly anchor_policy")
    policy = value["anchor_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"anchor_policy must be one of {POLICIES!r}")
    return {"anchor_policy": policy}


def _grid(value: Any) -> list[list[int]]:
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
        raise ValueError("grid must be rectangular 1..30 with exact colors 0..9")
    return [row[:] for row in value]


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot take a bounding box of no cells")
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows), max(cols)


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        r, c = todo.pop()
        for dr, dc in _CARDINAL:
            p = (r + dr, c + dc)
            if p in cells and p not in seen:
                seen.add(p)
                todo.append(p)
    return len(seen) == len(cells)


def _translated(
    motif: list[tuple[int, int]],
    anchor: tuple[int, int],
    marker: tuple[int, int],
) -> list[tuple[int, int]]:
    return [(marker[0] + r - anchor[0], marker[1] + c - anchor[1]) for r, c in motif]


def analyze(value: Any) -> dict[str, Any]:
    source = _grid(value)
    height, width = len(source), len(source[0])
    motif = sorted((r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 2)
    if not 3 <= len(motif) <= 20:
        raise ValueError(f"expected 3..20 color-2 motif cells, got {len(motif)}")
    if not _connected(motif):
        raise ValueError("color-2 motif must be connected")
    top, left, bottom, right = _bbox(motif)
    if top == bottom or left == right:
        raise ValueError("color-2 motif must span at least two rows and columns")

    markers = [(r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 1]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one color-1 marker, got {len(markers)}")
    marker = markers[0]

    key = sorted((r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 3)
    if not 1 <= len(key) <= 4:
        raise ValueError(f"expected a 1..4-cell color-3 key object, got {len(key)} cells")
    if not _connected(key):
        raise ValueError("color-3 key object must be connected")

    anchors = {
        "top_left": (top, left),
        "top_right": (top, right),
        "bottom_left": (bottom, left),
        "bottom_right": (bottom, right),
    }
    translated_by_corner = {
        name: _translated(motif, anchor, marker) for name, anchor in anchors.items()
    }
    for name, cells in translated_by_corner.items():
        if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
            raise ValueError(f"{name} anchored stamp falls outside grid bounds")

    selected = CORNERS[len(key) - 1]
    distractor_cells = sum(
        value not in (0, 1, 2, 3) for row in source for value in row
    )
    return {
        "height": height,
        "width": width,
        "motif_cells": motif,
        "motif_size": len(motif),
        "motif_bbox": (top, left, bottom, right),
        "motif_shape": (bottom - top + 1, right - left + 1),
        "marker": marker,
        "key_cells": key,
        "key_count": len(key),
        "selected_corner": selected,
        "anchors": anchors,
        "translated_by_corner": translated_by_corner,
        "distractor_cells": distractor_cells,
    }


def _paint(cells: list[tuple[int, int]], height: int, width: int, color: int = 8) -> list[list[int]]:
    output = [[0] * width for _ in range(height)]
    for r, c in cells:
        output[r][c] = color
    return output


def output_for_corner(value: Any, corner: str, color: int = 8) -> list[list[int]]:
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    info = analyze(value)
    return _paint(info["translated_by_corner"][corner], info["height"], info["width"], color)


def apply_policy(value: Any, policy: str) -> list[list[int]]:
    info = analyze(value)
    if policy == "bottom_right":
        corner = "bottom_right"
    elif policy == "key_count_corner":
        corner = info["selected_corner"]
    else:
        raise ValueError(f"unknown anchor_policy: {policy!r}")
    return _paint(info["translated_by_corner"][corner], info["height"], info["width"])


def program(settings: Any) -> str:
    policy = normalize_settings(settings)["anchor_policy"]
    name = "canonical.rkt" if policy == "bottom_right" else "key_count_corner.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "always_bottom_right.rkt").read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:key-corner-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _motif(rng: random.Random, size: int) -> list[tuple[int, int]]:
    side = max(2, min(5, int((size - 1) ** 0.5) + 2))
    cells = {(0, 0), (1, 0), (1, 1)}
    while len(cells) < size:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _CARDINAL
            if 0 <= r + dr < side and 0 <= c + dc < side
            and (r + dr, c + dc) not in cells
        })
        if not frontier:
            side += 1
            continue
        cells.add(rng.choice(frontier))
    top, left, _, _ = _bbox(cells)
    return sorted((r - top, c - left) for r, c in cells)


def _key_shape(count: int) -> list[tuple[int, int]]:
    shapes = {
        1: [(0, 0)],
        2: [(0, 0), (0, 1)],
        3: [(0, 0), (1, 0), (1, 1)],
        4: [(0, 0), (0, 1), (1, 0), (1, 1)],
    }
    return shapes[count]


def _placements(height: int, width: int, shape: list[tuple[int, int]]) -> list[tuple[int, int]]:
    bottom = max(r for r, _ in shape)
    right = max(c for _, c in shape)
    return [
        (top, left)
        for top in range(height - bottom)
        for left in range(width - right)
    ]


def _near(cells: set[tuple[int, int]], occupied: set[tuple[int, int]], distance: int = 1) -> bool:
    return any(
        max(abs(r - rr), abs(c - cc)) <= distance
        for r, c in cells
        for rr, cc in occupied
    )


def make_scene(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    if split == "train":
        if not 0 <= index < len(_DEMO_PROFILES):
            raise ValueError("train profile index out of range")
        height, width, motif_size, key_count, distractor_count = _DEMO_PROFILES[index]
    elif split == "test":
        if not 0 <= index < len(_QUERY_PROFILES):
            raise ValueError("test profile index out of range")
        height, width, motif_size, key_count, distractor_count = _QUERY_PROFILES[index]
    else:
        raise ValueError("split must be train or test")

    rng = _rng(seed, split, index)
    motif_local = _motif(rng, motif_size)
    _, _, local_bottom, local_right = _bbox(motif_local)
    motif_height, motif_width = local_bottom + 1, local_right + 1
    marker_rows = list(range(motif_height - 1, height - motif_height + 1))
    marker_cols = list(range(motif_width - 1, width - motif_width + 1))
    if not marker_rows or not marker_cols:
        raise AssertionError("profile cannot support all four corner placements")
    marker = (rng.choice(marker_rows), rng.choice(marker_cols))

    motif_slots = _placements(height, width, motif_local)
    rng.shuffle(motif_slots)
    motif: set[tuple[int, int]] | None = None
    for top, left in motif_slots:
        candidate = {(top + r, left + c) for r, c in motif_local}
        if marker not in candidate and not _near(candidate, {marker}):
            motif = candidate
            break
    if motif is None:
        raise AssertionError("could not place source motif")

    occupied = set(motif) | {marker}
    key_local = _key_shape(key_count)
    key_slots = _placements(height, width, key_local)
    rng.shuffle(key_slots)
    key: set[tuple[int, int]] | None = None
    for top, left in key_slots:
        candidate = {(top + r, left + c) for r, c in key_local}
        if not _near(candidate, occupied):
            key = candidate
            break
    if key is None:
        raise AssertionError("could not place key object")
    occupied |= key

    available = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in occupied and not _near({(r, c)}, occupied)
    ]
    rng.shuffle(available)
    if len(available) < distractor_count:
        raise AssertionError("profile lacks distractor capacity")
    distractors = available[:distractor_count]

    grid = [[0] * width for _ in range(height)]
    for r, c in motif:
        grid[r][c] = 2
    grid[marker[0]][marker[1]] = 1
    for r, c in key:
        grid[r][c] = 3
    for pos, (r, c) in enumerate(distractors):
        grid[r][c] = _DISTRACTOR_COLORS[(pos * 3 + index) % len(_DISTRACTOR_COLORS)]

    info = analyze(grid)
    if info["motif_size"] != motif_size or info["key_count"] != key_count:
        raise AssertionError("internal composed-scene mismatch")
    if info["distractor_cells"] != distractor_count:
        raise AssertionError("internal distractor count mismatch")
    return grid


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    policy = normalize_settings(settings)["anchor_policy"]
    _integer(demos, "demos", 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    train_inputs = [make_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [make_scene(seed, "test", index) for index in range(queries)]
    return {
        "train": [
            {"input": grid, "output": apply_policy(grid, policy)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": apply_policy(grid, policy)} for grid in test_inputs
        ],
        "program_solution": program({"anchor_policy": policy}),
    }
