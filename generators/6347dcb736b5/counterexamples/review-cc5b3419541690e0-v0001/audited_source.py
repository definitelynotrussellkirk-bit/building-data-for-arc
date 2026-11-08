"""Generator for arc_additional_puzzle_bank_volume2:M9 — Replace each object with its bbox-outline.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_rectangular, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6347dcb736b5"
VERSION = "1.2.1"
TASK_ID = "6347dcb736b5"
SUMMARY = "2-5 non-touching colored blobs (some non-rectangular); output traces each obj's bbox outline."

# Rivals: 'outline the largest blob only' refuted by ≥1 demo with ≥2
# blobs (all get outlined). 'fill bbox solid instead of outline'
# refuted by ≥1 demo with a ≥4×4 blob (interior visible as bg).
# 'recolor outline' refuted by any demo (output preserves color).
# 'erase original blob' refuted by ≥1 demo where the outline lies on
# the bbox border but the original cells could have been elsewhere.
# 3 demos with varied blob counts + shapes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "between 2 and 4 non-touching blobs",
    "at least one blob is non-rectangular (so output != input)",
    "blobs use distinct non-bg colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_rectangular", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "6..15"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "6..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥2 non-bg cells present (unless degenerate no_blobs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture == "no_blobs":
        return errs
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonzero) < 2:
        errs.append(f"fewer than 2 non-bg cells: {len(nonzero)}")
    return errs


def _has_neighbor(p, used, ignore=frozenset()):
    r, c = p
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        if (r+dr, c+dc) in ignore: continue
        if (r+dr, c+dc) in used: return True
    return False


def _grow_blob(rng, h, w, used, target_size):
    for _ in range(50):
        seed = (rng.randint(0, h-1), rng.randint(0, w-1))
        if seed in used or _has_neighbor(seed, used): continue
        cells = {seed}
        frontier = [seed]
        while frontier and len(cells) < target_size:
            r, c = frontier.pop(rng.randint(0, len(frontier)-1))
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                nr, nc = r+dr, c+dc
                if not (0 <= nr < h and 0 <= nc < w): continue
                cand = (nr, nc)
                if cand in cells or cand in used: continue
                if _has_neighbor(cand, used, ignore=cells): continue
                cells.add(cand)
                frontier.append(cand)
                if len(cells) == target_size: break
        if len(cells) == target_size:
            return cells
    return None


def _seed_nonrect_blob(rng, h, w):
    """A small connected L/T-like blob whose bbox-outline differs from the input. Random growth
    occasionally produced only rectangles/lines, hiding the bbox-outline rule (output==input);
    the first helpful blob is now forced non-rectangular. (reviewer next252 fix)"""
    shapes = [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    ]
    shape = rng.choice(shapes)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    top = rng.randint(0, h - sh)
    left = rng.randint(0, w - sw)
    return {(top + r, left + c) for r, c in shape}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 7, 8, 7, 8
        n_blobs_lo, n_blobs_hi = 2, 3
        size_lo, size_hi = 3, 5
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 15, 12, 15
        n_blobs_lo, n_blobs_hi = 3, 5
        size_lo, size_hi = 4, 9
    else:
        h_lo, h_hi, w_lo, w_hi = 9, 12, 9, 12
        n_blobs_lo, n_blobs_hi = 2, 4
        size_lo, size_hi = 3, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n_blobs = ctx.draw_int("n_blobs", n_blobs_lo, n_blobs_hi)

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    sizes = [rng.randint(size_lo, size_hi) for _ in range(n_blobs)]
    colors = [c for c in range(1, 10)]
    rng.shuffle(colors)

    used: set[tuple[int,int]] = set()
    for i, size in enumerate(sizes):
        # force the FIRST blob non-rectangular so the bbox-outline rule is always visible
        # (used is empty on i==0, so no touching conflict). (reviewer next252 fix)
        blob = _seed_nonrect_blob(rng, h, w) if i == 0 else _grow_blob(rng, h, w, used, size)
        if blob is None: continue
        used |= blob
        color = colors[i % len(colors)]
        for r, c in blob: g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "all_rectangular":
        # all blobs are solid rectangles → bbox-outline equals input outline, rule is identity
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 4
        for r in range(6, 8):
            for c in range(6, 9):
                g[r][c] = 6
        return g
    if name == "single_blob":
        # one blob → no comparison among objects, rule still works but trivially
        for r, c in [(3, 3), (3, 4), (4, 3), (5, 4), (6, 4)]:
            g[r][c] = 5
        return g
    if name == "no_blobs":
        # empty grid → no objects to outline
        return g
    return g
