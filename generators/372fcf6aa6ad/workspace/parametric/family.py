"""Native parametric family for 372fcf6aa6ad.

The exact canonical default sorts isolated monochrome objects by hole count,
size and position, rotates each crop clockwise, and packs the crops.  The
alternate preserves that whole stage, measures the rotated width of the first
ranked crop, and uses that input-derived value to select which packed crop is
recolored to 8.

The authored scenes deliberately include a large hole-free winner and smaller
one-hole frames.  That makes the source task's primary hole-count ordering
observable and repairs the retained size-before-holes teaching shortcut inside
this parametric family without changing the production generator.
"""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "372fcf6aa6ad"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "winner_width_relay")
DEFAULT_MODE = "canonical"
HYPOTHESES = MODES + (
    "winner_height_clamped",
    "size_first_relay",
    "reverse_tiebreak_relay",
    "constant_first",
    "constant_second",
    "constant_third",
)
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

DEMO_PROFILES = (
    (18, 20, 1),
    (18, 22, 2),
    (20, 24, 3),
    (22, 24, 1),
    (24, 26, 2),
    (26, 28, 3),
)
QUERY_PROFILES = (
    (19, 21, 2),
    (21, 25, 3),
    (25, 28, 1),
    (30, 30, 2),
)


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def program_for(mode: str) -> str:
    selected = _mode(mode)
    return _read("canonical.rkt" if selected == "canonical" else "winner_width_relay.rkt")


def counterfactual_program() -> str:
    return _read("wrong_winner_height.rkt")


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _mode(value: Any, *, hypothesis: bool = False) -> str:
    options = HYPOTHESES if hypothesis else MODES
    if type(value) is not str or value not in options:
        raise ValueError(f"mode must be one of {options}")
    return value


def validate_grid(value: Any) -> list[list[int]]:
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
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _normalize(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    points = set(cells)
    if not points:
        raise ValueError("shape must contain cells")
    top = min(r for r, _ in points)
    left = min(c for _, c in points)
    return {(r - top, c - left) for r, c in points}


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def _rect(height: int, width: int) -> set[tuple[int, int]]:
    return {(r, c) for r in range(height) for c in range(width)}


def _frame(height: int, width: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    }


def _two_hole(height: int, width: int) -> set[tuple[int, int]]:
    if height < 5 or width < 4:
        raise ValueError("two-hole frame needs at least 5x4")
    middle = height // 2
    return (
        {(r, c) for r in (0, middle, height - 1) for c in range(width)}
        | {(r, c) for r in range(height) if r not in (0, middle, height - 1) for c in (0, width - 1)}
    )


def _paint(
    grid: list[list[int]],
    shape: Iterable[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> None:
    height, width = len(grid), len(grid[0])
    cells = {(top + r, left + c) for r, c in _normalize(shape)}
    if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
        raise ValueError("shape falls outside scene")
    occupied = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    halo = occupied | {
        (r + dr, c + dc)
        for r, c in occupied
        for dr, dc in DIR8
        if 0 <= r + dr < height and 0 <= c + dc < width
    }
    if cells & halo:
        raise ValueError("objects must remain separated even diagonally")
    for r, c in cells:
        grid[r][c] = color


def _components(value: Any) -> list[dict[str, Any]]:
    grid = validate_grid(value)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            cells: set[tuple[int, int]] = set()
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for dr, dc in DIR4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": cells, "bbox": _bbox(cells)})
    return result


def _crop(grid: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    r1, c1, r2, c2 = obj["bbox"]
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _hole_count(cells: Iterable[tuple[int, int]]) -> int:
    shape = _normalize(cells)
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    unseen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in shape
    }
    holes = 0
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        touches = False
        while queue:
            r, c = queue.popleft()
            if r in (0, height - 1) or c in (0, width - 1):
                touches = True
            for dr, dc in DIR4:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    queue.append(nxt)
        if not touches:
            holes += 1
    return holes


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _items(value: Any, *, ordering: str = "canonical") -> list[dict[str, Any]]:
    grid = validate_grid(value)
    items = []
    for obj in _components(grid):
        r1, c1, _, _ = obj["bbox"]
        crop = _crop(grid, obj)
        items.append(
            {
                "holes": _hole_count(obj["cells"]),
                "size": len(obj["cells"]),
                "top": r1,
                "left": c1,
                "color": obj["color"],
                "piece": _rotate_cw(crop),
            }
        )
    if ordering == "canonical":
        key = lambda item: (item["holes"], item["size"], item["top"], item["left"])
    elif ordering == "size_first":
        key = lambda item: (item["size"], item["holes"], item["top"], item["left"])
    elif ordering == "reverse_tiebreak":
        key = lambda item: (item["holes"], item["size"], -item["top"], -item["left"])
    else:
        raise ValueError(f"unknown ordering {ordering!r}")
    return sorted(items, key=key)


def _recolor(piece: list[list[int]], color: int = 8) -> list[list[int]]:
    return [[0 if value == 0 else color for value in row] for row in piece]


def _pack(pieces: list[list[list[int]]]) -> list[list[int]]:
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = _blank(height, width)
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def _selector(items: list[dict[str, Any]], hypothesis: str) -> int:
    first = items[0]["piece"]
    if hypothesis in ("winner_width_relay", "size_first_relay", "reverse_tiebreak_relay"):
        return len(first[0])
    if hypothesis == "winner_height_clamped":
        return min(3, len(first))
    if hypothesis == "constant_first":
        return 1
    if hypothesis == "constant_second":
        return 2
    if hypothesis == "constant_third":
        return 3
    raise ValueError(f"hypothesis has no selector: {hypothesis}")


def transform(value: Any, mode: str) -> list[list[int]]:
    selected = _mode(mode, hypothesis=True)
    if selected == "canonical":
        items = _items(value)
        return _pack([item["piece"] for item in items])
    ordering = (
        "size_first"
        if selected == "size_first_relay"
        else "reverse_tiebreak"
        if selected == "reverse_tiebreak_relay"
        else "canonical"
    )
    items = _items(value, ordering=ordering)
    selector = _selector(items, selected)
    if not 1 <= selector <= len(items):
        raise ValueError("selector is outside packed piece range")
    pieces = [item["piece"] for item in items]
    pieces[selector - 1] = _recolor(pieces[selector - 1])
    return _pack(pieces)


def explain_dependency(value: Any) -> dict[str, Any]:
    canonical_items = _items(value)
    first = canonical_items[0]["piece"]
    selector = len(first[0])
    counterfactual = min(3, len(first))
    return {
        "step_a": "sort the objects by holes, size and position, then rotate every crop clockwise",
        "intermediate": "rotated width of the first ranked crop",
        "step_b": "use that width as a 1-based index and recolor the selected packed crop to color 8",
        "why_b_depends_on_a": "the selected crop index is unavailable until canonical ranking identifies the winner and rotation exposes its width",
        "winner_color": canonical_items[0]["color"],
        "selector": selector,
        "counterfactual_selector": counterfactual,
        "output": transform(value, "winner_width_relay"),
        "counterfactual_output": transform(value, "winner_height_clamped"),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"372fcf6aa6ad-parametric-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _profile(seed: int, split: str, index: int) -> tuple[int, int, int]:
    base = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    height, width, canonical_k = base[index]
    if split == "train" and seed % 2 == 1 and index < 2:
        canonical_k = 3 - canonical_k
    return height, width, canonical_k


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, selector = _profile(seed, split, index)
    rng = _rng(seed, split, index)
    colors = list(range(1, 8))
    rng.shuffle(colors)
    colors = colors[:5]
    grid = _blank(height, width)

    if (height, width) == (30, 30):
        shapes = [
            (_rect(2, 14), 0, 0),
            (_rect(4, 8), 0, 22),
            (_frame(5, 5), 10, 0),
            (_frame(5, 5), 10, 25),
            (_two_hole(7, 6), 23, 10),
        ]
    else:
        controller = _rect(selector, {1: 10, 2: 5, 3: 4}[selector])
        companion = _rect(3, 5) if rng.randrange(2) == 0 else _rect(5, 3)
        if index % 2 == 0:
            frame_positions = ((7, 1), (7, 8))
        else:
            frame_positions = ((7, 1), (12, 1))
        shapes = [
            (controller, 1, 1),
            (companion, 1, width - (5 if max(c for _, c in companion) == 4 else 3) - 1),
            (_frame(3, 3), *frame_positions[0]),
            (_frame(3, 3), *frame_positions[1]),
            (_two_hole(5, 5), height - 6, width - 6),
        ]

    for color, (shape, top, left) in zip(colors, shapes):
        _paint(grid, shape, top, left, color)
    _validate_scene(grid, expected_selector=selector)
    return grid


def _validate_scene(value: Any, *, expected_selector: int | None = None) -> None:
    grid = validate_grid(value)
    components = _components(grid)
    if len(components) != 5:
        raise ValueError(f"scene must contain five objects, found {len(components)}")
    colors = [obj["color"] for obj in components]
    if len(colors) != len(set(colors)) or 8 in colors:
        raise ValueError("objects need five distinct non-8 colors")
    holes = sorted(_hole_count(obj["cells"]) for obj in components)
    if holes != [0, 0, 1, 1, 2]:
        raise ValueError(f"expected hole profile [0,0,1,1,2], got {holes}")
    items = _items(grid)
    selector = len(items[0]["piece"][0])
    if selector not in (1, 2, 3):
        raise ValueError(f"winner-width selector must be 1..3, got {selector}")
    if expected_selector is not None and selector != expected_selector:
        raise ValueError(f"scene selector {selector} differs from requested {expected_selector}")
    size_first = _items(grid, ordering="size_first")
    if [item["color"] for item in size_first] == [item["color"] for item in items]:
        raise ValueError("scene failed to expose holes-before-size ordering")


def certificate(train: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(transform(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    declared = [mode for mode in MODES if mode in survivors]
    selected = declared[0] if len(declared) == 1 else None
    query_changing = []
    if selected is not None:
        for hypothesis in survivors:
            if any(transform(grid, hypothesis) != transform(grid, selected) for grid in query_inputs):
                query_changing.append(hypothesis)
    return {
        "survivors": survivors,
        "selected_declared_mode": selected,
        "query_changing_survivors": query_changing,
        "hypotheses": list(HYPOTHESES),
    }


def build_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    selected = _mode(mode)
    seen: set[tuple[tuple[int, ...], ...]] = set()

    def collect(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        pairs = []
        for index in range(count):
            grid = _scene(seed, split, index)
            key = tuple(tuple(row) for row in grid)
            if key in seen:
                raise RuntimeError("scene schedule produced a duplicate input")
            seen.add(key)
            pairs.append({"input": grid, "output": transform(grid, selected)})
        return pairs

    return {
        "train": collect("train", demos),
        "test": collect("test", queries),
        "program_solution": program_for(selected),
    }
