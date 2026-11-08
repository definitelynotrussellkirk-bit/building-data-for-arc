"""Generator for ARC task 5bb29951ab1a.

The input contains several rectangles in one color and dots in a second color.
The unchanged Racket authority recolors a dot to the rectangle color exactly
when at least two of its four orthogonal neighbors are rectangle cells;
all other dots become background.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5bb29951ab1a"
TASK_ID = GENERATOR_ID
RULE_HASH = "9d2494fd4f65"
VERSION = "2.0.0"
SUMMARY = (
    "Multiple same-color rectangles contain or flank a second-color dot set. "
    "Dots with at least two orthogonal rectangle-color neighbors are absorbed; "
    "one-neighbor and isolated dots are removed."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 0 and exactly two nonzero colors are present",
    "the more frequent nonzero color forms two to five separated rectangles",
    "at least two dots have >=2 orthogonal rectangle-color neighbors",
    "at least one dot has exactly one rectangle-color neighbor",
    "at least one dot has no rectangle-color neighbor",
    "every generated input includes an opposite-neighbor bridge witness",
]

# Ordered pairs are (rectangle color, dot color).  The first three reproduce
# all official palettes; the others broaden color support without changing the
# frequency-based role inference used by the authority.
_PALETTES = (
    (2, 1), (3, 8), (5, 4), (1, 6),
    (4, 7), (6, 9), (8, 3), (9, 2),
)

AXES = {
    "grid_h": {"type": "int", "default": "weighted toward 12..13", "valid": "12..17"},
    "grid_w": {"type": "int", "default": "weighted toward 14,16,17", "valid": "14..19"},
    "n_absorb": {"type": "int", "default": "2..8, difficulty weighted", "valid": "2..8"},
    "n_reject": {"type": "int", "default": "2..8, difficulty weighted", "valid": "2..8"},
    "palette_id": {"type": "int", "default": "0..7", "valid": "0..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_OPPOSITE = {frozenset(((-1, 0), (1, 0))), frozenset(((0, -1), (0, 1)))}


def _weighted(ctx, name, lo, hi, favored):
    choices = list(range(lo, hi + 1)) + list(favored) * 5
    return ctx.draw_choice(name, choices)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (12, 17),
        "grid_w": (14, 19),
        "n_absorb": (2, 8),
        "n_reject": (2, 8),
        "palette_id": (0, len(_PALETTES) - 1),
    }
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _validate_difficulty(difficulty):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    _validate_difficulty(difficulty)


def _partition(total, parts):
    """Return `parts` intervals with one-cell margins and one-cell gaps."""
    usable = total - 2 - (parts - 1)
    if usable < 3 * parts:
        raise ValueError(f"cannot fit {parts} rectangle bands in length {total}")
    base, extra = divmod(usable, parts)
    sizes = [base + (index < extra) for index in range(parts)]
    starts = []
    cursor = 1
    for size in sizes:
        starts.append((cursor, size))
        cursor += size + 1
    return starts


def _layout_candidates(h, w, count):
    # A two-rectangle layout must use adjacent slots.  Allowing a three-slot
    # strip and then dropping its middle slot can leave two disconnected
    # rectangles, eliminating the opposite-neighbor bridge this construction
    # is designed to guarantee.  Larger one-extra-slot layouts remain safe:
    # deleting any one cell from a 2x2 or 2x3 slot grid leaves an adjacent pair.
    shapes = {
        2: ((1, 2), (2, 1)),
        3: ((1, 3), (3, 1), (2, 2)),
        4: ((2, 2),),
        5: ((2, 3), (3, 2)),
    }
    candidates = []
    for rows, cols in shapes.get(count, ()):
        try:
            _partition(h, rows)
            _partition(w, cols)
        except ValueError:
            continue
        candidates.append((rows, cols))
    if not candidates:
        raise ValueError(f"no constructive layout for {count} rectangles on {h}x{w}")
    return candidates


def _rectangles(h, w, count, rng):
    rows, cols = rng.choice(_layout_candidates(h, w, count))
    row_bands = _partition(h, rows)
    col_bands = _partition(w, cols)
    slots = [(ri, ci) for ri in range(rows) for ci in range(cols)]
    if len(slots) > count:
        slots.remove(rng.choice(slots))
    rng.shuffle(slots)
    rectangles = []
    for ri, ci in slots:
        rr, rh = row_bands[ri]
        rc, rw = col_bands[ci]
        rectangles.append((rr, rc, rh, rw))
    return rectangles


def _adjacent_directions(grid, r, c, color):
    h, w = len(grid), len(grid[0])
    return tuple(
        (dr, dc)
        for dr, dc in _DIRS
        if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == color
    )


def _bridge_candidates(grid, rect_color):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0 and frozenset(_adjacent_directions(grid, r, c, rect_color)) in _OPPOSITE
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _weighted(ctx, "grid_h", 12, 17, (12, 13))
    w = _weighted(ctx, "grid_w", 14, 19, (14, 16, 17))
    if difficulty == "easy":
        absorb_favored, reject_favored, rect_choices = (2, 3, 4), (2, 3, 4), (2, 2, 3)
    elif difficulty == "hard":
        absorb_favored, reject_favored, rect_choices = (6, 7, 8), (6, 7, 8), (4, 5, 5)
    else:
        absorb_favored, reject_favored, rect_choices = (3, 4, 5, 6), (3, 4, 5, 6), (2, 3, 4, 5)
    n_absorb = _weighted(ctx, "n_absorb", 2, 8, absorb_favored)
    n_reject = _weighted(ctx, "n_reject", 2, 8, reject_favored)
    palette_id = ctx.draw_choice("palette_id", list(range(len(_PALETTES))))
    rect_color, dot_color = _PALETTES[palette_id]

    rectangle_count = ctx.draw_rng("rectangle_count").choice(rect_choices)
    placement_rng = ctx.draw_rng("rectangle_layout")
    rectangles = _rectangles(h, w, rectangle_count, placement_rng)
    grid = full_grid(h, w, 0)
    for rr, rc, rh, rw in rectangles:
        for r in range(rr, rr + rh):
            for c in range(rc, rc + rw):
                grid[r][c] = rect_color

    # A one-cell gutter between adjacent rectangles supplies a lawful dot with
    # exactly two opposite rectangle neighbors.  This is the key witness that
    # canonical demonstrations omit and the declared shortcut gets wrong.
    bridges = _bridge_candidates(grid, rect_color)
    if not bridges:
        raise RuntimeError("constructive layout produced no opposite-neighbor bridge")
    dot_rng = ctx.draw_rng("dot_positions")
    bridge = dot_rng.choice(bridges)

    # Same-parity rectangle cells are never orthogonally adjacent, so replacing
    # any subset preserves each selected cell's original >=2 neighbor count.
    phase = dot_rng.randrange(2)
    bridge_neighbors = {
        (bridge[0] + dr, bridge[1] + dc)
        for dr, dc in _DIRS
        if 0 <= bridge[0] + dr < h and 0 <= bridge[1] + dc < w
    }
    replacements = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == rect_color
        and (r + c) % 2 == phase
        and (r, c) not in bridge_neighbors
        and len(_adjacent_directions(grid, r, c, rect_color)) >= 2
    ]
    needed = n_absorb - 1
    if len(replacements) < needed:
        raise RuntimeError(f"only {len(replacements)} absorbable cells for requested {needed}")
    absorbed = [bridge] + dot_rng.sample(replacements, needed)
    for r, c in absorbed:
        grid[r][c] = dot_color

    one_candidates = []
    zero_candidates = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            adjacent = len(_adjacent_directions(grid, r, c, rect_color))
            if adjacent == 1:
                one_candidates.append((r, c))
            elif adjacent == 0:
                zero_candidates.append((r, c))
    n_one = (n_reject + 1) // 2
    n_zero = n_reject - n_one
    if len(one_candidates) < n_one or len(zero_candidates) < n_zero:
        raise RuntimeError(
            f"insufficient reject positions: one={len(one_candidates)}/{n_one}, "
            f"zero={len(zero_candidates)}/{n_zero}"
        )
    for r, c in dot_rng.sample(one_candidates, n_one) + dot_rng.sample(zero_candidates, n_zero):
        grid[r][c] = dot_color

    # Refuse silent shortening or role inversion if this implementation changes.
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_absorb": n_absorb,
        "n_reject": n_reject,
        "palette_id": palette_id,
    }
    if observed != expected:
        raise RuntimeError(f"constructive generation mismatch: expected {expected}, observed {observed}")
    return grid


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["every row must be a nonempty sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9 (booleans rejected)"]

    counts = Counter(value for row in grid for value in row)
    nonzero = sorted(((count, color) for color, count in counts.items() if color), reverse=True)
    if len(nonzero) != 2:
        return None, [f"expected exactly two nonzero colors, found {len(nonzero)}"]
    (rect_count, rect_color), (dot_count, dot_color) = nonzero
    if rect_count <= dot_count:
        errors.append("rectangle color is not strictly more frequent than dot color")
    if rect_count < 9:
        errors.append("rectangle support is too small")

    absorb = reject = one = zero = opposite_two = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != dot_color:
                continue
            directions = _adjacent_directions(grid, r, c, rect_color)
            adjacent = len(directions)
            absorb += adjacent >= 2
            reject += adjacent < 2
            one += adjacent == 1
            zero += adjacent == 0
            opposite_two += adjacent == 2 and frozenset(directions) in _OPPOSITE
    if absorb < 1:
        errors.append("no dot has at least two rectangle neighbors")
    if one < 1:
        errors.append("no rejected dot has exactly one rectangle neighbor")
    if zero < 1:
        errors.append("no isolated rejected dot")
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "rect_color": rect_color,
        "dot_color": dot_color,
        "n_absorb": absorb,
        "n_reject": reject,
        "one_neighbor_rejects": one,
        "isolated_rejects": zero,
        "opposite_two_neighbors": opposite_two,
    }, errors


def self_check(grid, *, difficulty=None, meta=None):
    _stats, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    stats, errors = _analyze(grid)
    if errors or stats is None:
        raise ValueError(f"grid is outside the generator contract: {errors}")
    pair = (stats["rect_color"], stats["dot_color"])
    try:
        palette_id = _PALETTES.index(pair)
    except ValueError as exc:
        raise ValueError(f"unrecognized generated palette {pair}") from exc
    return {
        "grid_h": stats["grid_h"],
        "grid_w": stats["grid_w"],
        "n_absorb": stats["n_absorb"],
        "n_reject": stats["n_reject"],
        "palette_id": palette_id,
    }


def _roles(grid):
    stats, errors = _analyze(grid)
    if errors or stats is None:
        raise ValueError(f"invalid task input: {errors}")
    return stats["rect_color"], stats["dot_color"]


def _corner_or_dense_only(grid):
    """Rival: absorb dense holes and perpendicular corner notches, not bridges."""
    rect_color, dot_color = _roles(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != dot_color:
                continue
            directions = _adjacent_directions(grid, r, c, rect_color)
            keep = len(directions) >= 3 or (
                len(directions) == 2 and frozenset(directions) not in _OPPOSITE
            )
            out[r][c] = rect_color if keep else 0
    return out


def _has_opposite_two_neighbors(grid):
    stats, errors = _analyze(grid)
    return not errors and bool(stats and stats["opposite_two_neighbors"])


SEMANTIC_WITNESSES = {"opposite_two_neighbors": _has_opposite_two_neighbors}
SEMANTIC_RIVALS = {"corner_or_dense_only": _corner_or_dense_only}
WITNESS_RIVALS = {"opposite_two_neighbors": ["corner_or_dense_only"]}
CANONICAL_SHORTCUTS = {"corner_or_dense_only": _corner_or_dense_only}
LESSON_COMPETITORS = {"corner_or_dense_only": _corner_or_dense_only}
