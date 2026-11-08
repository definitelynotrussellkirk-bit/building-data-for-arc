"""Input sampler for divider reflection, arc_puzzle_bank_21_set9_s:S9_E5.

The selected Racket authority detects the unique full-height color-5 divider
and mirrors every colored source cell on its left to the equidistant cell on
its right.  This sampler deliberately includes off-center dividers, colors not
present in the three canonical inputs, and two- and three-color examples in both palette families so lessons
refute centered-divider, canonical-color-only, first-two-colors, and
palette/count-correlation shortcuts.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9baf979683ef"
TASK_ID = GENERATOR_ID
RULE_HASH = "1fce392f92a1"
VERSION = "3.2.0"
SUMMARY = (
    "A 0-background grid contains one full-height color-5 divider and 3..10 "
    "colored source cells strictly to its left.  The divider may be centered "
    "or off-center, and every source has an in-bounds reflected destination. "
    "The output preserves the input and copies each source to the same row, "
    "equidistant on the divider's right.  A four-profile schedule orthogonally "
    "crosses centered/off-center geometry, canonical/extended palettes, and "
    "two/three object colors."
)

INVARIANTS = [
    "background is color 0 and exactly one full-height divider is color 5",
    "all non-background, non-divider cells begin strictly left of the divider",
    "every source cell has an in-bounds mirror location to the divider's right",
    "each input uses two or three object colors and 3..10 source cells",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "5..14; canonical curriculum favors 7 or 8",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "7..17; canonical curriculum favors 9, 11, or 13",
        "valid": "7..17",
    },
    "left_cell_count": {
        "type": "int",
        "default": "3..10; canonical curriculum favors 5",
        "valid": "3..10",
    },
}
# Every advertised combination is constructive, including 5x7 with 10 cells.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CANONICAL_COLORS = (2, 3, 4)
_EXTENDED_COLORS = (1, 6, 7, 8, 9)
_ALL_OBJECT_COLORS = frozenset(_CANONICAL_COLORS + _EXTENDED_COLORS)
_CANONICAL_SHAPES = ((7, 11), (8, 9), (7, 13))
SCHEDULE_PROFILES = (
    "center_canonical_2",
    "center_extended_3",
    "offcenter_canonical_3",
    "offcenter_extended_2",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """A four-example lesson window always visits every teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _weighted_axis(ctx, name, lo, hi, *, anchor, favored=()):
    """Draw exactly from the full declared domain while biasing a curriculum.

    Keeping every legal value in ``options`` is important: an explicit override
    remains valid in every difficulty band, while repeated anchors only alter
    default sampling frequency.
    """
    options = list(range(lo, hi + 1))
    options.extend([anchor] * 20)
    options.extend(favored)
    return ctx.draw_choice(name, options)


def _draw_dimensions(ctx, sample_index, difficulty):
    anchor_h, anchor_w = _CANONICAL_SHAPES[int(sample_index) % len(_CANONICAL_SHAPES)]
    if difficulty == "easy":
        favored_h = tuple(range(5, 9)) * 2
        favored_w = tuple(range(7, 12)) * 2
    elif difficulty == "hard":
        favored_h = tuple(range(10, 15)) * 2
        favored_w = tuple(range(13, 18)) * 2
    else:
        favored_h = ()
        favored_w = ()
    h = _weighted_axis(ctx, "grid_h", 5, 14, anchor=anchor_h, favored=favored_h)
    w = _weighted_axis(ctx, "grid_w", 7, 17, anchor=anchor_w, favored=favored_w)
    return h, w


def _draw_count(ctx, difficulty):
    if difficulty == "easy":
        favored = (3, 4, 5) * 2
    elif difficulty == "hard":
        favored = (7, 8, 9, 10) * 2
    else:
        favored = ()
    return _weighted_axis(
        ctx, "left_cell_count", 3, 10, anchor=5, favored=favored
    )


def _source_col_lo(width, divider):
    """Smallest left column whose reflection remains in bounds."""
    return max(0, 2 * divider - (width - 1))


def _divider_candidates(height, width, count, *, centered):
    center = width // 2
    candidates = []
    for divider in range(2, width - 2):
        source_width = divider - _source_col_lo(width, divider)
        if height * source_width < count:
            continue
        if (divider == center) == centered:
            candidates.append(divider)
    return candidates


def _choose_divider(ctx, height, width, count, profile):
    centered = profile.startswith("center_")
    candidates = _divider_candidates(height, width, count, centered=centered)
    if not candidates:
        # The declared domain is constructive.  This fallback is defensive and
        # should be unreachable; failing loudly is safer than returning a grid
        # that lies about its scheduled profile.
        raise RuntimeError(
            f"no {'centered' if centered else 'off-center'} divider fits "
            f"h={height}, w={width}, count={count}"
        )
    return ctx.draw_rng("divider_col").choice(candidates)


def _connected_positions(candidates, count, rng):
    allowed = set(candidates)
    start = rng.choice(candidates)
    chosen = {start}
    while len(chosen) < count:
        frontier = sorted({
            (nr, nc)
            for r, c in chosen
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if (nr, nc) in allowed and (nr, nc) not in chosen
        })
        if not frontier:
            raise RuntimeError("connected placement exhausted a rectangular source region")
        chosen.add(rng.choice(frontier))
    return list(chosen)


def _snake_positions(height, col_lo, divider):
    path = []
    for row in range(height):
        columns = list(range(col_lo, divider))
        if row % 2:
            columns.reverse()
        path.extend((row, col) for col in columns)
    return path


def _choose_positions(ctx, height, divider, col_lo, count, sample_index):
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(col_lo, divider)
    ]
    # Four scattered slots preserve the canonical task's separated-object
    # morphology; one connected and one snake slot retain lawful component
    # diversity.  The period is coprime enough with the four-profile teaching
    # schedule (LCM 12) that no palette/geometry profile owns one layout type.
    mode = int(sample_index) % 6
    rng = ctx.draw_rng("source_layout")
    if mode < 4:
        return rng.sample(candidates, count)
    if mode == 4:
        return _connected_positions(candidates, count, rng)
    path = _snake_positions(height, col_lo, divider)
    start = rng.randrange(len(path) - count + 1)
    return path[start:start + count]


def _choose_colors(ctx, profile):
    palette = _CANONICAL_COLORS if "_canonical_" in profile else _EXTENDED_COLORS
    color_count = int(profile.rsplit("_", 1)[1])
    return ctx.draw_rng("object_colors").choice(
        tuple(combinations(palette, color_count))
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    height, width = _draw_dimensions(ctx, sample_index, difficulty)
    count = _draw_count(ctx, difficulty)
    divider = _choose_divider(ctx, height, width, count, profile)
    col_lo = _source_col_lo(width, divider)
    positions = _choose_positions(
        ctx, height, divider, col_lo, count, sample_index
    )
    colors = _choose_colors(ctx, profile)

    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 5
    # Sorting makes color assignment stable even when a placement helper uses a
    # set internally.  Alternation guarantees both selected colors are visible.
    for index, (row, col) in enumerate(sorted(positions)):
        grid[row][col] = colors[index % len(colors)]
    return grid


def _divider_col(grid):
    height, width = len(grid), len(grid[0])
    columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(columns) != 1:
        raise ValueError(
            f"expected exactly one full-height color-5 divider, found {columns}"
        )
    return columns[0]


def _source_cells(grid, divider):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5) and col < divider
    ]


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    divider = _divider_col(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "left_cell_count": len(_source_cells(grid, divider)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    height, width = len(grid), len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["ragged grid"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]

    errors = []
    if not 5 <= height <= 14:
        errors.append(f"grid_h={height} outside [5,14]")
    if not 7 <= width <= 17:
        errors.append(f"grid_w={width} outside [7,17]")
    try:
        divider = _divider_col(grid)
    except ValueError as exc:
        return errors + [str(exc)]
    if not 2 <= divider <= width - 3:
        errors.append(
            f"divider column {divider} must leave at least two columns per side"
        )
    stray_fives = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5 and col != divider
    ]
    if stray_fives:
        errors.append(f"color-5 cells outside divider: {stray_fives[:3]}")

    sources = _source_cells(grid, divider)
    right = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5) and col > divider
    ]
    if not 3 <= len(sources) <= 10:
        errors.append(f"left_cell_count={len(sources)} outside [3,10]")
    if right:
        errors.append(f"non-divider cells already on right side: {right[:3]}")
    colors = {value for _, _, value in sources}
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected two or three object colors, found {sorted(colors)}")
    if colors and not (
        colors <= set(_CANONICAL_COLORS)
        or colors <= set(_EXTENDED_COLORS)
    ):
        errors.append(
            "object colors must come wholly from canonical {2,3,4} or "
            f"extended {list(_EXTENDED_COLORS)} palette; found {sorted(colors)}"
        )
    bad_mirrors = [
        (row, col)
        for row, col, _ in sources
        if not divider < 2 * divider - col < width
    ]
    if bad_mirrors:
        errors.append(
            f"source cells have invalid mirror locations: {bad_mirrors[:3]}"
        )
    return errors


def strict_canonical_like(grid):
    """Lawful divider-reflection instances in this sampler's declared domain."""
    return self_check(grid)


def _mirror_with_divider(grid, divider, *, allowed_colors=None):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(divider):
            value = grid[row][col]
            target = 2 * divider - col
            if (
                value not in (0, 5)
                and (allowed_colors is None or value in allowed_colors)
                and 0 <= target < width
            ):
                out[row][target] = value
    return out


def _assume_center_divider(grid):
    """RIVAL: incorrectly mirror around floor(width/2), not the 5-divider."""
    return _mirror_with_divider(grid, len(grid[0]) // 2)


def _canonical_colors_only(grid):
    """RIVAL: incorrectly mirror only colors present in canonical examples."""
    return _mirror_with_divider(
        grid, _divider_col(grid), allowed_colors=set(_CANONICAL_COLORS)
    )


def _first_two_colors_only(grid):
    """RIVAL: incorrectly process at most two distinct source colors."""
    divider = _divider_col(grid)
    colors = sorted({
        value for _, _, value in _source_cells(grid, divider)
    })[:2]
    return _mirror_with_divider(
        grid, divider, allowed_colors=set(colors)
    )


def _has_off_center_divider(grid):
    return _divider_col(grid) != len(grid[0]) // 2


def _uses_extended_palette(grid):
    divider = _divider_col(grid)
    return any(
        value not in _CANONICAL_COLORS
        for _, _, value in _source_cells(grid, divider)
    )


def _uses_three_or_more_colors(grid):
    divider = _divider_col(grid)
    return len({value for _, _, value in _source_cells(grid, divider)}) >= 3


SEMANTIC_WITNESSES = {
    "off_center_divider": _has_off_center_divider,
    "extended_palette": _uses_extended_palette,
    "three_or_more_colors": _uses_three_or_more_colors,
}
SEMANTIC_RIVALS = {
    "assume_center_divider": _assume_center_divider,
    "canonical_colors_only": _canonical_colors_only,
    "first_two_colors_only": _first_two_colors_only,
}
WITNESS_RIVALS = {
    "off_center_divider": ["assume_center_divider"],
    "extended_palette": ["canonical_colors_only"],
    "three_or_more_colors": ["first_two_colors_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
