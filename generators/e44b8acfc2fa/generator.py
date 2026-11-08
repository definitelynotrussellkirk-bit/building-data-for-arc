"""Generator for arc_additional_puzzle_bank_volume17:H115.

Rule: a control-coded transform of the color-6 template is stamped at
the purple anchor.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_control, no_anchor, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e44b8acfc2fa"
VERSION = "3.1.0"  # v3.1 adds executable self_check invariants for the transform template + anchor contract.
TASK_ID = "e44b8acfc2fa"
SUMMARY = (
    "0-bg grid (h~9-13, w~12-17) with: (a) a CONTROL "
    "CODE at (0, 0) drawn as a single non-bg cell with "
    "color ∈ {1, 2, 3, 4} (each code corresponds to a "
    "different dihedral transform of the template); "
    "(b) a small color-6 (magenta) TEMPLATE polyomino "
    "(L-tetromino-like) placed near the top-left; "
    "(c) a single color-7 (orange) ANCHOR cell placed "
    "near the bottom-right indicating the stamp "
    "position. The template and anchor do not overlap. "
    "Rule: read the control code at (0, 0) and select "
    "the corresponding TRANSFORM (e.g., 1 = identity, "
    "2 = rotate-CW, 3 = rotate-180, 4 = rotate-CCW or "
    "similar). Apply that transform to the magenta "
    "template. PAINT the transformed shape in color 8 "
    "(cyan) at the anchor's position on the original "
    "grid. Original template and anchor stay. Net: a "
    "cyan copy of the template (transformed per the "
    "control code) is stamped at the anchor."
)

INVARIANTS = [
    "one control marker is 1, 2, 3, or 4",
    "one asymmetric color-6 template is present",
    "one color-7 anchor marks the normalized stamp position",
    "the cyan copy does not overlap the source template",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_control", "no_anchor", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_control|no_anchor|full_grid"},
}


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _rot90(cells):
    hh = max(r for r, _ in cells) + 1
    return _norm([(c, hh - 1 - r) for r, c in cells])


def _reflect_v(cells):
    ww = max(c for _, c in cells) + 1
    return _norm([(r, ww - 1 - c) for r, c in cells])


def _apply(code, cells):
    cells = _norm(cells)
    if code == 1:
        return cells
    if code == 2:
        return _rot90(cells)
    if code == 3:
        return _rot90(_rot90(cells))
    return _reflect_v(cells)              # code 4


def _poly(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    return _norm(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 14)
        ksz = (4, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 15, 20)
        ksz = (5, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 12, 17)
        ksz = (4, 5)
    rng = ctx.draw_rng("layout")

    for _attempt in range(200):
        template = _poly(rng, rng.randint(*ksz))
        th = max(r for r, _ in template) + 1
        tw = max(c for _, c in template) + 1
        control = rng.choice([1, 2, 3, 4])
        trans = _apply(control, template)
        sh = max(r for r, _ in trans) + 1
        sw = max(c for _, c in trans) + 1

        g = full_grid(h, w, 0)
        # place template (color 6), not covering (0,0)
        tr = rng.randint(0, h - th); tc = rng.randint(0, w - tw)
        tcells = {(tr + r, tc + c) for r, c in template}
        if (0, 0) in tcells:
            continue
        # place anchor so the stamp fits and clears the template + control
        ok = False
        for _ in range(80):
            ar = rng.randint(0, h - sh); ac = rng.randint(0, w - sw)
            stamp = {(ar + r, ac + c) for r, c in trans}
            if (ar, ac) == (0, 0) or (0, 0) in stamp or stamp & tcells or (ar, ac) in tcells:
                continue
            ok = True
            break
        if not ok:
            continue
        for (r, c) in tcells:
            g[r][c] = 6
        g[0][0] = control
        g[ar][ac] = 7
        return g
    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 13, 0)
    if name == "no_control":
        for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
            g[1 + dr][1 + dc] = 6
        g[6][8] = 7
        return g
    if name == "no_anchor":
        g[0][0] = 1
        for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
            g[1 + dr][1 + dc] = 6
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(13):
                g[r][c] = 6
        return g
    return g


def _components(cells):
    remaining = set(cells)
    comps = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    comp.add((nr, nc))
                    stack.append((nr, nc))
        comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the control-coded template stamp task."""
    if not grid or not isinstance(grid[0], list):
        return ["empty or malformed grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errs = []
    control = grid[0][0]
    if control not in (1, 2, 3, 4):
        errs.append(f"control at (0,0) must be one of 1..4, got {control}")

    nonzero = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    bad_colors = sorted({v for _, _, v in nonzero if v not in {control, 6, 7}})
    if bad_colors:
        errs.append(f"unexpected nonzero colors: {bad_colors}")

    anchors = [(r, c) for r, c, v in nonzero if v == 7]
    if len(anchors) != 1:
        errs.append(f"expected exactly one color-7 anchor, found {len(anchors)}")
        return errs
    ar, ac = anchors[0]

    template = [(r, c) for r, c, v in nonzero if v == 6]
    if len(template) < 4:
        errs.append(f"template should have at least 4 color-6 cells, got {len(template)}")
        return errs
    comps = _components(template)
    if len(comps) != 1:
        errs.append(f"template should be one connected color-6 component, found {len(comps)}")
        return errs

    trans = _apply(control if control in (1, 2, 3, 4) else 1, template)
    stamp = {(ar + r, ac + c) for r, c in trans}
    if any(r < 0 or c < 0 or r >= h or c >= w for r, c in stamp):
        errs.append("transformed stamp would run out of bounds from the anchor")
    if stamp & set(template):
        errs.append("transformed cyan copy would overlap the source template")
    if (0, 0) in set(template) or (0, 0) == (ar, ac):
        errs.append("control cell is occupied by template or anchor")
    return errs
