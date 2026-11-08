"""Contrastive input sampler for “fill the center of uniform 3x3 rings”.

The canonical Racket program remains the label authority.  This module samples
small inputs that distinguish the full eight-border test from a plausible
four-cardinal-neighbor shortcut, while retaining every canonical size/palette
profile and exact, pixel-observable overrides.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ef9eae12446"
TASK_ID = GENERATOR_ID
RULE_HASH = "ddc9a34d6cd5"
VERSION = "3.0.0"

SUMMARY = (
    "Find every 3x3 window whose eight border cells are the same nonzero "
    "color and whose center is zero; fill only that center with the border "
    "color. Generated lessons pair real rings with cornerless crosses, "
    "mixed-color borders, occupied centers, or a second true ring so the "
    "eight-cell conjunction and multiplicity are visible."
)

INVARIANTS = [
    "rectangular ARC grid with integer colors 0..9 and background 0",
    "every generated input contains one or two genuine uniform hollow 3x3 rings",
    "every generated input uses exactly two distinct nonzero colors",
    "contrastive profiles preserve rule-inert near misses instead of deleting them",
    "grid_h, grid_w, and profile overrides are exact and recoverable from pixels",
]

PROFILE_ORDER = (
    "cross_guard",
    "multi_target",
    "mixed_guard",
    "filled_guard",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor with one scheduled larger contrastive draw",
        "valid": "4..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor with one scheduled larger contrastive draw",
        "valid": "6..12",
    },
    "profile": {
        "type": "str",
        "default": "four-position contrastive schedule",
        "valid": "|".join(PROFILE_ORDER),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 6
# Three shortcut-breaking entries are intentional: every cyclic four-pair
# window contains two cornerless crosses, so after any query rotation at least
# one witness remains in the three demonstrations.  The other positions expose
# every advertised profile in ordinary generation.
SCHEDULE_PROFILES = (
    "cross_guard",
    "multi_target",
    "cross_guard",
    "filled_guard",
    "cross_guard",
    "mixed_guard",
)

_BORDER_OFFSETS = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)
_CARDINAL_OFFSETS = ((0, 1), (2, 1), (1, 0), (1, 2))
_CORNER_OFFSETS = ((0, 0), (0, 2), (2, 0), (2, 2))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the deterministic curriculum branch for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _scheduled_dimensions(sample_index: int, difficulty: Any) -> tuple[int, int]:
    """Keep canonical support dense while preventing shape-locked lessons."""
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    if difficulty == "easy":
        return {3: (5, 7), 5: (4, 7)}.get(phase, (4, 6))
    if difficulty == "medium":
        return {3: (6, 8), 5: (5, 9)}.get(phase, (5, 7))
    if difficulty == "hard":
        return {3: (8, 10), 5: (7, 9)}.get(phase, (6, 7))
    # Unbanded lesson assembly cycles through all three canonical dimensions
    # and three canonical-adjacent shapes.
    return ((4, 6), (5, 7), (6, 7), (5, 8), (4, 7), (6, 8))[phase]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    profile = overrides.get("profile")
    if profile is not None and type(profile) is not str:
        raise TypeError(f"profile must be a string, not {type(profile).__name__}")


def _draw_scheduled_int(ctx, name: str, lo: int, hi: int, planned: int, overrides: dict[str, Any]) -> int:
    options = tuple(range(lo, hi + 1)) if overrides.get(name) is not None else (planned,)
    return ctx.draw_choice(name, options)


def _paint_ring(grid: list[list[int]], row0: int, col0: int, color: int) -> None:
    for dr, dc in _BORDER_OFFSETS:
        grid[row0 + dr][col0 + dc] = color


def _paint_cross(grid: list[list[int]], row0: int, col0: int, color: int) -> None:
    for dr, dc in _CARDINAL_OFFSETS:
        grid[row0 + dr][col0 + dc] = color


def _paint_mixed_border(
    grid: list[list[int]], row0: int, col0: int, color: int, other: int
) -> None:
    _paint_ring(grid, row0, col0, color)
    # One wrong corner preserves all four matching cardinal neighbors while
    # falsifying the intended eight-cell border condition.
    grid[row0 + 2][col0 + 2] = other


def _paint_filled_center(
    grid: list[list[int]], row0: int, col0: int, color: int, other: int
) -> None:
    _paint_ring(grid, row0, col0, color)
    grid[row0 + 1][col0 + 1] = other


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

    planned_h, planned_w = _scheduled_dimensions(sample_index, difficulty)
    height = _draw_scheduled_int(ctx, "grid_h", 4, 10, planned_h, overrides)
    width = _draw_scheduled_int(ctx, "grid_w", 6, 12, planned_w, overrides)
    if overrides.get("profile") is not None:
        profile = ctx.draw_choice("profile", PROFILE_ORDER)
    else:
        profile = ctx.draw_choice(
            "profile", (schedule_profile(seed, sample_index, difficulty),)
        )

    color_a, color_b = ctx.draw_rng("palette").sample(range(1, 10), 2)
    row0 = ctx.draw_rng("motif_row").randint(0, height - 3)
    positions = [(row0, 0), (row0, width - 3)]
    if ctx.draw_rng("motif_order").choice((False, True)):
        positions.reverse()

    grid = full_grid(height, width, 0)
    target_pos, contrast_pos = positions
    _paint_ring(grid, *target_pos, color_a)

    if profile == "multi_target":
        _paint_ring(grid, *contrast_pos, color_b)
    elif profile == "cross_guard":
        _paint_cross(grid, *contrast_pos, color_b)
    elif profile == "mixed_guard":
        _paint_mixed_border(grid, *contrast_pos, color_b, color_a)
    elif profile == "filled_guard":
        _paint_filled_center(grid, *contrast_pos, color_b, color_a)
    else:  # defensive: draw_choice already constrains this
        raise RuntimeError(f"unsupported profile {profile!r}")

    return grid


def _shape_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"], 0, 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], len(grid), width
    errors: list[str] = []
    height = len(grid)
    if height < 3 or width < 3:
        errors.append(f"grid too small for a 3x3 ring: {height}x{width}")
    if height > 30 or width > 30:
        errors.append(f"grid too large: {height}x{width}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (bool is not a color)")
    return errors, height, width


def _ring_centers(grid: Any) -> dict[tuple[int, int], int]:
    errors, height, width = _shape_errors(grid)
    if errors:
        return {}
    centers: dict[tuple[int, int], int] = {}
    for row0 in range(height - 2):
        for col0 in range(width - 2):
            border = [grid[row0 + dr][col0 + dc] for dr, dc in _BORDER_OFFSETS]
            color = border[0]
            if (
                color != 0
                and grid[row0 + 1][col0 + 1] == 0
                and all(value == color for value in border)
            ):
                centers[(row0 + 1, col0 + 1)] = color
    return centers


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept lawful task inputs and reject grids on which the rule cannot fire."""
    del difficulty, meta
    errors, _, _ = _shape_errors(grid)
    if errors:
        return errors
    if not _ring_centers(grid):
        errors.append("expected at least one uniform nonzero 3x3 border with a zero center")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The task manifold is any valid ARC grid containing a genuine target ring."""
    return self_check(grid)


def _window_features(grid: Any) -> dict[str, set[tuple[int, int]] | dict[tuple[int, int], int]]:
    errors, height, width = _shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    targets = _ring_centers(grid)
    crosses: set[tuple[int, int]] = set()
    mixed: set[tuple[int, int]] = set()
    occupied: set[tuple[int, int]] = set()
    for row0 in range(height - 2):
        for col0 in range(width - 2):
            center = (row0 + 1, col0 + 1)
            center_value = grid[center[0]][center[1]]
            border = [grid[row0 + dr][col0 + dc] for dr, dc in _BORDER_OFFSETS]
            arms = [grid[row0 + dr][col0 + dc] for dr, dc in _CARDINAL_OFFSETS]
            corners = [grid[row0 + dr][col0 + dc] for dr, dc in _CORNER_OFFSETS]
            if (
                center_value == 0
                and arms[0] != 0
                and len(set(arms)) == 1
                and all(value == 0 for value in corners)
            ):
                crosses.add(center)
            if (
                center_value == 0
                and all(value != 0 for value in border)
                and len(set(border)) > 1
            ):
                mixed.add(center)
            if (
                center_value != 0
                and border[0] != 0
                and len(set(border)) == 1
                and center_value != border[0]
            ):
                occupied.add(center)
    return {
        "targets": targets,
        "crosses": crosses,
        "mixed": mixed,
        "occupied": occupied,
    }


def _classify_profile(grid: Any) -> str:
    features = _window_features(grid)
    targets = features["targets"]
    crosses = features["crosses"]
    mixed = features["mixed"]
    occupied = features["occupied"]
    if len(targets) == 2 and not crosses and not mixed and not occupied:
        return "multi_target"
    if len(targets) != 1:
        raise ValueError(f"expected one or two target rings, found {len(targets)}")
    signatures = {
        "cross_guard": bool(crosses),
        "mixed_guard": bool(mixed),
        "filled_guard": bool(occupied),
    }
    hits = [name for name, present in signatures.items() if present]
    if len(hits) != 1:
        raise ValueError(f"could not uniquely classify profile; signatures={hits}")
    return hits[0]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact advertised axis from returned pixels."""
    errors, height, width = _shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": height,
        "grid_w": width,
        "profile": _classify_profile(grid),
    }


def _orthogonal_neighbors_only(grid: Any) -> list[list[int]]:
    """RIVAL, not authority: wrongly ignores the four corners of each window."""
    errors, height, width = _shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            arms = (
                grid[row - 1][col],
                grid[row + 1][col],
                grid[row][col - 1],
                grid[row][col + 1],
            )
            if grid[row][col] == 0 and arms[0] != 0 and len(set(arms)) == 1:
                out[row][col] = arms[0]
    return out


def _has_missing_corners_cross(grid: Any) -> bool:
    try:
        return bool(_window_features(grid)["crosses"])
    except ValueError:
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "orthogonal_neighbors_only": _orthogonal_neighbors_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "missing_corners_cross": _has_missing_corners_cross,
}
WITNESS_RIVALS = {
    "missing_corners_cross": ["orthogonal_neighbors_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return surviving declared rivals that alter the held-out answer."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons


def mutation_fixtures():
    """Retain the exact validator counterexample reported against v2.0.1."""
    return [
        (
            "eight_unstructured_nonzero_cells",
            [
                [4, 4, 4, 4, 4, 4, 4],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [7, 0, 0, 0, 0, 0, 0],
            ],
        )
    ]
