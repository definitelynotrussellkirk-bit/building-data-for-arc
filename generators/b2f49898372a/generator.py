"""Generator for puzzle b2f49898372a.

Rule: each color-7 marker looks along 8-background rays; the first
visible adjacent 1/6 pair is rewritten to ordered 6,1 in that viewing
direction.

Combinatorial axes (8): grid_h/w, ray_direction, gap_min, gap_max,
n_corridors, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_corridor, no_pair, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b2f49898372a"
VERSION = "2.1.0"
TASK_ID = "b2f49898372a"
SUMMARY = (
    "8-bg grid (h, w ~ 8-18) containing MANY independent color-7 "
    "markers. Each marker has a clear ray of color-8 background cells "
    "in one of four directions and then a visible adjacent 1/6 pair. "
    "The input deliberately puts the near/far pair as 1 then 6; the "
    "canonical rule scans from each marker through 8s and rewrites the "
    "visible pair to 6 then 1 in the viewing direction. This matches "
    "the real task, whose examples are dense 8-background fields with "
    "multiple 7 markers and multiple 1/6 pairs, not a sparse 0-bg "
    "single-corridor scene."
)

INVARIANTS = [
    "background/modal color is 8",
    "there are multiple color-7 markers",
    "each marker has a non-blocked 8 ray to a visible adjacent 1/6 pair",
    "all non-background colors are exactly 1, 6, and 7",
]

DIRECTIONS = ("right", "left", "down", "up")
DEGENERATE_TEXTURES = ("no_corridor", "no_pair", "full_grid")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "7..18"},
    "ray_direction":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DIRECTIONS)},
    "gap_min":        {"type": "int", "default": "0", "valid": "0..3"},
    "gap_max":        {"type": "int", "default": "rng 2..5", "valid": "0..8"},
    "n_corridors":    {"type": "int", "default": "rng by difficulty",
                       "valid": "3..14"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for ray_direction",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_DIR_DELTAS = {
    "right": (0, 1),
    "left": (0, -1),
    "down": (1, 0),
    "up": (-1, 0),
}


def _visible_pair(grid, r, c, direction):
    h = len(grid)
    w = len(grid[0]) if h else 0
    dr, dc = _DIR_DELTAS[direction]
    rr, cc = r + dr, c + dc
    while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 8:
        rr += dr
        cc += dc
    r2, c2 = rr + dr, cc + dc
    if (0 <= rr < h and 0 <= cc < w and
            0 <= r2 < h and 0 <= c2 < w):
        pair = (grid[rr][cc], grid[r2][c2])
        if set(pair) == {1, 6}:
            return (rr, cc, r2, c2)
    return None


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariant check for the multi-marker 8-field task."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w or any(len(row) != w for row in grid):
        return ["grid is empty or ragged"]
    palette = {v for row in grid for v in row}
    if not palette <= {1, 6, 7, 8}:
        errors.append(f"unexpected colors: {sorted(palette - {1, 6, 7, 8})}")
    bg_count = sum(1 for row in grid for v in row if v == 8)
    if bg_count <= (h * w) // 2:
        errors.append("8 is not the dominant background/corridor color")
    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    if len(sevens) < 3:
        errors.append(f"expected multiple 7 markers, found {len(sevens)}")
    ones = sum(1 for row in grid for v in row if v == 1)
    sixes = sum(1 for row in grid for v in row if v == 6)
    if ones != sixes or ones < 3:
        errors.append(f"expected balanced multiple 1/6 pairs, found 1:{ones} 6:{sixes}")
    visible = 0
    for r, c in sevens:
        if any(_visible_pair(grid, r, c, d) for d in DIRECTIONS):
            visible += 1
    if visible < max(1, len(sevens) // 2):
        errors.append(f"too few markers see a 1/6 pair through 8s: {visible}/{len(sevens)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h_lo, h_hi = 8, 10
        n_lo, n_hi = 3, 5
    elif difficulty == "hard":
        h_lo, h_hi = 13, 18
        n_lo, n_hi = 8, 14
    else:
        h_lo, h_hi = 9, 14
        n_lo, n_hi = 5, 8

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 8)

    direction_override = overrides.get("texture") or overrides.get("ray_direction")
    if direction_override not in _DIR_DELTAS:
        direction_override = None

    gap_min = max(0, min(3, int(overrides.get("gap_min", 0))))
    gap_max = int(overrides.get("gap_max", ctx.draw_int("gap_max", 2, 5)))
    gap_max = max(gap_min, min(8, gap_max))

    n_target = int(overrides.get("n_corridors", ctx.draw_int("n_corridors", n_lo, n_hi)))
    n_target = max(3, min(14, n_target))

    occupied = set()

    def candidates():
        dirs = [direction_override] if direction_override else list(DIRECTIONS)
        rng.shuffle(dirs)
        out = []
        for r in range(h):
            for c in range(w):
                for direction in dirs:
                    dr, dc = _DIR_DELTAS[direction]
                    max_gap = min(gap_max, max(h, w))
                    gaps = list(range(gap_min, max_gap + 1))
                    rng.shuffle(gaps)
                    for gap in gaps:
                        ray = [(r + dr * i, c + dc * i) for i in range(gap + 3)]
                        if all(0 <= rr < h and 0 <= cc < w for rr, cc in ray):
                            out.append((r, c, direction, gap, ray))
        rng.shuffle(out)
        return out

    placed = 0
    for r, c, direction, gap, ray in candidates():
        if placed >= n_target:
            break
        if any(cell in occupied for cell in ray):
            continue
        # Keep colored cells from accidentally sitting in another marker's ray.
        for cell in ray:
            occupied.add(cell)
        dr, dc = _DIR_DELTAS[direction]
        g[r][c] = 7
        near = (r + dr * (gap + 1), c + dc * (gap + 1))
        far = (r + dr * (gap + 2), c + dc * (gap + 2))
        g[near[0]][near[1]] = 1
        g[far[0]][far[1]] = 6
        placed += 1

    # If a cramped override produced too few placements, retry once on a larger
    # clean field with no direction override.  This keeps self_check/gates stable.
    if sum(1 for row in g for v in row if v == 7) < 3:
        h = max(h, 12)
        w = max(w, 12)
        g = full_grid(h, w, 8)
        occupied = set()
        for r, c, direction, gap, ray in candidates():
            if sum(1 for row in g for v in row if v == 7) >= 3:
                break
            if any(cell in occupied for cell in ray):
                continue
            for cell in ray:
                occupied.add(cell)
            dr, dc = _DIR_DELTAS[direction]
            g[r][c] = 7
            near = (r + dr * (gap + 1), c + dc * (gap + 1))
            far = (r + dr * (gap + 2), c + dc * (gap + 2))
            g[near[0]][near[1]] = 1
            g[far[0]][far[1]] = 6
    return g


def _draw_from_degenerate(name, rng):
    h = w = 11
    g = full_grid(h, w, 8)
    if name == "no_corridor":
        g[h // 2][1] = 7
        g[h // 2][2] = 0
        g[h // 2][4] = 1
        g[h // 2][5] = 6
        return g
    if name == "no_pair":
        g[h // 2][1] = 7
        return g
    if name == "full_grid":
        return g
    return g
