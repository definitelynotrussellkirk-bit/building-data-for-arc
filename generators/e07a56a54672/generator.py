"""Generator for v3_rich_schema:hard_02_scale_smallest_object_2x — scale smallest 2x.

Rule: 2 color-3 motifs of strictly different sizes; the smallest is scaled
2× (each cell → 2×2 block) and painted in color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: equal_sizes (both motifs same size → "smallest" is
ambiguous; tie-break by position is the only signal); single_motif
(only 1 motif → rule's "smallest of two" precondition fails);
no_motifs (empty grid → rule's selector finds nothing, output is empty).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e07a56a54672"
VERSION = "2.1.1"  # add executable self_check invariants + literal AXES for lintable valid domains; distinct-size motif behavior preserved
TASK_ID = "e07a56a54672"

SUMMARY = (
    "0-bg grid (h ∈ 9-14, w ∈ 11-16, "
    "by difficulty) with: EXACTLY TWO "
    "COLOR-3 (GREEN) CONNECTED MOTIFS "
    "of STRICTLY DIFFERENT SIZES — "
    "drawn from SIZE_PAIR (e.g., (2, 4) "
    "for easy/medium, (3, 6) for hard) "
    "shuffled, each motif built via "
    "_build_motif random adjacent-step "
    "walk, placed at non-overlapping "
    "positions via _free check (1-cell "
    "padding). Both motifs painted in "
    "COLOR 3 only. Retries up to 40 "
    "outer × 120 inner attempts. "
    "Rule (FIND THE SMALLER OF THE 2 "
    "COLOR-3 MOTIFS, SCALE IT 2× "
    "(EACH CELL → 2×2 BLOCK), "
    "RECOLOR THE SCALED COPY TO "
    "COLOR 8 (CYAN); LARGER MOTIF "
    "DISCARDED): EXTRACT both "
    "COLOR-3 components and compute "
    "their cell counts. SELECT the "
    "SMALLER one (with fewer cells). "
    "UPSCALE its cells by factor 2: "
    "each (r, c) in the original "
    "becomes a 2×2 BLOCK at "
    "(2r..2r+1, 2c..2c+1). PAINT "
    "every cell of the upscaled "
    "shape with COLOR 8 (cyan). "
    "OUTPUT the scaled cyan crop "
    "(on a fresh canvas sized to "
    "the scaled bbox). Net: "
    "smaller motif is enlarged "
    "and recolored cyan; larger "
    "motif is gone."
)

INVARIANTS = [
    "background is 0",
    "all non-zero cells are color 3",
    "exactly 2 separated color-3 motifs with strictly different sizes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("equal_sizes", "single_motif", "no_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "two_unequal_motifs",
                       "valid": "two_unequal_motifs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|equal_sizes|single_motif|no_motifs"},
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


def _components4(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the two unequal green-motif task."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    bad_values = sorted({v for row in grid for v in row if v not in (0, 3)})
    if bad_values:
        errs.append(f"expected only background 0 and motif color 3; found {bad_values}")
    comps = _components4(grid, 3)
    if len(comps) != 2:
        errs.append(f"expected exactly two 4-connected color-3 motifs; found {len(comps)}")
        return errs
    sizes = sorted(len(comp) for comp in comps)
    if sizes[0] == sizes[1]:
        errs.append(f"motifs must have strictly different sizes; found tie {sizes}")
    if sizes[0] < 2:
        errs.append(f"smaller motif should contain at least 2 cells; found {sizes[0]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        size_lo, size_hi = 2, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        size_lo, size_hi = 3, 8
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        size_lo, size_hi = 2, 6
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        # two STRICTLY DIFFERENT sizes (rule selects the smaller, scales 2x)
        sizes = list(rng.sample(range(size_lo, size_hi + 1), 2))
        rng.shuffle(sizes)
        ok = True
        for size in sizes:
            cells = _build_motif(rng, size)
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = 3
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    return g   # graceful fallback (last attempt); never raise


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "equal_sizes":
        # Both motifs same cell count → rule's "smallest" is
        # ambiguous; only positional tie-break decides which scales.
        for r, c in [(2, 2), (2, 3), (3, 3)]: g[r][c] = 3
        for r, c in [(6, 7), (6, 8), (7, 8)]: g[r][c] = 3
        return g
    if name == "single_motif":
        # Only one motif — rule's "smallest of two" precondition
        # fails; output's contrast (smallest scaled, largest kept)
        # collapses.
        for r, c in [(3, 3), (3, 4), (4, 4)]: g[r][c] = 3
        return g
    if name == "no_motifs":
        # Empty grid — rule's selector finds nothing.
        return g
    return g
