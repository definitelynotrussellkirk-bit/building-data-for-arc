"""Generator for puzzle dc1df850.

Rule: for each cell with v != 0 → keep. For bg cells: if any 8-neighbor
(incl self) has value 2 → 1, else 0. (Halo of 1 around 2-cells; 2s and
distractors preserved.)

Combinatorial axes (8): grid_h/w, n_seeds (2-cells), n_distractors,
seed_layout (random/cluster/diagonal/border/scattered/grid),
distractor_palette_size, distractor_density, separation
(min distance between seeds).
Degenerates: no_seeds, all_seeds, touching_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c6c61bbe7a2c"
VERSION = "1.2.0"  # restore canonical small-grid scale and add executable invariants
TASK_ID = "c6c61bbe7a2c"
SUMMARY = "Color-2 seeds get a Chebyshev-1 halo of 1; other non-zeros preserved."

INVARIANTS = [
    "≥1 color-2 seed",
    "seed cells preserved (rule's first branch)",
    "distractor non-zero cells preserved (rule's first branch)",
]

SEED_LAYOUTS = ("random", "cluster", "diagonal", "border", "scattered", "grid")
DEGENERATE_TEXTURES = ("no_seeds", "all_seeds", "touching_seeds")
HELPFUL_TEXTURES = SEED_LAYOUTS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 4..8", "valid": "4..12"},
    "grid_w":              {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "n_seeds":             {"type": "int", "default": "rng 1..2", "valid": "1..5"},
    "n_distractors":       {"type": "int", "default": "rng 0..3", "valid": "0..8"},
    "seed_layout":         {"type": "str", "default": "rng helpful",
                            "valid": "random|cluster|diagonal|border|scattered|grid"},
    "distractor_palette_size": {"type": "int", "default": "rng 1..4", "valid": "1..7"},
    "distractor_density":  {"type": "float", "default": "rng 0..0.1", "valid": "0..0.3"},
    "separation":          {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "texture":             {"type": "str", "default": "alias for seed_layout",
                            "valid": "random|cluster|diagonal|border|scattered|grid|no_seeds|all_seeds|touching_seeds"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi, d_hi = 4, 6, 5, 7, 1, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi, d_hi = 6, 9, 6, 10, 2, 3, 4
    else:
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi, d_hi = 5, 8, 5, 9, 1, 2, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_seeds = int(overrides.get("n_seeds", ctx.draw_int("n_seeds", n_lo, n_hi)))
    n_dist = int(overrides.get("n_distractors", ctx.draw_int("n_distractors", 0, d_hi)))
    layout = (overrides.get("texture") or overrides.get("seed_layout")
              or ctx.draw_choice("seed_layout", list(SEED_LAYOUTS)))
    n_decor = int(overrides.get("distractor_palette_size",
                                ctx.draw_int("distractor_palette_size", 1, 4)))
    dist_d = float(overrides.get("distractor_density",
                                 ctx.draw_rng("distractor_density").uniform(0.0, 0.035)))
    sep = int(overrides.get("separation", ctx.draw_int("separation", 2, 3)))
    g = full_grid(h, w, 0)
    seed_cells = _seed_layout(layout, h, w, n_seeds, sep, rng)
    for r, c in seed_cells:
        g[r][c] = 2
    decor_palette = [c for c in range(1, 10) if c not in {1, 2}]
    rng.shuffle(decor_palette)
    decor_palette = decor_palette[:max(1, n_decor)]
    cells_avail = [(r, c) for r in range(h) for c in range(w)
                   if g[r][c] == 0]
    rng.shuffle(cells_avail)
    placed_dist = 0
    for r, c in cells_avail:
        if placed_dist >= n_dist:
            break
        # Don't place a distractor adjacent to a seed (so halo computation is clean).
        if all(g[r + dr][c + dc] != 2 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
               if 0 <= r + dr < h and 0 <= c + dc < w):
            g[r][c] = rng.choice(decor_palette)
            placed_dist += 1
    if dist_d > 0 and decor_palette:
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and rng.random() < dist_d:
                    if all(g[r + dr][c + dc] != 2 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                           if 0 <= r + dr < h and 0 <= c + dc < w):
                        g[r][c] = rng.choice(decor_palette)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Small 0-bg halo instance: at least one color-2 seed; nonzero cells are sparse.

    The canonical task uses compact 4x5/5x5/8x8 grids, not large decorative
    canvases. This check keeps the generator in that regime while still allowing
    a few preserved distractor colors.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 12 or w > 12:
        errs.append(f"grid too large for canonical halo task: {h}x{w}")
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not seeds:
        errs.append("missing color-2 seed")
    nonzero = sum(1 for row in grid for v in row if v != 0)
    if nonzero > max(8, (h * w) // 3):
        errs.append(f"too many nonzero cells for sparse halo task: {nonzero}")
    if any(v not in range(10) for row in grid for v in row):
        errs.append("colors must be ARC digits 0..9")
    return errs


def _seed_layout(layout, h, w, n, sep, rng):
    cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    if layout == "cluster":
        cr = rng.randint(1, h - 2); cc = rng.randint(1, w - 2)
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
    elif layout == "diagonal":
        cells = [(k, k) for k in range(1, min(h, w) - 1)]
    elif layout == "border":
        cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                 if r in (1, h - 2) or c in (1, w - 2)]
        rng.shuffle(cells)
    elif layout == "scattered":
        cells = [(r, c) for r in range(1, h - 1, sep) for c in range(1, w - 1, sep)]
        rng.shuffle(cells)
    elif layout == "grid":
        cells = [(r, c) for r in range(2, h, 3) for c in range(2, w, 3)]
        rng.shuffle(cells)
    else:
        rng.shuffle(cells)
    chosen: list = []
    for cand in cells:
        if len(chosen) >= n: break
        if all(max(abs(cand[0] - cr), abs(cand[1] - cc)) >= sep
               for (cr, cc) in chosen):
            chosen.append(cand)
    return chosen


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        for _ in range(rng.randint(2, 4)):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = rng.choice([3, 4, 5, 6, 7, 8, 9])
        # Force 1 seed for invariant.
        g[h // 2][w // 2] = 2
        return g
    if name == "all_seeds":
        for r in range(0, h, 3):
            for c in range(0, w, 3):
                g[r][c] = 2
        return g
    if name == "touching_seeds":
        # Two seeds adjacent — their halos overlap.
        g[h // 2][w // 2 - 1] = 2
        g[h // 2][w // 2 + 1] = 2
        return g
    return g
