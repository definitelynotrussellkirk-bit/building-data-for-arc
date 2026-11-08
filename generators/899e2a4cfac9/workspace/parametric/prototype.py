"""Deterministic matched-input lessons for border filtering and signal-ranked retention.

The canonical setting keeps every same-color four-connected object that does not
reach an edge.  The alternate setting first measures the unique blue border
signal, treats its cell count as a one-based rank, then keeps only that interior
object in row-major discovery order.  Native qualification re-executes all claim
labels through protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "899e2a4cfac9"
MODES = ("all_interior", "signal_rank")
PARAMETER = "retention"
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "all_interior": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "signal_rank": (_DIR / "signal_rank.rkt").read_text(encoding="utf-8"),
}

_DEMO_DIMS = ((14, 16), (15, 18), (16, 19), (17, 21), (18, 22), (20, 24))
_QUERY_DIMS = ((15, 17), (19, 21), (24, 27), (30, 30))
_DEMO_COUNTS = (5, 5, 6, 6, 7, 8)
_QUERY_COUNTS = (5, 6, 7, 8)
_DEMO_RANKS = (2, 4, 1, 3, 5, 2)
_QUERY_RANKS = (3, 1, 4, 2)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Every shape fits a 3x3 slot and includes its normalized top-left cell.  The
# sampler varies shape at a fixed size without changing the signal semantics.
_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)), ((0, 0), (1, 0))),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    7: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
}


def _retention(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly retention")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"retention must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for one declared episode setting."""
    return _PROGRAMS[_retention(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or len(grid) > 30 or len(grid[0]) > 30):
        raise ValueError("grid must be a nonempty rectangle no larger than 30x30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return same-color four-components in row-major discovery order."""
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _ORTHOGONAL:
                    nxt = (rr + dr, cc + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        stack.append(nxt)
            cells.sort()
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            result.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return result


def _edges(obj: dict[str, Any], height: int, width: int) -> set[str]:
    edges: set[str] = set()
    for row, col in obj["cells"]:
        if row == 0:
            edges.add("top")
        if row == height - 1:
            edges.add("bottom")
        if col == 0:
            edges.add("left")
        if col == width - 1:
            edges.add("right")
    return edges


def paint_objects(grid: list[list[int]], objects: list[dict[str, Any]]) -> list[list[int]]:
    """Paint selected component dictionaries into a fresh zero grid."""
    _validate_grid(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for obj in objects:
        color = obj["color"]
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def _partition(grid: list[list[int]]):
    objects = _components(grid)
    height, width = len(grid), len(grid[0])
    borders = [obj for obj in objects if _edges(obj, height, width)]
    interiors = [obj for obj in objects if not _edges(obj, height, width)]
    return objects, borders, interiors


def observables(grid: list[list[int]]) -> dict[str, Any]:
    """Expose structural facts for focused tests and future audits."""
    objects, borders, interiors = _partition(grid)
    height, width = len(grid), len(grid[0])
    signals = [obj for obj in borders if obj["color"] == 1]
    if len(signals) != 1:
        raise ValueError("generated scene must have exactly one blue border signal")
    signal = signals[0]
    touched = sorted({edge for obj in borders for edge in _edges(obj, height, width)})
    return {
        "objects": copy.deepcopy(objects),
        "borders": copy.deepcopy(borders),
        "interiors": copy.deepcopy(interiors),
        "border_count": len(borders),
        "interior_count": len(interiors),
        "signal_color": signal["color"],
        "signal_rank": signal["size"],
        "signal_bbox": signal["bbox"],
        "signal_touches_border": bool(_edges(signal, height, width)),
        "touched_edges": touched,
    }


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    """Python claim-label mirror; protected Racket remains authoritative."""
    mode = _retention(settings)
    _objects, borders, interiors = _partition(grid)
    if mode == "all_interior":
        return paint_objects(grid, interiors)
    signals = [obj for obj in borders if obj["color"] == 1]
    if len(signals) != 1:
        raise ValueError("signal_rank requires one blue border signal")
    rank = signals[0]["size"]
    if not 1 <= rank <= len(interiors):
        raise ValueError("signal rank exceeds the number of interior objects")
    return paint_objects(grid, [interiors[rank - 1]])


def solve_rival(grid: list[list[int]], name: str) -> list[list[int]]:
    """Finite plausible shortcuts used by the bounded lesson audit."""
    objects, borders, interiors = _partition(grid)
    if not interiors:
        return paint_objects(grid, [])
    signals = [obj for obj in borders if obj["color"] == 1]
    if len(signals) != 1:
        raise ValueError("rivals require the generated signal grammar")
    rank = signals[0]["size"]
    if name == "first_interior":
        selected = interiors[:1]
    elif name == "last_interior":
        selected = interiors[-1:]
    elif name == "smallest_interior":
        selected = [min(interiors, key=lambda obj: (obj["size"], obj["bbox"]))]
    elif name == "largest_interior":
        selected = [max(interiors, key=lambda obj: (obj["size"], tuple(-v for v in obj["bbox"])))]
    elif name == "column_major_rank":
        ordered = sorted(interiors, key=lambda obj: (obj["bbox"][1], obj["bbox"][0], obj["bbox"][3], obj["bbox"][2]))
        selected = [ordered[rank - 1]]
    elif name == "reverse_row_major_rank":
        selected = [list(reversed(interiors))[rank - 1]]
    elif name == "signal_size_match":
        selected = [obj for obj in interiors if obj["size"] == rank]
    elif name == "fixed_rank_2":
        selected = [interiors[min(1, len(interiors) - 1)]]
    elif name == "fixed_rank_4":
        selected = [interiors[min(3, len(interiors) - 1)]]
    elif name == "erase_border_cells_only":
        output = copy.deepcopy(grid)
        for col in range(len(grid[0])):
            output[0][col] = 0
            output[-1][col] = 0
        for row in range(len(grid)):
            output[row][0] = 0
            output[row][-1] = 0
        return output
    else:
        raise ValueError(f"unknown rival: {name}")
    return paint_objects(grid, selected)


def _derived_rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _normal_shape(size: int, rng: random.Random, *, variant: int | None = None):
    variants = _SHAPES[size]
    return variants[variant % len(variants)] if variant is not None else rng.choice(variants)


def _place(grid: list[list[int]], cells: list[tuple[int, int]], color: int, *, separate_same_color: bool = True):
    height, width = len(grid), len(grid[0])
    cell_set = set(cells)
    if len(cell_set) != len(cells):
        raise ValueError("shape contains duplicate cells")
    for row, col in cells:
        if not (0 <= row < height and 0 <= col < width) or grid[row][col] != 0:
            raise ValueError("shape placement collides or leaves the grid")
        if separate_same_color:
            for dr, dc in _ORTHOGONAL:
                rr, cc = row + dr, col + dc
                if (rr, cc) not in cell_set and 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == color:
                    raise ValueError("same-color placements would merge")
    for row, col in cells:
        grid[row][col] = color


def _interior_slots(height: int, width: int, count: int) -> list[tuple[int, int]]:
    rows = (2, (height - 3) // 2, height - 4)
    cols = (2, (width - 3) // 2, width - 4)
    pattern = ((0, 1), (1, 0), (1, 2), (2, 1), (2, 2), (0, 0), (0, 2), (2, 0), (1, 1))
    selected = sorted((rows[ri], cols[ci]) for ri, ci in pattern[:count])
    if len(selected) != count or len(set(selected)) != count:
        raise ValueError("profile is too small for its interior-object count")
    return selected


def _sizes(split: str, index: int, count: int, rank: int, rng: random.Random) -> list[int]:
    if split == "train" and index == 0:
        values = [3, 5, 2, 4, 1, 6, 7, 2]
    elif split == "train" and index == 1:
        values = [5, 2, 4, 1, 3, 6, 7, 2]
    elif split == "test" and index == 3:
        values = [7, 5, 6, 4, 3, 5, 6, 4]
    else:
        values = [1, 2, 3, 4, 5, 6, 7, 3][:count]
        rng.shuffle(values)
    values = values[:count]
    chosen = rank - 1
    # Keep rank and target-size interpretations distinct in every generated pair.
    if values[chosen] == rank:
        swap = next(i for i, value in enumerate(values) if i != chosen and value != rank)
        values[chosen], values[swap] = values[swap], values[chosen]
    # Avoid making the chosen component invariably the largest or smallest.
    if count >= 4 and values[chosen] in {min(values), max(values)} and not (split == "train" and index < 2):
        ordered = sorted(range(count), key=lambda i: values[i])
        middle = ordered[len(ordered) // 2]
        values[chosen], values[middle] = values[middle], values[chosen]
    return values


def _edge_cells(edge: str, height: int, width: int, offsets: tuple[tuple[int, int], ...], start: int):
    if edge == "top":
        return [(depth, start + along) for depth, along in offsets]
    if edge == "bottom":
        return [(height - 1 - depth, start + along) for depth, along in offsets]
    if edge == "left":
        return [(start + along, depth) for depth, along in offsets]
    if edge == "right":
        return [(start + along, width - 1 - depth) for depth, along in offsets]
    raise ValueError(edge)


def _place_edge_object(
    grid: list[list[int]], edge: str, offsets: tuple[tuple[int, int], ...], color: int, rng: random.Random
):
    height, width = len(grid), len(grid[0])
    along_span = max(along for _depth, along in offsets) + 1
    length = width if edge in {"top", "bottom"} else height
    starts = list(range(1, length - along_span))
    rng.shuffle(starts)
    for start in starts:
        cells = _edge_cells(edge, height, width, offsets, start)
        try:
            _place(grid, cells, color)
        except ValueError:
            continue
        return cells
    raise ValueError(f"could not place {edge} object")


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    rng = _derived_rng(seed, split, index)
    if split == "train":
        height, width = _DEMO_DIMS[index]
        count = _DEMO_COUNTS[index]
        rank = _DEMO_RANKS[index]
    elif split == "test":
        height, width = _QUERY_DIMS[index]
        count = _QUERY_COUNTS[index]
        base = _QUERY_RANKS[index]
        rank = ((base - 1 + rng.randrange(5)) % 5) + 1
    else:  # pragma: no cover - internal guard
        raise ValueError(split)
    grid = [[0] * width for _ in range(height)]
    colors = list(range(2, 10))
    rng.shuffle(colors)
    sizes = _sizes(split, index, count, rank, rng)
    slots = _interior_slots(height, width, count)
    for object_index, ((top, left), size, color) in enumerate(zip(slots, sizes, colors[:count], strict=True)):
        shape = _normal_shape(size, rng, variant=0 if object_index == 0 else None)
        _place(grid, [(top + dr, left + dc) for dr, dc in shape], color)

    # Same-color diagonal witness: a top-border tail shares the first interior
    # color but only touches it diagonally under the canonical 4-connectivity.
    objects, _borders, interiors = _partition(grid)
    del objects
    first = interiors[0]
    top, left, _bottom, _right = first["bbox"]
    if top != 2 or grid[top][left] != first["color"]:
        raise AssertionError("first interior slot must expose its normalized top-left cell")
    _place(grid, [(0, left - 1), (1, left - 1)], first["color"])

    # Three additional edge objects have inward tails, so deleting only the
    # perimeter cannot imitate whole-object border filtering.
    edge_offsets = ((0, 0), (1, 0), (2, 0), (2, 1))
    _place_edge_object(grid, "bottom", edge_offsets, colors[1], rng)
    _place_edge_object(grid, "left", edge_offsets, colors[2], rng)
    _place_edge_object(grid, "right", edge_offsets, colors[3], rng)

    signal_shapes = {
        1: ((0, 0),),
        2: ((0, 0), (1, 0)),
        3: ((0, 0), (1, 0), (1, 1)),
        4: ((0, 0), (0, 1), (1, 0), (1, 1)),
        5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    }
    edge = ("top", "right", "bottom", "left")[(index + rng.randrange(4)) % 4]
    _place_edge_object(grid, edge, signal_shapes[rank], 1, rng)

    facts = observables(grid)
    if (facts["interior_count"] != count or facts["signal_rank"] != rank
            or set(facts["touched_edges"]) != {"top", "bottom", "left", "right"}
            or solve(grid, {PARAMETER: "all_interior"}) == solve(grid, {PARAMETER: "signal_rank"})):
        raise AssertionError("constructed scene violates the parametric grammar")
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Generate a deterministic matched-input episode with stable split prefixes."""
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _retention(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    chosen = {PARAMETER: mode}
    return {
        "train": [{"input": grid, "output": solve(grid, chosen)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, chosen)} for grid in test_inputs],
        "program_solution": _PROGRAMS[mode],
    }


RIVAL_NAMES = (
    "first_interior",
    "last_interior",
    "smallest_interior",
    "largest_interior",
    "column_major_rank",
    "reverse_row_major_rank",
    "signal_size_match",
    "fixed_rank_2",
    "fixed_rank_4",
    "erase_border_cells_only",
)


def audit_episode(seed: int, mode: str, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    """Return a finite lesson-survivor report used by audit_lessons.py."""
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    other = MODES[1 - MODES.index(mode)]
    findings = []
    if all(solve(pair["input"], {PARAMETER: other}) == pair["output"] for pair in episode["train"]):
        findings.append({"rival": other, "reason": "declared alternate survives demonstrations"})
    for rival in RIVAL_NAMES:
        fits = all(solve_rival(pair["input"], rival) == pair["output"] for pair in episode["train"])
        harmful = any(solve_rival(pair["input"], rival) != pair["output"] for pair in episode["test"])
        if fits and harmful:
            findings.append({"rival": rival, "reason": "fits demos and changes a query"})
    return {
        "seed": seed,
        "settings": {PARAMETER: mode},
        "demos": demos,
        "queries": queries,
        "findings": findings,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--retention", choices=MODES, default=MODES[0])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, {PARAMETER: args.retention}, args.demos, args.queries), indent=2))
