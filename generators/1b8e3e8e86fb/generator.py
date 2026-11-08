"""Generator for arc_puzzle_bank_next21:M8 — recolor selected obj to 8.

Rule: among components, pick by (max-col descending, size descending,
min-row ascending); recolor that component to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: tied_max_col (≥2 components share max-col → rule's
primary key falls to size tie-break), single_motif (only 1 component
→ trivially selected, no contrast), no_motifs (empty grid → no
candidate to recolor).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b8e3e8e86fb"
VERSION = "1.1.1"
TASK_ID = "1b8e3e8e86fb"

SUMMARY = "2-3 connected motifs in distinct colors at distinct positions (different max-col)."

INVARIANTS = [
    "background is 0",
    "2-3 motifs in distinct non-zero colors at distinct horizontal positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_max_col", "single_motif", "no_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "n":              {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_distinct_max_col",
                       "valid": "scattered_distinct_max_col"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 8, 8)
        n = ctx.draw_int("n", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 10)
        n = ctx.draw_int("n", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(2, 4))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 distinct non-bg colors (motifs) present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct motif colors, found {len(colors)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "tied_max_col":
        # Two components share max-col=8 — rule's primary sort key
        # is tied; selection falls to size/row tie-break.
        for r, c in [(0, 7), (0, 8), (1, 8)]: g[r][c] = 2
        for r, c in [(3, 7), (4, 7), (4, 8)]: g[r][c] = 3
        return g
    if name == "single_motif":
        # Only one component — trivially the selected one; no
        # contrast across candidates.
        for r, c in [(2, 4), (2, 5), (3, 5)]: g[r][c] = 6
        return g
    if name == "no_motifs":
        # Empty grid — rule's selector finds nothing.
        return g
    return g
