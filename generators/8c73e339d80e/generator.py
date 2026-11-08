"""Generator for arc_puzzle_bank_21_set10_s:S10_H2 — rotate-stamp at color-1 markers.

Rule: a base shape in some color + color-1 markers; the base is rotated by
each marker's neighbor rotation code and stamped at the marker.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_base, no_markers, no_rotation_codes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8c73e339d80e"
VERSION = "2.0.1"
TASK_ID = "8c73e339d80e"

SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) with: (a) one BASE motif in "
    "color 3 (green), 3-4 cells, placed in the upper-left "
    "region; (b) 2-3 MARKER PAIRS in the right region: each "
    "pair = a CODE cell (color in {2, 4, 6, 9}) immediately to "
    "the LEFT of a color-1 (blue) MARKER cell. Rule: extract "
    "base = normalized cells of color 3. For each color-1 "
    "marker at (r, c), look at code = g[r][c-1]. Decode code → "
    "rotation count: 2→0, 4→1, 6→2, 9→3. Rotate base CW that "
    "many times. Stamp the rotated base at the marker position "
    "(anchor at marker's (r, c)), painted color 8 (cyan). "
    "Original base, markers, codes all replaced by 0 in output "
    "except where stamped cells overwrite."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-3 connected motif (3-5 cells)",
    "2-3 color-1 markers each with a color-2/4/6/9 code cell to the LEFT",
    "stamped rotations stay in bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_base", "no_markers", "no_rotation_codes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "base_upper_left_markers_right",
                       "valid": "base_upper_left_markers_right"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..4"},
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


def _rotation_is_visible(cells, code):
    """Whether this code changes the normalized base's occupied cells."""
    turned = cells
    for _ in range({2: 0, 4: 1, 6: 2, 9: 3}[code]):
        turned = [(c, -r) for r, c in turned]
    return set(_selfcheck_norm(turned)) != set(_selfcheck_norm(cells))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n_markers", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_markers", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        n = ctx.draw_int("n_markers", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        cells = _build_motif(rng, rng.randint(3, 4))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        placed = False
        for _ in range(80):
            r0 = rng.randint(0, max(0, h // 2 - sh - 1))
            c0 = rng.randint(0, max(0, w // 3 - sw))
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
            for r, c in cells:
                g[r0 + r - min(rs)][c0 + c - min(cs)] = 3
            placed = True; break
        if not placed:
            continue
        base_norm = [(r - min(rs), c - min(cs)) for r, c in cells]
        base_h = max(r for r, _ in base_norm) + 1
        base_w = max(c for _, c in base_norm) + 1
        reserved = set()
        ok = True
        visible_rotation = False
        for _ in range(n):
            placed_m = False
            codes = [2, 4, 6, 9]
            rng.shuffle(codes)
            for code in codes:
                rot = {2: 0, 4: 1, 6: 2, 9: 3}[code]
                stamp_h, stamp_w = ((base_h, base_w) if rot % 2 == 0 else (base_w, base_h))
                max_code_c = w - stamp_w - 1  # marker is at code_c+1 and anchors the stamp
                if max_code_c < max(0, w // 3):
                    continue
                for _t in range(120):
                    r = rng.randint(0, h - stamp_h)
                    code_c = rng.randint(max(0, w // 3), max_code_c)
                    marker_c = code_c + 1
                    stamp_cells = {(rr, cc)
                                   for rr in range(r, r + stamp_h)
                                   for cc in range(marker_c, marker_c + stamp_w)}
                    pair_cells = {(r, code_c), (r, marker_c)}
                    cand = stamp_cells | pair_cells
                    if cand & reserved:
                        continue
                    if any(g[rr][cc] != 0 for rr, cc in cand):
                        continue
                    g[r][code_c] = code
                    g[r][marker_c] = 1
                    visible_rotation |= _rotation_is_visible(base_norm, code)
                    reserved |= cand
                    placed_m = True
                    break
                if placed_m:
                    break
            if not placed_m:
                ok = False; break
        # Symmetric bases and identity-only choices can make every code inert.
        # Keep partial symmetries when an actual selected code remains visible.
        if ok and visible_rotation:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_base":
        # Markers but no color-3 base — rule has nothing to stamp.
        g[5][6] = 2; g[5][7] = 1
        return g
    if name == "no_markers":
        # Base but no color-1 markers — rule has no anchors.
        g[1][1] = 3; g[1][2] = 3; g[2][1] = 3
        return g
    if name == "no_rotation_codes":
        # Markers without adjacent rotation codes — rule has no rotation count.
        g[1][1] = 3; g[1][2] = 3; g[2][1] = 3
        g[5][5] = 1; g[5][8] = 1
        return g
    return g


def _selfcheck_norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    base = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if len(base) < 3:
        errors.append(f"expected a nontrivial color-3 base motif, found {len(base)} cells")
        return errors
    nbase = _selfcheck_norm(base)
    bh = max(r for r, _ in nbase) + 1
    bw = max(c for _, c in nbase) + 1
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    lo, hi = ((1, 2) if difficulty == "easy" else (3, 4) if difficulty == "hard" else (2, 3))
    if not (lo <= len(markers) <= hi):
        errors.append(f"expected {lo}..{hi} color-1 markers, found {len(markers)}")
    for r, c in markers:
        if c == 0 or grid[r][c - 1] not in (2, 4, 6, 9):
            errors.append(f"marker at {(r, c)} lacks a valid left rotation code")
            continue
        code = grid[r][c - 1]
        rot = {2: 0, 4: 1, 6: 2, 9: 3}[code]
        rh, rw = ((bh, bw) if rot % 2 == 0 else (bw, bh))
        if r + rh > h or c + rw > w:
            errors.append(f"stamp for marker {(r, c)} with code {code} would leave the grid")
    return errors

