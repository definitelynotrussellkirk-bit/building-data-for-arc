"""Horizontal-mirror completion with exact controls and lesson witnesses.

Racket owns labels.  Every original orange (7) cell is copied to the
horizontally reflected row ``h - 1 - r`` in the same column.  Inputs exclude
centerline cells and already-completed mirror pairs so every generated marker
has an observable completion.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b22fce018c84"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "149529c7164c"
SUMMARY = (
    "Copy every orange (7) source cell across the horizontal midline, "
    "preserving the original source and its column."
)
INVARIANTS = [
    "rectangular 7..14 by 7..14 grid with background zero and orange sources",
    "sources never occupy an odd-height centerline",
    "at most one endpoint of each horizontal mirror orbit is occupied initially",
    "every declared override is exact and observable in the returned grid",
]
PALETTE_KINDS = ("default",)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical or difficulty-banded",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical or difficulty-banded",
        "valid": "7..14",
    },
    "n_markers": {
        "type": "int",
        "default": "3..6 by scheduled profile",
        "valid": "2..8",
    },
    "position_bias": {
        "type": "str",
        "default": "scheduled top_half, bottom_half or mixed",
        "valid": "top_half|bottom_half|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_top",
    "top_adjacency",
    "bottom_column",
    "mixed_dual",
)
MIN_STRICT_FRAC = 0.20

_CANONICAL_SHAPES = ((8, 10), (10, 9), (12, 12), (8, 11), (10, 12))
_INT_RANGES = {
    "grid_h": (7, 14),
    "grid_w": (7, 14),
    "n_markers": (2, 8),
}
_POSITION_BIASES = ("top_half", "bottom_half", "mixed")


def _normalize(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override keys: " + ", ".join(sorted(unknown)))
    clean = {name: value for name, value in overrides.items() if value is not None}
    for name, (lo, hi) in _INT_RANGES.items():
        if name in clean and (type(clean[name]) is not int or not lo <= clean[name] <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if "position_bias" in clean:
        value = clean["position_bias"]
        if not isinstance(value, str) or value not in _POSITION_BIASES:
            raise ValueError(f"position_bias must be one of {_POSITION_BIASES}")
    return clean


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile for a sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _top_rows(height):
    return [row for row in range(height) if 2 * row < height - 1]


def _bottom_rows(height):
    return [height - 1 - row for row in reversed(_top_rows(height))]


def _side(row, height):
    if 2 * row < height - 1:
        return "top"
    if 2 * row > height - 1:
        return "bottom"
    return "center"


def _orbit(row, col, height):
    return (min(row, height - 1 - row), col)


def _cells(grid):
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 7
    ]


def _copy_with(grid, selected, transform):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row, col in selected:
        target_row, target_col = transform(row, col, height, width)
        out[target_row][target_col] = 7
    return out


def _mirror_all(grid):
    return _copy_with(grid, _cells(grid), lambda r, c, h, w: (h - 1 - r, c))


def _identity(grid):
    return [list(row) for row in grid]


def _rotate_180_add(grid):
    return _copy_with(grid, _cells(grid), lambda r, c, h, w: (h - 1 - r, w - 1 - c))


def _vertical_add(grid):
    return _copy_with(grid, _cells(grid), lambda r, c, h, w: (r, w - 1 - c))


def _top_only(grid):
    height = len(grid)
    selected = [(row, col) for row, col in _cells(grid) if _side(row, height) == "top"]
    return _copy_with(grid, selected, lambda r, c, h, w: (h - 1 - r, c))


def _bottom_only(grid):
    height = len(grid)
    selected = [(row, col) for row, col in _cells(grid) if _side(row, height) == "bottom"]
    return _copy_with(grid, selected, lambda r, c, h, w: (h - 1 - r, c))


def _isolated_only(grid):
    height, width = len(grid), len(grid[0])
    occupied = set(_cells(grid))
    selected = [
        (row, col)
        for row, col in occupied
        if not any(
            (row + dr, col + dc) in occupied
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= row + dr < height and 0 <= col + dc < width
        )
    ]
    return _copy_with(grid, selected, lambda r, c, h, w: (h - 1 - r, c))


def _first_per_row(grid):
    selected = []
    seen = set()
    for row, col in _cells(grid):
        if row not in seen:
            selected.append((row, col))
            seen.add(row)
    return _copy_with(grid, selected, lambda r, c, h, w: (h - 1 - r, c))


def _first_per_column(grid):
    selected = []
    seen = set()
    for row, col in _cells(grid):
        if col not in seen:
            selected.append((row, col))
            seen.add(col)
    return _copy_with(grid, selected, lambda r, c, h, w: (h - 1 - r, c))


def _first_three(grid):
    return _copy_with(grid, _cells(grid)[:3], lambda r, c, h, w: (h - 1 - r, c))


SEMANTIC_RIVALS = {
    "identity": _identity,
    "rotate_180_add": _rotate_180_add,
    "vertical_add": _vertical_add,
    "top_only": _top_only,
    "bottom_only": _bottom_only,
    "isolated_only": _isolated_only,
    "first_per_row": _first_per_row,
    "first_per_column": _first_per_column,
    "first_three": _first_three,
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("top_only", "isolated_only", "first_per_row", "first_per_column")
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _rival_witness(name):
    rival = SEMANTIC_RIVALS[name]
    return lambda grid: rival(grid) != _mirror_all(grid)


SEMANTIC_WITNESSES = {
    "nonidentity": _rival_witness("identity"),
    "column_preserved": _rival_witness("rotate_180_add"),
    "row_reflected": _rival_witness("vertical_add"),
    "bottom_source": _rival_witness("top_only"),
    "top_source": _rival_witness("bottom_only"),
    "adjacent_sources": _rival_witness("isolated_only"),
    "same_row_sources": _rival_witness("first_per_row"),
    "same_column_sources": _rival_witness("first_per_column"),
    "more_than_three_sources": _rival_witness("first_three"),
}
WITNESS_RIVALS = {
    "nonidentity": ["identity"],
    "column_preserved": ["rotate_180_add"],
    "row_reflected": ["vertical_add"],
    "bottom_source": ["top_only"],
    "top_source": ["bottom_only"],
    "adjacent_sources": ["isolated_only"],
    "same_row_sources": ["first_per_row"],
    "same_column_sources": ["first_per_column"],
    "more_than_three_sources": ["first_three"],
}


def _default_dimensions(profile, difficulty, rng):
    if profile == "canonical_top":
        return rng.choice(_CANONICAL_SHAPES)
    bands = {
        "easy": ((7, 9), (7, 10)),
        "medium": ((9, 12), (9, 12)),
        "hard": ((12, 14), (12, 14)),
    }
    h_range, w_range = bands[difficulty or "medium"]
    return rng.randint(*h_range), rng.randint(*w_range)


def _default_marker_count(profile, rng):
    if profile == "canonical_top":
        return 3 if rng.randrange(4) else 4
    return {"top_adjacency": 5, "bottom_column": 5, "mixed_dual": 6}[profile]


def _default_bias(profile):
    return {
        "canonical_top": "top_half",
        "top_adjacency": "top_half",
        "bottom_column": "bottom_half",
        "mixed_dual": "mixed",
    }[profile]


def _reserved_positions(height, width, count, bias, profile, rng):
    """Return profile witnesses when the requested count/side can support them."""
    top = _top_rows(height)
    bottom = _bottom_rows(height)
    if profile == "canonical_top" and bias == "top_half" and count <= min(len(top), width):
        rows = rng.sample(top, count)
        cols = rng.sample(range(width), count)
        return list(zip(rows, cols))

    if profile == "top_adjacency" and count >= 2 and bias != "mixed":
        rows = top if bias == "top_half" else bottom
        row = rng.choice(rows)
        col = rng.randrange(width - 1)
        return [(row, col), (row, col + 1)]

    if profile == "bottom_column" and count >= 2 and bias != "mixed":
        rows = bottom if bias == "bottom_half" else top
        start = rng.randrange(len(rows) - 1)
        col = rng.randrange(width)
        return [(rows[start], col), (rows[start + 1], col)]

    if profile == "mixed_dual" and bias == "mixed" and count >= 4:
        top_row = rng.choice(top)
        top_col = rng.randrange(width - 1)
        candidates = []
        for start in range(len(bottom) - 1):
            for bottom_col in range(width):
                reserved = [
                    (top_row, top_col),
                    (top_row, top_col + 1),
                    (bottom[start], bottom_col),
                    (bottom[start + 1], bottom_col),
                ]
                if len({_orbit(r, c, height) for r, c in reserved}) == len(reserved):
                    candidates.append(reserved)
        if not candidates:
            raise RuntimeError("mixed_dual profile has no collision-free anchor placement")
        return rng.choice(candidates)
    return []


def _fill_positions(height, width, count, bias, reserved, rng):
    chosen = []
    used_orbits = set()
    for row, col in reserved:
        orbit = _orbit(row, col, height)
        if orbit not in used_orbits:
            chosen.append((row, col))
            used_orbits.add(orbit)

    top_candidates = [(r, c) for r in _top_rows(height) for c in range(width)]
    bottom_candidates = [(height - 1 - r, c) for r in _top_rows(height) for c in range(width)]
    rng.shuffle(top_candidates)
    rng.shuffle(bottom_candidates)

    def add_from(candidates):
        for point in candidates:
            orbit = _orbit(point[0], point[1], height)
            if orbit not in used_orbits:
                chosen.append(point)
                used_orbits.add(orbit)
                return True
        return False

    if bias == "mixed":
        if not any(_side(r, height) == "top" for r, _ in chosen):
            add_from(top_candidates)
        if len(chosen) < count and not any(_side(r, height) == "bottom" for r, _ in chosen):
            add_from(bottom_candidates)
        pools = [top_candidates, bottom_candidates]
        rng.shuffle(pools)
        while len(chosen) < count:
            progressed = False
            for candidates in pools:
                if len(chosen) < count and add_from(candidates):
                    progressed = True
            if not progressed:
                break
    else:
        candidates = top_candidates if bias == "top_half" else bottom_candidates
        while len(chosen) < count and add_from(candidates):
            pass

    if len(chosen) != count:
        raise ValueError("requested marker count exceeds available horizontal-mirror orbits")
    return chosen


def _make_grid(height, width, positions):
    grid = full_grid(height, width, 0)
    for row, col in positions:
        grid[row][col] = 7
    return grid


def _construct_grid(height, width, count, bias, profile, rng):
    # Different attempts shift profile anchors and fill order.  Reject only the
    # two geometric coincidences that would hide which axis is reflected.
    for _ in range(128):
        reserved = _reserved_positions(height, width, count, bias, profile, rng)
        positions = _fill_positions(height, width, count, bias, reserved, rng)
        grid = _make_grid(height, width, positions)
        authority = _mirror_all(grid)
        if (
            not self_check(grid)
            and authority != _rotate_180_add(grid)
            and authority != _vertical_add(grid)
        ):
            return grid
    raise RuntimeError("unable to construct an axis-disambiguating mirror instance")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    clean = _normalize(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("layout:" + profile)
    height, width = _default_dimensions(profile, difficulty, rng)
    count = _default_marker_count(profile, rng)
    bias = _default_bias(profile)

    height = clean.get("grid_h", height)
    width = clean.get("grid_w", width)
    count = clean.get("n_markers", count)
    bias = clean.get("position_bias", bias)

    # Record every public axis through the keyed provenance API after defaults
    # have adapted.  Singleton bounds are intentional: explicit values remain
    # exact across every difficulty band.
    height = ctx.draw_int("grid_h", height, height)
    width = ctx.draw_int("grid_w", width, width)
    count = ctx.draw_int("n_markers", count, count)
    bias = ctx.draw_choice("position_bias", [bias])

    return _construct_grid(height, width, count, bias, profile, rng)


def observe_overrides(grid):
    points = _cells(grid)
    height = len(grid)
    top = any(_side(row, height) == "top" for row, _ in points)
    bottom = any(_side(row, height) == "bottom" for row, _ in points)
    bias = "mixed" if top and bottom else "top_half" if top else "bottom_half"
    return {
        "grid_h": height,
        "grid_w": len(grid[0]),
        "n_markers": len(points),
        "position_bias": bias,
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
        return ["expected a rectangular grid"]
    height = len(grid)
    errors = []
    if not 7 <= height <= 14 or not 7 <= width <= 14:
        errors.append("grid dimensions must each be in 7..14")
    if any(type(value) is not int or value not in (0, 7) for row in grid for value in row):
        errors.append("cells must be integer colors 0 or 7")
        return errors
    points = _cells(grid)
    if not 2 <= len(points) <= 8:
        errors.append("expected 2..8 orange source markers")
    if any(_side(row, height) == "center" for row, _ in points):
        errors.append("odd-height centerline markers have no visible completion")
    occupied = set(points)
    if any((height - 1 - row, col) in occupied for row, col in points):
        errors.append("horizontal mirror endpoints must be empty in the input")
    if len(points) == 4:
        rows = sorted({row for row, _ in points})
        cols = sorted({col for _, col in points})
        if len(rows) == 1 and len(cols) == 4 and cols == list(range(cols[0], cols[0] + 4)):
            errors.append("a bare four-cell line is outside the teaching grammar")
        if (
            len(rows) == 2
            and len(cols) == 2
            and rows == list(range(rows[0], rows[0] + 2))
            and cols == list(range(cols[0], cols[0] + 2))
            and occupied == {(row, col) for row in rows for col in cols}
        ):
            errors.append("a bare solid 2x2 block is outside the teaching grammar")
    return errors


def strict_canonical_like(grid):
    reasons = self_check(grid)
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    points = _cells(grid)
    if (height, width) not in _CANONICAL_SHAPES or len(points) not in (3, 4):
        return ["expected a canonical shape with three or four markers"]
    if any(_side(row, height) != "top" for row, _ in points):
        return ["canonical sources are strictly above the horizontal midline"]
    if len({row for row, _ in points}) != len(points):
        return ["canonical sources occupy distinct rows"]
    if len({col for _, col in points}) != len(points):
        return ["canonical sources occupy distinct columns"]
    return []


def lesson_identifiable(demos, query):
    return [
        f"{name} fits every demo and disagrees on the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
