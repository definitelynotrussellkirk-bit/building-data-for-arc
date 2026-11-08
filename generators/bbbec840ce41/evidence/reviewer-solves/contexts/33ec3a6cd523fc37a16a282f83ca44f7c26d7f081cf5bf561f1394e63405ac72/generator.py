"""Constructive generator for anti-diagonal reflection with copy semantics.

For each non-background cell ``(r, c)`` in an ``n x n`` input, the authority
preserves the original cell and paints the same color at
``(n - 1 - c, n - 1 - r)``.  Inputs are deliberately confined to the
anti-diagonal and the strict region above it, so the added copies are visible
and cannot overwrite another source cell.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bbbec840ce41"
TASK_ID = "bbbec840ce41"
VERSION = "2.0.0"
RULE_HASH = "655e255b5949"
EXAMPLES_NEEDED = 4
SUMMARY = (
    "Preserve colored source cells and copy each color across the anti-diagonal "
    "(r,c) -> (n-1-c,n-1-r)."
)
INVARIANTS = [
    "Square integer grid with colors 0..9 and background 0.",
    "Every source lies on or strictly above the anti-diagonal.",
    "At least one uniquely colored off-axis source makes the reflection, axis, and color observable.",
]

# All four controls are exactly recoverable from the returned pixels.
AXES = {
    "grid_n": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-weighted 6..16 draws",
        "valid": "6..16",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled anchors plus difficulty-weighted 4..12 draws",
        "valid": "4..12",
    },
    "n_colors": {
        "type": "int",
        "default": "2..min(7,n_cells)",
        "valid": "2..7",
    },
    "n_axis": {
        "type": "int",
        "default": "0..min(3,n_cells-1)",
        "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("n_cells", "n_colors"),
    ("n_cells", "n_axis"),
]
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Residues 0,4,8,12,16 in each 20-draw block pin all five canonical
# (height, width, palette-size) profiles.  Other residues retain broad random
# geometry and counts.  The schedule is the same in every difficulty band.
_ANCHOR_SPECS = (
    (8, 6, 4, 1),   # profile (8, 8, 5), including background
    (8, 6, 5, 1),   # profile (8, 8, 6)
    (9, 7, 6, 1),   # profile (9, 9, 7)
    (9, 7, 7, 1),   # profile (9, 9, 8)
    (10, 7, 6, 1),  # profile (10, 10, 7)
)
SCHEDULE_PROFILES = (
    "canonical_8x6x4",
    "canonical_8x6x5",
    "canonical_9x7x6",
    "canonical_9x7x7",
    "canonical_10x7x6",
    "broad",
)


class IncompatibleOverrides(ValueError):
    """A reproducible joint-control failure with machine-readable axes."""

    def __init__(self, message: str, axes: tuple[str, str]):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the declared curriculum profile for this sample index."""
    residue = sample_index % 20
    if residue % 4 == 0:
        anchor_index = residue // 4
        return SCHEDULE_PROFILES[anchor_index]
    return "broad"


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        supported = ", ".join(sorted(AXES))
        raise ValueError(
            f"unknown override(s): {', '.join(sorted(unknown))}; supported: {supported}"
        )
    bounds = (
        ("grid_n", 6, 16),
        ("n_cells", 4, 12),
        ("n_colors", 2, 7),
        ("n_axis", 0, 3),
    )
    # Type-check first, then report impossible jointly pinned counts before the
    # ordinary scalar range error.  This keeps the rejection machine-readable
    # even when a bad pair also puts one member just outside its scalar domain.
    for name, lo, hi in bounds:
        if name in overrides and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer in {lo}..{hi} (not bool)")
    if "n_cells" in overrides and "n_colors" in overrides:
        if overrides["n_colors"] > overrides["n_cells"]:
            raise IncompatibleOverrides(
                "n_colors cannot exceed n_cells",
                ("n_cells", "n_colors"),
            )
    if "n_cells" in overrides and "n_axis" in overrides:
        if overrides["n_axis"] >= overrides["n_cells"]:
            raise IncompatibleOverrides(
                "n_axis must leave at least one strict off-axis source cell",
                ("n_cells", "n_axis"),
            )
    for name, lo, hi in bounds:
        if name in overrides and not lo <= overrides[name] <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _default_counts(ctx, sample_index: int, difficulty) -> dict[str, int]:
    """Build one feasible default tuple before exact strict draws consume it."""
    residue = sample_index % 20
    if residue % 4 == 0:
        n, n_cells, n_colors, n_axis = _ANCHOR_SPECS[residue // 4]
    else:
        rng = ctx.draw_rng("default_tuple")
        if difficulty == "easy":
            n = rng.randint(6, 9)
            n_cells = rng.randint(4, 7)
        elif difficulty == "hard":
            n = rng.randint(10, 16)
            n_cells = rng.randint(8, 12)
        else:
            n = rng.randint(8, 12)
            n_cells = rng.randint(6, 10)
        n_colors = rng.randint(2, min(7, n_cells))
        n_axis = rng.randint(0, min(3, n_cells - 1))

    # A pinned dependent control should not fail merely because an unrelated
    # free default happened to be too small.  Only jointly pinned impossible
    # values are rejected by _validate_overrides / the post-draw guard.
    explicit = ctx.overrides
    if "n_cells" in explicit:
        n_cells = explicit["n_cells"]
        if "n_colors" not in explicit:
            n_colors = min(n_colors, n_cells)
        if "n_axis" not in explicit:
            n_axis = min(n_axis, n_cells - 1)
    if "n_colors" in explicit:
        n_colors = explicit["n_colors"]
        if "n_cells" not in explicit:
            n_cells = max(n_cells, n_colors)
    if "n_axis" in explicit:
        n_axis = explicit["n_axis"]
        if "n_cells" not in explicit:
            n_cells = max(n_cells, n_axis + 1)
    if "grid_n" in explicit:
        n = explicit["grid_n"]

    return {
        "grid_n": n,
        "n_cells": n_cells,
        "n_colors": n_colors,
        "n_axis": n_axis,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic, nonidentity input with exact controls."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    defaults = _default_counts(ctx, sample_index, difficulty)
    for name, value in defaults.items():
        ctx.overrides.setdefault(name, value)

    n = ctx.draw_int_strict("grid_n", 6, 16)
    n_cells = ctx.draw_int_strict("n_cells", 4, 12)
    n_colors = ctx.draw_int_strict("n_colors", 2, 7)
    n_axis = ctx.draw_int_strict("n_axis", 0, 3)

    if n_colors > n_cells:
        raise IncompatibleOverrides(
            "n_colors cannot exceed n_cells",
            ("n_cells", "n_colors"),
        )
    if n_axis >= n_cells:
        raise IncompatibleOverrides(
            "n_axis must leave at least one strict off-axis source cell",
            ("n_cells", "n_axis"),
        )

    strict = [(r, c) for r in range(n) for c in range(n) if r + c < n - 1]
    witness_pool = [(r, c) for r, c in strict if r != c]
    axis = [(r, n - 1 - r) for r in range(n)]

    position_rng = ctx.draw_rng("positions")
    witness = position_rng.choice(witness_pool)
    axis_positions = position_rng.sample(axis, n_axis)
    remaining_strict = [position for position in strict if position != witness]
    strict_positions = position_rng.sample(
        remaining_strict,
        n_cells - n_axis - 1,
    )

    color_rng = ctx.draw_rng("colors")
    witness_color = color_rng.choice([value for value in range(1, 10) if value != 8])
    other_colors = color_rng.sample(
        [value for value in range(1, 10) if value != witness_color],
        n_colors - 1,
    )
    other_positions = [*axis_positions, *strict_positions]
    color_rng.shuffle(other_positions)
    assignments = list(other_colors)
    assignments.extend(
        color_rng.choice(other_colors)
        for _ in range(len(other_positions) - len(other_colors))
    )
    color_rng.shuffle(assignments)

    grid = full_grid(n, n, 0)
    grid[witness[0]][witness[1]] = witness_color
    for (r, c), value in zip(other_positions, assignments):
        grid[r][c] = value
    return grid


def _shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty square grid"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty lists or tuples"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if len(grid) != width:
        return [f"expected square grid, got {len(grid)}x{width}"]
    if not 1 <= len(grid) <= 30:
        return ["grid size must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cell values must be integers in 0..9 (not bool)"]
    return []


def _unique_coordinate_anchors(grid) -> list[tuple[int, int, int]]:
    n = len(grid)
    counts = Counter(value for row in grid for value in row if value)
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
        and counts[value] == 1
        and r + c < n - 1
        and r != c
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Safely validate the broad, lesson-bearing source-grid grammar."""
    errors = _shape_errors(grid)
    if errors:
        return errors
    n = len(grid)
    nonzero = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if len(nonzero) < 4:
        errors.append("need at least four source cells")
    colors = {value for _, _, value in nonzero}
    if len(colors) < 2:
        errors.append("need at least two source colors")
    if any(r + c > n - 1 for r, c, _ in nonzero):
        errors.append("source cells must lie on or above the anti-diagonal")
    if not any(r + c < n - 1 for r, c, _ in nonzero):
        errors.append("need a strict off-axis source so the output changes")
    if not _unique_coordinate_anchors(grid):
        errors.append("need a uniquely colored off-axis coordinate anchor")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the structural and profile envelope of the five authorities."""
    errors = self_check(grid)
    if errors:
        return errors
    n = len(grid)
    n_cells = sum(value != 0 for row in grid for value in row)
    n_colors = len({value for row in grid for value in row if value})
    if not 8 <= n <= 10:
        errors.append("canonical grid size is 8..10")
    if not 6 <= n_cells <= 8:
        errors.append("canonical source count is 6..8")
    if not 4 <= n_colors <= 7:
        errors.append("canonical non-background palette size is 4..7")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared control exactly from pixels."""
    n = len(grid)
    nonzero = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return {
        "grid_n": n,
        "n_cells": len(nonzero),
        "n_colors": len({value for _, _, value in nonzero}),
        "n_axis": sum(r + c == n - 1 for r, c, _ in nonzero),
    }


def rule_output(grid):
    """Local semantic oracle used only by review hooks, never for labels."""
    n = len(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[n - 1 - c][n - 1 - r] = value
    return out


def rival_identity(grid):
    return [list(row) for row in grid]


def rival_main_diagonal(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[c][r] = value
    return out


def rival_half_turn(grid):
    n = len(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[n - 1 - r][n - 1 - c] = value
    return out


def rival_move_instead_of_copy(grid):
    n = len(grid)
    out = full_grid(n, n, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[n - 1 - c][n - 1 - r] = value
    return out


def rival_fixed_mirror_color(grid):
    n = len(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[n - 1 - c][n - 1 - r] = 8
    return out


def _has_coordinate_anchor(grid) -> bool:
    return bool(_unique_coordinate_anchors(grid))


def _has_off_axis_copy(grid) -> bool:
    n = len(grid)
    return any(value and r + c < n - 1 for r, row in enumerate(grid) for c, value in enumerate(row))


def _has_non8_colored_copy(grid) -> bool:
    return any(value != 8 for _, _, value in _unique_coordinate_anchors(grid))


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": rival_identity,
    "main_diagonal": rival_main_diagonal,
    "half_turn": rival_half_turn,
    "move_instead_of_copy": rival_move_instead_of_copy,
    "fixed_mirror_color": rival_fixed_mirror_color,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable] = {
    "coordinate_anchor": _has_coordinate_anchor,
    "off_axis_copy": _has_off_axis_copy,
    "colored_copy": _has_non8_colored_copy,
}
WITNESS_RIVALS = {
    "coordinate_anchor": ["main_diagonal", "half_turn"],
    "off_axis_copy": ["identity", "move_instead_of_copy"],
    "colored_copy": ["fixed_mirror_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared plausible shortcut survives all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        expected = rule_output(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the pinned rule")
    expected_query = rule_output(query["input"])
    if query.get("output") is not None and query["output"] != expected_query:
        reasons.append("query output disagrees with the pinned rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != expected_query:
            reasons.append(f"competitor '{name}' fits every demo but changes the query answer")
    return reasons


def mutation_fixtures():
    """Deterministic impostors for self-check mutation-sensitivity probes."""
    blank = full_grid(8, 8, 0)

    all_axis = full_grid(8, 8, 0)
    for r, value in enumerate((1, 2, 3, 4)):
        all_axis[r][7 - r] = value

    lower_triangle = full_grid(8, 8, 0)
    for r, c, value in ((0, 0, 1), (0, 1, 2), (1, 0, 3), (7, 7, 4)):
        lower_triangle[r][c] = value

    one_color = full_grid(8, 8, 0)
    for r, c in ((0, 0), (0, 2), (1, 0), (2, 1)):
        one_color[r][c] = 5

    no_unique_anchor = full_grid(8, 8, 0)
    for r, c, value in ((0, 0, 1), (0, 2, 1), (1, 0, 2), (2, 1, 2)):
        no_unique_anchor[r][c] = value

    return [
        ("blank", blank),
        ("all_on_anti_diagonal", all_axis),
        ("lower_triangle_source", lower_triangle),
        ("one_color_only", one_color),
        ("no_unique_coordinate_anchor", no_unique_anchor),
    ]
