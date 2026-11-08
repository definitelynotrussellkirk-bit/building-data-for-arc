"""Generator for arc_puzzle_bank_nineteenth21:H127.

The first two panels show a shape transform plus a consistent color map. The
third panel is transformed and recolored by the learned relation.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers (no color-5 separator columns → rule
cannot identify panels); identity_transform (panel 2 == panel 1
→ t = identity, output = query unchanged); identity_recolor
(target_colors == source_colors → no recolor mapping, output
shape only).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "155cf6b30713"
# 1.4.0: reverse-diversity -- panels were fixed 4x4 (shape-locked). The rule's
# split-panels-row uses (cols-2)//3 panel width and grid rows for height, so it
# handles any square panel size. Now vary panel size 4..6 and generate random
# cells per panel programmatically (was fixed cell banks). Breaks shape-lock.
VERSION = "1.5.0"  # add D4-unique witnesses, fix degenerate override crash, add self_check
TASK_ID = "155cf6b30713"
SUMMARY = "Infer dihedral transform + color mapping from panels 1→2; apply both to query panel 3; output is 4×4."

# Grid is fixed at 4×14 by rule (three 4×4 panels + 2 dividers).
# Diversity lives in cell patterns + transforms + color mappings.
#
# Rivals: 'use identity transform' refuted by ≥2 demos with different
# transform codes. 'use source colors in output' refuted by ≥2 demos
# with different mappings. 'output equals query unchanged' refuted by
# ≥1 demo where transform is observable.
# 4 demos covering ≥2 transform codes + varied cell patterns.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the input has three square panels (size 4..6) separated by color-5 columns",
    "panel 2 is a dihedral transform of panel 1 with a consistent recolor",
    "the query panel uses only colors seen in the example input panel",
    "the output is the transformed query with the learned color mapping",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "identity_transform", "identity_recolor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "transform":         {"type": "enum", "default": "rng", "valid": "r1|r2|r3|fh|fv|tr|atr"},
    "panel_size":        {"type": "int", "default": "rng 4..6", "valid": "4..6"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "position_bias":     {"type": "str", "default": "three_4x4_panels",
                          "valid": "three_4x4_panels"},
    "n_distinct_colors": {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CODES = ["r1", "r2", "r3", "fh", "fv", "tr", "atr"]
_EXAMPLE_CELL_BANK = [
    # Each entry: a list of (r, c, slot) where slot ∈ {1, 2, 3}
    [(0, 0, 1), (1, 0, 1), (1, 1, 2), (2, 1, 2), (2, 2, 3)],
    [(0, 0, 1), (0, 1, 1), (1, 1, 2), (2, 1, 3), (2, 2, 3)],
    [(0, 1, 1), (1, 0, 2), (1, 1, 2), (1, 2, 2), (2, 1, 3)],
    [(0, 2, 1), (1, 1, 2), (1, 2, 2), (2, 0, 3), (2, 1, 3)],
    [(0, 0, 1), (1, 0, 2), (2, 0, 3), (1, 1, 1), (0, 1, 2)],
    [(0, 0, 1), (0, 3, 1), (1, 1, 2), (1, 2, 2), (3, 0, 3), (3, 3, 3)],
]
_QUERY_CELL_BANK = [
    [(0, 1, 1), (1, 1, 1), (1, 2, 2), (2, 2, 3)],
    [(0, 2, 1), (1, 2, 1), (2, 2, 2), (2, 1, 3)],
    [(0, 0, 1), (1, 0, 2), (1, 1, 2), (2, 1, 3)],
    [(0, 2, 1), (1, 1, 1), (2, 1, 2), (2, 0, 3)],
    [(0, 0, 1), (0, 1, 2), (1, 0, 2), (1, 1, 3)],
]


def _grid_from_cells(cells, colors, p=4):
    g = full_grid(p, p, 0)
    for r, c, slot in cells:
        g[r][c] = colors[slot - 1]
    return g


def _random_panel_cells(rng, p, n_slots):
    """Random set of colored cells in a p x p panel, covering n_slots distinct
    color slots (1..n_slots), each slot used at least once, leaving >=1 bg."""
    all_pos = [(r, c) for r in range(p) for c in range(p)]
    rng.shuffle(all_pos)
    n = rng.randint(n_slots, max(n_slots, (p * p) - 1))
    chosen = all_pos[:n]
    cells = []
    # ensure each slot appears at least once
    for i in range(n_slots):
        r, c = chosen[i]
        cells.append((r, c, i + 1))
    for (r, c) in chosen[n_slots:]:
        cells.append((r, c, rng.randint(1, n_slots)))
    return cells


def _xform_grid(grid, code):
    h = len(grid)
    w = len(grid[0])
    if code == "id":
        return [row[:] for row in grid]
    if code == "r1":
        return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == "r2":
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if code == "r3":
        return [[grid[r][w - 1 - c] for r in range(h)] for c in range(w)]
    if code == "fh":
        return [list(reversed(row)) for row in grid]
    if code == "fv":
        return list(reversed([row[:] for row in grid]))
    if code == "tr":
        return [[grid[r][c] for r in range(h)] for c in range(w)]
    return [[grid[h - 1 - c][w - 1 - r] for c in range(h)] for r in range(w)]


def _recolor(grid, mapping):
    return [[mapping.get(v, v) for v in row] for row in grid]


def _shape_sig(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not cells:
        return ()
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _d4_unique(grid):
    return len({_shape_sig(_xform_grid(grid, code)) for code in ("id", *_CODES)}) == 8


def _paste_panel(out, panel, grid, p=4):
    left = panel * (p + 1)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            out[r][left + c] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        codes = ["fh", "fv", "tr"]
    elif difficulty == "hard":
        codes = _CODES
    else:
        codes = _CODES
    code = ctx.draw_choice("transform", codes)
    # Panel size varies (square 4..6) -> breaks the old 4x4 shape-lock.
    if difficulty == "easy":
        p = ctx.draw_int("panel_size", 4, 4)
    elif difficulty == "hard":
        p = ctx.draw_int("panel_size", 5, 6)
    else:
        p = ctx.draw_int("panel_size", 4, 6)
    source_colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    target_colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    if target_colors == source_colors:
        target_colors = target_colors[1:] + target_colors[:1]
    mapping = dict(zip(source_colors, target_colors))

    for _attempt in range(100):
        example_cells = _random_panel_cells(rng, p, 3)
        query_cells = _random_panel_cells(rng, p, 3)
        ex_in = _grid_from_cells(example_cells, source_colors, p)
        query = _grid_from_cells(query_cells, source_colors, p)
        # Dense random panels can accidentally be invariant under a reflection or
        # rotation, making the transform code unlearnable.  Keep only full-D4-
        # unique witnesses, and require the query panel to visibly change too.
        if not (_d4_unique(ex_in) and _d4_unique(query)):
            continue
        if _shape_sig(_xform_grid(query, code)) == _shape_sig(query):
            continue
        ex_out = _recolor(_xform_grid(ex_in, code), mapping)
        break
    else:
        raise ValueError("could not realize D4-unique transform analogy panels")

    cols = 3 * p + 2
    g = full_grid(p, cols, 0)
    for sep in (p, 2 * p + 1):
        for r in range(p):
            g[r][sep] = 5
    _paste_panel(g, 0, ex_in, p)
    _paste_panel(g, 1, ex_out, p)
    _paste_panel(g, 2, query, p)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(4, 14, 0)
    if name == "no_dividers":
        # No color-5 separators — rule cannot identify panels.
        g[0][0] = 4; g[1][0] = 4; g[1][1] = 5
        g[0][6] = 4; g[1][6] = 4
        g[0][11] = 6; g[1][12] = 7
        return g
    if name == "identity_transform":
        # Panel 2 == panel 1 (no transform) — output = query unchanged.
        for sep in (4, 9):
            for r in range(4):
                g[r][sep] = 5
        for (r, c, _slot), color in zip(_EXAMPLE_CELL_BANK[0], [4, 4, 6, 6, 7]):
            g[r][c] = color
            g[r][5 + c] = color
        for (r, c, _slot), color in zip(_QUERY_CELL_BANK[0], [4, 4, 6, 7]):
            g[r][10 + c] = color
        return g
    if name == "identity_recolor":
        # Source == target colors — no recolor effect.
        for sep in (4, 9):
            for r in range(4):
                g[r][sep] = 5
        for (r, c, _slot), color in zip(_EXAMPLE_CELL_BANK[1], [4, 4, 6, 6, 7]):
            g[r][c] = color
            g[r][5 + c] = color
        for (r, c, _slot), color in zip(_QUERY_CELL_BANK[1], [4, 4, 6, 7]):
            g[r][10 + c] = color
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    h, w = len(grid), len(grid[0])
    seps = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(seps) != 2:
        return [f"expected exactly two full color-5 separator columns, found {seps}"]
    p = seps[0]
    if seps != [p, 2 * p + 1] or w != 3 * p + 2 or h != p:
        errs.append(f"expected three equal square panels separated at p and 2p+1; got h={h} w={w} seps={seps}")
        return errs
    panels = []
    for start in (0, p + 1, 2 * p + 2):
        panels.append([row[start:start + p] for row in grid])
    if any(not _shape_sig(panel) for panel in panels):
        errs.append("all three panels need non-empty shape witnesses")
    if panels and not _d4_unique(panels[0]):
        errs.append("example input panel is not full-D4-unique")
    if panels and not _d4_unique(panels[2]):
        errs.append("query panel is not full-D4-unique")
    matches = [code for code in _CODES if _shape_sig(_xform_grid(panels[0], code)) == _shape_sig(panels[1])]
    if len(matches) != 1:
        errs.append(f"example panels should imply exactly one non-identity transform, got {matches}")
    elif _shape_sig(_xform_grid(panels[2], matches[0])) == _shape_sig(panels[2]):
        errs.append("query panel is unchanged by the learned transform")
    return errs
