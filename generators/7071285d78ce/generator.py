"""Collision-free inputs for independently transposing each object locally.

The unchanged Racket authority paints each same-color 4-connected component's
transpose onto a BLANK output, anchored at its original bbox top-left. Input
and destination footprints may intersect; destinations of different objects
must not overlap in this sampler. Python transforms below are declared rivals
and witness diagnostics, never the label authority.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import (
    components, components_have_clearance, d4_transform, normalize,
)

GENERATOR_ID = "7071285d78ce"
TASK_ID = GENERATOR_ID
RULE_HASH = "9eb76f1bb8b7"
VERSION = "3.0.0"
SUMMARY = (
    "On a zero background, transpose each of 2..4 distinct-color, isolated "
    "4-connected objects about its own bbox top-left. Each object has 3..5 "
    "cells, is nonrectangular and changes under transpose. All destinations "
    "fit and are pairwise disjoint. Paint onto a blank same-size output. "
    "Alternate canonical-shaped tetromino lessons with broad lessons that "
    "include both a width-four asymmetric pentomino and a three-cell object, "
    "on 8..14 by 8..14 grids."
)
INVARIANTS = [
    "rectangular 8..14 by 8..14 integer grid, colors 0..9, background 0",
    "2..4 orthogonally non-touching blobs, with distinct nonzero colors",
    "each object has 3..5 cells, is nonrectangular and changes under transpose",
    "all local transposes fit in bounds and their destination cell sets are disjoint",
    "input-destination overlap is lawful: the reference paints a blank output",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_blobs", "all_solid_squares", "single_cell_blobs")
_COUNT_AXES = ("n_blobs", "palette_size", "n_distinct_colors")
_PALETTE_AXES = ("palette_kind", "texture")
_WARM = frozenset((2, 4, 6, 7, 9))
_COOL = frozenset((1, 3, 5, 8))
AXES = {
    "grid_h": {"type": "int", "default": "8..14; canonical core favors 8,9,10", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "8..14; canonical core favors 10,11,12", "valid": "8..14"},
    "n_blobs": {"type": "int", "default": "2..4; canonical core uses 2", "valid": "2..4",
                "aliases": ["palette_size", "n_distinct_colors"]},
    "palette_kind": {"type": "str", "default": "uniform palette class", "valid": "|".join(PALETTE_KINDS),
                     "aliases": ["texture"]},
    # Legacy descriptive controls have one supported value; they are not
    # independently variable semantic axes. The historical position name does
    # not exclude a lawful, nonidentity square-bbox object in the broad domain.
    "position_bias": {"type": "str", "default": "spaced_nonsquare_blobs", "valid": "spaced_nonsquare_blobs", "probe": "diagnostic"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse", "probe": "diagnostic"},
}
# Compatibility spellings are still exact, observed and regression-tested;
# they add no independent dimension to the advertised variation space.
AXIS_ALIASES = {"palette_size": "n_blobs", "n_distinct_colors": "n_blobs",
                "texture": "palette_kind"}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {left: a, right: b}
    for left, right in combinations(_COUNT_AXES, 2)
    for a in range(2, 5) for b in range(2, 5) if a != b
] + [
    {"palette_kind": a, "texture": b}
    for a in PALETTE_KINDS for b in PALETTE_KINDS if a != b
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical_core", "wide_witness")
MIN_STRICT_FRAC = 0.45


def schedule_profile(seed, sample_index, difficulty=None):
    """Two broad witnesses per four consecutive draws, for every seed/band."""
    phase = stable_rng(seed, f"{TASK_ID}|curriculum_phase", VERSION).randrange(2)
    return SCHEDULE_PROFILES[(phase + sample_index) % LESSON_SCHEDULE_PERIOD]


def _conflict(names):
    error = ValueError(f"incompatible exact aliases: {', '.join(names)} must agree")
    error.incompatible_axes = tuple(names)
    raise error


def _aliases(ctx, names, choices, default):
    requested = [name for name in names if ctx.overrides.get(name) is not None]
    if not requested:
        return ctx.draw_choice(names[0], default)
    values = [ctx.draw_choice(name, choices) for name in requested]
    if any(value != values[0] for value in values[1:]):
        _conflict(requested)
    return values[0]


def _extent(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


@lru_cache(maxsize=1)
def _shape_pool():
    """All oriented connected 3..5-cell nonrectangles that change on transpose.

    Grow normalized SETS of shapes, not a direction-biased random walk. Cache
    only immutable geometry; the sorted order makes keyed draws portable.
    """
    current = {((0, 0),)}
    eligible = []
    for size in range(2, 6):
        next_shapes = set()
        for shape in current:
            for r, c in shape:
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    point = r + dr, c + dc
                    if point not in shape:
                        next_shapes.add(normalize((*shape, point)))
        current = next_shapes
        if size >= 3:
            for shape in current:
                h, w = _extent(shape)
                if size < h * w and d4_transform(shape, 6) != shape:
                    eligible.append(shape)
    return tuple(sorted(eligible))


@lru_cache(maxsize=1)
def _shape_classes():
    pool = _shape_pool()
    canonical = tuple(s for s in pool if len(s) == 4 and _extent(s) == (3, 2))
    asymmetric_core = tuple(s for s in canonical if len({d4_transform(s, k) for k in range(8)}) == 8)
    wide = tuple(s for s in pool if len(s) == 5 and _extent(s) == (2, 4)
                 and len({d4_transform(s, k) for k in range(8)}) == 8)
    return canonical, asymmetric_core, wide


def _choose_shapes(ctx, count, core, *, compact=False):
    canonical, asymmetric_core, wide = _shape_classes()
    pool = canonical if core else _shape_pool()
    witness = asymmetric_core if core else wide
    if compact:
        pool = tuple(s for s in pool if max(_extent(s)) <= 3)
        if core:
            witness = tuple(s for s in witness if max(_extent(s)) <= 3)
    rng = ctx.draw_rng("compact_shapes" if compact else "object_shapes")
    shapes = [rng.choice(witness)]
    if not core:
        # Three-cell shapes are lawful but absent from canonical examples.
        # Keep one in EVERY broad draw so no holdout is their first lesson.
        shapes.append(rng.choice(tuple(s for s in pool if len(s) == 3)))
    for _ in range(count - len(shapes)):
        if core:
            favored = pool
        else:
            size = rng.choice((3, 4, 4) if ctx.difficulty == "easy" else
                              ((4, 5, 5) if ctx.difficulty == "hard" else (3, 4, 5)))
            favored = tuple(s for s in pool if len(s) == size)
        shapes.append(rng.choice(favored))
    return shapes


@lru_cache(maxsize=128)
def _palette_options(kind, count):
    default = tuple(range(1, count + 1))
    if kind == "default":
        return (default,)
    if kind == "warm":
        return tuple(combinations(sorted(_WARM), count))
    if kind == "cool":
        return tuple(combinations(sorted(_COOL), count))
    return tuple(p for p in combinations(range(1, 10), count)
                 if p != default and set(p) & _WARM and set(p) & _COOL)


def _placed_cells(shape, origin, transpose=False):
    r0, c0 = origin
    return {(r0 + (c if transpose else r), c0 + (r if transpose else c))
            for r, c in shape}


def _layout(ctx, h, w, shapes):
    rng = ctx.draw_rng("positions")
    for _ in range(12):
        blocked_sources, used_destinations = set(), set()
        placed = []
        for shape in shapes:
            side = max(_extent(shape))
            positions = [(r, c) for r in range(h - side + 1) for c in range(w - side + 1)]
            rng.shuffle(positions)
            for origin in positions:
                source = _placed_cells(shape, origin)
                target = _placed_cells(shape, origin, True)
                if source & blocked_sources or target & used_destinations:
                    continue
                placed.append((shape, origin))
                blocked_sources.update(source)
                blocked_sources.update((r + dr, c + dc) for r, c in source
                                       for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)))
                used_destinations.update(target)
                break
            else:
                break
        if len(placed) == len(shapes) and (h != w or any(r != c for _, (r, c) in placed)):
            return placed
    # At the 8x8 minimum, one 4x4 corner and three 3x3 corners fit with a
    # one-cell gap along shared sides. Preserve BOTH broad witnesses even
    # here; shrinking the wide object would create a held-out extent shortcut.
    core = schedule_profile(ctx.seed, ctx.sample_index) == "canonical_core"
    compact = _choose_shapes(ctx, len(shapes), core, compact=True)
    origins = [(0, 0), (0, w - 3), (h - 3, 0), (h - 3, w - 3)]
    if core:
        rng.shuffle(origins)
    else:
        corner = rng.randrange(4)
        large = [(0, 0), (0, w - 4), (h - 4, 0), (h - 4, w - 4)][corner]
        others = [origin for index, origin in enumerate(origins) if index != corner]
        rng.shuffle(others)
        origins = [large, *others]
    if h == w and len(shapes) == 2 and all(r == c for r, c in origins[:2]):
        origins[1], origins[2] = origins[2], origins[1]
    return list(zip(compact, origins))[:len(shapes)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - (set(AXES) | set(AXIS_ALIASES))
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    for name, value in overrides.items():
        if value is None:
            continue
        wanted = int if AXES[AXIS_ALIASES.get(name, name)]["type"] == "int" else str
        if type(value) is not wanted:
            raise ValueError(f"{name} must be {wanted.__name__}, not {type(value).__name__}")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        others = [name for name, value in overrides.items() if name != "texture" and value is not None]
        if others:
            _conflict(["texture", *others])
        return _draw_from_degenerate(texture, None)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = schedule_profile(seed, sample_index, difficulty) == "canonical_core"
    canonical_shape = ctx.draw_choice("canonical_canvas", ((10, 10), (9, 11), (8, 12)))
    dimensions = []
    for axis, anchor in zip(("grid_h", "grid_w"), canonical_shape):
        if overrides.get(axis) is not None:
            dimensions.append(ctx.draw_int_strict(axis, 8, 14))
        else:
            dimensions.append(ctx.draw_choice(axis, (anchor,) if core else tuple(range(8, 15))))
    h, w = dimensions
    count_defaults = (2,) if core else ((2, 2, 3, 4) if difficulty != "hard" else (2, 3, 4, 4))
    count = _aliases(ctx, _COUNT_AXES, tuple(range(2, 5)), count_defaults)
    kind = _aliases(ctx, _PALETTE_AXES, PALETTE_KINDS, PALETTE_KINDS)
    ctx.draw_choice("position_bias", ("spaced_nonsquare_blobs",))
    ctx.draw_choice("density", ("sparse",))
    rng = ctx.draw_rng("palette")
    colors = list(rng.choice(_palette_options(kind, count)))
    rng.shuffle(colors)
    shapes = _choose_shapes(ctx, count, core)
    placed = _layout(ctx, h, w, shapes)
    grid = full_grid(h, w, 0)
    for color, (shape, origin) in zip(colors, placed):
        for r, c in _placed_cells(shape, origin):
            grid[r][c] = color
    return grid


def _draw_from_degenerate(name, rng):
    """Deliberate invalid fixtures, outside the ordinary texture domain."""
    grid = full_grid(10, 10, 0)
    if name == "all_solid_squares":
        for color, r0, c0, side in ((4, 1, 1, 2), (6, 5, 5, 3)):
            for r in range(r0, r0 + side):
                for c in range(c0, c0 + side):
                    grid[r][c] = color
    elif name == "single_cell_blobs":
        grid[1][2], grid[5][7], grid[8][3] = 4, 6, 3
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9"]
    errors = []
    if not 8 <= h <= 14 or not 8 <= w <= 14:
        errors.append("grid dimensions outside 8..14")
    blobs = components(grid, same_color=True)
    if not 2 <= len(blobs) <= 4:
        errors.append("expected 2..4 blobs")
    if len({obj["color"] for obj in blobs}) != len(blobs):
        errors.append("blob colors are not distinct")
    if not components_have_clearance(grid, blobs, diagonal=False):
        errors.append("distinct blobs touch orthogonally")
    targets = set()
    for obj in blobs:
        shape = obj["norm"]
        bh, bw = _extent(shape)
        if not 3 <= len(shape) <= 5:
            errors.append("blob must contain 3..5 cells")
        if len(shape) == bh * bw:
            errors.append("blob is a solid rectangle")
        if d4_transform(shape, 6) == shape:
            errors.append("blob's local transpose is identity")
        r0, c0, _, _ = obj["bbox"]
        target = _placed_cells(shape, (r0, c0), True)
        if any(not 0 <= r < h or not 0 <= c < w for r, c in target):
            errors.append("blob transpose would go out of bounds")
        if targets & target:
            errors.append("transposed destinations of distinct blobs overlap")
        targets.update(target)
    return errors


def observe_overrides(grid):
    """Recover exact control values from pixels; no RNG or metadata lookup."""
    colors = {v for row in grid for v in row if v}
    count = len(colors)
    if colors == set(range(1, count + 1)):
        kind = "default"
    elif colors <= _WARM:
        kind = "warm"
    elif colors <= _COOL:
        kind = "cool"
    else:
        kind = "varied"
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_blobs": len(components(grid, same_color=True)),
            "palette_size": count, "n_distinct_colors": count,
            "palette_kind": kind, "texture": kind,
            "position_bias": "spaced_nonsquare_blobs", "density": "sparse"}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    blobs = components(grid, same_color=True)
    if len(blobs) != 2 or any(len(obj["cells"]) != 4 or _extent(obj["norm"]) != (3, 2) for obj in blobs):
        return ["canonical core has two four-cell blobs, each bbox 3x2"]
    return []


def _local_rival(grid, code=6, mode="all"):
    """Pure diagnostic transform; code=6 is used only to evaluate witnesses."""
    out = full_grid(len(grid), len(grid[0]), 0)
    blobs = components(grid, same_color=True)
    max_color = max((obj["color"] for obj in blobs), default=0)
    min_color = min((obj["color"] for obj in blobs), default=0)
    canonical = _canonical_shapes()
    for obj in blobs:
        shape = obj["norm"]
        bh, bw = _extent(shape)
        apply = (mode == "all" or (mode == "tall" and bh > bw)
                 or (mode == "four_cells" and len(shape) == 4)
                 or (mode == "canonical_extent" and len(shape) == 4 and (bh, bw) == (3, 2))
                 or (mode == "canonical_shapes" and shape in canonical)
                 or (mode == "at_least_four" and len(shape) >= 4)
                 or (mode == "extent_at_most_three" and max(bh, bw) <= 3)
                 or (mode == "max_color" and obj["color"] == max_color)
                 or (mode == "min_color" and obj["color"] == min_color))
        transformed = d4_transform(shape, code) if apply else shape
        r0, c0, _, _ = obj["bbox"]
        for r, c in transformed:
            rr, cc = r0 + r, c0 + c
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                out[rr][cc] = obj["color"]
    return out


def _canonical_shapes():
    # Exact observed normalized shapes; a RIVAL lookup, never sampler labels.
    return frozenset((
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((0, 1), (1, 0), (1, 1), (2, 1)),
    ))


def _identity(grid):
    return [list(row) for row in grid]


def _global_transpose(grid):
    return [list(row) for row in zip(*grid)]


def _cw(grid):
    return _local_rival(grid, 1)


def _half_turn(grid):
    return _local_rival(grid, 2)


def _ccw(grid):
    return _local_rival(grid, 3)


def _flip_lr(grid):
    return _local_rival(grid, 4)


def _flip_ud(grid):
    return _local_rival(grid, 5)


def _anti_transpose(grid):
    return _local_rival(grid, 7)


def _tall_only(grid):
    return _local_rival(grid, mode="tall")


def _size_four_only(grid):
    return _local_rival(grid, mode="four_cells")


def _canonical_extent_only(grid):
    return _local_rival(grid, mode="canonical_extent")


def _canonical_shapes_only(grid):
    return _local_rival(grid, mode="canonical_shapes")


def _max_color_only(grid):
    return _local_rival(grid, mode="max_color")


def _min_color_only(grid):
    return _local_rival(grid, mode="min_color")


def _ignore_three_cell_objects(grid):
    return _local_rival(grid, mode="at_least_four")


def _extent_at_most_three(grid):
    return _local_rival(grid, mode="extent_at_most_three")


def _has_wide_five(grid):
    return any(len(obj["cells"]) == 5 and _extent(obj["norm"]) == (2, 4)
               and len({d4_transform(obj["norm"], k) for k in range(8)}) == 8
               for obj in components(grid, same_color=True))


def _has_three_cells(grid):
    return any(len(obj["cells"]) == 3 for obj in components(grid, same_color=True))


CANONICAL_SHORTCUTS = {
    "tall_only": _tall_only,
    "size_four_only": _size_four_only,
    "canonical_extent_only": _canonical_extent_only,
    "canonical_shapes_only": _canonical_shapes_only,
    "ignore_three_cell_objects": _ignore_three_cell_objects,
    "extent_at_most_three": _extent_at_most_three,
}
LESSON_COMPETITORS = {
    "identity": _identity, "global_transpose": _global_transpose,
    "rotate_cw": _cw, "rotate_180": _half_turn, "rotate_ccw": _ccw,
    "flip_lr": _flip_lr, "flip_ud": _flip_ud, "anti_transpose": _anti_transpose,
    "max_color_only": _max_color_only, "min_color_only": _min_color_only,
    **CANONICAL_SHORTCUTS,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {"wide_asymmetric_pentomino": _has_wide_five,
                      "three_cell_object": _has_three_cells}
WITNESS_RIVALS = {
    "wide_asymmetric_pentomino": ["tall_only", "size_four_only", "canonical_extent_only",
                                  "canonical_shapes_only", "extent_at_most_three"],
    "three_cell_object": ["ignore_three_cell_objects"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; does not assert universal identifiability."""
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
