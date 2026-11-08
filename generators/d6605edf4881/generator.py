"""Generator for arc_additional_puzzle_bank_volume4:M27 — Transpose-within-bbox per object.

Rule: for each object, paint its cells at transposed positions
(swap r/c offsets within the bbox). Output unions original + transpose.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: symmetric_blobs, square_blobs, blobs_off_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob, bbox_of, bbox_overlaps

GENERATOR_ID = "d6605edf4881"
VERSION = "2.1.1"  # FIX: require all requested blobs to place; 2.1.0 could silently underfill while still having one asymmetric blob.
TASK_ID = "d6605edf4881"
SUMMARY = (
    "0-bg grid (h, w~9-12) with 2-4 "
    "NON-TOUCHING BLOBS, each in a "
    "DISTINCT color drawn from 1..9 "
    "(shuffled), each of size 3-6 cells "
    "(4-conn random growth). Blobs are "
    "BBOX-ISOLATED (no bbox overlap with "
    "each other) and at least one blob "
    "is ASYMMETRIC (differs from its "
    "diagonal transpose). For each blob, "
    "the bbox transpose-within-grid is "
    "validated to fit in bounds. Rule "
    "(TRANSPOSE-WITHIN-BBOX UNION): for "
    "EACH BLOB, COMPUTE its BBOX "
    "(r1, c1, r2, c2). For each cell "
    "(r, c) of the blob, its TRANSPOSED "
    "POSITION within the bbox is "
    "(r1 + (c - c1), c1 + (r - r1)) — "
    "i.e., swap row and column OFFSETS "
    "from bbox top-left. PAINT both the "
    "original blob cells AND their "
    "transposed positions with the "
    "blob's COLOR. UNION the original "
    "and transposed cells. Other "
    "0-cells stay 0. Net: each blob "
    "gains its bbox-local diagonal-"
    "transpose copy in the same color."
)

INVARIANTS = [
    "between 2 and 4 non-touching blobs",
    "blobs are bbox-isolated",
    "at least one blob differs from its transpose (asymmetric)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("symmetric_blobs", "square_blobs", "blobs_off_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread_asymmetric_blobs",
                       "valid": "spread_asymmetric_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_blobs = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_blobs = 4
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n_blobs = ctx.draw_int("n_blobs", 2, 4)
    rng = ctx.draw_rng("layout")
    for _attempt in range(40):
        g = full_grid(h, w, 0)
        colors = list(range(1, 10)); rng.shuffle(colors)
        used = set(); bboxes = []
        placed = 0
        placed_asym = False
        for i in range(n_blobs):
            size = rng.randint(3, 6)
            for _ in range(12):
                blob = grow_blob(rng, h, w, used, size)
                if blob is None: continue
                bb = bbox_of(blob)
                if any(bbox_overlaps(bb, ob) for ob in bboxes): continue
                r1, c1, r2, c2 = bb
                bh = r2-r1+1; bw = c2-c1+1
                if r1 + bw - 1 >= h or c1 + bh - 1 >= w: continue
                # Force the FIRST blob to be asymmetric (differs from its
                # within-bbox transpose) so the rule's transpose-union changes
                # something; later blobs may be anything.
                if i == 0 and not _is_asym(blob):
                    continue
                used |= blob; bboxes.append(bb)
                for r, c in blob: g[r][c] = colors[i % len(colors)]
                placed += 1
                if _is_asym(blob):
                    placed_asym = True
                break
        if placed == n_blobs and placed_asym:
            return g
    raise ValueError("could not place an asymmetric (non-transpose-symmetric) blob")


def _is_asym(blob):
    """A blob whose within-bbox transpose is NOT equal to itself (the rule's
    transpose-union will add/move cells -> visible change)."""
    r1 = min(r for r, _ in blob); c1 = min(c for _, c in blob)
    trans = {(r1 + (c - c1), c1 + (r - r1)) for r, c in blob}
    return trans != set(blob)


def self_check(grid, *, difficulty=None, meta=None):
    """At least one object must differ from its within-bbox transpose (so the
    rule's transpose-union visibly changes the grid). Returns a list of
    violations (empty == pass)."""
    h, w = len(grid), len(grid[0])
    seen = set(); n_obj = 0; any_asym = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                            and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            n_obj += 1
            if _is_asym(cells):
                any_asym = True
    msgs = []
    min_objs = 4 if difficulty == "hard" else 2
    if n_obj < min_objs:
        msgs.append(f"expected at least {min_objs} blobs, got {n_obj}")
    if not any_asym:
        msgs.append("no asymmetric blob -> transpose-union is identity")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "symmetric_blobs":
        # all blobs are transpose-symmetric → rule's union is identity, no visible change
        # 2x2 solid square has equal h/w and is transpose-symmetric
        for (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]: g[r][c] = 4
        # diagonal-symmetric L
        for (r, c) in [(5, 5), (6, 5), (5, 6)]: g[r][c] = 6
        return g
    if name == "square_blobs":
        # solid square blobs → transpose within bbox is identity for solids
        for r in range(1, 4):
            for c in range(1, 4): g[r][c] = 4
        for r in range(6, 9):
            for c in range(6, 9): g[r][c] = 6
        return g
    if name == "blobs_off_grid":
        # blob bbox transpose would land outside grid → rule has nowhere to paint
        # Place a tall thin blob that would need a wide bbox after transpose
        for r in range(1, 8): g[r][9] = 4   # 7-tall column at right edge
        return g
    return g
