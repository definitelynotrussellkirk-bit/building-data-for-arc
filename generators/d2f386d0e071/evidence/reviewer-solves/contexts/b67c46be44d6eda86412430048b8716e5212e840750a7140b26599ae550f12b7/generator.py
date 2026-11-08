"""Training generator for ``d2f386d0e071`` — complete a vertical mirror.

The selected Racket rule is ``(overlay g (flip-lr g))``.  Lawful inputs are
sparse, zero-background grids whose non-zero source cells occupy the left side
of the vertical midline (the center column is also legal on odd widths).  Every
off-axis mirror destination starts blank, so the output keeps each source and
adds its same-color left/right reflection.

The canonical task deliberately contains both even and odd widths and one
center-column source.  The schedule below keeps those branches visible while
four exact, independently observable axes provide controlled variation.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d2f386d0e071"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f48a460c6519"

SUMMARY = (
    "Sparse non-zero cells occupy the left side of a zero-background grid; "
    "on odd widths the center column may also contain a source.  Widths may "
    "be even (midline between columns) or odd (center-column axis).  The rule "
    "preserves every source and copies its color to column w-1-c, completing "
    "left/right mirror symmetry.  Off-axis mirror destinations are blank in "
    "the input."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is color 0",
    "width may be even or odd; an odd-width center-column source is legal",
    "all non-zero sources lie at or left of the vertical midline",
    "every off-axis mirror destination is initially blank",
    "at least four sources and two distinct off-axis distances make the rule visible",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-scale height",
        "valid": "5..12",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-scale even/odd width",
        "valid": "7..14",
        "doc": "Returned grid width; both parities are meaningful.",
    },
    "n_cells": {
        "type": "int",
        "default": "4 easy, 6 medium/default, 8 hard",
        "valid": "4..9",
        "doc": "Exact number of non-zero source cells in the input.",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "4",
        "valid": "2..4",
        "doc": "Exact number of non-zero colors used by source cells.",
    },
}

# Four consecutive sample indexes cover every semantic branch.  The first
# profile alternates between the two 9-wide canonical dimensions, so all five
# public (height, width, palette-size) profiles remain represented.
SCHEDULE_PROFILES = (
    "odd_plain",
    "even_narrow",
    "odd_centerline",
    "even_wide",
)
_PROFILE_DIMS = {
    "even_narrow": (6, 8),
    "odd_centerline": (8, 7),
    "even_wide": (7, 10),
}

_COLORS = tuple(range(1, 10))
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")


def _difficulty_offset(difficulty: Any) -> int:
    return {None: 0, "easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Semantic profile selected for a draw.

    ``seed`` is intentionally not part of the branch index: every consecutive
    four-example window must cover every profile, independent of lesson seed.
    """
    del seed
    return SCHEDULE_PROFILES[
        (int(sample_index) + _difficulty_offset(difficulty))
        % len(SCHEDULE_PROFILES)
    ]


def _scheduled_dimensions(
    profile: str, seed: int, sample_index: int
) -> tuple[int, int]:
    if profile == "odd_plain":
        # Both are exact canonical profiles.  Mix them without adding a hidden
        # semantic branch to the four-step teaching schedule.
        return ((7, 9), (9, 9))[(int(seed) + int(sample_index)) & 1]
    return _PROFILE_DIMS[profile]


def _default_n_cells(difficulty: Any) -> int:
    return {"easy": 4, "hard": 8}.get(difficulty, 6)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'; "
            f"got {difficulty!r}"
        )


def _source_columns(width: int) -> list[int]:
    """Columns on or left of the vertical axis."""
    return list(range((width - 1) // 2 + 1))


def _off_axis_columns(width: int) -> list[int]:
    return [c for c in _source_columns(width) if c != width - 1 - c]


def _place_sources(
    *,
    height: int,
    width: int,
    n_cells: int,
    n_colors: int,
    include_centerline: bool,
    layout_rng: Any,
    palette_rng: Any,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    off_axis = _off_axis_columns(width)
    if len(off_axis) < 2:
        raise ValueError(f"width {width} does not provide two off-axis distances")

    rows = list(range(height))
    layout_rng.shuffle(rows)
    far_col, near_col = off_axis[0], off_axis[-1]
    positions: list[tuple[int, int]] = [
        (rows[0], far_col),
        (rows[1 % height], near_col),
    ]

    center_row: int | None = None
    center = width // 2
    if include_centerline and width % 2 == 1:
        center_row = rows[2 % height]
        positions.append((center_row, center))

    used = set(positions)
    candidates = [
        (row, col)
        for row in range(height)
        for col in _source_columns(width)
        if (row, col) not in used
        # Keep the centerline witness unambiguous: no other source in that row,
        # so a solver that duplicates the axis cell is visibly wrong.
        and (center_row is None or row != center_row)
    ]
    layout_rng.shuffle(candidates)
    need = n_cells - len(positions)
    if need < 0:
        positions = positions[:n_cells]
    elif need > len(candidates):
        raise ValueError(
            f"cannot place {n_cells} sources in {height}x{width} under the "
            "mirror-destination constraints"
        )
    else:
        positions.extend(candidates[:need])

    palette = palette_rng.sample(_COLORS, n_colors)
    # Cycling guarantees every requested color is realized.  The first two
    # positions are off-axis anchors, so default multi-color draws also refute
    # one-color-only mirror shortcuts in every lesson.
    values = [palette[index % n_colors] for index in range(len(positions))]
    for (row, col), value in zip(positions, values, strict=True):
        grid[row][col] = value
    return grid


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    """Generate one deterministic lawful input.

    Default dimensions are pinned to canonical profiles.  Explicit axes remain
    fully Cartesian: every value in each declared range works with every value
    of the other axes and in every difficulty band.
    """
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _scheduled_dimensions(profile, seed, sample_index)

    effective = dict(overrides)
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("n_cells", _default_n_cells(difficulty))
    effective.setdefault("n_distinct_colors", 4)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 5, 12)
    width = ctx.draw_int("grid_w", 7, 14)
    n_cells = ctx.draw_int("n_cells", 4, 9)
    n_colors = ctx.draw_int("n_distinct_colors", 2, 4)

    return _place_sources(
        height=height,
        width=width,
        n_cells=n_cells,
        n_colors=n_colors,
        include_centerline=profile == "odd_centerline",
        layout_rng=ctx.draw_rng("layout"),
        palette_rng=ctx.draw_rng("palette"),
    )


def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    return []


def self_check(
    grid: Any, *, difficulty: Any = None, meta: dict[str, Any] | None = None
) -> list[str]:
    """Validate a source-side mirror-completion input.

    The validator intentionally accepts both width parities and odd-width
    centerline marks because all occur in the authoritative examples.
    """
    del difficulty, meta
    errors = _grid_shape_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 12:
        errors.append(f"height {height} outside supported 5..12")
    if not 7 <= width <= 14:
        errors.append(f"width {width} outside supported 7..14")

    source_limit = (width - 1) // 2
    sources: list[tuple[int, int, int]] = []
    bad_values: list[tuple[int, int, Any]] = []
    right_sources: list[tuple[int, int]] = []
    occupied_targets: list[tuple[int, int, int]] = []

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                bad_values.append((row, col, value))
                continue
            if value == 0:
                continue
            sources.append((row, col, value))
            if col > source_limit:
                right_sources.append((row, col))
                continue
            mirror_col = width - 1 - col
            if mirror_col != col and grid[row][mirror_col] != 0:
                occupied_targets.append((row, col, mirror_col))

    if bad_values:
        errors.append(f"cell values must be integer colors 0..9; found {bad_values[:3]}")
    if not 4 <= len(sources) <= 9:
        errors.append(f"expected 4..9 non-zero sources; found {len(sources)}")
    colors = {value for _, _, value in sources}
    if not 2 <= len(colors) <= 4:
        errors.append(f"expected 2..4 non-zero colors; found {len(colors)}")
    if right_sources:
        errors.append(
            "non-zero sources must be on or left of the vertical midline; "
            f"found {right_sources[:4]}"
        )
    if occupied_targets:
        errors.append(
            "off-axis mirror destinations must start blank; conflicts "
            f"{occupied_targets[:4]}"
        )

    off_axis = [
        (row, col)
        for row, col, _ in sources
        if col <= source_limit and col != width - 1 - col
    ]
    if not off_axis:
        errors.append("no off-axis source: the selected rule would be an identity")
    distances = {abs((width - 1) - 2 * col) for _, col in off_axis}
    if len(distances) < 2:
        errors.append(
            "need sources at two distinct off-axis distances to expose the "
            "vertical midline"
        )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    return self_check(grid)


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover every declared exact axis from a returned grid."""
    sources = [value for row in grid for value in row if value != 0]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": len(sources),
        "n_distinct_colors": len(set(sources)),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Faithful Python mirror of ``(overlay g (flip-lr g))``.

    Overlay semantics matter for arbitrary conflicting inputs: the flipped
    grid is the top layer, so a non-zero mirrored value wins at each cell.
    Lawful generated inputs have blank destinations and therefore behave as a
    same-color union with the left/right reflection.
    """
    if _grid_shape_errors(grid):
        raise ValueError("rule_mirror requires a non-empty rectangular grid")
    width = len(grid[0])
    return [
        [
            row[width - 1 - col]
            if row[width - 1 - col] != 0
            else row[col]
            for col in range(width)
        ]
        for row in grid
    ]


# ---------------------------------------------------------------------------
# Plausible wrong rules and task-linked counterexample witnesses.
# ---------------------------------------------------------------------------


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _mirror_only(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _union_flip_ud(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    return [
        [
            grid[height - 1 - row][col]
            if grid[height - 1 - row][col] != 0
            else grid[row][col]
            for col in range(len(grid[0]))
        ]
        for row in range(height)
    ]


def _nearest_axis_only(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    width = len(grid[0])
    candidates = [
        (abs((width - 1) - 2 * col), row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and col != width - 1 - col
    ]
    if not candidates:
        return output
    nearest = min(distance for distance, *_ in candidates)
    for distance, row, col, value in candidates:
        if distance == nearest:
            output[row][width - 1 - col] = value
    return output


def _lowest_color_only(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    width = len(grid[0])
    nonzero = [value for row in grid for value in row if value != 0]
    if not nonzero:
        return output
    chosen = min(nonzero)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == chosen:
                output[row][width - 1 - col] = value
    return output


def _duplicate_centerline(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    width = len(grid[0])
    if width % 2 == 0:
        return output
    center = width // 2
    for row, values in enumerate(grid):
        if values[center] != 0 and center + 1 < width:
            output[row][center + 1] = values[center]
    return output


def _off_by_one_axis(grid: list[list[int]]) -> list[list[int]]:
    """Wrongly mirror around the gap one half-cell to the right."""
    output = [list(row) for row in grid]
    width = len(grid[0])
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            target = width - col
            if value != 0 and 0 <= target < width:
                output[row][target] = value
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "mirror_only": _mirror_only,
    "flip_up_down_union": _union_flip_ud,
    "nearest_axis_only": _nearest_axis_only,
    "lowest_color_only": _lowest_color_only,
    "duplicate_centerline": _duplicate_centerline,
    "off_by_one_axis": _off_by_one_axis,
}


def _rival_differs(name: str, grid: list[list[int]]) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


def _w_visible_copy(grid: list[list[int]]) -> bool:
    return _rival_differs("identity", grid)


def _w_preserve_sources(grid: list[list[int]]) -> bool:
    return _rival_differs("mirror_only", grid)


def _w_same_row_axis(grid: list[list[int]]) -> bool:
    return _rival_differs("flip_up_down_union", grid)


def _w_multiple_distances(grid: list[list[int]]) -> bool:
    return _rival_differs("nearest_axis_only", grid)


def _w_multiple_colors(grid: list[list[int]]) -> bool:
    return _rival_differs("lowest_color_only", grid)


def _w_centerline_noop(grid: list[list[int]]) -> bool:
    width = len(grid[0])
    return (
        width % 2 == 1
        and any(row[width // 2] != 0 for row in grid)
        and _rival_differs("duplicate_centerline", grid)
    )


def _w_even_between_columns(grid: list[list[int]]) -> bool:
    return len(grid[0]) % 2 == 0 and _rival_differs("off_by_one_axis", grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "visible_mirror_copy": _w_visible_copy,
    "original_sources_remain": _w_preserve_sources,
    "reflection_stays_in_same_row": _w_same_row_axis,
    "all_axis_distances_are_mirrored": _w_multiple_distances,
    "all_source_colors_are_mirrored": _w_multiple_colors,
    "centerline_source_is_a_noop": _w_centerline_noop,
    "even_width_axis_is_between_columns": _w_even_between_columns,
}

WITNESS_RIVALS = {
    "visible_mirror_copy": ["identity"],
    "original_sources_remain": ["mirror_only"],
    "reflection_stays_in_same_row": ["flip_up_down_union"],
    "all_axis_distances_are_mirrored": ["nearest_axis_only"],
    "all_source_colors_are_mirrored": ["lowest_color_only"],
    "centerline_source_is_a_noop": ["duplicate_centerline"],
    "even_width_axis_is_between_columns": ["off_by_one_axis"],
}

# Four consecutive scheduled demos include odd/even widths and the centerline
# branch, so every named rival is expected to be refuted within one lesson.
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(
    demos: list[dict[str, list[list[int]]]],
    query: dict[str, list[list[int]]],
) -> list[str]:
    """Return rivals that fit every demo but change the official query answer."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if fits_demos and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query"
            )
    return reasons
