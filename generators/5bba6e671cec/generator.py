"""Canonical-scale inputs for ARC task 880c1354.

Colors 4 and 7 form a fixed frame. Every other color is treated as one region,
even when the color is zero or the frame splits it into several components.
Order those colors by the angle of their whole-color centroid around the grid
center (north=0, clockwise positive), then recolor every region by one clockwise
step. This module generates INPUTS ONLY; labels remain authoritative Racket.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5bba6e671cec"
TASK_ID = "5bba6e671cec"
RULE_HASH = "f90a485d851e"
VERSION = "3.2.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.90

SUMMARY = (
    "An 8x8 color-4/color-7 frame partitions two to four large color regions. "
    "Treat every non-{4,7} color, including zero when present, as a region. "
    "Sort whole-color centroids clockwise around the grid center and move each "
    "color one clockwise position while preserving every cell and both frame "
    "colors. Four scheduled profiles redundantly expose row-order, first-cell, quadrant, "
    "zero-background, and two-region cases so every three-demo query rotation "
    "still identifies the intended rule."
)
INVARIANTS = [
    "the 8x8 geometry and all color-4/color-7 frame cells are preserved",
    "each non-frame color is rotated as one semantic region, even if disconnected",
    "color 0 is not background when it occurs outside the fixed frame",
    "every four-pair lesson covers palette sizes 6, 5, and 4",
    "removing any one pair still leaves counterevidence for every declared rival",
    "explicit overrides are exact and do not change the selected Racket authority",
]
AXES = {
    "region_count": {
        "type": "int",
        "default": "scheduled 3, 4, 3, 2",
        "valid": "2..4",
    },
    "include_zero": {
        "type": "bool",
        "default": "scheduled true, false, true, false",
        "valid": "true|false",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PERIOD = 4
LESSON_SCHEDULE_PERIOD = SCHEDULE_PERIOD
SCHEDULE_PROFILES = (
    "dual_zero_three",
    "row_four",
    "quadrant_zero_three",
    "paired_two",
)
_PROFILE_AXES = {
    "dual_zero_three": (3, True),
    "row_four": (4, False),
    "quadrant_zero_three": (3, True),
    "paired_two": (2, False),
}
_DIFFICULTY_PHASE = {None: 0, "easy": 0, "medium": 1, "hard": 2}

# Dots are region cells; 4 and 7 are the unchanged frame. These masks are
# canonical-scale structural templates, not replayed canonical input grids.
_FRAME_TEMPLATES = (
    (
        "..7447..",
        ".744447.",
        "74444447",
        "44444447",
        "7444777.",
        ".7447...",
        "..747...",
        "...77...",
    ),
    (
        "..7447..",
        ".74447..",
        "744447..",
        ".74447..",
        "..7447..",
        "...747..",
        "....77..",
        ".....7..",
    ),
    (
        "........",
        "........",
        "7777777.",
        "74444447",
        "74444777",
        "74777...",
        "77......",
        "7.......",
    ),
    (
        "..777...",
        "..7447..",
        ".74447..",
        "744447..",
        "444447..",
        "777747..",
        "....7...",
        "....7...",
    ),
)

# (template index, sector-boundary step out of 96, angle-warp variant).
# The dual profile falsifies both canonical-fitting order shortcuts. The row
# and quadrant profiles redundantly falsify one each, so holding out any one of
# the four lesson pairs cannot remove all counterevidence for a rival.
_GEOMETRY_CANDIDATES = {
    "dual_zero_three": {
        "easy": ((2, 0, 0),),
        "medium": ((2, 0, 0),),
        "hard": ((2, 0, 0),),
    },
    "row_four": {
        "easy": ((1, 0, 0), (1, 8, 0), (1, 22, 0)),
        "medium": ((0, 7, 0), (0, 28, 0), (2, 10, 0)),
        "hard": ((3, 31, 0), (3, 55, 0), (2, 58, 0)),
    },
    "quadrant_zero_three": {
        "easy": ((2, 0, 0), (2, 26, 0), (2, 31, 0)),
        "medium": ((2, 58, 0), (2, 61, 0), (2, 64, 0)),
        "hard": ((2, 90, 0), (2, 93, 0), (2, 22, 2)),
    },
    "paired_two": {
        "easy": ((1, 0, 0), (1, 8, 0), (1, 16, 0)),
        "medium": ((3, 12, 0), (3, 24, 0), (3, 36, 0)),
        "hard": ((1, 40, 0), (1, 48, 0), (3, 60, 0)),
    },
}
_NONFRAME_NONZERO = (1, 2, 3, 5, 6, 8, 9)
_FRAME_COLORS = frozenset((4, 7))
_TWO_PI = 2.0 * math.pi


def schedule_profile(seed, sample_index, difficulty=None):
    """A four-slot cycle; each full three-demo/one-query lesson is complete."""
    if difficulty not in _DIFFICULTY_PHASE:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be integers")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    phase = _DIFFICULTY_PHASE[difficulty]
    return SCHEDULE_PROFILES[(seed + sample_index + phase) % SCHEDULE_PERIOD]


def _axis(ctx, name, default, legal):
    """Record one exact public axis while retaining its full override domain."""
    options = legal if name in ctx.overrides else (default,)
    return ctx.draw_choice(name, options)


def _validate_call(difficulty, overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in _DIFFICULTY_PHASE:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if "region_count" in overrides:
        value = overrides["region_count"]
        if type(value) is not int:
            raise TypeError("region_count must be an integer")
        if not 2 <= value <= 4:
            raise ValueError("region_count must be in 2..4")
    if "include_zero" in overrides and type(overrides["include_zero"]) is not bool:
        raise TypeError("include_zero must be a boolean")


def _angle_at(r, c, h=8, w=8):
    return math.atan2(c - (w - 1) / 2.0, -(r - (h - 1) / 2.0)) % _TWO_PI


def _warped_angle(angle, r, warp):
    if warp == 0:
        return angle
    if warp == 1:
        return (angle + 0.16 * math.sin(2.0 * angle)) % _TWO_PI
    if warp == 2:
        return (angle + 0.24 * math.sin(3.0 * angle)) % _TWO_PI
    if warp == 3:
        return (angle + 0.15 * (r - 3.5) / 3.5) % _TWO_PI
    raise ValueError(f"unknown angle warp {warp}")


def _sector_grid(template_index, region_count, offset_step, warp):
    template = _FRAME_TEMPLATES[template_index]
    offset = _TWO_PI * offset_step / 96.0
    sector_width = _TWO_PI / region_count
    grid = []
    for r, source_row in enumerate(template):
        row = []
        for c, cell in enumerate(source_row):
            if cell != ".":
                row.append(int(cell))
                continue
            angle = _warped_angle(_angle_at(r, c), r, warp)
            sector = int(((angle - offset) % _TWO_PI) / sector_width)
            row.append(min(sector, region_count - 1))
        grid.append(row)
    present = {value for row in grid for value in row if value not in _FRAME_COLORS}
    if present != set(range(region_count)):
        raise RuntimeError(
            f"geometry omitted a sector: wanted {region_count}, observed {sorted(present)}"
        )
    return grid


def _apply_profile_geometry(profile, grid, region_count):
    # Template 2 / offset 0 already defeats the fixed-quadrant shortcut. Moving
    # one top-row cell from sector 2 to sector 1 also makes row-major first
    # occurrence predict a different cycle, without changing centroid order.
    if profile == "dual_zero_three":
        grid[0][3] = 1
    elif profile == "quadrant_zero_three":
        # Both coordinates are non-frame cells in template 2. One remote
        # region pixel changes its first-cell angle without changing the
        # whole-color cycle. This supplies a second first-cell counterexample
        # when the dual profile is held out as the query.
        grid[0][1] = grid[7][3]
    present = {value for row in grid for value in row if value not in _FRAME_COLORS}
    if present != set(range(region_count)):
        raise RuntimeError(
            f"profile mutation omitted a sector: wanted {region_count}, observed {sorted(present)}"
        )
    return grid


def _region_palette(ctx, region_count, include_zero):
    n_nonzero = region_count - int(include_zero)
    selected = sorted(
        ctx.draw_distinct_colors(
            "region_nonzero_colors", n=n_nonzero, exclude=(0, 4, 7)
        )
    )
    colors = ([0] if include_zero else []) + selected
    # A nontrivial cyclic order prevents numeric-color order from imitating
    # geometry whenever there are at least three regions.
    permutations = {
        2: (0, 1),
        3: (0, 2, 1),
        4: (0, 2, 1, 3),
    }
    ordered = [colors[index] for index in permutations[region_count]]
    phase = ctx.draw_int("region_color_phase", 0, region_count - 1)
    return ordered[phase:] + ordered[:phase]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be integers")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_count, default_zero = _PROFILE_AXES[profile]
    region_count = _axis(ctx, "region_count", default_count, (2, 3, 4))
    include_zero = _axis(ctx, "include_zero", default_zero, (False, True))
    band = difficulty if difficulty is not None else "medium"
    template_index, offset_step, warp = ctx.draw_choice(
        "geometry_variant", _GEOMETRY_CANDIDATES[profile][band]
    )
    sectors = _apply_profile_geometry(
        profile, _sector_grid(template_index, region_count, offset_step, warp), region_count
    )
    colors = _region_palette(ctx, region_count, include_zero)
    return [
        [value if value in _FRAME_COLORS else colors[value] for value in row]
        for row in sectors
    ]


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors in 0..9"]
    return []


def _cycle_colors(grid, *, excluded=_FRAME_COLORS):
    return set(value for row in grid for value in row) - set(excluded)


def _centroid(grid, color, *, mode="pixels"):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"color {color} is absent")
    if mode == "pixels":
        return (
            sum(r for r, _ in cells) / len(cells),
            sum(c for _, c in cells) / len(cells),
        )
    if mode == "first":
        return min(cells)
    raise ValueError(f"unknown centroid mode {mode}")


def _centroid_angle(grid, color, *, mode="pixels"):
    mr, mc = _centroid(grid, color, mode=mode)
    return math.atan2(
        mc - (len(grid[0]) - 1) / 2.0,
        -(mr - (len(grid) - 1) / 2.0),
    ) % _TWO_PI


def _ordered_colors(grid, *, mode="pixels", excluded=_FRAME_COLORS):
    colors = _cycle_colors(grid, excluded=excluded)
    if mode == "numeric":
        return sorted(colors)
    if mode == "row_major":
        return sorted(
            colors,
            key=lambda color: min(
                (r, c)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value == color
            ),
        )
    if mode == "quadrant":
        def quadrant_key(color):
            angle = _centroid_angle(grid, color)
            quadrant = int(((angle + math.pi / 4.0) % _TWO_PI) / (math.pi / 2.0))
            return quadrant, angle
        return sorted(colors, key=quadrant_key)
    return sorted(colors, key=lambda color: _centroid_angle(grid, color, mode=mode))


def _recolor(grid, order, *, direction="clockwise", fixed=_FRAME_COLORS):
    if len(order) < 2:
        return [list(row) for row in grid]
    delta = -1 if direction == "clockwise" else 1
    mapping = {color: order[(index + delta) % len(order)] for index, color in enumerate(order)}
    return [
        [value if value in fixed else mapping.get(value, value) for value in row]
        for row in grid
    ]


def _semantic_oracle(grid):
    """Diagnostic mirror of the selected Racket rule; never label authority."""
    return _recolor(grid, _ordered_colors(grid), direction="clockwise")


def self_check(grid, *, difficulty=None, meta=None):
    errors = _validate_grid(grid)
    if errors:
        return errors
    colors = set(value for row in grid for value in row)
    missing = sorted(_FRAME_COLORS - colors)
    if missing:
        errors.append(f"missing fixed frame colors: {missing}")
    rotating = colors - _FRAME_COLORS
    if not 2 <= len(rotating) <= 4:
        errors.append(f"expected 2..4 non-frame colors, found {len(rotating)}")
        return errors
    center_r = (len(grid) - 1) / 2.0
    center_c = (len(grid[0]) - 1) / 2.0
    angles = []
    for color in rotating:
        mr, mc = _centroid(grid, color)
        if abs(mr - center_r) < 1e-12 and abs(mc - center_c) < 1e-12:
            errors.append(f"color {color} centroid is exactly at grid center")
        angles.append((color, _centroid_angle(grid, color)))
    for index, (color, angle) in enumerate(angles):
        for other, other_angle in angles[index + 1:]:
            separation = abs(angle - other_angle)
            separation = min(separation, _TWO_PI - separation)
            if separation < 1e-9:
                errors.append(f"colors {color} and {other} have tied centroid angles")
    if not errors and _semantic_oracle(grid) == [list(row) for row in grid]:
        errors.append("clockwise recoloring would be identity")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) != (8, 8):
        return [f"canonical-scale inputs are 8x8, found {len(grid)}x{len(grid[0])}"]
    palette_size = len(set(value for row in grid for value in row))
    if not 4 <= palette_size <= 6:
        return [f"canonical palette size must be 4..6, found {palette_size}"]
    return []


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    rotating = _cycle_colors(grid)
    return {"region_count": len(rotating), "include_zero": 0 in rotating}


# --- Executable rival rules -------------------------------------------------

def _identity(grid):
    return [list(row) for row in grid]


def _counterclockwise(grid):
    return _recolor(grid, _ordered_colors(grid), direction="counterclockwise")


def _numeric_color_cycle(grid):
    return _recolor(grid, _ordered_colors(grid, mode="numeric"), direction="clockwise")


def _zero_is_background(grid):
    order = _ordered_colors(grid, excluded=_FRAME_COLORS | {0})
    return _recolor(grid, order, direction="clockwise", fixed=_FRAME_COLORS | {0})


def _include_frame_colors(grid):
    order = _ordered_colors(grid, excluded=frozenset())
    return _recolor(grid, order, direction="clockwise", fixed=frozenset())


def _row_major_cycle(grid):
    return _recolor(grid, _ordered_colors(grid, mode="row_major"), direction="clockwise")


def _quadrant_cycle(grid):
    return _recolor(grid, _ordered_colors(grid, mode="quadrant"), direction="clockwise")


def _first_cell_angle_cycle(grid):
    return _recolor(grid, _ordered_colors(grid, mode="first"), direction="clockwise")


CANONICAL_SHORTCUTS = {
    "row_major_first_occurrence": _row_major_cycle,
    "fixed_quadrant_order": _quadrant_cycle,
    "first_cell_angle": _first_cell_angle_cycle,
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "identity": _identity,
    "counterclockwise": _counterclockwise,
    "numeric_color_cycle": _numeric_color_cycle,
    "zero_is_background": _zero_is_background,
    "rotate_frame_too": _include_frame_colors,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _counterexample_predicate(rival):
    def predicate(grid):
        return rival(grid) != _semantic_oracle(grid)
    return predicate


SEMANTIC_WITNESSES = {}
WITNESS_RIVALS = {}
for _rival_name, _rival in SEMANTIC_RIVALS.items():
    _witness_name = "counterexample_" + _rival_name
    SEMANTIC_WITNESSES[_witness_name] = _counterexample_predicate(_rival)
    WITNESS_RIVALS[_witness_name] = [_rival_name]


def lesson_identifiable(demos, query):
    """Finite-rival audit; [] does not claim universal logical uniqueness."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"rival {name} fits every demo but disagrees on query")
    return reasons
