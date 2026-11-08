"""Connected red/blue shapes whose bounding-box intersection is filled by a key.

The Racket authority is unchanged. Two informative area examples and one
compact example recur every three draws; keys traverse all seven legal colors.
Latent variation includes shape, reflection, rotation, teeth, size and location.
Only grid dimensions and key color are advertised as exact override controls.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "41851e57e1a5"
TASK_ID = "41851e57e1a5"
VERSION = "3.0.0"
RULE_HASH = "b8f48f4e78e4"
SUMMARY = (
    "Two disjoint, connected shapes use fixed colors red 2 and blue 1. "
    "Their inclusive bounding boxes overlap. One isolated key in color 3..9 "
    "selects the fill color. On a blank same-size canvas, fill the entire "
    "intersection rectangle, including previously empty cells. Generated "
    "lessons mix singleton/line/compact overlaps with full two-dimensional "
    "overlaps; the selected Racket rule supplies all training labels."
)
INVARIANTS = [
    "rectangular integer grids use colors 0..9 and at most 30 rows/columns",
    "background is 0; exactly one connected red(2) and blue(1) component",
    "each shape has at least three cells and the two bounding boxes overlap",
    "one isolated key cell has color 3..9; red/blue cells are disjoint",
]
AXES = {
    "grid_h": {"type": "int", "default": "profile/schedule aware 8..20", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "profile/schedule aware 8..20", "valid": "8..20"},
    "key_color": {"type": "int", "default": "cyclic 3..9 by seed and sample index", "valid": "3..9"},
}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = ("rich", "compact")


# Normalized geometric motifs from the canonical examples, plus a small
# area-fill extension. These are shapes, not stored input/output episodes.
_COMPACT_SHAPES = (
    (((0, 0), (1, 0), (2, 0), (2, 1)),
     ((0, 1), (1, 1), (1, 2), (2, 2), (2, 3))),
    (((2, 0), (2, 2), (3, 0), (3, 1), (3, 2)),
     ((0, 2), (1, 2), (1, 3), (2, 3), (2, 4))),
    (((1, 0), (2, 0), (3, 0), (3, 1)),
     ((0, 1), (0, 3), (1, 1), (1, 2), (1, 3))),
    (((2, 0), (2, 1), (2, 2), (3, 1)),
     ((0, 2), (1, 2), (1, 3), (2, 3), (2, 4))),
    (((0, 0), (1, 0), (2, 0), (2, 1)),
     ((0, 1), (0, 2), (0, 3), (1, 2))),
    (((1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
     ((0, 1), (0, 2), (0, 3), (1, 3), (2, 3))),
)


def _cells_of(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _intersection(grid):
    red, blue = _bbox(_cells_of(grid, 2)), _bbox(_cells_of(grid, 1))
    return (max(red[0], blue[0]), max(red[1], blue[1]),
            min(red[2], blue[2]), min(red[3], blue[3]))


def _key(grid):
    return next(value for row in grid for value in row if value not in (0, 1, 2))


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    stack = [min(remaining)]
    remaining.remove(stack[0])
    while stack:
        r, c = stack.pop()
        for candidate in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if candidate in remaining:
                remaining.remove(candidate)
                stack.append(candidate)
    return not remaining


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the authored domain, including canonical five-cell shapes."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["expected a nonempty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid dimensions exceed 30"]
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["colors must be integers 0..9, excluding booleans"]
    errors = []
    shapes = {color: _cells_of(grid, color) for color in (1, 2)}
    for color, cells in shapes.items():
        if len(cells) < 3 or not _connected(cells):
            errors.append(f"color {color} must form one connected shape of at least three cells")
    keys = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 1, 2)]
    if len(keys) != 1:
        errors.append("expected exactly one key cell of color 3..9")
    else:
        kr, kc = keys[0]
        if any(abs(kr - r) <= 1 and abs(kc - c) <= 1 for cells in shapes.values() for r, c in cells):
            errors.append("key cell touches a red/blue shape")
    if shapes[1] and shapes[2]:
        r0, c0, r1, c1 = _intersection(grid)
        if r0 > r1 or c0 > c1:
            errors.append("red and blue bounding boxes do not overlap")
    return errors


def strict_canonical_like(grid):
    """Canonical dimensions and 4/5-cell geometry, allowing task symmetries.

    Key color/translation are semantic roles, not fixed literal identities.
    Larger lawful area witnesses belong to the explicitly augmented stratum.
    """
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in ((8, 8), (8, 9), (9, 9)):
        errors.append("outside canonical grid-size profiles")
    if any(len(_cells_of(grid, color)) not in (4, 5) for color in (1, 2)):
        errors.append("outside canonical four/five-cell shape sizes")
    return errors


def schedule_profile(seed, sample_index, difficulty=None):
    return "compact" if sample_index % 3 == 2 else "rich"


def _orient(red, blue, rng):
    turns, reflected = rng.randrange(4), rng.choice((False, True))
    def transform(cells):
        result = []
        for r, c in cells:
            if reflected:
                c = -c
            for _ in range(turns):
                r, c = c, -r
            result.append((r, c))
        return result
    red, blue = transform(red), transform(blue)
    top = min(r for r, _ in red + blue)
    left = min(c for _, c in red + blue)
    red = sorted((r - top, c - left) for r, c in red)
    blue = sorted((r - top, c - left) for r, c in blue)
    if rng.choice((False, True)):
        red, blue = blue, red
    return red, blue


def _rich_shapes(rng, difficulty):
    limit = 3 if difficulty == "easy" else 5 if difficulty == "hard" else 4
    ih, iw = rng.randint(3, limit), rng.randint(3, limit)
    # Opposite Ls have disjoint actual cells and an ih by iw box overlap.
    red = {(r, 0) for r in range(1, ih + 2)} | {(ih + 1, c) for c in range(iw + 1)}
    blue = {(0, c) for c in range(1, iw + 2)} | {(r, iw + 1) for r in range(ih + 1)}
    # Optional inward teeth vary occupancy while leaving the middle interior
    # blank. Full fill and perimeter/occupied-cell rivals remain distinguishable.
    for c in range(1, iw + 1):
        if rng.randrange(3) == 0:
            red.add((ih, c))
        if rng.randrange(3) == 0:
            blue.add((1, c))
    return sorted(red), sorted(blue)


def _place(h, w, red, blue, key, rng, *, avoid_upper_left=False):
    sh = max(r for r, _ in red + blue) + 1
    sw = max(c for _, c in red + blue) + 1
    positions = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(positions)
    for top, left in positions:
        grid = full_grid(h, w, 0)
        occupied = []
        for color, cells in ((2, red), (1, blue)):
            for r, c in cells:
                rr, cc = r + top, c + left
                grid[rr][cc] = color
                occupied.append((rr, cc))
        r0, c0, r1, c1 = _intersection(grid)
        candidates = [
            (r, c) for r in range(h) for c in range(w)
            if grid[r][c] == 0 and not (r0 <= r <= r1 and c0 <= c <= c1)
            and (not avoid_upper_left or (r, c) != (0, 0))
            and all(abs(r - rr) > 1 or abs(c - cc) > 1 for rr, cc in occupied)
        ]
        if candidates:
            r, c = rng.choice(candidates)
            grid[r][c] = key
            return grid
    raise ValueError("no isolated key placement for this geometry and canvas")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override controls: {', '.join(sorted(unknown))}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer; omit it to use its scheduled default")
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be integers")
    profile = schedule_profile(seed, sample_index, difficulty)
    # Resolved schedule defaults are passed through the same typed GenCtx draws
    # as caller controls, so recorded provenance describes the realized grid.
    controls = {"key_color": 3 + (seed + sample_index) % 7}
    if profile == "compact":
        height = 8 + (seed + sample_index // 3) % 2
        controls.update(grid_h=height, grid_w=8 if height == 8 and (seed // 2 + sample_index // 3) % 2 == 0 else 9)
    controls.update(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=controls)
    h = ctx.draw_int_diff("grid_h", 8, 20)
    w = ctx.draw_int_diff("grid_w", 8, 20)
    key = ctx.draw_int_strict("key_color", 3, 9)
    rng = ctx.draw_rng("geometry")
    red, blue = rng.choice(_COMPACT_SHAPES) if profile == "compact" else _rich_shapes(rng, difficulty)
    red, blue = _orient(red, blue, rng)
    return _place(h, w, red, blue, key, ctx.draw_rng("placement"), avoid_upper_left=profile == "rich")


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "key_color": _key(grid)}


def _rival(grid, *, mode):
    red, blue = _bbox(_cells_of(grid, 2)), _bbox(_cells_of(grid, 1))
    box = _intersection(grid)
    if mode == "red_bbox":
        box = red
    elif mode == "blue_bbox":
        box = blue
    elif mode == "union_bbox":
        box = (min(red[0], blue[0]), min(red[1], blue[1]), max(red[2], blue[2]), max(red[3], blue[3]))
    r0, c0, r1, c1 = box
    color = grid[0][0] if mode == "upper_left_key" else int(mode.rsplit("_", 1)[1]) if mode.startswith("fixed_key_") else _key(grid)
    output = full_grid(len(grid), len(grid[0]), 0)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if mode == "corner_only" and (r, c) != (r0, c0):
                continue
            if mode == "occupied_only" and grid[r][c] == 0:
                continue
            if mode == "perimeter_only" and r not in (r0, r1) and c not in (c0, c1):
                continue
            output[r][c] = color
    return output


SEMANTIC_RIVALS = {
    name: partial(_rival, mode=name) for name in
    ("corner_only", "occupied_only", "perimeter_only", "red_bbox", "blue_bbox",
     "union_bbox", "upper_left_key", *(f"fixed_key_{color}" for color in range(3, 10)))
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"upper_left_key": SEMANTIC_RIVALS["upper_left_key"]}


def _has_blank_overlap(grid):
    r0, c0, r1, c1 = _intersection(grid)
    return any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))


def _has_interior(grid):
    r0, c0, r1, c1 = _intersection(grid)
    return r1 - r0 >= 2 and c1 - c0 >= 2


def _has_multiple_target_cells(grid):
    r0, c0, r1, c1 = _intersection(grid)
    return (r1 - r0 + 1) * (c1 - c0 + 1) > 1


SEMANTIC_WITNESSES = {
    "fills_previously_empty_cells": _has_blank_overlap,
    "fills_rectangle_interior": _has_interior,
    "fills_more_than_one_cell": _has_multiple_target_cells,
    "key_is_not_upper_left": lambda grid: grid[0][0] in (0, 1, 2),
}
WITNESS_RIVALS = {
    "fills_previously_empty_cells": ["occupied_only"],
    "fills_rectangle_interior": ["perimeter_only"],
    "fills_more_than_one_cell": ["corner_only"],
    "key_is_not_upper_left": ["upper_left_key"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; no claim of universal rule identification."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
