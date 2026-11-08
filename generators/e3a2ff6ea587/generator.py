"""Constructive generator for ARC task ``e3a2ff6ea587``.

Canonical rule
--------------
Visit non-background colors in first-appearance order.  A color qualifies only
when it has exactly four cells and those cells are exactly the four corners of
its bounding box.  Qualifying colors paint their entire bounding box into a
fresh zero grid; every other color is omitted.

The ordinary curriculum deliberately mixes qualifying rectangles with three
minimal negative classes.  This prevents the former shortcut of filling every
nonzero color's bounding box and makes every declared control observable.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e3a2ff6ea587"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "fc212e483f16"
SUMMARY = (
    "A zero-background grid contains one to three true rectangle-corner colors "
    "and one to three deliberately nonqualifying colors.  In first-appearance "
    "order, a color with exactly four cells at exactly the corners of its bbox "
    "fills that bbox into a fresh output; all other colors disappear."
)
EXAMPLES_NEEDED = 3

DISTRACTOR_TEXTURES = ("three_corners", "misplaced_four", "extra_cell")
TEXTURES = ("mixed",) + DISTRACTOR_TEXTURES
DEGENERATE_TEXTURES = ("only_3_corners", "cells_aligned", "no_cells")
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "n_rects", "n_distractors", "texture"}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "7..9 easy / 8..10 medium / 10..12 hard",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "9..12 easy / 11..14 medium / 13..16 hard",
        "valid": "9..16",
    },
    "n_rects": {
        "type": "int",
        "default": "1 easy / 1..2 medium / 2..3 hard",
        "valid": "1..3",
    },
    "n_distractors": {
        "type": "int",
        "default": "1 easy / 1..2 medium / 2..3 hard",
        "valid": "1..3",
    },
    "texture": {
        "type": "str",
        "default": "mixed",
        "valid": "|".join(TEXTURES + DEGENERATE_TEXTURES),
    },
}

INVARIANTS = [
    "ordinary samples contain at least one qualifying and one nonqualifying color",
    "qualifying colors have exactly the four non-degenerate bbox corners",
    "negative colors instantiate a named near-miss rather than random noise",
    "all controls are strict, deterministic, and observable from the generated grid",
]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _colors_in_appearance_order(grid: list[list[int]]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                result.append(value)
    return result


def _cells_by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                result[value].append((r, c))
    return dict(result)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    rows = [r for r, _ in points]
    columns = [c for _, c in points]
    return min(rows), min(columns), max(rows), max(columns)


def _corners(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}


def _is_qualifying(cells: Iterable[tuple[int, int]]) -> bool:
    points = tuple(cells)
    if len(points) != 4:
        return False
    box = _bbox(points)
    return box[0] < box[2] and box[1] < box[3] and set(points) == _corners(box)


def _distractor_kind(cells: Iterable[tuple[int, int]]) -> str | None:
    points = tuple(cells)
    if not points:
        return None
    box = _bbox(points)
    corners = _corners(box)
    if len(points) == 3 and set(points) <= corners:
        return "three_corners"
    if len(points) == 4 and set(points) != corners:
        return "misplaced_four"
    if len(points) == 5 and corners < set(points):
        return "extra_cell"
    return None


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the exact canonical Racket semantics."""
    height, width = _validate_grid(grid)
    cells = _cells_by_color(grid)
    out = full_grid(height, width, 0)
    for color in _colors_in_appearance_order(grid):
        positions = cells[color]
        if not _is_qualifying(positions):
            continue
        r1, c1, r2, c2 = _bbox(positions)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] = color
    return out


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    """Recover every declared constructive control from a generated sample."""
    height, width = _validate_grid(grid)
    by_color = _cells_by_color(grid)
    positives = [cells for cells in by_color.values() if _is_qualifying(cells)]
    negatives = [cells for cells in by_color.values() if not _is_qualifying(cells)]
    kinds = [_distractor_kind(cells) for cells in negatives]
    known = [kind for kind in kinds if kind is not None]
    if len(set(known)) > 1:
        texture = "mixed"
    elif known:
        texture = known[0]
    elif not negatives:
        texture = "none"
    else:
        texture = "unknown"
    return {
        "grid_h": height,
        "grid_w": width,
        "n_rects": len(positives),
        "n_distractors": len(negatives),
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the constructive grammar and optional pinned-control witness."""
    try:
        _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]

    meta = meta or {}
    expected = meta.get("overrides", meta)
    texture = expected.get("texture") if isinstance(expected, dict) else None
    if texture in DEGENERATE_TEXTURES:
        return []

    observed = observe_overrides(grid)
    issues: list[str] = []
    if observed["n_rects"] < 1:
        issues.append("no color forms an exact four-corner rectangle")
    if observed["n_distractors"] < 1:
        issues.append("no nonqualifying color; fill-every-bbox shortcut survives")

    by_color = _cells_by_color(grid)
    unknown = [color for color, cells in by_color.items() if not _is_qualifying(cells) and _distractor_kind(cells) is None]
    if unknown:
        issues.append(f"unclassified distractor colors: {unknown}")

    if isinstance(expected, dict):
        for key in ("grid_h", "grid_w", "n_rects", "n_distractors", "texture"):
            if key in expected and expected[key] is not None and observed[key] != expected[key]:
                issues.append(f"{key}: expected {expected[key]!r}, observed {observed[key]!r}")
    return issues


def _shape_cells(
    kind: str,
    r1: int,
    c1: int,
    r2: int,
    c2: int,
    *,
    variant: int,
) -> tuple[tuple[int, int], ...]:
    corners = ((r1, c1), (r1, c2), (r2, c1), (r2, c2))
    if kind == "qualifying":
        return corners
    if kind == "three_corners":
        missing = variant % 4
        return tuple(cell for index, cell in enumerate(corners) if index != missing)
    if kind == "misplaced_four":
        missing = variant % 4
        interior_options = (
            (r1 + 1, c1 + 1),
            (r1 + 1, c2 - 1),
            (r2 - 1, c1 + 1),
            (r2 - 1, c2 - 1),
        )
        return tuple(cell for index, cell in enumerate(corners) if index != missing) + (
            interior_options[missing],
        )
    if kind == "extra_cell":
        return corners + ((r1 + 1 + variant % max(1, r2 - r1 - 1), c1 + 1),)
    raise ValueError(f"unknown shape kind {kind!r}")


def _place_shape(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    color: int,
    kind: str,
    rng,
) -> None:
    height, width = len(grid), len(grid[0])
    max_height = min(7, height)
    max_width = min(7, width)
    for attempt in range(1024):
        rect_height = rng.randint(3, max_height)
        rect_width = rng.randint(3, max_width)
        r1 = rng.randint(0, height - rect_height)
        c1 = rng.randint(0, width - rect_width)
        r2, c2 = r1 + rect_height - 1, c1 + rect_width - 1
        cells = _shape_cells(kind, r1, c1, r2, c2, variant=attempt + rng.randrange(32))
        if len(set(cells)) != len(cells) or any(cell in occupied for cell in cells):
            continue
        for r, c in cells:
            grid[r][c] = color
            occupied.add((r, c))
        return
    raise RuntimeError(f"could not place {kind} shape in {height}x{width} grid")


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(7, 9, 0)
    if name == "only_3_corners":
        grid[1][1] = grid[1][6] = grid[5][1] = 4
    elif name == "cells_aligned":
        for column in (1, 3, 5, 7):
            grid[3][column] = 5
    elif name == "no_cells":
        pass
    else:
        raise ValueError(f"unknown degenerate texture {name!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        h = ctx.draw_int_strict("grid_h", 7, 9)
        w = ctx.draw_int_strict("grid_w", 9, 12)
        n_rects = ctx.draw_int_strict("n_rects", 1, 1)
        n_distractors = ctx.draw_int_strict("n_distractors", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int_strict("grid_h", 10, 12)
        w = ctx.draw_int_strict("grid_w", 13, 16)
        n_rects = ctx.draw_int_strict("n_rects", 2, 3)
        n_distractors = ctx.draw_int_strict("n_distractors", 2, 3)
    else:
        h = ctx.draw_int_strict("grid_h", 8, 10)
        w = ctx.draw_int_strict("grid_w", 11, 14)
        n_rects = ctx.draw_int_strict("n_rects", 1, 2)
        n_distractors = ctx.draw_int_strict("n_distractors", 1, 2)

    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        if any(key in overrides for key in ("grid_h", "grid_w", "n_rects", "n_distractors")):
            raise ValueError("degenerate textures do not accept constructive count/size overrides")
        # Record the explicit axis through the normal validity/provenance gate.
        texture = ctx.draw_choice("texture", TEXTURES + DEGENERATE_TEXTURES)
        return _draw_from_degenerate(texture)
    texture = ctx.draw_choice("texture", TEXTURES)

    total_colors = n_rects + n_distractors
    colors = ctx.draw_distinct_colors("shape_colors", n=total_colors, exclude=(0,))
    layout_rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()

    shape_plan: list[tuple[int, str]] = [(color, "qualifying") for color in colors[:n_rects]]
    if texture == "mixed":
        offset = layout_rng.randrange(len(DISTRACTOR_TEXTURES))
        kinds = [DISTRACTOR_TEXTURES[(offset + index) % len(DISTRACTOR_TEXTURES)] for index in range(n_distractors)]
        # A pinned three-distractor mixed sample must expose every negative class.
        if n_distractors == len(DISTRACTOR_TEXTURES):
            kinds = list(DISTRACTOR_TEXTURES)
            layout_rng.shuffle(kinds)
    else:
        kinds = [texture] * n_distractors
    shape_plan.extend(zip(colors[n_rects:], kinds))
    layout_rng.shuffle(shape_plan)

    for color, kind in shape_plan:
        _place_shape(grid, occupied, color, kind, layout_rng)

    issues = self_check(grid)
    if issues:
        raise RuntimeError(f"constructive generator emitted invalid grid: {issues}")
    return grid
