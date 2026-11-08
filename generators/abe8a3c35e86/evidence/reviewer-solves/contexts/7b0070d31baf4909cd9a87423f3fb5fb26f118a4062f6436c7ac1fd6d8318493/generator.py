"""Constructive sampler for the color-9 hinge-reflection task.

The selected canonical rule gives *column-side geometry priority*: if the
motif is wholly left or right of the 9 pivot, copy it across the pivot column.
Only when that condition is false does an above/below motif copy across the
pivot row.  The sampler deliberately includes quadrant cases where both tests
are true, because those are counterexamples to the plausible row-priority
shortcut left unresolved by the three canonical examples.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "abe8a3c35e86"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "eb5d6fb489a0"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A unique color-9 pivot copies one connected monochrome motif across the "
    "pivot column when the motif is wholly left/right; otherwise it copies "
    "an above/below motif across the pivot row. Column priority is exercised "
    "explicitly when both conditions hold."
)

INVARIANTS = [
    "7..14 by 7..14 integer grid with background 0",
    "exactly one color-9 pivot",
    "one 4-connected monochrome motif of 3..5 cells in color 1..8",
    "motif is wholly left/right of the pivot or, failing that, wholly above/below",
    "the selected reflection remains in bounds and lands only on background",
]

LAYOUTS = (
    "left", "right", "above", "below",
    "upper_left", "upper_right", "lower_left", "lower_right",
)
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 7 anchor or difficulty-weighted 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "scheduled 7 anchor or difficulty-weighted 7..14", "valid": "7..14"},
    "motif_size": {"type": "int", "default": "difficulty-weighted 3..5", "valid": "3..5"},
    "motif_color": {"type": "int", "default": "uniform 1..8", "valid": "1..8"},
    "layout": {"type": "str", "default": "ten-step teaching schedule", "valid": "|".join(LAYOUTS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Category pattern Q,R,C,Q,R repeats.  Therefore every five consecutive
# examples contain two quadrant/priority witnesses, two row-only cases, and one
# column-only case.  Holding out any one of the five leaves at least one of each
# decisive witness class.  The ten roles also cover every exact layout value.
_SCHEDULE_LAYOUTS = (
    "upper_left", "above", "left", "lower_right", "below",
    "upper_right", "below", "right", "lower_left", "above",
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE_LAYOUTS)))
_CANONICAL_SIZE_ROLES = frozenset({0, 2, 4, 6, 8})


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the public default-schedule role; explicit controls still win."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}
    for name, value in active.items():
        if name == "layout":
            if not isinstance(value, str):
                raise TypeError("layout override must be a string")
            if value not in LAYOUTS:
                raise ValueError(f"layout must be one of {LAYOUTS}")
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = {
            "grid_h": (7, 14),
            "grid_w": (7, 14),
            "motif_size": (3, 5),
            "motif_color": (1, 8),
        }[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    return active


def _weighted(values, preferred):
    values = tuple(values)
    # Keep every documented value in the draw domain in every difficulty band;
    # duplicates change only default frequency, never override legality.
    return values + tuple(v for v in preferred if v in values) * 5


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        r, c = frontier.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                frontier.append(point)
    return len(seen) == len(cells)


@lru_cache(maxsize=None)
def _base_shapes(family, size):
    """Connected offset sets for a left-side or upper-left motif.

    Side shapes include pivot-row offset 0, making the alternate row-side test
    false.  Quadrant shapes are strictly negative on both coordinates, making
    both canonical branch predicates true.
    """
    if family == "side":
        region = tuple((r, c) for r in range(-2, 3) for c in range(-3, 0))
        keep = lambda combo: any(r == 0 for r, _ in combo)
    elif family == "quadrant":
        region = tuple((r, c) for r in range(-3, 0) for c in range(-3, 0))
        keep = lambda combo: True
    else:  # pragma: no cover - internal misuse guard
        raise ValueError(f"unknown shape family {family!r}")
    shapes = tuple(
        tuple(sorted(combo))
        for combo in combinations(region, size)
        if keep(combo) and _connected(combo)
    )
    if not shapes:  # pragma: no cover - static domains are covered by tests
        raise RuntimeError(f"no {family} shapes of size {size}")
    return shapes


def _transform(base, layout):
    if layout == "left":
        return base
    if layout == "right":
        return tuple((r, -c) for r, c in base)
    if layout == "above":
        return tuple((c, r) for r, c in base)
    if layout == "below":
        return tuple((-c, r) for r, c in base)
    if layout == "upper_left":
        return base
    if layout == "upper_right":
        return tuple((r, -c) for r, c in base)
    if layout == "lower_left":
        return tuple((-r, c) for r, c in base)
    if layout == "lower_right":
        return tuple((-r, -c) for r, c in base)
    raise ValueError(f"unknown layout {layout!r}")


def _motif_offsets(ctx, layout, motif_size):
    family = "quadrant" if "_" in layout else "side"
    base = ctx.draw_rng("motif_shape").choice(_base_shapes(family, motif_size))
    return tuple(sorted(_transform(base, layout)))


def _uses_column_branch(layout):
    return layout in {
        "left", "right", "upper_left", "upper_right", "lower_left", "lower_right"
    }


def _reflected_offsets(offsets, layout):
    if _uses_column_branch(layout):
        return tuple((dr, -dc) for dr, dc in offsets)
    return tuple((-dr, dc) for dr, dc in offsets)


def _pivot_candidates(height, width, offsets, layout):
    occupied = tuple(offsets) + _reflected_offsets(offsets, layout)
    return tuple(
        (pr, pc)
        for pr in range(height)
        for pc in range(width)
        if all(0 <= pr + dr < height and 0 <= pc + dc < width
               for dr, dc in occupied)
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _controls(overrides)
    role = schedule_profile(seed, sample_index, difficulty)
    scheduled = {"layout": _SCHEDULE_LAYOUTS[role]}
    if role in _CANONICAL_SIZE_ROLES:
        scheduled.update({"grid_h": 7, "grid_w": 7})
    # Caller values have final precedence over curriculum defaults.
    effective = {**scheduled, **active}
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)

    preferred_dims = {
        "easy": (7, 8, 9),
        "medium": (8, 9, 10, 11, 12),
        "hard": (11, 12, 13, 14),
    }.get(difficulty, (7, 8, 9, 10, 11))
    preferred_sizes = {
        "easy": (3,), "medium": (3, 4), "hard": (4, 5),
    }.get(difficulty, (3, 4, 5))

    height = ctx.draw_choice("grid_h", _weighted(range(7, 15), preferred_dims))
    width = ctx.draw_choice("grid_w", _weighted(range(7, 15), preferred_dims))
    motif_size = ctx.draw_choice("motif_size", _weighted(range(3, 6), preferred_sizes))
    motif_color = ctx.draw_choice("motif_color", tuple(range(1, 9)))
    layout = ctx.draw_choice("layout", LAYOUTS)

    offsets = _motif_offsets(ctx, layout, motif_size)
    candidates = _pivot_candidates(height, width, offsets, layout)
    if not candidates:  # all documented combinations are constructively feasible
        raise RuntimeError(
            f"no pivot fits {height}x{width}, size={motif_size}, layout={layout}"
        )
    pivot_r, pivot_c = ctx.draw_rng("pivot_position").choice(candidates)
    grid = full_grid(height, width, 0)
    grid[pivot_r][pivot_c] = 9
    for dr, dc in offsets:
        grid[pivot_r + dr][pivot_c + dc] = motif_color
    return grid


def _basic_grid_errors(grid):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not booleans)"]
    return []


def _parts(grid):
    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value == 9]
    motif = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 9)]
    return pivots, motif


def _sides(pivot, motif):
    pr, pc = pivot
    rows = [r for r, _ in motif]
    cols = [c for _, c in motif]
    column_side = "left" if max(cols) < pc else ("right" if min(cols) > pc else None)
    row_side = "above" if max(rows) < pr else ("below" if min(rows) > pr else None)
    return column_side, row_side


def _layout_name(pivot, motif):
    column_side, row_side = _sides(pivot, motif)
    if column_side and row_side:
        return f"{'upper' if row_side == 'above' else 'lower'}_{column_side}"
    return column_side or row_side


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    pivots, motif = _parts(grid)
    colors = {grid[r][c] for r, c in motif}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motif_size": len(motif),
        "motif_color": next(iter(colors)),
        "layout": _layout_name(pivots[0], motif),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    errors = []
    if not 7 <= height <= 14 or not 7 <= width <= 14:
        errors.append("grid dimensions must each be in 7..14")

    pivots, motif = _parts(grid)
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-9 pivot, found {len(pivots)}")
    if not 3 <= len(motif) <= 5:
        errors.append(f"expected a 3..5-cell motif, found {len(motif)}")
    colors = {grid[r][c] for r, c in motif}
    if len(colors) != 1 or (colors and next(iter(colors)) not in range(1, 9)):
        errors.append("motif must be monochrome in one color from 1..8")
    if motif and not _connected(motif):
        errors.append("motif must be 4-connected")

    if len(pivots) == 1 and motif:
        pivot = pivots[0]
        column_side, row_side = _sides(pivot, motif)
        if not column_side and not row_side:
            errors.append("motif must be wholly left/right or wholly above/below the pivot")
        else:
            pr, pc = pivot
            use_column = bool(column_side)  # exact canonical branch priority
            targets = [
                (r, 2 * pc - c) if use_column else (2 * pr - r, c)
                for r, c in motif
            ]
            if any(not (0 <= r < height and 0 <= c < width) for r, c in targets):
                errors.append("selected reflection would leave the grid")
            elif any(grid[r][c] != 0 for r, c in targets):
                errors.append("selected reflection must land on background")
    return errors


def strict_canonical_like(grid):
    """Lawful task inputs in this sampler's declared, connected motif manifold."""
    return self_check(grid)


def _copy(grid):
    return [list(row) for row in grid]


def _paint_reflection(grid, axis):
    pivots, motif = _parts(grid)
    if len(pivots) != 1:
        return _copy(grid)
    pr, pc = pivots[0]
    output = _copy(grid)
    for r, c in motif:
        rr, cc = ((r, 2 * pc - c) if axis == "column" else (2 * pr - r, c))
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            output[rr][cc] = grid[r][c]
    return output


def _geometry(grid):
    pivots, motif = _parts(grid)
    if len(pivots) != 1 or not motif:
        return None, None
    return _sides(pivots[0], motif)


def _row_priority_when_both(grid):
    """Plausible rival: above/below is checked before left/right."""
    column_side, row_side = _geometry(grid)
    if row_side:
        return _paint_reflection(grid, "row")
    if column_side:
        return _paint_reflection(grid, "column")
    return _copy(grid)


def _column_only(grid):
    column_side, _ = _geometry(grid)
    return _paint_reflection(grid, "column") if column_side else _copy(grid)


def _row_only(grid):
    _, row_side = _geometry(grid)
    return _paint_reflection(grid, "row") if row_side else _copy(grid)


def _identity(grid):
    return _copy(grid)


def _both_axes(grid):
    column_side, row_side = _geometry(grid)
    return bool(column_side and row_side)


def _row_branch(grid):
    column_side, row_side = _geometry(grid)
    return bool(row_side and not column_side)


def _column_branch(grid):
    column_side, _ = _geometry(grid)
    return bool(column_side)


SEMANTIC_WITNESSES = {
    "column_priority_when_both": _both_axes,
    "row_branch": _row_branch,
    "column_branch": _column_branch,
}
BRANCH_WITNESSES = ("row_branch", "column_branch")
SEMANTIC_RIVALS = {"row_priority_when_both": _row_priority_when_both}
WITNESS_RIVALS = {
    "column_priority_when_both": ["row_priority_when_both"],
}
CANONICAL_SHORTCUTS = {"row_priority_when_both": _row_priority_when_both}
LESSON_COMPETITORS = {
    "row_priority_when_both": _row_priority_when_both,
    "column_only": _column_only,
    "row_only": _row_only,
    "identity": _identity,
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; no claim of universal rule uniqueness."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(
                f"declared rival {name!r} fits every demonstration but changes the query"
            )
    return reasons
