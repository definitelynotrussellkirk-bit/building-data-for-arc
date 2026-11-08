"""Generator for arc_puzzle_bank_seventh21:H47 — translate color-4 by marker vector.

REAL rule (the "gallery pack" docstring was WRONG): let v = (first color-2
cell) - (first color-1 cell). Translate every color-4 cell by v (dropping any
that leave the grid), then output a same-size grid with the BBOX of the moved
cells filled solid in color 4.

The old generator drew scattered random motifs, so the markers/payload were
incidental -> noisy, repetitive output (distinct=48, dup33%). This builds one
color-1 and one color-2 marker (the vector) plus a color-4 payload shape.

Combinatorial axes: grid size, the vector, the color-4 payload bbox/position.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "90745f7073da"
VERSION = "2.0.1"
TASK_ID = "90745f7073da"

SUMMARY = "0-bg grid with one color-1 marker and one color-2 marker (defining vector v = p2 - p1) plus a color-4 payload shape. Rule: translate the color-4 cells by v (dropping out-of-bounds), then fill the moved bbox solid with color 4. Output is input-sized. Grid size, vector and payload bbox/position vary."

INVARIANTS = [
    "background is 0",
    "exactly one color-1 marker and one color-2 marker",
    "a color-4 payload whose cells stay in-bounds after translation by v",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 color-1, exactly 1 color-2, and >=1 color-4."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_motifs", "single_motif", "all_same_color"):
        return errs
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    c4 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 4)
    if c1 != 1:
        errs.append(f"expected exactly 1 color-1 marker, found {c1}")
    if c2 != 1:
        errs.append(f"expected exactly 1 color-2 marker, found {c2}")
    if c4 < 1:
        errs.append("expected >=1 color-4 payload cells")
    return errs


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
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 9, 11)
        k_lo, k_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        k_lo, k_hi = 5, 9
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 10, 13)
        k_lo, k_hi = 4, 8
    rng = ctx.draw_rng("layout")

    for _outer in range(60):
        g = full_grid(h, w, 0)
        dr = rng.randint(-3, 3); dc = rng.randint(-3, 3)
        if dr == 0 and dc == 0:
            continue
        # color-4 payload: a random polyomino that stays in-bounds after +v
        shape = _build_motif(rng, rng.randint(k_lo, k_hi))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        if sh >= h or sw >= w:
            continue
        # placement bounds so shape AND shape+v are both inside the grid
        r_lo = max(0, -dr); r_hi = min(h - sh, h - sh - dr)
        c_lo = max(0, -dc); c_hi = min(w - sw, w - sw - dc)
        if r_lo > r_hi or c_lo > c_hi:
            continue
        r0 = rng.randint(r_lo, r_hi); c0 = rng.randint(c_lo, c_hi)
        cells = {(r0 + r, c0 + c) for r, c in shape}
        for r, c in cells:
            g[r][c] = 4
        # two markers: p1 (color 1), p2 = p1 + v (color 2), both off the payload
        placed = False
        for _ in range(120):
            pr = rng.randint(0, h - 1); pc = rng.randint(0, w - 1)
            qr, qc = pr + dr, pc + dc
            if not (0 <= qr < h and 0 <= qc < w):
                continue
            if (pr, pc) in cells or (qr, qc) in cells or (pr, pc) == (qr, qc):
                continue
            if g[pr][pc] != 0 or g[qr][qc] != 0:
                continue
            g[pr][pc] = 1; g[qr][qc] = 2; placed = True; break
        if placed:
            return g
    raise ValueError("could not realize translate-fill layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
