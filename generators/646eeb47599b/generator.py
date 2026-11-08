"""Fixed-color laser inputs for 6bcdb01e / 646eeb47599b.

Two green seed cells set the initial axis. Cyan walls split a beam at the
last open cell; touching cyan cells are ordinary walls too. Orange becomes
green. The unchanged canonical Racket rule remains the label authority.
"""
from __future__ import annotations

from functools import partial
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "646eeb47599b"
VERSION = "4.1.1"
RULE_HASH = "610c94f513d9"
SUMMARY = (
    "5..8 by 5..8 orange fields, exactly 4..14 cyan wall cells (which may "
    "touch), and an adjacent green seed. Unpinned production alternates two "
    "rich laser examples with one broad lawful draw. Rich examples distinguish "
    "nine declared rivals, including centerward-only launch and absorbing "
    "cyan clusters. Racket remains the label authority."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("teaching", "broad")
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
INVARIANTS = [
    "integer palette exactly {3, 7, 8}; task symbols are not permutable",
    "exactly two adjacent green seed cells in one row or column",
    "exactly the requested number of cyan cells; cyan cells may touch",
    "at least one orange cell is reachable, including immediate wall turns",
]
AXES = {
    "grid_h": {"type": "int", "default": "5..6 easy / 5..8 medium / 7..8 hard", "valid": "5..8"},
    "grid_w": {"type": "int", "default": "5..6 easy / 5..8 medium / 7..8 hard", "valid": "5..8"},
    "n_walls": {"type": "int", "default": "4..8 easy / 6..12 medium / 9..14 hard", "valid": "4..14"},
    "orientation": {"type": "str", "default": "rng", "valid": "horizontal|vertical"},
}


def _seed_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 3]


def _axis(grid):
    seeds = _seed_cells(grid)
    return seeds, len({r for r, _ in seeds}) == 1


def _laser_output(grid, *, launch="both", branch="both", max_splits=None):
    """Diagnostic/rival optics; independently checked against Racket.

    Read the original input throughout. Directed cells are states: merely
    marking a cell visited would lose crossing beams. Never used as labels.
    """
    h, w = len(grid), len(grid[0])
    seeds, horizontal = _axis(grid)
    out = [list(row) for row in grid]
    if not seeds:
        return out
    dirs = ((0, 1), (0, -1)) if horizontal else ((1, 0), (-1, 0))
    positions = [c if horizontal else r for r, c in seeds]
    length = w if horizontal else h
    if launch == "axis_edge" and min(positions) != 0 and max(positions) != length - 1:
        return out
    if launch == "centerward":
        positive = min(positions) + max(positions) <= length - 1
        dirs = (dirs[0] if positive else dirs[1],)
    stack = [(r, c, dr, dc, 0) for r, c in seeds for dr, dc in dirs]
    visited = set()

    def open_cell(r, c):
        return 0 <= r < h and 0 <= c < w and grid[r][c] != 8

    while stack:
        r, c, dr, dc, splits = stack.pop()
        state = (r, c, dr, dc, splits if max_splits is not None else 0)
        if state in visited:
            continue
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w):
            continue
        if grid[nr][nc] != 8:
            if grid[nr][nc] == 7:
                out[nr][nc] = 3
            stack.append((nr, nc, dr, dc, splits))
            continue
        if branch == "absorb" or (max_splits is not None and splits >= max_splits):
            continue
        if branch == "cluster_absorb" and any(
            0 <= nr + rr < h and 0 <= nc + cc < w and grid[nr + rr][nc + cc] == 8
            for rr, cc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            continue
        clockwise, counterclockwise = (dc, -dr), (-dc, dr)
        turns = [d for d in (clockwise, counterclockwise) if open_cell(r + d[0], c + d[1])]
        if branch == "two_exits" and len(turns) != 2:
            continue
        if branch == "clockwise":
            turns = [d for d in turns if d == clockwise]
        elif branch == "counterclockwise":
            turns = [d for d in turns if d == counterclockwise]
        stack.extend((r, c, rr, cc, splits + 1) for rr, cc in turns)
    return out


def _centerward_only(grid):
    return _laser_output(grid, launch="centerward")


def _axis_edge_only(grid):
    return _laser_output(grid, launch="axis_edge")


def _cluster_absorbs(grid):
    return _laser_output(grid, branch="cluster_absorb")


def _straight_only(grid):
    return _laser_output(grid, branch="absorb")


def _one_split(grid):
    return _laser_output(grid, max_splits=1)


def _clockwise_only(grid):
    return _laser_output(grid, branch="clockwise")


def _counterclockwise_only(grid):
    return _laser_output(grid, branch="counterclockwise")


def _both_exits_only(grid):
    return _laser_output(grid, branch="two_exits")


def _first_input_component_only(grid):
    """Rival: retain laser changes only in the first input component.

    For this rule all changed cells were orange, so their nearest input
    component is their own orange component. This independently implements
    the three generic first-object attribution mutations on our task domain.
    """
    out = _laser_output(grid)
    if grid[0][0] != 7:
        return [list(row) for row in grid]
    component, pending = {(0, 0)}, [(0, 0)]
    while pending:
        r, c = pending.pop()
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= rr < len(grid) and 0 <= cc < len(grid[0])
                    and grid[rr][cc] == 7 and (rr, cc) not in component):
                component.add((rr, cc))
                pending.append((rr, cc))
    return [[out[r][c] if (r, c) in component else value
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


SEMANTIC_RIVALS = {
    "centerward_only": _centerward_only,
    "axis_edge_only": _axis_edge_only,
    "cluster_absorbs": _cluster_absorbs,
    "straight_only": _straight_only,
    "one_split": _one_split,
    "clockwise_only": _clockwise_only,
    "counterclockwise_only": _counterclockwise_only,
    "both_exits_only": _both_exits_only,
    "first_input_component_only": _first_input_component_only,
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in (
    "centerward_only", "axis_edge_only", "cluster_absorbs",
)}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, *, rival):
    return _laser_output(grid) != SEMANTIC_RIVALS[rival](grid)


SEMANTIC_WITNESSES = {name: partial(_refutes, rival=name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def schedule_profile(seed, sample_index, difficulty=None):
    """Two rich draws, then a broad draw; unpinned production only."""
    return "broad" if sample_index % LESSON_SCHEDULE_PERIOD == 2 else "teaching"


def _int_axis(ctx, name, global_bounds, preferred_bounds):
    # Difficulty changes default preferences, never the legal exact domain.
    bounds = global_bounds if ctx.overrides.get(name) is not None else preferred_bounds
    return ctx.draw_int_strict(name, *bounds)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    size_bounds = (5, 6) if difficulty == "easy" else ((7, 8) if difficulty == "hard" else (5, 8))
    wall_bounds = (4, 8) if difficulty == "easy" else ((9, 14) if difficulty == "hard" else (6, 12))
    h = _int_axis(ctx, "grid_h", (5, 8), size_bounds)
    w = _int_axis(ctx, "grid_w", (5, 8), size_bounds)
    n_walls = _int_axis(ctx, "n_walls", (4, 14), wall_bounds)
    horizontal = ctx.draw_choice("orientation", ("horizontal", "vertical")) == "horizontal"
    # Pins request individual lawful grids; lesson guarantees apply to defaults.
    pinned = any(value is not None for value in overrides.values())
    rich = not pinned and schedule_profile(seed, sample_index, difficulty) == "teaching"
    rng = ctx.draw_rng("layout")
    for _ in range(8192):
        if horizontal:
            r = rng.randint(1, h - 2) if rich else rng.randrange(h)
            c = rng.randint(1, w - 3) if rich else rng.randrange(w - 1)
            seeds = ((r, c), (r, c + 1))
        else:
            r = rng.randint(1, h - 3) if rich else rng.randrange(h - 1)
            c = rng.randint(1, w - 2) if rich else rng.randrange(w)
            seeds = ((r, c), (r + 1, c))
        grid = full_grid(h, w, 7)
        for r, c in seeds:
            grid[r][c] = 3
        available = [(r, c) for r in range(h) for c in range(w) if (r, c) not in seeds]
        for r, c in rng.sample(available, n_walls):
            grid[r][c] = 8
        target = _laser_output(grid)
        if target == grid:
            continue
        if rich and any(rival(grid) == target for rival in SEMANTIC_RIVALS.values()):
            continue
        return grid
    raise RuntimeError("No qualifying laser layout in 8192 deterministic candidates; no fallback label or shortened count emitted")


def observe_overrides(grid):
    """Recover exact controls from returned pixels, not RNG bookkeeping."""
    seeds, horizontal = _axis(grid)
    if len(seeds) != 2:
        raise ValueError("expected two green seed cells")
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "n_walls": sum(value == 8 for row in grid for value in row),
        "orientation": "horizontal" if horizontal else "vertical",
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or v not in (3, 7, 8) for row in grid for v in row):
        return ["cells must be integer task colors 3, 7, 8"]
    errors = []
    if not (5 <= h <= 8 and 5 <= w <= 8):
        errors.append(f"expected 5..8 rows and columns, got {h}x{w}")
    seeds = _seed_cells(grid)
    if len(seeds) != 2:
        return errors + [f"expected two green seed cells, found {len(seeds)}"]
    if sum(abs(seeds[0][a] - seeds[1][a]) for a in (0, 1)) != 1:
        return errors + ["seed cells must be adjacent in a row or column"]
    count = sum(v == 8 for row in grid for v in row)
    if not 4 <= count <= 14:
        errors.append(f"expected 4..14 cyan wall cells, found {count}")
    if not any(v == 7 for row in grid for v in row):
        errors.append("no orange field")
    # Immediate cyan collisions can turn at a seed and still change the grid.
    if _laser_output(grid) == [list(row) for row in grid]:
        errors.append("no orange cell is reachable by the laser")
    return errors


def strict_canonical_like(grid):
    """Declared task manifold, including immediate turns and cyan clusters."""
    return self_check(grid)


def lesson_identifiable(demos, query):
    """Ambiguity against declared competitors; not a uniqueness proof."""
    return [name + " fits the demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
