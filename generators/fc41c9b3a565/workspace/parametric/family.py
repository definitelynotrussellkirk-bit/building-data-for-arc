"""Deterministic two-stage parametric family for ARC task fc41c9b3a565.

The canonical setting retains exactly the monochrome components whose
normalised masks are invariant under a half turn.  The composed setting
performs that operation first, then highlights the unique largest survivor.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "fc41c9b3a565"
MODES = ("canonical", "largest_symmetric_highlight")
HIGHLIGHT_COLOR = 9
PARAMETRIC_DIR = Path(__file__).resolve().parent

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]


def _normalise(cells: Iterable[Cell]) -> Shape:
    points = tuple(cells)
    if not points:
        return ()
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _rect(rows: int, cols: int, removed: Iterable[Cell] = ()) -> Shape:
    missing = set(removed)
    return _normalise(
        (r, c) for r in range(rows) for c in range(cols) if (r, c) not in missing
    )


SHAPES: dict[str, Shape] = {
    "sym5": _normalise(((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))),
    "sym7": _rect(3, 3, ((0, 0), (2, 2))),
    "sym9": _rect(3, 3),
    "sym13": _normalise(
        (r, c) for r in range(5) for c in range(5) if abs(r - 2) + abs(c - 2) <= 2
    ),
    "sym16": _rect(4, 4),
    "sym17": _normalise(
        [(r, c) for r in range(5) for c in range(5) if abs(r - 2) + abs(c - 2) <= 2]
        + [(0, 1), (1, 0), (3, 4), (4, 3)]
    ),
    "sym25": _rect(5, 5),
    "asym10": _rect(3, 4, ((0, 0), (0, 1))),
    "asym14": _rect(4, 4, ((0, 0), (0, 1))),
    "asym15": _rect(4, 4, ((0, 0),)),
    "asym18": _rect(4, 5, ((0, 0), (0, 1))),
    "asym21": _rect(5, 5, ((0, 0), (0, 1), (0, 2), (0, 3))),
    "asym24": _rect(5, 5, ((0, 0),)),
    "asym27": _rect(5, 6, ((0, 0), (0, 1), (1, 0))),
    "asym29": _rect(5, 6, ((0, 0),)),
    "asym35": _rect(6, 6, ((0, 0),)),
}

# Every profile has at least two survivors and at least one asymmetric object
# larger than the unique largest survivor.  The number of larger asymmetric
# distractors varies, so the winner's original rank cannot be memorised.
PROFILE_SHAPES: tuple[tuple[str, ...], ...] = (
    ("asym15", "sym13", "sym9", "sym7", "sym5"),
    ("asym24", "asym18", "sym16", "sym13", "sym9", "sym5"),
    ("asym24", "asym21", "asym18", "sym17", "sym13", "sym9", "sym7"),
)
STRESS_SHAPES = (
    "asym35",
    "asym29",
    "asym27",
    "sym25",
    "sym17",
    "sym13",
    "sym9",
    "sym7",
)
DEMO_SIZES = ((16, 18), (17, 20), (18, 22), (20, 23), (22, 25), (24, 27))
QUERY_SIZES = ((19, 21), (21, 24), (26, 28), (30, 30))


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def validate_settings(settings: Any) -> dict[str, str]:
    if not isinstance(settings, dict) or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly the key 'mode'")
    mode = settings["mode"]
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return {"mode": mode}


def _validate_request(seed: Any, demos: Any, queries: Any) -> tuple[int, int, int]:
    return (
        _strict_int("seed", seed, 0, 2**63 - 1),
        _strict_int("demos", demos, 2, 6),
        _strict_int("queries", queries, 1, 4),
    )


def _shape_size(shape: Shape) -> int:
    return len(shape)


def _shape_bounds(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _rotate(shape: Shape) -> Shape:
    height, width = _shape_bounds(shape)
    return _normalise((c, height - 1 - r) for r, c in shape)


def _flip(shape: Shape) -> Shape:
    _, width = _shape_bounds(shape)
    return _normalise((r, width - 1 - c) for r, c in shape)


def _transform(shape: Shape, code: int) -> Shape:
    out = shape
    if code >= 4:
        out = _flip(out)
    for _ in range(code % 4):
        out = _rotate(out)
    return _normalise(out)


def _half_turn_symmetric(shape: Shape) -> bool:
    height, width = _shape_bounds(shape)
    turned = _normalise((height - 1 - r, width - 1 - c) for r, c in shape)
    return shape == turned


def _components(grid: Grid) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[Cell] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            cells.sort()
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            shape = _normalise(cells)
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "size": len(cells),
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "shape": shape,
                    "symmetric": _half_turn_symmetric(shape),
                }
            )
    return result


def _ranked(components: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        components,
        key=lambda item: (-item["size"], item["r1"], item["c1"], item["color"]),
    )


def _blank_like(grid: Grid) -> Grid:
    return [[0 for _ in row] for row in grid]


def _paint(grid: Grid, cells: Iterable[Cell], color: int) -> Grid:
    out = [row[:] for row in grid]
    for r, c in cells:
        out[r][c] = color
    return out


def _canonical(grid: Grid) -> Grid:
    out = _blank_like(grid)
    for component in _components(grid):
        if component["symmetric"]:
            for r, c in component["cells"]:
                out[r][c] = component["color"]
    return out


def _largest_survivor(grid: Grid) -> dict[str, Any]:
    survivors = _ranked(_components(_canonical(grid)))
    if not survivors:
        raise ValueError("generated grid has no symmetric component")
    if len(survivors) > 1 and survivors[0]["size"] == survivors[1]["size"]:
        raise ValueError("generated grid has no unique largest survivor")
    return survivors[0]


def solve(grid: Grid, mode: str) -> Grid:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    intermediate = _canonical(grid)
    if mode == "canonical":
        return intermediate
    winner = _largest_survivor(grid)
    return _paint(intermediate, winner["cells"], HIGHLIGHT_COLOR)


def solve_wrong_order(grid: Grid) -> Grid:
    largest_original = _ranked(_components(grid))[0]
    return _paint(_canonical(grid), largest_original["cells"], HIGHLIGHT_COLOR)


def solve_fixed_color(grid: Grid, color: int) -> Grid:
    intermediate = _canonical(grid)
    cells = [
        cell
        for component in _components(intermediate)
        if component["color"] == color
        for cell in component["cells"]
    ]
    return _paint(intermediate, cells, HIGHLIGHT_COLOR)


def solve_fixed_original_rank(grid: Grid, rank: int) -> Grid:
    ranked = _ranked(_components(grid))
    if not 1 <= rank <= len(ranked):
        return _canonical(grid)
    return _paint(_canonical(grid), ranked[rank - 1]["cells"], HIGHLIGHT_COLOR)


def trace(grid: Grid) -> dict[str, Any]:
    original = _components(grid)
    ranked = _ranked(original)
    intermediate = _canonical(grid)
    survivors = _ranked(_components(intermediate))
    if not ranked or not survivors:
        raise ValueError("trace requires original and surviving components")
    winner = survivors[0]
    winner_rank = next(
        index
        for index, component in enumerate(ranked, start=1)
        if component["color"] == winner["color"]
        and component["cells"] == winner["cells"]
    )
    return {
        "intermediate": intermediate,
        "largest_original_is_symmetric": bool(ranked[0]["symmetric"]),
        "survivor_count": len(survivors),
        "winner_size": winner["size"],
        "largest_original_size": ranked[0]["size"],
        "winner_color": winner["color"],
        "winner_original_rank": winner_rank,
        "winner_cells": [list(cell) for cell in winner["cells"]],
        "object_count": len(original),
        "foreground_cells": sum(component["size"] for component in original),
        "original_sizes": [component["size"] for component in ranked],
        "survivor_sizes": [component["size"] for component in survivors],
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _candidate_anchors(
    height: int, width: int, shape: Shape, rng: random.Random
) -> list[Cell]:
    shape_height, shape_width = _shape_bounds(shape)
    anchors = [
        (r, c)
        for r in range(height - shape_height + 1)
        for c in range(width - shape_width + 1)
    ]
    rng.shuffle(anchors)
    return anchors


def _buffered_conflict(cells: set[Cell], occupied: set[Cell]) -> bool:
    for r, c in cells:
        if (r, c) in occupied:
            return True
        if any(
            neighbour in occupied
            for neighbour in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        ):
            return True
    return False


def _place_shapes(
    height: int,
    width: int,
    named_shapes: tuple[str, ...],
    rng: random.Random,
) -> list[tuple[Shape, set[Cell]]]:
    transformed: list[tuple[Shape, int]] = []
    for name in named_shapes:
        shape = _transform(SHAPES[name], rng.randrange(8))
        transformed.append((shape, _shape_size(shape)))
    transformed.sort(key=lambda item: -item[1])

    def search(position: int, occupied: set[Cell], placed: list[tuple[Shape, set[Cell]]]):
        if position == len(transformed):
            return placed
        shape = transformed[position][0]
        candidates = _candidate_anchors(height, width, shape, rng)
        for anchor_r, anchor_c in candidates:
            absolute = {(anchor_r + r, anchor_c + c) for r, c in shape}
            if _buffered_conflict(absolute, occupied):
                continue
            answer = search(position + 1, occupied | absolute, placed + [(shape, absolute)])
            if answer is not None:
                return answer
        return None

    answer = search(0, set(), [])
    if answer is None:
        raise RuntimeError(f"could not place {len(named_shapes)} objects in {height}x{width}")
    return answer


def sample_input(seed: int, split: str, index: int) -> Grid:
    if split == "train":
        if not 0 <= index < len(DEMO_SIZES):
            raise ValueError("train profile index out of range")
        height, width = DEMO_SIZES[index]
        names = PROFILE_SHAPES[index % len(PROFILE_SHAPES)]
    elif split == "test":
        if not 0 <= index < len(QUERY_SIZES):
            raise ValueError("test profile index out of range")
        height, width = QUERY_SIZES[index]
        names = STRESS_SHAPES if index == 3 else PROFILE_SHAPES[(index + 1) % 3]
    else:
        raise ValueError("split must be 'train' or 'test'")

    rng = _rng(seed, split, index)
    placements = _place_shapes(height, width, names, rng)
    colors = list(range(1, len(placements) + 1))
    rng.shuffle(colors)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, (_, cells) in zip(colors, placements):
        for r, c in cells:
            grid[r][c] = color

    details = trace(grid)
    if details["largest_original_is_symmetric"]:
        raise AssertionError("profile failed to make the largest original object asymmetric")
    if details["survivor_count"] < 2:
        raise AssertionError("profile failed to provide multiple survivors")
    if details["winner_size"] >= details["largest_original_size"]:
        raise AssertionError("profile failed to make stage B depend on stage A")
    return grid


def rule_text(mode: str) -> str:
    if mode == "canonical":
        name = "canonical.rkt"
    elif mode == "largest_symmetric_highlight":
        name = "largest_symmetric_highlight.rkt"
    else:
        raise ValueError(f"mode must be one of {MODES}")
    return (PARAMETRIC_DIR / name).read_text(encoding="utf-8")


def generate_episode(seed: Any, mode: str, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed, demos, queries = _validate_request(seed, demos, queries)
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    train = []
    test = []
    for index in range(demos):
        grid = sample_input(seed, "train", index)
        train.append({"input": grid, "output": solve(grid, mode)})
    for index in range(queries):
        grid = sample_input(seed, "test", index)
        test.append({"input": grid, "output": solve(grid, mode)})
    return {"train": train, "test": test, "program_solution": rule_text(mode)}
