"""Generator for 1d9f465ac56f — select object by (holes ∧ main-diag symmetry), upscale ×2.

Rule (from canonical Racket):
  For each connected object (4-conn, bg=0), examine its bbox crop.
  Filter: binary mask must have ≥1 hole (interior 0 cell in bbox)
  AND must be MAIN-DIAGONAL symmetric (bbox is square AND
  mask[r][c] == mask[c][r] for all r,c).
  Output: the first matching object's bbox crop, recolored 8, then
  upscaled ×2 (each cell → 2×2 block).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1d9f465ac56f"
VERSION = "3.0.1"  # distinct_out=10: target was chosen from a FIXED pool of 12 hardcoded masks (2 dupes -> ~10) and output is fully determined by the target mask. Now GENERATE diverse transpose-symmetric holed masks procedurally at varying sizes N=3..8 -> output 6x6..16x16 with many distinct hole patterns.
TASK_ID = "1d9f465ac56f"

SUMMARY = (
    "0-bg grid containing 3-5 connected motifs in distinct non-zero "
    "colors, placed with ≥1-cell buffer between them. EXACTLY ONE "
    "target motif satisfies all three properties: (a) its bbox is "
    "SQUARE (h==w); (b) its binary mask is symmetric along the main "
    "diagonal (mask[r][c] == mask[c][r]); (c) it contains ≥1 HOLE "
    "(at least one bg cell strictly inside the bbox, not on the "
    "outline). Other motifs (decoys) fail at least one of these "
    "properties. Rule: find the unique target. Crop it. Recolor all "
    "non-zero cells to color 8. Upscale ×2 (each cell → 2×2 block). "
    "Output size = 2*target_bbox_side per side."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-5 connected motifs in distinct non-zero colors",
    "exactly one motif is square + main-diag symmetric + has ≥1 hole (target)",
    "other motifs fail at least one of: square, diag-symmetric, has hole",
    "motifs placed with ≥1-cell buffer (no 8-neighborhood contact)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "two_targets", "no_target")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "9..22"},
    "grid_w":            {"type": "int", "default": "rng 11..14", "valid": "9..22"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "n_motifs":          {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "palette_size":      {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "scattered",
                          "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


# Target candidates: square, main-diag symmetric, ≥1 hole, connected.
# Each given as a 2D 0/1 mask. Validated by _validate_target below.
_TARGET_MASKS = [
    # 3x3 ring (1 hole)
    [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
    # 4x4 ring (4 holes)
    [[1, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]],
    # 5x5 ring (9 holes)
    [[1, 1, 1, 1, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 1],
     [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]],
    # 4x4 with diagonal extension into interior
    [[1, 1, 1, 1], [1, 1, 0, 1], [1, 0, 1, 1], [1, 1, 1, 1]],
    # 5x5 ring with diagonal
    [[1, 1, 1, 1, 1], [1, 1, 0, 0, 1], [1, 0, 1, 0, 1],
     [1, 0, 0, 1, 1], [1, 1, 1, 1, 1]],
    # 3x3 frame with one off-diag corner filled
    [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
    # 4x4 X-frame (diagonals + sides)
    [[1, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]],
    # 5x5 with cross-hole (connected outer + 4 inner-corners pull-in)
    [[1, 1, 1, 1, 1], [1, 1, 0, 1, 1], [1, 0, 0, 0, 1],
     [1, 1, 0, 1, 1], [1, 1, 1, 1, 1]],
    # 6x6 ring
    [[1, 1, 1, 1, 1, 1], [1, 0, 0, 0, 0, 1], [1, 0, 0, 0, 0, 1],
     [1, 0, 0, 0, 0, 1], [1, 0, 0, 0, 0, 1], [1, 1, 1, 1, 1, 1]],
    # 4x4 with two diagonal holes
    [[1, 1, 1, 1], [1, 0, 1, 1], [1, 1, 0, 1], [1, 1, 1, 1]],
    # 5x5 with one anti-diag hole pair
    [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 0, 1, 1],
     [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]],
    # 6x6 with diag chain holes
    [[1, 1, 1, 1, 1, 1], [1, 0, 1, 1, 0, 1], [1, 1, 0, 1, 1, 1],
     [1, 1, 1, 0, 1, 1], [1, 0, 1, 1, 0, 1], [1, 1, 1, 1, 1, 1]],
]


def _validate_target(mask):
    """Verify mask is square, main-diag symmetric, ≥1 hole, connected."""
    h = len(mask); w = len(mask[0]) if mask else 0
    if h != w or h < 3:
        return False
    # main-diag symmetric
    for r in range(h):
        for c in range(w):
            if mask[r][c] != mask[c][r]:
                return False
    # ≥1 hole (any cell strictly inside bbox that is 0; "inside" = at least
    # one neighbor on each of 4 sides is on cells of the mask)
    # We use the canonical rule interpretation: a bbox interior 0-cell.
    holes = 0
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if mask[r][c] == 0:
                holes += 1
    if holes < 1:
        return False
    # connected
    cells = [(r, c) for r in range(h) for c in range(w) if mask[r][c]]
    if not cells:
        return False
    stack = [cells[0]]
    seen = {cells[0]}
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in seen:
                continue
            if 0 <= nr < h and 0 <= nc < w and mask[nr][nc]:
                seen.add((nr, nc)); stack.append((nr, nc))
    return len(seen) == len(cells)


# Pre-validate target list and keep only the valid ones (kept as a fallback seed).
_TARGET_MASKS = [m for m in _TARGET_MASKS if _validate_target(m)]


def _make_target_mask(rng, nmin, nmax):
    """Procedurally build a DIVERSE square, main-diag-symmetric, holed,
    connected mask. Start from the full border ring (always valid) then add
    random symmetric interior pairs (each adjacent to existing structure for
    connectivity), leaving >=1 interior hole. Validated before return."""
    for _ in range(80):
        n = rng.randint(nmin, nmax)
        mask = [[0] * n for _ in range(n)]
        for i in range(n):
            mask[0][i] = mask[n - 1][i] = mask[i][0] = mask[i][n - 1] = 1  # border ring
        interior = [(r, c) for r in range(1, n - 1) for c in range(1, n - 1)]
        rng.shuffle(interior)
        # add symmetric interior pairs, keeping >=1 hole; force >=1 pair when the
        # interior is big enough (N>=4) so most targets aren't plain rings
        maxadd = max(0, (len(interior) - 1) // 2)
        n_add = rng.randint(min(1, maxadd), maxadd) if maxadd > 0 else 0
        added = 0
        for (r, c) in interior:
            if added >= n_add:
                break
            if mask[r][c] == 1:
                continue
            if any(0 <= r + dr < n and 0 <= c + dc < n and mask[r + dr][c + dc] == 1
                   for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                mask[r][c] = 1; mask[c][r] = 1; added += 1   # keep transpose symmetry
        if _validate_target(mask):
            return mask
    return [[1, 1, 1], [1, 0, 1], [1, 1, 1]]   # fallback 3x3 ring


def _make_decoy_mask(rng, kind):
    """Build a decoy mask that FAILS at least one property."""
    if kind == "non_square":
        # rectangular non-square shape
        h = rng.randint(2, 4)
        w = h + rng.randint(1, 2)
        # ensure connected: a plus or L
        mask = [[0] * w for _ in range(h)]
        cells = [(0, 0)]
        while len(cells) < rng.randint(3, h * w - 1):
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells:
                cells.append((nr, nc))
        for r, c in cells:
            mask[r][c] = 1
        return mask
    if kind == "square_no_hole":
        # filled square (no interior 0) — symmetric but no hole
        sz = rng.randint(2, 4)
        return [[1] * sz for _ in range(sz)]
    if kind == "square_asym":
        # square with hole but NOT diag-symmetric
        sz = rng.randint(3, 4)
        # build a connected shape with a hole, then break symmetry
        for _ in range(40):
            mask = [[0] * sz for _ in range(sz)]
            # outline + 1 internal cell offset
            for i in range(sz):
                mask[0][i] = 1; mask[sz - 1][i] = 1
                mask[i][0] = 1; mask[i][sz - 1] = 1
            # punch asymmetric defect: remove a non-diagonal-pair cell
            r0, c0 = rng.choice([(0, 1), (1, 0), (0, sz - 2), (sz - 2, 0)])
            if mask[r0][c0] == 1 and mask[c0][r0] == 1:
                # remove one but not the diagonal pair, creating asymmetry
                mask[r0][c0] = 0
                # check: must still be connected, ≥1 hole, asymmetric
                if sz < 3:
                    continue
                holes = sum(1 for r in range(1, sz - 1) for c in range(1, sz - 1)
                            if mask[r][c] == 0)
                if holes < 1:
                    continue
                # check NOT diag-symmetric
                sym = all(mask[r][c] == mask[c][r]
                          for r in range(sz) for c in range(sz))
                if sym:
                    continue
                # check connected
                cells = [(r, c) for r in range(sz) for c in range(sz) if mask[r][c]]
                if not cells:
                    continue
                stack = [cells[0]]; seen = {cells[0]}
                while stack:
                    r, c = stack.pop()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in seen: continue
                        if 0 <= nr < sz and 0 <= nc < sz and mask[nr][nc]:
                            seen.add((nr, nc)); stack.append((nr, nc))
                if len(seen) != len(cells):
                    continue
                return mask
        return _make_decoy_mask(rng, "square_no_hole")
    # fallback simple plus shape (square 3x3 but no hole if center=1)
    return [[0, 1, 0], [1, 1, 1], [0, 1, 0]]


def _free(g, cells_abs, h, w):
    cell_set = set(cells_abs)
    for r, c in cells_abs:
        if not (0 <= r < h and 0 <= c < w):
            return False
        if g[r][c] != 0:
            return False
    for r, c in cells_abs:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if g[nr][nc] != 0 and (nr, nc) not in cell_set:
                        return False
    return True


def _mask_to_cells(mask, r0, c0):
    return [(r0 + r, c0 + c) for r in range(len(mask))
            for c in range(len(mask[0])) if mask[r][c]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_motifs = 3; nmin, nmax = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22)
        w = ctx.draw_int("grid_w", 16, 22)
        n_motifs = ctx.draw_int("n_motifs", 4, 6); nmin, nmax = 4, 8
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_motifs = ctx.draw_int("n_motifs", 3, 4); nmin, nmax = 3, 6
    rng = ctx.draw_rng("layout")

    for outer in range(80):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_motifs)
        # the rule outputs the unique (square + diag-symmetric + holed) object
        # upscaled x2, so the target mask determines the output -> generate a
        # DIVERSE one each time (was a fixed 12-mask pool -> distinct_out=10).
        target_mask = _make_target_mask(rng, nmin, nmax)
        target_cells_local = _mask_to_cells(target_mask, 0, 0)
        sh, sw = len(target_mask), len(target_mask[0])
        target_placed = False
        for _ in range(120):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            cells_abs = [(r0 + r, c0 + c) for r, c in target_cells_local]
            if not _free(g, cells_abs, h, w):
                continue
            for r, c in cells_abs:
                g[r][c] = colors[0]
            target_placed = True
            target_anchor = r0
            break
        if not target_placed:
            continue
        # decoys
        all_ok = True
        decoy_kinds = ["non_square", "square_no_hole", "square_asym"]
        for color in colors[1:]:
            kind = rng.choice(decoy_kinds)
            mask = _make_decoy_mask(rng, kind)
            dh, dw = len(mask), len(mask[0])
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - dh)
                c0 = rng.randint(0, w - dw)
                cells_abs = _mask_to_cells(mask, r0, c0)
                if not _free(g, cells_abs, h, w):
                    continue
                for r, c in cells_abs:
                    g[r][c] = color
                placed = True
                break
            if not placed:
                all_ok = False
                break
        if all_ok:
            return g
    raise ValueError("could not realize target + decoy layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 distinct non-bg motif colors; >=1 non-bg cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct non-bg colors (target + distractors), found {len(colors)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "two_targets":
        # two rings — rule picks the FIRST one, but the puzzle is
        # ambiguous (multiple valid targets)
        for r in range(3):
            for c in range(3):
                if (r, c) != (1, 1):
                    g[1 + r][1 + c] = 4
        for r in range(3):
            for c in range(3):
                if (r, c) != (1, 1):
                    g[7 + r][7 + c] = 6
        return g
    if name == "no_target":
        # only decoys — rule has nothing to output
        for r, c in [(2, 2), (2, 3), (3, 2), (3, 3)]:
            g[r][c] = 4  # filled square (no hole)
        for r, c in [(7, 7), (8, 7), (8, 8), (9, 7)]:
            g[r][c] = 6  # non-square L
        return g
    return g
