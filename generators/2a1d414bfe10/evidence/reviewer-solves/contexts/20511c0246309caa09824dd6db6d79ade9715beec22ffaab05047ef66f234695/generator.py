"""Input sampler for exactly two of three independently normalized color shapes.

Racket supplies all dataset labels. Python incidence calculations below select
teaching witnesses and implement deliberately competing rules; they are not a
replacement label authority. See notes.md for the compact/broad curriculum.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2a1d414bfe10"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "95b31785aa4f"
SUMMARY = (
    "Three separate connected shapes in fixed colors 1, 2, 3 on background 0. "
    "Normalize each shape independently; retain locations in exactly two "
    "supports, crop their bounding box, and paint them 8. Alternate compact "
    "five-cell shapes with broader counterexamples to declared shortcuts."
)
INVARIANTS = [
    "one nonempty four-connected shape per fixed color 1, 2, 3; background 0",
    "shape bounding boxes are separated by at least one background row or column",
    "normalize colors independently, without requiring equal bounding boxes",
    "at least one normalized location belongs to exactly two shapes",
    "all exact grid_h/grid_w combinations are honored; no partial-grid fallback",
]
AXES = {
    "grid_h": {"type": "int", "default": "8..16; compact draws favor 9/10", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "10..18; compact draws favor 11/12/13", "valid": "10..18"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("compact", "broad")
MIN_STRICT_FRAC = 1.0
_COLORS = (1, 2, 3)
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells):
    if not cells:
        return frozenset()
    top = min(r for r, c in cells)
    left = min(c for r, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _supports(grid):
    return tuple(_normalize({(r, c) for r, row in enumerate(grid)
                             for c, value in enumerate(row) if value == color})
                 for color in _COLORS)


def _exact_two(shapes):
    counts = Counter(point for shape in shapes for point in shape)
    return {point for point, count in counts.items() if count == 2}


def _render(cells):
    cells = _normalize(cells)
    if not cells:
        return [[0]]
    h, w = 1 + max(r for r, c in cells), 1 + max(c for r, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]


def _rival_outputs(shapes):
    """Wrong rules, including two shortcuts fitting all five canonical pairs."""
    counts = Counter(point for shape in shapes for point in shape)
    exact = {point for point, count in counts.items() if count == 2}
    h = 1 + max(r for shape in shapes for r, c in shape)
    w = 1 + max(c for shape in shapes for r, c in shape)
    common_h = min(1 + max(r for r, c in shape) for shape in shapes)
    common_w = min(1 + max(c for r, c in shape) for shape in shapes)
    clipped = tuple({p for p in shape if p[0] < 3 and p[1] < 3} for shape in shapes)
    first_five = tuple(set(sorted(shape)[:5]) for shape in shapes)
    return {
        "clip_3x3": _render(_exact_two(clipped)),
        "first_five": _render(_exact_two(first_five)),
        "at_least_two": _render({p for p, n in counts.items() if n >= 2}),
        "odd_parity": _render({p for p, n in counts.items() if n % 2}),
        "pair_12": _render(shapes[0] & shapes[1]),
        "common_bbox": _render({p for p in exact if p[0] < common_h and p[1] < common_w}),
        "uncropped": [[8 if (r, c) in exact else 0 for c in range(w)] for r in range(h)],
    }


def _grow_shape(rng, h, w, count):
    """Grow a connected polyomino in its own independently chosen frame."""
    cells = {(rng.randrange(h), rng.randrange(w))}
    while len(cells) < count:
        frontier = {(r + dr, c + dc) for r, c in cells for dr, dc in _STEPS
                    if 0 <= r + dr < h and 0 <= c + dc < w}
        frontier -= cells
        cells.add(rng.choice(sorted(frontier)))
    return _normalize(cells)


def schedule_profile(seed, sample_index, difficulty=None):
    """Two broad witnesses in any four consecutive samples, in every band."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_shapes(rng, slots, profile, difficulty):
    # A complete candidate is accepted or rejected before painting starts.
    # Exhaustion raises; it can never return an unfinished or overwritten grid.
    for _ in range(4096):
        shapes = []
        for top, left, slot_h, slot_w in slots:
            if profile == "compact":
                h, w = rng.choice(((2, 3), (3, 2), (3, 3)))
                count = 5
            else:
                h = rng.randint(2, min(5, slot_h))
                w = rng.randint(4, min(5, slot_w))
                cap = 9 if difficulty == "easy" else 12
                count = rng.randint(5, min(cap, h * w))
            shapes.append(_grow_shape(rng, h, w, count))
        if not _exact_two(shapes):
            continue
        if profile == "broad":
            intended = _render(_exact_two(shapes))
            if any(rival == intended for rival in _rival_outputs(shapes).values()):
                continue
        return shapes
    raise RuntimeError("could not construct a complete teaching witness in 4096 attempts")


def _separated(a, b):
    return (a[0] + a[2] < b[0] or b[0] + b[2] < a[0] or
            a[1] + a[3] < b[1] or b[1] + b[3] < a[1])


def _relocate_boxes(rng, h, w, boxes):
    """Translate whole boxes from a feasible packing, without a global divider.

    The current position is always legal, so every move has a candidate. Keeping
    a complete valid placement is distinct from returning a partially drawn grid.
    No color support or normalization changes during this layout-only step.
    """
    boxes = list(boxes)
    for _ in range(3):
        order = list(range(len(boxes)))
        rng.shuffle(order)
        for i in order:
            _, _, bh, bw = boxes[i]
            candidates = [(r, c, bh, bw) for r in range(h - bh + 1)
                          for c in range(w - bw + 1)
                          if all(i == j or _separated((r, c, bh, bw), box)
                                 for j, box in enumerate(boxes))]
            if not candidates:
                raise RuntimeError("a previously feasible box lost every legal position")
            boxes[i] = rng.choice(candidates)
    return boxes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "compact":
        favored_h, favored_w = [9, 10] * 20, [11, 12, 13] * 20
    elif difficulty == "easy":
        favored_h, favored_w = [8, 9, 10] * 4, [10, 11, 12] * 4
    elif difficulty == "hard":
        favored_h, favored_w = [13, 14, 15, 16] * 4, [15, 16, 17, 18] * 4
    else:
        favored_h, favored_w = [10, 11, 12] * 4, [12, 13, 14] * 4
    # Weighted full-domain choices preserve exact controls in every band/profile.
    h = ctx.draw_choice("grid_h", list(range(8, 17)) + favored_h)
    w = ctx.draw_choice("grid_w", list(range(10, 19)) + favored_w)
    layout = ctx.draw_rng("layout")
    split_r = layout.randint(3, h - 4)
    split_c = layout.randint(4, w - 5)
    slots = [(0, 0, split_r, split_c),
             (0, split_c + 1, split_r, w - split_c - 1),
             (split_r + 1, 0, h - split_r - 1, split_c),
             (split_r + 1, split_c + 1, h - split_r - 1, w - split_c - 1)]
    layout.shuffle(slots)
    slots = slots[:3]
    shapes = _draw_shapes(ctx.draw_rng("shapes"), slots, profile, difficulty)
    boxes = []
    for shape, (top, left, slot_h, slot_w) in zip(shapes, slots):
        shape_h = 1 + max(r for r, c in shape)
        shape_w = 1 + max(c for r, c in shape)
        r0 = top + layout.randint(0, slot_h - shape_h)
        c0 = left + layout.randint(0, slot_w - shape_w)
        boxes.append((r0, c0, shape_h, shape_w))
    boxes = _relocate_boxes(ctx.draw_rng("relocation"), h, w, boxes)
    grid = full_grid(h, w, 0)
    for color, shape, (r0, c0, _, _) in zip(_COLORS, shapes, boxes):
        for r, c in shape:
            if grid[r0 + r][c0 + c] != 0:
                raise RuntimeError("constructive placement collided")
            grid[r0 + r][c0 + c] = color
    return grid


def observe_overrides(grid):
    """Observe exact controls from returned pixels, independently of draw logs."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        return ["grid exceeds 30 rows or columns"]
    if any(type(value) is not int or value not in (0, 1, 2, 3) for row in grid for value in row):
        return ["cells must be integer colors 0, 1, 2, 3"]
    shapes = []
    boxes = []
    for color in _COLORS:
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        if not cells:
            return [f"no color-{color} cells"]
        reached = {min(cells)}
        frontier = list(reached)
        while frontier:
            r, c = frontier.pop()
            for dr, dc in _STEPS:
                point = r + dr, c + dc
                if point in cells and point not in reached:
                    reached.add(point)
                    frontier.append(point)
        if reached != cells:
            return [f"color-{color} is not one four-connected shape"]
        boxes.append((min(r for r, c in cells), max(r for r, c in cells),
                      min(c for r, c in cells), max(c for r, c in cells)))
        shapes.append(_normalize(cells))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if not (a[1] + 1 < b[0] or b[1] + 1 < a[0] or
                    a[3] + 1 < b[2] or b[3] + 1 < a[2]):
                return ["shape bounding boxes require a background row or column between them"]
    if not _exact_two(shapes):
        return ["no normalized location belongs to exactly two shapes"]
    return []


def strict_canonical_like(grid):
    """Task-lawful connected-shape manifold, including all canonical inputs."""
    return self_check(grid)


def _rival(name, grid):
    return _rival_outputs(_supports(grid))[name]


def _counterexample(name, grid):
    shapes = _supports(grid)
    return _rival_outputs(shapes)[name] != _render(_exact_two(shapes))


_RIVAL_NAMES = ("clip_3x3", "first_five", "at_least_two", "odd_parity",
                "pair_12", "common_bbox", "uncropped")
SEMANTIC_RIVALS = {name: (lambda grid, key=name: _rival(key, grid)) for name in _RIVAL_NAMES}
SEMANTIC_WITNESSES = {name: (lambda grid, key=name: _counterexample(key, grid)) for name in _RIVAL_NAMES}
WITNESS_RIVALS = {name: [name] for name in _RIVAL_NAMES}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in ("clip_3x3", "first_five")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report ambiguity against the declared finite rival set, never all rules."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but disagrees on the query")
    return reasons
