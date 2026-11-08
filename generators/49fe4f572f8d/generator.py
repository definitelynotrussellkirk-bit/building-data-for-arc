"""Reviewed generator for ARC task 49fe4f572f8d — column gravity down.

The selected rule is ``(rule! (gravity g "down"))``.  Each column is
compressed independently against the bottom edge while preserving the
foreground cells' top-to-bottom order.

The ordinary curriculum alternates exact linked canonical profiles with
counterexamples to plausible semantic and scope-restricted rivals.  Every
five-example sliding window now contains floor-supported, deep-stack,
repeated-color, and beyond-canonical-scope evidence, so the declared lesson
size is executable rather than an aggregate-only claim.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "49fe4f572f8d"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "c3638032481f"

SUMMARY = (
    "Generate sparse 6..10 by 7..10 grids containing 5..10 colored cells in "
    "2..4 columns.  Downward gravity packs each column against the bottom "
    "while preserving its top-to-bottom color order.  Half of the ordinary "
    "curriculum follows exact canonical shape/palette/count profiles; the "
    "other half supplies deep, repeated-color, floor-supported, and joint "
    "scope-boundary examples. Every five-demo window refutes the declared "
    "semantic and canonical-fitting competitors."
)

INVARIANTS = [
    "grid dimensions are 6..10 rows by 7..10 columns",
    "there are exactly 5..10 nonzero cells in exactly 2..4 occupied columns",
    "the foreground uses 2..7 distinct nonzero ARC colors",
    "at least one multicolor column makes within-column order observable",
    "at least one foreground cell moves under downward gravity",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile or full-support difficulty-biased draw",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile or full-support difficulty-biased draw",
        "valid": "7..10",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled canonical count or full-support scene-aware draw",
        "valid": "5..10",
    },
    "n_occupied_columns": {
        "type": "int",
        "default": "scheduled canonical count or full-support scene-aware draw",
        "valid": "2..4",
    },
}

# Every public-axis combination is constructively feasible.  Even the tightest
# case (height 6, ten cells, two columns) fits as two five-cell moving stacks.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# (height, width, total palette including background, cells, occupied columns)
_CANONICAL_PROFILES = (
    (7, 8, 7, 6, 3),
    (8, 7, 6, 5, 2),
    (6, 9, 7, 6, 3),
    (9, 8, 7, 6, 3),
    (8, 9, 8, 7, 3),
)
_CANONICAL_PROFILE_SET = frozenset(_CANONICAL_PROFILES)
_CANONICAL_SHAPES = frozenset((profile[0], profile[1]) for profile in _CANONICAL_PROFILES)

# Five canonical slots alternate with five anti-shortcut slots.  Boundary
# slots 1, 5, and 9 are at most four positions apart cyclically, so every
# EXAMPLES_NEEDED=5 sliding window includes one joint counterexample to the
# canonical-only scope restrictions.  Supported and deep scenes are likewise
# spaced so every five-demo window refutes their corresponding rivals.
SCHEDULE_PROFILES = tuple(range(10))
_BOUNDARY_SLOTS = frozenset({1, 5, 9})
_BOUNDARY_AXES = {
    "grid_h": 10,
    "grid_w": 10,
    "n_cells": 10,
    "n_occupied_columns": 4,
    "foreground_palette_size": 2,
}
_NONCANONICAL_SCENES = {
    1: "supported",
    3: "deep",
    5: "mixed",
    7: "mixed",
    9: "mixed",
}
MIN_STRICT_FRAC = 0.40
EXAMPLES_NEEDED = 5


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic ten-slot teaching curriculum position."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    height = len(grid)
    if not 6 <= height <= 10:
        return [f"grid height must be in 6..10, found {height}"]
    if not 7 <= width <= 10:
        return [f"grid width must be in 7..10, found {width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers in 0..9"]
    return []


def _gravity_down(grid) -> list[list[int]]:
    """Small Python mirror used only by validation and semantic witnesses."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        start = height - len(values)
        for offset, value in enumerate(values):
            out[start + offset][column] = value
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and lawful-looking inputs that hide the rule."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    foreground = [
        (row, column, grid[row][column])
        for row in range(height)
        for column in range(width)
        if grid[row][column] != 0
    ]
    if not 5 <= len(foreground) <= 10:
        errors.append(f"foreground cell count must be in 5..10, found {len(foreground)}")

    occupied_columns = sorted({column for _row, column, _value in foreground})
    if not 2 <= len(occupied_columns) <= 4:
        errors.append(
            "occupied-column count must be in 2..4, "
            f"found {len(occupied_columns)}"
        )

    colors = {value for _row, _column, value in foreground}
    if not 2 <= len(colors) <= 7:
        errors.append(f"foreground palette size must be in 2..7, found {len(colors)}")

    has_order_witness = any(
        len(values := [
            grid[row][column]
            for row in range(height)
            if grid[row][column] != 0
        ]) >= 2
        and len(set(values)) >= 2
        for column in occupied_columns
    )
    if not has_order_witness:
        errors.append("at least one occupied column must contain two distinct colors")

    if not errors and _gravity_down(grid) == [list(row) for row in grid]:
        errors.append("input must contain at least one downward gravity movement")
    return errors


def _profile(grid) -> tuple[int, int, int, int, int]:
    foreground = [value for row in grid for value in row if value != 0]
    occupied_columns = sum(
        any(grid[row][column] != 0 for row in range(len(grid)))
        for column in range(len(grid[0]))
    )
    return (
        len(grid),
        len(grid[0]),
        len(set(foreground)) + 1,
        len(foreground),
        occupied_columns,
    )


def strict_canonical_like(grid) -> list[str]:
    """Require one of the five linked official empirical input profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = _profile(grid)
    if profile not in _CANONICAL_PROFILE_SET:
        return [
            "canonical linked profiles are "
            f"{sorted(_CANONICAL_PROFILE_SET)}, found {profile}"
        ]
    return []


def observe_overrides(grid) -> dict[str, int | None]:
    """Recover every public exact axis directly from a returned grid."""
    if _grid_errors(grid):
        return {axis: None for axis in AXES}
    foreground = [value for row in grid for value in row if value != 0]
    occupied_columns = sum(
        any(grid[row][column] != 0 for row in range(len(grid)))
        for column in range(len(grid[0]))
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": len(foreground),
        "n_occupied_columns": occupied_columns,
    }


def _validate_call(difficulty: Any, overrides: dict[str, object]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for axis, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{axis} override must be an integer, found {value!r}")


def _draw_axis(
    ctx,
    overrides: dict[str, object],
    label: str,
    domain: tuple[int, ...],
    *,
    scheduled: int | None,
    weighted: tuple[int, ...],
) -> int:
    if label in overrides and overrides[label] is not None:
        options = domain
    elif scheduled is not None:
        options = (scheduled,)
    else:
        options = domain + weighted
    return int(ctx.draw_choice(label, options))


def _difficulty_bias(
    difficulty: str | None,
    *,
    easy: tuple[int, ...],
    medium: tuple[int, ...],
    hard: tuple[int, ...],
) -> tuple[int, ...]:
    return {"easy": easy, "hard": hard}.get(difficulty, medium) * 5


def _allocate_column_counts(
    *, total: int, columns: int, height: int, scene: str, rng
) -> list[int]:
    """Construct a positive bounded composition, reserving one vertical gap."""
    counts = [1] * columns
    remaining = total - columns
    capacity = height - 1

    if scene in {"deep", "mixed"}:
        target = min(4, capacity, total - (columns - 1))
        addition = min(remaining, target - counts[0])
        counts[0] += addition
        remaining -= addition

    while remaining:
        available = [index for index, count in enumerate(counts) if count < capacity]
        if not available:
            raise ValueError("requested foreground count exceeds constructive capacity")
        if scene == "canonical":
            minimum = min(counts[index] for index in available)
            choices = [index for index in available if counts[index] == minimum]
            index = rng.choice(choices)
        else:
            index = rng.choice(available)
        counts[index] += 1
        remaining -= 1
    return counts


def _choose_rows(*, height: int, count: int, supported: bool, rng) -> list[int]:
    if supported:
        # A bottom cell plus a deliberately empty penultimate row refutes the
        # shortcut that any floor contact freezes the entire column.
        upper = rng.sample(range(0, height - 2), count - 1)
        return sorted(upper + [height - 1])
    # Excluding the floor guarantees movement, even for a contiguous stack.
    return sorted(rng.sample(range(0, height - 1), count))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; the selected Racket rule owns outputs."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    slot = schedule_profile(seed, sample_index, difficulty)
    canonical = _CANONICAL_PROFILES[slot // 2] if slot % 2 == 0 else None
    boundary = slot in _BOUNDARY_SLOTS
    scene = "canonical" if canonical is not None else _NONCANONICAL_SCENES[slot]

    heights = tuple(range(6, 11))
    widths = tuple(range(7, 11))
    occupied_counts = tuple(range(2, 5))
    cell_counts = tuple(range(5, 11))

    height = _draw_axis(
        ctx,
        overrides,
        "grid_h",
        heights,
        scheduled=canonical[0] if canonical else (_BOUNDARY_AXES["grid_h"] if boundary else None),
        weighted=_difficulty_bias(
            difficulty,
            easy=(6, 7),
            medium=(6, 7, 8, 9),
            hard=(8, 9, 10),
        ),
    )
    width = _draw_axis(
        ctx,
        overrides,
        "grid_w",
        widths,
        scheduled=canonical[1] if canonical else (_BOUNDARY_AXES["grid_w"] if boundary else None),
        weighted=_difficulty_bias(
            difficulty,
            easy=(7, 8),
            medium=(7, 8, 9),
            hard=(9, 10),
        ),
    )
    n_columns = _draw_axis(
        ctx,
        overrides,
        "n_occupied_columns",
        occupied_counts,
        scheduled=canonical[4] if canonical else (_BOUNDARY_AXES["n_occupied_columns"] if boundary else None),
        weighted=(2, 2, 3, 3, 4) * (6 if scene not in {"deep", "mixed"} else 1)
        + ((2, 2, 3) * 8 if scene in {"deep", "mixed"} else ()),
    )

    cell_domain = cell_counts
    if canonical is not None:
        cell_weighted: tuple[int, ...] = ()
        scheduled_cells = canonical[3]
    else:
        scheduled_cells = _BOUNDARY_AXES["n_cells"] if boundary else None
        if (
            scheduled_cells is None
            and scene in {"deep", "mixed"}
            and "n_cells" not in overrides
        ):
            # A teaching slot is a contract, not a weight.  Restrict the
            # ordinary draw to counts that force one four-cell column.  Exact
            # public overrides still use the full advertised 5..10 domain.
            feasible = tuple(value for value in cell_counts if value >= n_columns + 3)
            cell_domain = feasible
            cell_weighted = feasible * 10
        else:
            cell_weighted = _difficulty_bias(
                difficulty,
                easy=(5, 6, 7),
                medium=(5, 6, 7, 8, 9),
                hard=(7, 8, 9, 10),
            )
    n_cells = _draw_axis(
        ctx,
        overrides,
        "n_cells",
        cell_domain,
        scheduled=scheduled_cells,
        weighted=cell_weighted,
    )

    column_rng = ctx.draw_rng("occupied_columns_layout")
    columns = sorted(column_rng.sample(range(width), n_columns))
    counts = _allocate_column_counts(
        total=n_cells,
        columns=n_columns,
        height=height,
        scene=scene,
        rng=ctx.draw_rng("column_counts"),
    )

    support_index = None
    if scene in {"supported", "mixed"}:
        support_index = max(range(n_columns), key=lambda index: counts[index])

    row_rng = ctx.draw_rng("row_positions")
    column_rows = [
        _choose_rows(
            height=height,
            count=count,
            supported=index == support_index,
            rng=row_rng,
        )
        for index, count in enumerate(counts)
    ]

    if canonical is not None:
        palette_size = min(canonical[2] - 1, n_cells)
    elif boundary:
        palette_size = min(_BOUNDARY_AXES["foreground_palette_size"], n_cells - 1)
    else:
        max_palette = min(6, n_cells - 1)
        palette_options = tuple(range(2, max_palette + 1))
        palette_size = ctx.draw_choice(
            "foreground_palette_size",
            palette_options
            + _difficulty_bias(
                difficulty,
                easy=(2, 3),
                medium=palette_options,
                hard=tuple(value for value in palette_options if value >= 3) or palette_options,
            ),
        )
    palette = ctx.draw_distinct_colors("palette", n=int(palette_size), exclude={0})

    primary_index = max(range(n_columns), key=lambda index: counts[index])
    primary_coords = [
        (row, columns[primary_index]) for row in column_rows[primary_index]
    ]
    all_coords = [
        (row, columns[index])
        for index in range(n_columns)
        for row in column_rows[index]
    ]

    assignments: dict[tuple[int, int], int] = {
        primary_coords[0]: palette[0],
        primary_coords[-1]: palette[1],
    }
    remaining_coords = [coord for coord in all_coords if coord not in assignments]
    color_rng = ctx.draw_rng("color_assignment")
    color_rng.shuffle(remaining_coords)
    for color, coord in zip(palette[2:], remaining_coords):
        assignments[coord] = color
    for coord in remaining_coords[len(palette[2:]):]:
        assignments[coord] = color_rng.choice(palette)

    grid = full_grid(height, width, 0)
    for (row, column), color in assignments.items():
        grid[row][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid gravity scene: {errors}")
    return [list(row) for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------

def _identity(grid):
    """Wrong rival: sparse colored cells remain fixed."""
    return [list(row) for row in grid]


def _reverse_column_order(grid):
    """Wrong rival: pack columns downward but reverse each color sequence."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        values.reverse()
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


def _freeze_bottom_supported_columns(grid):
    """Wrong shortcut: one floor contact freezes that entire column."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        if grid[-1][column] != 0:
            for row in range(height):
                out[row][column] = grid[row][column]
            continue
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


def _cap_three_cells_per_column(grid):
    """Wrong shortcut: gravity is defined only for the observed <=3-cell regime."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        if len(values) > 3:
            for row in range(height):
                out[row][column] = grid[row][column]
            continue
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


def _unique_colors_only_gravity(grid):
    """Wrong shortcut: apply gravity only when every foreground color is unique."""
    foreground = [value for row in grid for value in row if value != 0]
    if len(foreground) == len(set(foreground)):
        return _gravity_down(grid)
    return _identity(grid)


def _max_seven_cells_only(grid):
    """Wrong scope shortcut: gravity was observed only with at most seven cells."""
    foreground = [value for row in grid for value in row if value != 0]
    return _gravity_down(grid) if len(foreground) <= 7 else _identity(grid)


def _max_three_columns_only(grid):
    """Wrong scope shortcut: gravity was observed only in at most three columns."""
    occupied = sum(
        any(grid[row][column] != 0 for row in range(len(grid)))
        for column in range(len(grid[0]))
    )
    return _gravity_down(grid) if occupied <= 3 else _identity(grid)


def _canonical_profile_only(grid):
    """Wrong memorization shortcut: apply gravity only to official profiles."""
    return _gravity_down(grid) if _profile(grid) in _CANONICAL_PROFILE_SET else _identity(grid)


def _canonical_shape_only(grid):
    """Wrong scope shortcut: apply gravity only to an official grid shape."""
    shape = (len(grid), len(grid[0]))
    return _gravity_down(grid) if shape in _CANONICAL_SHAPES else _identity(grid)


def _five_plus_colors_only(grid):
    """Wrong scope shortcut: official inputs always use at least five colors."""
    colors = {value for row in grid for value in row if value != 0}
    return _gravity_down(grid) if len(colors) >= 5 else _identity(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "reverse_column_order": _reverse_column_order,
    "freeze_bottom_supported_columns": _freeze_bottom_supported_columns,
    "cap_three_cells_per_column": _cap_three_cells_per_column,
    "unique_colors_only_gravity": _unique_colors_only_gravity,
    "max_seven_cells_only": _max_seven_cells_only,
    "max_three_columns_only": _max_three_columns_only,
    "canonical_profile_only": _canonical_profile_only,
    "canonical_shape_only": _canonical_shape_only,
    "five_plus_colors_only": _five_plus_colors_only,
}


def _moves_under_gravity(grid) -> bool:
    return not self_check(grid) and _identity(grid) != _gravity_down(grid)


def _has_order_counterexample(grid) -> bool:
    return not self_check(grid) and _reverse_column_order(grid) != _gravity_down(grid)


def _has_bottom_support_counterexample(grid) -> bool:
    return (
        not self_check(grid)
        and _freeze_bottom_supported_columns(grid) != _gravity_down(grid)
    )


def _has_deep_column_counterexample(grid) -> bool:
    return not self_check(grid) and _cap_three_cells_per_column(grid) != _gravity_down(grid)


def _has_repeated_color_counterexample(grid) -> bool:
    return not self_check(grid) and _unique_colors_only_gravity(grid) != _gravity_down(grid)


def _has_beyond_canonical_scope_counterexample(grid) -> bool:
    if self_check(grid):
        return False
    truth = _gravity_down(grid)
    scope_rivals = (
        _max_seven_cells_only,
        _max_three_columns_only,
        _canonical_profile_only,
        _canonical_shape_only,
        _five_plus_colors_only,
    )
    return all(rival(grid) != truth for rival in scope_rivals)


SEMANTIC_WITNESSES = {
    "moving_cells": _moves_under_gravity,
    "preserve_column_order": _has_order_counterexample,
    "bottom_contact_does_not_freeze_column": _has_bottom_support_counterexample,
    "gravity_handles_four_plus_cells": _has_deep_column_counterexample,
    "repeated_colors_still_fall": _has_repeated_color_counterexample,
    "beyond_canonical_scope": _has_beyond_canonical_scope_counterexample,
}

WITNESS_RIVALS = {
    "moving_cells": ["identity"],
    "preserve_column_order": ["reverse_column_order"],
    "bottom_contact_does_not_freeze_column": ["freeze_bottom_supported_columns"],
    "gravity_handles_four_plus_cells": ["cap_three_cells_per_column"],
    "repeated_colors_still_fall": ["unique_colors_only_gravity"],
    "beyond_canonical_scope": [
        "max_seven_cells_only",
        "max_three_columns_only",
        "canonical_profile_only",
        "canonical_shape_only",
        "five_plus_colors_only",
    ],
}

# Every canonical input has unique foreground colors, no column deeper than
# three cells, 5..7 cells total, 2..3 occupied columns, one of five shapes, and
# at least five foreground colors.  Each restriction below therefore fits all
# official pairs and must be rejected by generated demonstrations.
CANONICAL_SHORTCUTS = {
    "cap_three_cells_per_column": _cap_three_cells_per_column,
    "unique_colors_only_gravity": _unique_colors_only_gravity,
    "max_seven_cells_only": _max_seven_cells_only,
    "max_three_columns_only": _max_three_columns_only,
    "canonical_profile_only": _canonical_profile_only,
    "canonical_shape_only": _canonical_shape_only,
    "five_plus_colors_only": _five_plus_colors_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a declared rival survives all demonstrations."""
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence of input/output pairs"]
    if len(demos) < EXAMPLES_NEEDED:
        return [
            f"need at least {EXAMPLES_NEEDED} demonstrations, found {len(demos)}"
        ]

    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is outside the teaching grammar: {errors[0]}")
            continue
        if pair["output"] != _gravity_down(pair["input"]):
            reasons.append(f"pair {index} output does not match downward gravity")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:
            reasons.append(
                f"competitor {name!r} raised {type(exc).__name__}: {exc}"
            )
            continue
        if survives:
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
