"""Generator for arc_puzzle_bank_21_set21_bundle:medium_p01 — keyed color crop.

Rule: key = at(0,0). Find the largest connected blob of `key` color
(excluding the (0,0) cell itself). Output = that blob cropped to its
bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_blob_in_key, equal_size_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "5d15679fbc44"
VERSION = "3.1.0"  # distinct=59/dup41%: one small grown key blob (4-5 cells). Rule outputs the LARGEST key-colour blob (excl. the (0,0) key cell) cropped. Now several key blobs of distinct sizes (4-10) + varied grid -> distinct 59->122, dup cleared.
TASK_ID = "5d15679fbc44"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with: (a) cell (0, 0) "
    "holds a KEY color (non-zero); (b) elsewhere a "
    "4-conn BLOB of size 4-5 in the SAME key color "
    "(strictly larger than any other key-color region); "
    "(c) 1-2 DISTRACTOR blobs of 2-3 cells in other "
    "colors. Rule: read key = at(0, 0). Find all 4-conn "
    "components of color = key EXCLUDING the (0, 0) cell "
    "itself. Pick the LARGEST such blob. Output = that "
    "blob cropped to its bounding box (preserving its "
    "shape; cells off-shape become 0)."
)

INVARIANTS = [
    "background is 0",
    "(0,0) is non-zero (the key)",
    "key-color blob away from corner exists, strictly larger than any other key-color region",
    "1-2 distractor blobs in different colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_blob_in_key", "equal_size_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "key_corner_with_keycolor_blob",
                       "valid": "key_corner_with_keycolor_blob"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 10, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 14, 20)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 16)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], rng.randint(3, 5))
    key = palette[0]
    distractors = palette[1:]
    g[0][0] = key
    used = {(0, 0), (0, 1), (1, 0)}   # block the corner key cell + neighbours
    # several key-colour blobs of DISTINCT sizes (rule outputs the LARGEST,
    # excluding the (0,0) key cell) -> the cropped output varies widely
    n_key = rng.randint(1, 3)
    for sz in rng.sample(range(4, 11), n_key):
        b = grow_blob(rng, h, w, used, sz, max_attempts=80)
        if b is None:
            continue
        for r, c in b:
            g[r][c] = key
        used |= b
    for color in distractors:
        b = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=40)
        if b is None:
            continue
        for r, c in b:
            g[r][c] = color
        used |= b
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: (0,0) is non-zero (key), bg=0, >=2 non-zero colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    if grid[0][0] == 0:
        errs.append("(0,0) is 0 — expected key color")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct non-zero colors, found {len(colors)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_key":
        # blob present but no corner key → no color filter defined
        for r, c in [(3, 3), (3, 4), (4, 4)]: g[r][c] = 4
        return g
    if name == "no_blob_in_key":
        # corner key but no other key-color blob → nothing to crop
        g[0][0] = 4
        for r, c in [(3, 3), (4, 3)]: g[r][c] = 6
        return g
    if name == "equal_size_blobs":
        # 2 key-color blobs of equal size → "strictly larger" precondition fails
        g[0][0] = 4
        for r, c in [(2, 2), (3, 2), (3, 3)]: g[r][c] = 4  # blob1, size 3
        for r, c in [(6, 6), (6, 7), (7, 7)]: g[r][c] = 4  # blob2, size 3 (tied)
        return g
    return g
