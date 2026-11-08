"""Input sampler for ARC task 691d467ddb4d.

Selected rule (authority remains the canonical Racket program): find every
4-connected yellow object and recolor the uniquely leftmost object green.

The sampler uses a constructive 2x2-block lattice.  Objects are separated by
at least one zero row/column, so requested distractor counts are exact and no
rejection loop can shorten a scene.  A three-profile teaching schedule places
two of every three targets away from the border and below a distractor; this
prevents the former "touches the first two columns" and "topmost object"
shortcuts from surviving a two-demonstration lesson.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "691d467ddb4d"
TASK_ID = GENERATOR_ID
RULE_HASH = "cbcf1f4c6292"
VERSION = "2.0.0"

SUMMARY = "Recolor the uniquely leftmost yellow object green."

INVARIANTS = [
    "the input contains only zero background and yellow (4) objects",
    "there are exactly one selected object and 1..3 right-side distractors",
    "all yellow objects are 4-connected and separated from one another",
    "exactly one object has the smallest minimum column",
    "the selected object stays in place and changes from yellow 4 to green 3",
]

# Every declared axis is visible in the returned pixels and every legal value is
# constructive in every difficulty band, including the 8x10 / three-distractor
# boundary case.
AXES = {
    "grid_h": {"type": "int", "default": "weighted full-domain draw; favors 8, 9, or 10", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "weighted full-domain draw; favors 10, 11, or 12", "valid": "10..18"},
    "n_right": {"type": "int", "default": "weighted full-domain draw; difficulty favors 1, 2, or 3", "valid": "1..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

EXAMPLES_NEEDED = 2
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("interior_near", "interior_far", "edge")

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_CANONICAL_PROFILES = ((8, 10), (9, 11), (10, 12))

# Connected shapes whose bounding boxes fit a 2x2 lattice block.  Every shape
# contains its block origin, making its min row/column equal to the scheduled
# block coordinate.
_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the declared branch for a draw.

    The seed and difficulty do not alter the schedule: any consecutive three
    examples contain two independent interior shortcut counterexamples.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _weighted_axis(ctx, name: str, lo: int, hi: int, anchor: int) -> int:
    """Draw across the full override domain while retaining canonical support."""
    choices = list(range(lo, hi + 1)) + [anchor] * 80
    return ctx.draw_choice(name, choices)


def _draw_dimensions(ctx) -> tuple[int, int]:
    # One keyed anchor keeps height and width correlated.  Each actual axis is
    # still drawn through GenCtx over its complete documented domain, so exact
    # overrides remain validated and recorded normally.
    anchor_h, anchor_w = ctx.draw_rng("canonical_profile_anchor").choice(_CANONICAL_PROFILES)
    return (
        _weighted_axis(ctx, "grid_h", 8, 14, anchor_h),
        _weighted_axis(ctx, "grid_w", 10, 18, anchor_w),
    )


def _draw_n_right(ctx, difficulty) -> int:
    favored = {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 2)
    return ctx.draw_choice("n_right", [1, 2, 3] + [favored] * 20)


def _component_cells(grid, color: int = 4) -> list[list[tuple[int, int]]]:
    """Return cardinal components; callers validate rectangular integer grids."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    point = r + dr, c + dc
                    if (
                        0 <= point[0] < h
                        and 0 <= point[1] < w
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            comps.append(sorted(cells))
    return comps


def _rank(comp: list[tuple[int, int]]) -> tuple[int, int]:
    return min(c for _, c in comp), min(r for r, _ in comp)


def _top_rank(comp: list[tuple[int, int]]) -> tuple[int, int]:
    return min(r for r, _ in comp), min(c for _, c in comp)


def _paint(grid: list[list[int]], cells, r0: int, c0: int) -> None:
    for dr, dc in cells:
        grid[r0 + dr][c0 + dc] = 4


def _feasible_target_indices(
    row_starts: list[int], col_starts: list[int], n_right: int
) -> list[int]:
    return [
        index
        for index in range(len(col_starts) - 1)
        if len(row_starts) * (len(col_starts) - index - 1) >= n_right
    ]


def _layout_blocks(
    *, h: int, w: int, n_right: int, profile: str, ctx
) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    """Construct target and distractor block origins without rejection."""
    row_starts = list(range(0, h - 1, 3))
    if profile == "edge":
        offset = ctx.draw_rng("edge_offset").choice((0, 1))
    else:
        offset = 2
    col_starts = list(range(offset, w - 1, 3))

    feasible = _feasible_target_indices(row_starts, col_starts, n_right)
    if not feasible:
        raise ValueError(
            f"grid {h}x{w} cannot realize {n_right} right-side distractors "
            f"for schedule profile {profile!r}"
        )

    if profile == "interior_near":
        target_col_index = min(feasible)
    elif profile == "interior_far":
        target_col_index = max(feasible)
    elif profile == "edge":
        target_col_index = min(feasible)
    else:  # fail closed if the schedule declaration and generator diverge
        raise ValueError(f"unknown schedule profile {profile!r}")

    layout_rng = ctx.draw_rng("layout")
    if profile.startswith("interior"):
        target_row_index = len(row_starts) - 1
    else:
        target_row_index = layout_rng.randrange(len(row_starts))

    target = (row_starts[target_row_index], col_starts[target_col_index])
    candidates = [
        (row, col)
        for col in col_starts[target_col_index + 1 :]
        for row in row_starts
    ]

    distractors: list[tuple[int, int]] = []
    if profile.startswith("interior"):
        # A guaranteed higher distractor independently refutes "choose topmost".
        forced = (row_starts[0], col_starts[target_col_index + 1])
        distractors.append(forced)
        candidates.remove(forced)

    remaining = n_right - len(distractors)
    if remaining:
        distractors.extend(layout_rng.sample(candidates, remaining))
    return target, distractors


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
    h, w = _draw_dimensions(ctx)
    n_right = _draw_n_right(ctx, difficulty)
    profile = schedule_profile(seed, sample_index, difficulty)
    target, distractors = _layout_blocks(
        h=h, w=w, n_right=n_right, profile=profile, ctx=ctx
    )

    grid = full_grid(h, w, 0)
    shape_rng = ctx.draw_rng("object_shapes")
    _paint(grid, shape_rng.choice(_SHAPES), *target)
    for origin in distractors:
        _paint(grid, shape_rng.choice(_SHAPES), *origin)
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the declared rule manifold and fail closed on malformed grids."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list/tuple of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a non-empty list/tuple"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]

    errors: list[str] = []
    invalid = [
        value
        for row in grid
        for value in row
        if type(value) is not int or value not in (0, 4)
    ]
    if invalid:
        sample = sorted({repr(value) for value in invalid})[:8]
        errors.append(f"input must contain only integer colors 0 and 4; found {sample}")
        return errors

    comps = _component_cells(grid, 4)
    if not 2 <= len(comps) <= 4:
        errors.append(
            f"expected one target plus 1..3 distractors, found {len(comps)} yellow objects"
        )
        return errors

    left_cols = [min(c for _, c in comp) for comp in comps]
    if left_cols.count(min(left_cols)) != 1:
        errors.append("leftmost yellow object is tied by minimum column")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return diagnostics for grids outside this sampler's lawful manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared axis from pixels rather than RNG bookkeeping."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe overrides from invalid grid: {errors[0]}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_right": len(_component_cells(grid, 4)) - 1,
    }


def _paint_selected(
    grid: list[list[int]], selected: list[tuple[int, int]] | None
) -> list[list[int]]:
    out = deepcopy(grid)
    if selected is not None:
        for r, c in selected:
            out[r][c] = 3
    return out


def _apply_intended(grid: list[list[int]]) -> list[list[int]]:
    comps = _component_cells(grid, 4)
    return _paint_selected(grid, min(comps, key=_rank) if comps else None)


def _border_touch_first_two_columns(grid: list[list[int]]) -> list[list[int]]:
    """Rival: recolor only an object whose minimum column is zero or one."""
    candidates = [comp for comp in _component_cells(grid, 4) if _rank(comp)[0] <= 1]
    return _paint_selected(grid, min(candidates, key=_rank) if candidates else None)


def _topmost_object(grid: list[list[int]]) -> list[list[int]]:
    """Rival: choose the topmost object, breaking ties to the left."""
    comps = _component_cells(grid, 4)
    return _paint_selected(grid, min(comps, key=_top_rank) if comps else None)


def _safe_witness(grid, predicate: Callable[[list[list[int]]], bool]) -> bool:
    try:
        return not self_check(grid) and bool(predicate(grid))
    except (TypeError, ValueError, IndexError, KeyError):
        return False


def _interior_leftmost(grid) -> bool:
    return _safe_witness(
        grid,
        lambda value: _rank(min(_component_cells(value, 4), key=_rank))[0] >= 2
        and _apply_intended(value) != _border_touch_first_two_columns(value),
    )


def _leftmost_not_topmost(grid) -> bool:
    return _safe_witness(
        grid,
        lambda value: min(_component_cells(value, 4), key=_rank)
        != min(_component_cells(value, 4), key=_top_rank)
        and _apply_intended(value) != _topmost_object(value),
    )


SEMANTIC_RIVALS = {
    "border_touch_first_two_columns": _border_touch_first_two_columns,
    "topmost_object": _topmost_object,
}
SEMANTIC_WITNESSES = {
    "interior_leftmost": _interior_leftmost,
    "leftmost_not_topmost": _leftmost_not_topmost,
}
WITNESS_RIVALS = {
    "interior_leftmost": ["border_touch_first_two_columns"],
    "leftmost_not_topmost": ["topmost_object"],
}
CANONICAL_SHORTCUTS = {
    "border_touch_first_two_columns": _border_touch_first_two_columns,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return [] only when the examples validate and refute every rival."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    errors: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output grids")
            continue
        input_errors = self_check(pair["input"])
        if input_errors:
            errors.append(f"pair {index} invalid input: {input_errors[0]}")
            continue
        if _apply_intended(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} output disagrees with the leftmost-object rule")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"demonstrations do not refute competitor {name!r}")
    return errors
