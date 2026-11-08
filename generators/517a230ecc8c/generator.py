"""Generator for arc_puzzle_bank_21_set7_s:S7_M7 — one-step object halo.

Rule: every 0-cell whose 4-orthogonal neighbors are all 0 OR all the
same (single) non-zero color — gets painted that color. Effectively
expands each blob by 1 cell in 4 cardinals.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, blob_on_border, halo_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "517a230ecc8c"
VERSION = "2.1.0"  # guarantee the requested 2-3 blobs instead of silently underfilling
TASK_ID = "517a230ecc8c"
SUMMARY = (
    "0-bg grid (h~8-13, w~10-15) with 2-3 BLOBS "
    "of 2-4 cells each (4-connected, grown via "
    "grow_blob), each in a DISTINCT non-0 color "
    "drawn from {1..9}. Blobs are placed STRICTLY "
    "IN THE INTERIOR (excluding the outer border "
    "row/column — added to `used` set before "
    "growing) so their 1-step halos won't extend "
    "off-grid. Blobs are spaced apart by ≥2 cells "
    "(via 2-cell dilation check) so their halos "
    "do NOT touch each other or overlap. Rule "
    "(EXPAND EACH BLOB BY ONE CELL IN 4 "
    "CARDINALS — PAINT EACH HALO CELL ITS BLOB'S "
    "COLOR): for EACH bg-0 cell in the input: "
    "INSPECT its 4 ORTHOGONAL NEIGHBORS. IF all "
    "neighbors are 0 → leave the cell as bg-0; "
    "IF all NON-0 neighbors share the same color "
    "C and at least one neighbor is non-0 → PAINT "
    "this cell with C (the halo color). IF "
    "neighbors have multiple distinct non-0 "
    "colors → the rule is undefined (but the "
    "input is constructed so this never "
    "happens). The original blob cells stay "
    "their colors. Net: each blob is dilated by "
    "1 cell in the 4 cardinal directions, "
    "growing a single-cell halo around it."
)

INVARIANTS = [
    "background is 0",
    "blobs separated by ≥3 cells in 4-norm (dilated halos disjoint)",
    "blobs not on grid border (so halos stay in-bounds)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "blob_on_border", "halo_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "spaced_blobs_interior",
                       "valid": "spaced_blobs_interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 15)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    n = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    # Build whole layouts until every requested blob is placed.  The old code
    # accepted partial layouts after placement failures, so easy/default samples
    # usually contained only one blob and hid the multi-object halo rule.
    for _layout_attempt in range(120):
        g = full_grid(h, w, 0)
        blocked: set[tuple[int, int]] = set()
        placed = 0
        for color in palette:
            cells = _grow_blob_in_clear(rng, h, w, blocked, rng.randint(2, 4))
            if cells is None:
                break
            for r, c in cells:
                g[r][c] = color
            blocked |= _dilate(cells, h, w, radius=2)
            placed += 1
        if placed == n:
            return g
    # Deterministic, still helpful fallback: two separated interior dominoes.
    g = full_grid(max(h, 8), max(w, 10), 0)
    for r, c in ((2, 2), (2, 3)):
        g[r][c] = palette[0]
    for r, c in ((len(g) - 3, len(g[0]) - 4), (len(g) - 3, len(g[0]) - 3)):
        g[r][c] = palette[1]
    return g


def _dilate(cells, h, w, *, radius):
    out = set()
    for r, c in cells:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out.add((rr, cc))
    return out


def _grow_blob_in_clear(rng, h, w, blocked, target_size):
    """Grow a connected blob inside the grid interior and outside `blocked`."""
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                  if (r, c) not in blocked]
    if not candidates:
        return None
    for _ in range(160):
        seed = rng.choice(candidates)
        cells = {seed}
        frontier = [seed]
        while frontier and len(cells) < target_size:
            r, c = rng.choice(frontier)
            nbrs = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 1 <= r + dr < h - 1 and 1 <= c + dc < w - 1
                    and (r + dr, c + dc) not in blocked
                    and (r + dr, c + dc) not in cells]
            if not nbrs:
                frontier.remove((r, c))
                continue
            nb = rng.choice(nbrs)
            cells.add(nb)
            frontier.append(nb)
        if len(cells) == target_size:
            return cells
    return None


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no blobs to dilate; output equals input.
        return g
    if name == "blob_on_border":
        # Blob touches grid border — its halo would extend off-grid;
        # rule's expand-by-1 has no destination cells outside.
        for r, c in [(0, 0), (0, 1), (1, 0)]: g[r][c] = 4
        return g
    if name == "halo_overlap":
        # Two blobs of distinct colors so close that their 1-step
        # halos overlap on the same 0-cell — rule's "all same color"
        # neighborhood test produces ambiguous color for the overlap.
        for r, c in [(2, 2), (2, 3)]: g[r][c] = 4
        for r, c in [(2, 5), (2, 6)]: g[r][c] = 6
        return g
    return g


def _selfcheck_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                rr, cc = q.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append((color, cells))
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    comps = _selfcheck_components(grid)
    if not (2 <= len(comps) <= 3):
        errs.append(f"expected 2..3 separated blobs, got {len(comps)}")
    h, w = len(grid), len(grid[0])
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("blob colors should be distinct")
    for _, cells in comps:
        if not (2 <= len(cells) <= 4):
            errs.append("each blob should have 2..4 cells")
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
            errs.append("normal blobs should stay off the border")
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            neigh = {grid[r + dr][c + dc] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                     if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0}
            if len(neigh) > 1:
                errs.append("a zero halo cell sees multiple blob colors")
                return errs
    return errs
