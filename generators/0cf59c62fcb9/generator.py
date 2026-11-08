"""Generator for arc_puzzle_bank_twentieth_21_bundle:hard_136_fill_chambers_by_nearest_seed_with_tie_break.

Color 8 forms walls.  Within each chamber, colored seeds determine the
nearest-seed fill under the canonical shortest-path rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0cf59c62fcb9"
VERSION = "1.2.1"  # diversity: wider grids + interior wall obstacles (exercise geodesic detour) + more seeds (was straight dividers only -> geodesic==manhattan)
TASK_ID = "0cf59c62fcb9"

SUMMARY = (
    "8-wall-bounded grid split into chambers by straight dividers, PLUS "
    "scattered interior 8-wall obstacles inside chambers (so the rule's "
    "geodesic BFS must DETOUR around them, not just Manhattan-fill). Each "
    "chamber holds 1..4 colored seeds. Rule: within each chamber every "
    "open cell takes the color of the geodesically-nearest seed (ties → "
    "smaller color value). Grid size, divider layout, obstacle count and "
    "seed count/positions all vary."
)

INVARIANTS = [
    "walls are color 8",
    "open chamber cells are 0 or seed colors",
    "each chamber contains at least one colored seed",
    "interior obstacles never isolate a seed-free pocket from its seed",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng 7..11", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "layout": {"type": "choice", "default": "rng vertical|horizontal|cross"},
    "n_obstacles": {"type": "int", "default": "rng 0..4 per chamber", "valid": "0..6"},
}


def _room_cells(r1, c1, r2, c2):
    return [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def _connected_count(open_set):
    """Size of the connected component reachable from any one open cell."""
    if not open_set:
        return 0
    start = next(iter(open_set))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (r + dr, c + dc)
            if n in open_set and n not in seen:
                seen.add(n)
                stack.append(n)
    return len(seen)


def _add_obstacles(grid, cells, rng, n_obstacles):
    """Drop up to n_obstacles 8-walls inside the chamber, keeping the
    remaining open cells a single connected region (so no cell is cut off
    from every seed)."""
    open_set = set(cells)
    placed = 0
    attempts = 0
    while placed < n_obstacles and attempts < 40 and len(open_set) > 3:
        attempts += 1
        r, c = rng.choice(list(open_set))
        cand = open_set - {(r, c)}
        if _connected_count(cand) == len(cand):  # stays fully connected
            grid[r][c] = 8
            open_set = cand
            placed += 1
    return sorted(open_set)


def _seed_room(grid, cells, rng, colors):
    if len(cells) < 2:
        return
    count = min(len(cells) - 1, rng.randint(1, 4))
    positions = rng.sample(cells, count)
    seed_colors = rng.sample(colors, count)
    for (r, c), color in zip(positions, seed_colors):
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 15)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 9, 13)
    rng = ctx.draw_rng("layout_rng")

    requested = overrides.get("layout")
    if requested is not None:
        if requested not in {"vertical", "horizontal", "cross"}:
            raise ValueError("layout override must be vertical, horizontal, or cross")
        layout = requested
    else:
        layout = rng.choice(["vertical", "horizontal", "cross"])

    grid = full_grid(h, w, 8)
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            grid[r][c] = 0

    rooms = [(1, 1, h - 2, w - 2)]
    if layout == "vertical":
        wall_c = rng.randint(3, w - 4)
        for r in range(1, h - 1):
            grid[r][wall_c] = 8
        rooms = [(1, 1, h - 2, wall_c - 1), (1, wall_c + 1, h - 2, w - 2)]
    elif layout == "horizontal":
        wall_r = rng.randint(3, h - 4) if h >= 8 else 3
        for c in range(1, w - 1):
            grid[wall_r][c] = 8
        rooms = [(1, 1, wall_r - 1, w - 2), (wall_r + 1, 1, h - 2, w - 2)]
    else:
        wall_r = rng.randint(3, h - 4) if h >= 8 else 3
        wall_c = rng.randint(3, w - 4)
        for c in range(1, w - 1):
            grid[wall_r][c] = 8
        for r in range(1, h - 1):
            grid[r][wall_c] = 8
        rooms = [
            (1, 1, wall_r - 1, wall_c - 1),
            (1, wall_c + 1, wall_r - 1, w - 2),
            (wall_r + 1, 1, h - 2, wall_c - 1),
            (wall_r + 1, wall_c + 1, h - 2, w - 2),
        ]

    colors = [2, 3, 4, 5, 6, 7, 9]
    for box in rooms:
        cells = _room_cells(*box)
        n_obstacles = rng.randint(0, min(4, max(0, len(cells) - 4)))
        open_cells = _add_obstacles(grid, cells, rng, n_obstacles)
        _seed_room(grid, open_cells, rng, colors)

    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 color-8 wall cell; >=1 seed cell (non-0 non-8) in
    the open region; >=1 open (0) cell for the rule to fill."""
    msgs = []
    h, w = len(grid), len(grid[0])
    has_wall = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    if not has_wall:
        msgs.append("no color-8 wall cell — chamber structure missing")
    seeds = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 8)]
    if not seeds:
        msgs.append("no seed cell (non-0 non-8) — rule has nothing to propagate")
    open_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    if not open_cells:
        msgs.append("no open (0) cell — rule has nothing to fill")
    return msgs
