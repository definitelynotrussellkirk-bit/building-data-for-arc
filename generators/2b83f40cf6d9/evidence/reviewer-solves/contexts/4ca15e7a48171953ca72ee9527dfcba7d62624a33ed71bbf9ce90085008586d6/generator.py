"""Generator for connecting same-color marker pairs with monotone staircases.

The selected Racket authority scans colors in reading order.  For each color that
appears exactly twice, it repeatedly moves one row toward the second marker and
then one column toward it, painting every visited cell in that color.

Ordinary generated inputs contain two or three colors, exactly two isolated
markers per color, and no orthogonally adjacent marker cells.  A four-position
semantic schedule alternates diagonal-only inputs with inputs containing aligned
pairs so lessons cannot teach the canonical-fitting "ignore aligned pairs"
shortcut.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2b83f40cf6d9"
TASK_ID = GENERATOR_ID
RULE_HASH = "cbbc66a297e5"
VERSION = "2.0.0"

SUMMARY = (
    "Two or three colors appear exactly twice. Connect each pair by moving one "
    "row toward the later marker, then one column, repeating to form a monotone "
    "staircase; aligned pairs become straight segments."
)

INVARIANTS = [
    "background is color 0",
    "2-3 distinct non-background colors are present",
    "each non-background color appears in exactly 2 cells",
    "marker cells are pairwise non-adjacent under 4-connectivity",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted full range", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "weighted full range", "valid": "8..20"},
    "n_colors": {"type": "int", "default": "weighted 2..3", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
_LAYOUT_SCHEDULE = ("diagonal", "one_aligned", "diagonal", "all_aligned")
_CANONICAL_PROFILES = (
    (10, 10, 3),
    (10, 12, 3),
    (11, 11, 3),
    (11, 12, 3),
    (12, 13, 3),
)
_CANONICAL_ANCHOR_PERIOD = 3
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

Cell = tuple[int, int]
Grid = list[list[int]]
Pair = tuple[Cell, Cell]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}; valid axes: {sorted(AXES)}")
    bounds = {"grid_h": (7, 18), "grid_w": (8, 20), "n_colors": (2, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _weighted_int(ctx, name: str, lo: int, hi: int, favored: tuple[int, ...]) -> int:
    """Draw over the complete override domain while weighting useful profiles."""
    options = list(range(lo, hi + 1)) + list(favored) * 6
    return ctx.draw_choice(name, options)


@lru_cache(maxsize=512)
def _candidate_pairs(height: int, width: int, aligned: bool) -> tuple[Pair, ...]:
    cells = [(row, col) for row in range(height) for col in range(width)]
    pairs: list[Pair] = []
    for index, first in enumerate(cells):
        for second in cells[index + 1 :]:
            if abs(first[0] - second[0]) + abs(first[1] - second[1]) <= 1:
                continue
            is_aligned = first[0] == second[0] or first[1] == second[1]
            if is_aligned == aligned:
                pairs.append((first, second))
    return tuple(pairs)


def _blocked_with(pair: Pair, blocked: frozenset[Cell]) -> frozenset[Cell]:
    expanded = set(blocked)
    for row, col in pair:
        expanded.add((row, col))
        expanded.update((row + dr, col + dc) for dr, dc in _CARDINALS)
    return frozenset(expanded)


def _place_pairs(height: int, width: int, modes: list[bool], rng) -> list[Pair]:
    """Choose exact aligned/diagonal pair modes with complete backtracking."""
    candidate_sets = [_candidate_pairs(height, width, aligned) for aligned in modes]
    starts = [rng.randrange(len(candidates)) for candidates in candidate_sets]

    def search(index: int, blocked: frozenset[Cell], chosen: list[Pair]) -> list[Pair] | None:
        if index == len(candidate_sets):
            return chosen
        candidates = candidate_sets[index]
        start = starts[index]
        for offset in range(len(candidates)):
            pair = candidates[(start + offset) % len(candidates)]
            if pair[0] in blocked or pair[1] in blocked:
                continue
            result = search(index + 1, _blocked_with(pair, blocked), chosen + [pair])
            if result is not None:
                return result
        return None

    result = search(0, frozenset(), [])
    if result is None:
        raise ValueError(
            f"could not place {len(modes)} isolated marker pairs in {height}x{width} grid"
        )
    return result


def _layout_modes(sample_index: int, n_colors: int, rng) -> list[bool]:
    layout = _LAYOUT_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]
    if layout == "diagonal":
        modes = [False] * n_colors
    elif layout == "all_aligned":
        modes = [True] * n_colors
    else:
        modes = [True] + [False] * (n_colors - 1)
        rng.shuffle(modes)
    return modes


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

    canonical_h = (10, 11, 12)
    canonical_w = (10, 11, 12, 13)
    if difficulty == "easy":
        height_favored = canonical_h + (7, 8, 9, 10)
        width_favored = canonical_w + (8, 9, 10, 11)
        color_favored = (2, 2, 3)
    elif difficulty == "hard":
        height_favored = canonical_h + (13, 14, 15, 16, 17, 18)
        width_favored = canonical_w + (14, 15, 16, 17, 18, 19, 20)
        color_favored = (3, 3, 2)
    else:
        height_favored = canonical_h + (9, 13, 14)
        width_favored = canonical_w + (9, 14, 15)
        color_favored = (3, 3, 2)

    # Anchor every difficulty band to the exact canonical shape/palette manifold.
    # Exact overrides always bypass this schedule and remain independently observable.
    if not overrides and sample_index % _CANONICAL_ANCHOR_PERIOD == 0:
        profile_index = (sample_index // _CANONICAL_ANCHOR_PERIOD) % len(
            _CANONICAL_PROFILES
        )
        anchor_h, anchor_w, anchor_colors = _CANONICAL_PROFILES[profile_index]
        height = ctx.draw_choice("grid_h", [anchor_h])
        width = ctx.draw_choice("grid_w", [anchor_w])
        n_colors = ctx.draw_choice("n_colors", [anchor_colors])
    else:
        height = _weighted_int(ctx, "grid_h", 7, 18, height_favored)
        width = _weighted_int(ctx, "grid_w", 8, 20, width_favored)
        n_colors = _weighted_int(ctx, "n_colors", 2, 3, color_favored)

    layout_rng = ctx.draw_rng("layout")
    modes = _layout_modes(sample_index, n_colors, layout_rng)
    pairs = _place_pairs(height, width, modes, layout_rng)
    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude=(0,))

    grid = full_grid(height, width, 0)
    for color, pair in zip(palette, pairs):
        for row, col in pair:
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    expected = {"grid_h": height, "grid_w": width, "n_colors": n_colors}
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"observable-axis mismatch: expected {expected}, observed {observed}")
    return grid


def _shape_errors(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["expected nonempty grid rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    return len(grid), width, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete ordinary input domain without raising."""
    del difficulty, meta
    height, width, errors = _shape_errors(grid)
    if errors:
        return errors
    if not 7 <= height <= 18:
        errors.append(f"height {height} outside supported range 7..18")
    if not 8 <= width <= 20:
        errors.append(f"width {width} outside supported range 8..20")

    bad_cells = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append("cells must be integer ARC colors 0..9 (booleans are not colors)")
        return errors

    counts = Counter(value for row in grid for value in row if value != 0)
    if not 2 <= len(counts) <= 3:
        errors.append(f"expected 2..3 non-background colors, found {len(counts)}")
    for color, count in sorted(counts.items()):
        if count != 2:
            errors.append(f"color {color} has {count} cells (expected exactly 2)")

    occupied = {(row, col) for row, line in enumerate(grid) for col, value in enumerate(line) if value}
    for row, col in sorted(occupied):
        for dr, dc in ((1, 0), (0, 1)):
            if (row + dr, col + dc) in occupied:
                errors.append(
                    f"marker cells {(row, col)} and {(row + dr, col + dc)} are 4-adjacent"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe axes on invalid grid: {errors}")
    counts = Counter(value for row in grid for value in row if value)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_colors": len(counts)}


def _colors_in_reading_order(grid: Grid) -> list[int]:
    colors: list[int] = []
    for row in grid:
        for value in row:
            if value and value not in colors:
                colors.append(value)
    return colors


def _positions(grid: Grid, color: int) -> list[Cell]:
    return [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == color
    ]


def _staircase(first: Cell, second: Cell) -> list[Cell]:
    row, col = first
    target_row, target_col = second
    cells = [(row, col)]
    while (row, col) != (target_row, target_col):
        if row != target_row:
            row += 1 if target_row > row else -1
            cells.append((row, col))
        if col != target_col:
            col += 1 if target_col > col else -1
            cells.append((row, col))
    return cells


def _render(grid: Grid, *, skip_aligned: bool = False) -> Grid:
    out = [list(row) for row in grid]
    for color in _colors_in_reading_order(grid):
        points = _positions(grid, color)
        if len(points) != 2:
            continue
        aligned = points[0][0] == points[1][0] or points[0][1] == points[1][1]
        if skip_aligned and aligned:
            continue
        for row, col in _staircase(points[0], points[1]):
            out[row][col] = color
    return out


def _intended_output(grid: Grid) -> Grid:
    """Independent Python mirror used only for tests and semantic contracts."""
    return _render(grid)


def _diagonal_pairs_only(grid: Grid) -> Grid:
    """Plausible rival: connect only pairs separated on both axes."""
    return _render(grid, skip_aligned=True)


def _has_aligned_pair(grid: Grid) -> bool:
    if self_check(grid):
        return False
    return any(
        points[0][0] == points[1][0] or points[0][1] == points[1][1]
        for color in _colors_in_reading_order(grid)
        if len(points := _positions(grid, color)) == 2
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "diagonal_pairs_only": _diagonal_pairs_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "aligned_pair": _has_aligned_pair,
}
WITNESS_RIVALS = {"aligned_pair": ["diagonal_pairs_only"]}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute the aligned-pair omission shortcut."""
    issues: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        issues.append("query must contain an input grid")
    elif self_check(query["input"]):
        issues.append("query input is outside the lawful task domain")

    rival_refuted = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            issues.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        errors = self_check(grid)
        if errors:
            issues.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = _intended_output(grid)
        if demo["output"] != expected:
            issues.append(f"demo {index} output does not match the staircase rule")
            continue
        rival_refuted = rival_refuted or _diagonal_pairs_only(grid) != expected
    if not rival_refuted:
        issues.append("demonstrations do not refute rival diagonal_pairs_only")
    return issues
