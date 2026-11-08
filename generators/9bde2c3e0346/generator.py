"""Input sampler for replacing each object by its bounding-box frame.

The selected Racket program is the sole label authority.  This module samples
lawful inputs and exposes an independently testable Python mirror plus finite
semantic rivals for curriculum diagnostics.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9bde2c3e0346"
TASK_ID = GENERATOR_ID
RULE_HASH = "8f9e53b42241"
VERSION = "3.0.0"
SUMMARY = (
    "Two or three separated single-color objects are replaced by the border "
    "of each object's bounding box on an otherwise blank output."
)
EXAMPLES_NEEDED = 1
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0",
    "the grid is 8..12 rows by 8..12 columns",
    "there are 2..3 four-connected objects with distinct nonzero colors",
    "object bounding boxes are disjoint and each object omits a border cell",
    "generated scenes include both a missing-border cell and an interior cell to erase",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted canonical profiles plus broad 8..12 support",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted canonical profiles plus broad 8..12 support",
        "valid": "8..12",
    },
    "n_objects": {
        "type": "int",
        "default": "weighted canonical profiles plus broad 2..3 support",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# (height, width, nonzero palette size).  The palette size equals n_objects
# because generated objects deliberately use distinct colors.
_CANONICAL_PROFILES = ((8, 8, 2), (9, 9, 2))

# The first object is always a 3x3 connected path containing its interior
# center while omitting some frame cells.  It simultaneously teaches that the
# rule adds missing frame cells and clears original interior pixels.
_INTERIOR_WITNESS = frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)})
_COMPANION_BASES = (
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
)


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _variants(cells):
    variants = set()
    for reflected in (False, True):
        current = {(r, -c if reflected else c) for r, c in cells}
        for _ in range(4):
            current = {(c, -r) for r, c in current}
            variants.add(tuple(sorted(_normalize(current))))
    return tuple(frozenset(points) for points in sorted(variants))


_WITNESS_VARIANTS = _variants(_INTERIOR_WITNESS)
_COMPANION_VARIANTS = tuple(
    variant
    for base in _COMPANION_BASES
    for variant in _variants(base)
)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _weighted_int(ctx, name, lo, hi, *, anchor=None, favored=()):
    """Draw full-domain values while strongly weighting a canonical profile."""
    options = list(range(lo, hi + 1))
    options.extend(favored)
    if anchor is not None:
        options.extend([anchor] * 64)
    return ctx.draw_choice(name, options)


def _shape_size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _boxes_have_blank_separation(left, right):
    """True when two boxes have at least one blank row or column between them."""
    lt, ll, lb, lr = left
    rt, rl, rb, rr = right
    return lb + 1 < rt or rb + 1 < lt or lr + 1 < rl or rr + 1 < ll


def _place_shapes(h, w, shapes, rng):
    """Backtrack over shuffled origins; the small domains make this bounded."""
    candidate_lists = []
    for shape in shapes:
        sh, sw = _shape_size(shape)
        candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
        rng.shuffle(candidates)
        candidate_lists.append((sh, sw, candidates))

    placements = []
    boxes = []

    def search(index):
        if index == len(shapes):
            return True
        sh, sw, candidates = candidate_lists[index]
        for top, left in candidates:
            box = (top, left, top + sh - 1, left + sw - 1)
            if all(_boxes_have_blank_separation(box, previous) for previous in boxes):
                placements.append((top, left))
                boxes.append(box)
                if search(index + 1):
                    return True
                boxes.pop()
                placements.pop()
        return False

    if not search(0):
        raise RuntimeError(f"could not place {len(shapes)} objects on {h}x{w} grid")
    return placements


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

    mode = ctx.draw_choice("curriculum_mode", ("canonical", "canonical", "broad"))
    profile = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
    anchor_h, anchor_w, anchor_objects = profile if mode == "canonical" else (None, None, None)

    if difficulty == "easy":
        favored_h = favored_w = (8, 9)
        favored_objects = (2,)
    elif difficulty == "hard":
        favored_h = favored_w = (10, 11, 12)
        favored_objects = (3,)
    else:
        favored_h = favored_w = favored_objects = ()

    h = _weighted_int(ctx, "grid_h", 8, 12, anchor=anchor_h, favored=favored_h)
    w = _weighted_int(ctx, "grid_w", 8, 12, anchor=anchor_w, favored=favored_w)
    n_objects = _weighted_int(
        ctx, "n_objects", 2, 3, anchor=anchor_objects, favored=favored_objects
    )

    shape_rng = ctx.draw_rng("shapes")
    shapes = [shape_rng.choice(_WITNESS_VARIANTS)]
    shapes.extend(shape_rng.choice(_COMPANION_VARIANTS) for _ in range(n_objects - 1))
    placement_rng = ctx.draw_rng("placements")
    placements = _place_shapes(h, w, shapes, placement_rng)
    colors = ctx.draw_rng("colors").sample(range(1, 10), n_objects)

    grid = full_grid(h, w, 0)
    for color, shape, (top, left) in zip(colors, shapes, placements):
        for r, c in shape:
            grid[top + r][left + c] = color
    return grid


def _components(grid):
    pending = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    groups = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    stack.append(point)
                    cells.add(point)
        groups.append((color, cells))
    return groups


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _frame(cells):
    top, left, bottom, right = _bbox(cells)
    return (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the sampler's strict, canonical-supporting input manifold."""
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid must have a nonempty first row"]

    h = len(grid)
    w = len(grid[0])
    problems = []
    if not 8 <= h <= 12:
        problems.append(f"height {h} outside 8..12")
    if not 8 <= w <= 12:
        problems.append(f"width {w} outside 8..12")

    rectangular = True
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != w:
            problems.append(f"row {r} has invalid width")
            rectangular = False
            continue
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                problems.append(f"cell ({r},{c}) is not an ARC color 0..9")
    if not rectangular or problems:
        return problems

    groups = _components(grid)
    if not 2 <= len(groups) <= 3:
        problems.append(f"found {len(groups)} objects, expected 2..3")
        return problems
    colors = [color for color, _ in groups]
    if len(set(colors)) != len(colors):
        problems.append("objects must use distinct nonzero colors")

    boxes = []
    for index, (_, cells) in enumerate(groups):
        top, left, bottom, right = _bbox(cells)
        bh, bw = bottom - top + 1, right - left + 1
        if not 3 <= len(cells) <= 5:
            problems.append(f"object {index} has {len(cells)} cells, expected 3..5")
        if not (2 <= bh <= 3 and 2 <= bw <= 3):
            problems.append(f"object {index} bbox is {bh}x{bw}, expected dimensions 2..3")
        if not (_frame(cells) - cells):
            problems.append(f"object {index} already contains its full bbox frame")
        boxes.append((top, left, bottom, right))

    for index, box in enumerate(boxes):
        top, left, bottom, right = box
        for other in boxes[index + 1:]:
            ot, ol, ob, oright = other
            if not (bottom < ot or ob < top or right < ol or oright < left):
                problems.append("object bounding boxes overlap")
    return problems


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    problems = self_check(grid)
    if problems:
        raise ValueError(f"cannot observe invalid grid: {problems}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(_components(grid)),
    }


def rule_mirror(grid):
    """Independent executable mirror for diagnostics; Racket remains authority."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        for r, c in _frame(cells):
            output[r][c] = color
    return output


def _identity(grid):
    return [list(row) for row in grid]


def _solid_bbox_fill(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        top, left, bottom, right = _bbox(cells)
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                output[r][c] = color
    return output


def _existing_border_only(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        for r, c in cells & _frame(cells):
            output[r][c] = color
    return output


def _add_frame_keep_interior(grid):
    output = rule_mirror(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                output[r][c] = value
    return output


def _adds_missing_border(grid):
    return any(_frame(cells) - cells for _, cells in _components(grid))


def _clears_original_interior(grid):
    for _, cells in _components(grid):
        top, left, bottom, right = _bbox(cells)
        if any(top < r < bottom and left < c < right for r, c in cells):
            return True
    return False


SEMANTIC_WITNESSES = {
    "adds_missing_border": _adds_missing_border,
    "clears_original_interior": _clears_original_interior,
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)
SEMANTIC_RIVALS = {
    "identity": _identity,
    "solid_bbox_fill": _solid_bbox_fill,
    "existing_border_only": _existing_border_only,
    "add_frame_keep_interior": _add_frame_keep_interior,
}
WITNESS_RIVALS = {
    "adds_missing_border": ["identity", "existing_border_only"],
    "clears_original_interior": ["solid_bbox_fill", "add_frame_keep_interior"],
}
CANONICAL_SHORTCUTS = {"add_frame_keep_interior": _add_frame_keep_interior}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require lawful labels and at least one refutation of every finite rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    reasons = [f"query input is invalid: {query_errors[0]}"] if query_errors else []

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
            reasons.append(f"demo {index} output disagrees with the bbox-frame rule")
            continue
        valid.append(demo)
    if reasons:
        return reasons

    for witness_name, predicate in SEMANTIC_WITNESSES.items():
        if not any(predicate(demo["input"]) for demo in valid):
            reasons.append(f"demonstrations lack witness {witness_name}")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in valid):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
