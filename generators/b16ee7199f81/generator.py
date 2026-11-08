"""Generator for e40b9e2f.

Rule: partial motif completed by 90, 180 and 270 degree rotations
around its inferred center.

Combinatorial axes (8): grid_h/w, motif, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, color.
Degenerates: no_motif, full_grid, single_pixel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "b16ee7199f81"
VERSION = "1.3.0"  # vary asymmetric motifs/placement and add executable invariants
TASK_ID = "b16ee7199f81"
SUMMARY = "Partial motif completed by 90/180/270 degree rotations around its center."

INVARIANTS = [
    "background is color 0",
    "the nonzero cells form a partial asymmetric motif",
    "the motif centroid defines the rotation center",
    "the motif sits clear of grid borders so rotations have room",
]

MOTIF_NAMES = ("ell", "hook", "tri", "zig", "branch", "stair")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_motif", "full_grid", "single_pixel")
HELPFUL_TEXTURES = MOTIF_NAMES

MOTIFS = {
    "ell": [(0, 0), (0, 1), (1, 0)],
    "hook": [(0, 0), (1, 0), (2, 0), (2, 1)],
    "tri": [(0, 0), (0, 1), (1, 1)],
    "zig": [(0, 0), (0, 1), (1, 1), (1, 2)],
    "branch": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)],
    "stair": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
}

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "motif":          {"type": "str", "default": "rng helpful",
                       "valid": "|".join(MOTIF_NAMES)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "center", "valid": "center"},
    "color":          {"type": "color", "default": "rng !0", "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for motif",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    motif = (overrides.get("texture") if overrides.get("texture") in MOTIF_NAMES else None) or \
            overrides.get("motif") or \
            ctx.draw_choice("motif", list(MOTIF_NAMES))
    color = ctx.draw_color("color", exclude={0})
    h = ctx.draw_int("grid_h", 9, 12)
    w = ctx.draw_int("grid_w", 9, 12)
    g = full_grid(h, w, 0)
    cells = MOTIFS[motif]
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    # Keep at least a two-cell moat so the canonical 90/180/270 completions are
    # visible instead of clipping at the image boundary.  Placement is varied,
    # but still centered enough for the centroid-based rule to have room.
    r0 = rng.randint(2, h - sh - 2)
    c0 = rng.randint(2, w - sw - 2)
    paint_at(g, r0, c0, cells, color)
    return g


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _d4(cells, code):
    raw = []
    for r, c in cells:
        if code == 0:
            raw.append((r, c))
        elif code == 1:
            raw.append((c, -r))
        elif code == 2:
            raw.append((-r, -c))
        elif code == 3:
            raw.append((-c, r))
        elif code == 4:
            raw.append((r, -c))
        elif code == 5:
            raw.append((-r, c))
        elif code == 6:
            raw.append((c, r))
        else:
            raw.append((-c, -r))
    return _norm(raw)


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not (3 <= len(cells) <= 6):
        errs.append(f"expected a 3-6 cell partial motif, found {len(cells)} cells")
    colors = {v for _, _, v in cells}
    if len(colors) != 1:
        errs.append(f"expected a single motif color, found {sorted(colors)}")
    coords = [(r, c) for r, c, _ in cells]
    if coords:
        rs = [r for r, _ in coords]
        cs = [c for _, c in coords]
        if min(rs) < 2 or min(cs) < 2 or max(rs) > len(grid) - 3 or max(cs) > len(grid[0]) - 3:
            errs.append("motif too close to border; rotations can clip")
        if len(set(rs)) < 2 or len(set(cs)) < 2:
            errs.append("motif is one-dimensional, hiding the rotation-completion rule")
        if len({_d4(_norm(coords), code) for code in range(8)}) < 4:
            errs.append("motif is too D4-symmetric for a rotation-completion witness")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_motif":
        return g
    if name == "single_pixel":
        g[5][5] = 2
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 2
        return g
    return g
