"""Generator for training task ea9794b1 / f112ec4615da.

Split an even grid into four equal quadrants. Each quadrant has one distinct
foreground color. At each local coordinate, overlay TL, then BR, then BL,
then TR; a nonzero higher-priority value replaces the current value.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f112ec4615da"
VERSION = "3.0.0"
TASK_ID = "f112ec4615da"
RULE_HASH = "8724ec70a45a"

SUMMARY = (
    "Build an even rectangular grid from four equal quadrants, each using one "
    "distinct foreground color over zero background. The output overlays "
    "corresponding cells with fixed priority TR > BL > BR > TL. General "
    "lessons force witnesses for all five outcomes: all-zero, TL, BR, BL, "
    "and TR."
)

INVARIANTS = [
    "the input has independent even dimensions from 6 through 30",
    "zero is the background",
    "each quadrant contains exactly one foreground color and some zero",
    "the four quadrant colors are distinct",
    "each quadrant contains at least one foreground cell",
    "the output dimensions are exactly half the input dimensions",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_EVEN_DIMS = (6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)
_PROFILE_PRIOR = 0.28
_BAND_DIMS = {
    "easy": (6, 8, 10),
    "medium": (10, 12, 14, 16, 18, 20),
    "hard": (18, 20, 22, 24, 26, 28, 30),
}
_DENSITY_RANGES = {
    "easy": (0.25, 0.45),
    "medium": (0.35, 0.60),
    "hard": (0.50, 0.75),
}
_QUADRANT_OFFSETS = ((0, 0), (0, 1), (1, 0), (1, 1))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware even choice",
        "valid": "6|8|10|12|14|16|18|20|22|24|26|28|30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware even choice",
        "valid": "6|8|10|12|14|16|18|20|22|24|26|28|30",
    },
}

# Seven public inputs as TL/TR/BL/BR binary masks. Fixed public colors are
# intentionally omitted: color labels are nuisance.
_PROFILE_MASKS = (
    (
        ("01110", "11000", "10011", "00101", "00111"),
        ("00011", "10110", "01110", "10010", "11111"),
        ("01011", "10011", "00010", "00110", "11010"),
        ("00010", "01101", "00110", "10100", "01011"),
    ),
    (
        ("01001", "01111", "01000", "11000", "00110"),
        ("00001", "11111", "01110", "11101", "11000"),
        ("10101", "00010", "11010", "00111", "11010"),
        ("00110", "00010", "01110", "00000", "11110"),
    ),
    (
        ("10000", "00111", "11010", "11100", "00101"),
        ("10001", "11111", "11111", "10000", "11000"),
        ("00001", "10101", "00100", "11110", "01100"),
        ("01011", "10100", "10110", "10001", "11111"),
    ),
    (
        ("01110", "01000", "00000", "00110", "01111"),
        ("01010", "01001", "00111", "10111", "11111"),
        ("10110", "10001", "00100", "00010", "00001"),
        ("00000", "01010", "00001", "11000", "00111"),
    ),
    (
        ("11111", "10110", "00101", "11100", "11110"),
        ("11011", "00101", "00010", "10011", "10101"),
        ("11101", "11001", "00010", "01000", "00001"),
        ("00111", "10000", "00000", "10100", "01010"),
    ),
    (
        ("10001", "10000", "01101", "01101", "00001"),
        ("00110", "11110", "10011", "00100", "00001"),
        ("01111", "00111", "11100", "11101", "01101"),
        ("01001", "10001", "11010", "01111", "01001"),
    ),
    (
        ("10100", "10000", "00111", "00101", "11110"),
        ("10110", "11001", "00010", "11110", "10000"),
        ("00011", "01011", "00011", "00111", "10100"),
        ("00101", "10001", "00110", "10000", "00110"),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if value not in _EVEN_DIMS:
            raise ValueError(
                f"{label} must be one of {', '.join(map(str, _EVEN_DIMS))}"
            )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _winner_counts(grid):
    height = len(grid)
    width = len(grid[0])
    half_h = height // 2
    half_w = width // 2
    counts = {"zero": 0, "tl": 0, "br": 0, "bl": 0, "tr": 0}
    for row in range(half_h):
        for col in range(half_w):
            tl = grid[row][col]
            tr = grid[row][col + half_w]
            bl = grid[row + half_h][col]
            br = grid[row + half_h][col + half_w]
            if tr != 0:
                counts["tr"] += 1
            elif bl != 0:
                counts["bl"] += 1
            elif br != 0:
                counts["br"] += 1
            elif tl != 0:
                counts["tl"] += 1
            else:
                counts["zero"] += 1
    return counts


def _scene_analysis(grid):
    if not isinstance(grid, list) or not grid:
        return None, None, ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return None, None, [
            "grid rows must be non-empty lists or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]

    height = len(coerced)
    errors = []
    if height not in _EVEN_DIMS:
        errors.append("grid height must be an allowed even dimension")
    if width not in _EVEN_DIMS:
        errors.append("grid width must be an allowed even dimension")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return coerced, None, errors
    if errors:
        return coerced, None, errors

    half_h = height // 2
    half_w = width // 2
    area = half_h * half_w
    colors = []
    masks = []
    occupancies = []
    for vertical, horizontal in _QUADRANT_OFFSETS:
        top = vertical * half_h
        left = horizontal * half_w
        values = [
            coerced[top + row][left + col]
            for row in range(half_h)
            for col in range(half_w)
        ]
        foreground = {value for value in values if value != 0}
        if len(foreground) != 1:
            errors.append(
                "each quadrant must contain exactly one foreground color"
            )
            continue
        color = next(iter(foreground))
        occupied = sum(value != 0 for value in values)
        if not 1 <= occupied < area:
            errors.append(
                "each quadrant must contain foreground and background"
            )
        colors.append(color)
        occupancies.append(occupied)
        masks.append(tuple(value != 0 for value in values))
    if len(colors) == 4 and len(set(colors)) != 4:
        errors.append("the four quadrant colors must be distinct")
    if errors:
        return coerced, None, errors

    return coerced, {
        "grid_h": height,
        "grid_w": width,
        "half_h": half_h,
        "half_w": half_w,
        "colors": tuple(colors),
        "masks": tuple(masks),
        "occupancies": tuple(occupancies),
        "winner_counts": _winner_counts(coerced),
    }, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    half_h = features["half_h"]
    half_w = features["half_w"]
    output = full_grid(half_h, half_w, 0)
    for row in range(half_h):
        for col in range(half_w):
            value = coerced[row][col]
            for source_row, source_col in (
                (row + half_h, col + half_w),
                (row + half_h, col),
                (row, col + half_w),
            ):
                if coerced[source_row][source_col] != 0:
                    value = coerced[source_row][source_col]
            output[row][col] = value
    return output


def _profile_feature(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    return (
        features["grid_h"],
        features["grid_w"],
        features["masks"],
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    (
        10,
        10,
        tuple(
            tuple(value == "1" for row in quadrant for value in row)
            for quadrant in profile
        ),
    )
    for profile in _PROFILE_MASKS
)


def canonical_profile_signature(grid):
    signature = _profile_feature(_coerce_grid(grid))
    return (
        signature
        if signature in _CANONICAL_PROFILE_SIGNATURES
        else None
    )


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def _grid_from_masks(masks, colors):
    half_h = len(masks[0])
    half_w = len(masks[0][0])
    grid = full_grid(half_h * 2, half_w * 2, 0)
    for index, (vertical, horizontal) in enumerate(_QUADRANT_OFFSETS):
        top = vertical * half_h
        left = horizontal * half_w
        for row in range(half_h):
            for col in range(half_w):
                if masks[index][row][col] in ("1", True, 1):
                    grid[top + row][left + col] = colors[index]
    return grid


def _draw_profile(profile, colors):
    grid = _grid_from_masks(profile, colors)
    if canonical_profile_signature(grid) is None:
        raise AssertionError("constructed public profile drifted")
    return grid


def _draw_general(ctx, band, overrides):
    height_options = (
        _EVEN_DIMS
        if overrides.get("grid_h") is not None
        else _BAND_DIMS[band]
    )
    width_options = (
        _EVEN_DIMS
        if overrides.get("grid_w") is not None
        else _BAND_DIMS[band]
    )
    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", width_options)
    half_h = height // 2
    half_w = width // 2
    area = half_h * half_w
    rng = ctx.draw_rng("layout")
    colors = rng.sample(list(range(1, 10)), 4)
    low_density, high_density = _DENSITY_RANGES[band]
    density = rng.uniform(low_density, high_density)
    masks = [
        [rng.random() < density for _ in range(area)]
        for _ in range(4)
    ]

    # A compact proof of the priority chain: none, TL, TL+BR,
    # TL+BR+BL, then all four.
    positions = rng.sample(range(area), 5)
    forced_patterns = (
        (False, False, False, False),
        (True, False, False, False),
        (True, False, False, True),
        (True, False, True, True),
        (True, True, True, True),
    )
    for position, pattern in zip(positions, forced_patterns):
        for quadrant, occupied in enumerate(pattern):
            masks[quadrant][position] = occupied

    rows = [
        tuple(
            "".join(
                "1" if masks[index][row * half_w + col] else "0"
                for col in range(half_w)
            )
            for row in range(half_h)
        )
        for index in range(4)
    ]
    return _grid_from_masks(rows, colors)


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
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_MASKS))),
            )

    if profile_index is not None:
        colors = ctx.draw_rng("profile_layout").sample(
            list(range(1, 10)), 4
        )
        grid = _draw_profile(_PROFILE_MASKS[profile_index], colors)
        ctx.draw_choice("grid_h", (10,))
        ctx.draw_choice("grid_w", (10,))
    else:
        grid = _draw_general(ctx, band, overrides)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
