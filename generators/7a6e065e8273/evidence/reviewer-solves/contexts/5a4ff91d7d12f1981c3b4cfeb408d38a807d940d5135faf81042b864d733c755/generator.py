"""Curriculum generator for ARC task 7a6e065e8273, Halo Without the Center.

Every nonzero input cell is a center.  The selected rule creates a fresh
background grid, paints the four in-bounds cardinal neighbours of every center
cyan (8), and does not copy the centers themselves.  Center color is therefore
a distractor, not the output color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a6e065e8273"
TASK_ID = "7a6e065e8273"
VERSION = "3.1.0"
RULE_HASH = "1724b71ea895"

SUMMARY = (
    "A 6..12 by 6..12 zero-background grid contains 1..6 non-adjacent "
    "interior seed cells.  Seed colors may repeat and may be color 5 or other "
    "non-cyan colors.  The output is a fresh zero grid containing color-8 "
    "cells at the four cardinal neighbors of every seed; original seed "
    "centers are omitted.  Overlapping halos are unioned."
)

INVARIANTS = [
    "input has one to six nonzero interior centers",
    "centers are never orthogonally adjacent",
    "all output halo arms are cyan (8), regardless of center color",
    "the output starts from a fresh background and omits every center",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "6..12; strongly favors canonical 8 and 9",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "6..12; strongly favors canonical 8 and 9",
        "valid": "6..12",
    },
    "seed_count": {
        "type": "int",
        "default": "1..6; difficulty changes weights, not support",
        "valid": "1..6",
    },
    "color_profile": {
        "type": "str",
        "default": "mostly non-canonical colors",
        "valid": "canonical|monochrome|mixed",
    },
}

# A mixed profile is observable only when at least two centers exist.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"seed_count": 1, "color_profile": "mixed"},
]

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SOURCE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_MONOCHROME_COLORS = (1, 2, 3, 4, 6, 7, 9)
# Duplicates are deliberate weights.  The complete documented domain remains
# available to exact overrides in every difficulty band.
_DIMENSION_OPTIONS = tuple([8] * 24 + [9] * 24 + [6, 7, 10, 11, 12])
_PROFILE_OPTIONS = tuple(["canonical"] + ["monochrome"] * 4 + ["mixed"] * 5)
_SINGLE_PROFILE_OPTIONS = tuple(["canonical"] + ["monochrome"] * 8)
_NONCANONICAL_PROFILE_OPTIONS = tuple(["monochrome"] * 4 + ["mixed"] * 5)
_SINGLE_NONCANONICAL_PROFILE_OPTIONS = tuple(["monochrome"] * 8)


def _count_options(difficulty):
    if difficulty == "easy":
        return tuple([1] * 6 + [2] * 5 + [3] * 3 + [4, 5, 6])
    if difficulty == "hard":
        return tuple([1, 2] + [3] * 2 + [4] * 3 + [5] * 4 + [6] * 5)
    return tuple([1] * 3 + [2] * 3 + [3] * 2 + [4] * 2 + [5, 6])


def _validate_override_types(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "seed_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    profile = overrides.get("color_profile")
    if profile is not None and type(profile) is not str:
        raise ValueError(
            f"color_profile must be a string, not {type(profile).__name__}"
        )
    if overrides.get("seed_count") == 1 and overrides.get("color_profile") == "mixed":
        raise ValueError("seed_count=1 and color_profile='mixed' are incompatible")


def _seed_colors(ctx, count, profile):
    if profile == "canonical":
        return [5] * count
    if profile == "monochrome":
        color = ctx.draw_choice("monochrome_color", _MONOCHROME_COLORS)
        return [color] * count
    if profile != "mixed":
        raise ValueError(f"unsupported color_profile {profile!r}")
    if count < 2:
        raise ValueError("seed_count=1 and color_profile='mixed' are incompatible")
    rng = ctx.draw_rng("mixed_colors")
    distinct = min(count, 3)
    palette = rng.sample(list(_SOURCE_COLORS), distinct)
    colors = list(palette)
    colors.extend(rng.choice(palette) for _ in range(count - distinct))
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one exact, observable member of the reviewed curriculum."""
    _validate_override_types(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_choice("grid_h", _DIMENSION_OPTIONS)
    width = ctx.draw_choice("grid_w", _DIMENSION_OPTIONS)

    counts = _count_options(difficulty)
    # A profile-only exact override must not fail stochastically because a
    # one-center default happened to be drawn.
    if overrides.get("color_profile") == "mixed" and overrides.get("seed_count") is None:
        counts = tuple(value for value in counts if value >= 2)
    count = ctx.draw_choice("seed_count", counts)
    if "color_profile" in overrides:
        profiles = _SINGLE_PROFILE_OPTIONS if count == 1 else _PROFILE_OPTIONS
    elif sample_index % 2 == 0:
        # Lessons are assembled from four consecutive sample indexes.  Making
        # every even default sample non-canonical guarantees that any choice
        # of one query still leaves at least one non-five demonstration, which
        # refutes the canonical-fitting "only color 5 matters" shortcut.
        profiles = (
            _SINGLE_NONCANONICAL_PROFILE_OPTIONS
            if count == 1
            else _NONCANONICAL_PROFILE_OPTIONS
        )
    else:
        profiles = _SINGLE_PROFILE_OPTIONS if count == 1 else _PROFILE_OPTIONS
    profile = ctx.draw_choice("color_profile", profiles)

    parity = ctx.draw_choice("layout_parity", (0, 1))
    candidates = [
        (r, c)
        for r in range(1, height - 1)
        for c in range(1, width - 1)
        if (r + c) % 2 == parity
    ]
    if len(candidates) < count:
        raise RuntimeError("declared canvas cannot fit the requested centers")
    positions = ctx.draw_rng("center_positions").sample(candidates, count)
    colors = _seed_colors(ctx, count, profile)

    grid = full_grid(height, width, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    return grid


def _source_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def observe_overrides(grid):
    """Recover every public exact axis from returned pixels."""
    points = _source_cells(grid)
    colors = {value for _r, _c, value in points}
    if colors == {5}:
        profile = "canonical"
    elif len(colors) == 1:
        profile = "monochrome"
    else:
        profile = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "seed_count": len(points),
        "color_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the generator's lawful source manifold and canonical inputs."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["expected a rectangular grid"]
    height = len(grid)
    errors = []
    if not (6 <= height <= 12 and 6 <= width <= 12):
        errors.append(f"grid dimensions must each be in 6..12, got {height}x{width}")
    allowed = {0, *_SOURCE_COLORS}
    if any(type(value) is not int or value not in allowed for row in grid for value in row):
        errors.append("cells must be integer colors 0,1,2,3,4,5,6,7,9; cyan 8 is output-only")
        return errors

    points = _source_cells(grid)
    if not (1 <= len(points) <= 6):
        errors.append(f"expected 1..6 center cells, got {len(points)}")
    if any(r in (0, height - 1) or c in (0, width - 1) for r, c, _ in points):
        errors.append("all centers must be interior so four cardinal arms fit")
    occupied = {(r, c) for r, c, _value in points}
    if any(
        (r + dr, c + dc) in occupied
        for r, c in occupied
        for dr, dc in _CARDINAL
    ):
        errors.append("centers must not be orthogonally adjacent")
    return errors


def strict_canonical_like(grid):
    """All generated samples and all canonical inputs satisfy this predicate."""
    return self_check(grid)


def _paint_halos(grid, *, select=lambda value: True, preserve_colors=False, keep_centers=False):
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    selected = [cell for cell in _source_cells(grid) if select(cell[2])]
    for r, c, value in selected:
        for dr, dc in _CARDINAL:
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value if preserve_colors else 8
    if keep_centers:
        for r, c, _value in selected:
            out[r][c] = 8
    return out


def _fixed_cyan_halos(grid):
    return _paint_halos(grid)


def _only_color_five_centers(grid):
    return _paint_halos(grid, select=lambda value: value == 5)


def _preserve_center_colors(grid):
    return _paint_halos(grid, preserve_colors=True)


def _keep_cyan_centers(grid):
    return _paint_halos(grid, keep_centers=True)


SEMANTIC_RIVALS = {
    "only_color_five_centers": _only_color_five_centers,
    "preserve_center_colors": _preserve_center_colors,
    "keep_cyan_centers": _keep_cyan_centers,
}

SEMANTIC_WITNESSES = {
    "non_five_center_matters": (
        lambda grid: _only_color_five_centers(grid) != _fixed_cyan_halos(grid)
    ),
    "output_color_is_fixed_cyan": (
        lambda grid: _preserve_center_colors(grid) != _fixed_cyan_halos(grid)
    ),
    "centers_are_removed": (
        lambda grid: _keep_cyan_centers(grid) != _fixed_cyan_halos(grid)
    ),
}

WITNESS_RIVALS = {
    "non_five_center_matters": ["only_color_five_centers"],
    "output_color_is_fixed_cyan": ["preserve_center_colors"],
    "centers_are_removed": ["keep_cyan_centers"],
}

# This shortcut fits every canonical pair because all canonical centers are 5;
# non-five generated examples are therefore essential training evidence.
CANONICAL_SHORTCUTS = {
    "only_color_five_centers": _only_color_five_centers,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
MIN_STRICT_FRAC = 1.0
