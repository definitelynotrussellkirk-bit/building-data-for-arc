"""Three components ranked by exposed unit-edge perimeter, stable on ties.

The selected Racket authority supplies outputs. Sampling explicitly separates
edge perimeter from canonical-fitting area and bounding-box shortcuts. Each
four-pair window contains two tied and two distinct-perimeter examples.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, is_well_formed
from puzzle_generators.helpers.indices import bbox, normalize_to_origin
from puzzle_generators.helpers.selfcheck import components_cells

GENERATOR_ID = "c78d339cf2f2"
TASK_ID = "c78d339cf2f2"
VERSION = "2.0.0"
RULE_HASH = "ea2222b6763c"
SUMMARY = "Rank three 4-connected components by exposed-edge perimeter; stable row-major ties; recolor 2,3,4."
INVARIANTS = [
    "background is 0; exactly three spatial 4-connected nonzero components",
    "generated components share one foreground color; input color does not determine rank",
    "perimeter includes hole boundaries; ties use row-major component discovery order",
    "every generated input distinguishes area, bbox perimeter, bbox area and scan-order ranking",
    "even sample indices teach stable perimeter ties; odd indices have three distinct perimeters",
]
AXES = {
    "grid_h": {"type": "int", "default": "weighted 8..20, favors 8..10", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "weighted 12..20, favors 12..13", "valid": "12..20"},
    "foreground": {"type": "int", "default": "weighted 1..9, favors canonical 6", "valid": "1..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("tied", "distinct")
MIN_STRICT_FRAC = 0.25
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _metrics(cells):
    body = frozenset(cells)
    r0, c0, r1, c1 = bbox(body)
    perimeter = sum((r + dr, c + dc) not in body for r, c in body for dr, dc in _DIRS)
    return perimeter, len(body), 2 * (r1 - r0 + c1 - c0 + 2), (r1 - r0 + 1) * (c1 - c0 + 1)


@lru_cache(maxsize=1)
def _shape_groups():
    """Finite geometry, not cached samples: all normalized connected 3x3 subsets.

    Keep oriented masks distinct. Vertical length-4/5 lines add the canonical
    long-line family while keeping every shape at most three columns wide.
    """
    shapes = set()
    for mask in range(1, 1 << 9):
        if mask.bit_count() < 2:
            continue
        cells = {(i // 3, i % 3) for i in range(9) if mask & (1 << i)}
        reached = {min(cells)}
        queue = [min(cells)]
        for r, c in queue:
            for dr, dc in _DIRS:
                point = (r + dr, c + dc)
                if point in cells and point not in reached:
                    reached.add(point)
                    queue.append(point)
        if reached == cells:
            shapes.add(tuple(sorted(normalize_to_origin(cells))))
    for length in (4, 5):
        shapes.add(tuple((r, 0) for r in range(length)))
    groups = {}
    for cells in sorted(shapes):
        groups.setdefault(_metrics(cells), []).append(cells)
    return {key: tuple(value) for key, value in sorted(groups.items())}


def _order(metrics, column):
    return tuple(sorted(range(3), key=lambda i: metrics[i][column]))


@lru_cache(maxsize=6)
def _profiles(tied, band):
    profiles = []
    for keys in product(_shape_groups(), repeat=3):
        distinct = len({key[0] for key in keys})
        if distinct != (2 if tied else 3):
            continue
        truth = _order(keys, 0)
        if truth == (0, 1, 2) or any(_order(keys, k) == truth for k in (1, 2, 3)):
            continue
        profiles.append(keys)
    # Difficulty changes weights without removing any parameter value or mode.
    favored = [p for p in profiles if (sum(k[1] for k in p) <= 16 if band == "easy"
                                      else sum(k[1] for k in p) >= 18 if band == "hard"
                                      else True)]
    return tuple(profiles + favored * 2)


def _separated(a, b, bh, bw):
    return a[0] + bh < b[0] or b[0] + bh < a[0] or a[1] + bw < b[1] or b[1] + bw < a[1]


def _slots(rng, h, w, bh, bw, truth):
    """Bounded random placement with a constructive, observable-safe fallback."""
    candidates = [(r, c) for r in range(h - bh + 1) for c in range(w - bw + 1)]
    for _ in range(24):
        rng.shuffle(candidates)
        chosen = []
        for origin in candidates:
            if all(_separated(origin, old, bh, bw) for old in chosen):
                chosen.append(origin)
                if len(chosen) == 3:
                    break
        if len(chosen) == 3:
            chosen.sort()
            column_order = tuple(sorted(range(3), key=lambda i: (chosen[i][1], chosen[i][0])))
            if column_order != truth:
                return chosen
    # The minimum 8x12 canvas fits three <=5x3 slots. Equal top rows ensure
    # both scan orders are (0,1,2), which the profile construction excludes.
    row = rng.randrange(h - bh + 1)
    return [(row, col) for col in (0, (w - bw) // 2, w - bw)]


def schedule_profile(seed, sample_index, difficulty=None):
    return "tied" if sample_index % 2 == 0 else "distinct"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be a literal integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = ctx.draw_choice("grid_h", list(range(8, 21)) + [8, 9, 10] * 8)
    w = ctx.draw_choice("grid_w", list(range(12, 21)) + [12, 13] * 12)
    color = ctx.draw_choice("foreground", list(range(1, 10)) + [6] * 9)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    tied = schedule_profile(seed, sample_index, difficulty) == "tied"
    keys = ctx.draw_rng("shape_profile").choice(_profiles(tied, band))
    groups = _shape_groups()
    shapes = [ctx.draw_rng(f"shape_{i}").choice(groups[key]) for i, key in enumerate(keys)]
    bh = max(max(r for r, c in body) + 1 for body in shapes)
    bw = max(max(c for r, c in body) + 1 for body in shapes)
    origins = _slots(ctx.draw_rng("positions"), h, w, bh, bw, _order(keys, 0))
    grid = full_grid(h, w, 0)
    for body, (r0, c0) in zip(shapes, origins):
        for r, c in body:
            grid[r + r0][c + c0] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the reference domain, including multicolor bodies and true ties."""
    if not is_well_formed(grid):
        return ["expected a rectangular ARC grid of integers 0..9 with dimensions 1..30"]
    if any(type(value) is not int for row in grid for value in row):
        return ["grid values must be literal integers, not booleans"]
    if not any(value == 0 for row in grid for value in row):
        return ["background 0 is required"]
    count = len(components_cells(grid, same_color=False))
    return [] if count == 3 else [f"expected exactly 3 spatial 4-connected components, found {count}"]


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if not (8 <= len(grid) <= 10 and 12 <= len(grid[0]) <= 13):
        return ["outside canonical dimension envelope 8..10 by 12..13"]
    if len({value for row in grid for value in row}) != 2:
        return ["canonical inputs use one foreground color on background 0"]
    return []


def observe_overrides(grid):
    colors = {value for row in grid for value in row if value}
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "foreground": next(iter(colors)) if len(colors) == 1 else None}


def _ranked(grid, metric=0, reverse=False, reverse_ties=False, spatial=None):
    """Python diagnostic hypotheses; production labels always come from Racket."""
    bodies = [tuple(sorted(body)) for body in components_cells(grid, same_color=False)]
    if spatial == "row":
        order = list(range(len(bodies)))
    elif spatial == "column":
        order = sorted(range(len(bodies)), key=lambda i: (min(c for r, c in bodies[i]), min(r for r, c in bodies[i])))
    else:
        order = sorted(range(len(bodies)), key=lambda i: (
            (-1 if reverse else 1) * _metrics(bodies[i])[metric], -i if reverse_ties else i))
    out = full_grid(len(grid), len(grid[0]), 0)
    for index, color in zip(order, (2, 3, 4)):
        for r, c in bodies[index]:
            out[r][c] = color
    return out


def _area(grid):
    return _ranked(grid, metric=1)


def _bbox_perimeter(grid):
    return _ranked(grid, metric=2)


def _bbox_area(grid):
    return _ranked(grid, metric=3)


def _row_major(grid):
    return _ranked(grid, spatial="row")


def _column_major(grid):
    return _ranked(grid, spatial="column")


def _descending(grid):
    return _ranked(grid, reverse=True)


def _reverse_ties(grid):
    return _ranked(grid, reverse_ties=True)


def _stable_tie(grid):
    values = [_metrics(body)[0] for body in components_cells(grid, same_color=False)]
    return len(values) == 3 and len(set(values)) < 3


def _metric_conflict(grid):
    truth = _ranked(grid)
    return all(rival(grid) != truth for rival in (_area, _bbox_perimeter, _bbox_area))


def lesson_identifiable(demos, query):
    if not demos:
        return ["no demonstrations"]
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


SEMANTIC_RIVALS = {"area": _area, "bbox_perimeter": _bbox_perimeter,
                   "bbox_area": _bbox_area, "row_major": _row_major,
                   "column_major": _column_major, "descending": _descending,
                   "reverse_ties": _reverse_ties}
CANONICAL_SHORTCUTS = {"area": _area, "bbox_perimeter": _bbox_perimeter}
LESSON_COMPETITORS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {"metric_conflict": _metric_conflict, "stable_tie": _stable_tie}
WITNESS_RIVALS = {"metric_conflict": ["area", "bbox_perimeter", "bbox_area"],
                  "stable_tie": ["reverse_ties"]}
