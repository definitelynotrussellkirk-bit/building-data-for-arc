"""Constructive inputs for component bounding-box outlines (bank M52).

The selected Racket rule supplies labels. Same-color disconnected components
and occupied interiors teach two distinctions absent from the canonical pairs.
Default lessons alternate rich and canonical-scale inputs; overrides describe
lawful individual inputs and do not promise a teaching schedule.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = "623cca1dd5a8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "9e6a7457666e"
SUMMARY = (
    "Outline each monochromatic four-connected component's bounding box. "
    "Teach disconnected repeated colors, removal of interior pixels, and thin boxes."
)
INVARIANTS = [
    "background is 0; objects use colors 1..9 and monochromatic four-connectivity",
    "production realizes exactly 2..4 components with disjoint, moat-separated bboxes",
    "thin boxes remain lawful; production shapes span both bbox axes and are nonrectangular",
    "default even indices contain repeated colors and an occupied bbox interior",
    "default odd indices retain the 8x8, 9x9 or 10x10 three-color canonical profiles",
]
AXES = {
    "grid_h": {"type": "int", "default": "8..16; canonical profile 8|9|10", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "8..16; canonical profile 8|9|10", "valid": "8..16"},
    "n_blobs": {"type": "int", "default": "2 in canonical profile; 2..4 in rich profile", "valid": "2..4"},
    "n_distinct_colors": {
        "type": "int", "default": "including background: 3 in canonical profile; 2..n_blobs in rich profile",
        "valid": "2..5",
    },
}
# Exactly the impossible color/component pairs, not a blanket allowance for
# placement failures. Every other advertised joint setting fits.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_blobs": 2, "n_distinct_colors": [4, 5]},
    {"n_blobs": 3, "n_distinct_colors": 5},
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("rich", "canonical_scale")
MIN_STRICT_FRAC = 0.25


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(seed, sample_index, difficulty, overrides):
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer, not bool/float/string")
    if difficulty is not None and difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    limits = {"grid_h": (8, 16), "grid_w": (8, 16), "n_blobs": (2, 4), "n_distinct_colors": (2, 5)}
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = limits[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, not bool/float/string")
    n, colors = overrides.get("n_blobs"), overrides.get("n_distinct_colors")
    if n is not None and colors is not None and colors > n + 1:
        raise ValueError("n_distinct_colors includes background and cannot exceed n_blobs + 1")


def _draw_axis(ctx, name, lo, hi, defaults):
    """Honor the full exact override range in every difficulty/profile."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(defaults))


def _split_slot(slot, axis, rng):
    r, c, h, w = slot
    length = h if axis == 0 else w
    cut = rng.randint(3, length - 4)
    if axis == 0:
        return (r, c, cut, w), (r + cut + 1, c, h - cut - 1, w)
    return (r, c, h, cut), (r, c + cut + 1, h, w - cut - 1)


def _slots(h, w, n, rng):
    """Two strips, a T partition, or independently split strip pairs.

    Each leaf is at least 3x3. Variable cuts, strip directions and independent
    second cuts avoid a fixed quadrant/orientation rule. No object is dropped.
    """
    axis = rng.randrange(2)
    slots = list(_split_slot((0, 0, h, w), axis, rng))
    if n == 3:
        chosen = rng.randrange(2)
        slots[chosen:chosen + 1] = _split_slot(slots[chosen], 1 - axis, rng)
    elif n == 4:
        slots = [part for slot in slots for part in _split_slot(slot, 1 - axis, rng)]
    rng.shuffle(slots)
    return slots


def _shape(h, w, rng, *, interior=False, sparse=False):
    # A connected elbow spans the exact bbox. Adding only frontier cells keeps
    # one component; reserving the opposite corner keeps it nonrectangular.
    cells = {(r, 0) for r in range(h)} | {(h - 1, c) for c in range(w)}
    if interior:
        cells.add((h // 2, 1))
    forbidden = (0, w - 1)
    extra_limit = min(h * w - 1, len(cells) + (1 if sparse else h * w))
    target = rng.randint(len(cells), extra_limit)
    while len(cells) < target:
        frontier = sorted({(r + dr, c + dc) for r, c in cells
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 0 <= r + dr < h and 0 <= c + dc < w
                           and (r + dr, c + dc) not in cells
                           and (r + dr, c + dc) != forbidden})
        cells.add(rng.choice(frontier))
    flip_r, flip_c = rng.randrange(2), rng.randrange(2)
    return {(h - 1 - r if flip_r else r, w - 1 - c if flip_c else c) for r, c in cells}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rich = schedule_profile(seed, sample_index, difficulty) == "rich"
    anchor = ctx.draw_choice("canonical_side", (8, 9, 10))
    broad_sizes = range(8, 13) if difficulty == "easy" else (
        range(11, 17) if difficulty == "hard" else range(8, 17))
    sizes = broad_sizes if rich else (anchor,)
    h = _draw_axis(ctx, "grid_h", 8, 16, sizes)
    w = _draw_axis(ctx, "grid_w", 8, 16, sizes)
    required_n = max(2, (overrides.get("n_distinct_colors") or 3) - 1)
    n_defaults = range(required_n, 5) if rich else (required_n,)
    n = _draw_axis(ctx, "n_blobs", 2, 4, n_defaults)
    color_defaults = range(2, n + 1) if rich else (3,)
    color_count = _draw_axis(ctx, "n_distinct_colors", 2, 5, color_defaults)
    if color_count > n + 1:
        raise ValueError("n_distinct_colors includes background and cannot exceed n_blobs + 1")

    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(range(1, 10), color_count - 1)
    colors = palette + [palette_rng.choice(palette) for _ in range(n - len(palette))]
    palette_rng.shuffle(colors)
    layout = _slots(h, w, n, ctx.draw_rng("partition"))
    grid = full_grid(h, w, 0)
    for index, ((r0, c0, slot_h, slot_w), color) in enumerate(zip(layout, colors)):
        rng = ctx.draw_rng(f"blob_{index}")
        interior = rich and index == 0
        min_side = 3 if interior else 2
        bh, bw = rng.randint(min_side, slot_h), rng.randint(min_side, slot_w)
        if not rich and index == 0:
            # Every canonical-scale sample retains a thin component, including
            # the canonical 3x2 case rejected by the predecessor validator.
            if rng.randrange(2):
                bh = 2
            else:
                bw = 2
        top = r0 + rng.randint(0, slot_h - bh)
        left = c0 + rng.randint(0, slot_w - bw)
        for r, c in _shape(bh, bw, rng, interior=interior, sparse=not rich):
            grid[top + r][left + c] = color
    return grid


def _components(grid):
    groups = find_objects(grid, univalued=True, diagonal=False, bg=0)
    return [(next(iter(group))[0], {cell for _, cell in group}) for group in groups]


def _bounds(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def self_check(grid, *, difficulty=None, meta=None):
    """Lawful nonoverlapping component boxes, wider than production sampling.

    Singletons, solid/thin boxes and different-color contacts are meaningful
    endpoints of the selected rule. Overlapping bboxes are excluded because
    their outlines may depend on paint order, which this sampler does not teach.
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["expected a nonempty list of nonempty rows"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid must fit the ARC 30x30 bounds"]
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        return ["grid colors must be integers 0..9, not bool"]
    groups = _components(grid)
    if not groups:
        return ["grid has no foreground components"]
    occupied = set()
    for _, cells in groups:
        r0, c0, r1, c1 = _bounds(cells)
        rectangle = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        if rectangle & occupied:
            return ["component bounding boxes overlap; paint-order collisions are outside this domain"]
        occupied.update(rectangle)
    return []


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_blobs": len(_components(grid)),
            "n_distinct_colors": len({color for row in grid for color in row})}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    if not (8 <= observed["grid_h"] <= 10 and 8 <= observed["grid_w"] <= 10
            and observed["n_blobs"] == 2 and observed["n_distinct_colors"] == 3):
        return ["outside the canonical 8..10 canvas, two-component, three-color profile"]
    return []


def _repeated_color(grid):
    return max(Counter(color for color, _ in _components(grid)).values(), default=0) > 1


def _occupied_interior(grid):
    return any(any(r0 < r < r1 and c0 < c < c1 for r, c in cells)
               for _, cells in _components(grid) for r0, c0, r1, c1 in [_bounds(cells)])


def _broad_box(grid):
    return any(r1 - r0 >= 2 and c1 - c0 >= 2
               for _, cells in _components(grid) for r0, c0, r1, c1 in [_bounds(cells)])


def _thin_box(grid):
    return any(min(r1 - r0, c1 - c0) <= 1
               for _, cells in _components(grid) for r0, c0, r1, c1 in [_bounds(cells)])


def _rival(grid, kind):
    """Deliberately different hypotheses for authoritative lesson checks."""
    groups = _components(grid)
    if kind == "color_union":
        by_color = {}
        for color, cells in groups:
            by_color.setdefault(color, set()).update(cells)
        groups = list(by_color.items())
    result = [row[:] for row in grid] if kind == "keep_interior" else full_grid(len(grid), len(grid[0]), 0)
    for color, cells in groups:
        r0, c0, r1, c1 = _bounds(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if kind == "fill" or r in (r0, r1) or c in (c0, c1):
                    result[r][c] = color
    return result


def _color_union(grid):
    return _rival(grid, "color_union")


def _keep_interior(grid):
    return _rival(grid, "keep_interior")


def _fill_boxes(grid):
    return _rival(grid, "fill")


SEMANTIC_WITNESSES = {
    "disconnected_same_color": _repeated_color,
    "occupied_bbox_interior": _occupied_interior,
    "broad_bbox": _broad_box,
    "thin_bbox": _thin_box,
}
SEMANTIC_RIVALS = {"color_union": _color_union, "keep_interior": _keep_interior, "fill_boxes": _fill_boxes}
WITNESS_RIVALS = {
    "disconnected_same_color": ["color_union"],
    "occupied_bbox_interior": ["keep_interior"],
    "broad_bbox": ["fill_boxes"],
}
BRANCH_WITNESSES = ["thin_bbox"]
CANONICAL_SHORTCUTS = {"color_union": _color_union, "keep_interior": _keep_interior}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check; never a claim of universal induction."""
    return [f"{name} fits demonstrations but changes the query"
            for name, predict in LESSON_COMPETITORS.items()
            if all(predict(pair["input"]) == pair["output"] for pair in demos)
            and predict(query["input"]) != query["output"]]
