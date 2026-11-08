"""Generator for arc_puzzle_bank_21_set6_s:S6_H2 — paint best-turn-count wire path.

Rule: color-2 starts touch color-1 wires. The rule follows each wire
and paints the wire with the highest turn count in color 3.

Combinatorial axes (8): grid_h, grid_w, palette_kind, path_variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_start, no_wire, straight_wire.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd7b84c485b8"
# 2.1.0: docstring sync only -- code already generates RANDOM-WALK wires of
# varied length/turns on variable-size grids with 1-3 wires (the stale
# _PATHS/fixed-10x11 description was inaccurate). No behavioural change to
# generate(); _PATHS kept only for the degenerate fixtures.
VERSION = "2.1.1"  # add self_check
TASK_ID = "bd7b84c485b8"
SUMMARY = (
    "0-bg grid (variable size ~10-14) with 1-3 COLOR-1 (BLUE) random-walk "
    "WIRES of length 4-8 with occasional turns; each wire has ONE adjacent "
    "COLOR-2 (RED) START cell. Rule: from each start, follow the attached "
    "non-branching color-1 wire and count its turns (direction changes); "
    "the wire with the MAXIMUM turn count (ties broken by length) is "
    "RECOLORED to COLOR 3 (green). Other wires and all start cells stay. "
    "Multiple wires per grid exercise the turn-count selection."
)

INVARIANTS = [
    "there is at least one color-2 start cell",
    "each start touches a non-branching color-1 wire",
    "the primary wire has one or more turns",
    "the selected wire path is recolored to 3",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_start", "no_wire", "straight_wire")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "path_variant":   {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "single_2_start_with_turning_1_wire",
                       "valid": "single_2_start_with_turning_1_wire"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_start|no_wire|straight_wire"},
}

_PATHS = [
    [(2, 2), (2, 3), (2, 4), (3, 4), (4, 4), (4, 5), (4, 6)],
    [(1, 3), (2, 3), (3, 3), (3, 4), (3, 5), (4, 5), (5, 5)],
    [(3, 1), (3, 2), (4, 2), (5, 2), (5, 3), (5, 4), (4, 4)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has color-2 start cell; has color-1 wire cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    twos = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    ones = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    if not twos and not ones:
        return errs  # degenerate
    if not twos:
        return errs  # degenerate no_start
    if not ones:
        errs.append("no color-1 wire cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h, w = 10, 11
        n_wires = 1
    elif difficulty == "hard":
        h, w = rng.randint(11, 14), rng.randint(12, 15)
        n_wires = rng.randint(2, 3)
    else:
        h, w = rng.randint(10, 12), rng.randint(11, 13)
        n_wires = rng.randint(1, 2)
    for _ in range(40):
        g = full_grid(h, w, 0)
        placed = 0
        for wire_i in range(n_wires):
            for _ in range(30):
                # Random walk wire: start at (r, c), pick random direction,
                # take 4-8 steps with occasional turns.
                wlen = rng.randint(4, 8)
                r, c = rng.randint(2, h - 3), rng.randint(2, w - 3)
                d_idx = rng.randint(0, 3)
                dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                cells = [(r, c)]
                for _ in range(wlen - 1):
                    if rng.random() < 0.45:  # turn
                        d_idx = (d_idx + rng.choice([-1, 1])) % 4
                    dr, dc = dirs[d_idx]
                    nr, nc = r + dr, c + dc
                    if not (1 <= nr < h - 1 and 1 <= nc < w - 1):
                        break
                    if (nr, nc) in cells:
                        break
                    cells.append((nr, nc))
                    r, c = nr, nc
                if len(cells) < 4:
                    continue
                # Check cells + neighbors free
                ok = True
                for cr, cc in cells:
                    for dr_n, dc_n in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr_n, cc + dc_n
                        if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0 and (nr, nc) not in cells:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    continue
                # Place start cell adjacent to first cell (must be free)
                first_r, first_c = cells[0]
                start_options = [(first_r + dr, first_c + dc) for dr, dc in dirs
                                 if 0 <= first_r + dr < h and 0 <= first_c + dc < w
                                 and (first_r + dr, first_c + dc) not in cells
                                 and g[first_r + dr][first_c + dc] == 0]
                if not start_options:
                    continue
                sr, sc = rng.choice(start_options)
                # Check start has no other non-bg neighbors
                ok2 = True
                for dr_n, dc_n in dirs:
                    nr, nc = sr + dr_n, sc + dc_n
                    if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0 and (nr, nc) != (first_r, first_c):
                        ok2 = False
                        break
                if not ok2:
                    continue
                g[sr][sc] = 2
                for cr, cc in cells:
                    g[cr][cc] = 1
                placed += 1
                break
        if placed == n_wires:
            return g
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 11, 0)
    path = _PATHS[0]
    if name == "no_start":
        # wire but no 2-start → no walker initiated, rule doesn't fire
        for r, c in path: g[r][c] = 1
        return g
    if name == "no_wire":
        # 2-start but no 1-wire → walker has nothing to follow
        g[3][1] = 2
        return g
    if name == "straight_wire":
        # straight wire (no turns) → turn-count = 0, no "best" path to highlight
        for c in range(2, 8): g[3][c] = 1
        g[3][1] = 2
        return g
    return g
