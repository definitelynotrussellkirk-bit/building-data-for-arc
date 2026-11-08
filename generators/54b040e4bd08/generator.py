"""Input generator for ARC task 54b040e4bd08: repair a periodic hole.

A grid is filled by a small two-dimensional tile.  One solid interior
rectangle is erased to color 0.  The selected Racket authority infers the
smallest complete row/column period from every visible nonzero cell and fills
only the erased cells.

The four-slot default curriculum is deliberately adversarial.  Two slots leave
insufficient evidence for a row-at-a-time repair, two leave insufficient
evidence for a column-at-a-time repair, and every slot lets the hole overlap
the top-left period block.  Thus demonstrations distinguish genuine global
2-D periodic reconstruction from three tempting shortcuts that fit every
canonical example.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "54b040e4bd08"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "55b239af8777"

SUMMARY = (
    "Fill a 6..10 by 9..12 grid with a distinct-color 2x2, 2x3, or 3x2 "
    "periodic tile, erase one solid interior row- or column-band, then recover "
    "the smallest global two-dimensional period and restore every zero cell."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the intact cells agree with the smallest complete 2x2, 2x3, or 3x2 tile",
    "every tile residue has a distinct nonzero ARC color",
    "all zeros form exactly one nonempty solid rectangle strictly inside the grid",
    "the output changes only zero cells and restores the global periodic pattern",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "scheduled", "valid": "9..12"},
    "tile_shape": {
        "type": "str",
        "default": "scheduled",
        "valid": "2x2|2x3|3x2",
    },
    "vertical_margin": {
        "type": "int",
        "default": "scheduled",
        "valid": "1..2",
    },
    "horizontal_margin": {
        "type": "int",
        "default": "scheduled",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_TILE_SHAPES = {
    "2x2": (2, 2),
    "2x3": (2, 3),
    "3x2": (3, 2),
}

# Each profile is a real counterexample to the top-left-block shortcut.  The
# row_* profiles additionally defeat row-only repair; column_* defeat
# column-only repair.  Profiles b also exercise the public margin value 2.
PROFILE_SPECS: dict[str, dict[str, Any]] = {
    "row_gap_a": {
        "grid_h": 6,
        "grid_w": 12,
        "tile_shape": "2x3",
        "vertical_margin": 1,
        "horizontal_margin": 1,
    },
    "column_gap_a": {
        "grid_h": 9,
        "grid_w": 10,
        "tile_shape": "3x2",
        "vertical_margin": 1,
        "horizontal_margin": 1,
    },
    "row_gap_b": {
        "grid_h": 8,
        "grid_w": 11,
        "tile_shape": "2x3",
        "vertical_margin": 1,
        "horizontal_margin": 2,
    },
    "column_gap_b": {
        "grid_h": 8,
        "grid_w": 12,
        "tile_shape": "3x2",
        "vertical_margin": 2,
        "horizontal_margin": 1,
    },
}
SCHEDULE_PROFILES = (
    "row_gap_a",
    "column_gap_a",
    "row_gap_b",
    "column_gap_b",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the exact four-slot teaching schedule profile.

    The profile depends only on the sample index, so every consecutive block of
    four samples contains both row and column counterexamples in every band.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))

    int_domains = {
        "grid_h": (6, 10),
        "grid_w": (9, 12),
        "vertical_margin": (1, 2),
        "horizontal_margin": (1, 2),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "tile_shape":
            if type(value) is not str or value not in _TILE_SHAPES:
                raise ValueError(
                    "tile_shape must be one of " + ", ".join(_TILE_SHAPES)
                )
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = int_domains[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axes(seed: int, sample_index: int, difficulty: str | None, overrides: dict[str, Any]):
    profile = schedule_profile(seed, sample_index, difficulty)
    effective = {
        **PROFILE_SPECS[profile],
        **{name: value for name, value in overrides.items() if value is not None},
    }
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    values = {
        "grid_h": ctx.draw_int_strict("grid_h", 6, 10),
        "grid_w": ctx.draw_int_strict("grid_w", 9, 12),
        "tile_shape": ctx.draw_choice("tile_shape", tuple(_TILE_SHAPES)),
        "vertical_margin": ctx.draw_int_strict("vertical_margin", 1, 2),
        "horizontal_margin": ctx.draw_int_strict("horizontal_margin", 1, 2),
    }
    return ctx, values


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    """Generate one lawful periodic grid with a single interior zero hole."""
    _validate_overrides(overrides)
    ctx, axes = _draw_axes(seed, sample_index, difficulty, overrides)
    height = axes["grid_h"]
    width = axes["grid_w"]
    tile_h, tile_w = _TILE_SHAPES[axes["tile_shape"]]
    vertical_margin = axes["vertical_margin"]
    horizontal_margin = axes["horizontal_margin"]

    # All advertised combinations are constructive.  Keep this explicit so a
    # future domain extension fails loudly instead of silently clipping a hole.
    if height - 2 * vertical_margin < 1 or width - 2 * horizontal_margin < 1:
        raise ValueError("margins leave no nonempty interior hole")

    raw_colors = ctx.draw_distinct_colors(
        "tile_colors", n=tile_h * tile_w, exclude={0}
    )
    # GenCtx's keyed RNG intentionally excludes difficulty.  Rotate the nonzero
    # palette by a fixed-point-free amount so easy/medium/hard are observably
    # different without changing geometry, period, or override semantics.
    palette_shift = {"easy": 0, "medium": 3, "hard": 6}.get(difficulty, 0)
    colors = tuple(((color - 1 + palette_shift) % 9) + 1 for color in raw_colors)
    tile = [
        list(colors[row * tile_w : (row + 1) * tile_w])
        for row in range(tile_h)
    ]
    grid = full_grid(height, width, 0)
    for row in range(height):
        for column in range(width):
            grid[row][column] = tile[row % tile_h][column % tile_w]

    # A thin adversarial band keeps 0 non-modal (matching canonical visual
    # statistics) while withholding exactly the evidence a one-dimensional
    # shortcut needs.  Wide tiles lose a row band; tall tiles lose a column
    # band.  The public margins are the observable top/left offsets.
    if tile_w >= tile_h:
        row = vertical_margin
        for column in range(horizontal_margin, width - 1):
            grid[row][column] = 0
    else:
        column = horizontal_margin
        for row in range(vertical_margin, height - 1):
            grid[row][column] = 0
    return grid


def _normalise_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return None, ["every row must be a nonempty sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid is ragged"]

    normalised: list[list[int]] = []
    for row_index, row in enumerate(grid):
        clean_row: list[int] = []
        for column_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{column_index}) must be an integer ARC color 0..9"
                )
            else:
                clean_row.append(value)
        if len(clean_row) == width:
            normalised.append(clean_row)
    if errors:
        return None, errors
    return normalised, []


def _zero_bounds(grid: list[list[int]]) -> tuple[int, int, int, int] | None:
    zeros = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 0
    ]
    if not zeros:
        return None
    rows = [point[0] for point in zeros]
    columns = [point[1] for point in zeros]
    return min(rows), min(columns), max(rows), max(columns)


def _infer_tile(grid: list[list[int]]) -> tuple[int, int, list[list[int]]]:
    """Infer exactly as the Racket authority: first complete candidate 1..5."""
    height, width = len(grid), len(grid[0])
    for period_r in range(1, min(5, height) + 1):
        for period_c in range(1, min(5, width) + 1):
            buckets = [
                [set() for _ in range(period_c)]
                for _ in range(period_r)
            ]
            for row, values in enumerate(grid):
                for column, value in enumerate(values):
                    if value != 0:
                        buckets[row % period_r][column % period_c].add(value)
            if all(len(bucket) == 1 for line in buckets for bucket in line):
                tile = [
                    [next(iter(bucket)) for bucket in line]
                    for line in buckets
                ]
                return period_r, period_c, tile
    raise ValueError("no complete periodic tile is inferable")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return diagnostics unless ``grid`` is a lawful task instance."""
    del difficulty, meta
    clean, errors = _normalise_grid(grid)
    if errors or clean is None:
        return errors
    height, width = len(clean), len(clean[0])
    if not 6 <= height <= 10:
        errors.append(f"grid height {height} outside 6..10")
    if not 9 <= width <= 12:
        errors.append(f"grid width {width} outside 9..12")

    bounds = _zero_bounds(clean)
    if bounds is None:
        errors.append("grid has no zero hole")
        return errors
    top, left, bottom, right = bounds
    if top == 0 or left == 0 or bottom == height - 1 or right == width - 1:
        errors.append("zero rectangle must be strictly interior")
    for row in range(height):
        for column in range(width):
            inside = top <= row <= bottom and left <= column <= right
            if (clean[row][column] == 0) != inside:
                errors.append("zeros do not form one solid rectangle")
                # A single diagnostic is enough and keeps mutation reports small.
                row = height
                break
        if errors and errors[-1] == "zeros do not form one solid rectangle":
            break

    try:
        period_r, period_c, tile = _infer_tile(clean)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if (period_r, period_c) not in set(_TILE_SHAPES.values()):
        errors.append(
            f"smallest complete period {period_r}x{period_c} is not an allowed tile shape"
        )
    flat_tile = [value for row in tile for value in row]
    if 0 in flat_tile:
        errors.append("inferred tile contains background")
    if len(set(flat_tile)) != len(flat_tile):
        errors.append("tile residues must use distinct colors")
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None):
    """Semantic-gate hook: this generator samples only the strict manifold."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every public control from returned pixels."""
    clean, errors = _normalise_grid(grid)
    if errors or clean is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    top_left = _zero_bounds(clean)
    if top_left is None:
        raise ValueError("grid has no zero hole")
    top, left, _bottom, _right = top_left
    period_r, period_c, _tile = _infer_tile(clean)
    return {
        "grid_h": len(clean),
        "grid_w": len(clean[0]),
        "tile_shape": f"{period_r}x{period_c}",
        "vertical_margin": top,
        "horizontal_margin": left,
    }


def _periodic_fill(grid: list[list[int]]) -> list[list[int]]:
    period_r, period_c, tile = _infer_tile(grid)
    return [
        [
            value if value != 0 else tile[row % period_r][column % period_c]
            for column, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


def _line_period(values: Iterable[tuple[int, int]]) -> tuple[int, dict[int, int]] | None:
    visible = list(values)
    for period in range(1, 6):
        buckets: dict[int, set[int]] = {residue: set() for residue in range(period)}
        for position, value in visible:
            if value != 0:
                buckets[position % period].add(value)
        if all(len(bucket) == 1 for bucket in buckets.values()):
            return period, {
                residue: next(iter(bucket))
                for residue, bucket in buckets.items()
            }
    return None


def _row_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: infer and repair each row independently."""
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        inferred = _line_period(enumerate(values))
        if inferred is None:
            continue
        period, residues = inferred
        for column, value in enumerate(values):
            if value == 0:
                output[row][column] = residues[column % period]
    return output


def _column_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: infer and repair each column independently."""
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for column in range(width):
        inferred = _line_period((row, grid[row][column]) for row in range(height))
        if inferred is None:
            continue
        period, residues = inferred
        for row in range(height):
            if grid[row][column] == 0:
                output[row][column] = residues[row % period]
    return output


def _top_left_tile(grid: list[list[int]]) -> list[list[int]]:
    """Strongest canonical-fitting shortcut: read only the top-left block."""
    period_r, period_c, _ = _infer_tile(grid)
    tile = [list(row[:period_c]) for row in grid[:period_r]]
    return [
        [
            value if value != 0 else tile[row % period_r][column % period_c]
            for column, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "row_only": _row_only,
    "column_only": _column_only,
    "top_left_tile": _top_left_tile,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "row_only_counterexample": lambda grid: _row_only(grid) != _periodic_fill(grid),
    "column_only_counterexample": lambda grid: _column_only(grid) != _periodic_fill(grid),
    "top_left_tile_counterexample": lambda grid: _top_left_tile(grid) != _periodic_fill(grid),
}
WITNESS_RIVALS = {
    "row_only_counterexample": ["row_only"],
    "column_only_counterexample": ["column_only"],
    "top_left_tile_counterexample": ["top_left_tile"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require visible demonstrations to refute every declared rival."""
    del query
    survivors = [
        name
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
    if survivors:
        return [
            "declared competitors fit every demonstration: "
            + ", ".join(sorted(survivors))
        ]
    return []
