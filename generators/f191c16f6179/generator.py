"""Inputs for the canonical diagonal-bridge rule; labels remain Racket-derived.

The three-draw curriculum alternates a compact example with two guard examples.
All exact controls are recovered from pixels, including inactive paired colors.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f191c16f6179"
TASK_ID = "f191c16f6179"
VERSION = "3.0.0"
RULE_HASH = "f7b2de2c3ed0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Fill initially empty 45-degree gaps for colors occurring exactly twice. "
    "Read eligibility from the original input; later colors in input reading "
    "order win at crossings. A three-draw schedule supplies one compact example "
    "and two examples teaching non-diagonal, blocker, cardinality and order guards."
)
INVARIANTS = [
    "rectangular integer grid with background 0 and colors 1..9",
    "at least one exactly-two color has a clear diagonal gap of span at least 2",
    "non-diagonal, blocked, singleton and three-occurrence distractors are lawful",
    "eligibility uses the original input, including at crossing diagonals",
]
AXES = {
    "grid_h": {"type": "int", "default": "schedule: 7..16", "valid": "5..16"},
    "grid_w": {"type": "int", "default": "schedule: 7..16", "valid": "5..16"},
    "pairs": {"type": "int", "default": "core 2..3; guard 4..5", "valid": "1..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("core", "guard_ascending", "guard_descending")
_CONTROL_BOUNDS = {"grid_h": (5, 16), "grid_w": (5, 16), "pairs": (1, 5)}
_LAYOUT_ATTEMPTS = 24


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the default curriculum position, independently of difficulty."""
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


class _Path(NamedTuple):
    cells: tuple[int, ...]
    mask: int
    ends: int
    inner: int
    slope: int


def _mask(cells):
    result = 0
    for cell in cells:
        result |= 1 << cell
    return result


def _path(cells, slope=0):
    cells = tuple(cells)
    return _Path(cells, _mask(cells), _mask((cells[0], cells[-1])),
                 _mask(cells[1:-1]), slope)


@lru_cache(maxsize=144)
def _diagonal_geometry(h, w):
    """Immutable, exhaustive span>=2 geometry; no RNG or mutable grids cached."""
    return tuple(
        _path(((r + k) * w + c + (k if slope == 1 else span - k)
               for k in range(span + 1)), slope)
        for span in range(2, min(h, w))
        for r in range(h - span)
        for c in range(w - span)
        for slope in (1, -1)
    )


def _straight_cells(a, b, w):
    """Bresenham segment used by the deliberately overgeneralized rival."""
    r, c = divmod(a, w)
    r1, c1 = divmod(b, w)
    dr, dc = abs(r1 - r), abs(c1 - c)
    sr, sc = (1 if r < r1 else -1), (1 if c < c1 else -1)
    error = dr - dc
    cells = []
    while True:
        cells.append(r * w + c)
        if (r, c) == (r1, c1):
            return tuple(cells)
        twice = 2 * error
        if twice > -dc:
            error -= dc
            r += sr
        if twice < dr:
            error += dr
            c += sc


def _non_diagonal(a, b, w):
    r0, c0 = divmod(a, w)
    r1, c1 = divmod(b, w)
    return abs(r1 - r0) != abs(c1 - c0) and max(abs(r1 - r0), abs(c1 - c0)) >= 2


def _off_diagonal_pair(h, w, occupied, protected, active_inner, rng):
    """Find a clear non-diagonal gap with an observable unpainted gap pixel."""
    free = [p for p in range(h * w) if not (1 << p) & (occupied | protected)]
    if len(free) < 2:
        return None
    # Random proposals are bounded. The caller has a verified geometric fallback.
    for _ in range(96):
        a, b = sorted(rng.sample(free, 2))
        if not _non_diagonal(a, b, w):
            continue
        candidate = _path(_straight_cells(a, b, w))
        if not candidate.inner & occupied and candidate.inner & ~active_inner:
            return candidate
    return None


def _inactive_pair(free, w, rng):
    """An extra paired color, without turning a protected gap into a blocker."""
    free = list(free)
    rng.shuffle(free)
    for a, b in combinations(free, 2):
        r0, c0 = divmod(a, w)
        r1, c1 = divmod(b, w)
        if abs(r1 - r0) != abs(c1 - c0) or abs(r1 - r0) < 2:
            return (a, b)
    return None


def _core_layout(h, w, target, rng):
    paths = _diagonal_geometry(h, w)
    active_count = target - 1 if target == 3 else target
    for _ in range(_LAYOUT_ATTEMPTS):
        chosen, reserved = [], 0
        first_slope = rng.choice((-1, 1))
        for index in range(active_count):
            slope = first_slope if index == 0 else -first_slope if index == 1 else None
            available = [p for p in paths if not p.mask & reserved
                         and (slope is None or p.slope == slope)]
            if not available:
                break
            selected = rng.choice(available)
            chosen.append(selected)
            reserved |= selected.mask
        if len(chosen) != active_count:
            continue
        groups = [(p.cells[0], p.cells[-1]) for p in chosen]
        if target == 3:
            occupied = _mask(cell for group in groups for cell in group)
            extra = _off_diagonal_pair(h, w, occupied, reserved, reserved, rng)
            if extra is None:
                continue
            groups.append((extra.cells[0], extra.cells[-1]))
        return tuple(groups)
    return None


def _guard_layout(h, w, target, rng):
    paths = _diagonal_geometry(h, w)
    for _ in range(_LAYOUT_ATTEMPTS):
        first = rng.choice(paths)
        crossing = [p for p in paths if first.inner & p.inner
                    and not first.ends & p.mask and not p.ends & first.mask]
        if not crossing:
            continue
        second = rng.choice(crossing)
        occupied = first.ends | second.ends
        active_inner = first.inner | second.inner
        triples = [p for p in paths if not p.ends & (occupied | active_inner)
                   and not p.inner & occupied and p.inner & ~active_inner]
        for triple in rng.sample(triples, min(8, len(triples))):
            occupied2 = occupied | triple.ends
            protected = active_inner | triple.inner
            blocked = [p for p in paths if not p.ends & (occupied2 | protected)]
            for obstacle_path in rng.sample(blocked, min(16, len(blocked))):
                tr, tc = divmod(triple.cells[0], w)
                third_points = [p for p in obstacle_path.cells[1:-1]
                                if not (1 << p) & (occupied2 | protected)
                                and divmod(p, w)[1] - tc != triple.slope * (divmod(p, w)[0] - tr)]
                if not third_points:
                    continue
                third = rng.choice(third_points)
                occupied3 = occupied2 | obstacle_path.ends | (1 << third)
                offdiag = _off_diagonal_pair(h, w, occupied3, protected, active_inner, rng)
                if offdiag is None:
                    continue
                groups = [(first.cells[0], first.cells[-1]),
                          (second.cells[0], second.cells[-1]),
                          (obstacle_path.cells[0], obstacle_path.cells[-1]),
                          (offdiag.cells[0], offdiag.cells[-1])]
                if target == 5:
                    reserved = occupied3 | offdiag.mask | protected
                    extra_paths = [p for p in paths if not p.mask & reserved]
                    if extra_paths and rng.randrange(2):
                        extra = rng.choice(extra_paths)
                        extra_pair = (extra.cells[0], extra.cells[-1])
                    else:
                        extra_pair = _inactive_pair(
                            (p for p in range(h * w) if not (1 << p) & reserved), w, rng)
                    if extra_pair is None:
                        continue
                    groups.append(extra_pair)
                # The third occurrence is off the triple's entire infinite line.
                # It blocks another color; the triple's own gap remains empty.
                groups.append((triple.cells[0], triple.cells[-1], third))
                return tuple(groups)
    return None


_CORE_FALLBACK = (
    ((0, 3), (2, 1)), ((0, 0), (2, 2)), ((1, 4), (3, 2)),
    ((0, 2), (2, 4)), ((2, 0), (4, 2)),
)
_GUARD_FALLBACK = (
    ((0, 0), (2, 2)), ((0, 2), (2, 0)),  # crossing bridges
    ((0, 4), (4, 0)),                    # blocked by the triple's extra point
    ((1, 4), (3, 4)),                    # clear, non-diagonal pair
    ((0, 1), (0, 3)),                    # optional fifth pair
    ((1, 0), (3, 2), (1, 3)),            # clear diagonal plus off-line occurrence
)


def _fallback_layout(h, w, target, comprehensive, rng):
    """Proved 5x5 constructions, transformed and embedded in every allowed shape."""
    if comprehensive:
        groups = _GUARD_FALLBACK[:target] + (_GUARD_FALLBACK[-1],)
    elif target == 3:
        groups = _CORE_FALLBACK[:2] + (((3, 0), (3, 4)),)
    else:
        groups = _CORE_FALLBACK[:target]
    transpose, flip_r, flip_c = (rng.randrange(2) for _ in range(3))
    scale = rng.randint(1, (min(h, w) - 1) // 4)
    side = 4 * scale + 1
    top, left = rng.randrange(h - side + 1), rng.randrange(w - side + 1)

    def transform(point):
        r, c = point
        if transpose:
            r, c = c, r
        r, c = (4 - r if flip_r else r), (4 - c if flip_c else c)
        return (top + scale * r) * w + left + scale * c

    return tuple(tuple(transform(point) for point in group) for group in groups)


def _paint_input(h, w, groups, profile, rng):
    colors = rng.sample(range(1, 10), len(groups))
    if profile != "core":
        early, late = sorted((0, 1), key=lambda index: min(groups[index]))
        low, high = sorted(colors[:2])
        colors[early], colors[late] = (low, high) if profile == "guard_ascending" else (high, low)
    grid = full_grid(h, w, 0)
    for color, group in zip(colors, groups):
        for point in group:
            r, c = divmod(point, w)
            if grid[r][c]:
                raise RuntimeError("layout construction produced overlapping input endpoints")
            grid[r][c] = color
    return grid


def _draw_control(ctx, name, default_bounds):
    bounds = _CONTROL_BOUNDS[name] if ctx.overrides.get(name) is not None else default_bounds
    return ctx.draw_int_strict(name, *bounds)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return an input only; all three controls are exact in every difficulty."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError("unsupported override(s): " + ", ".join(sorted(unknown)))
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, excluding bool; None means unset")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "core":
        side = ctx.draw_choice("core_size", (7, 8, 9))
        default_shape = (side, side)
        default_pairs = (3, 3) if side == 9 else (2, 2)
    else:
        default_shape = {"easy": (8, 10), "hard": (11, 16)}.get(difficulty, (9, 12))
        default_pairs = (4, 5)
    h = _draw_control(ctx, "grid_h", default_shape)
    w = _draw_control(ctx, "grid_w", default_shape)
    target = _draw_control(ctx, "pairs", default_pairs)
    comprehensive = profile != "core" and target >= 4
    realized_profile = profile if comprehensive else "core"
    layout_rng = ctx.draw_rng("geometry")
    layout = (_guard_layout(h, w, target, layout_rng) if comprehensive
              else _core_layout(h, w, target, layout_rng))
    if layout is None:
        layout = _fallback_layout(h, w, target, comprehensive, ctx.draw_rng("fallback"))
    grid = _paint_input(h, w, layout, realized_profile, ctx.draw_rng("palette"))
    errors = _generated_errors(grid, target, realized_profile)
    if errors:
        # A bounded search may be conservative, but never return an underfilled
        # or semantically weakened draw. Check the fallback by the same gates.
        layout = _fallback_layout(h, w, target, comprehensive, ctx.draw_rng("fallback"))
        grid = _paint_input(h, w, layout, realized_profile, ctx.draw_rng("palette"))
        errors = _generated_errors(grid, target, realized_profile)
    if errors:
        raise RuntimeError("verified placement failed: " + "; ".join(errors))
    return grid


def _positions(grid):
    """Insertion order is the first occurrence in row-major input reading order."""
    found = {}
    w = len(grid[0])
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                found.setdefault(color, []).append(r * w + c)
    return found


def _diagonal_pair(cells, w):
    if len(cells) != 2:
        return None
    a, b = sorted(cells)
    r0, c0 = divmod(a, w)
    r1, c1 = divmod(b, w)
    if abs(r1 - r0) != abs(c1 - c0) or r1 - r0 < 2:
        return None
    slope = 1 if c1 > c0 else -1
    return _path(((r0 + k) * w + c0 + slope * k for k in range(r1 - r0 + 1)), slope)


def _eligible_paths(grid):
    w = len(grid[0])
    flat = tuple(value for row in grid for value in row)
    result = []
    for color, cells in _positions(grid).items():
        path = _diagonal_pair(cells, w)
        if path is not None and all(flat[p] == 0 for p in path.cells[1:-1]):
            result.append((color, path))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid rows must be nonempty sequences"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer digits 0..9, excluding bool"]
    errors = []
    if not 5 <= len(grid) <= 16 or not 5 <= len(grid[0]) <= 16:
        errors.append("grid dimensions must be in 5..16")
    if any(len(cells) > 3 for cells in _positions(grid).values()):
        errors.append("endpoint-domain colors may have one, two or three occurrences")
    if not _eligible_paths(grid):
        errors.append("expected at least one exactly-two color with a clear diagonal gap")
    return errors


def strict_canonical_like(grid):
    """Accept the canonical endpoint domain and its explicit lawful guard cases."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "pairs": sum(len(cells) == 2 for cells in _positions(grid).values())}


def _rival_prediction(grid, *, slope=None, non_diagonal=False, ignore_blockers=False,
                      ignore_count=False, progressive=False, numeric_order=None):
    """Pure alternative predictors for counterexample tests, never label authority."""
    w = len(grid[0])
    original = [value for row in grid for value in row]
    output = original[:]
    groups = _positions(grid)
    order = list(groups)
    if numeric_order is not None:
        order.sort(reverse=numeric_order == "descending")
    for color in order:
        cells = groups[color]
        candidates = combinations(cells, 2) if ignore_count else [cells]
        for pair in candidates:
            path = _diagonal_pair(pair, w)
            if path is None and non_diagonal and len(pair) == 2:
                a, b = sorted(pair)
                if _non_diagonal(a, b, w):
                    path = _path(_straight_cells(a, b, w))
            if path is None or (slope is not None and path.slope != slope):
                continue
            inspection = output if progressive else original
            if not ignore_blockers and any(inspection[p] for p in path.cells[1:-1]):
                continue
            for p in path.cells:
                output[p] = color
    return [output[r * w:(r + 1) * w] for r in range(len(grid))]


def _identity(grid):
    return [list(row) for row in grid]


def _only_falling(grid):
    return _rival_prediction(grid, slope=1)


def _only_rising(grid):
    return _rival_prediction(grid, slope=-1)


def _connect_non_diagonal(grid):
    return _rival_prediction(grid, non_diagonal=True)


def _ignore_blockers(grid):
    return _rival_prediction(grid, ignore_blockers=True)


def _ignore_exact_two(grid):
    return _rival_prediction(grid, ignore_count=True)


def _painted_eligibility(grid):
    return _rival_prediction(grid, progressive=True)


def _numeric_ascending(grid):
    return _rival_prediction(grid, numeric_order="ascending")


def _numeric_descending(grid):
    return _rival_prediction(grid, numeric_order="descending")


SEMANTIC_RIVALS = {
    "identity": _identity,
    "falling_only": _only_falling,
    "rising_only": _only_rising,
    "connect_non_diagonal": _connect_non_diagonal,
    "ignore_blockers": _ignore_blockers,
    "ignore_exact_two": _ignore_exact_two,
    "painted_eligibility": _painted_eligibility,
    "numeric_ascending": _numeric_ascending,
    "numeric_descending": _numeric_descending,
}


def _refutes(grid, rival):
    """Check a rival against actual final input-gap owners, not object presence.

    This structural calculation only verifies witness claims. Dataset outputs
    and lesson labels are supplied by the unchanged Racket authority.
    """
    w = len(grid[0])
    owners = {}
    for color, path in _eligible_paths(grid):
        for p in path.cells[1:-1]:
            owners[p] = color
    prediction = SEMANTIC_RIVALS[rival](grid)
    return any(prediction[r][c] != owners.get(r * w + c, value)
               for r, row in enumerate(grid) for c, value in enumerate(row))


def _active_witness(grid):
    return bool(_eligible_paths(grid)) and _refutes(grid, "identity")


def _rising_witness(grid):
    return any(path.slope == -1 for _, path in _eligible_paths(grid)) and _refutes(grid, "falling_only")


def _falling_witness(grid):
    return any(path.slope == 1 for _, path in _eligible_paths(grid)) and _refutes(grid, "rising_only")


def _off_diagonal_witness(grid):
    w = len(grid[0])
    return (any(len(cells) == 2 and _non_diagonal(*cells, w)
                for cells in _positions(grid).values())
            and _refutes(grid, "connect_non_diagonal"))


def _blocker_witness(grid):
    w = len(grid[0])
    flat = [value for row in grid for value in row]
    return (any(path is not None and any(flat[p] for p in path.cells[1:-1])
                for cells in _positions(grid).values()
                for path in [_diagonal_pair(cells, w)])
            and _refutes(grid, "ignore_blockers"))


def _exact_two_witness(grid):
    w = len(grid[0])
    flat = [value for row in grid for value in row]
    for cells in _positions(grid).values():
        if len(cells) != 3:
            continue
        for pair in combinations(cells, 2):
            path = _diagonal_pair(pair, w)
            if path is None or any(flat[p] for p in path.cells[1:-1]):
                continue
            other = next(p for p in cells if p not in pair)
            r0, c0 = divmod(path.cells[0], w)
            r1, c1 = divmod(other, w)
            if c1 - c0 != path.slope * (r1 - r0) and _refutes(grid, "ignore_exact_two"):
                return True
    return False


def _crossing_witness(grid):
    paths = _eligible_paths(grid)
    return (any(a.inner & b.inner for (_, a), (_, b) in combinations(paths, 2))
            and _refutes(grid, "painted_eligibility"))


def _ascending_order_witness(grid):
    return _crossing_witness(grid) and _refutes(grid, "numeric_ascending")


def _descending_order_witness(grid):
    return _crossing_witness(grid) and _refutes(grid, "numeric_descending")


SEMANTIC_WITNESSES = {
    "active_bridge": _active_witness,
    "rising_bridge": _rising_witness,
    "falling_bridge": _falling_witness,
    "non_diagonal_guard": _off_diagonal_witness,
    "blocker_guard": _blocker_witness,
    "exact_two_guard": _exact_two_witness,
    "crossing_input_guard": _crossing_witness,
    "reading_not_numeric_ascending": _ascending_order_witness,
    "reading_not_numeric_descending": _descending_order_witness,
}
WITNESS_RIVALS = {
    "active_bridge": ["identity"],
    "rising_bridge": ["falling_only"],
    "falling_bridge": ["rising_only"],
    "non_diagonal_guard": ["connect_non_diagonal"],
    "blocker_guard": ["ignore_blockers"],
    "exact_two_guard": ["ignore_exact_two"],
    "crossing_input_guard": ["painted_eligibility"],
    "reading_not_numeric_ascending": ["numeric_ascending"],
    "reading_not_numeric_descending": ["numeric_descending"],
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("ignore_blockers", "ignore_exact_two", "painted_eligibility",
                 "numeric_ascending", "numeric_descending")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Check supplied Racket-labeled pairs against this finite declared rival set."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


def _generated_errors(grid, target, profile):
    errors = self_check(grid)
    if observe_overrides(grid)["pairs"] != target:
        errors.append("realized paired-color count differs from requested pairs")
    if profile != "core":
        required = ["non_diagonal_guard", "blocker_guard", "exact_two_guard", "crossing_input_guard",
                    "reading_not_numeric_descending" if profile == "guard_ascending"
                    else "reading_not_numeric_ascending"]
        errors.extend(f"missing meaningful {name}" for name in required
                      if not SEMANTIC_WITNESSES[name](grid))
    return errors
