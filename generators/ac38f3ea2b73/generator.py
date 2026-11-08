"""Generator for arc_puzzle_bank_tenth21:M67.

Rule: a small 7-frame interior is transplanted into a larger 7-frame
(centered).

Combinatorial axes (8): grid_h, grid_w, palette_kind, small_h, small_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_small_frame, no_large_frame, no_interior.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "ac38f3ea2b73"
VERSION = "2.0.1"  # shape-locked in+out: hardcoded 16x20 grid + fixed frames (canonical is 10x14/11x15). Rule pastes the smaller color-7 frame's interior centered into the bigger frame; now vary grid + both frame sizes/positions/marks."
TASK_ID = "ac38f3ea2b73"
SUMMARY = "A small 7-frame interior is transplanted into a larger 7-frame."

INVARIANTS = [
    "there are exactly two color-7 rectangular frames",
    "the smaller frame has a nonzero interior pattern",
    "the larger frame interior can contain the smaller frame interior centered",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_small_frame", "no_large_frame", "no_interior")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "16", "valid": "16"},
    "grid_w":         {"type": "int", "default": "20", "valid": "20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "small_h":        {"type": "int", "default": "rng 5..6", "valid": "3..7"},
    "small_w":        {"type": "int", "default": "rng 5..6", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "two_frames",
                       "valid": "two_frames"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-7 cells present (two frames), and non-{0,7} cells present (interior)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_small_frame", "no_large_frame", "no_interior"):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_7 = any(grid[r][c] == 7 for r in range(h) for c in range(w))
    has_interior = any(grid[r][c] not in (0, 7) for r in range(h) for c in range(w))
    if not has_7:
        errs.append("no color-7 frame cells found")
    if not has_interior:
        errs.append("no interior (non-{0,7}) cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # Rule: two color-7 rect frames; the smaller (by perimeter) is the SOURCE,
    # the bigger is the DEST; paste the source's interior pattern centered into
    # the dest. v1.x hardcoded a 16x20 grid + fixed frames (shape-locked in+out)
    # though canonical is 10x14 / 11x15. Now vary grid + both frame sizes/marks.
    if difficulty == "easy":
        ssh = ctx.draw_int("small_h", 3, 4); ssw = ctx.draw_int("small_w", 3, 4)
        bbh = ctx.draw_int("big_h", 6, 8); bbw = ctx.draw_int("big_w", 6, 8)
    elif difficulty == "hard":
        ssh = ctx.draw_int("small_h", 4, 6); ssw = ctx.draw_int("small_w", 4, 6)
        bbh = ctx.draw_int("big_h", 9, 12); bbw = ctx.draw_int("big_w", 9, 12)
    else:
        ssh = ctx.draw_int("small_h", 3, 5); ssw = ctx.draw_int("small_w", 3, 5)
        bbh = ctx.draw_int("big_h", 7, 10); bbw = ctx.draw_int("big_w", 7, 10)
    bbh = max(bbh, ssh + 2); bbw = max(bbw, ssw + 2)   # dest strictly bigger
    gh = max(ssh, bbh) + 2
    gw = 1 + ssw + 1 + bbw + 1                          # small left, big right
    g = full_grid(gh, gw, 0)
    # source frame top-left
    draw_frame(g, 1, 1, ssh, ssw, 7)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 8, 9], 3)
    interior = [(r, c) for r in range(2, ssh) for c in range(2, ssw)]
    if interior:
        k = rng.randint(1, len(interior))
        for i, (r, c) in enumerate(rng.sample(interior, k)):
            g[r][c] = colors[i % len(colors)]
    # dest frame to the right (empty interior)
    bc = ssw + 3
    draw_frame(g, 1, bc, bbh, bc + bbw - 1, 7)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(16, 20, 0)
    if name == "no_small_frame":
        # only the large frame → no source pattern to transplant
        draw_frame(g, 3, 10, 13, 18, 7)
        return g
    if name == "no_large_frame":
        # only small frame with interior → no destination
        draw_frame(g, 1, 1, 5, 5, 7)
        g[2][2] = 4; g[3][2] = 6
        return g
    if name == "no_interior":
        # both frames present but small frame is empty → nothing to transplant
        draw_frame(g, 1, 1, 5, 5, 7)
        draw_frame(g, 3, 10, 13, 18, 7)
        return g
    return g
