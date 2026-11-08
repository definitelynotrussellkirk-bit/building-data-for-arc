"""Semantic generator for ARC task 40ad7195c775.

A dense 30x30 board uses four distinct nonzero colors.  The modal color is
background; a color occurring exactly twice marks the endpoints; a color
occurring more than thirty times forms three or four almost-solid parallel
stripes; and a color occurring between two and thirty times makes one
three-cell waypoint in every stripe.  Normalize vertical stripes by
transposition, then route an endpoint-colored staircase through the middle of
each waypoint in stripe order.
"""
from __future__ import annotations

import itertools
from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "40ad7195c775"
TASK_ID = "40ad7195c775"
VERSION = "3.1.0"
RULE_HASH = "1482fe487ae4"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Infer background, endpoint, stripe, and waypoint roles from frequency; "
    "transpose vertical stripe scenes; then draw an endpoint-colored "
    "vertical/horizontal staircase through every waypoint center in order. "
    "Easy scenes favor three crossings, medium balances three/four, and hard "
    "favors four crossings."
)
INVARIANTS = [
    "the calibrated input is exactly 30x30 and contains four distinct nonzero colors",
    "the modal background occupies 808 cells for three stripes or 778 for four",
    "the endpoint color occurs exactly twice, above and below every normalized stripe",
    "the stripe color occurs 81 or 108 times across three or four parallel lines",
    "each stripe contains one centered three-cell waypoint cluster",
    "horizontal and vertical stripe orientations are both represented",
    "difficulty changes crossing count while retaining every geometry branch in every band",
    "the output preserves the scene and paints the routed staircase in endpoint color",
]

HORIZONTAL = 0
VERTICAL = 1
ORIENTATION_NAMES = {HORIZONTAL: "horizontal", VERTICAL: "vertical"}
PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))

# A normalized geometry is (orientation, start, goal, ((stripe_row, marker_col), ...)).
PUBLIC_GEOMETRIES = (
    (VERTICAL, (1, 10), (27, 15), ((4, 4), (11, 18), (19, 7))),
    (VERTICAL, (1, 18), (26, 24), ((6, 4), (11, 17), (23, 7))),
    (HORIZONTAL, (1, 8), (27, 12), ((3, 6), (8, 16), (17, 9), (23, 22))),
    (HORIZONTAL, (1, 4), (28, 10), ((3, 13), (8, 6), (19, 18), (22, 5))),
)
PUBLIC_PALETTES = (
    (3, 8, 2, 4),
    (8, 3, 6, 1),
    (1, 9, 2, 3),
    (8, 3, 1, 6),
)

_ROW_BANK_3 = (
    (3, 10, 20),
    (4, 11, 19),
    (5, 13, 22),
    (6, 14, 23),
    (4, 15, 24),
    (7, 12, 21),
    (3, 16, 25),
)
_ROW_BANK_4 = (
    (3, 7, 14, 21),
    (3, 8, 17, 23),
    (4, 10, 16, 24),
    (3, 11, 18, 25),
    (5, 9, 15, 22),
    (4, 12, 19, 24),
    (6, 11, 17, 23),
)


def _general_geometries():
    geometries = []
    for index in range(28):
        stripe_count = 3 if index % 2 == 0 else 4
        bank = _ROW_BANK_3 if stripe_count == 3 else _ROW_BANK_4
        rows = bank[(index // 2) % len(bank)]
        orientation = HORIZONTAL if (index // 2) % 2 == 0 else VERTICAL
        start = (1 + ((index // 4) % 2), 1 + ((7 * index + 3) % 28))
        goal = (28 - ((index // 6) % 2), 1 + ((11 * index + 9) % 28))
        stripes = tuple(
            (row, 1 + ((5 * index + 9 * marker_index + 2) % 28))
            for marker_index, row in enumerate(rows)
        )
        geometry = (orientation, start, goal, stripes)
        if geometry in PUBLIC_GEOMETRIES or geometry in geometries:
            raise AssertionError("general geometry construction must be unique")
        geometries.append(geometry)
    return tuple(geometries)


GENERAL_GEOMETRIES = _general_geometries()
GEOMETRIES = PUBLIC_GEOMETRIES + GENERAL_GEOMETRIES
GEOMETRY_TO_INDEX = {geometry: index for index, geometry in enumerate(GEOMETRIES)}
PALETTES = tuple(itertools.permutations(range(1, 10), 4))
PALETTE_TO_INDEX = {palette: index for index, palette in enumerate(PALETTES)}
PALETTE_COUNT = len(PALETTES)
SCENE_COUNT = len(GEOMETRIES) * PALETTE_COUNT

assert len(PUBLIC_GEOMETRIES) == 4
assert len(GENERAL_GEOMETRIES) == 28
assert len(GEOMETRIES) == len(GEOMETRY_TO_INDEX) == 32
assert PALETTE_COUNT == 3024
assert len(PALETTE_TO_INDEX) == PALETTE_COUNT
assert SCENE_COUNT == 96768

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_code": {
        "type": "int",
        "default": "exact schedule over 0..96767 with 20% official-geometry emphasis and banded crossing counts",
        "valid": "0..96767",
        "doc": (
            "Exact mixed-radix index: geometry_index * 3024 + palette_index. "
            "The geometry specifies orientation, endpoints, stripe rows, and waypoint centers."
        ),
    }
}


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _make_grid(geometry, palette):
    orientation, start, goal, stripes = geometry
    background, endpoint, stripe, waypoint = palette
    normalized = [[background] * 30 for _ in range(30)]
    normalized[start[0]][start[1]] = endpoint
    normalized[goal[0]][goal[1]] = endpoint
    for row, marker_col in stripes:
        normalized[row] = [stripe] * 30
        for col in range(marker_col - 1, marker_col + 2):
            normalized[row][col] = waypoint
    return normalized if orientation == HORIZONTAL else _transpose(normalized)


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["input must contain at least one row"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["input must contain at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC colors from zero through nine"]
    return []


def _role_colors(grid):
    frequency = Counter(value for row in grid for value in row)
    colors = sorted(frequency)
    background = min(colors, key=lambda color: (-frequency[color], color))
    endpoint_candidates = [color for color in colors if frequency[color] == 2]
    if not endpoint_candidates:
        return None
    endpoint = endpoint_candidates[0]
    others = [color for color in colors if color not in (background, endpoint)]
    stripe_candidates = [color for color in others if frequency[color] > 30]
    if not stripe_candidates:
        return None
    stripe = stripe_candidates[0]
    waypoint_candidates = [
        color for color in others
        if color != stripe and 2 < frequency[color] < 30
    ]
    if not waypoint_candidates:
        return None
    waypoint = waypoint_candidates[0]
    return background, endpoint, stripe, waypoint


def _orientation(grid, stripe_color):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == stripe_color
    ]
    if not cells:
        return None
    row_peak = max(Counter(row for row, _ in cells).values())
    col_peak = max(Counter(col for _, col in cells).values())
    return HORIZONTAL if row_peak > col_peak else VERTICAL


def _geometry_signature(grid, palette):
    _, endpoint, stripe, waypoint = palette
    orientation = _orientation(grid, stripe)
    if orientation is None:
        return None
    normalized = [list(row) for row in grid]
    if orientation == VERTICAL:
        normalized = _transpose(normalized)
    endpoints = sorted(
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == endpoint
    )
    if len(endpoints) != 2:
        return None
    stripes = []
    for row, values in enumerate(normalized):
        if sum(value == stripe for value in values) < len(values) - 5:
            continue
        marker_cols = [col for col, value in enumerate(values) if value == waypoint]
        if len(marker_cols) != 3 or marker_cols != list(range(marker_cols[0], marker_cols[0] + 3)):
            return None
        stripes.append((row, marker_cols[1]))
    return orientation, endpoints[0], endpoints[1], tuple(stripes)


def _paint_segment(output, row1, col1, row2, col2, color):
    if row1 == row2:
        for col in range(min(col1, col2), max(col1, col2) + 1):
            output[row1][col] = color
    elif col1 == col2:
        for row in range(min(row1, row2), max(row1, row2) + 1):
            output[row][col1] = color
    else:
        raise ValueError("route segments must be axis aligned")


def _solve_normalized(grid, endpoint_color, stripe_color, waypoint_color):
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    endpoints = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == endpoint_color
    )
    if len(endpoints) != 2:
        raise ValueError("executable route requires exactly two endpoint cells")
    start, goal = endpoints
    stripe_rows = [
        row for row in range(height)
        if sum(grid[row][col] == stripe_color for col in range(width)) >= width - 5
    ]
    waypoint_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == waypoint_color
    ]
    current_row, current_col = start[0] + 1, start[1]
    for stripe_row in stripe_rows:
        marker_cols = sorted(col for row, col in waypoint_cells if row == stripe_row)
        marker_col = -1 if not marker_cols else marker_cols[len(marker_cols) // 2]
        _paint_segment(
            output, current_row, current_col, stripe_row - 1, current_col, endpoint_color
        )
        _paint_segment(
            output, stripe_row - 1, current_col, stripe_row - 1, marker_col, endpoint_color
        )
        output[stripe_row][marker_col] = endpoint_color
        current_row, current_col = stripe_row + 1, marker_col
    for row in range(current_row, goal[0]):
        output[row][current_col] = endpoint_color
    _paint_segment(output, goal[0], current_col, goal[0], goal[1], endpoint_color)
    return output


def rule_mirror(grid):
    """Broad, input-pure mirror of frequency roles and transposed routing."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    palette = _role_colors(grid)
    if palette is None:
        raise ValueError("could not infer background, endpoint, stripe, and waypoint colors")
    _, endpoint, stripe, waypoint = palette
    orientation = _orientation(grid, stripe)
    if orientation == HORIZONTAL:
        return _solve_normalized(grid, endpoint, stripe, waypoint)
    if orientation == VERTICAL:
        return _transpose(
            _solve_normalized(_transpose(grid), endpoint, stripe, waypoint)
        )
    raise ValueError("could not infer stripe orientation")


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if (height, width) != (30, 30):
        errors.append("calibrated stripe-route scenes must be exactly 30x30")
    palette_set = {value for row in grid for value in row}
    if len(palette_set) != 4 or 0 in palette_set:
        errors.append("calibrated scenes require exactly four distinct nonzero colors")
    palette = _role_colors(grid)
    geometry = _geometry_signature(grid, palette) if palette is not None else None
    geometry_index = GEOMETRY_TO_INDEX.get(geometry)
    palette_index = PALETTE_TO_INDEX.get(palette)
    scene_code = None
    if palette is None:
        errors.append("frequency roles are not uniquely recoverable")
    if geometry_index is None:
        errors.append("endpoint/stripe/waypoint geometry is outside the declared curriculum")
    if palette_index is None:
        errors.append("frequency-role colors do not form one declared ordered palette")
    if geometry_index is not None and palette_index is not None:
        scene_code = geometry_index * PALETTE_COUNT + palette_index
        if tuple(tuple(row) for row in grid) != tuple(
            tuple(row) for row in _make_grid(geometry, palette)
        ):
            errors.append("returned cells do not exactly reconstruct from scene_code")

    frequency = Counter(value for row in grid for value in row)
    stripe_count = len(geometry[3]) if geometry is not None else 0
    if stripe_count not in (3, 4):
        errors.append("calibrated scenes require exactly three or four stripes")
    if palette is not None and stripe_count in (3, 4):
        background, endpoint, stripe, waypoint = palette
        expected = {
            background: 808 if stripe_count == 3 else 778,
            endpoint: 2,
            stripe: 27 * stripe_count,
            waypoint: 3 * stripe_count,
        }
        if frequency != Counter(expected):
            errors.append(f"color frequencies must be exactly {expected!r}")
    facts = {
        "height": height,
        "width": width,
        "palette_set": palette_set,
        "palette": palette,
        "frequency": frequency,
        "geometry": geometry,
        "geometry_index": geometry_index,
        "orientation": geometry[0] if geometry is not None else None,
        "orientation_name": (
            ORIENTATION_NAMES[geometry[0]] if geometry is not None else None
        ),
        "stripe_count": stripe_count,
        "public_profile": (
            PUBLIC_PROFILES[geometry_index]
            if geometry_index is not None and geometry_index < len(PUBLIC_PROFILES)
            else None
        ),
    }
    output = None
    if palette is not None:
        try:
            output = rule_mirror(grid)
        except (IndexError, ValueError):
            errors.append("route construction failed on the returned geometry")
    return {
        "errors": errors,
        "scene_code": scene_code,
        "facts": facts,
        "output": output,
    }


def canonical_profile_signature(grid):
    try:
        key = tuple(tuple(row) for row in grid)
    except TypeError:
        return None
    return _CANONICAL_EXACT.get(key)


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return analysis["facts"]["public_profile"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_code": analysis["scene_code"]}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Return reasons when an input falls outside the selected lesson grammar."""
    return self_check(grid)


def _canonical_profile_lookup(grid):
    """Canonical-fitting shortcut: solve only the four public geometry profiles.

    The eight labeled canonical occurrences contain four unique geometries (up
    to repetition across source variants).  A learner can therefore memorize
    those geometry profiles while still appearing perfect on the public data.
    On every generalized geometry this rival returns the unchanged input.
    """
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid stripe-route scene: " + "; ".join(analysis["errors"]))
    if analysis["facts"]["public_profile"] is not None:
        return rule_mirror(grid)
    return [list(row) for row in grid]


def _generalized_geometry_witness(grid):
    analysis = _analysis(grid)
    return bool(
        not analysis["errors"]
        and analysis["facts"]["public_profile"] is None
        and _canonical_profile_lookup(grid) != analysis["output"]
    )


SEMANTIC_WITNESSES = {
    "generalized_geometry": _generalized_geometry_witness,
}
SEMANTIC_RIVALS = {
    "canonical_profile_lookup": _canonical_profile_lookup,
}
WITNESS_RIVALS = {
    "generalized_geometry": ["canonical_profile_lookup"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require demonstrations to refute the canonical-profile lookup shortcut."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    errors = []
    labeled = [
        *((f"demo {index}", pair) for index, pair in enumerate(demos)),
        ("query", query),
    ]
    for label, pair in labeled:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"{label} must contain input and output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            errors.append(f"{label} is outside the grammar: {grammar[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"{label} output disagrees with the selected rule")

    if not errors and all(
        _canonical_profile_lookup(pair["input"]) == pair["output"]
        for pair in demos
    ):
        if _canonical_profile_lookup(query["input"]) != query["output"]:
            errors.append("surviving lesson shortcut: canonical_profile_lookup")
    return errors


def _grid_from_code(scene_code):
    geometry_index, palette_index = divmod(scene_code, PALETTE_COUNT)
    return _make_grid(GEOMETRIES[geometry_index], PALETTES[palette_index])


_CANONICAL_EXACT = {
    tuple(tuple(row) for row in _make_grid(geometry, palette)): profile
    for geometry, palette, profile in zip(
        PUBLIC_GEOMETRIES, PUBLIC_PALETTES, PUBLIC_PROFILES
    )
}

_BAND_INDEX = {None: 0, "easy": 1, "medium": 2, "hard": 3}


def _general_geometry_index(general_rank, seed, difficulty):
    """Choose all 28 generalized geometries with banded crossing complexity.

    Each residue in ``0..13`` names one horizontal/vertical position family;
    the low bit selects its three- or four-stripe member.  A keyed rotation of
    the residue plus the quotient phase lets every family reach both crossing
    counts in every band while weighting easy 3:1 toward three stripes, hard
    3:1 toward four, and medium evenly.
    """
    base_residue, quotient = general_rank % 14, general_rank // 14
    residue = (base_residue + 8 * seed) % 14
    phase = (quotient + seed + residue) % 4
    if difficulty == "easy":
        four_stripes = phase == 0
    elif difficulty == "hard":
        four_stripes = phase != 0
    else:
        four_stripes = (quotient + seed + residue) % 2 == 1
    return 2 * residue + int(four_stripes)


def _natural_scene_code(seed, sample_index, difficulty):
    band_index = _BAND_INDEX[difficulty]
    sample_in_lane = sample_index % 5000
    sample_residue = sample_in_lane % 5
    block = sample_in_lane // 5
    if sample_residue == band_index:
        public_rank = block
        geometry_index = (public_rank + band_index) % len(PUBLIC_GEOMETRIES)
        occurrence_in_profile = public_rank // len(PUBLIC_GEOMETRIES)
        palette_subindex = (occurrence_in_profile + 3 * seed) % 756
    else:
        # Remove this band's one public slot from each five-sample block to
        # obtain a dense 0..3999 generalized rank.
        within_block = (
            sample_residue
            if sample_residue < band_index
            else sample_residue - 1
        )
        general_rank = 4 * block + within_block
        geometry_index = (
            len(PUBLIC_GEOMETRIES)
            + _general_geometry_index(general_rank, seed, difficulty)
        )
        palette_subindex = (general_rank // 14 + 3 * seed) % 756
    # Reserve one palette-index residue for each difficulty band.  This keeps
    # the ordinary four-band producer stream pair-unique by construction while
    # forced scene_code still exposes all 3,024 ordered palettes in each geometry.
    palette_index = 4 * palette_subindex + band_index
    return geometry_index * PALETTE_COUNT + palette_index


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool/float/string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be a nonnegative literal integer (not bool/float/string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in _BAND_INDEX:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_code"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    requested_code = overrides.get("scene_code")
    if requested_code is not None:
        if isinstance(requested_code, bool) or not isinstance(requested_code, int):
            raise TypeError("scene_code must be a literal integer")
        if not 0 <= requested_code < SCENE_COUNT:
            raise ValueError(f"scene_code must be in 0..{SCENE_COUNT - 1}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if requested_code is not None:
        scene_code = ctx.draw_int("scene_code", 0, SCENE_COUNT - 1)
    else:
        scheduled = _natural_scene_code(seed, sample_index, difficulty)
        scene_code = ctx.draw_int("scene_code", scheduled, scheduled)
    return _grid_from_code(scene_code)
