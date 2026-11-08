"""Generator for 2c420f77c907 — unavoidable-cells-on-shortest-paths.

Rule (from canonical Racket):
  Grid is a maze: 5 = wall, 0 = open passage, 2 = start, 3 = goal.
  BFS from start computes distance + path-count to every cell.
  BFS from goal computes distance + path-count back.
  A cell (r, c) with value 0 is UNAVOIDABLE iff
    dist_start(c) + dist_goal(c) == total_dist(start→goal)
    AND  paths_start(c) * paths_goal(c) == total_paths(start→goal).
  Output: unavoidable 0-cells become 8; everything else stays unchanged.
  (Cells on ALL shortest paths from 2 to 3 get marked 8;
  cells with branching alternatives stay 0.)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c420f77c907"
VERSION = "2.1.1"  # palette intrinsic (role-fixed 5/2/3/8); widened maze size + ring count (n_rings up to 3) for more bottleneck structure. distinct 96->100.
TASK_ID = "2c420f77c907"
SUMMARY = (
    "Maze grid (walls=5, open=0, start=2, goal=3) with ONE start "
    "cell and ONE goal cell. Path consists of: (a) a straight "
    "corridor segment from start, (b) one or more rectangular ring "
    "bypasses that branch into 2 equal-length paths, (c) a straight "
    "corridor segment to goal. Rule: BFS from start and from goal "
    "to count shortest-path distance and path multiplicity for "
    "every open cell. A 0-cell is UNAVOIDABLE iff dist(s→x) + "
    "dist(x→g) == dist(s→g) AND paths(s→x) * paths(x→g) == "
    "total_paths(s→g). Mark all unavoidable cells 8; leave others "
    "unchanged. Output has 8s on bottleneck corridor cells, 0s on "
    "ring branches (where multiple shortest paths exist)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "walls are color 5, open passages are 0, start is 2, goal is 3",
    "exactly one start (color 2) and one goal (color 3)",
    "≥1 ring bypass on the path (so SOME cells remain 0 in output)",
    "≥1 bottleneck corridor segment (so SOME cells become 8 in output)",
    "start and goal are connected by ≥1 shortest path",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corridor", "no_endpoints", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "9..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_rings":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "ring_size":      {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "horizontal_corridor_with_rings",
                       "valid": "horizontal_corridor_with_rings"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_corridor|no_endpoints|full_grid"},
}


def _carve_horizontal_corridor(g, r, c1, c2):
    """Open cells (r, c) for c in [c1, c2]."""
    for c in range(c1, c2 + 1):
        g[r][c] = 0


def _carve_ring(g, r_mid, c1, c2, half_height):
    """Carve a rectangular ring on horizontal corridor centered at r_mid,
    spanning cols c1..c2, extending half_height above and below.
    Result: two parallel paths (top and bottom of ring) of equal length
    from c1 to c2, joined at columns c1 and c2 by vertical connectors.
    """
    h = len(g); w = len(g[0])
    r_top = max(0, r_mid - half_height)
    r_bot = min(h - 1, r_mid + half_height)
    # carve top and bottom edges
    for c in range(c1, c2 + 1):
        g[r_top][c] = 0
        g[r_bot][c] = 0
    # carve left and right vertical edges
    for r in range(r_top, r_bot + 1):
        g[r][c1] = 0
        g[r][c2] = 0
    # close the middle of the corridor (so paths must go around)
    for c in range(c1 + 1, c2):
        if r_mid != r_top and r_mid != r_bot:
            g[r_mid][c] = 5  # wall
    # interior cells (between top/bot rows, between c1+1 and c2-1) are walls
    for r in range(r_top + 1, r_bot):
        for c in range(c1 + 1, c2):
            if r != r_mid:
                g[r][c] = 5
            # if r == r_mid we already set wall above


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one start (color 2), one goal (color 3), and wall cells (color 5)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    for color, label in ((2, "start"), (3, "goal")):
        count = sum(grid[r][c] == color for r in range(h) for c in range(w))
        if count != 1:
            errs.append(f"expected exactly 1 {label} cell (color {color}), got {count}")
    fives = sum(grid[r][c] == 5 for r in range(h) for c in range(w))
    if fives == 0:
        errs.append("no wall cells (color 5) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # colours are role-fixed (5=wall,2=start,3=goal,8=output) so palette is intrinsic;
    # diversity comes from maze size + ring count. Widen both (n_rings up to 3).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 13, 16)
        n_rings = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 18, 24)
        n_rings = ctx.draw_int("n_rings", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 14, 20)
        n_rings = ctx.draw_int("n_rings", 1, 3)

    rng = ctx.draw_rng("placement")
    for outer in range(40):
        g = full_grid(h, w, 5)
        # Choose middle row for horizontal corridor
        r_mid = rng.randint(max(3, h // 2 - 1), min(h - 4, h // 2 + 1))
        # Start near left edge, goal near right edge
        c_start = 1
        c_goal = w - 2

        # Plan rings: pick n_rings non-overlapping column intervals
        # along the corridor for the ring bypasses.
        available_width = c_goal - c_start - 1  # space for rings + bottlenecks
        if available_width < 6:
            continue

        # Pick ring widths
        ring_specs = []
        cur_c = c_start + 2  # leave a bottleneck of length ≥1 before first ring
        ok = True
        for _ in range(n_rings):
            ring_w = ctx.draw_int("ring_size", 3, 5) + rng.randint(0, 1)
            if cur_c + ring_w + 2 >= c_goal:
                ok = False; break
            # gap before next ring
            ring_specs.append((cur_c, cur_c + ring_w))
            cur_c += ring_w + 2 + rng.randint(0, 2)  # bottleneck gap
        if not ok or not ring_specs:
            continue
        if ring_specs[-1][1] >= c_goal - 1:
            continue

        # Carve the corridor first
        _carve_horizontal_corridor(g, r_mid, c_start, c_goal)
        # Carve rings
        for ring_c1, ring_c2 in ring_specs:
            half_h = rng.choice([1, 1, 2])
            # ensure ring fits vertically
            if r_mid - half_h < 1 or r_mid + half_h > h - 2:
                half_h = 1
            _carve_ring(g, r_mid, ring_c1, ring_c2, half_h)

        # Place start and goal
        g[r_mid][c_start] = 2
        g[r_mid][c_goal] = 3
        return g
    # Fallback: simple maze with one ring
    g = full_grid(h, w, 5)
    r_mid = h // 2
    _carve_horizontal_corridor(g, r_mid, 1, w - 2)
    _carve_ring(g, r_mid, 4, 8, 1)
    g[r_mid][1] = 2
    g[r_mid][w - 2] = 3
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 12, 5)
    if name == "no_corridor":
        # all wall — start/goal but no open passage
        g[3][1] = 2
        g[3][10] = 3
        return g
    if name == "no_endpoints":
        # corridor but missing both start and goal markers
        for c in range(2, 8):
            g[3][c] = 0
        return g
    if name == "full_grid":
        # all open — every interior cell sits on multiple paths
        for r in range(8):
            for c in range(12):
                g[r][c] = 0
        g[3][1] = 2
        g[3][10] = 3
        return g
    return g
