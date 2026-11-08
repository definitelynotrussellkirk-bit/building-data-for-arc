"""Generator for independently normalized union of the blue and red shapes.

The canonical rule finds all color-1 cells and all color-2 cells, translates
EACH color set independently to its own bounding-box top-left, overlays the two
normalized masks, and paints their union green (3) in the resulting tight grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "9cea0e6444f1"
TASK_ID = GENERATOR_ID
RULE_HASH = "fe554f47cd7a"
VERSION = "3.0.0"
SUMMARY = (
    "One connected blue shape (1) and one connected red shape (2) are placed "
    "apart on a zero background. Their independently normalized masks overlap "
    "and each contributes exclusive cells. The output top-left-aligns the two "
    "masks, takes their union, and paints it green (3). Alternating lawful "
    "lessons add a distant color-7 decoy pair that the rule ignores."
)
EXAMPLES_NEEDED = 3

_ORIGIN_KINDS = ("corner", "split")
_PLACEMENT_KINDS = ("horizontal", "vertical", "diagonal")
_DECOY_KINDS = ("none", "far_pair")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

INVARIANTS = [
    "exactly one 4-connected color-1 shape and one 4-connected color-2 shape",
    "the normalized shapes overlap and each has at least one exclusive cell",
    "the two source shapes are spatially separated before independent normalization",
    "the normalized union is non-solid, so filling its bbox is not a valid shortcut",
    "an optional color-7 far pair is ignored by the selected rule",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 9..16", "valid": "9..16"},
    "grid_w": {"type": "int", "default": "canonical-weighted 9..18", "valid": "9..18"},
    "n_one": {"type": "int", "default": "difficulty-weighted 4..8", "valid": "4..8"},
    "n_two": {"type": "int", "default": "difficulty-weighted 4..8", "valid": "4..8"},
    "origin_kind": {
        "type": "str",
        "default": "scheduled corner|split",
        "valid": "corner|split",
    },
    "placement_kind": {
        "type": "str",
        "default": "scheduled horizontal|vertical|diagonal",
        "valid": "horizontal|vertical|diagonal",
    },
    "decoy_kind": {
        "type": "str",
        "default": "scheduled none|far_pair",
        "valid": "none|far_pair",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _scheduled_choice(ctx, label, options, salt):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    offset = stable_rng(ctx.seed, f"{TASK_ID}|{salt}", VERSION).randrange(len(options))
    value = options[(ctx.sample_index + offset) % len(options)]
    return ctx.draw_choice(label, (value,))


def _exact_or_choice(ctx, label, lo, hi, choices):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, tuple(choices))


def _grid_dimensions(ctx, decoy_kind):
    # Every no-decoy default draw has an exact canonical input profile:
    # 9x9x3 or 11x11x3 (height, width, palette size). This preserves a clean
    # source-distribution anchor in every difficulty band while the alternating
    # decoy draws explore broader canvases.
    if decoy_kind == "none":
        offset = stable_rng(ctx.seed, f"{TASK_ID}|canonical-size", VERSION).randrange(2)
        size = (9, 11)[(ctx.sample_index // 2 + offset) % 2]
        h = _exact_or_choice(ctx, "grid_h", 9, 16, (size,))
        w = _exact_or_choice(ctx, "grid_w", 9, 18, (size,))
        return h, w

    ranges = {
        "easy": ((9, 11), (9, 12)),
        "medium": ((10, 14), (10, 15)),
        "hard": ((12, 16), (13, 18)),
    }
    (hlo, hhi), (wlo, whi) = ranges.get(ctx.difficulty, ((9, 16), (9, 18)))
    h = _exact_or_choice(ctx, "grid_h", 9, 16, range(hlo, hhi + 1))
    w = _exact_or_choice(ctx, "grid_w", 9, 18, range(wlo, whi + 1))
    return h, w


def _shape_size(ctx, label):
    bounds = {
        "easy": (4, 5),
        "medium": (5, 7),
        "hard": (7, 8),
    }.get(ctx.difficulty, (4, 8))
    return _exact_or_choice(ctx, label, 4, 8, range(bounds[0], bounds[1] + 1))


def _neighbors(cell):
    r, c = cell
    return tuple((r + dr, c + dc) for dr, dc in _CARDINAL)


def _grow_connected(seed_cells, allowed, target_size, rng):
    cells = set(seed_cells)
    while len(cells) < target_size:
        frontier = sorted(
            q
            for p in cells
            for q in _neighbors(p)
            if q in allowed and q not in cells
        )
        if not frontier:
            return None
        cells.add(rng.choice(frontier))
    return cells


def _shape_pair(ctx, n_one, n_two, origin_kind):
    """Construct two connected normalized masks with genuine partial overlap."""
    rng = ctx.draw_rng("normalized_shape_pair")
    universe = {(r, c) for r in range(4) for c in range(4)}
    if origin_kind == "corner":
        base = {(0, 0), (0, 1), (1, 0)}
    else:
        universe.remove((0, 0))
        base = {(0, 1), (1, 0), (1, 1)}

    for _ in range(500):
        max_core = min(min(n_one, n_two) - 1, 5)
        core_size = rng.randint(len(base), max_core)
        core = _grow_connected(base, universe, core_size, rng)
        if core is None:
            continue

        one = _grow_connected(core, universe, n_one, rng)
        if one is None:
            continue
        one_private = one - core
        two_allowed = universe - one_private
        two = _grow_connected(core, two_allowed, n_two, rng)
        if two is None:
            continue

        union = one | two
        uh = max(r for r, _ in union) + 1
        uw = max(c for _, c in union) + 1
        if not (one & two and one - two and two - one):
            continue
        if uh < 2 or uw < 2 or len(union) == uh * uw:
            continue
        return sorted(one), sorted(two)
    raise RuntimeError("could not construct a sparse partially-overlapping shape pair")


def _shape_size_hw(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _placement_origins(h, w, one, two, placement_kind, rng):
    ah, aw = _shape_size_hw(one)
    bh, bw = _shape_size_hw(two)
    if placement_kind == "horizontal":
        total_w = aw + 1 + bw
        if total_w > w or max(ah, bh) > h:
            return None
        row = rng.randint(0, h - max(ah, bh))
        left = rng.randint(0, w - total_w)
        if rng.randrange(2):
            return (row, left), (row, left + aw + 1)
        return (row, left + bw + 1), (row, left)

    if placement_kind == "vertical":
        total_h = ah + 1 + bh
        if total_h > h or max(aw, bw) > w:
            return None
        top = rng.randint(0, h - total_h)
        col = rng.randint(0, w - max(aw, bw))
        if rng.randrange(2):
            return (top, col), (top + ah + 1, col)
        return (top + bh + 1, col), (top, col)

    total_h = ah + 1 + bh
    total_w = aw + 1 + bw
    if total_h > h or total_w > w:
        return None
    top = rng.randint(0, h - total_h)
    left = rng.randint(0, w - total_w)
    one_above = bool(rng.randrange(2))
    one_left = bool(rng.randrange(2))
    if one_above:
        ar, br = top, top + ah + 1
    else:
        br, ar = top, top + bh + 1
    if one_left:
        ac, bc = left, left + aw + 1
    else:
        bc, ac = left, left + bw + 1
    return (ar, ac), (br, bc)


def _far_pair_candidates(grid):
    h, w = len(grid), len(grid[0])
    candidates = []
    for r in range(h - 4):
        for c in range(w - 4):
            for a, b in (((r, c), (r + 4, c + 4)), ((r, c + 4), (r + 4, c))):
                if grid[a[0]][a[1]] == 0 and grid[b[0]][b[1]] == 0:
                    candidates.append((a, b))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    origin_kind = _scheduled_choice(ctx, "origin_kind", _ORIGIN_KINDS, "origin")
    placement_kind = _scheduled_choice(
        ctx, "placement_kind", _PLACEMENT_KINDS, "placement"
    )
    decoy_kind = _scheduled_choice(ctx, "decoy_kind", _DECOY_KINDS, "decoy")
    h, w = _grid_dimensions(ctx, decoy_kind)
    n_one = _shape_size(ctx, "n_one")
    n_two = _shape_size(ctx, "n_two")

    placement_rng = ctx.draw_rng("global_placement")
    decoy_rng = ctx.draw_rng("decoy_placement")
    for _ in range(240):
        one, two = _shape_pair(ctx, n_one, n_two, origin_kind)
        origins = _placement_origins(h, w, one, two, placement_kind, placement_rng)
        if origins is None:
            continue
        grid = full_grid(h, w, 0)
        paint_at(grid, origins[0][0], origins[0][1], one, 1)
        paint_at(grid, origins[1][0], origins[1][1], two, 2)
        if decoy_kind == "far_pair":
            candidates = _far_pair_candidates(grid)
            if not candidates:
                continue
            for r, c in decoy_rng.choice(candidates):
                grid[r][c] = 7
        return grid
    raise RuntimeError("could not place the requested shapes and decoy on the canvas")


def _color_cells(grid, color):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def _norm_cells(cells):
    if not cells:
        return set()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        for q in _neighbors(stack.pop()):
            if q in remaining:
                remaining.remove(q)
                stack.append(q)
    return not remaining


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _placement_kind_from_grid(grid):
    one, two = _color_cells(grid, 1), _color_cells(grid, 2)
    ar0, ac0, ar1, ac1 = _bbox(one)
    br0, bc0, br1, bc1 = _bbox(two)
    rows_separate = ar1 < br0 or br1 < ar0
    cols_separate = ac1 < bc0 or bc1 < ac0
    if cols_separate and not rows_separate:
        return "horizontal"
    if rows_separate and not cols_separate:
        return "vertical"
    if rows_separate and cols_separate:
        return "diagonal"
    raise ValueError("source shape bounding boxes overlap in both axes")


def _decoy_kind_from_grid(grid):
    cells = _color_cells(grid, 7)
    if not cells:
        return "none"
    normalized = _norm_cells(cells)
    if normalized in ({(0, 0), (4, 4)}, {(0, 4), (4, 0)}):
        return "far_pair"
    raise ValueError("color-7 cells are not the advertised far-pair decoy")


def observe_overrides(grid):
    one = _color_cells(grid, 1)
    two = _color_cells(grid, 2)
    a, b = _norm_cells(one), _norm_cells(two)
    if (0, 0) in a and (0, 0) in b:
        origin_kind = "corner"
    elif (0, 0) not in a and (0, 0) not in b:
        origin_kind = "split"
    else:
        raise ValueError("mixed normalized-origin support is outside the advertised domain")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_one": len(one),
        "n_two": len(two),
        "origin_kind": origin_kind,
        "placement_kind": _placement_kind_from_grid(grid),
        "decoy_kind": _decoy_kind_from_grid(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["expected a nonempty rectangular grid"]
    if any(type(value) is not int or value not in (0, 1, 2, 7) for row in grid for value in row):
        return ["cells must be integer colors from 0,1,2,7"]

    errors = []
    one, two = _color_cells(grid, 1), _color_cells(grid, 2)
    if not one:
        errors.append("color-1 shape is missing")
    elif not _connected(one):
        errors.append("color-1 cells must form one 4-connected shape")
    if not two:
        errors.append("color-2 shape is missing")
    elif not _connected(two):
        errors.append("color-2 cells must form one 4-connected shape")
    if one and two and any(q in two for p in one for q in _neighbors(p)):
        errors.append("color-1 and color-2 shapes must be spatially separated")
    try:
        _decoy_kind_from_grid(grid)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def strict_canonical_like(grid):
    """Generated teaching manifold plus every canonical source input."""
    return self_check(grid)


def _render_cells(cells):
    if not cells:
        return [[0]]
    normalized = _norm_cells(cells)
    h = max(r for r, _ in normalized) + 1
    w = max(c for _, c in normalized) + 1
    out = full_grid(h, w, 0)
    for r, c in normalized:
        out[r][c] = 3
    return out


def _reference_output(grid):
    one = _norm_cells(_color_cells(grid, 1))
    two = _norm_cells(_color_cells(grid, 2))
    return _render_cells(one | two)


def _absolute_coordinates(grid):
    return _render_cells(_color_cells(grid, 1) | _color_cells(grid, 2))


def _color_1_only(grid):
    return _render_cells(_norm_cells(_color_cells(grid, 1)))


def _color_2_only(grid):
    return _render_cells(_norm_cells(_color_cells(grid, 2)))


def _intersection_only(grid):
    one = _norm_cells(_color_cells(grid, 1))
    two = _norm_cells(_color_cells(grid, 2))
    return _render_cells(one & two)


def _xor_only(grid):
    one = _norm_cells(_color_cells(grid, 1))
    two = _norm_cells(_color_cells(grid, 2))
    return _render_cells(one ^ two)


def _solid_bbox(grid):
    reference = _reference_output(grid)
    return full_grid(len(reference), len(reference[0]), 3)


def _all_nonzero_colors(grid):
    colors = sorted({value for row in grid for value in row if value != 0})
    union = set()
    for color in colors:
        union |= _norm_cells(_color_cells(grid, color))
    return _render_cells(union)


def _needs_independent_normalization(grid):
    return _reference_output(grid) != _absolute_coordinates(grid)


def _both_shapes_contribute(grid):
    expected = _reference_output(grid)
    return expected != _color_1_only(grid) and expected != _color_2_only(grid)


def _overlap_and_union_are_visible(grid):
    expected = _reference_output(grid)
    return expected != _intersection_only(grid) and expected != _xor_only(grid)


def _sparse_union(grid):
    return _reference_output(grid) != _solid_bbox(grid)


def _ignore_decoy(grid):
    return _decoy_kind_from_grid(grid) == "far_pair" and _reference_output(grid) != _all_nonzero_colors(grid)


SEMANTIC_WITNESSES = {
    "independent_normalization": _needs_independent_normalization,
    "both_shapes_contribute": _both_shapes_contribute,
    "overlap_and_union": _overlap_and_union_are_visible,
    "sparse_union": _sparse_union,
    "ignore_decoy": _ignore_decoy,
}
SEMANTIC_RIVALS = {
    "absolute_coordinates": _absolute_coordinates,
    "color_1_only": _color_1_only,
    "color_2_only": _color_2_only,
    "intersection_only": _intersection_only,
    "xor_only": _xor_only,
    "solid_bbox": _solid_bbox,
    "all_nonzero_colors": _all_nonzero_colors,
}
WITNESS_RIVALS = {
    "independent_normalization": ["absolute_coordinates"],
    "both_shapes_contribute": ["color_1_only", "color_2_only"],
    "overlap_and_union": ["intersection_only", "xor_only"],
    "sparse_union": ["solid_bbox"],
    "ignore_decoy": ["all_nonzero_colors"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
