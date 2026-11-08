"""Generator for arc_puzzle_bank_21_set12_bundle:hard_l21 — even-distance halo per seed.

Rule: each non-{0, 5} cell is a seed. BFS shortest distance (through 0-cells,
blocked by 5-walls AND by other colored cells) to each reachable 0-cell; cells
at EVEN BFS distance get painted with that seed's color. 5-walls and seeds are
preserved; overlapping halos resolve in row-major seed order (later wins).

Rule-safe diversity (this version): grid size, seed COUNT and colors (any
non-{0,5}), and WALL count/shape — walls reshape the BFS topology, so more of
them (as short segments, not just dots) = richer, harder halos.
Rule-LOCKED: color 5 is the wall sentinel; seeds must be non-0 and non-5.
Degenerates: no_seeds, walls_seal_seed, single_cell_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7ebaf709467"
VERSION = "2.1.0"  # add executable seed/wall invariants for even-distance halo episodes.
TASK_ID = "f7ebaf709467"

SUMMARY = (
    "0-bg grid (size varies, up to ~16x20). Several single-cell colored SEEDS "
    "in distinct non-{0,5} colors, plus color-5 WALLS placed as short segments "
    "and dots. Rule: from each seed, BFS through open 0-cells (blocked by walls "
    "and other colors); paint every reachable 0-cell at EVEN BFS distance with "
    "the seed's color. Seeds and walls stay; overlapping halos resolve in "
    "row-major seed order. Net: each seed emits an every-other-ring halo that "
    "wraps around the walls. (Was: 8-10x9-11, 1-2 seeds, <=3 dot walls.)"
)

INVARIANTS = [
    "background is 0",
    ">=1 single-cell seed in a non-{0,5} color (distinct per seed)",
    "color-5 walls never seal a seed (each seed keeps its 4 orthogonal neighbors open)",
    "seeds are single isolated cells (not adjacent to each other)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "walls_seal_seed", "single_cell_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)  # any non-0, non-5 (5 is the wall)

AXES = {
    "grid_h":         {"type": "int", "default": "8-10 easy / 10-13 med / 13-16 hard", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "9-11 easy / 11-15 med / 15-20 hard", "valid": "8..24"},
    "n_seeds":        {"type": "int", "default": "1-2 easy / 2-4 med / 3-6 hard", "valid": "1..6"},
    "n_walls":        {"type": "int", "default": "0-3 easy / 3-7 med / 6-12 hard", "valid": "0..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "= n_seeds", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "seeds_with_wall_segments",
                       "valid": "seeds_with_wall_segments"},
    "n_distinct_colors": {"type": "int", "default": "= n_seeds", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _near_seed(r, c, seed_pos, d=1):
    return any(abs(r - sr) + abs(c - sc) <= d for sr, sc in seed_pos)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, sr_, wl = (8, 10), (9, 11), (1, 2), (0, 3)
    elif difficulty == "hard":
        hr, wr, sr_, wl = (13, 16), (15, 20), (3, 6), (6, 12)
    else:
        hr, wr, sr_, wl = (10, 13), (11, 15), (2, 4), (3, 7)
    rng = ctx.draw_rng("layout")

    for _outer in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        n_seeds = min(rng.randint(*sr_), len(SEED_COLORS))
        n_walls = rng.randint(*wl)
        g = full_grid(h, w, 0)
        seed_colors = rng.sample(SEED_COLORS, n_seeds)
        seed_pos = []
        ok = True
        for color in seed_colors:
            placed = False
            for _ in range(120):
                r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
                if g[r][c] != 0:
                    continue
                if any(abs(r - sr) + abs(c - sc) < 3 for sr, sc in seed_pos):
                    continue
                g[r][c] = color
                seed_pos.append((r, c))
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue

        # walls as short segments (length 1-3) — reshape the BFS topology;
        # never within Manhattan-1 of a seed, so every seed keeps all 4
        # orthogonal neighbors open (halos always spread).
        placed_walls = 0
        for _ in range(n_walls * 3):
            if placed_walls >= n_walls:
                break
            r0 = rng.randint(0, h - 1); c0 = rng.randint(0, w - 1)
            dr, dc = rng.choice(((0, 1), (1, 0), (1, 1), (1, -1)))
            length = rng.randint(1, 3)
            seg = [(r0 + dr * i, c0 + dc * i) for i in range(length)]
            if not all(0 <= r < h and 0 <= c < w and g[r][c] == 0
                       and not _near_seed(r, c, seed_pos) for r, c in seg):
                continue
            for r, c in seg:
                g[r][c] = 5
            placed_walls += 1
        return g
    raise ValueError("could not realize hard_l21 layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # Walls but no seeds — rule's BFS has no source; output is just walls.
        g[3][4] = 5; g[5][6] = 5
        return g
    if name == "walls_seal_seed":
        # Seed completely surrounded by walls — BFS reaches no 0-cell; halo is
        # just the seed.
        g[4][4] = 4
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            g[4 + dr][4 + dc] = 5
        return g
    if name == "single_cell_grid":
        # 1x1 grid with just a seed — no other cells to halo.
        return [[4]]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v not in (0, 5)]
    if not seeds:
        errors.append("expected at least one non-{0,5} seed")
    colors = [v for _, _, v in seeds]
    if len(colors) != len(set(colors)):
        errors.append("seed colors are not distinct")
    for i, (r1, c1, _) in enumerate(seeds):
        for r2, c2, _ in seeds[i + 1:]:
            if abs(r1 - r2) + abs(c1 - c2) < 3:
                errors.append("seeds are too close to each other")
                return errors
    for sr, sc, _ in seeds:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = sr + dr, sc + dc
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 5:
                errors.append("wall touches a seed orthogonally")
                return errors
    return errors
