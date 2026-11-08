"""Generator for arc_puzzle_bank_eighteenth21:H126 — transform example then merge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: identity_transform (panel 2 == panel 1 → rule's inferred
transform is identity, query merge is just panel 4 with X overlaid),
no_dividers (no color-9 separators → rule can't split panels),
asymmetric_panels (panel A's cells coincide under the chosen
transform → transform is unidentifiable from A alone).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b15d96b5d45"
VERSION = "1.1.0"
TASK_ID = "6b15d96b5d45"

SUMMARY = "Four square panels: an example transform pair followed by a query merge pair."

INVARIANTS = [
    "background is 0",
    "four equal square panels are separated by single color-9 columns",
    "panel 2 is exactly a geometric transform of panel 1",
    "the example panel is asymmetric so the transform is unambiguous",
    "query panels contain nonzero overlaps after the same transform is applied",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_transform", "no_dividers", "asymmetric_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_size":        {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 5..6", "valid": "5..7"},
    "position_bias":     {"type": "str", "default": "four_panels_with_dividers",
                          "valid": "four_panels_with_dividers"},
    "n_distinct_colors": {"type": "int", "default": "rng 5..6", "valid": "5..7"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _rot180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return grid[::-1]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _anti_transpose(grid):
    return _rot180(_transpose(grid))


def _apply(name, grid):
    return {
        "rot90": _rot_cw,
        "rot180": _rot180,
        "rot270": _rot_ccw,
        "flip-h": _flip_lr,
        "flip-v": _flip_ud,
        "transpose": _transpose,
        "anti-transpose": _anti_transpose,
    }[name](grid)


def _panel(n, cells):
    g = full_grid(n, n, 0)
    for r, c, color in cells:
        g[r][c] = color
    return g


def _paste_panel(out, panel, left):
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            out[r][left + c] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("panel_size", 5, 5)
    elif difficulty == "hard":
        n = ctx.draw_int("panel_size", 6, 6)
    else:
        n = ctx.draw_int("panel_size", 5, 6)
    rng = ctx.draw_rng("layout")
    name = rng.choice([
        "rot90", "rot180", "rot270", "flip-h", "flip-v",
        "transpose", "anti-transpose",
    ])

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 6)
    a = _panel(n, [
        (0, 1, colors[0]),
        (1, n - 2, colors[1]),
        (n - 3, 0, colors[2]),
        (n - 2, 2, colors[3]),
    ])
    b = _apply(name, a)
    y = _panel(n, [
        (0, 0, colors[1]),
        (1, 2, colors[4]),
        (n - 2, n - 3, colors[5]),
    ])
    ty = _apply(name, y)
    occupied = [(r, c) for r in range(n) for c in range(n) if ty[r][c] != 0]
    conflict_r, conflict_c = rng.choice(occupied)
    x = _panel(n, [
        (conflict_r, conflict_c, colors[0] if ty[conflict_r][conflict_c] != colors[0] else colors[2]),
        (n - 1, 1, colors[3]),
    ])

    out = full_grid(n, 4 * n + 3, 9)
    for i, panel in enumerate([a, b, x, y]):
        _paste_panel(out, panel, i * (n + 1))
    return out


def _draw_from_degenerate(name, rng):
    n = 5
    out = full_grid(n, 4 * n + 3, 9)
    a = _panel(n, [(0, 1, 4), (1, 3, 6), (2, 0, 7), (3, 2, 8)])
    if name == "identity_transform":
        # Panel 2 == Panel 1 — rule's inferred transform is identity.
        b = a
        y = _panel(n, [(0, 0, 6), (2, 2, 4)])
        x = _panel(n, [(1, 1, 7)])
        for i, panel in enumerate([a, b, x, y]):
            _paste_panel(out, panel, i * (n + 1))
        return out
    if name == "no_dividers":
        # No color-9 separators — rule can't split panels.
        out2 = full_grid(n, 4 * n + 3, 0)
        b = _flip_lr(a)
        y = _panel(n, [(0, 0, 6), (2, 2, 4)])
        x = _panel(n, [(1, 1, 7)])
        for i, panel in enumerate([a, b, x, y]):
            _paste_panel(out2, panel, i * (n + 1))
        return out2
    if name == "asymmetric_panels":
        # Panel A is symmetric — transform is unidentifiable from A.
        # Symmetric A: 2x2 in center.
        a_sym = _panel(n, [(2, 2, 4), (2, 3, 4), (3, 2, 4), (3, 3, 4)])
        b = _apply("rot180", a_sym)   # same as a_sym
        y = _panel(n, [(0, 0, 6), (2, 2, 4)])
        x = _panel(n, [(1, 1, 7)])
        for i, panel in enumerate([a_sym, b, x, y]):
            _paste_panel(out, panel, i * (n + 1))
        return out
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    n = len(grid)
    if len(grid[0]) != 4 * n + 3:
        return ["grid is not four square panels plus three dividers"]
    divs = [n, 2 * n + 1, 3 * n + 2]
    for d in divs:
        if not all(row[d] == 9 for row in grid):
            errors.append("divider column is not solid color 9")
    panels = []
    for left in [0, n + 1, 2 * n + 2, 3 * n + 3]:
        panels.append([row[left:left + n] for row in grid])
    names = ["rot90", "rot180", "rot270", "flip-h", "flip-v", "transpose", "anti-transpose"]
    matches = [name for name in names if _apply(name, panels[0]) == panels[1]]
    if len(matches) != 1:
        errors.append(f"example transform is not uniquely identified: {matches}")
    else:
        ty = _apply(matches[0], panels[3])
        if not any(panels[2][r][c] != 0 and ty[r][c] != 0 for r in range(n) for c in range(n)):
            errors.append("query panels have no visible overlap after transform")
    return errors
