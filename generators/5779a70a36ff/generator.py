"""Generator for arc_puzzle_bank_21_set6:hard_f04 — A-minus-B of two motifs.

Rule: take the first 2 objects (sorted by bbox col then row). Normalize each to
its bbox top-left. Output a max(h_a,h_b) x max(w_a,w_b) grid containing A's
cells that are NOT in B, painted in A's color (A = the leftmost/topmost object).

The old docstring called this a "gallery pack" and the generator drew n=2-5
motifs — but the rule only ever reads the FIRST TWO objects, so the extra
motifs were decoy the rule ignores (canonical has exactly 2). It also never
ensured A-minus-B is non-empty (A could be a subset of B -> blank output). Now:
EXACTLY 2 motifs whose normalized shapes are mutually non-subset (so the set
difference is always non-empty), varied in shape/size/color/position.

Combinatorial axes: the two motif shapes/sizes (-> output dims + difference
pattern), the 2 colors, positions, grid size.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5779a70a36ff"
VERSION = "3.0.1"  # rule = A-minus-B of the FIRST 2 objects (A=leftmost). Old gen drew n=2-5 motifs (3rd+ are decoys the rule ignores; canonical has exactly 2) + never ensured A-B non-empty. Now EXACTLY 2 motifs, normalized shapes mutually non-subset, varied shape/size/colour/position + grid size.
TASK_ID = "5779a70a36ff"

SUMMARY = (
    "0-bg grid (size varies) with EXACTLY 2 isolated 4-connected MOTIFS in "
    "distinct non-0 colors (3-6 cells each), placed apart by >=1 bg cell. The "
    "two motifs' NORMALIZED shapes are mutually non-subset. Rule: take the "
    "first 2 objects sorted by bbox (col, then row); A = leftmost/topmost. "
    "Normalize each; output a max(h_a,h_b) x max(w_a,w_b) grid with A's cells "
    "that are NOT in B painted in A's color, rest 0. Net: set-difference "
    "A-minus-B of the two aligned shapes, in A's color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 connected motifs in distinct non-0 colors, separated by bg",
    "neither motif's normalized shape is a subset of the other (A-B non-empty)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motif_cells":    {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_diff_motifs",
                       "valid": "two_diff_motifs"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            for (r, c) in cells:
                g[r0 + r][c0 + c] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 13, 17)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")

    for _outer in range(60):
        g = full_grid(h, w, 0)
        ca, cb = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
        a = _build_motif(rng, rng.randint(3, 6))
        aset = {tuple(p) for p in a}
        b = None
        for _ in range(60):
            cand = _build_motif(rng, rng.randint(3, 6))
            cset = {tuple(p) for p in cand}
            if not (aset <= cset) and not (cset <= aset):   # mutually non-subset
                b = cand
                break
        if b is None:
            continue
        if _place(g, rng, a, ca) and _place(g, rng, b, cb):
            return g
    raise ValueError("could not realize 5779 layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly 2 connected motifs in distinct non-0 colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    # 4-connected flood fill to count components
    visited = [[False] * w for _ in range(h)]
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                visited[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == color:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                components.append(color)
    if len(components) != 2:
        errs.append(f"expected exactly 2 motifs, found {len(components)}")
    elif len(set(components)) != 2:
        errs.append(f"expected 2 distinct colors, found {set(components)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]:
            g[r][c] = 4
        return g
    if name == "all_same_color":
        for r, c in [(1, 1), (1, 2), (2, 2)]:
            g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]:
            g[r][c] = 4
        return g
    return g
