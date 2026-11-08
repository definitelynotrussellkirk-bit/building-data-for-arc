"""Generator for training task 8f2ea7aa / f4f11295a6f5.

Crop the zero-padded input to its nonzero bounding box. Treat that crop as
both a block mask and a tile: every nonzero crop cell selects one copy of the
whole crop in the corresponding output block, while zero crop cells select a
blank block.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f4f11295a6f5"
VERSION = "3.1.0"
TASK_ID = "f4f11295a6f5"
RULE_HASH = "0a5d84c1cab4"

SUMMARY = (
    "Place a nontrivial 2x2 through 5x5 pattern inside a zero canvas whose "
    "height and width equal the squared crop dimensions. The output has the "
    "same dimensions and is a self-tile fractal: a nonzero pattern cell emits "
    "one complete pattern block and a zero pattern cell emits a blank block."
)

INVARIANTS = [
    "zero is background and all padding outside the crop is zero",
    "the nonzero bounding-box crop is two through five cells per dimension",
    "the crop has at least two nonzero cells and at least one zero cell",
    "one through three foreground colors may occur and every chosen color is used",
    "input and output dimensions are ph squared by pw squared",
    "the crop touches all four sides of its own bounding box",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_PATTERN_SIZES = (2, 3, 4, 5)
_COLORS = tuple(range(1, 10))
_LAYOUTS = (
    "random",
    "diag",
    "anti_diag",
    "cross",
    "l_shape",
    "checker",
)
LESSON_SCHEDULE_PERIOD = 7
SCHEDULE_PROFILES = ("canonical_profile", "multicolor_general")
_BAND_SIZES = {
    "easy": (3,),
    "medium": (3, 4),
    "hard": (3, 4, 5),
}
_BAND_COLOR_COUNTS = {
    # Single-color support comes from the exact canonical-profile residue.
    # Every broad draw is deliberately multicolor so any three-example lesson
    # refutes the canonical-fitting selector-colored-tile shortcut.
    "easy": (2,),
    "medium": (2,),
    "hard": (2, 3),
}
_BAND_DENSITY = {
    "easy": (0.30, 0.55),
    "medium": (0.30, 0.70),
    "hard": (0.25, 0.75),
}

AXES = {
    "pattern_h": {
        "type": "int",
        "default": "difficulty-aware choice",
        "valid": "2|3|4|5",
    },
    "pattern_w": {
        "type": "int",
        "default": "difficulty-aware choice",
        "valid": "2|3|4|5",
    },
}

# Cropped public patterns, normalized to one foreground role. Their input
# translation is discarded by the executable rule, so the strict linked
# profile retains the complete crop under lawful D4 and color relabeling while
# treating placement anywhere inside the 9x9 canvas as nuisance.
_PROFILE_PATTERNS = (
    (
        "001",
        "011",
        "100",
    ),
    (
        "110",
        "001",
        "100",
    ),
    (
        "010",
        "101",
        "110",
    ),
    (
        "100",
        "110",
        "011",
    ),
)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
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
        if value not in _PATTERN_SIZES:
            raise ValueError(f"{label} must be 2, 3, 4, or 5")


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


def _crop_to_content(grid):
    positions = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not positions:
        return None, None
    top = min(row for row, _col in positions)
    bottom = max(row for row, _col in positions)
    left = min(col for _row, col in positions)
    right = max(col for _row, col in positions)
    return (
        [
            values[left:right + 1]
            for values in grid[top:bottom + 1]
        ],
        (top, left, bottom, right),
    )


def _scene_analysis(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, None, ["grid must be a non-empty list or tuple"]
    if not all(
        isinstance(row, (list, tuple, str)) and row for row in grid
    ):
        return None, None, [
            "rows must be non-empty lists, tuples, or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]
    height = len(coerced)
    errors = []
    if not 4 <= height <= 25 or not 4 <= width <= 25:
        errors.append("grid dimensions must be between 4 and 25")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return coerced, None, errors
    crop, bbox = _crop_to_content(coerced)
    if crop is None:
        errors.append("grid must contain a nonzero pattern")
        return coerced, None, errors
    pattern_h = len(crop)
    pattern_w = len(crop[0])
    if pattern_h not in _PATTERN_SIZES:
        errors.append("cropped pattern height must be 2, 3, 4, or 5")
    if pattern_w not in _PATTERN_SIZES:
        errors.append("cropped pattern width must be 2, 3, 4, or 5")
    nonzero = [
        value
        for row in crop
        for value in row
        if value != 0
    ]
    if len(nonzero) < 2:
        errors.append("cropped pattern must have at least two nonzero cells")
    if len(nonzero) >= pattern_h * pattern_w:
        errors.append("cropped pattern must contain at least one zero")
    colors = tuple(sorted(set(nonzero)))
    if not 1 <= len(colors) <= 3:
        errors.append("cropped pattern must use one through three colors")
    if height != pattern_h * pattern_h:
        errors.append("input height must equal cropped height squared")
    if width != pattern_w * pattern_w:
        errors.append("input width must equal cropped width squared")
    if errors:
        return coerced, None, errors
    return coerced, {
        "height": height,
        "width": width,
        "crop": tuple(tuple(row) for row in crop),
        "bbox": bbox,
        "pattern_h": pattern_h,
        "pattern_w": pattern_w,
        "colors": colors,
        "color_count": len(colors),
        "nonzero_count": len(nonzero),
        "density": len(nonzero) / (pattern_h * pattern_w),
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "pattern_h": features["pattern_h"],
        "pattern_w": features["pattern_w"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    pattern = features["crop"]
    pattern_h = features["pattern_h"]
    pattern_w = features["pattern_w"]
    output = full_grid(
        pattern_h * pattern_h,
        pattern_w * pattern_w,
        0,
    )
    for row in range(len(output)):
        block_row, pattern_row = divmod(row, pattern_h)
        for col in range(len(output[0])):
            block_col, pattern_col = divmod(col, pattern_w)
            if pattern[block_row][block_col] != 0:
                output[row][col] = pattern[pattern_row][pattern_col]
    return output


def strict_canonical_like(grid):
    """Accept exactly the lawful task domain documented by ``self_check``."""
    return self_check(grid)


def _selector_colored_tiles(grid):
    """Plausible wrong rule: recolor each emitted mask by selector color.

    It is answer-equivalent to the canonical rule on every public single-color
    pair, but differs whenever the cropped tile contains multiple colors.
    """
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    pattern = features["crop"]
    pattern_h = features["pattern_h"]
    pattern_w = features["pattern_w"]
    output = full_grid(pattern_h * pattern_h, pattern_w * pattern_w, 0)
    for row in range(len(output)):
        block_row, pattern_row = divmod(row, pattern_h)
        for col in range(len(output[0])):
            block_col, pattern_col = divmod(col, pattern_w)
            selector = pattern[block_row][block_col]
            if selector != 0 and pattern[pattern_row][pattern_col] != 0:
                output[row][col] = selector
    return output


def _is_multicolor_tile_copy(grid):
    _coerced, features, errors = _scene_analysis(grid)
    return not errors and features["color_count"] > 1


SEMANTIC_WITNESSES = {
    "multicolor_tile_copy": _is_multicolor_tile_copy,
}
SEMANTIC_RIVALS = {
    "selector_colored_tiles": _selector_colored_tiles,
}
WITNESS_RIVALS = {
    "multicolor_tile_copy": ["selector_colored_tiles"],
}
CANONICAL_SHORTCUTS = {
    "selector_colored_tiles": _selector_colored_tiles,
}
LESSON_COMPETITORS = {
    "selector_colored_tiles": _selector_colored_tiles,
}


def lesson_identifiable(demos, query):
    """Report when the declared shortcut survives demos and changes the query."""
    rival = _selector_colored_tiles
    if not all(rival(pair["input"]) == pair["output"] for pair in demos):
        return []
    if rival(query["input"]) != query["output"]:
        return [
            "selector_colored_tiles fits every demonstration but predicts "
            "a different query output"
        ]
    return []


def _rotate_90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _reflect(grid):
    return [row[::-1] for row in grid]


def _d4_patterns(pattern):
    current = _coerce_grid(pattern)
    variants = []
    for _turn in range(4):
        variants.append([row[:] for row in current])
        variants.append(_reflect(current))
        current = _rotate_90(current)
    return tuple(variants)


def _normalized_crop(grid):
    coerced = _coerce_grid(grid)
    crop, _bbox = _crop_to_content(coerced)
    if crop is None:
        return None
    colors = sorted({
        value for row in crop for value in row if value != 0
    })
    if len(colors) != 1:
        return None
    color = colors[0]
    return tuple(
        tuple(1 if value == color else 0 for value in row)
        for row in crop
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _normalized_crop(variant)
    for source in _PROFILE_PATTERNS
    for variant in _d4_patterns(source)
)
_PROFILE_SIGNATURE_TO_INDEX = {
    _normalized_crop(variant): index
    for index, source in enumerate(_PROFILE_PATTERNS)
    for variant in _d4_patterns(source)
}


def canonical_profile_signature(grid):
    signature = _normalized_crop(grid)
    return (
        signature
        if signature in _CANONICAL_PROFILE_SIGNATURES
        else None
    )


def canonical_profile_index(grid):
    return _PROFILE_SIGNATURE_TO_INDEX.get(_normalized_crop(grid))


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def _place_pattern(pattern, rng):
    pattern_h = len(pattern)
    pattern_w = len(pattern[0])
    height = pattern_h * pattern_h
    width = pattern_w * pattern_w
    top = rng.randint(0, height - pattern_h)
    left = rng.randint(0, width - pattern_w)
    grid = full_grid(height, width, 0)
    for row in range(pattern_h):
        for col in range(pattern_w):
            grid[top + row][left + col] = pattern[row][col]
    return grid


def _draw_profile(source, rng):
    occupancy = rng.choice(_d4_patterns(source))
    color = rng.choice(_COLORS)
    pattern = [
        [color if value != 0 else 0 for value in row]
        for row in occupancy
    ]
    grid = _place_pattern(pattern, rng)
    if canonical_profile_index(grid) is None:
        raise AssertionError("constructed public profile drifted")
    return grid


def _occupancy_mask(layout, pattern_h, pattern_w, density, rng):
    mask = [[False] * pattern_w for _ in range(pattern_h)]
    if layout == "diag":
        for row in range(pattern_h):
            col = round(row * (pattern_w - 1) / (pattern_h - 1))
            mask[row][col] = True
    elif layout == "anti_diag":
        for row in range(pattern_h):
            col = pattern_w - 1 - round(
                row * (pattern_w - 1) / (pattern_h - 1)
            )
            mask[row][col] = True
    elif layout == "cross":
        middle_row = pattern_h // 2
        middle_col = pattern_w // 2
        for col in range(pattern_w):
            mask[middle_row][col] = True
        for row in range(pattern_h):
            mask[row][middle_col] = True
    elif layout == "l_shape":
        for row in range(pattern_h):
            mask[row][0] = True
        for col in range(pattern_w):
            mask[-1][col] = True
    elif layout == "checker":
        for row in range(pattern_h):
            for col in range(pattern_w):
                mask[row][col] = (row + col) % 2 == 0
    else:
        for row in range(pattern_h):
            for col in range(pattern_w):
                mask[row][col] = rng.random() < density

    # Ensure the intended bbox without pinning two particular corners. This
    # keeps translation and crop size exact while retaining many morphologies.
    edges = (
        [(0, col) for col in range(pattern_w)],
        [(pattern_h - 1, col) for col in range(pattern_w)],
        [(row, 0) for row in range(pattern_h)],
        [(row, pattern_w - 1) for row in range(pattern_h)],
    )
    for edge in edges:
        if not any(mask[row][col] for row, col in edge):
            row, col = rng.choice(edge)
            mask[row][col] = True
    if all(value for row in mask for value in row):
        candidates = [
            (row, col)
            for row in range(pattern_h)
            for col in range(pattern_w)
            if all(
                any(
                    mask[edge_row][edge_col]
                    and (edge_row, edge_col) != (row, col)
                    for edge_row, edge_col in edge
                )
                for edge in edges
            )
        ]
        row, col = rng.choice(candidates)
        mask[row][col] = False
    return mask


def _draw_general(ctx, band, overrides):
    height_options = (
        _PATTERN_SIZES
        if overrides.get("pattern_h") is not None
        else _BAND_SIZES[band]
    )
    width_options = (
        _PATTERN_SIZES
        if overrides.get("pattern_w") is not None
        else _BAND_SIZES[band]
    )
    pattern_h = ctx.draw_choice("pattern_h", height_options)
    pattern_w = ctx.draw_choice("pattern_w", width_options)
    rng = ctx.draw_rng("pattern")
    density = rng.uniform(*_BAND_DENSITY[band])
    layout = (
        "random"
        if rng.random() < 0.75
        else rng.choice(_LAYOUTS[1:])
    )
    mask = _occupancy_mask(
        layout,
        pattern_h,
        pattern_w,
        density,
        rng,
    )
    occupied = [
        (row, col)
        for row in range(pattern_h)
        for col in range(pattern_w)
        if mask[row][col]
    ]
    color_count = min(
        rng.choice(_BAND_COLOR_COUNTS[band]),
        len(occupied),
    )
    colors = rng.sample(_COLORS, color_count)
    rng.shuffle(occupied)
    pattern = full_grid(pattern_h, pattern_w, 0)
    for index, (row, col) in enumerate(occupied):
        pattern[row][col] = colors[index % color_count]
    return _place_pattern(pattern, rng)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum role for one production draw.

    One exact-profile draw every seven samples preserves the measured ~15%
    canonical prior. The other six residues are multicolor counterexamples to
    the strongest shortcut fitting the public single-color demonstrations.
    """
    del seed, difficulty
    return (
        "canonical_profile"
        if sample_index % LESSON_SCHEDULE_PERIOD == 0
        else "multicolor_general"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
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
    if (
        not has_override
        and schedule_profile(seed, sample_index, difficulty)
        == "canonical_profile"
    ):
        profile_index = ctx.draw_choice(
            f"canonical_form|{band}",
            tuple(range(len(_PROFILE_PATTERNS))),
        )

    if profile_index is not None:
        grid = _draw_profile(
            _PROFILE_PATTERNS[profile_index],
            ctx.draw_rng("profile_layout"),
        )
        _coerced, features, errors = _scene_analysis(grid)
        if errors:
            raise AssertionError(
                "generated invalid profile: " + "; ".join(errors)
            )
        ctx.draw_choice("pattern_h", (features["pattern_h"],))
        ctx.draw_choice("pattern_w", (features["pattern_w"],))
    else:
        grid = _draw_general(ctx, band, overrides)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
