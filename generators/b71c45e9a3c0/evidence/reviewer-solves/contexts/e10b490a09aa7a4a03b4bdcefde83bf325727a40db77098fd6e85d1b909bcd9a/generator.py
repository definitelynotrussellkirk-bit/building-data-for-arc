"""Input sampler for recoloring each green object by its bbox-anchored key.

The unchanged authority reads one cell at ``(bbox_top - 1, bbox_left)`` for
each 4-connected color-3 object, then recolors that whole object.  Generated
lessons deliberately include objects whose bbox top-left is empty: those cases
distinguish the bbox anchor from the tempting "above the topmost occupied cell"
shortcut.  Outputs are not generated here; the selected Racket rule remains the
label authority.  Independent authoring probes live in ``workspace/``.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b71c45e9a3c0"
TASK_ID = GENERATOR_ID
RULE_HASH = "0668839edbcc"
VERSION = "2.1.0"
SUMMARY = (
    "Place 2-4 disconnected green(3) objects.  Each object has one distinct "
    "colored key at (bbox_top-1,bbox_left); recolor the object to that key.  "
    "Every generated input contains at least one empty bbox-corner object so "
    "the bbox anchor is taught rather than merely asserted."
)

INVARIANTS = [
    "background is color 0; object cells are color 3; keys use distinct non-{0,3} colors",
    "each 4-connected object has 3-5 cells in a 2x2, 2x3, 3x2, or 3x3 bbox",
    "the only non-{0,3} cell for an object is exactly at (bbox_top-1,bbox_left)",
    "2-4 groups are placed constructively in separated quadrants with varied margins; none are silently dropped",
    "each generated input contains 1-2 objects with an empty bbox top-left corner",
]

AXES = {
    "grid_h": {"type": "int", "default": "9..14, strongly favors 11", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "9..14, favors 10/11/12 by band", "valid": "9..14"},
    "n_groups": {"type": "int", "default": "2..4, strongly favors 3", "valid": "2..4"},
    "n_gap_shapes": {"type": "int", "default": "1..2", "valid": "1..2"},
    "palette_kind": {"type": "str", "default": "low|high|mixed", "valid": "low|high|mixed"},
    "shape_profile": {
        "type": "str",
        "default": "compact|extended|mixed, favors mixed",
        "valid": "compact|extended|mixed",
    },
}

# All 6-axis products are constructive, including 4 extended groups on 9x9.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.80

_LOW_COLORS = (1, 2, 4, 5)
_HIGH_COLORS = (6, 7, 8, 9)

# Every compact shape has bbox height 2; every extended shape has height 3.
# Gap shapes have an empty normalized (0,0), but still have bbox left == 0.
_OCCUPIED_COMPACT = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
)
_GAP_COMPACT = (
    ((0, 1), (1, 0), (1, 1)),
    ((0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
)
_OCCUPIED_EXTENDED = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
)
_GAP_EXTENDED = (
    ((0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 2), (1, 1), (1, 2), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (1, 2), (2, 0), (2, 1)),
)

_INT_AXES = frozenset({"grid_h", "grid_w", "n_groups", "n_gap_shapes"})
_STR_AXES = frozenset({"palette_kind", "shape_profile"})


def _weighted_choice(ctx, name, values, *, anchor, weight=24, favored=()):
    """Keep the full override domain while reserving substantial core support."""
    options = tuple(values) + tuple(favored) + (anchor,) * weight
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_AXES and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if name in _STR_AXES and type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")


def _palette(ctx, kind, count):
    rng = ctx.draw_rng("key_palette")
    if kind == "low":
        colors = rng.sample(list(_LOW_COLORS), count)
    elif kind == "high":
        colors = rng.sample(list(_HIGH_COLORS), count)
    else:
        # Exact mixed semantics: at least one color from each disjoint half.
        low_count = rng.randint(1, count - 1)
        colors = rng.sample(list(_LOW_COLORS), low_count)
        colors += rng.sample(list(_HIGH_COLORS), count - low_count)
        rng.shuffle(colors)
    return tuple(colors)


def _profile_kinds(ctx, profile, count):
    if profile == "compact":
        return ("compact",) * count
    if profile == "extended":
        return ("extended",) * count
    # A mixed request is exact even at the minimum count of two.
    kinds = ["compact"] * max(1, count // 2)
    kinds += ["extended"] * (count - len(kinds))
    ctx.draw_rng("profile_assignment").shuffle(kinds)
    return tuple(kinds)


def _shape_pool(profile_kind, gap):
    if profile_kind == "compact":
        return _GAP_COMPACT if gap else _OCCUPIED_COMPACT
    return _GAP_EXTENDED if gap else _OCCUPIED_EXTENDED


def _shape_size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _slot_origin(ctx, index, slot, h, w, shape):
    """Choose a collision-free origin inside one quadrant, not just at a corner.

    A full central row and column remain empty.  This makes the four slot
    products constructive even for 9x9 extended shapes while allowing larger
    grids to vary both outer margins.  ``top`` is the shape bbox top; its key is
    placed one row above at the same left coordinate.
    """
    sh, sw = _shape_size(shape)
    footprint_h = sh + 1
    split_row = h // 2
    split_col = w // 2

    if slot[0] == "n":
        key_min, key_max = 0, split_row - footprint_h
    else:
        key_min, key_max = split_row + 1, h - footprint_h
    if slot[1] == "w":
        left_min, left_max = 0, split_col - sw
    else:
        left_min, left_max = split_col + 1, w - sw
    if key_min > key_max or left_min > left_max:
        raise RuntimeError("shape does not fit its constructive quadrant")

    rng = ctx.draw_rng(f"slot_origin_{index}")
    key_row = rng.randint(key_min, key_max)
    left = rng.randint(left_min, left_max)
    return key_row + 1, left


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    width_anchor = {"easy": 10, "medium": 11, "hard": 12}.get(difficulty, 11)
    gap_anchor = 2 if difficulty == "hard" else 1
    h = _weighted_choice(ctx, "grid_h", range(9, 15), anchor=11)
    w = _weighted_choice(
        ctx,
        "grid_w",
        range(9, 15),
        anchor=width_anchor,
        favored=(10, 11, 12) * 4,
    )
    n_groups = _weighted_choice(ctx, "n_groups", range(2, 5), anchor=3)
    n_gap = _weighted_choice(ctx, "n_gap_shapes", range(1, 3), anchor=gap_anchor, weight=8)
    palette_kind = _weighted_choice(
        ctx,
        "palette_kind",
        ("low", "high", "mixed"),
        anchor="mixed",
        weight=4,
    )
    shape_profile = _weighted_choice(
        ctx,
        "shape_profile",
        ("compact", "extended", "mixed"),
        anchor="mixed",
        weight=6,
    )

    colors = _palette(ctx, palette_kind, n_groups)
    profile_kinds = _profile_kinds(ctx, shape_profile, n_groups)
    gap_indices = set(ctx.draw_rng("gap_assignment").sample(range(n_groups), n_gap))
    slots = ctx.draw_rng("slot_assignment").sample(
        (("n", "w"), ("n", "e"), ("s", "w"), ("s", "e")),
        n_groups,
    )

    grid = full_grid(h, w, 0)
    occupied = set()
    for index, (color, profile_kind, slot) in enumerate(zip(colors, profile_kinds, slots)):
        pool = _shape_pool(profile_kind, index in gap_indices)
        shape = ctx.draw_rng(f"shape_{index}").choice(pool)
        top, left = _slot_origin(ctx, index, slot, h, w, shape)
        key = (top - 1, left)
        cells = {(top + dr, left + dc) for dr, dc in shape}
        footprint = cells | {key}
        if occupied & footprint:
            raise RuntimeError("constructive quadrant slots overlapped")
        if any(not (0 <= r < h and 0 <= c < w) for r, c in footprint):
            raise RuntimeError("constructive quadrant slot escaped the grid")
        for r, c in cells:
            grid[r][c] = 3
        grid[key[0]][key[1]] = color
        occupied.update(footprint)
    return grid


def _color3_components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        components.append(tuple(sorted(cells)))
    return tuple(sorted(components, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells), cells)))


def _bbox(component):
    return (
        min(r for r, _ in component),
        min(c for _, c in component),
        max(r for r, _ in component),
        max(c for _, c in component),
    )


def _observed(grid):
    components = _color3_components(grid)
    keys = []
    heights = []
    gaps = 0
    for component in components:
        top, left, bottom, _ = _bbox(component)
        keys.append(grid[top - 1][left])
        heights.append(bottom - top + 1)
        gaps += (top, left) not in component
    key_set = set(keys)
    if key_set and key_set <= set(_LOW_COLORS):
        palette_kind = "low"
    elif key_set and key_set <= set(_HIGH_COLORS):
        palette_kind = "high"
    else:
        palette_kind = "mixed"
    if heights and all(height <= 2 for height in heights):
        shape_profile = "compact"
    elif heights and all(height == 3 for height in heights):
        shape_profile = "extended"
    else:
        shape_profile = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_groups": len(components),
        "n_gap_shapes": gaps,
        "palette_kind": palette_kind,
        "shape_profile": shape_profile,
    }


def observe_overrides(grid):
    """Recover every advertised axis from returned pixels."""
    return _observed(grid)


def self_check(grid, *, difficulty=None, meta=None):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    h, w = len(grid), width
    components = _color3_components(grid)
    errors = []
    if not (2 <= len(components) <= 4):
        errors.append(f"expected 2-4 color-3 components, found {len(components)}")

    expected_keys = set()
    key_colors = []
    for component in components:
        top, left, bottom, right = _bbox(component)
        height, shape_width = bottom - top + 1, right - left + 1
        if not (3 <= len(component) <= 5):
            errors.append(f"shape at {(top, left)} has {len(component)} cells outside 3..5")
        if not (2 <= height <= 3 and 2 <= shape_width <= 3):
            errors.append(
                f"shape at {(top, left)} has bbox {height}x{shape_width} outside 2..3"
            )
        if top == 0:
            errors.append(f"shape at {(top, left)} has no row for its key")
            continue
        key = (top - 1, left)
        expected_keys.add(key)
        color = grid[key[0]][key[1]]
        key_colors.append(color)
        if color in (0, 3):
            errors.append(f"missing non-{{0,3}} key at {key}")

    actual_keys = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 3)
    }
    if actual_keys != expected_keys:
        errors.append(
            f"key cells mismatch: expected {sorted(expected_keys)}, got {sorted(actual_keys)}"
        )
    if len(set(key_colors)) != len(key_colors):
        errors.append("key colors must be distinct within an input")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if not (9 <= len(grid) <= 14 and 9 <= len(grid[0]) <= 14):
        return ["grid dimensions outside the declared 9..14 manifold"]
    return []


def _bbox_key_output(grid):
    out = deepcopy(grid)
    for component in _color3_components(grid):
        top, left, _, _ = _bbox(component)
        color = grid[top - 1][left]
        for r, c in component:
            out[r][c] = color
    return out


def _above_topmost_occupied(grid):
    """RIVAL: associate a key with the leftmost occupied cell in the top row."""
    out = deepcopy(grid)
    for component in _color3_components(grid):
        top = min(r for r, _ in component)
        column = min(c for r, c in component if r == top)
        color = grid[top - 1][column]
        for r, c in component:
            out[r][c] = color
    return out


def _one_key_for_all(grid):
    """RIVAL: use the first object's key color for every green object."""
    components = _color3_components(grid)
    top, left, _, _ = _bbox(components[0])
    color = grid[top - 1][left]
    out = deepcopy(grid)
    for component in components:
        for r, c in component:
            out[r][c] = color
    return out


def _has_empty_bbox_corner(grid):
    return any(
        (top, left) not in component
        for component in _color3_components(grid)
        for top, left, _, _ in (_bbox(component),)
    )


def _has_multiple_key_colors(grid):
    colors = []
    for component in _color3_components(grid):
        top, left, _, _ = _bbox(component)
        colors.append(grid[top - 1][left])
    return len(set(colors)) >= 2


def lesson_identifiable(demos, query):
    """Require demos that refute both declared task-local shortcut families."""
    reasons = []
    if not demos:
        return ["lesson has no demonstrations"]
    if not any(_has_empty_bbox_corner(pair["input"]) for pair in demos):
        reasons.append("demonstrations do not distinguish bbox-left from topmost-occupied anchoring")
    if not any(_has_multiple_key_colors(pair["input"]) for pair in demos):
        reasons.append("demonstrations do not distinguish per-object keys from one global key")
    return reasons


SEMANTIC_WITNESSES = {
    "empty_bbox_corner": _has_empty_bbox_corner,
    "multiple_key_colors": _has_multiple_key_colors,
}
SEMANTIC_RIVALS = {
    "above_topmost_occupied": _above_topmost_occupied,
    "one_key_for_all": _one_key_for_all,
}
WITNESS_RIVALS = {
    "empty_bbox_corner": ["above_topmost_occupied"],
    "multiple_key_colors": ["one_key_for_all"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
