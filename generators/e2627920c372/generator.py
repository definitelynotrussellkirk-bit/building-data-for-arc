"""Generator for arc_additional_puzzle_bank_volume16:H108.

Rule: a control marker selects a transform of the blue source shape
stamped at the maroon anchor.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_control, no_anchor, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e2627920c372"
VERSION = "2.1.0"  # source shape + anchor were FIXED; only the control code (2/3/4/6) varied -> uniq 58%, distinct 83. Rule transforms the color-1 source per code (2=id,3=rot90,4=reflect-h,6=reflect-v) and stamps it (color 8) at the color-9 anchor. Now random asymmetric source + random anchor + all 4 codes.
TASK_ID = "e2627920c372"
SUMMARY = "Random color-1 source shape + a control marker (2=id,3=rot90,4=reflect-h,6=reflect-v) + a color-9 anchor; the rule stamps the transformed source (color 8) at the anchor."

INVARIANTS = [
    "one blue source shape is present",
    "one control marker is 2, 3, 4, or 6",
    "one maroon anchor marks the normalized stamp position",
    "the transformed copy stays inside the grid",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_control", "no_anchor", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _rot90(cells):
    hh = max(r for r, _ in cells) + 1
    return _norm([(c, hh - 1 - r) for r, c in cells])


def _reflect_h(cells):
    hh = max(r for r, _ in cells) + 1
    return _norm([(hh - 1 - r, c) for r, c in cells])


def _reflect_v(cells):
    ww = max(c for _, c in cells) + 1
    return _norm([(r, ww - 1 - c) for r, c in cells])


def _apply(code, cells):
    cells = _norm(cells)
    if code == 2:
        return cells
    if code == 3:
        return _rot90(cells)
    if code == 4:
        return _reflect_h(cells)
    return _reflect_v(cells)              # code 6


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
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 12, 14); ksz = (4, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 15, 20); ksz = (5, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 12, 17); ksz = (4, 5)
    rng = ctx.draw_rng("layout")

    for _attempt in range(1000):
        source = _poly(rng, rng.randint(*ksz))
        sh = max(r for r, _ in source) + 1; sw = max(c for _, c in source) + 1
        control = rng.choice([2, 3, 4, 6])
        trans = _apply(control, source)
        # Non-identity controls must visibly change the normalized source. The
        # old default frequently emitted symmetric shapes where rot/reflect was
        # indistinguishable from identity, hiding the very control-code branch the
        # demos are meant to teach.
        if control != 2 and trans == _norm(source):
            continue
        th = max(r for r, _ in trans) + 1; tw = max(c for _, c in trans) + 1

        g = full_grid(h, w, 0)
        # place source (color 1), not covering (0,0) where control sits
        sr = rng.randint(0, h - sh); sc = rng.randint(0, w - sw)
        scells = {(sr + r, sc + c) for r, c in source}
        if (0, 0) in scells:
            continue
        # place anchor so the transformed stamp fits and clears source + control
        ok = False
        for _ in range(80):
            ar = rng.randint(0, h - th); ac = rng.randint(0, w - tw)
            stamp = {(ar + r, ac + c) for r, c in trans}
            if ((ar, ac) == (0, 0) or (0, 0) in stamp
                    or stamp & scells or (ar, ac) in scells):
                continue
            ok = True
            break
        if not ok:
            continue
        for (r, c) in scells:
            g[r][c] = 1
        g[0][0] = control
        g[ar][ac] = 9
        return g
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 13, 0)
    if name == "no_control":
        for dr, dc in [(0, 0), (1, 0), (2, 0), (2, 1)]:
            g[1 + dr][1 + dc] = 1
        g[1][8] = 9
        return g
    if name == "no_anchor":
        for dr, dc in [(0, 0), (1, 0), (2, 0), (2, 1)]:
            g[1 + dr][1 + dc] = 1
        g[8][1] = 2
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(13):
                g[r][c] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Assert the control/anchor/source layout teaches a visible transform."""
    errs = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    controls = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
                if v in (2, 3, 4, 6)]
    # In default examples the control is deliberately placed at (0,0), away from
    # the source/anchor, so there should be exactly one such marker.
    if len(controls) != 1:
        errs.append(f"expected exactly one control marker in {{2,3,4,6}}, found {len(controls)}")
        return errs
    cr, cc, control = controls[0]
    if (cr, cc) != (0, 0):
        errs.append("default control marker should be at (0,0)")
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(anchors) != 1:
        errs.append(f"expected exactly one color-9 anchor, found {len(anchors)}")
    source_abs = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if len(source_abs) < 4:
        errs.append("source shape must contain at least four color-1 cells")
        return errs
    mr = min(r for r, _ in source_abs); mc = min(c for _, c in source_abs)
    source = _norm([(r - mr, c - mc) for r, c in source_abs])
    trans = _apply(control, source)
    if control != 2 and trans == source:
        errs.append("non-identity control must visibly change the normalized source shape")
    if anchors:
        ar, ac = anchors[0]
        for dr, dc in trans:
            if not (0 <= ar + dr < h and 0 <= ac + dc < w):
                errs.append("transformed stamp must fit inside the grid at the anchor")
                break
            if grid[ar + dr][ac + dc] == 1:
                errs.append("transformed stamp must not overlap the source shape")
                break
    return errs
