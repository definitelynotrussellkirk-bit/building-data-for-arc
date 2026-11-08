"""Input sampler for simultaneous, red-only rectangle-corner completion.

The canonical Racket rule is the label authority. It can complete overlapping
rectangles sharing red rows/columns, never overwrites nonzero cells, and never
uses newly painted green corners as evidence. Diagnostic predictors below are
rivals/witness machinery, not generated labels.
"""
from __future__ import annotations
from collections import Counter
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ce99418cc163"
TASK_ID = "ce99418cc163"
RULE_HASH = "bc2eb2b8f3e7"
VERSION = "2.0.0"
SUMMARY = "Add green only at empty fourth corners supported by three original red corners, simultaneously."
INVARIANTS = [
    "0 is background, 2 is the only evidence color; all other cells are preserved",
    "red support is one L, two independent Ls, a shared-rail pair, or a five-edge chain",
    "shared rows/columns may induce more completions than the nominal number of rectangles",
    "at least one empty supported corner remains; occupied supported corners are never overwritten",
    "three consecutive default draws include a blocked chain distinguishing one pass from closure",
]
LAYOUTS = ("single", "separate", "shared", "chain")
SCHEDULE_PROFILES = ("teaching", "multi", "single")
AXES = {
    "grid_h": {"type": "int", "default": "4..20, favors 10", "valid": "4..20"},
    "grid_w": {"type": "int", "default": "4..20, favors 12", "valid": "4..20"},
    "layout": {"type": "str", "default": "three-slot curriculum", "valid": "|".join(LAYOUTS)},
    "n_blockers": {"type": "int", "default": "1 in teaching chain, otherwise 0", "valid": "0..1"},
    "n_distractors": {"type": "int", "default": "0..6, favors 3 and 4", "valid": "0..6"},
}
# Exact failures identify the actual incompatible axes on their exceptions.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"layout": "single", "n_blockers": 1},
    ("grid_h", "grid_w", "layout", "n_distractors"),
]


class IncompatibleOverrides(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def schedule_profile(seed, sample_index, difficulty=None):
    """Every cyclic three-draw window has one teaching grid, at any seed."""
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % 3]


def _red_cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}


def _supported_corners(red):
    """Geometric opportunities, ignoring occupancy; input construction only."""
    by_row = {}
    by_col = {}
    for r, c in sorted(red):
        by_row.setdefault(r, set()).add(c)
        by_col.setdefault(c, set()).add(r)
    result = set()
    for rr, cc in sorted(red):
        for r in sorted(by_col[cc] - {rr}):
            for c in sorted(by_row[rr] - {cc}):
                if (r, c) not in red:
                    result.add((r, c))
    return result


def _graph_components(red):
    remaining = set(red)
    components = []
    while remaining:
        first = min(remaining)
        component = {first}
        remaining.remove(first)
        frontier = [first]
        while frontier:
            r, c = frontier.pop()
            neighbours = {p for p in remaining if p[0] == r or p[1] == c}
            remaining.difference_update(neighbours)
            component.update(neighbours)
            frontier.extend(sorted(neighbours))
        components.append(component)
    return components


def _layout_of(red):
    rows, cols = Counter(r for r, _ in red), Counter(c for _, c in red)
    rd, cd = sorted(rows.values()), sorted(cols.values())
    components = _graph_components(red)
    if len(red) == 3 and rd == cd == [1, 2]:
        return "single"
    if len(red) == 5 and rd == cd == [1, 2, 2] and len(components) == 1:
        return "chain"
    if len(red) == 6 and len(components) == 2:
        if all(len(p) == 3 and len({r for r, _ in p}) == len({c for _, c in p}) == 2 for p in components):
            return "separate"
    if len(red) == 6 and len(components) == 1:
        if (rd == [1, 1, 2, 2] and cd == [1, 1, 4]) or (cd == [1, 1, 2, 2] and rd == [1, 1, 4]):
            return "shared"
    raise ValueError("red geometry is not a supported L / independent-pair / shared-rail / chain motif")


def _draw_size(ctx, name, anchor, difficulty):
    full = list(range(4, 21))
    favored = list(range(7, 11)) if difficulty == "easy" else list(range(11, 18)) if difficulty == "hard" else []
    # Both axes retain their complete domain in every band. No canonical grids
    # are replayed: only canvas dimensions have a canonical-density component.
    return ctx.draw_choice(name, full + favored + [anchor] * 90)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or retired override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "layout":
            if value not in LAYOUTS:
                raise ValueError(f"layout must be one of {LAYOUTS}")
        else:
            lo, hi = (4, 20) if name in ("grid_h", "grid_w") else (0, 1) if name == "n_blockers" else (0, 6)
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _motif(layout, rng):
    if layout == "single":
        points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        points.remove(rng.choice(points))
    elif layout == "separate":
        points = []
        for offset in (0, 2):
            corners = [(offset + r, offset + c) for r in range(2) for c in range(2)]
            corners.remove(rng.choice(corners))
            points.extend(corners)
    elif layout == "shared":
        points = [(0, 1), (1, 1), (1, 2), (2, 0), (2, 1), (3, 1)]
    else:
        points = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]
    if rng.choice((False, True)):
        points = [(c, r) for r, c in points]
    return points


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = _draw_size(ctx, "grid_h", 10, difficulty)
    w = _draw_size(ctx, "grid_w", 12, difficulty)
    profile = schedule_profile(seed, sample_index, difficulty)
    default_layout = "chain" if profile == "teaching" else "single" if profile == "single" else ctx.draw_rng("multi_kind").choice(("separate", "shared"))
    # The scheduled default is a one-option keyed draw. Explicit controls are
    # validated against the full domain above and replace that scheduled value.
    layout = ctx.draw_choice("layout", (overrides.get("layout") or default_layout,))
    default_blockers = int(layout == "chain")
    block_choice = overrides.get("n_blockers")
    blockers = ctx.draw_choice("n_blockers", (default_blockers if block_choice is None else block_choice,))
    if layout == "single" and blockers:
        raise IncompatibleOverrides("layout=single with n_blockers=1 hides its only completion", ("layout", "n_blockers"))
    rng = ctx.draw_rng("geometry")
    points = _motif(layout, rng)
    rows = rng.sample(range(h), 1 + max(r for r, _ in points))
    cols = rng.sample(range(w), 1 + max(c for _, c in points))
    red = {(rows[r], cols[c]) for r, c in points}
    supported = _supported_corners(red)
    grid = full_grid(h, w, 0)
    for r, c in sorted(red):
        grid[r][c] = 2
    color = ctx.draw_rng("distractor_color").choice((1, 4, 5, 6, 7, 8, 9))
    for r, c in ctx.draw_rng("blocked_corners").sample(sorted(supported), blockers):
        grid[r][c] = color
    # Reserve the chain's entire 3x3 support: ordinary distractors must not
    # accidentally occupy the cell which distinguishes one pass from closure.
    reserved = red | supported
    if layout == "chain":
        reserved |= {(r, c) for r in rows for c in cols}
    free = [(r, c) for r in range(h) for c in range(w) if (r, c) not in reserved]
    capacity = min(6, len(free))
    requested = overrides.get("n_distractors")
    if requested is not None and requested > capacity:
        raise IncompatibleOverrides("n_distractors exceeds free cells for grid_h/grid_w/layout", ("grid_h", "grid_w", "layout", "n_distractors"))
    options = list(range(capacity + 1)) + [v for v in (3, 4) for _ in range(12) if v <= capacity]
    count = ctx.draw_choice("n_distractors", options)
    for r, c in ctx.draw_rng("noise_positions").sample(free, count):
        grid[r][c] = color
    return grid


def observe_overrides(grid):
    red = _red_cells(grid)
    supported = _supported_corners(red)
    noise = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 2)}
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "layout": _layout_of(red),
            "n_blockers": len(noise & supported), "n_distractors": len(noise - supported)}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9 (not bool/float)"]
    if not (4 <= h <= 20 and 4 <= w <= 20):
        return ["canvas dimensions must be 4..20"]
    try:
        observed = observe_overrides(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if observed["n_blockers"] > 1 or observed["n_distractors"] > 6:
        errors.append("too many blockers or distractors for the declared manifold")
    if not any(grid[r][c] == 0 for r, c in _supported_corners(_red_cells(grid))):
        errors.append("no empty supported corner: identity/underdetermined instance")
    return errors


def strict_canonical_like(grid):
    """Task-local grammar, not merely canvas/palette similarity."""
    return self_check(grid)


def _diagnostic_one_pass(grid):
    """Diagnostic prediction only; Racket remains the output-label authority."""
    out = [list(row) for row in grid]
    for r, c in _supported_corners(_red_cells(grid)):
        if grid[r][c] == 0:
            out[r][c] = 3
    return out


def _overwrite_occupied(grid):
    """Rival: incorrectly replace a non-red occupied fourth corner."""
    out = [list(row) for row in grid]
    for r, c in _supported_corners(_red_cells(grid)):
        out[r][c] = 3
    return out


def _cascade_new_corners(grid):
    """Rival: use newly painted corners as red evidence until stable."""
    out = [list(row) for row in grid]
    active = _red_cells(grid)
    while True:
        new = {p for p in _supported_corners(active) if out[p[0]][p[1]] == 0}
        if not new:
            return out
        for r, c in new:
            out[r][c] = 3
        active.update(new)


def _has_blocked_corner(grid):
    return any(grid[r][c] not in (0, 2, 3) for r, c in _supported_corners(_red_cells(grid)))


def _has_cascade_gap(grid):
    return _cascade_new_corners(grid) != _diagnostic_one_pass(grid)


SEMANTIC_WITNESSES = {"occupied_corner": _has_blocked_corner, "non_cascading": _has_cascade_gap}
SEMANTIC_RIVALS = {"overwrite_occupied": _overwrite_occupied, "cascade_new_corners": _cascade_new_corners}
WITNESS_RIVALS = {"occupied_corner": ["overwrite_occupied"], "non_cascading": ["cascade_new_corners"]}
CANONICAL_SHORTCUTS = {"overwrite_occupied": _overwrite_occupied, "cascade_new_corners": _cascade_new_corners}
LESSON_COMPETITORS = {"overwrite_occupied": _overwrite_occupied, "cascade_new_corners": _cascade_new_corners}
