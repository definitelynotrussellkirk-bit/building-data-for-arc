"""Generator for puzzle ea959feb.

Rule: detect smallest period p such that non-1 cells obey period.
Reconstruct tile + tile across grid.

Combinatorial axes (8): period, h_factor, w_factor, palette_size,
n_corruption_blocks, block_size, anchor_corner, asymmetry_force.
Degenerates: no_corruption, all_corrupted, no_period.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f839f3ccafe5"
VERSION = "2.2.0"  # periods 2..7 (was 3/5/7) + wider factors + minimal-vertical-period gate so the rule detects exactly p
TASK_ID = "f839f3ccafe5"
SUMMARY = (
    "PERIODIC-TILED grid: a random p × p TILE (p ∈ {3, "
    "5, 7}) populated with colors from a palette of 2-4 "
    "distinct non-{0,1} colors drawn from {2..9}, then "
    "REPEATED across an h × w grid where h = p * h_factor "
    "and w = p * w_factor (h_factor, w_factor each ∈ "
    "{3, 4}, so h, w both divisible by p). After tiling, "
    "1-3 RECTANGULAR CORRUPTION BLOCKS of size 2..5 × 2..5 "
    "are placed at positions determined by a position_bias "
    "(scattered / centered / corners / spread), and every "
    "cell inside each block is OVERWRITTEN with COLOR 1 "
    "(blue) — corrupting the periodic pattern there. "
    "Rule (DETECT THE PERIODIC TILE, RESTORE OVER COLOR-1 "
    "CELLS): find the smallest period p such that the "
    "non-1 cells obey period p in both axes (grid[r][c] = "
    "grid[r mod p][c mod p] for every non-1 cell). "
    "RECONSTRUCT the p × p tile by reading any non-1 "
    "representatives at each (r mod p, c mod p) offset. "
    "REPAINT every COLOR-1 cell with the tile's value at "
    "its (r mod p, c mod p) offset. Non-corruption cells "
    "stay unchanged. Net: the 1-block corruption vanishes, "
    "leaving a clean periodic tiling."
)

INVARIANTS = [
    "h, w divisible by p",
    "p in {3, 5, 7}",
    "tile uses colors from {2..9} (no 0 or 1)",
    "non-corruption cells obey period",
    "1-3 rectangular 1-blocks corrupt the pattern",
]

POSITION_BIASES = ("scattered", "centered", "corners", "spread")
DEGENERATE_TEXTURES = ("no_corruption", "all_corrupted", "no_period")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "period":           {"type": "int", "default": "2-4 easy / 5-7 hard",
                         "valid": "2|3|4|5|6|7"},
    "h_factor":         {"type": "int", "default": "rng 3..4",
                         "valid": "2..5"},
    "w_factor":         {"type": "int", "default": "rng 3..4",
                         "valid": "2..5"},
    "palette_size":     {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "n_corruption":     {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "block_size_max":   {"type": "int", "default": "rng 3..5",
                         "valid": "2..6"},
    "position_bias":    {"type": "str", "default": "rng helpful",
                         "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for position_bias",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        period_pool = [5, 6]
    elif difficulty == "hard":
        period_pool = [7]
    else:
        period_pool = [6, 7]
    p = int(overrides.get("period", rng.choice(period_pool)))
    if p not in (5, 6, 7):
        p = 6
    fmax = max(3, min(4, 28 // p))               # eval-like 20..28 grids, <=30
    h_factor = int(overrides.get("h_factor", ctx.draw_int("h_factor", 3, fmax)))
    w_factor = int(overrides.get("w_factor", ctx.draw_int("w_factor", 3, fmax)))
    h = p * max(2, min(fmax, h_factor))
    w = p * max(2, min(fmax, w_factor))
    palette_size = int(overrides.get("palette_size", 6))
    palette_size = max(5, min(8, palette_size))
    palette_pool = list(range(2, 10))
    rng.shuffle(palette_pool)
    palette = palette_pool[:palette_size]

    def _min_vperiod_is_p(tile):
        # the rule detects the smallest VERTICAL period; require it to equal p,
        # i.e. the row-sequence is NOT periodic with any proper divisor of p.
        for q in range(1, p):
            if p % q == 0 and all(tile[r] == tile[(r + q) % p] for r in range(p)):
                return False
        return True

    tile = None
    # Use a high-frequency Latin-style tile rather than iid color blobs.  The
    # canonical task has almost no modal background and hundreds of tiny
    # same-color components; random low-palette tiles drifted to ~36 objects.
    for _ in range(40):
        a = rng.choice([1, 2, 3, 4, 5])
        b = rng.choice([1, 2, 3, 4, 5])
        off = rng.randrange(len(palette))
        cand = [[palette[(a * r + b * c + off) % len(palette)]
                 for c in range(p)] for r in range(p)]
        if _min_vperiod_is_p(cand):
            tile = cand
            break
    if tile is None:
        return _draw_from_degenerate("no_corruption", rng)
    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            g[r][c] = tile[r % p][c % p]
    n_blocks = int(overrides.get("n_corruption",
                                 ctx.draw_int("n_corruption", 1, 3)))
    n_blocks = max(1, min(5, n_blocks))
    block_max = int(overrides.get("block_size_max",
                                  ctx.draw_int("block_size_max", 4, 6)))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    for _ in range(n_blocks):
        bh = rng.randint(2, max(2, block_max - 1))
        bw = rng.randint(2, max(2, block_max))
        if bh > h or bw > w:
            continue
        br, bc = _pick_block_pos(bias, h, w, bh, bw, rng)
        for r in range(br, min(br + bh, h)):
            for c in range(bc, min(bc + bw, w)):
                g[r][c] = 1
    return g


def _pick_block_pos(bias, h, w, bh, bw, rng):
    if bias == "centered":
        return max(0, (h - bh) // 2), max(0, (w - bw) // 2)
    if bias == "corners":
        return rng.choice([(0, 0), (0, w - bw), (h - bh, 0),
                           (h - bh, w - bw)])
    return rng.randint(0, h - bh), rng.randint(0, w - bw)




def _detect_period(grid):
    h, w = len(grid), len(grid[0])
    for p in range(2, 12):
        ok = True
        for r in range(0, h - p):
            for c in range(w):
                v1, v2 = grid[r][c], grid[r + p][c]
                if v1 != 1 and v2 != 1 and v1 != v2:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return p
    return None


def self_check(grid, *, difficulty=None, meta=None):
    """Verify eval-like periodic corruption: no 0-bg, has 1-blocks, detectable period."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    vals = {v for row in grid for v in row}
    if 0 in vals:
        errs.append("default instance should not contain 0 background")
    if 1 not in vals:
        errs.append("missing color-1 corruption cells")
    p = _detect_period(grid)
    if p is None:
        errs.append("non-1 cells do not expose a detectable vertical period")
    else:
        # Every residue class used by the Racket reconstruction should have at
        # least one non-1 witness; otherwise the repair can leave 1s in output.
        for rr in range(p):
            for cc in range(p):
                if not any(grid[r][c] != 1 for r in range(rr, h, p) for c in range(cc, w, p)):
                    errs.append("a period residue class is fully corrupted")
                    return errs
    return errs

def _draw_from_degenerate(name, rng):
    p = 3
    h = p * 3; w = p * 3
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    tile = [[palette[(r + c) % 3] for c in range(p)] for r in range(p)]
    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            g[r][c] = tile[r % p][c % p]
    if name == "no_corruption":
        return g
    if name == "all_corrupted":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    if name == "no_period":
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice(palette)
        return g
    return g
