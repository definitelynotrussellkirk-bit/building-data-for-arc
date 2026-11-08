"""Semantic generator for ARC task 2fd7d58a066c (Vertical Gap Fill).

The authoritative rule is column-local and color-blind: on a fresh blank grid,
paint cyan from the topmost nonzero cell through the bottommost nonzero cell in
every occupied column.  Version 3 replaces a narrow "same-color,
non-adjacent endpoint pairs" grammar with a five-example / four-profile lesson schedule that
keeps canonical-looking examples while explicitly falsifying plausible
surface shortcuts:

* adjacent columns and repeated marker colors are lawful;
* endpoint colors may differ and any nonzero ARC color is evidence;
* a column may contain extra interior evidence;
* a singleton occupied column is a one-cell span, not an ignored degenerate.

Only ``scene_profile`` is a public exact override.  Geometry, colors, and
placement vary internally, avoiding a large dishonest Cartesian override
surface whose combinations the old generator could not honor.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2fd7d58a066c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5fe179015bd4"

SUMMARY = (
    "For each occupied column independently, discard marker colors and paint "
    "the inclusive topmost-to-bottommost span cyan (8) on a fresh zero grid. "
    "The lesson schedule covers canonical color-2 endpoint pairs, adjacent "
    "columns with shared colors, mixed-color extremes, extra markers, and "
    "singleton one-cell spans."
)

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "background is 0 and all nonzero ARC colors are interchangeable evidence",
    "at least two columns have separated extreme markers with a visible blank gap",
    "occupied columns may be adjacent and may reuse colors",
    "the output is a fresh zero grid with inclusive cyan spans per occupied column",
    "singleton occupied columns are lawful one-cell spans",
    "ordinary generated inputs are non-identity teaching examples",
]

SCENE_PROFILES = (
    "canonical_pairs",
    "adjacent_shared",
    "mixed_extremes",
    "singleton_and_extra",
)
# Canonical scale is deliberately anchored twice per cycle.  The other three
# entries remain high-information shortcut counterexamples; any five
# consecutive samples contain every semantic profile.
PROFILE_SCHEDULE = (
    "canonical_pairs",
    "canonical_pairs",
    "adjacent_shared",
    "mixed_extremes",
    "singleton_and_extra",
)
SCHEDULE_PROFILES = SCENE_PROFILES
CANONICAL_DIMS = ((10, 8), (9, 9), (10, 10))

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index modulo 5 schedule with two canonical anchors",
        "valid": "|".join(SCENE_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_NONZERO_COLORS = tuple(range(1, 10))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(
            "scene_profile must be one of " + ", ".join(SCENE_PROFILES)
        )


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty row"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be integer ARC colors in 0..9"]
    return []


def _occupied_columns(grid: Any) -> dict[int, list[tuple[int, int]]]:
    if _grid_errors(grid):
        return {}
    h, w = len(grid), len(grid[0])
    return {
        c: [(r, int(grid[r][c])) for r in range(h) if grid[r][c] != 0]
        for c in range(w)
        if any(grid[r][c] != 0 for r in range(h))
    }


def _dimension_band(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (7, 9), (6, 8)
    if difficulty == "medium":
        return (8, 11), (7, 10)
    if difficulty == "hard":
        return (10, 14), (9, 12)
    return (7, 14), (6, 12)


def _profile_dimensions(ctx, profile: str) -> tuple[int, int]:
    if profile == "canonical_pairs":
        rng = ctx.draw_rng("canonical_dimensions")
        return CANONICAL_DIMS[rng.randrange(len(CANONICAL_DIMS))]
    (h_lo, h_hi), (w_lo, w_hi) = _dimension_band(ctx.difficulty)
    rng = ctx.draw_rng("dimensions")
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi)


def _sample_columns(rng, width: int, count: int) -> list[int]:
    if count > width:
        raise ValueError(f"cannot place {count} occupied columns in width {width}")
    return sorted(rng.sample(range(width), count))


def _sample_adjacent_columns(rng, width: int, count: int) -> list[int]:
    if count < 2 or count > width:
        raise ValueError("adjacent profile needs 2..width occupied columns")
    start = rng.randrange(width - 1)
    chosen = {start, start + 1}
    remaining = [c for c in range(width) if c not in chosen]
    chosen.update(rng.sample(remaining, count - 2))
    return sorted(chosen)


def _span_rows(rng, height: int, *, min_cells: int = 3) -> tuple[int, int]:
    if height < min_cells:
        raise ValueError(f"height {height} cannot hold a {min_cells}-cell span")
    span_cells = rng.randint(min_cells, height)
    top = rng.randint(0, height - span_cells)
    return top, top + span_cells - 1


def _paint_pair(grid, column: int, top: int, bottom: int, top_color: int, bottom_color: int) -> None:
    grid[top][column] = top_color
    grid[bottom][column] = bottom_color


def _draw_canonical_pairs(ctx, h: int, w: int) -> list[list[int]]:
    layout = ctx.draw_rng("layout")
    rows = ctx.draw_rng("spans")
    grid = full_grid(h, w, 0)
    for column in _sample_columns(layout, w, 3):
        top, bottom = _span_rows(rows, h, min_cells=3)
        _paint_pair(grid, column, top, bottom, 2, 2)
    return grid


def _draw_adjacent_shared(ctx, h: int, w: int) -> list[list[int]]:
    layout = ctx.draw_rng("layout")
    rows = ctx.draw_rng("spans")
    colors = ctx.draw_rng("colors")
    count = 3 if w < 9 else colors.choice((3, 4))
    columns = _sample_adjacent_columns(layout, w, count)
    adjacent_pair = next(
        (a, b) for a, b in zip(columns, columns[1:]) if b == a + 1
    )
    shared = colors.choice(tuple(c for c in _NONZERO_COLORS if c != 2))
    palette = [shared if c in adjacent_pair else colors.choice(_NONZERO_COLORS) for c in columns]
    grid = full_grid(h, w, 0)
    for column, color in zip(columns, palette):
        top, bottom = _span_rows(rows, h, min_cells=3)
        _paint_pair(grid, column, top, bottom, color, color)
    return grid


def _draw_mixed_extremes(ctx, h: int, w: int) -> list[list[int]]:
    layout = ctx.draw_rng("layout")
    rows = ctx.draw_rng("spans")
    colors = ctx.draw_rng("colors")
    count = 3 if w < 10 else colors.choice((3, 4))
    columns = _sample_columns(layout, w, count)
    mixed_column = columns[colors.randrange(len(columns))]
    top_color, bottom_color = colors.sample(_NONZERO_COLORS, 2)
    grid = full_grid(h, w, 0)
    for column in columns:
        top, bottom = _span_rows(rows, h, min_cells=3)
        if column == mixed_column:
            _paint_pair(grid, column, top, bottom, top_color, bottom_color)
        else:
            color = colors.choice(_NONZERO_COLORS)
            _paint_pair(grid, column, top, bottom, color, color)
    return grid


def _draw_singleton_and_extra(ctx, h: int, w: int) -> list[list[int]]:
    layout = ctx.draw_rng("layout")
    rows = ctx.draw_rng("spans")
    colors = ctx.draw_rng("colors")
    count = 3 if w < 9 else colors.choice((3, 4))
    columns = _sample_columns(layout, w, count)
    singleton_column = columns[0]
    extra_column = columns[1]
    grid = full_grid(h, w, 0)

    singleton_row = rows.randrange(h)
    grid[singleton_row][singleton_column] = colors.choice(tuple(c for c in _NONZERO_COLORS if c != 8))

    for column in columns[1:]:
        min_cells = 4 if column == extra_column else 3
        top, bottom = _span_rows(rows, h, min_cells=min_cells)
        color = colors.choice(_NONZERO_COLORS)
        _paint_pair(grid, column, top, bottom, color, color)
        if column == extra_column:
            interior = list(range(top + 1, bottom))
            # With a >=4-cell span, one interior mark still leaves at least one
            # blank cell for the rule to visibly add.
            grid[rows.choice(interior)][column] = color
    return grid


_PROFILE_DRAWERS = {
    "canonical_pairs": _draw_canonical_pairs,
    "adjacent_shared": _draw_adjacent_shared,
    "mixed_extremes": _draw_mixed_extremes,
    "singleton_and_extra": _draw_singleton_and_extra,
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; labels remain Racket-authoritative."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        scheduled = PROFILE_SCHEDULE[sample_index % len(PROFILE_SCHEDULE)]
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    h, w = _profile_dimensions(ctx, profile)
    grid = _PROFILE_DRAWERS[profile](ctx, h, w)
    errors = self_check(grid, difficulty=difficulty)
    if errors:  # Construction assertion: fail loudly instead of shipping drift.
        raise AssertionError(f"generated invalid {profile} scene: {errors}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's informative training grammar, not surface colors."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    occupied = _occupied_columns(grid)
    spanning_columns = 0
    visible_gap = False
    for column, cells in occupied.items():
        if len(cells) == 1:
            continue  # Lawful one-cell span; other columns must teach expansion.
        top, bottom = cells[0][0], cells[-1][0]
        if bottom - top < 2:
            errors.append(f"column {column} span is shorter than 3 cells")
            continue
        spanning_columns += 1
        if any(grid[row][column] == 0 for row in range(top, bottom + 1)):
            visible_gap = True

    if spanning_columns < 2:
        errors.append(
            f"expected at least two informative spanning columns, got {spanning_columns}"
        )
    if spanning_columns >= 2 and not visible_gap:
        errors.append("all occupied spans are already filled; transformation is identity")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the literal canonical surface while accepting all three pairs."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in CANONICAL_DIMS:
        errors.append(f"dimensions {(h, w)} are outside canonical profiles")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 2}:
        errors.append("canonical inputs use only background 0 and marker color 2")
    occupied = _occupied_columns(grid)
    if len(occupied) != 3 or any(len(cells) != 2 for cells in occupied.values()):
        errors.append("canonical inputs have exactly three columns with two markers each")
    return errors


def expected_output(grid) -> list[list[int]]:
    """Python audit mirror of the pinned Racket rule; never used for labels."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for column, cells in _occupied_columns(grid).items():
        for row in range(cells[0][0], cells[-1][0] + 1):
            output[row][column] = 8
    return output


# Alias used by some review tooling and makes the audit-only role explicit.
_official_python_mirror = expected_output


def _is_canonical_surface(grid) -> bool:
    return strict_canonical_like(grid) == []


def _has_adjacent_columns(grid) -> bool:
    columns = sorted(_occupied_columns(grid))
    return any(b == a + 1 for a, b in zip(columns, columns[1:]))


def _has_repeated_column_colors(grid) -> bool:
    colors = []
    for cells in _occupied_columns(grid).values():
        values = {value for _, value in cells}
        if len(values) == 1:
            colors.append(next(iter(values)))
    return len(colors) != len(set(colors))


def _has_noncanonical_marker_color(grid) -> bool:
    return any(value not in (0, 2) for row in grid for value in row)


def _has_mixed_extremes(grid) -> bool:
    return any(
        len(cells) >= 2 and cells[0][1] != cells[-1][1]
        for cells in _occupied_columns(grid).values()
    )


def _has_singleton_column(grid) -> bool:
    return any(len(cells) == 1 for cells in _occupied_columns(grid).values())


def _has_extra_marker_column(grid) -> bool:
    return any(len(cells) >= 3 for cells in _occupied_columns(grid).values())


def _classify_profile(grid) -> str | None:
    if self_check(grid):
        return None
    if _has_singleton_column(grid) and _has_extra_marker_column(grid):
        return "singleton_and_extra"
    if _has_mixed_extremes(grid):
        return "mixed_extremes"
    if _is_canonical_surface(grid):
        return "canonical_pairs"
    if _has_adjacent_columns(grid) and _has_repeated_column_colors(grid):
        return "adjacent_shared"
    return None


def observe_overrides(grid) -> dict[str, str]:
    """Recover the one declared exact axis from generated geometry/semantics."""
    profile = _classify_profile(grid)
    return {"scene_profile": profile} if profile is not None else {}


def semantic_observables(grid) -> dict[str, Any]:
    occupied = _occupied_columns(grid)
    return {
        **observe_overrides(grid),
        "valid": self_check(grid) == [],
        "height": len(grid) if isinstance(grid, (list, tuple)) else 0,
        "width": len(grid[0]) if isinstance(grid, (list, tuple)) and grid else 0,
        "occupied_columns": len(occupied),
        "singleton_columns": sum(len(cells) == 1 for cells in occupied.values()),
        "mixed_extreme_columns": sum(
            len(cells) >= 2 and cells[0][1] != cells[-1][1]
            for cells in occupied.values()
        ),
        "extra_marker_columns": sum(len(cells) >= 3 for cells in occupied.values()),
        "adjacent_columns": _has_adjacent_columns(grid),
        "repeated_column_colors": _has_repeated_column_colors(grid),
    }


def _paint_selected_columns(grid, predicate: Callable[[int, list[tuple[int, int]], dict[int, list[tuple[int, int]]]], bool]) -> list[list[int]]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    occupied = _occupied_columns(grid)
    for column, cells in occupied.items():
        if not predicate(column, cells, occupied):
            continue
        for row in range(cells[0][0], cells[-1][0] + 1):
            output[row][column] = 8
    return output


def _rival_same_color_extremes(grid):
    return _paint_selected_columns(
        grid, lambda _c, cells, _all: cells[0][1] == cells[-1][1]
    )


def _rival_exactly_two_markers(grid):
    return _paint_selected_columns(grid, lambda _c, cells, _all: len(cells) == 2)


def _rival_ignore_singletons(grid):
    return _paint_selected_columns(grid, lambda _c, cells, _all: len(cells) >= 2)


def _rival_color2_only(grid):
    return _paint_selected_columns(
        grid, lambda _c, cells, _all: all(value == 2 for _, value in cells)
    )


def _rival_canonical_surface_only(grid):
    return _paint_selected_columns(
        grid,
        lambda _c, cells, _all: len(cells) == 2
        and all(value == 2 for _, value in cells),
    )


def _rival_nonadjacent_only(grid):
    return _paint_selected_columns(
        grid,
        lambda column, _cells, occupied: (column - 1 not in occupied)
        and (column + 1 not in occupied),
    )


def _rival_unique_column_color_only(grid):
    occupied = _occupied_columns(grid)
    mono = {
        column: cells[0][1]
        for column, cells in occupied.items()
        if len({value for _, value in cells}) == 1
    }
    counts = Counter(mono.values())
    return _paint_selected_columns(
        grid,
        lambda column, _cells, _all: column in mono and counts[mono[column]] == 1,
    )


SEMANTIC_RIVALS = {
    "same_color_extremes_only": _rival_same_color_extremes,
    "exactly_two_markers_only": _rival_exactly_two_markers,
    "ignore_singleton_columns": _rival_ignore_singletons,
    "color_2_only": _rival_color2_only,
    "canonical_surface_only": _rival_canonical_surface_only,
    "nonadjacent_columns_only": _rival_nonadjacent_only,
    "one_column_per_marker_color": _rival_unique_column_color_only,
}

# These five reproduce every canonical pair and therefore require generated
# counterexamples; the other two are still useful lesson competitors.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "same_color_extremes_only",
        "exactly_two_markers_only",
        "ignore_singleton_columns",
        "color_2_only",
        "canonical_surface_only",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "adjacent_active_columns": _has_adjacent_columns,
    "repeated_column_colors": _has_repeated_column_colors,
    "noncanonical_marker_colors": _has_noncanonical_marker_color,
    "mixed_extreme_colors": _has_mixed_extremes,
    "singleton_column": _has_singleton_column,
    "extra_marker_column": _has_extra_marker_column,
}

WITNESS_RIVALS = {
    "adjacent_active_columns": ["nonadjacent_columns_only"],
    "repeated_column_colors": ["one_column_per_marker_color"],
    "noncanonical_marker_colors": ["color_2_only", "canonical_surface_only"],
    "mixed_extreme_colors": ["same_color_extremes_only"],
    "singleton_column": ["ignore_singleton_columns", "exactly_two_markers_only"],
    "extra_marker_column": ["exactly_two_markers_only", "canonical_surface_only"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic five-example semantic schedule to the gate."""
    del seed, difficulty
    return PROFILE_SCHEDULE[sample_index % len(PROFILE_SCHEDULE)]


def _normalized_grid(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def lesson_identifiable(demos, query) -> list[str]:
    """Require one five-demo cycle to rule out every named competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is not lawful: {errors[0]}")
            continue
        profile = _classify_profile(pair["input"])
        if profile is not None:
            profiles.add(profile)
        if expected_output(pair["input"]) != _normalized_grid(pair["output"]):
            reasons.append(f"demo {index} disagrees with the pinned Python audit mirror")

    missing_profiles = sorted(set(SCENE_PROFILES) - profiles)
    if missing_profiles:
        reasons.append("demonstrations miss semantic profile(s): " + ", ".join(missing_profiles))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is not lawful: {query_errors[0]}")
    elif expected_output(query["input"]) != _normalized_grid(query["output"]):
        reasons.append("query disagrees with the pinned Python audit mirror")

    for name, rival in LESSON_COMPETITORS.items():
        rejected = any(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) != _normalized_grid(pair["output"])
            for pair in demos
        )
        if rejected:
            continue
        if not query_errors and rival(query["input"]) == _normalized_grid(query["output"]):
            continue  # Answer-equivalent on this query despite surviving demos.
        reasons.append(f"named rival remains viable on demos: {name}")
    return reasons


def mutation_fixtures():
    """Task-local must-reject teaching impostors for future regression gates."""
    blank = full_grid(9, 8, 0)

    only_singleton = full_grid(9, 8, 0)
    only_singleton[4][3] = 2

    short_spans = full_grid(9, 8, 0)
    short_spans[1][2] = short_spans[2][2] = 3
    short_spans[5][5] = short_spans[6][5] = 4

    already_filled = full_grid(9, 8, 0)
    for row in range(1, 6):
        already_filled[row][2] = 3
    for row in range(2, 8):
        already_filled[row][5] = 4

    return [
        ("all_background", blank),
        ("only_singleton", only_singleton),
        ("two_short_spans", short_spans),
        ("already_filled_identity", already_filled),
    ]
