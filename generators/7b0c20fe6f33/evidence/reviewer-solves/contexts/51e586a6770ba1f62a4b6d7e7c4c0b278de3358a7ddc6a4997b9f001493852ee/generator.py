"""Input generator for ARC task 7b0c20fe6f33: translate by anchor vector.

A unique blue marker (1) and red marker (2) define a displacement.  The
complete connected green object (3) is copied by that displacement and the
copy is colored cyan (8); the input object and markers remain unchanged.

The four-example curriculum deliberately alternates canonical anchors with
larger motifs, legacy knight vectors, and cardinal vectors.  Consequently any
three demonstrations distinguish the full rule from the retained shortcuts.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7b0c20fe6f33"
TASK_ID = GENERATOR_ID
RULE_HASH = "6f9c816ac7aa"
VERSION = "3.0.0"
SUMMARY = (
    "A 9..16 zero-background grid contains exactly one blue source marker "
    "(1), exactly one red destination marker (2), and one connected green "
    "object (3) of 3..5 cells.  The marker displacement is one of sixteen "
    "supported vectors, including the three canonical long vectors, legacy "
    "knight vectors, and cardinal vectors.  Translating every green cell by "
    "that displacement stays in bounds and avoids the source object and both "
    "markers.  The rule preserves the input and paints the translated object "
    "cyan (8).  A four-position schedule supplies explicit witnesses against "
    "small-vector, first-three-cells, and filled-bounding-box shortcuts."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and cells are integer colors from {0,1,2,3}",
    "grid dimensions are independently 9..16",
    "there is exactly one blue marker and one red marker",
    "the green object is one of eleven connected 3..5-cell motifs",
    "the marker vector is one of sixteen declared displacement vectors",
    "translated green cells are in bounds and overlap neither source nor markers",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 10..12 or difficulty-aware 9..16",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 10..12 or difficulty-aware 9..16",
        "valid": "9..16",
    },
    "vector_choice": {
        "type": "int",
        "default": "scheduled profile choice",
        "valid": "0..15",
    },
    "motif_choice": {
        "type": "int",
        "default": "scheduled profile choice",
        "valid": "0..10",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = (
    "canonical",
    "extended",
    "legacy_bridge",
    "cardinal",
)

# Ordered so observe_overrides can recover the exact integer axis value.
VECTORS = (
    (1, 2),
    (2, 1),
    (-1, 2),
    (2, -1),
    (-2, -1),
    (-2, 1),
    (1, -2),
    (-1, -2),
    (4, 5),       # canonical train 0
    (-4, 3),      # canonical train 1
    (5, 1),       # canonical test 0
    (-3, -4),
    (0, 4),
    (4, 0),
    (0, -4),
    (-4, 0),
)
VECTOR_INDEX = {vector: index for index, vector in enumerate(VECTORS)}
LEGACY_NARROW_VECTORS = frozenset(VECTORS[:4])

# Every motif is normalized to top-left and four-connected.  The first four
# are rotations/reflections of the canonical three-cell L.
MOTIFS = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
)
MOTIF_INDEX = {motif: index for index, motif in enumerate(MOTIFS)}

_PROFILE_VECTORS = {
    "canonical": (8, 9, 10),
    "extended": (8, 9, 10, 11),
    "legacy_bridge": tuple(range(8)),
    "cardinal": (12, 13, 14, 15),
}
_PROFILE_MOTIFS = {
    "canonical": (0, 1, 2, 3),
    "extended": (6, 10),
    "legacy_bridge": (6, 10),
    "cardinal": (7, 8, 9),
}
_DIM_LIMITS = (9, 16)
_CANONICAL_SIZES = (10, 11, 12)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic four-position curriculum profile name."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_controls(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    bounds = {
        "grid_h": _DIM_LIMITS,
        "grid_w": _DIM_LIMITS,
        "vector_choice": (0, len(VECTORS) - 1),
        "motif_choice": (0, len(MOTIFS) - 1),
    }
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _scheduled_dimension(ctx, name, scheduled):
    # Explicit overrides always retain the full advertised axis domain.
    if name in ctx.overrides:
        return ctx.draw_int_strict(name, *_DIM_LIMITS)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _profile_axes(ctx, profile, sample_index):
    if profile == "canonical":
        side = _CANONICAL_SIZES[(sample_index // len(SCHEDULE_PROFILES)) % len(_CANONICAL_SIZES)]
        h = _scheduled_dimension(ctx, "grid_h", side)
        w = _scheduled_dimension(ctx, "grid_w", side)
    else:
        h = ctx.draw_int_diff("grid_h", *_DIM_LIMITS)
        w = ctx.draw_int_diff("grid_w", *_DIM_LIMITS)

    if "vector_choice" in ctx.overrides:
        vector_choice = ctx.draw_int_strict("vector_choice", 0, len(VECTORS) - 1)
    else:
        vector_choice = ctx.draw_choice("vector_choice", _PROFILE_VECTORS[profile])

    if "motif_choice" in ctx.overrides:
        motif_choice = ctx.draw_int_strict("motif_choice", 0, len(MOTIFS) - 1)
    else:
        motif_choice = ctx.draw_choice("motif_choice", _PROFILE_MOTIFS[profile])
    return h, w, vector_choice, motif_choice


def _translated(cells, vector):
    dr, dc = vector
    return {(r + dr, c + dc) for r, c in cells}


def _candidate_motif_anchors(h, w, motif, vector):
    max_r = max(r for r, _ in motif)
    max_c = max(c for _, c in motif)
    anchors = []
    for base_r in range(h - max_r):
        for base_c in range(w - max_c):
            source = {(base_r + r, base_c + c) for r, c in motif}
            target = _translated(source, vector)
            if source & target:
                continue
            if all(0 <= r < h and 0 <= c < w for r, c in target):
                anchors.append((base_r, base_c))
    return anchors


def _candidate_marker_anchors(h, w, vector):
    dr, dc = vector
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if 0 <= r + dr < h and 0 <= c + dc < w
    ]


def _choose_layout(ctx, h, w, motif, vector):
    motif_anchors = _candidate_motif_anchors(h, w, motif, vector)
    marker_anchors = _candidate_marker_anchors(h, w, vector)
    rng = ctx.draw_rng("layout")
    rng.shuffle(motif_anchors)
    rng.shuffle(marker_anchors)

    for base_r, base_c in motif_anchors:
        source = {(base_r + r, base_c + c) for r, c in motif}
        target = _translated(source, vector)
        forbidden = source | target
        for marker in marker_anchors:
            red = (marker[0] + vector[0], marker[1] + vector[1])
            if marker not in forbidden and red not in forbidden:
                return source, marker, red
    raise RuntimeError(
        f"no constructive layout for shape={h}x{w}, motif={motif}, vector={vector}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, vector_choice, motif_choice = _profile_axes(ctx, profile, sample_index)
    vector = VECTORS[vector_choice]
    motif = MOTIFS[motif_choice]
    source, blue, red = _choose_layout(ctx, h, w, motif, vector)

    grid = full_grid(h, w, 0)
    grid[blue[0]][blue[1]] = 1
    grid[red[0]][red[1]] = 2
    for r, c in source:
        grid[r][c] = 3

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive sampler violated its contract: {errors}")
    return grid


def _positions(grid, color):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _scene(grid):
    blue = _positions(grid, 1)
    red = _positions(grid, 2)
    green = _positions(grid, 3)
    if len(blue) != 1 or len(red) != 1 or not green:
        raise ValueError("grid does not contain one marker pair and a green object")
    blue_cell = next(iter(blue))
    red_cell = next(iter(red))
    vector = (red_cell[0] - blue_cell[0], red_cell[1] - blue_cell[1])
    return blue_cell, red_cell, green, vector


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe axes from invalid grid: {errors}")
    _, _, green, vector = _scene(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "vector_choice": VECTOR_INDEX[vector],
        "motif_choice": MOTIF_INDEX[_normalize(green)],
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
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"]

    h, w = len(grid), width
    errors = []
    if not (_DIM_LIMITS[0] <= h <= _DIM_LIMITS[1]):
        errors.append(f"grid_h={h} outside 9..16")
    if not (_DIM_LIMITS[0] <= w <= _DIM_LIMITS[1]):
        errors.append(f"grid_w={w} outside 9..16")
    if any(type(value) is not int or value not in {0, 1, 2, 3} for row in grid for value in row):
        errors.append("cells must be integer input colors from {0,1,2,3}")
        return errors

    blue = _positions(grid, 1)
    red = _positions(grid, 2)
    green = _positions(grid, 3)
    if len(blue) != 1 or len(red) != 1:
        errors.append(
            f"expected one blue marker and one red marker, found {len(blue)} and {len(red)}"
        )
        return errors
    if not 3 <= len(green) <= 5:
        errors.append(f"expected a 3..5-cell green object, found {len(green)}")
        return errors

    motif = _normalize(green)
    if motif not in MOTIF_INDEX:
        errors.append("green object is not one of the supported connected motifs")

    blue_cell = next(iter(blue))
    red_cell = next(iter(red))
    vector = (red_cell[0] - blue_cell[0], red_cell[1] - blue_cell[1])
    if vector not in VECTOR_INDEX:
        errors.append(f"marker displacement {vector} is outside the supported vector set")
        return errors

    target = _translated(green, vector)
    if any(not (0 <= r < h and 0 <= c < w) for r, c in target):
        errors.append("a translated green cell goes out of bounds")
    if target & green:
        errors.append("translated green cells overlap the source object")
    if target & {blue_cell, red_cell}:
        errors.append("translated green cells overlap a marker")
    return errors


def strict_canonical_like(grid):
    """All generated/canonical scenes obey the exact executable rule contract."""
    return self_check(grid)


def _apply_with_sources(grid, sources):
    blue, red, _, vector = _scene(grid)
    del blue, red
    dr, dc = vector
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            source_position = (r - dr, c - dc)
            if value in (1, 2):
                out[r][c] = value
            elif source_position in sources:
                out[r][c] = 8
            elif value != 0:
                out[r][c] = value
    return out


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"invalid rule input: {errors}")
    return _apply_with_sources(grid, _positions(grid, 3))


def _legacy_knight_only(grid):
    _, _, green, vector = _scene(grid)
    if vector not in LEGACY_NARROW_VECTORS:
        return deepcopy(grid)
    return _apply_with_sources(grid, green)


def _copy_first_three(grid):
    green = sorted(_positions(grid, 3))[:3]
    return _apply_with_sources(grid, set(green))


def _filled_bounding_box(grid):
    green = _positions(grid, 3)
    min_r = min(r for r, _ in green)
    max_r = max(r for r, _ in green)
    min_c = min(c for _, c in green)
    max_c = max(c for _, c in green)
    box = {
        (r, c)
        for r in range(min_r, max_r + 1)
        for c in range(min_c, max_c + 1)
    }
    return _apply_with_sources(grid, box)


def _non_legacy_vector(grid):
    return _scene(grid)[3] not in LEGACY_NARROW_VECTORS


def _motif_more_than_three(grid):
    return len(_positions(grid, 3)) > 3


def _non_rectangular_motif(grid):
    green = _positions(grid, 3)
    rows = [r for r, _ in green]
    columns = [c for _, c in green]
    area = (max(rows) - min(rows) + 1) * (max(columns) - min(columns) + 1)
    return len(green) < area


SEMANTIC_RIVALS = {
    "legacy_knight_only": _legacy_knight_only,
    "copy_first_three": _copy_first_three,
    "filled_bounding_box": _filled_bounding_box,
}
CANONICAL_SHORTCUTS = {
    "copy_first_three": _copy_first_three,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "non_legacy_vector": _non_legacy_vector,
    "motif_more_than_three": _motif_more_than_three,
    "non_rectangular_motif": _non_rectangular_motif,
}
WITNESS_RIVALS = {
    "non_legacy_vector": ["legacy_knight_only"],
    "motif_more_than_three": ["copy_first_three"],
    "non_rectangular_motif": ["filled_bounding_box"],
}


def lesson_identifiable(demos, query):
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demonstration {index} must contain input and output grids")
            continue
        try:
            if rule_mirror(pair["input"]) != pair["output"]:
                reasons.append(f"demonstration {index} output disagrees with the canonical rule")
        except Exception as exc:
            reasons.append(f"demonstration {index} is invalid: {type(exc).__name__}: {exc}")
    try:
        if rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the canonical rule")
    except Exception as exc:
        reasons.append(f"query is invalid: {type(exc).__name__}: {exc}")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query answer")
    return reasons
