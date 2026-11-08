"""Input generator for “Match a prototype family up to symmetry”.

Three equal panels are separated by full-height color-8 columns.  The first two
panels contain prototype supports; the third contains a rotated or reflected
instance of exactly one prototype in a new color.  The selected Racket rule
returns the displayed prototype orientation, tightly cropped and recolored with
the query color.

The sampler deliberately gives both prototypes the same area.  Solving therefore
requires support geometry under the full D4 symmetry group rather than the cell-
count shortcut that fits most canonical demonstrations.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a51a8e285ce9"
TASK_ID = GENERATOR_ID
RULE_HASH = "d76e03446f2a"
VERSION = "4.0.0"
SUMMARY = (
    "Three equal panels, separated by full-height color-8 columns, contain two "
    "same-area prototype polyominoes and a differently colored query. Match the "
    "query to exactly one prototype under any rotation or reflection; output the "
    "displayed prototype support tightly cropped and recolored with the query color."
)

EXAMPLES_NEEDED = 4
INVARIANTS = [
    "the width is 3*panel_w+2 and the two geometric separator columns are color 8",
    "each panel contains one connected, monochromatic nonzero support",
    "the query matches exactly one prototype under the eight D4 symmetries",
    "generated prototypes have equal area, distinct D4 orbits, and eight-element orbits",
    "the output is the displayed matched prototype support in the query color",
]

_CODES = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
_ROTATIONS = _CODES[:4]
_REFLECTIONS = _CODES[4:]
# Interleaving rotations/reflections makes every four consecutive examples show
# both match roles and at least one genuinely reflection-only query.
_TEACHING_CODES = ("id", "fh", "r1", "fv", "r2", "tr", "r3", "atr")
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 4..7", "valid": "4..7"},
    "panel_w": {"type": "int", "default": "scheduled 4..7", "valid": "4..7"},
    "prototype_size": {"type": "int", "default": "difficulty schedule", "valid": "5..8"},
    "match_index": {"type": "int", "default": "alternates 0,1", "valid": "0..1"},
    "transform": {"type": "enum", "default": "teaching schedule", "valid": "id|r1|r2|r3|fh|fv|tr|atr"},
    "palette_size": {"type": "int", "default": "scheduled 4 or 5", "valid": "4..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_INT_BOUNDS = {
    "grid_h": (4, 7),
    "panel_w": (4, 7),
    "prototype_size": (5, 8),
    "match_index": (0, 1),
    "palette_size": (4, 5),
}
_SIZE_SCHEDULES = {
    None: (5, 6, 7, 8, 5, 7, 6, 8),
    "easy": (5, 5, 6, 6, 5, 7, 6, 5),
    "medium": (5, 6, 7, 8, 6, 7, 8, 5),
    "hard": (7, 8, 8, 7, 8, 6, 8, 7),
}
_NONCORE_DIMS = {
    None: ((5, 4), (4, 5), (6, 5), (5, 6)),
    "easy": ((5, 4), (4, 5), (5, 5), (6, 4)),
    "medium": ((5, 6), (6, 5), (6, 6), (4, 7)),
    "hard": ((7, 7), (7, 6), (6, 7), (5, 7)),
}


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return tuple()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells):
    cells = _normalize(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _xform(cells, code):
    cells = _normalize(cells)
    h, w = _dims(cells)
    if code == "id":
        raw = cells
    elif code == "r1":
        raw = tuple((c, h - 1 - r) for r, c in cells)
    elif code == "r2":
        raw = tuple((h - 1 - r, w - 1 - c) for r, c in cells)
    elif code == "r3":
        raw = tuple((w - 1 - c, r) for r, c in cells)
    elif code == "fh":
        raw = tuple((r, w - 1 - c) for r, c in cells)
    elif code == "fv":
        raw = tuple((h - 1 - r, c) for r, c in cells)
    elif code == "tr":
        raw = tuple((c, r) for r, c in cells)
    elif code == "atr":
        raw = tuple((w - 1 - c, h - 1 - r) for r, c in cells)
    else:
        raise ValueError(f"unknown transform {code!r}")
    return _normalize(raw)


def _dihedral_set(cells):
    return frozenset(_xform(cells, code) for code in _CODES)


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _NEIGHBORS:
            q = (r + dr, c + dc)
            if q in cells and q not in seen:
                seen.add(q)
                stack.append(q)
    return seen == cells


@lru_cache(maxsize=None)
def _fixed_polyominoes(size):
    """All translation-normalized fixed polyominoes of ``size`` cells."""
    if size < 1:
        return tuple()
    if size == 1:
        return (((0, 0),),)
    out = set()
    for shape in _fixed_polyominoes(size - 1):
        occupied = set(shape)
        for r, c in shape:
            for dr, dc in _NEIGHBORS:
                q = (r + dr, c + dc)
                if q not in occupied:
                    out.add(_normalize((*shape, q)))
    return tuple(sorted(out))


@lru_cache(maxsize=None)
def _shape_catalog(size, limit):
    """One deterministic representative per asymmetric free-polyomino class."""
    representatives = {}
    for shape in _fixed_polyominoes(size):
        orbit = _dihedral_set(shape)
        representative = min(orbit)
        representatives[representative] = representative
    result = []
    for shape in sorted(representatives):
        h, w = _dims(shape)
        if h <= limit and w <= limit and len(_dihedral_set(shape)) == 8:
            result.append(shape)
    return tuple(result)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_BOUNDS:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            lo, hi = _INT_BOUNDS[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "transform":
            if type(value) is not str:
                raise ValueError(f"transform must be a string, not {type(value).__name__}")
            if value not in _CODES:
                raise ValueError(f"transform={value!r} not in {_CODES}")


def _scheduled_defaults(seed, sample_index, difficulty):
    band = difficulty if difficulty in _SIZE_SCHEDULES else None
    # Two thirds of indices anchor the canonical 4x14 scale. Non-core indices
    # still cover larger panels and make difficulty bands visibly different.
    core = seed % 2 == 0 or sample_index % 2 == 0 or sample_index % 3 == 0
    if core:
        h, panel_w = 4, 4
    else:
        choices = _NONCORE_DIMS[band]
        h, panel_w = choices[(sample_index // 6) % len(choices)]
    return {
        "grid_h": h,
        "panel_w": panel_w,
        "prototype_size": _SIZE_SCHEDULES[band][sample_index % 8],
        "match_index": sample_index % 2,
        "transform": _TEACHING_CODES[sample_index % 8],
        "palette_size": 4 if sample_index % 3 == 0 else 5,
    }


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return sample_index % 8


SCHEDULE_PROFILES = tuple(range(8))


def _draw_axes(seed, sample_index, difficulty, overrides):
    effective = _scheduled_defaults(seed, sample_index, difficulty)
    effective.update({name: value for name, value in overrides.items() if value is not None})
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    values = {
        "grid_h": ctx.draw_int("grid_h", 4, 7),
        "panel_w": ctx.draw_int("panel_w", 4, 7),
        "prototype_size": ctx.draw_int("prototype_size", 5, 8),
        "match_index": ctx.draw_int("match_index", 0, 1),
        "transform": ctx.draw_choice("transform", _CODES),
        "palette_size": ctx.draw_int("palette_size", 4, 5),
    }
    return ctx, values


def _prototype_pair(ctx, size, limit):
    catalog = _shape_catalog(size, limit)
    if len(catalog) < 2:
        raise RuntimeError(
            f"no constructive pair of asymmetric {size}-cell prototypes fits {limit}x{limit}"
        )
    first, second = ctx.draw_rng("prototype_families").sample(catalog, 2)
    orientations = ctx.draw_rng("prototype_orientations")
    return (
        _xform(first, orientations.choice(_CODES)),
        _xform(second, orientations.choice(_CODES)),
    )


def _object_colors(ctx, palette_size):
    rng = ctx.draw_rng("object_colors")
    non_separator = [1, 2, 3, 4, 5, 6, 7, 9]
    if palette_size == 5:
        return tuple(rng.sample(non_separator, 3))
    other_proto, query = rng.sample(non_separator, 2)
    proto_colors = [8, other_proto]
    rng.shuffle(proto_colors)
    return proto_colors[0], proto_colors[1], query


def _place(grid, panel_w, panel_index, cells, color, rng):
    shape_h, shape_w = _dims(cells)
    max_r = len(grid) - shape_h
    max_c = panel_w - shape_w
    if max_r < 0 or max_c < 0:
        raise RuntimeError("selected prototype does not fit its panel")
    top = rng.randint(0, max_r)
    left_local = rng.randint(0, max_c)
    panel_left = panel_index * (panel_w + 1)
    for r, c in cells:
        grid[top + r][panel_left + left_local + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx, axes = _draw_axes(seed, sample_index, difficulty, overrides)
    h = axes["grid_h"]
    panel_w = axes["panel_w"]
    prototypes = _prototype_pair(ctx, axes["prototype_size"], min(h, panel_w))
    query = _xform(prototypes[axes["match_index"]], axes["transform"])
    colors = _object_colors(ctx, axes["palette_size"])

    grid = full_grid(h, 3 * panel_w + 2, 0)
    for separator in (panel_w, 2 * panel_w + 1):
        for r in range(h):
            grid[r][separator] = 8
    position_rng = ctx.draw_rng("object_positions")
    _place(grid, panel_w, 0, prototypes[0], colors[0], position_rng)
    _place(grid, panel_w, 1, prototypes[1], colors[1], position_rng)
    _place(grid, panel_w, 2, query, colors[2], position_rng)
    return grid


def _analyze_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be non-empty lists")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer ARC colors 0..9")
    if (w - 2) % 3:
        raise ValueError("width must equal 3*panel_w+2")
    panel_w = (w - 2) // 3
    if panel_w < 1:
        raise ValueError("panel width must be positive")
    separators = (panel_w, 2 * panel_w + 1)
    if any(grid[r][c] != 8 for c in separators for r in range(h)):
        raise ValueError("the two geometric separator columns must be full-height color 8")

    panels = []
    for panel_index in range(3):
        panel_left = panel_index * (panel_w + 1)
        raw = tuple(
            (r, c)
            for r in range(h)
            for c in range(panel_w)
            if grid[r][panel_left + c] != 0
        )
        if not raw:
            raise ValueError(f"panel {panel_index} is empty")
        colors = {grid[r][panel_left + c] for r, c in raw}
        if len(colors) != 1:
            raise ValueError(f"panel {panel_index} must contain one nonzero object color")
        support = _normalize(raw)
        if not _connected(support):
            raise ValueError(f"panel {panel_index} support must be 4-connected")
        panels.append({"support": support, "color": next(iter(colors)), "raw": raw})
    if len({panel["color"] for panel in panels}) != 3:
        raise ValueError("the two prototype colors and query color must be distinct")

    prototypes = panels[:2]
    query = panels[2]
    matches = [
        index
        for index, prototype in enumerate(prototypes)
        if query["support"] in _dihedral_set(prototype["support"])
    ]
    if len(matches) != 1:
        raise ValueError(f"query must match exactly one prototype under D4; got {matches}")
    return {
        "h": h,
        "w": w,
        "panel_w": panel_w,
        "panels": panels,
        "prototypes": prototypes,
        "query": query,
        "match_index": matches[0],
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        _analyze_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _support_grid(cells, color):
    cells = _normalize(cells)
    h, w = _dims(cells)
    out = full_grid(h, w, 0)
    for r, c in cells:
        out[r][c] = color
    return out


def rule_mirror(grid):
    """Independent-of-RNG Python mirror used only by tests and semantic rivals."""
    info = _analyze_grid(grid)
    prototype = info["prototypes"][info["match_index"]]
    return _support_grid(prototype["support"], info["query"]["color"])


def observe_overrides(grid):
    """Recover every exact advertised axis from returned pixels."""
    info = _analyze_grid(grid)
    prototype = info["prototypes"][info["match_index"]]["support"]
    query = info["query"]["support"]
    codes = [code for code in _CODES if _xform(prototype, code) == query]
    return {
        "grid_h": info["h"],
        "panel_w": info["panel_w"],
        # Generated prototypes have equal area; query area is the same exact axis.
        "prototype_size": len(query),
        "match_index": info["match_index"],
        # Generated supports are asymmetric, hence unique. Canonical symmetric
        # supports may admit aliases; the first fixed code is deterministic.
        "transform": codes[0],
        "palette_size": len({value for row in grid for value in row}),
    }


def _output_for_index(info, index, *, query_orientation=False, prototype_color=False):
    cells = info["query"]["support"] if query_orientation else info["prototypes"][index]["support"]
    color = info["prototypes"][index]["color"] if prototype_color else info["query"]["color"]
    return _support_grid(cells, color)


def _always_first(grid):
    info = _analyze_grid(grid)
    return _output_for_index(info, 0)


def _count_then_second(grid):
    """Canonical-fitting shortcut: unique equal-count match, otherwise panel 1."""
    info = _analyze_grid(grid)
    query_size = len(info["query"]["support"])
    candidates = [i for i, p in enumerate(info["prototypes"]) if len(p["support"]) == query_size]
    index = candidates[0] if len(candidates) == 1 else 1
    return _output_for_index(info, index)


def _rotations_only(grid):
    info = _analyze_grid(grid)
    query = info["query"]["support"]
    candidates = [
        i
        for i, prototype in enumerate(info["prototypes"])
        if query in {_xform(prototype["support"], code) for code in _ROTATIONS}
    ]
    return _output_for_index(info, candidates[0] if candidates else 0)


def _query_orientation(grid):
    info = _analyze_grid(grid)
    return _output_for_index(info, info["match_index"], query_orientation=True)


def _prototype_color(grid):
    info = _analyze_grid(grid)
    return _output_for_index(info, info["match_index"], prototype_color=True)


SEMANTIC_RIVALS = {
    "always_first": _always_first,
    "count_then_second": _count_then_second,
    "rotations_only": _rotations_only,
    "query_orientation": _query_orientation,
    "prototype_color": _prototype_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"count_then_second": _count_then_second}


def _witness(grid, predicate, rivals):
    try:
        info = _analyze_grid(grid)
        if not predicate(info):
            return False
        expected = rule_mirror(grid)
        return all(SEMANTIC_RIVALS[name](grid) != expected for name in rivals)
    except (TypeError, ValueError):
        return False


def _equal_area(info):
    return len(info["prototypes"][0]["support"]) == len(info["prototypes"][1]["support"])


def _equal_area_match_first(grid):
    return _witness(grid, lambda info: _equal_area(info) and info["match_index"] == 0, ("count_then_second",))


def _equal_area_match_second(grid):
    return _witness(grid, lambda info: _equal_area(info) and info["match_index"] == 1, ("always_first",))


def _reflection_required(grid):
    def predicate(info):
        prototype = info["prototypes"][info["match_index"]]["support"]
        query = info["query"]["support"]
        return query not in {_xform(prototype, code) for code in _ROTATIONS}
    return _witness(grid, predicate, ("rotations_only",))


def _canonical_orientation_differs(grid):
    return _witness(
        grid,
        lambda info: info["query"]["support"] != info["prototypes"][info["match_index"]]["support"],
        ("query_orientation",),
    )


def _recolor_required(grid):
    return _witness(
        grid,
        lambda info: info["query"]["color"] != info["prototypes"][info["match_index"]]["color"],
        ("prototype_color",),
    )


SEMANTIC_WITNESSES = {
    "equal_area_match_first": _equal_area_match_first,
    "equal_area_match_second": _equal_area_match_second,
    "reflection_required": _reflection_required,
    "canonical_orientation_differs": _canonical_orientation_differs,
    "recolor_required": _recolor_required,
}
WITNESS_RIVALS = {
    "equal_area_match_first": ["count_then_second"],
    "equal_area_match_second": ["always_first"],
    "reflection_required": ["rotations_only"],
    "canonical_orientation_differs": ["query_orientation"],
    "recolor_required": ["prototype_color"],
}


def lesson_identifiable(demos, query):
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query input is invalid: {query_errors[0]}")

    valid = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        valid.append(demo)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid and all(competitor(demo["input"]) == demo["output"] for demo in valid):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def mutation_fixtures():
    """Task-semantic malformed near-misses that self_check must reject."""
    lawful = generate(
        11,
        1,
        grid_h=5,
        panel_w=5,
        prototype_size=6,
        match_index=1,
        transform="fh",
        palette_size=5,
    )
    info = _analyze_grid(lawful)
    panel_w = info["panel_w"]

    missing_separator = [row[:] for row in lawful]
    missing_separator[0][panel_w] = 0

    empty_query = [row[:] for row in lawful]
    qleft = 2 * (panel_w + 1)
    for r in range(len(empty_query)):
        for c in range(qleft, qleft + panel_w):
            empty_query[r][c] = 0

    ambiguous = [row[:] for row in lawful]
    p1left = panel_w + 1
    for r in range(len(ambiguous)):
        for c in range(p1left, p1left + panel_w):
            ambiguous[r][c] = 0
    source = info["prototypes"][0]
    target_color = info["prototypes"][1]["color"]
    for r, c in source["raw"]:
        ambiguous[r][p1left + c] = target_color

    return (
        ("missing_separator", missing_separator),
        ("empty_query", empty_query),
        ("ambiguous_prototypes", ambiguous),
    )
