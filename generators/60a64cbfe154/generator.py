"""Generator for 9b:m60 — translate components to matching markers.

Rule: for each non-bg color, the smallest component (a single cell)
is the marker; the largest component is the shape. Output translates
the shape so its bbox top-left lands at the marker's position.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (color has only the shape, no single-cell
marker → rule's marker selector returns nothing for that color),
no_shape (color has only the marker, no multi-cell shape → rule's
shape selector returns nothing), marker_at_shape (marker position is
already inside shape's bbox → rule's translation lands on existing
cells, output equals input).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "60a64cbfe154"
VERSION = "1.1.0"
TASK_ID = "60a64cbfe154"

SUMMARY = "Per color: 1 multi-cell shape + 1 isolated single-cell marker."

INVARIANTS = [
    "background is 0",
    "2 distinct non-bg colors",
    "each color has exactly 2 components: one multi-cell shape + one isolated single-cell marker",
    "the marker's position + the shape's bbox dims fit in-bounds for translation",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_shape", "marker_at_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "shape_plus_marker_per_color",
                          "valid": "shape_plus_marker_per_color"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 9, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 11, 11)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)
    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            shape = rng.choice(_SHAPES)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed_shape = False
            for _ in range(40):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed_shape = True; break
            if not placed_shape:
                ok = False; break
            placed_marker = False
            for _ in range(60):
                mr = rng.randint(0, h - sh); mc = rng.randint(0, w - sw)
                if g[mr][mc] != 0: continue
                bad = False
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = mr + dr, mc + dc
                        if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                            bad = True; break
                    if bad: break
                if bad: continue
                g[mr][mc] = color
                placed_marker = True; break
            if not placed_marker:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not place 2 (shape, marker) pairs in 40 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # Color has only the shape (no isolated marker) — rule's
        # marker selector returns nothing for that color.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[5 + dr][6 + dc] = 6
        return g
    if name == "no_shape":
        # Color has only the marker (single cell), no multi-cell
        # shape — rule's shape selector returns nothing.
        g[2][2] = 4
        g[6][7] = 6
        return g
    if name == "marker_at_shape":
        # Marker position lands inside shape's bbox — rule's translation
        # places shape on top of itself; output equals input.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        # marker for color 4 placed at (3,3) — translation puts shape
        # bbox starting at (3,3), overlapping original (2,2)..(3,3)
        g[3][3] = 4   # but adjacent — illegal isolated marker, demonstrates degeneracy
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[6 + dr][6 + dc] = 6
        g[7][7] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    colors = sorted({v for row in grid for v in row if v != 0})
    if len(colors) != 2:
        errors.append(f"expected exactly two active colors, got {colors}")
    for color in colors:
        comps = components(grid, colors={color})
        sizes = sorted(len(comp["cells"]) for comp in comps)
        if len(comps) != 2 or sizes[0] != 1 or sizes[-1] < 2:
            errors.append(f"color {color} should have one singleton marker and one multi-cell shape, sizes={sizes}")
            continue
        marker = [comp for comp in comps if len(comp["cells"]) == 1][0]["cells"][0]
        shape = [comp for comp in comps if len(comp["cells"]) > 1][0]
        r1, c1, r2, c2 = shape["bbox"]
        if marker[0] + (r2 - r1 + 1) > h or marker[1] + (c2 - c1 + 1) > w:
            errors.append(f"translated shape for color {color} would go out of bounds")
    return errors
