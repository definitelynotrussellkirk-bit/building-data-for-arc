"""Lawful input sampler for recoloring rectangles by nearest row-0 marker.

The selected Racket authority computes each color-5 object's bounding-box
integer horizontal midpoint (the Racket runtime floors even-width centers) and
paints the object with the color of the uniquely nearest nonzero row-0 marker.  Exact center ties are intentionally outside this
sampler's teaching domain because the canonical examples do not define a tie
policy.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "424c822d69f3"
TASK_ID = GENERATOR_ID
RULE_HASH = "5abbdbb61293"
VERSION = "2.2.0"
SUMMARY = (
    "Distinct colored markers in row 0 label solid color-5 rectangles below: "
    "paint every rectangle by the uniquely nearest marker to its floored bbox midpoint."
)

INVARIANTS = [
    "row 0 contains 2..4 distinct nonzero, non-5 marker colors",
    "row 1 is blank and every lower nonzero cell belongs to a solid 5-rectangle",
    "rectangles are separate and every floored bbox midpoint has one uniquely nearest marker",
    "ordinary lessons include repeated nearest-marker assignments and an assigned marker outside a rectangle span",
]

MARKER_LAYOUTS = (
    "evenly_spaced",
    "left_biased",
    "right_biased",
    "scattered",
    "edges",
)
RECT_SIZE_KINDS = ("small", "medium", "large", "varied")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 10..18", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "scheduled 10..20", "valid": "10..20"},
    "n_markers": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "n_rects": {"type": "int", "default": "scheduled 2..3", "valid": "2..3"},
    "marker_layout": {
        "type": "str",
        "default": "scheduled",
        "valid": "evenly_spaced|left_biased|right_biased|scattered|edges",
    },
    "rect_size_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "small|medium|large|varied",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "warm|cool|broad|small",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_INT_AXES = {
    "grid_h": (10, 18),
    "grid_w": (10, 20),
    "n_markers": (2, 4),
    "n_rects": (2, 3),
}
_STR_AXES = {
    "marker_layout": MARKER_LAYOUTS,
    "rect_size_kind": RECT_SIZE_KINDS,
    "palette_kind": PALETTE_KINDS,
}

# Prefix sets are unique at every legal n_markers, so palette_kind is exactly
# recoverable from returned pixels while the first three sets retain canonical
# palettes {3,6,9}, {2,6,8}, {1,4,7}, and {1,6,7}.
_PALETTES = {
    "warm": (3, 6, 9, 4),
    "cool": (2, 6, 8, 1),
    "broad": (1, 4, 7, 8),
    "small": (1, 6, 7, 2),
}
_RECT_PATTERNS = {
    "small": ((2, 2),),
    "medium": ((2, 3),),
    "large": ((2, 7),),
    "varied": ((2, 4), (3, 2), (3, 3)),
}

SCHEDULE_PROFILES = (
    "edge_overlap",
    "canonical_anchor",
    "canonical_anchor",
    "right_varied",
    "left_large",
    "scattered_small",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    """Finite semantic/default schedule; independent of process hash state."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_AXES:
            lo, hi = _INT_AXES[name]
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        else:
            allowed = _STR_AXES[name]
            if type(value) is not str or value not in allowed:
                raise ValueError(f"{name} must be one of {allowed}, got {value!r}")


def _band_values(difficulty, easy, medium, hard):
    if difficulty == "easy":
        return tuple(easy)
    if difficulty == "hard":
        return tuple(hard)
    return tuple(medium)


def _defaults(profile, difficulty):
    if profile == "canonical_anchor":
        return {
            "grid_h": (10,), "grid_w": (10,), "n_markers": (3,), "n_rects": (3,),
            "marker_layout": ("left_biased",), "rect_size_kind": ("small",),
            "palette_kind": PALETTE_KINDS,
        }
    heights = _band_values(difficulty, range(10, 13), range(11, 16), range(14, 19))
    widths = _band_values(difficulty, range(10, 14), range(12, 17), range(16, 21))
    profile_values = {
        "edge_overlap": (2, 2, "edges", "medium", "cool"),
        "right_varied": (3, 3, "right_biased", "varied", "broad"),
        "left_large": (2, 3, "left_biased", "large", "small"),
        "scattered_small": (4, 3, "scattered", "small", "warm"),
    }
    n_markers, n_rects, layout, rect_kind, palette = profile_values[profile]
    if profile == "scattered_small" and difficulty == "easy":
        # Four scattered markers in a 10-column canvas leave no two distinct
        # teaching rectangles that jointly witness both declared shortcuts.
        # Widths 11..13 preserve the easy scale and are fully constructive.
        widths = tuple(range(11, 14))
    return {
        "grid_h": heights,
        "grid_w": widths,
        "n_markers": (n_markers,),
        "n_rects": (n_rects,),
        "marker_layout": (layout,),
        "rect_size_kind": (rect_kind,),
        "palette_kind": (palette,),
    }


def _draw_axis(ctx, name, defaults, overrides):
    if name in overrides and overrides[name] is not None:
        if name in _INT_AXES:
            lo, hi = _INT_AXES[name]
            options = tuple(range(lo, hi + 1))
        else:
            options = _STR_AXES[name]
    else:
        options = tuple(defaults[name])
    return ctx.draw_choice(name, options)


def _layout_signature(name, width, count):
    if name == "left_biased":
        return tuple(range(0, 2 * count, 2))
    if name == "right_biased":
        return tuple(range(width - (2 * count - 1), width, 2))
    if name == "edges":
        if count == 2:
            return (0, width - 1)
        return tuple(
            [0]
            + [round(i * (width - 1) / (count - 1)) for i in range(1, count - 1)]
            + [width - 1]
        )
    if name == "evenly_spaced":
        return tuple(round((i + 1) * (width - 1) / (count + 1)) for i in range(count))
    if count == 2:
        return (1, width - 2)
    if count == 3:
        return (1, width // 2, width - 2)
    return (1, 3, width - 4, width - 2)


def _rect_dimensions(kind, count):
    pattern = _RECT_PATTERNS[kind]
    return tuple(pattern[index % len(pattern)] for index in range(count))


def _nearest_index(marker_cols, c0, width):
    # The selected Racket runtime maps integer `/` to quotient.  Therefore the
    # source expression (c0 + c1) / 2 uses the left cell of an even-width box.
    center = c0 + (width - 1) // 2
    distances = [abs(col - center) for col in marker_cols]
    best = min(distances)
    return distances.index(best) if distances.count(best) == 1 else None


def _separate(box, prior):
    r0, c0, r1, c1 = box
    q0, d0, q1, d1 = prior
    return r1 + 1 < q0 or q1 + 1 < r0 or c1 + 1 < d0 or d1 + 1 < c0


def _rank_mismatch(boxes, nearest, marker_count):
    order = sorted(range(len(boxes)), key=lambda index: (boxes[index][1], boxes[index][0]))
    if len(order) == 1:
        assigned = [0]
    else:
        assigned = [round(rank * (marker_count - 1) / (len(order) - 1)) for rank in range(len(order))]
    return any(nearest[index] != assigned[rank] for rank, index in enumerate(order))


def _row_arrangements(h, dimensions):
    """Return deterministic lawful row placements, including vertical packing."""
    arrangements = []
    for top_or_bottom in product((0, 1), repeat=len(dimensions)):
        rows = tuple(
            2 if side == 0 else h - rh
            for side, (rh, _rw) in zip(top_or_bottom, dimensions)
        )
        if all(2 <= row and row + dimensions[index][0] <= h for index, row in enumerate(rows)):
            arrangements.append(rows)

    cursor = 2
    top_stack = []
    for rh, _rw in dimensions:
        top_stack.append(cursor)
        cursor += rh + 1
    if top_stack[-1] + dimensions[-1][0] <= h:
        arrangements.append(tuple(top_stack))

    cursor = h
    bottom_stack = [0] * len(dimensions)
    for index in range(len(dimensions) - 1, -1, -1):
        rh, _rw = dimensions[index]
        cursor -= rh
        bottom_stack[index] = cursor
        cursor -= 1
    if bottom_stack[0] >= 2:
        arrangements.append(tuple(bottom_stack))

    # Preserve order while removing duplicate top/bottom arrangements.
    return tuple(dict.fromkeys(arrangements))


def _choose_rectangles(h, w, marker_cols, dimensions, rng, require_witnesses):
    row_arrangements = list(_row_arrangements(h, dimensions))
    rng.shuffle(row_arrangements)
    candidate_lists = []
    for rh, rw in dimensions:
        candidates = []
        for c0 in range(w - rw + 1):
            nearest = _nearest_index(marker_cols, c0, rw)
            if nearest is None:
                continue
            outside = not (c0 <= marker_cols[nearest] <= c0 + rw - 1)
            candidates.append((c0, nearest, outside))
        rng.shuffle(candidates)
        candidate_lists.append(candidates)
    choices = list(product(*candidate_lists))
    rng.shuffle(choices)
    for selected in choices:
        for rows in row_arrangements:
            boxes = []
            valid = True
            for index, (c0, _nearest, _outside) in enumerate(selected):
                rh, rw = dimensions[index]
                r0 = rows[index]
                box = (r0, c0, r0 + rh - 1, c0 + rw - 1)
                if any(not _separate(box, previous) for previous in boxes):
                    valid = False
                    break
                boxes.append(box)
            if not valid:
                continue
            if require_witnesses:
                nearest = [entry[1] for entry in selected]
                if len(set(nearest)) == len(nearest):
                    continue
                if not any(entry[2] for entry in selected):
                    continue
                if not _rank_mismatch(boxes, nearest, len(marker_cols)):
                    continue
            return boxes
    raise ValueError(
        "no lawful rectangle placement for exact controls "
        f"h={h}, w={w}, markers={marker_cols}, dimensions={dimensions}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _defaults(profile, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_axis(ctx, "grid_h", defaults, overrides)
    w = _draw_axis(ctx, "grid_w", defaults, overrides)
    n_markers = _draw_axis(ctx, "n_markers", defaults, overrides)
    n_rects = _draw_axis(ctx, "n_rects", defaults, overrides)
    layout = _draw_axis(ctx, "marker_layout", defaults, overrides)
    rect_kind = _draw_axis(ctx, "rect_size_kind", defaults, overrides)
    palette_kind = _draw_axis(ctx, "palette_kind", defaults, overrides)

    marker_cols = _layout_signature(layout, w, n_markers)
    if len(set(marker_cols)) != n_markers or not all(0 <= col < w for col in marker_cols):
        raise ValueError(f"marker layout {layout!r} is infeasible for width={w}, count={n_markers}")
    palette = list(_PALETTES[palette_kind][:n_markers])
    ctx.draw_rng("palette_order").shuffle(palette)
    dimensions = _rect_dimensions(rect_kind, n_rects)
    boxes = _choose_rectangles(
        h,
        w,
        marker_cols,
        dimensions,
        ctx.draw_rng("rectangle_positions"),
        require_witnesses=not any(value is not None for value in overrides.values()),
    )

    grid = full_grid(h, w, 0)
    for col, color in zip(marker_cols, palette):
        grid[0][col] = color
    for (r0, c0, r1, c1) in boxes:
        draw_rect(grid, r0, c0, r1 - r0 + 1, c1 - c0 + 1, 5)
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive sampler produced an invalid grid: {errors}")
    return grid


def _color_components(grid, color):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        todo = [start]
        cells = []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    todo.append(point)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: (min(c for _, c in cells), min(r for r, _ in cells)))


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _markers(grid):
    return [(c, value) for c, value in enumerate(grid[0]) if value not in (0, 5)]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (bool is not a color)"]
    h, w = len(grid), width
    errors = []
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    if any(value == 5 for value in grid[0]):
        errors.append("row 0 marker legend may not contain color 5")
    legend = _markers(grid)
    if len(legend) < 2:
        errors.append("row 0 must contain at least two marker cells")
    colors = [color for _, color in legend]
    if len(colors) != len(set(colors)):
        errors.append("row-0 marker colors must be distinct")
    if h < 2 or any(value != 0 for value in grid[1]):
        errors.append("row 1 must be blank")
    if any(value not in (0, 5) for row in grid[1:] for value in row):
        errors.append("below row 0 only background 0 and rectangle color 5 are lawful")
    components = _color_components(grid, 5)
    if not components:
        errors.append("at least one color-5 rectangle is required")
    marker_cols = [col for col, _ in legend]
    for index, cells in enumerate(components):
        r0, c0, r1, c1 = _bbox(cells)
        expected = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        if set(cells) != expected:
            errors.append(f"color-5 component {index} is not a solid rectangle")
        if r0 < 2:
            errors.append(f"color-5 component {index} must begin below row 1")
        if marker_cols and _nearest_index(marker_cols, c0, c1 - c0 + 1) is None:
            errors.append(f"color-5 component {index} has an exact nearest-marker tie")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe controls on an invalid grid: {errors}")
    legend = _markers(grid)
    marker_cols = tuple(col for col, _ in legend)
    n_markers = len(legend)
    marker_colors = frozenset(color for _, color in legend)

    layout = "scattered"
    for candidate in ("evenly_spaced", "left_biased", "right_biased", "edges"):
        if marker_cols == _layout_signature(candidate, len(grid[0]), n_markers):
            layout = candidate
            break

    palette_matches = [
        name
        for name, palette in _PALETTES.items()
        if marker_colors == frozenset(palette[:n_markers])
    ]
    if len(palette_matches) != 1:
        raise ValueError(f"marker palette is not one exact declared profile: {sorted(marker_colors)}")

    components = _color_components(grid, 5)
    dimensions = sorted(
        (r1 - r0 + 1, c1 - c0 + 1)
        for r0, c0, r1, c1 in (_bbox(cells) for cells in components)
    )
    rect_matches = []
    for name, pattern in _RECT_PATTERNS.items():
        expected = sorted(pattern[index % len(pattern)] for index in range(len(components)))
        if dimensions == expected:
            rect_matches.append(name)
    if len(rect_matches) != 1:
        raise ValueError(f"rectangle dimensions are not one exact declared profile: {dimensions}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_markers": n_markers,
        "n_rects": len(components),
        "marker_layout": layout,
        "rect_size_kind": rect_matches[0],
        "palette_kind": palette_matches[0],
    }


def _intended(grid):
    out = deepcopy(grid)
    legend = _markers(grid)
    marker_cols = [col for col, _ in legend]
    for cells in _color_components(grid, 5):
        _r0, c0, _r1, c1 = _bbox(cells)
        nearest = _nearest_index(marker_cols, c0, c1 - c0 + 1)
        if nearest is None:
            raise ValueError("nearest-marker rule is undefined on exact ties")
        color = legend[nearest][1]
        for r, c in cells:
            out[r][c] = color
    return out


def _rank_order(grid):
    out = deepcopy(grid)
    legend = _markers(grid)
    rects = _color_components(grid, 5)
    if not rects or not legend:
        return out
    for index, cells in enumerate(rects):
        marker_index = 0 if len(rects) == 1 else round(index * (len(legend) - 1) / (len(rects) - 1))
        color = legend[marker_index][1]
        for r, c in cells:
            out[r][c] = color
    return out


def _vertical_overlap_only(grid):
    out = deepcopy(grid)
    legend = _markers(grid)
    for cells in _color_components(grid, 5):
        _r0, c0, _r1, c1 = _bbox(cells)
        inside = [(col, color) for col, color in legend if c0 <= col <= c1]
        if not inside:
            continue
        center = (c0 + c1) // 2
        _col, color = min(inside, key=lambda item: (abs(item[0] - center), item[0]))
        for r, c in cells:
            out[r][c] = color
    return out


def _nearest_assignments(grid):
    legend = _markers(grid)
    marker_cols = [col for col, _ in legend]
    assignments = []
    outside = False
    for cells in _color_components(grid, 5):
        _r0, c0, _r1, c1 = _bbox(cells)
        nearest = _nearest_index(marker_cols, c0, c1 - c0 + 1)
        if nearest is None:
            continue
        assignments.append(nearest)
        outside |= not (c0 <= marker_cols[nearest] <= c1)
    return assignments, outside


def _has_shared_nearest(grid):
    assignments, _outside = _nearest_assignments(grid)
    return len(assignments) != len(set(assignments))


def _has_nearest_outside_bbox(grid):
    _assignments, outside = _nearest_assignments(grid)
    return outside


SEMANTIC_WITNESSES = {
    "shared_nearest": _has_shared_nearest,
    "nearest_outside_bbox": _has_nearest_outside_bbox,
}
SEMANTIC_RIVALS = {
    "rank_order": _rank_order,
    "vertical_overlap_only": _vertical_overlap_only,
}
WITNESS_RIVALS = {
    "shared_nearest": ["rank_order"],
    "nearest_outside_bbox": ["vertical_overlap_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, solver in LESSON_COMPETITORS.items():
        try:
            fits = all(solver(pair["input"]) == pair["output"] for pair in demos)
            changes_query = solver(query["input"]) != query["output"]
        except Exception as exc:  # diagnostic contract, never hide rival failures
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"competitor {name} fits every demonstration but changes the query")
    return reasons
