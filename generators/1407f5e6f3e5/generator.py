"""Input sampler for component-wise bounding-box filling.

The unchanged Racket authority finds every same-color 4-connected nonzero
component and paints its tight bounding box on a fresh zero canvas.  Default
even sample indices are teaching scenes with two disconnected components of the
same color; they distinguish component segmentation from the canonical-fitting
shortcut that merges all cells of one color before taking a bounding box.
Odd indices alternate between a canonical-profile anchor and broad sampling.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1407f5e6f3e5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c86a6d30fc9f"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SUMMARY = (
    "A zero-background grid contains 2-4 same-color 4-connected sparse objects. "
    "Each object's tight bounding box has at least one hole and object bounding "
    "boxes do not overlap. Fill every component's bounding box with that "
    "component's color on a fresh zero canvas. Scheduled repeated-color scenes "
    "teach that disconnected objects are processed separately."
)
INVARIANTS = [
    "background is 0 and all cells are integer ARC colors",
    "there are 2-4 same-color 4-connected components of 3-7 cells",
    "every component has a 2x2..3x3 bounding box with at least one hole",
    "component bounding boxes are disjoint",
    "zero or one color is reused by exactly two disconnected components",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/weighted 8..13", "valid": "8..13"},
    "grid_w": {"type": "int", "default": "scheduled/weighted 9..14", "valid": "9..14"},
    "components": {"type": "int", "default": "scheduled/weighted 2..4", "valid": "2..4"},
    "repeat_color": {"type": "int", "default": "teaching 1; otherwise 0..1", "valid": "0..1"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("teaching", "ordinary")
CANONICAL_DIMENSIONS = ((8, 10), (9, 11), (8, 9), (10, 10), (9, 10))

_AXIS_BOUNDS = {
    "grid_h": (8, 13),
    "grid_w": (9, 14),
    "components": (2, 4),
    "repeat_color": (0, 1),
}
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    reached = {min(cells)}
    todo = list(reached)
    for r, c in todo:
        for dr, dc in _STEPS:
            point = r + dr, c + dc
            if point in cells and point not in reached:
                reached.add(point)
                todo.append(point)
    return reached == cells


def _shape_library():
    """All normalized holed connected subsets of a 3x3 box, sizes 3..7."""
    points = tuple((r, c) for r in range(3) for c in range(3))
    shapes = set()
    for size in range(3, 8):
        for chosen in combinations(points, size):
            shape = _normalize(chosen)
            if shape in shapes or not _connected(shape):
                continue
            height = max(r for r, _ in shape) + 1
            width = max(c for _, c in shape) + 1
            if height >= 2 and width >= 2 and len(shape) < height * width:
                shapes.add(shape)
    return tuple(sorted(shapes, key=lambda s: (len(s), max(r for r, _ in s), max(c for _, c in s), s)))


_SHAPES = _shape_library()
_FALLBACK_SHAPE = ((0, 0), (1, 0), (1, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four-pair lesson window has two repeated-color teaching scenes."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % 2]


def _weighted_domain(lo, hi, favored):
    """Keep full override support while weighting ordinary default draws."""
    return tuple(range(lo, hi + 1)) + tuple(favored) * 3


def _bbox(shape, r0, c0):
    return (r0, c0,
            r0 + max(r for r, _ in shape),
            c0 + max(c for _, c in shape))


def _boxes_have_moat(a, b):
    """True when boxes are separated by at least one complete row or column."""
    return (a[2] + 1 < b[0] or b[2] + 1 < a[0]
            or a[3] + 1 < b[1] or b[3] + 1 < a[1])


def _placements(shape, h, w):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    return [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]


def _place_shapes(h, w, shapes, rng):
    """Place every requested shape exactly using finite backtracking, never truncation."""
    ordered = sorted(shapes, key=lambda s: (-(max(r for r, _ in s) + 1) * (max(c for _, c in s) + 1), -len(s), s))
    candidates = []
    for shape in ordered:
        options = _placements(shape, h, w)
        rng.shuffle(options)
        candidates.append(options)

    result = []
    boxes = []

    def search(index):
        if index == len(ordered):
            return True
        shape = ordered[index]
        for r0, c0 in candidates[index]:
            box = _bbox(shape, r0, c0)
            if all(_boxes_have_moat(box, prior) for prior in boxes):
                boxes.append(box)
                result.append((shape, r0, c0))
                if search(index + 1):
                    return True
                result.pop()
                boxes.pop()
        return False

    if search(0):
        return result

    # Defensive deterministic fallback.  Four 2x2 L-triomino boxes with a
    # one-cell moat fit the smallest advertised 8x9 canvas, so failure here
    # signals an implementation error rather than a seed-dependent short draw.
    fallback = [_FALLBACK_SHAPE] * len(shapes)
    ordered = fallback
    candidates = []
    for shape in ordered:
        options = _placements(shape, h, w)
        rng.shuffle(options)
        candidates.append(options)
    result.clear()
    boxes.clear()
    if search(0):
        return result
    raise RuntimeError(f"constructive placement failed for {len(shapes)} objects in {h}x{w}")


def _component_records(grid):
    """Same-color 4-connected objects in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            todo = [(r, c)]
            cells = []
            for cr, cc in todo:
                cells.append((cr, cc))
                for dr, dc in _STEPS:
                    point = cr + dr, cc + dc
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        todo.append(point)
            box = (min(x for x, _ in cells), min(y for _, y in cells),
                   max(x for x, _ in cells), max(y for _, y in cells))
            result.append((color, tuple(cells), box))
    return result


def observe_overrides(grid):
    records = _component_records(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "components": len(records),
        "repeat_color": len(records) - len({color for color, _, _ in records}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid exceeds ARC 30x30 limit"]
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    records = _component_records(grid)
    errors = []
    if not 2 <= len(records) <= 4:
        errors.append(f"expected 2..4 components, found {len(records)}")
    repeat_color = len(records) - len({color for color, _, _ in records})
    if repeat_color not in (0, 1):
        errors.append(f"expected zero or one repeated component color, found excess {repeat_color}")

    boxes = []
    for index, (_, cells, box) in enumerate(records):
        r0, c0, r1, c1 = box
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        if not 3 <= len(cells) <= 7:
            errors.append(f"component {index} must contain 3..7 cells, found {len(cells)}")
        if not (2 <= bh <= 3 and 2 <= bw <= 3):
            errors.append(f"component {index} bbox must be 2x2..3x3, found {bh}x{bw}")
        if len(cells) >= bh * bw:
            errors.append(f"component {index} bbox must contain at least one background hole")
        boxes.append(box)
    for left in range(len(boxes)):
        for right in range(left + 1, len(boxes)):
            a, b = boxes[left], boxes[right]
            if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                errors.append(f"component bboxes {left} and {right} overlap")
    return errors


def strict_canonical_like(grid):
    """Lawful component-bbox instances supported by this sampler."""
    return self_check(grid)


def _prediction(grid):
    """Supplementary executable contract; selected Racket remains authority."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, _, (r0, c0, r1, c1) in _component_records(grid):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def _global_color_bbox(grid):
    """Rival: incorrectly merge disconnected same-color components first."""
    points = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                points[value].append((r, c))
    out = full_grid(len(grid), len(grid[0]), 0)
    for color in sorted(points):
        cells = points[color]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def _repeated_color_components(grid):
    records = _component_records(grid)
    return (len(records) > len({color for color, _, _ in records})
            and _prediction(grid) != _global_color_bbox(grid))


SEMANTIC_RIVALS = {"global_color_bbox": _global_color_bbox}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"repeated_color_components": _repeated_color_components}
WITNESS_RIVALS = {"repeated_color_components": ["global_color_bbox"]}


def lesson_identifiable(demos, query):
    """Check finite declared rivals; this is not a universal uniqueness proof."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"declared rival {name} fits every demonstration but changes the query")
    return reasons


def _draw_axes(ctx, *, teaching, core, difficulty):
    if core:
        h, w = ctx.draw_rng("canonical_profile").choice(CANONICAL_DIMENSIONS)
        return (
            ctx.draw_choice("grid_h", (h,)),
            ctx.draw_choice("grid_w", (w,)),
            ctx.draw_choice("components", (3,)),
            ctx.draw_choice("repeat_color", (0,)),
        )

    favored_h = {
        None: (8, 9, 10, 11, 12, 13),
        "easy": (8, 8, 9, 9, 10),
        "medium": (9, 10, 11, 12),
        "hard": (11, 12, 13, 13),
    }[difficulty]
    favored_w = {
        None: (9, 10, 11, 12, 13, 14),
        "easy": (9, 9, 10, 10, 11),
        "medium": (10, 11, 12, 13),
        "hard": (12, 13, 14, 14),
    }[difficulty]
    favored_components = {
        None: (2, 3, 4), "easy": (2, 2, 3),
        "medium": (2, 3, 3, 4), "hard": (3, 4, 4),
    }[difficulty]
    h = ctx.draw_choice("grid_h", _weighted_domain(8, 13, favored_h))
    w = ctx.draw_choice("grid_w", _weighted_domain(9, 14, favored_w))
    count = ctx.draw_choice("components", _weighted_domain(2, 4, favored_components))
    repeat = ctx.draw_choice("repeat_color", (1,) if teaching else _weighted_domain(0, 1, (0, 1)))
    return h, w, count, repeat


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    explicit = any(value is not None for value in overrides.values())
    teaching = not explicit and schedule_profile(seed, sample_index, difficulty) == "teaching"
    core = not explicit and not teaching and sample_index % 4 == 1
    h, w, count, repeat = _draw_axes(ctx, teaching=teaching, core=core, difficulty=difficulty)

    shape_rng = ctx.draw_rng("component_shapes")
    shapes = [shape_rng.choice(_SHAPES) for _ in range(count)]
    placements = _place_shapes(h, w, shapes, ctx.draw_rng("component_layout"))

    color_rng = ctx.draw_rng("component_colors")
    distinct_count = count - repeat
    palette = color_rng.sample(list(range(1, 10)), distinct_count)
    if repeat:
        colors = [palette[0], palette[0], *palette[1:]]
    else:
        colors = list(palette)
    color_rng.shuffle(colors)

    grid = full_grid(h, w, 0)
    for (shape, r0, c0), color in zip(placements, colors):
        for dr, dc in shape:
            grid[r0 + dr][c0 + dc] = color

    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "components": count, "repeat_color": repeat}
    if observed != expected:
        raise RuntimeError(f"constructive scene mismatch: expected {expected}, observed {observed}")
    return grid
