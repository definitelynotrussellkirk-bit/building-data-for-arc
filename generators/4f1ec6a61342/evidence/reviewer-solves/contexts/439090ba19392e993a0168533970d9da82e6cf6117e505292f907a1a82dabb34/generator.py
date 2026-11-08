"""Count red cells in a walled chamber and match the top-left control.

Only inputs are generated. The pinned canonical Racket program supplies labels.
Alternating default profiles retain canonical crosses and supply counterexamples
to ordinal selection, occupied-column counting, and clipping the control at 3.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f1ec6a61342"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "f73a1c6442ab"
SUMMARY = (
    "Color-5 walls enclose 2..6 rectangular chambers. The top-left value "
    "1..6 selects the unique chamber containing exactly that many color-2 "
    "cells. The reference fills that chamber with 8 and erases other seeds; "
    "walls remain 5. The control becomes 0 except that control 5 remains 5. "
    "Canonical crosses alternate with count-disambiguating default inputs."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "rectangular integer grid with a color-5 outer border except the control",
    "2..6 nonempty rectangular four-connected chambers of colors 0 and 2",
    "top-left control is an integer 1..6 and is never counted as a seed",
    "exactly one chamber contains the requested number of seed cells",
    "every advertised exact override is recovered from the returned pixels",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..18; core favors 13", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "9..20; core favors 15", "valid": "9..20"},
    "n_chambers": {"type": "int", "default": "witness 2..4; core favors 4", "valid": "2..6"},
    "target_count": {"type": "int", "default": "witness 4..6; core favors 1..3", "valid": "1..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("count_witness", "core")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _axis(ctx, name, lo, hi, choices):
    # A profile changes default weights, never the validity of an exact override.
    options = tuple(range(lo, hi + 1)) if ctx.overrides.get(name) is not None else choices
    return ctx.draw_choice(name, options)


def _split_sizes(h, w, axis, cut):
    if axis == 0:
        return (cut, w), (h - cut - 1, w)
    return (h, cut), (h, w - cut - 1)


@lru_cache(maxsize=8192)
def _capacity(h, w, n, tall):
    """Largest eligible room in an n-leaf rectangular partition; 0 if impossible.

    Splits consume one wall row or column. Only the designated target needs a
    height of two when ``tall`` is true; other rooms may have height one.
    This finite geometry calculation prevents dropped chambers or clipped seeds.
    """
    if h < 1 or w < 1 or n < 1 or 2 * n - 1 > h * w:
        return 0
    if n == 1:
        return h * w if not tall or h >= 2 else 0
    best = 0
    for axis, length in ((0, h), (1, w)):
        for cut in range(1, length - 1):
            a, b = _split_sizes(h, w, axis, cut)
            for left_n in range(1, n):
                right_n = n - left_n
                left_any = _capacity(*a, left_n, False)
                right_any = _capacity(*b, right_n, False)
                if left_any and right_any:
                    best = max(best, _capacity(*a, left_n, tall),
                               _capacity(*b, right_n, tall))
    return best


@lru_cache(maxsize=8192)
def _split_options(h, w, n, need, tall):
    options = []
    for axis, length in ((0, h), (1, w)):
        for cut in range(1, length - 1):
            a, b = _split_sizes(h, w, axis, cut)
            for left_n in range(1, n):
                right_n = n - left_n
                if (_capacity(*a, left_n, tall) >= need
                        and _capacity(*b, right_n, False)):
                    options.append((axis, cut, left_n, 0))
                if (_capacity(*b, right_n, tall) >= need
                        and _capacity(*a, left_n, False)):
                    options.append((axis, cut, left_n, 1))
    return tuple(options)


def _partition(r, c, h, w, n, need, tall, rng):
    if n == 1:
        return [(r, c, r + h - 1, c + w - 1)]
    options = _split_options(h, w, n, need, tall)
    if not options:
        raise ValueError("requested chamber geometry has insufficient capacity")
    axis, cut, left_n, target_side = rng.choice(options)
    a, b = _split_sizes(h, w, axis, cut)
    r2, c2 = (r + cut + 1, c) if axis == 0 else (r, c + cut + 1)
    left = _partition(r, c, *a, left_n,
                      need if target_side == 0 else 1, tall and target_side == 0, rng)
    right = _partition(r2, c2, *b, n - left_n,
                       need if target_side == 1 else 1, tall and target_side == 1, rng)
    return left + right


def _cross(h, w, target, rng):
    # Each cross room has at least 2 rows and 2 columns. Dividers vary, including
    # asymmetric canonical geometries, without replaying any canonical grid.
    options = [(r, c) for r in range(3, h - 3) for c in range(3, w - 3)
               if max((r - 1) * (c - 1), (r - 1) * (w - c - 2),
                      (h - r - 2) * (c - 1), (h - r - 2) * (w - c - 2)) >= target]
    r, c = rng.choice(options)
    return [(1, 1, r - 1, c - 1), (1, c + 1, r - 1, w - 2),
            (r + 1, 1, h - 2, c - 1), (r + 1, c + 1, h - 2, w - 2)]


def _cells(rect):
    r1, c1, r2, c2 = rect
    return [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


@lru_cache(maxsize=4096)
def _teaching_options(h, w, n, target):
    """Construct two capacious rooms, so a larger-count decoy is always possible.

    Crosses and merged cross arms cover 2, 3 and 4 rooms. Every geometry has
    at least two rooms with target+1 cells; both are tall enough for repeated
    seed columns. Sorting removes dependence on set iteration order.
    """
    options = set()
    for r in range(3, h - 3):
        for c in range(3, w - 3):
            a, b = (1, 1, r - 1, c - 1), (1, c + 1, r - 1, w - 2)
            d, e = (r + 1, 1, h - 2, c - 1), (r + 1, c + 1, h - 2, w - 2)
            top, bottom = (1, 1, r - 1, w - 2), (r + 1, 1, h - 2, w - 2)
            left, right = (1, 1, h - 2, c - 1), (1, c + 1, h - 2, w - 2)
            layouts = {2: [(top, bottom), (left, right)],
                       3: [(top, d, e), (a, b, bottom), (left, b, e), (a, d, right)],
                       4: [(a, b, d, e)]}[n]
            for layout in layouts:
                if sum((r2 - r1 + 1) * (c2 - c1 + 1) >= target + 1
                       for r1, c1, r2, c2 in layout) >= 2:
                    options.add(tuple(sorted(layout)))
    return tuple(sorted(options))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    witness = schedule_profile(seed, sample_index, difficulty) == "count_witness"
    favored_h = list(range(7, 12)) if difficulty == "easy" else list(range(13, 19))
    favored_w = list(range(9, 14)) if difficulty == "easy" else list(range(15, 21))
    h = _axis(ctx, "grid_h", 7, 18, list(range(7, 19)) + (favored_h if witness else [13] * 48))
    w = _axis(ctx, "grid_w", 9, 20, list(range(9, 21)) + (favored_w if witness else [15] * 48))
    n = _axis(ctx, "n_chambers", 2, 6, [2, 3, 4] if witness else [2, 3, 4, 5, 6] + [4] * 24)
    target = _axis(ctx, "target_count", 1, 6, [4, 5, 6] if witness else [1, 2, 3] * 12 + [4, 5, 6])
    rng = ctx.draw_rng("layout")
    if witness and n <= 4:
        rects = rng.choice(_teaching_options(h, w, n, target))
    elif not witness and n == 4:
        rects = _cross(h, w, target, rng)
    else:
        rects = _partition(1, 1, h - 2, w - 2, n, target, target >= 2, rng)
    rooms = [_cells(rect) for rect in rects]
    capacities = [len(room) for room in rooms]
    grid = full_grid(h, w, 5)
    for room in rooms:
        for r, c in room:
            grid[r][c] = 0
    if not witness and n == 4 and target <= 3:
        # The canonical count multiset is a frequent component, not the entire
        # distribution. Explicit permutations preserve placement independence.
        allocations = [p for p in permutations(range(4))
                       if all(count <= capacity for count, capacity in zip(p, capacities))]
        counts = list(ctx.draw_rng("counts").choice(allocations))
        chosen = counts.index(target)
    else:
        eligible = [i for i, rect in enumerate(rects)
                    if capacities[i] >= target + (witness and n <= 4)
                    and (target < 2 or rect[2] > rect[0])]
        chosen = ctx.draw_rng("target_room").choice(eligible)
        count_rng = ctx.draw_rng("counts")
        counts = [count_rng.choice([v for v in range(min(cap, 7) + 1)
                                    if v != target and (not witness or v <= 2 or v > target)])
                  for cap in capacities]
        counts[chosen] = target
        if witness and n <= 4:
            # Refute clamped ordinal selection as well as the ordinary rank
            # rival. The target is not the chamber with the most seed cells.
            decoy = count_rng.choice([i for i in eligible if i != chosen])
            counts[decoy] = target + 1
    seed_rng = ctx.draw_rng("seed_positions")
    for i, (room, count) in enumerate(zip(rooms, counts)):
        placed = []
        if witness and i == chosen and count >= 2:
            available = set(room)
            pairs = [(r, c) for r, c in room if (r + 1, c) in available]
            r, c = seed_rng.choice(pairs)
            placed = [(r, c), (r + 1, c)]
        placed += seed_rng.sample([p for p in room if p not in placed], count - len(placed))
        for r, c in placed:
            grid[r][c] = 2
    grid[0][0] = target
    return grid


def _rooms(grid):
    h, w = len(grid), len(grid[0])
    seen = {(0, 0)}
    rooms = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 5:
                continue
            seen.add((r, c))
            queue, room = [(r, c)], []
            while queue:
                rr, cc = queue.pop()
                room.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = rr + dr, cc + dc
                    if (0 <= p[0] < h and 0 <= p[1] < w
                            and p not in seen and grid[p[0]][p[1]] != 5):
                        seen.add(p)
                        queue.append(p)
            rooms.append(room)
    return rooms


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_chambers": len(_rooms(grid)), "target_count": grid[0][0]}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9"]
    errors = []
    if not 7 <= h <= 18 or not 9 <= w <= 20:
        errors.append("grid dimensions outside 7..18 by 9..20")
    if not 1 <= grid[0][0] <= 6:
        errors.append("control must be 1..6")
    if any(grid[r][c] not in (0, 2, 5) for r in range(h) for c in range(w) if (r, c) != (0, 0)):
        errors.append("only colors 0, 2, 5 may occur outside the control")
    if any(grid[r][c] != 5 for r in range(h) for c in range(w)
           if (r, c) != (0, 0) and (r in (0, h - 1) or c in (0, w - 1))):
        errors.append("outer border must be color 5 except the control")
    rooms = _rooms(grid)
    if not 2 <= len(rooms) <= 6:
        errors.append(f"expected 2..6 chambers, got {len(rooms)}")
    for room in rooms:
        rs, cs = zip(*room)
        if len(room) != (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1):
            errors.append("chambers must be rectangular")
            break
    counts = [sum(grid[r][c] == 2 for r, c in room) for room in rooms]
    if sum(count == grid[0][0] for count in counts) != 1:
        errors.append("exactly one chamber must match the control seed count")
    return errors


def strict_canonical_like(grid):
    """Membership in the declared rectangular-chamber domain, not a shape proxy."""
    return self_check(grid)


def _paint(grid, selected):
    # Used only by declared rival probes, never to label generated data.
    out = [[5 if v == 5 else 0 for v in row] for row in grid]
    for room in selected:
        for r, c in room:
            out[r][c] = 8
    return out


def _ordinal_rank(grid):
    rooms = sorted(_rooms(grid), key=lambda room: sum(grid[r][c] == 2 for r, c in room))
    target = grid[0][0]
    return _paint(grid, rooms[target:target + 1])


def _clamped_ordinal_rank(grid):
    rooms = sorted(_rooms(grid), key=lambda room: sum(grid[r][c] == 2 for r, c in room))
    target = min(grid[0][0], len(rooms) - 1)
    return _paint(grid, rooms[target:target + 1])


def _distinct_seed_columns(grid):
    return _paint(grid, [room for room in _rooms(grid)
                        if len({c for r, c in room if grid[r][c] == 2}) == grid[0][0]])


def _clipped_control(grid):
    return _paint(grid, [room for room in _rooms(grid)
                        if sum(grid[r][c] == 2 for r, c in room) == min(grid[0][0], 3)])


def _refutes(grid, rival):
    expected_cells = [room for room in _rooms(grid)
                      if sum(grid[r][c] == 2 for r, c in room) == grid[0][0]]
    return rival(grid) != _paint(grid, expected_cells)


def _ordinal_witness(grid):
    return _refutes(grid, _ordinal_rank)


def _column_witness(grid):
    return _refutes(grid, _distinct_seed_columns)


def _clamped_rank_witness(grid):
    return _refutes(grid, _clamped_ordinal_rank)


def _clip_witness(grid):
    return _refutes(grid, _clipped_control)


SEMANTIC_RIVALS = {"ordinal_rank": _ordinal_rank,
                   "clamped_ordinal_rank": _clamped_ordinal_rank,
                   "distinct_seed_columns": _distinct_seed_columns,
                   "clipped_control": _clipped_control}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"ordinal_gap": _ordinal_witness,
                      "rank_saturation": _clamped_rank_witness,
                      "repeated_seed_column": _column_witness,
                      "high_control": _clip_witness}
WITNESS_RIVALS = {"ordinal_gap": ["ordinal_rank"],
                  "rank_saturation": ["clamped_ordinal_rank"],
                  "repeated_seed_column": ["distinct_seed_columns"],
                  "high_control": ["clipped_control"]}
