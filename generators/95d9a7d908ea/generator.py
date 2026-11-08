"""Generator for arc_puzzle_bank_seventh_21_bundle:hard_47_tile_component_with_most_holes — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "95d9a7d908ea"
# 2.1.0: the rule picks the motif with the MOST holes, crops it, and tiles 2x2.
# Random 3-5 cell motifs have NO holes, so the winner was an arbitrary solid
# shape -> the 2x2 tile was a single-color block (all_background_output). Now one
# motif is always a (varied) holed ring so the winner's crop has interior 0s and
# the tiled output shows real structure. Adds self_check.
VERSION = "2.1.0"
TASK_ID = "95d9a7d908ea"

SUMMARY = (
    "0-bg grid (h ∈ 9-13, w ∈ 11-16) "
    "with: n ∈ 2-5 SCATTERED MULTI-CELL "
    "CONNECTED MOTIFS, each a 3-5 cell "
    "motif (built via _build_motif "
    "random adjacent-step walk), each "
    "in a DISTINCT non-bg color drawn "
    "from {2..9}, placed at random "
    "non-overlapping positions via "
    "_free check (1-cell padding). "
    "Per-task semantics aim at "
    "tile-the-component-with-most-"
    "holes: motif with the largest "
    "enclosed-area is the target. "
    "Rule (FIND THE COMPONENT WITH "
    "THE MOST HOLES — IE, MOST "
    "ENCLOSED BG-CELLS WITHIN ITS "
    "BBOX OR CONVEX HULL — TILE IT "
    "OR EMIT IT AS THE ANSWER PER "
    "DEMOS): For EACH motif: COMPUTE "
    "the number of HOLES (interior "
    "bg cells trapped within the "
    "motif's bbox/region). SELECT "
    "the motif with the MOST holes. "
    "CROP it to its bbox. TILE / "
    "EXPAND / EMIT per the rule's "
    "canonical output for this "
    "task. Net: most-holed motif "
    "is extracted and emphasized "
    "as the answer."
)

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
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


def _build_holed_motif(rng):
    """A connected motif with >=1 enclosed hole: a rectangular ring (varied dims)
    plus 0-3 orthogonal protrusions for shape variety. The enclosed interior
    guarantees the rule's hole-count is >=1, so this motif wins and its crop has
    interior 0s (the 2x2-tiled output is never a solid block)."""
    rh = rng.randint(3, 5); rw = rng.randint(3, 5)
    cells = set()
    for r in range(rh):
        for c in range(rw):
            if r in (0, rh - 1) or c in (0, rw - 1):
                cells.add((r, c))
    # add OUTWARD protrusions only — a cell landing in the interior would fill the
    # enclosed hole and defeat the whole point.
    for _ in range(rng.randint(0, 3)):
        base = rng.choice(list(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = base[0] + dr, base[1] + dc
        if 1 <= nr <= rh - 2 and 1 <= nc <= rw - 2:
            continue  # inside the ring's interior — would close the hole
        cells.add((nr, nc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for i, color in enumerate(colors):
            # the first motif is a holed ring (guaranteed unique most-holes
            # winner); the rest are small hole-free random motifs.
            cells = _build_holed_motif(rng) if i == 0 \
                else _build_motif(rng, rng.randint(3, 5))
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


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or seen[sr][sc]:
                continue
            col = grid[sr][sc]; stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == col):
                        seen[nr][nc] = True; stack.append((nr, nc))
            comps.append((col, cells))
    return comps


def _hole_count(cells):
    """Number of enclosed 0-regions in the cell set's bbox (4-conn, not touching
    the bbox border) — mirrors the rule's f14b-hole-count."""
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    H, W = r1 - r0 + 1, c1 - c0 + 1
    filled = {(r - r0, c - c0) for r, c in cells}
    seen = set(); holes = 0
    for sr in range(H):
        for sc in range(W):
            if (sr, sc) in filled or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]; seen.add((sr, sc)); region = []; touches = False
            while stack:
                r, c = stack.pop(); region.append((r, c))
                if r in (0, H - 1) or c in (0, W - 1):
                    touches = True
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < H and 0 <= nc < W and (nr, nc) not in filled
                            and (nr, nc) not in seen):
                        seen.add((nr, nc)); stack.append((nr, nc))
            if not touches:
                holes += 1
    return holes


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """The most-holed motif (the rule's pick, then 2x2-tiled) must have >=1 hole,
    so the tiled output contains interior 0s (never a solid single-color block)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components(grid)
    if len(comps) < 2:
        return [f"expected multiple motifs, found {len(comps)}"]
    best = max(comps, key=lambda cc: (_hole_count(cc[1]), len(cc[1])))
    if _hole_count(best[1]) < 1:
        return ["winning motif has no holes — 2x2-tiled output would be a solid "
                "single-color block (all_background)"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
