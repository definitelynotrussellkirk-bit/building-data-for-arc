"""Generator for arc_additional_puzzles_21_set10_bundle:M69.

Rule: among 3 distinct-color blobs of distinct sizes, crop the median-size
blob's bbox; if h>w, rotate it 90° clockwise.

Combinatorial axes (8): grid_h/w, palette_kind, num_blobs, size_spread,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: all_same_size, only_two_blobs, square_median.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "5be74762ea16"
VERSION = "2.1.0"  # reject square median bbox (was leaking square_median into normal data)
TASK_ID = "5be74762ea16"
SUMMARY = (
    "0-bg grid (h×w, ~9-11 by ~10-12) with exactly 3 connected "
    "BLOBS in distinct non-zero colors and STRICTLY DISTINCT "
    "cell counts (e.g., 2, 4, 8). Blobs 8-conn isolated. The "
    "MEDIAN-size blob (the middle one by cell count) has a NON-"
    "SQUARE bbox so the h>w branch is triggerable. Rule: sort "
    "blobs by cell count ascending. Pick the MIDDLE one (median). "
    "Crop to its bbox (preserving holes as 0). If bbox h > w, "
    "rotate the crop 90° clockwise. Else output as-is. Output = "
    "the (possibly rotated) cropped median blob."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 3 connected blobs in distinct non-zero colors",
    "blobs have strictly distinct sizes (unambiguous median)",
    "blobs are 8-conn isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("all_same_size", "only_two_blobs", "square_median")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_blobs":      {"type": "int", "default": "3", "valid": "3"},
    "size_spread":    {"type": "str", "default": "wide", "valid": "wide"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
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
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
    rng = ctx.draw_rng("layout")
    from puzzle_generators.helpers.blobs import grow_blob

    # 3 blobs of strictly distinct sizes
    sizes = sorted(rng.sample([2, 3, 4, 5, 6, 7, 8], 3))
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)

    for _outer in range(60):
        g = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        ok = True
        blob_cells = []
        for size, color in zip(sizes, colors):
            cells = grow_blob(rng, h, w, used, size, max_attempts=40)
            if cells is None:
                ok = False; break
            blob_cells.append(cells)
            for r, c in cells:
                g[r][c] = color
            # 8-conn buffer
            for r, c in cells:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            used.add((nr, nc))
        if ok:
            # sizes is sorted ascending, so blob_cells[1] is the median-size
            # object. A square median bbox is explicitly a DEGENERATE texture:
            # it hides the rotate-if-h>w branch and teaches only crop identity.
            med = blob_cells[1]
            rs = [r for r, _ in med]; cs = [c for _, c in med]
            if (max(rs) - min(rs)) == (max(cs) - min(cs)):
                continue
            return g
    raise ValueError("could not place 3 distinct-size blobs")


def _components_8conn(g):
    """List of (color, cells) for each 8-connected non-zero blob. Local + tiny so
    self_check carries no heavy import; mirrors objects-8 over non-bg cells."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or seen[r][c]:
                continue
            color = g[r][c]
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and g[nr][nc] != 0:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for ONE default instance. Encodes exactly the
    properties the v2.1.0 fix added — so a regression that lets a square median
    (or an ambiguous median) leak back into the normal path is caught at lint
    time, not by a downstream reviewer audit."""
    errs = []
    comps = _components_8conn(grid)
    if len(comps) != 3:
        errs.append(f"expected exactly 3 blobs, found {len(comps)}")
        return errs
    colors = [col for col, _ in comps]
    if len(set(colors)) != 3:
        errs.append(f"blob colors not distinct: {sorted(colors)}")
    sizes = sorted(len(cells) for _, cells in comps)
    if len(set(sizes)) != 3:
        errs.append(f"blob sizes not strictly distinct (ambiguous median): {sizes}")
        return errs
    # median = the blob whose size is the middle of the three
    med = sorted(comps, key=lambda cc: len(cc[1]))[1][1]
    rs = [r for r, _ in med]; cs = [c for _, c in med]
    if (max(rs) - min(rs)) == (max(cs) - min(cs)):
        errs.append("median bbox is SQUARE — h>w rotate branch unreachable "
                    "(square_median degenerate leaked into normal path)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "all_same_size":
        # All 3 same size — median is ambiguous
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 2)
        paint_at(g, 1, 6, [(0, 0), (0, 1), (1, 0)], 4)
        paint_at(g, h - 4, 3, [(0, 0), (0, 1), (1, 0)], 7)
        return g
    if name == "only_two_blobs":
        # 2 blobs — no median (the middle of an even count is undefined)
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 2)
        paint_at(g, h - 4, 1, [(0, 0), (0, 1), (0, 2), (1, 0)], 4)
        return g
    if name == "square_median":
        # Median bbox is square — h>w branch never triggers
        paint_at(g, 1, 1, [(0, 0)], 2)
        paint_at(g, 1, 4, [(0, 0), (0, 1), (1, 0), (1, 1)], 4)
        paint_at(g, h - 4, 1, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)], 7)
        return g
    return g
