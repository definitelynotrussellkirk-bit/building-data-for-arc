"""Semantic generator for ARC task 4cfd24806fb2.

The authoritative transformation preserves the input and copies every nonzero,
non-gray cell left of the unique full-height gray divider to its reflected
position on the right.  Version 2 replaces a broad but mostly inert override
surface with a four-profile teaching schedule:

* ``canonical_sparse`` anchors the exact canonical size/palette profiles;
* ``off_center_cluster`` makes the divider, not the canvas midpoint, causal;
* ``edge_row_motif`` exercises dense, connected, same-row, and edge sources;
* ``preserved_right_noise`` proves unrelated right-side cells survive.

Every four consecutive samples contain all four profiles.  The Racket rule
remains authoritative; ``expected_output`` is an audit mirror used only by
review hooks and tests.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4cfd24806fb2"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b5a5db408e2f"

SUMMARY = (
    "Preserve the grid and reflect every colored cell left of the unique "
    "full-height gray(5) divider to the equidistant cell on its right, "
    "preserving color. The four-profile lesson schedule includes exact "
    "canonical anchors, off-center dividers, dense edge/row motifs, and "
    "unrelated right-side cells that must remain unchanged."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "background is 0 and the divider is the unique full-height color-5 column",
    "at least three multicolor source cells lie left of the divider",
    "source cells occupy at least two distances from the divider",
    "every source mirror destination is in bounds and initially empty",
    "right-side distractors, when present, do not occupy mirror destinations",
    "the output preserves the input and adds same-row, same-color reflections",
]

SCENE_PROFILES = (
    "canonical_sparse",
    "off_center_cluster",
    "edge_row_motif",
    "preserved_right_noise",
)
PROFILE_SCHEDULE = SCENE_PROFILES
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index modulo 4 semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_NONZERO_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

# (height, width): (divider column, source-cell count, source-color count)
# Every canonical puzzle has exactly one repeated source color, hence
# source_cell_count == source_color_count + 1.
_CANONICAL_SPECS = {
    (8, 9): (4, 4, 3),
    (9, 11): (5, 5, 4),
    (10, 12): (5, 5, 4),
    (10, 13): (6, 6, 5),
    (11, 15): (7, 6, 5),
}
CANONICAL_DIMS = tuple(sorted(_CANONICAL_SPECS))


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


def _divider_columns(grid: Any) -> list[int]:
    if _grid_errors(grid):
        return []
    h, w = len(grid), len(grid[0])
    return [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]


def _divider(grid: Any) -> int:
    columns = _divider_columns(grid)
    if not columns:
        raise ValueError("no full-height color-5 divider")
    return columns[0]


def _source_cells(grid: Any, divider: int | None = None) -> list[tuple[int, int, int]]:
    if _grid_errors(grid):
        return []
    div = _divider(grid) if divider is None else divider
    return [
        (r, c, int(grid[r][c]))
        for r in range(len(grid))
        for c in range(div)
        if grid[r][c] not in (0, 5)
    ]


def _right_cells(grid: Any, divider: int | None = None) -> list[tuple[int, int, int]]:
    if _grid_errors(grid):
        return []
    div = _divider(grid) if divider is None else divider
    return [
        (r, c, int(grid[r][c]))
        for r in range(len(grid))
        for c in range(div + 1, len(grid[0]))
        if grid[r][c] not in (0, 5)
    ]


def _mirror_column(divider: int, column: int) -> int:
    return 2 * divider - column


def _paint_divider(grid: list[list[int]], divider: int) -> None:
    for row in range(len(grid)):
        grid[row][divider] = 5


def _dimension_ranges(difficulty: Any, *, wide: bool = False) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (8, 10), ((13, 15) if wide else (11, 15))
    if difficulty == "medium":
        return (10, 14), ((15, 19) if wide else (13, 19))
    if difficulty == "hard":
        return (13, 18), ((19, 25) if wide else (17, 25))
    return (8, 18), ((13, 25) if wide else (11, 25))


def _draw_dimensions(ctx, label: str, *, wide: bool = False, odd_width: bool = False) -> tuple[int, int]:
    (h_lo, h_hi), (w_lo, w_hi) = _dimension_ranges(ctx.difficulty, wide=wide)
    rng = ctx.draw_rng(label)
    h = rng.randint(h_lo, h_hi)
    widths = [w for w in range(w_lo, w_hi + 1) if not odd_width or w % 2 == 1]
    if not widths:
        raise ValueError("dimension band has no legal width")
    return h, rng.choice(widths)


def _available_left_positions(h: int, w: int, divider: int) -> list[tuple[int, int]]:
    min_col = max(0, 2 * divider - (w - 1))
    return [(r, c) for r in range(h) for c in range(min_col, divider)]


def _fill_positions(
    grid: list[list[int]],
    positions: list[tuple[int, int]],
    colors: list[int],
) -> None:
    if len(positions) != len(colors):
        raise ValueError("position/color cardinality mismatch")
    for (row, column), color in zip(positions, colors):
        grid[row][column] = color


def _draw_canonical_sparse(ctx) -> list[list[int]]:
    spec_rng = ctx.draw_rng("canonical_spec")
    dims = spec_rng.choice(CANONICAL_DIMS)
    h, w = dims
    divider, source_count, color_count = _CANONICAL_SPECS[dims]
    grid = full_grid(h, w, 0)
    _paint_divider(grid, divider)

    layout = ctx.draw_rng("canonical_layout")
    color_rng = ctx.draw_rng("canonical_colors")
    colors = color_rng.sample(_NONZERO_COLORS, color_count)

    # The repeated color occupies an adjacent same-row pair, guaranteeing two
    # source distances while matching the canonical one-repeat palette pattern.
    pair_row = layout.randrange(h)
    pair_col = layout.randrange(max(1, divider - 1))
    pair_col = min(pair_col, divider - 2)
    positions = [(pair_row, pair_col), (pair_row, pair_col + 1)]
    available = [
        pos
        for pos in _available_left_positions(h, w, divider)
        if pos not in positions
    ]
    positions.extend(layout.sample(available, source_count - 2))
    assigned = [colors[0], colors[0], *colors[1:]]
    _fill_positions(grid, positions, assigned)
    return grid


def _draw_off_center_cluster(ctx) -> list[list[int]]:
    h, w = _draw_dimensions(ctx, "off_center_dimensions", wide=True)
    nominal = (w - 1) // 2
    axis_rng = ctx.draw_rng("off_center_axis")
    candidates = [
        axis
        for axis in range(4, w - 4)
        if abs(axis - nominal) >= 2 and min(axis, w - 1 - axis) >= 4
    ]
    if not candidates:
        raise ValueError(f"no off-center divider for width {w}")
    divider = axis_rng.choice(candidates)
    grid = full_grid(h, w, 0)
    _paint_divider(grid, divider)

    available_columns = sorted({c for _r, c in _available_left_positions(h, w, divider)})
    cluster_columns = [c for c in available_columns if c + 1 < divider]
    layout = ctx.draw_rng("off_center_layout")
    base_col = layout.choice(cluster_columns)
    base_row = layout.randrange(max(1, h - 1))
    base_row = min(base_row, h - 2)
    positions = [
        (base_row, base_col),
        (base_row, base_col + 1),
        (base_row + 1, base_col),
    ]
    target = {"easy": 6, "medium": 8, "hard": 10}.get(ctx.difficulty, 8)
    available = [
        pos
        for pos in _available_left_positions(h, w, divider)
        if pos not in positions
    ]
    positions.extend(layout.sample(available, target - len(positions)))

    color_rng = ctx.draw_rng("off_center_colors")
    assigned = [9, 9, color_rng.choice(tuple(c for c in _NONZERO_COLORS if c != 9))]
    assigned.extend(color_rng.choice(_NONZERO_COLORS) for _ in range(target - 3))
    _fill_positions(grid, positions, assigned)
    return grid


def _draw_edge_row_motif(ctx) -> list[list[int]]:
    h, w = _draw_dimensions(ctx, "edge_dimensions", odd_width=True)
    divider = (w - 1) // 2
    grid = full_grid(h, w, 0)
    _paint_divider(grid, divider)

    layout = ctx.draw_rng("edge_layout")
    middle = h // 2
    positions = [
        (0, 0),
        (h - 1, max(0, divider - 3)),
        (middle, divider - 2),
        (middle, divider - 1),
    ]
    target = {"easy": 8, "medium": 10, "hard": 14}.get(ctx.difficulty, 10)
    available = [
        pos
        for pos in _available_left_positions(h, w, divider)
        if pos not in positions
    ]
    positions.extend(layout.sample(available, target - len(positions)))

    color_rng = ctx.draw_rng("edge_colors")
    assigned = [color_rng.choice(_NONZERO_COLORS) for _ in positions]
    # Keep the guaranteed adjacent row pair visibly coherent.
    assigned[3] = assigned[2]
    _fill_positions(grid, positions, assigned)
    return grid


def _draw_preserved_right_noise(ctx) -> list[list[int]]:
    h, w = _draw_dimensions(ctx, "right_noise_dimensions", odd_width=True)
    divider = (w - 1) // 2
    grid = full_grid(h, w, 0)
    _paint_divider(grid, divider)

    layout = ctx.draw_rng("right_noise_layout")
    target = {"easy": 5, "medium": 7, "hard": 9}.get(ctx.difficulty, 7)
    # Guarantee an adjacent source pair, then scatter the rest.
    pair_row = layout.randrange(h)
    pair_col = layout.randrange(max(1, divider - 1))
    pair_col = min(pair_col, divider - 2)
    source_positions = [(pair_row, pair_col), (pair_row, pair_col + 1)]
    available = [
        pos
        for pos in _available_left_positions(h, w, divider)
        if pos not in source_positions
    ]
    source_positions.extend(layout.sample(available, target - 2))

    color_rng = ctx.draw_rng("right_noise_colors")
    source_colors = [color_rng.choice(_NONZERO_COLORS) for _ in source_positions]
    source_colors[1] = source_colors[0]
    _fill_positions(grid, source_positions, source_colors)

    destinations = {
        (row, _mirror_column(divider, column))
        for row, column in source_positions
    }
    source_set = set(source_positions)
    distractor_candidates = []
    for row in range(h):
        for column in range(divider + 1, w):
            reflected = _mirror_column(divider, column)
            if not 0 <= reflected < divider:
                continue
            if (row, column) in destinations or (row, reflected) in source_set:
                continue
            distractor_candidates.append((row, column))
    distractor_count = 2 if ctx.difficulty == "easy" else 3
    distractors = layout.sample(distractor_candidates, distractor_count)
    distractor_colors = [color_rng.choice(_NONZERO_COLORS) for _ in distractors]
    _fill_positions(grid, distractors, distractor_colors)
    return grid


_PROFILE_DRAWERS = {
    "canonical_sparse": _draw_canonical_sparse,
    "off_center_cluster": _draw_off_center_cluster,
    "edge_row_motif": _draw_edge_row_motif,
    "preserved_right_noise": _draw_preserved_right_noise,
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
        scheduled = PROFILE_SCHEDULE[(int(seed) + sample_index) % len(PROFILE_SCHEDULE)]
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    grid = _PROFILE_DRAWERS[profile](ctx)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"generated invalid {profile} scene: {errors}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the informative input grammar, including divider causality."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    h, w = len(grid), len(grid[0])
    dividers = _divider_columns(grid)
    if len(dividers) != 1:
        return [f"expected exactly one full-height color-5 divider, got {len(dividers)}"]
    divider = dividers[0]

    stray_gray = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if column != divider and grid[row][column] == 5
    ]
    if stray_gray:
        errors.append("color 5 appears outside the unique divider")

    sources = _source_cells(grid, divider)
    if len(sources) < 3:
        errors.append(f"expected at least three source cells, got {len(sources)}")
    if len({value for _row, _column, value in sources}) < 2:
        errors.append("source motif needs at least two colors")

    distances = {divider - column for _row, column, _value in sources}
    if len(distances) < 2:
        errors.append("source motif occupies fewer than two divider distances")

    for row, column, _value in sources:
        mirror = _mirror_column(divider, column)
        if not 0 <= mirror < w:
            errors.append(f"source at {(row, column)} mirrors out of bounds")
        elif grid[row][mirror] != 0:
            errors.append(
                f"mirror destination {(row, mirror)} is occupied before transformation"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact size/palette/multiplicity envelope of canonical inputs."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    spec = _CANONICAL_SPECS.get((h, w))
    if spec is None:
        return [f"dimensions {(h, w)} are not a canonical profile"]
    expected_divider, expected_cells, expected_colors = spec
    divider = _divider(grid)
    if divider != expected_divider:
        errors.append(
            f"divider {divider} does not match canonical column {expected_divider}"
        )
    if _right_cells(grid, divider):
        errors.append("canonical inputs have a blank right side")
    sources = _source_cells(grid, divider)
    if len(sources) != expected_cells:
        errors.append(
            f"canonical profile expects {expected_cells} source cells, got {len(sources)}"
        )
    counts = Counter(value for _row, _column, value in sources)
    if len(counts) != expected_colors:
        errors.append(
            f"canonical profile expects {expected_colors} source colors, got {len(counts)}"
        )
    if sorted(counts.values()) != [1] * max(0, expected_colors - 1) + [2]:
        errors.append("canonical source palette has exactly one color repeated twice")
    return errors


def expected_output(grid) -> list[list[int]]:
    """Python audit mirror of the pinned Racket rule; never used for labels."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    divider = _divider(grid)
    output = [list(row) for row in grid]
    width = len(output[0])
    for row, column, value in _source_cells(grid, divider):
        mirror = _mirror_column(divider, column)
        if 0 <= mirror < width:
            output[row][mirror] = value
    return output


_official_python_mirror = expected_output


def _source_positions(grid) -> set[tuple[int, int]]:
    try:
        return {(row, column) for row, column, _value in _source_cells(grid)}
    except ValueError:
        return set()


def _has_connected_sources(grid) -> bool:
    positions = _source_positions(grid)
    return any(
        (row + dr, column + dc) in positions
        for row, column in positions
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _has_multiple_source_distances(grid) -> bool:
    try:
        divider = _divider(grid)
    except ValueError:
        return False
    return len({divider - column for _row, column, _value in _source_cells(grid, divider)}) >= 2


def _has_color_9_source(grid) -> bool:
    try:
        return any(value == 9 for _row, _column, value in _source_cells(grid))
    except ValueError:
        return False


def _has_more_than_six_sources(grid) -> bool:
    try:
        return len(_source_cells(grid)) > 6
    except ValueError:
        return False


def _divider_off_center(grid) -> bool:
    try:
        return _divider(grid) != (len(grid[0]) - 1) // 2
    except (ValueError, TypeError, IndexError):
        return False


def _has_right_distractors(grid) -> bool:
    try:
        return bool(_right_cells(grid))
    except ValueError:
        return False


def _is_edge_row_motif(grid) -> bool:
    if self_check(grid) or _has_right_distractors(grid):
        return False
    sources = _source_cells(grid)
    if len(sources) <= 6:
        return False
    h = len(grid)
    rows = Counter(row for row, _column, _value in sources)
    return 0 in rows and h - 1 in rows and max(rows.values(), default=0) >= 2


def _classify_profile(grid) -> str | None:
    if self_check(grid):
        return None
    if _has_right_distractors(grid):
        return "preserved_right_noise"
    if strict_canonical_like(grid) == []:
        return "canonical_sparse"
    if _divider_off_center(grid) and _has_connected_sources(grid):
        return "off_center_cluster"
    if _is_edge_row_motif(grid):
        return "edge_row_motif"
    return None


def observe_overrides(grid) -> dict[str, str]:
    """Recover the single exact public axis from visible grid semantics."""
    profile = _classify_profile(grid)
    return {"scene_profile": profile} if profile is not None else {}


def semantic_observables(grid) -> dict[str, Any]:
    if _grid_errors(grid):
        return {"valid": False}
    try:
        divider = _divider(grid)
        sources = _source_cells(grid, divider)
        right = _right_cells(grid, divider)
    except ValueError:
        return {"valid": False}
    return {
        **observe_overrides(grid),
        "valid": self_check(grid) == [],
        "height": len(grid),
        "width": len(grid[0]),
        "divider": divider,
        "source_cells": len(sources),
        "source_colors": len({value for _row, _column, value in sources}),
        "source_distances": len({divider - column for _row, column, _value in sources}),
        "connected_source_cells": _has_connected_sources(grid),
        "color_9_source": _has_color_9_source(grid),
        "right_distractors": len(right),
    }


def _copy_selected_sources(
    grid,
    predicate: Callable[[int, tuple[int, int, int], list[tuple[int, int, int]]], bool],
    *,
    axis: int | None = None,
) -> list[list[int]]:
    divider = _divider(grid)
    mirror_axis = divider if axis is None else axis
    output = [list(row) for row in grid]
    width = len(output[0])
    sources = _source_cells(grid, divider)
    for index, source in enumerate(sources):
        row, column, value = source
        if not predicate(index, source, sources):
            continue
        mirror = _mirror_column(mirror_axis, column)
        if 0 <= mirror < width:
            output[row][mirror] = value
    return output


def _rival_nominal_midline(grid):
    nominal = (len(grid[0]) - 1) // 2
    return _copy_selected_sources(grid, lambda _i, _s, _all: True, axis=nominal)


def _rival_clear_unmatched_right(grid):
    divider = _divider(grid)
    output = [list(row) for row in grid]
    for row in range(len(output)):
        for column in range(divider + 1, len(output[0])):
            output[row][column] = 0
    for row, column, value in _source_cells(grid, divider):
        output[row][_mirror_column(divider, column)] = value
    return output


def _rival_mirror_both_sides(grid):
    divider = _divider(grid)
    output = [list(row) for row in grid]
    width = len(output[0])
    cells = [
        (row, column, int(grid[row][column]))
        for row in range(len(grid))
        for column in range(width)
        if column != divider and grid[row][column] not in (0, 5)
    ]
    for row, column, value in cells:
        mirror = _mirror_column(divider, column)
        if 0 <= mirror < width:
            output[row][mirror] = value
    return output


def _rival_require_blank_right(grid):
    return [list(row) for row in grid] if _has_right_distractors(grid) else expected_output(grid)


def _rival_ignore_color_9(grid):
    return _copy_selected_sources(
        grid, lambda _i, source, _all: source[2] != 9
    )


def _rival_cap_at_six_sources(grid):
    return _copy_selected_sources(grid, lambda index, _source, _all: index < 6)


def _rival_isolated_sources_only(grid):
    positions = _source_positions(grid)

    def isolated(_index, source, _all):
        row, column, _value = source
        return not any(
            (row + dr, column + dc) in positions
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )

    return _copy_selected_sources(grid, isolated)


def _rival_nearest_distance_only(grid):
    divider = _divider(grid)
    sources = _source_cells(grid, divider)
    nearest = min(divider - column for _row, column, _value in sources)
    return _copy_selected_sources(
        grid,
        lambda _index, source, _all: divider - source[1] == nearest,
    )


SEMANTIC_RIVALS = {
    "nominal_midline_instead_of_divider": _rival_nominal_midline,
    "clear_unmatched_right_cells": _rival_clear_unmatched_right,
    "mirror_both_sides": _rival_mirror_both_sides,
    "require_blank_right_half": _rival_require_blank_right,
    "ignore_color_9": _rival_ignore_color_9,
    "cap_at_six_source_cells": _rival_cap_at_six_sources,
    "isolated_sources_only": _rival_isolated_sources_only,
    "nearest_distance_only": _rival_nearest_distance_only,
}

CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "nominal_midline_instead_of_divider",
        "clear_unmatched_right_cells",
        "mirror_both_sides",
        "require_blank_right_half",
        "ignore_color_9",
        "cap_at_six_source_cells",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "off_center_divider": _divider_off_center,
    "right_side_distractors": _has_right_distractors,
    "color_9_source": _has_color_9_source,
    "more_than_six_sources": _has_more_than_six_sources,
    "connected_source_cells": _has_connected_sources,
    "multiple_source_distances": _has_multiple_source_distances,
}

WITNESS_RIVALS = {
    "off_center_divider": ["nominal_midline_instead_of_divider"],
    "right_side_distractors": [
        "clear_unmatched_right_cells",
        "mirror_both_sides",
        "require_blank_right_half",
    ],
    "color_9_source": ["ignore_color_9"],
    "more_than_six_sources": ["cap_at_six_source_cells"],
    "connected_source_cells": ["isolated_sources_only"],
    "multiple_source_distances": ["nearest_distance_only"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic four-example schedule to semantic tooling."""
    del difficulty
    return PROFILE_SCHEDULE[(int(seed) + sample_index) % len(PROFILE_SCHEDULE)]


def _normalized_grid(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo lesson to eliminate all named competitors."""
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
            continue
        reasons.append(f"named rival remains viable on demos: {name}")
    return reasons


def mutation_fixtures():
    """Task-local malformed teaching examples that self_check must reject."""
    no_divider = full_grid(9, 11, 0)
    no_divider[2][2] = 4

    no_sources = full_grid(9, 11, 0)
    _paint_divider(no_sources, 5)

    one_distance = [row[:] for row in no_sources]
    one_distance[1][3] = 2
    one_distance[3][3] = 3
    one_distance[5][3] = 4

    occupied_destination = [row[:] for row in no_sources]
    occupied_destination[1][2] = 2
    occupied_destination[2][3] = 3
    occupied_destination[3][1] = 4
    occupied_destination[1][8] = 7

    duplicate_divider = [row[:] for row in no_sources]
    _paint_divider(duplicate_divider, 6)
    duplicate_divider[1][2] = 2
    duplicate_divider[2][3] = 3
    duplicate_divider[3][1] = 4

    return [
        ("no_divider", no_divider),
        ("no_sources", no_sources),
        ("one_source_distance", one_distance),
        ("occupied_mirror_destination", occupied_destination),
        ("duplicate_divider", duplicate_divider),
    ]
