"""Input generator for ARC task 1d23d72f3b43.

For every non-background color appearing exactly twice, the unchanged Racket
rule fills the inclusive axis-aligned bounding rectangle of the two cells with
that color.  The two cells are diagonal corners; different colors have disjoint
bounding boxes.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1d23d72f3b43"
TASK_ID = GENERATOR_ID
RULE_HASH = "013675ae7255"
VERSION = "3.1.0"
SUMMARY = (
    "An 8-12 by 8-12 zero-background grid contains 2-4 colors, each exactly "
    "twice at opposite diagonal corners of a non-degenerate rectangle. The "
    "rectangles are disjoint and include both diagonal orientations. Fill each "
    "color's entire inclusive bounding box with that color."
)

INVARIANTS = [
    "2-4 distinct non-background colors, each appearing exactly twice",
    "each pair occupies opposite diagonal corners of a rectangle",
    "different colors' inclusive bounding boxes do not overlap",
    "ordinary draws contain both diagonal orientations",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 8..12", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 8..12", "valid": "8..12"},
    "n_pairs": {"type": "int", "default": "difficulty-weighted 2..4", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


Grid = list[list[int]]
Point = tuple[int, int]
Rect = tuple[int, int, int, int]


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _weighted_int(ctx, label: str, lo: int, hi: int, favored: Iterable[int]) -> int:
    """Draw from the full exact domain while weighting a difficulty profile."""
    base = list(range(lo, hi + 1))
    weighted = base + [value for value in favored for _ in range(8)]
    return ctx.draw_choice(label, tuple(weighted))


def _difficulty_favorites(difficulty: object) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if difficulty == "easy":
        return (8, 9), (2,)
    if difficulty == "hard":
        # Keep the largest canvases / four-pair cases favored without
        # abandoning the canonical two-pair, 8-10 scale entirely.
        return (9, 10, 11, 12), (2, 3, 4)
    if difficulty == "medium":
        return (9, 10), (2, 3)
    return (8, 9, 10), (2, 3)


def _slot_bounds(h: int, w: int, rng) -> list[Rect]:
    """Four disjoint, randomly split slots, each at least 3x3."""
    split_r = rng.randint(3, h - 3)
    split_c = rng.randint(3, w - 3)
    slots = [
        (0, 0, split_r - 1, split_c - 1),
        (0, split_c, split_r - 1, w - 1),
        (split_r, 0, h - 1, split_c - 1),
        (split_r, split_c, h - 1, w - 1),
    ]
    rng.shuffle(slots)
    return slots


def _draw_rect(slot: Rect, profile: str, rng) -> Rect:
    sr0, sc0, sr1, sc1 = slot
    slot_h = sr1 - sr0 + 1
    slot_w = sc1 - sc0 + 1

    if profile == "solid":
        rh = rng.randint(3, slot_h)
        rw = rng.randint(3, slot_w)
    elif profile == "horizontal":
        rh = 2
        rw = rng.randint(3, slot_w)
    elif profile == "vertical":
        rh = rng.randint(3, slot_h)
        rw = 2
    else:
        rh = rng.randint(2, slot_h)
        rw = rng.randint(2, slot_w)

    r0 = rng.randint(sr0, sr1 - rh + 1)
    c0 = rng.randint(sc0, sc1 - rw + 1)
    return r0, c0, r0 + rh - 1, c0 + rw - 1


def _shape_profiles(n_pairs: int, rng) -> list[str]:
    if n_pairs == 2:
        profiles = ["solid", rng.choice(("horizontal", "vertical"))]
    elif n_pairs == 3:
        profiles = ["solid", "horizontal", "vertical"]
    else:
        profiles = ["solid", "horizontal", "vertical", "any"]
    rng.shuffle(profiles)
    return profiles


def _orientations(n_pairs: int, rng) -> list[str]:
    orientations = ["main", "anti"]
    orientations.extend(rng.choice(("main", "anti")) for _ in range(n_pairs - 2))
    rng.shuffle(orientations)
    return orientations


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size_favorites, pair_favorites = _difficulty_favorites(difficulty)
    h = _weighted_int(ctx, "grid_h", 8, 12, size_favorites)
    w = _weighted_int(ctx, "grid_w", 8, 12, size_favorites)
    n_pairs = _weighted_int(ctx, "n_pairs", 2, 4, pair_favorites)

    layout_rng = ctx.draw_rng("layout")
    palette = ctx.draw_rng("palette").sample(range(1, 10), n_pairs)
    slots = _slot_bounds(h, w, layout_rng)
    profiles = _shape_profiles(n_pairs, layout_rng)
    orientations = _orientations(n_pairs, layout_rng)

    grid = full_grid(h, w, 0)
    for color, slot, profile, orientation in zip(
        palette, slots[:n_pairs], profiles, orientations
    ):
        r0, c0, r1, c1 = _draw_rect(slot, profile, layout_rng)
        if orientation == "main":
            points = ((r0, c0), (r1, c1))
        else:
            points = ((r0, c1), (r1, c0))
        for r, c in points:
            grid[r][c] = color
    return grid


def _positions_by_color(grid: Sequence[Sequence[int]]) -> dict[int, list[Point]]:
    positions: dict[int, list[Point]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))
    return dict(positions)


def _bbox(points: Sequence[Point]) -> Rect:
    (r0, c0), (r1, c1) = points
    return min(r0, r1), min(c0, c1), max(r0, r1), max(c0, c1)


def _rect_cells(rect: Rect) -> set[Point]:
    r0, c0, r1, c1 = rect
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    h, w = len(grid), width
    errors: list[str] = []
    if not 8 <= h <= 12 or not 8 <= w <= 12:
        errors.append(f"grid shape {(h, w)} outside 8..12 by 8..12")

    positions = _positions_by_color(grid)
    if not 2 <= len(positions) <= 4:
        errors.append(f"expected 2-4 non-background colors, found {len(positions)}")

    boxes: list[tuple[int, set[Point]]] = []
    for color, points in sorted(positions.items()):
        if len(points) != 2:
            errors.append(f"color {color} occurs {len(points)} times, expected exactly 2")
            continue
        (r0, c0), (r1, c1) = points
        if r0 == r1 or c0 == c1:
            errors.append(f"color {color} pair is collinear, not diagonal")
            continue
        boxes.append((color, _rect_cells(_bbox(points))))

    for index, (color, cells) in enumerate(boxes):
        for other_color, other_cells in boxes[index + 1 :]:
            if cells & other_cells:
                errors.append(
                    f"inclusive bounding boxes for colors {color} and {other_color} overlap"
                )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(_positions_by_color(grid)),
    }


def _fill_pairs(grid, *, main_only: bool = False) -> Grid:
    out = [list(row) for row in grid]
    for color, points in _positions_by_color(grid).items():
        if len(points) != 2:
            continue
        ordered = sorted(points)
        (r0, c0), (r1, c1) = ordered
        if main_only and c1 < c0:
            continue
        br0, bc0, br1, bc1 = _bbox(points)
        for r in range(br0, br1 + 1):
            for c in range(bc0, bc1 + 1):
                out[r][c] = color
    return out


def _main_diagonal_only(grid):
    """Plausible canonical shortcut: ignore anti-diagonal corner pairs."""
    return _fill_pairs(grid, main_only=True)


def _has_anti_diagonal_pair(grid) -> bool:
    for points in _positions_by_color(grid).values():
        if len(points) != 2:
            continue
        (r0, c0), (r1, c1) = sorted(points)
        if c1 < c0:
            return True
    return False


def lesson_identifiable(demos, query) -> list[str]:
    if not any(_has_anti_diagonal_pair(example["input"]) for example in demos):
        return ["demonstrations do not refute the main-diagonal-only shortcut"]
    return []


SEMANTIC_WITNESSES = {"anti_diagonal_pair": _has_anti_diagonal_pair}
SEMANTIC_RIVALS = {"main_diagonal_only": _main_diagonal_only}
WITNESS_RIVALS = {"anti_diagonal_pair": ["main_diagonal_only"]}
LESSON_COMPETITORS = {"main_diagonal_only": _main_diagonal_only}
CANONICAL_SHORTCUTS = {"main_diagonal_only": _main_diagonal_only}
