"""Generator for puzzle 484b58aa.

Rule: input has translational-periodic pattern with bg(0) holes; rule
fills holes by extending the detected period.

Combinatorial axes (8): grid_h/w, period_r, period_c, palette_size,
n_holes, tile_pattern, anchor_corner, asymmetry_force.
Degenerates: no_holes, all_holes, no_period.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "44a257e280a5"
VERSION = "2.1.0"
TASK_ID = "44a257e280a5"
SUMMARY = (
    "Grid (h, w~24-30) with a TRANSLATIONAL "
    "PERIODIC PATTERN of period (pr, pc) "
    "where pr, pc ∈ 2..4, painted from a "
    "tile (pr × pc) using one of 6 PATTERNS "
    "(rotated/stripe_h/stripe_v/checker/"
    "diagonal/block) over a 2-4 color "
    "palette drawn from 1..9. The repeating "
    "tile fills the entire grid. Then 2-6 "
    "RANDOM CELLS are punched as HOLES "
    "(set to bg = 0). Rule (PERIOD "
    "DETECTION + HOLE FILL): detect the "
    "translational period (pr, pc) of the "
    "non-bg cells. For EACH BG (0) CELL "
    "at (r, c), LOOK UP the periodic "
    "value at (r mod pr, c mod pc) of the "
    "underlying tile. PAINT the hole with "
    "that color. Original non-bg cells "
    "stay. Net: every bg hole gets filled "
    "by extending the detected periodic "
    "tiling."
)

INVARIANTS = [
    "background is 0",
    "non-bg cells follow a translational period (pr, pc) where pr,pc in 2..4",
    "many bg=0 holes / erased blocks within the periodic field",
    ">=2 distinct non-bg colors",
]

TILE_PATTERNS = ("rotated", "stripe_h", "stripe_v", "checker",
                 "diagonal", "block")
DEGENERATE_TEXTURES = ("no_holes", "all_holes", "no_period")
HELPFUL_TEXTURES = TILE_PATTERNS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 24..30", "valid": "12..30"},
    "grid_w":         {"type": "int", "default": "rng 24..30", "valid": "12..30"},
    "period_r":       {"type": "int", "default": "rng 3..6", "valid": "2..7"},
    "period_c":       {"type": "int", "default": "rng 3..6", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "rng 5..8", "valid": "2..8"},
    "n_holes":        {"type": "int", "default": "rng 24..90", "valid": "1..180"},
    "tile_pattern":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(TILE_PATTERNS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for tile_pattern",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # Canonical rows are 29x29 dense periodic fields with sizeable erased regions.
    # The old 8..14 / single-cell-hole generator was parity-correct but taught a
    # much smaller toy problem and tripped distribution_drift on both area and
    # object count.
    if difficulty == "easy":
        h_lo, h_hi = 18, 24
    elif difficulty == "hard":
        h_lo, h_hi = 28, 30
    else:
        h_lo, h_hi = 24, 30
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    pr = int(overrides.get("period_r",
                           ctx.draw_int("period_r", 3, 6)))
    pc = int(overrides.get("period_c",
                           ctx.draw_int("period_c", 3, 6)))
    pr = max(2, min(7, pr))
    pc = max(2, min(7, pc))
    palette_size = int(overrides.get("palette_size",
                                     ctx.draw_int("palette_size", 5, 8)))
    palette_size = max(2, min(8, palette_size))
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=palette_size, exclude={0}))
    n_holes = int(overrides.get("n_holes",
                                ctx.draw_int("n_holes", 35, 110)))
    n_holes = max(1, min(180, n_holes))
    pattern = (overrides.get("texture") or
               overrides.get("tile_pattern")
               or ctx.draw_choice("tile_pattern",
                                  ["rotated", "diagonal"]))
    tile = _build_tile(pattern, pr, pc, palette, rng)
    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            g[r][c] = tile[r % pr][c % pc]
    _punch_holes(g, n_holes, rng)
    return g


def _punch_holes(g, target_cells, rng):
    """Erase a mix of cells and short rectangles, like the canonical 29x29 rows."""
    h, w = len(g), len(g[0])
    holes = set()
    # Larger blocks/corridors give the learner a real extrapolation problem;
    # isolated holes alone make the task too much like local denoising.
    for _ in range(max(3, target_cells // 18)):
        rh = rng.randint(1, min(5, h // 3))
        rw = rng.randint(2, min(8, w // 3))
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                holes.add((r, c))
                if len(holes) >= target_cells:
                    break
            if len(holes) >= target_cells:
                break
        if len(holes) >= target_cells:
            break
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    for r, c in cells:
        if len(holes) >= target_cells:
            break
        holes.add((r, c))
    # Keep enough observed cells for period detection.
    max_holes = (h * w) // 3
    for r, c in list(holes)[:max_holes]:
        g[r][c] = 0


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the default rows are large, multicolor periodic fields with real holes."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w or any(len(row) != w for row in grid):
        return ["grid is empty or ragged"]
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    area = h * w
    zeros = sum(grid[r][c] == 0 for r in range(h) for c in range(w))
    nonzero_colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if difficulty != "easy" and area < 20 * 20:
        errors.append(f"default/hard grid too small for canonical-scale periodic fill: {h}x{w}")
    if zeros < max(8, area // 36):
        errors.append(f"only {zeros} bg holes in {h}x{w} grid")
    if zeros > area // 2:
        errors.append(f"too many bg holes for period detection: {zeros}/{area}")
    if len(nonzero_colors) < 4 and difficulty != "easy":
        errors.append(f"only {len(nonzero_colors)} non-bg colors; canonical rows use broad palettes")
    return errors


def _build_tile(pattern, pr, pc, palette, rng):
    if pattern == "rotated":
        return [[palette[(r + c) % len(palette)]
                 for c in range(pc)] for r in range(pr)]
    if pattern == "stripe_h":
        return [[palette[r % len(palette)] for c in range(pc)]
                for r in range(pr)]
    if pattern == "stripe_v":
        return [[palette[c % len(palette)] for c in range(pc)]
                for r in range(pr)]
    if pattern == "checker":
        return [[palette[(r + c) % 2] for c in range(pc)]
                for r in range(pr)]
    if pattern == "diagonal":
        return [[palette[(r * pc + c) % len(palette)]
                 for c in range(pc)] for r in range(pr)]
    if pattern == "block":
        return [[palette[r % len(palette)] if c < pc // 2
                 else palette[-1 % len(palette)]
                 for c in range(pc)] for r in range(pr)]
    return [[palette[(r * pc + c) % len(palette)] for c in range(pc)]
            for r in range(pr)]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    if name == "no_holes":
        for r in range(h):
            for c in range(w):
                g[r][c] = palette[(r + c) % 3]
        return g
    if name == "all_holes":
        return g
    if name == "no_period":
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice(palette)
        for _ in range(3):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = 0
        return g
    return g
