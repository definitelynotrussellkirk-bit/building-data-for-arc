"""Inputs for the canonical bounding-box projection matrix rule.

Alternate a contrast-rich lesson input with a broadly randomized input.  Racket
remains the label authority; the Python alternatives below are review rivals.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

GENERATOR_ID = "dfa5c1702b4c"
TASK_ID = GENERATOR_ID
RULE_HASH = "5264524f1c03"
VERSION = "3.0.1"
SUMMARY = (
    "Two to seven distinct-color, solid, separated rectangles on background 0. "
    "In top/left order, output their pairwise row/column projection matrix: "
    "both=3, row only=1, column only=2, neither=0. Alternate teaching inputs "
    "that distinguish ordering and one-cell overlaps with varied layouts."
)
INVARIANTS = [
    "2-7 distinct nonzero colors, each forming exactly one solid rectangle",
    "different rectangles have a one-cell Chebyshev moat",
    "output order is bounding-box top, then left; diagonal is 3",
    "all requested dimensions and object counts are realized exactly",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles / 10..20", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "canonical profiles / 11..20", "valid": "11..20"},
    "n_distinct_colors": {"type": "int", "default": "3-4 teaching; 2-7 varied", "valid": "2..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXPECTED_OUTPUT_CODOMAIN = (0, 1, 2, 3)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("teaching", "varied")
# Shape/palette-count support, not copies of canonical layouts or outputs.
_CANONICAL_PROFILES = ((12, 14, 3), (11, 13, 4), (10, 12, 3), (13, 15, 4), (12, 13, 4))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _axis(ctx, name, lo, hi, defaults):
    """Record the actual conditional draw; explicit controls use the full domain."""
    value = ctx.overrides.get(name)
    if value is not None:
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, defaults)


def _paint(h, w, rects, colors):
    grid = full_grid(h, w, 0)
    for (r0, c0, r1, c1), color in zip(rects, colors):
        fill_box(grid, r0, c0, r1, c1, color)
    return grid


def _separated(a, b):
    return a[2] + 1 < b[0] or b[2] + 1 < a[0] or a[3] + 1 < b[1] or b[3] + 1 < a[1]


def _teaching_rectangles(h, w, count, rng):
    # A tall rectangle A is left of singleton-height B at the SAME top row.
    # This teaches the left tie-break as well as reversing bottom/center order.
    # C distinguishes A and B by column projection.  A/B share exactly one row
    # and A/C exactly one column; C extends away from B to avoid a symmetry.
    aw, bw, cw = rng.randint(2, 3), rng.randint(1, 3), rng.randint(1, 3)
    reserve = 2 if count > 3 else 0
    ch = rng.randint(1, min(4, h - reserve - 5))
    top = rng.randint(0, h - reserve - 5 - ch)
    left = rng.randint(0, w - aw - bw - cw)
    a_left = left + cw - 1
    a_right = a_left + aw - 1
    rects = [
        (top, a_left, top + 3, a_right),
        (top, a_right + 2, top, a_right + bw + 1),
        (top + 5, left, top + 4 + ch, a_left),
    ]
    if count > 3:
        # A reserved separated row guarantees exact capacity even at 10x11,N=7.
        # Ordinary (odd-index) inputs do not have this teaching-only placement.
        slots = rng.sample(list(range(0, w, 2)), count - 3)
        rects.extend((h - 1, c, h - 1, c) for c in slots)
    return sorted(rects)


def _varied_rectangles(h, w, count, rng):
    for _ in range(16):
        rects = []
        for _ in range(count):
            for _ in range(80):
                bh, bw = rng.randint(1, 4), rng.randint(1, 4)
                r, c = rng.randrange(h - bh + 1), rng.randrange(w - bw + 1)
                candidate = (r, c, r + bh - 1, c + bw - 1)
                if all(_separated(candidate, other) for other in rects):
                    rects.append(candidate)
                    break
            else:
                break
        if len(rects) == count:
            return sorted(rects)
    # Constructive fallback: choose separated lattice cells and place a random
    # rectangle inside each.  Never return a partially placed count.
    rows, cols = 3, 3
    cell_h, cell_w = (h - rows + 1) // rows, (w - cols + 1) // cols
    rects = []
    for rr, cc in rng.sample([(r, c) for r in range(rows) for c in range(cols)], count):
        bh, bw = rng.randint(1, min(4, cell_h)), rng.randint(1, min(4, cell_w))
        r = rr * (cell_h + 1) + rng.randrange(cell_h - bh + 1)
        c = cc * (cell_w + 1) + rng.randrange(cell_w - bw + 1)
        rects.append((r, c, r + bh - 1, c + bw - 1))
    return sorted(rects)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, task_id=TASK_ID,
                  version=VERSION, difficulty=difficulty, overrides=overrides)
    teaching = schedule_profile(seed, sample_index, difficulty) == "teaching"
    if teaching:
        ph, pw, pn = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
        h_defaults, w_defaults, n_defaults = [ph], [pw], [pn]
    else:
        favored = {"easy": (2, 3, 4), "medium": (3, 4, 5), "hard": (5, 6, 7)}
        h_defaults = list(range(10, 21))
        w_defaults = list(range(11, 21))
        n_defaults = list(range(2, 8)) + list(favored.get(difficulty, (3, 4, 5))) * 3
    h = _axis(ctx, "grid_h", 10, 20, h_defaults)
    w = _axis(ctx, "grid_w", 11, 20, w_defaults)
    n = _axis(ctx, "n_distinct_colors", 2, 7, n_defaults)
    rng = ctx.draw_rng("layout")
    if teaching and n >= 3:
        rects = _teaching_rectangles(h, w, n, rng)
    else:
        rects = _varied_rectangles(h, w, n, rng)
    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(range(1, 10), n)
    grid = _paint(h, w, rects, colors)
    if teaching and n >= 3:
        # Teach geometry independently of numeric color rank.  Recolor only;
        # counts, rectangles and every requested control remain unchanged.
        for _ in range(24):
            if _color_sort(grid) != _projection(grid):
                break
            palette_rng.shuffle(colors)
            grid = _paint(h, w, rects, colors)
        else:
            colors.sort()
            colors[0], colors[1] = colors[1], colors[0]
            grid = _paint(h, w, rects, colors)
    return grid


def _boxes(grid):
    cells = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                cells.setdefault(color, []).append((r, c))
    return sorted(
        [(min(r for r, c in points), min(c for r, c in points),
          max(r for r, c in points), max(c for r, c in points), color)
         for color, points in cells.items()], key=lambda b: (b[0], b[1]))


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["expected nonempty row sequences"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        return ["grid dimensions exceed 30"]
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        return ["cells must be integer colors 0..9 (not booleans)"]
    boxes = _boxes(grid)
    errors = []
    if not 2 <= len(boxes) <= 7:
        errors.append(f"expected 2-7 distinct-color rectangles, got {len(boxes)}")
    for r0, c0, r1, c1, color in boxes:
        if any(grid[r][c] != color for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
            errors.append(f"color {color} is not one solid rectangle")
    for i, a in enumerate(boxes):
        if any(not _separated(a, b) for b in boxes[i + 1:]):
            errors.append(f"color {a[4]} lacks a one-cell moat")
    return errors


def strict_canonical_like(grid):
    """The canonical solid-rectangle manifold, independent of a shape profile."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_distinct_colors": len({v for row in grid for v in row if v})}


def _projection(grid, *, order="top", min_rows=1, min_cols=1, swap=False):
    """Geometry used to construct review rivals; never a label authority."""
    boxes = _boxes(grid)
    keys = {
        "top": lambda b: (b[0], b[1]),
        "top_tie_reverse": lambda b: (b[0], -b[1]),
        "bottom": lambda b: (b[2], b[1]),
        "center": lambda b: (b[0] + b[2], b[1]),
        "left": lambda b: (b[1], b[0]),
        "color": lambda b: b[4],
    }
    boxes.sort(key=keys[order])
    out = []
    for i, a in enumerate(boxes):
        row = []
        for j, b in enumerate(boxes):
            if i == j:
                row.append(3)
                continue
            ro = min(a[2], b[2]) - max(a[0], b[0]) + 1 >= min_rows
            co = min(a[3], b[3]) - max(a[1], b[1]) + 1 >= min_cols
            value = int(ro) + 2 * int(co)
            row.append({1: 2, 2: 1}.get(value, value) if swap else value)
        out.append(row)
    return out


def _bottom_sort(grid):
    return _projection(grid, order="bottom")


def _top_tie_reverse(grid):
    return _projection(grid, order="top_tie_reverse")


def _center_sort(grid):
    return _projection(grid, order="center")


def _left_sort(grid):
    return _projection(grid, order="left")


def _color_sort(grid):
    return _projection(grid, order="color")


def _two_row_overlap(grid):
    return _projection(grid, min_rows=2)


def _two_col_overlap(grid):
    return _projection(grid, min_cols=2)


def _swap_codes(grid):
    return _projection(grid, swap=True)


SEMANTIC_RIVALS = {
    "bottom_sort": _bottom_sort, "center_sort": _center_sort,
    "two_row_overlap": _two_row_overlap, "two_col_overlap": _two_col_overlap,
    "swap_codes": _swap_codes, "left_sort": _left_sort, "color_sort": _color_sort,
    "top_tie_reverse": _top_tie_reverse,
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                       for name in ("bottom_sort", "center_sort", "two_row_overlap")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_single_row_overlap(grid):
    boxes = _boxes(grid)
    return any(min(a[2], b[2]) - max(a[0], b[0]) + 1 == 1
               for i, a in enumerate(boxes) for b in boxes[i + 1:])


def _has_single_col_overlap(grid):
    boxes = _boxes(grid)
    return any(min(a[3], b[3]) - max(a[1], b[1]) + 1 == 1
               for i, a in enumerate(boxes) for b in boxes[i + 1:])


def _has_order_contrast(grid):
    intended = _projection(grid)
    return (_bottom_sort(grid) != intended and _center_sort(grid) != intended
            and _top_tie_reverse(grid) != intended)


SEMANTIC_WITNESSES = {
    "single_row_overlap": _has_single_row_overlap,
    "single_col_overlap": _has_single_col_overlap,
    "top_order_contrast": _has_order_contrast,
}
WITNESS_RIVALS = {
    "single_row_overlap": ["two_row_overlap"],
    "single_col_overlap": ["two_col_overlap"],
    "top_order_contrast": ["bottom_sort", "center_sort", "top_tie_reverse"],
}


def lesson_identifiable(demos, query):
    """Finite, query-aware declared-rival check; not a universal induction claim."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
