"""Generator for puzzle 6cf79266.

Rule: scan grid; whenever an empty 3x3 block is found (not yet
painted), fill it with color 1.

Combinatorial axes (8): grid_h/w, n_empty_blocks, fg_density, fg_color,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_empty_blocks, all_empty, monochrome.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8d83f9744f6a"
VERSION = "1.2.0"
TASK_ID = "8d83f9744f6a"
SUMMARY = "Sparse 0/3 grid with explicit 3x3 empty blocks; rule paints them 1."

INVARIANTS = [
    "non-bg color is exclusively 3 (the fg_color)",
    ">=1 explicit 3x3 all-0 region (rule paints it)",
    "fg density 40-70% (so blocks are detectable)",
]

POSITION_BIASES = ("scattered", "corners", "row_aligned", "diagonal",
                   "centered")
DEGENERATE_TEXTURES = ("no_empty_blocks", "all_empty", "monochrome")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..22", "valid": "10..28"},
    "grid_w":         {"type": "int", "default": "rng 14..22", "valid": "10..28"},
    "n_empty_blocks": {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "fg_density":     {"type": "float", "default": "rng 0.4..0.7",
                       "valid": "0.3..0.85"},
    "fg_color":       {"type": "color", "default": "3",
                       "valid": "1..9 (≠1)"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 22, 28
    else:
        h_lo, h_hi = 14, 22
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_blocks = int(overrides.get("n_empty_blocks",
                                 ctx.draw_int("n_empty_blocks", 1, 3)))
    n_blocks = max(1, min(5, n_blocks))
    fg_density = float(overrides.get("fg_density",
                                     ctx.draw_rng("fg_density")
                                     .uniform(0.4, 0.7)))
    fg_color = int(overrides.get("fg_color", 3))
    if fg_color == 1:
        fg_color = 3
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    # Start dense, then cut exact isolated 3x3 blank witnesses.  The previous
    # Bernoulli background often created many accidental all-zero 3x3 windows
    # (e.g. 13+ on normal/easy seeds), so the rule painted much more than the
    # declared `n_empty_blocks` evidence.
    positions = _pick_block_positions(bias, h, w, n_blocks, rng)[:n_blocks]
    g = full_grid(h, w, fg_color)
    allowed_starts = set(positions)
    for r0, c0 in positions:
        for dr in range(3):
            for dc in range(3):
                g[r0 + dr][c0 + dc] = 0

    # Sprinkle non-witness zero texture without creating new 3x3 blank starts.
    target_zeros = max(len(positions) * 9, int((1.0 - fg_density) * h * w))
    candidates = [(r, c) for r in range(h) for c in range(w) if g[r][c] != 0]
    rng.shuffle(candidates)
    for r, c in candidates:
        if sum(1 for row in g for v in row if v == 0) >= target_zeros:
            break
        g[r][c] = 0
        extra = set(_empty3_starts(g)) - allowed_starts
        if extra:
            g[r][c] = fg_color
    return g


def _block_cells(r0, c0):
    return {(r0 + dr, c0 + dc) for dr in range(3) for dc in range(3)}


def _non_touching_block(pos, chosen):
    cells = _block_cells(*pos)
    for other in chosen:
        other_cells = _block_cells(*other)
        if any(abs(r - rr) <= 1 and abs(c - cc) <= 1
               for r, c in cells for rr, cc in other_cells):
            return False
    return True


def _complete_positions(candidates, h, w, n, rng):
    out = []
    for pos in candidates:
        if len(out) >= n:
            return out
        if 0 <= pos[0] <= h - 3 and 0 <= pos[1] <= w - 3 and _non_touching_block(pos, out):
            out.append(pos)
    all_pos = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    rng.shuffle(all_pos)
    for pos in all_pos:
        if len(out) >= n:
            return out
        if _non_touching_block(pos, out):
            out.append(pos)
    if len(out) < n:
        raise ValueError(f"could not place {n} isolated empty 3x3 blocks in {h}x{w}")
    return out


def _pick_block_positions(bias, h, w, n, rng):
    if bias == "corners":
        candidates = [(0, 0), (0, w - 3), (h - 3, 0), (h - 3, w - 3)]
        rng.shuffle(candidates)
        return _complete_positions(candidates, h, w, n, rng)
    if bias == "row_aligned":
        r = rng.randint(0, h - 3)
        candidates = [(r, c) for c in range(0, w - 2, 4)]
        return _complete_positions(candidates, h, w, n, rng)
    if bias == "diagonal":
        candidates = [(i * 4, i * 4) for i in range(min(h // 4, w // 4))]
        return _complete_positions(candidates, h, w, n, rng)
    if bias == "centered":
        cr, cc = (h - 3) // 2, (w - 3) // 2
        candidates = [(cr, cc), (max(0, cr - 4), cc), (cr, max(0, cc - 4))]
        return _complete_positions(candidates, h, w, n, rng)
    candidates = [(rng.randint(0, h - 3), rng.randint(0, w - 3))
                  for _ in range(n * 4)]
    return _complete_positions(candidates, h, w, n, rng)


def _empty3_starts(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    out = []
    for r in range(h - 2):
        for c in range(w - 2):
            if all(grid[r + dr][c + dc] == 0 for dr in range(3) for dc in range(3)):
                out.append((r, c))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    vals = {v for row in grid for v in row}
    if not vals <= {0, 3}:
        errors.append(f"unexpected colors for empty-block task: {sorted(vals - {0, 3})}")
    starts = _empty3_starts(grid)
    if not starts:
        errors.append("no all-zero 3x3 block for the rule to paint")
    if len(starts) > 5:
        errors.append(f"too many all-zero 3x3 starts ({len(starts)}); likely accidental blank texture")
    return errors


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_empty_blocks":
        # Densely fill with 3s so no 3x3 empty block exists
        for r in range(h):
            for c in range(w):
                g[r][c] = 3 if rng.random() < 0.95 else 0
        return g
    if name == "all_empty":
        return g
    if name == "monochrome":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g
