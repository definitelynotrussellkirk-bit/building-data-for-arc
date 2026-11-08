"""Inputs for scaling the second-smallest green four-connected component by two.

Racket remains the label authority. Default lessons interleave unrestricted
shape/placement draws with five-component witnesses that separate eight
canonical-fitting shortcuts. Controls change real, observable quantities.
"""
from __future__ import annotations

from functools import lru_cache, partial
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd05f2963d17"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "97705631e594"
SUMMARY = (
    "Three to five isolated green components with distinct cell counts; "
    "scale the second-smallest shape 2x at its bounding-box origin in cyan. "
    "Mix random polyominoes with explicit ranking, shape and anchor witnesses."
)
INVARIANTS = [
    "background 0 and foreground 3; four-neighbor components have distinct sizes",
    "ordinary inputs contain three to five components",
    "the second component ordered by (size, bbox row, bbox column) is the target",
    "the target's whole doubled bounding box fits; distractors are erased",
]
AXES = {
    "grid_h": {"type": "int", "default": "10..16, with weighted 11-row profiles",
               "valid": "10..16"},
    "grid_w": {"type": "int", "default": "11..17, with weighted 11-column profiles",
               "valid": "11..17"},
    "n_components": {"type": "int", "default": "3..5; odd default indices use 5",
                     "valid": "3..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
# Semantic/profile policy repeats; random shapes and positions do not repeat.
# This is the default schedule. Exact count overrides may disable its witnesses.
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("profile_general", "profile_teaching",
                     "varied_general", "varied_teaching")
MIN_STRICT_FRAC = 1.0
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _size_key(cells):
    r, c, _, _ = _bbox(cells)
    return len(cells), r, c


def _components_3(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3}
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells, frontier = {start}, [start]
        while frontier:
            r, c = frontier.pop()
            for dr, dc in _NEIGHBORS:
                neighbor = r + dr, c + dc
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    frontier.append(neighbor)
        found.append(cells)
    return found


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected equally sized grid rows"]
    if len(grid) > 30 or width > 30:
        return ["ARC grid dimensions must be at most 30"]
    if any(type(value) is not int or value not in (0, 3)
           for row in grid for value in row):
        return ["cells must be integer colors 0 or 3, excluding booleans"]
    components = sorted(_components_3(grid), key=_size_key)
    if len(components) < 3:
        return ["expected at least three green four-connected components"]
    reasons = []
    if len({len(cells) for cells in components}) != len(components):
        reasons.append("component cell counts must be strictly distinct")
    r0, c0, r1, c1 = _bbox(components[1])
    if r0 + 2 * (r1-r0+1) > len(grid) or c0 + 2 * (c1-c0+1) > width:
        reasons.append("second-smallest component's doubled bounding box exceeds the grid")
    return reasons


def strict_canonical_like(grid):
    """Task domain, including unseen shapes/counts; not memorized canonical grids."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_components": len(_components_3(grid))}


def _poly(rng, size, max_dim=4):
    """Grow a connected polyomino exactly; enumerate the available frontier."""
    cells = {(0, 0)}
    while len(cells) < size:
        options = set()
        for r, c in cells:
            for dr, dc in _NEIGHBORS:
                point = r + dr, c + dc
                if point in cells:
                    continue
                r0, c0, r1, c1 = _bbox(cells | {point})
                if r1-r0+1 <= max_dim and c1-c0+1 <= max_dim:
                    options.add(point)
        if not options:
            raise ValueError("polyomino size cannot fit the requested bounding box")
        cells.add(rng.choice(sorted(options)))
    r0, c0, _, _ = _bbox(cells)
    return tuple(sorted((r-r0, c-c0) for r, c in cells))


@lru_cache(maxsize=1)
def _teaching_targets():
    """All 14 connected five-cell 3x3 shapes with an empty bbox corner."""
    shapes = []
    square = tuple((r, c) for r in range(3) for c in range(3))
    for candidate in combinations(square, 5):
        cells = set(candidate)
        if (0, 0) in cells or _bbox(cells) != (0, 0, 2, 2):
            continue
        seen, frontier = {candidate[0]}, [candidate[0]]
        while frontier:
            r, c = frontier.pop()
            for dr, dc in _NEIGHBORS:
                point = r + dr, c + dc
                if point in cells and point not in seen:
                    seen.add(point)
                    frontier.append(point)
        if seen == cells:
            shapes.append(candidate)
    return tuple(shapes)


def _draw_dimension(ctx, name, low, high, *, core, band):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    choices = list(range(low, high+1))
    if core:
        choices += [11] * 200
    elif band == "easy":
        choices += [11, 12] * 5
    elif band == "hard":
        choices += [high-1, high] * 6
    else:
        choices += [12, 13, 14] * 2
    return ctx.draw_choice(name, choices)


def _try_placement(shapes, h, w, rng, *, teaching):
    """Randomize rank placement; only four-neighbor contact merges components."""
    candidates = []
    for index, shape in enumerate(shapes):
        _, _, bottom, right = _bbox(shape)
        factor = 2 if index == 1 else 1
        candidates.append([(r, c)
                           for r in range(h-factor*(bottom+1)+1)
                           for c in range(w-factor*(right+1)+1)])
    for _ in range(40):
        order = list(range(len(shapes)))
        rng.shuffle(order)
        occupied, forbidden, positions = set(), set(), {}
        for index in order:
            origins = candidates[index][:]
            rng.shuffle(origins)
            for r0, c0 in origins:
                cells = {(r+r0, c+c0) for r, c in shapes[index]}
                if cells.isdisjoint(forbidden):
                    positions[index] = r0, c0
                    occupied.update(cells)
                    forbidden.update(cells)
                    forbidden.update((r+dr, c+dc) for r, c in cells
                                     for dr, dc in _NEIGHBORS)
                    break
            else:
                break
        if len(positions) != len(shapes):
            continue
        if teaching and positions[1] == max(positions.values()):
            continue
        grid = full_grid(h, w, 0)
        for r, c in occupied:
            grid[r][c] = 3
        return grid
    return None


def _compact_placement(shapes, h, w, rng, *, teaching):
    """Constructive fallback: six separated 3x3 slots fit every advertised size."""
    slots = [(r, c) for r in (0, 4) for c in (0, 4, 8)]
    target_slots = [(r, c) for r, c in slots
                    if r + 2*(_bbox(shapes[1])[2]+1) <= h
                    and c + 2*(_bbox(shapes[1])[3]+1) <= w
                    and (not teaching or r == 0)]
    target = rng.choice(target_slots)
    remaining = [slot for slot in slots if slot != target]
    rng.shuffle(remaining)
    grid = full_grid(h, w, 0)
    for index, shape in enumerate(shapes):
        r0, c0 = target if index == 1 else remaining.pop()
        for r, c in shape:
            grid[r+r0][c+c0] = 3
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unsupported override keys: " + ", ".join(sorted(unknown)))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, excluding booleans")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = sample_index % 4 < 2
    h = _draw_dimension(ctx, "grid_h", 10, 16, core=core, band=difficulty)
    w = _draw_dimension(ctx, "grid_w", 11, 17, core=core, band=difficulty)
    if overrides.get("n_components") is not None:
        count = ctx.draw_int_strict("n_components", 3, 5)
    else:
        count = ctx.draw_choice("n_components", [5] if sample_index % 2 else [3, 4, 5])
    teaching = bool(sample_index % 2 and count == 5)
    rng = ctx.draw_rng(f"shapes:{difficulty or 'medium'}")
    if teaching:
        small = rng.randint(1, 4)
        sizes = [small, 5, 6, 7, 8]
        rectangle = tuple((r, c) for r in range(2) for c in range(3))
        if rng.choice((False, True)):
            rectangle = tuple((c, r) for r, c in rectangle)
        shapes = [_poly(rng, small, 3), rng.choice(_teaching_targets()),
                  rectangle, _poly(rng, 7, 3), _poly(rng, 8, 3)]
    else:
        pool = range(1, 8) if difficulty == "easy" else (
            range(3, 10) if difficulty == "hard" else range(1, 10))
        sizes = sorted(rng.sample(list(pool), count))
        shapes = [_poly(rng, size, rng.choice((3, 4))) for size in sizes]
    placement_rng = ctx.draw_rng(f"placement:{difficulty or 'medium'}")
    grid = _try_placement(shapes, h, w, placement_rng, teaching=teaching)
    if grid is None:
        if not teaching:
            # Shape is not an exact control: preserve every requested count/size,
            # and compact only after the random placement search is exhausted.
            shapes = [_poly(rng, size, 3) for size in sizes]
        grid = _compact_placement(shapes, h, w, placement_rng, teaching=teaching)
    return grid


def _rival_grid(grid, name):
    """Authoring-only hypotheses. Generated labels still come only from Racket."""
    components = _components_3(grid)
    ranked = sorted(components, key=_size_key)
    target = ranked[1]
    if name == "second_largest":
        target = ranked[-2]
    elif name == "lower_median":
        target = ranked[(len(ranked)-1)//2]
    elif name == "upper_median":
        target = ranked[len(ranked)//2]
    elif name == "fixed_size_4":
        target = next((cells for cells in ranked if len(cells) == 4), ranked[0])
    elif name == "bottommost":
        target = max(components, key=lambda cells: _bbox(cells)[:2])
    elif name == "bbox_second":
        def box_key(cells):
            r0, c0, r1, c1 = _bbox(cells)
            return (r1-r0+1)*(c1-c0+1), r0, c0
        target = sorted(components, key=box_key)[1]
    r0, c0, _, _ = _bbox(target)
    shape = {(r-r0, c-c0) for r, c in target}
    if name == "fixed_S_stamp":
        shape = {(0, 0), (0, 1), (1, 1), (1, 2)}
    elif name == "first_cell_anchor":
        r0, c0 = min(target)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c in shape:
        for dr in range(2):
            for dc in range(2):
                rr, cc = r0+2*r+dr, c0+2*c+dc
                if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                    out[rr][cc] = 8
    return out


_RIVAL_NAMES = ("second_largest", "lower_median", "upper_median", "fixed_size_4",
                "bottommost", "bbox_second", "fixed_S_stamp", "first_cell_anchor")
SEMANTIC_RIVALS = {name: partial(_rival_grid, name=name) for name in _RIVAL_NAMES}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, name):
    return (not self_check(grid)
            and _rival_grid(grid, "intended") != _rival_grid(grid, name))


SEMANTIC_WITNESSES = {name: partial(_refutes, name=name) for name in _RIVAL_NAMES}
WITNESS_RIVALS = {name: [name] for name in _RIVAL_NAMES}


def lesson_identifiable(demos, query):
    """Finite declared-rival ambiguity check on already labelled lessons."""
    return [f"{name} fits every demonstration but disagrees with the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
