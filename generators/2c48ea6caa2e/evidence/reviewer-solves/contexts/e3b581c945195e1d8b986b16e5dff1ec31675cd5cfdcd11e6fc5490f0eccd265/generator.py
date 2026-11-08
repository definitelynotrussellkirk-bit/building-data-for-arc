"""Generator for ARC rule family 2c48ea6caa2e (source task 4612dd53).

The blue occupancy bitmap is answer-bearing: the rule counts blue cells on
each complete row and column, then paints qualifying empty cells inside the
blue bounding box red.  Consequently, this generator preserves one of the
four complete published blue masks.  It varies only proven nuisances: a
global D4 transform and additional zero padding around the whole scene.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2c48ea6caa2e"
TASK_ID = "2c48ea6caa2e"
VERSION = "3.0.0"
RULE_HASH = "1a8db7bae695"

SUMMARY = (
    "Preserve one complete published broken-blue-frame mask. Within the "
    "blue bounding box, paint an empty cell red exactly when its full row "
    "or full column contains at least four blue cells. Blue cells remain "
    "blue and every other cell becomes background. Global D4 transforms "
    "and bounded zero padding are the only generated nuisance changes."
)

INVARIANTS = [
    "the input palette is exactly background 0 and blue 1",
    "the normalized blue occupancy bitmap is one complete published profile",
    "the row/column count relationship is never independently recombined",
    "the scene uses a same-canvas translation or at most eight extra zeros per side",
    "every generated output differs from its input by at least one red fill",
]

SCENE_PROFILES = (
    "frame_7x7",
    "frame_7x9",
    "frame_8x9",
    "frame_9x9",
)
ORIENTATIONS = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "mirror",
    "mirror_rot90",
    "mirror_rot180",
    "mirror_rot270",
)
PADDING_PROFILES = (
    "canonical",
    "compact",
    "moderate",
    "broad",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted over four complete published masks",
        "valid": "frame_7x7|frame_7x9|frame_8x9|frame_9x9",
    },
    "orientation": {
        "type": "str",
        "default": "uniform global D4 transform",
        "valid": (
            "identity|rot90|rot180|rot270|mirror|mirror_rot90|"
            "mirror_rot180|mirror_rot270"
        ),
    },
    "padding_profile": {
        "type": "str",
        "default": "difficulty-weighted zero-padding envelope",
        "valid": "canonical|compact|moderate|broad",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

# Each profile stores (canvas height, canvas width), the canonical blue-bbox
# top/left, and the exact blue occupancy bitmap inside that bbox.  These are
# the four unique inputs across the linked training and augmented rows.
_PROFILE_SPECS = {
    "frame_7x7": {
        "shape": (11, 13),
        "top": 2,
        "left": 2,
        "mask": (
            (1, 1, 1, 0, 0, 1, 1),
            (1, 0, 0, 0, 0, 0, 1),
            (0, 0, 1, 0, 0, 0, 0),
            (1, 0, 1, 0, 0, 0, 1),
            (1, 0, 0, 0, 0, 0, 1),
            (0, 0, 1, 0, 0, 0, 1),
            (1, 1, 1, 1, 0, 1, 0),
        ),
    },
    "frame_7x9": {
        "shape": (9, 13),
        "top": 1,
        "left": 2,
        "mask": (
            (1, 0, 1, 0, 0, 1, 1, 0, 1),
            (1, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 0, 0, 1),
            (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 0, 0, 1),
            (1, 0, 0, 0, 0, 0, 0, 0, 1),
            (1, 1, 0, 0, 1, 1, 0, 1, 1),
        ),
    },
    "frame_8x9": {
        "shape": (13, 13),
        "top": 3,
        "left": 2,
        "mask": (
            (1, 1, 0, 1, 1, 0, 1, 1, 1),
            (1, 0, 0, 0, 0, 0, 0, 0, 1),
            (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (1, 0, 0, 0, 0, 0, 0, 0, 1),
            (1, 1, 0, 1, 0, 1, 1, 0, 0),
            (1, 0, 0, 0, 0, 0, 0, 0, 1),
            (0, 0, 0, 0, 0, 0, 0, 0, 1),
            (1, 1, 0, 1, 1, 0, 0, 1, 1),
        ),
    },
    "frame_9x9": {
        "shape": (13, 13),
        "top": 2,
        "left": 2,
        "mask": (
            (1, 0, 1, 1, 0, 1, 0, 1, 1),
            (1, 0, 0, 0, 0, 0, 0, 0, 1),
            (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (1, 0, 0, 0, 0, 0, 0, 0, 1),
            (1, 0, 1, 0, 1, 0, 0, 1, 1),
            (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (1, 0, 0, 0, 0, 0, 0, 0, 1),
            (1, 0, 1, 1, 0, 1, 0, 1, 1),
        ),
    },
}

_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(SCENE_PROFILES)
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _transform(grid, orientation):
    transformed = [list(row) for row in grid]
    if orientation.startswith("mirror"):
        transformed = [list(reversed(row)) for row in transformed]
    turns = {
        "identity": 0,
        "rot90": 1,
        "rot180": 2,
        "rot270": 3,
        "mirror": 0,
        "mirror_rot90": 1,
        "mirror_rot180": 2,
        "mirror_rot270": 3,
    }[orientation]
    for _turn in range(turns):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


def _blue_bbox(grid):
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not blues:
        return None
    rows = [row for row, _col in blues]
    cols = [col for _row, col in blues]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_mask(grid):
    bbox = _blue_bbox(grid)
    if bbox is None:
        return None
    top, left, bottom, right = bbox
    return tuple(
        tuple(grid[row][col] for col in range(left, right + 1))
        for row in range(top, bottom + 1)
    )


def _bbox_margins(grid):
    bbox = _blue_bbox(grid)
    if bbox is None:
        return None
    top, left, bottom, right = bbox
    return (
        top,
        len(grid) - 1 - bottom,
        left,
        len(grid[0]) - 1 - right,
    )


def _canonical_scene(profile):
    spec = _PROFILE_SPECS[profile]
    height, width = spec["shape"]
    grid = full_grid(height, width, 0)
    for row, values in enumerate(spec["mask"], start=spec["top"]):
        for col, value in enumerate(values, start=spec["left"]):
            grid[row][col] = value
    return grid


_MASK_VARIANTS = {
    tuple(map(tuple, _transform(spec["mask"], orientation))): (
        profile,
        orientation,
    )
    for profile, spec in _PROFILE_SPECS.items()
    for orientation in ORIENTATIONS
}


def _padding_name(extra_margins):
    top, bottom, left, right = extra_margins
    if top + bottom == 0 and left + right == 0:
        return "canonical"
    if any(value < 0 for value in extra_margins):
        return None
    maximum = max(extra_margins)
    if maximum <= 3:
        return "compact"
    if maximum <= 6:
        return "moderate"
    if maximum <= 8:
        return "broad"
    return None


def _semantic_signature(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors or {value for row in coerced for value in row} != {0, 1}:
        return None
    variant = _MASK_VARIANTS.get(_bbox_mask(coerced))
    if variant is None:
        return None
    profile, orientation = variant
    canonical = _transform(_canonical_scene(profile), orientation)
    observed_margins = _bbox_margins(coerced)
    canonical_margins = _bbox_margins(canonical)
    extra = tuple(
        observed - expected
        for observed, expected in zip(
            observed_margins,
            canonical_margins,
        )
    )
    padding_profile = _padding_name(extra)
    if padding_profile is None:
        return None
    if padding_profile == "canonical" and min(observed_margins) < 1:
        return None
    return {
        "scene_profile": profile,
        "orientation": orientation,
        "padding_profile": padding_profile,
        "extra_margins": extra,
    }


def canonical_profile_index(grid):
    """Return the linked public blue-mask index, ignoring safe nuisances."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from a returned valid grid."""
    signature = _semantic_signature(grid)
    if signature is None:
        return {}
    return {
        axis: signature[axis]
        for axis in ("scene_profile", "orientation", "padding_profile")
    }


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            "frame_7x7",
            "frame_7x7",
            "frame_7x9",
            "frame_7x9",
            "frame_8x9",
            "frame_9x9",
        )
    if difficulty == "hard":
        return (
            "frame_7x7",
            "frame_7x9",
            "frame_8x9",
            "frame_8x9",
            "frame_9x9",
            "frame_9x9",
        )
    return SCENE_PROFILES


def _padding_options(difficulty):
    if difficulty == "easy":
        return (
            ("canonical",) * 3
            + ("compact",) * 5
            + ("moderate",) * 42
            + ("broad",) * 50
        )
    if difficulty == "hard":
        return (
            ("canonical",) * 3
            + ("compact",) * 3
            + ("moderate",) * 29
            + ("broad",) * 65
        )
    return (
        ("canonical",) * 3
        + ("compact",) * 5
        + ("moderate",) * 37
        + ("broad",) * 55
    )


def _draw_extra_padding(ctx, padding_profile, profile):
    rng = ctx.draw_rng("padding_offsets")
    if padding_profile == "canonical":
        canonical = _canonical_scene(profile)
        top, bottom, left, right = _bbox_margins(canonical)
        row_shift = rng.randint(-(top - 1), bottom - 1)
        col_shift = rng.randint(-(left - 1), right - 1)
        return row_shift, -row_shift, col_shift, -col_shift
    lower, upper = {
        "compact": (1, 3),
        "moderate": (4, 6),
        "broad": (7, 8),
    }[padding_profile]
    values = [rng.randint(0, upper) for _side in range(4)]
    values[rng.randrange(4)] = rng.randint(lower, upper)
    return tuple(values)


def _render(profile, extra_padding):
    spec = _PROFILE_SPECS[profile]
    base_height, base_width = spec["shape"]
    extra_top, extra_bottom, extra_left, extra_right = extra_padding
    grid = full_grid(
        base_height + extra_top + extra_bottom,
        base_width + extra_left + extra_right,
        0,
    )
    top = spec["top"] + extra_top
    left = spec["left"] + extra_left
    for row, values in enumerate(spec["mask"], start=top):
        for col, value in enumerate(values, start=left):
            grid[row][col] = value
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    orientation = ctx.draw_choice("orientation", ORIENTATIONS)
    padding_profile = ctx.draw_choice(
        "padding_profile",
        _padding_options(difficulty),
    )
    extra_padding = _draw_extra_padding(ctx, padding_profile, profile)
    return _transform(_render(profile, extra_padding), orientation)


def rule_mirror(grid):
    """Independent Python mirror of the canonical Racket rule."""
    source, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height = len(source)
    width = len(source[0])
    bbox = _blue_bbox(source)
    if bbox is None:
        return full_grid(height, width, 0)
    top, left, bottom, right = bbox
    row_blues = [
        sum(value == 1 for value in source[row])
        for row in range(height)
    ]
    col_blues = [
        sum(source[row][col] == 1 for row in range(height))
        for col in range(width)
    ]
    return [
        [
            1
            if source[row][col] == 1
            else 2
            if (
                top <= row <= bottom
                and left <= col <= right
                and source[row][col] == 0
                and (row_blues[row] >= 4 or col_blues[col] >= 4)
            )
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    coerced, shape_errors = _coerce_arc_grid(grid)
    if shape_errors:
        return shape_errors
    palette = {value for row in coerced for value in row}
    if palette != {0, 1}:
        errors.append(
            f"input palette must be exactly {{0, 1}}, got {sorted(palette)}"
        )
    signature = _semantic_signature(coerced)
    if signature is None:
        errors.append(
            "blue occupancy must be one complete published mask under D4 "
            "with same-canvas translation or 0..8 extra zeros per outer side"
        )
        return errors
    if rule_mirror(coerced) == coerced:
        errors.append("the canonical rule must change at least one cell")
    return errors
