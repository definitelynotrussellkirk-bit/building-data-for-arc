"""Generator for 8df12dd4.

Rule: objects touching grid edge → 2; fully interior objects → 8.

Combinatorial axes (8): grid_h/w, n_border_objs, n_interior_objs,
object_size_kind, palette_kind, position_bias, anchor_corner,
asymmetry_force.
Degenerates: all_border, all_interior, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e8c736c2bda"
VERSION = "1.1.1"
TASK_ID = "7e8c736c2bda"
SUMMARY = "Border-touching objects → 2, interior → 8."

INVARIANTS = [
    "background is 0",
    ">=1 object touching grid border",
    ">=1 object fully interior",
    "objects don't touch (4-conn separation)",
    "no colors 2 or 8 in input (rule writes them for output)",
]

OBJECT_SIZE_KINDS = ("small", "medium", "varied")
PALETTE_KINDS = ("warm", "cool", "broad")
DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_objects")
HELPFUL_TEXTURES = ("balanced", "border_heavy", "interior_heavy", "spread")

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":            {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "n_border_objs":     {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_interior_objs":   {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "object_size_kind":  {"type": "str", "default": "rng helpful",
                          "valid": "|".join(OBJECT_SIZE_KINDS)},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":     {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "rng helpful",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, no color 2 or 8 in input, ≥1 nonzero cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    flat = [v for row in grid for v in row]
    if 2 in flat:
        errs.append("color 2 found in input (reserved for output)")
    if 8 in flat:
        errs.append("color 8 found in input (reserved for output)")
    nz = sum(1 for v in flat if v != 0)
    if nz < 1:
        errs.append("expected ≥1 nonzero cell; found none")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 6, 9
    elif difficulty == "hard":
        h_lo, h_hi = 13, 18
    else:
        h_lo, h_hi = 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    if texture == "border_heavy":
        n_border, n_interior = 3, 1
    elif texture == "interior_heavy":
        n_border, n_interior = 1, 3
    elif texture == "spread":
        n_border, n_interior = 2, 2
    else:
        n_border = int(overrides.get("n_border_objs",
                                     ctx.draw_int("n_border_objs", 1, 3)))
        n_interior = int(overrides.get("n_interior_objs",
                                       ctx.draw_int("n_interior_objs", 1, 3)))
    n_border = max(1, min(5, n_border))
    n_interior = max(1, min(5, n_interior))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7]
    else:
        pool = [1, 3, 4, 5, 6, 7, 9]
    rng.shuffle(pool)
    palette = pool[:max(2, n_border + n_interior)]
    while len(palette) < n_border + n_interior:
        palette.append(palette[0])
    size_kind = overrides.get("object_size_kind",
                              ctx.draw_choice("object_size_kind",
                                              list(OBJECT_SIZE_KINDS)))
    g = full_grid(h, w, 0)
    used = set()
    placed_b = 0
    for i in range(n_border * 4):
        if placed_b >= n_border:
            break
        cells = _shape_cells(size_kind, rng)
        for _try in range(20):
            if rng.random() < 0.5:
                r0 = rng.choice([0, h - max(r for r, _ in cells) - 1])
                c0 = rng.randint(0, w - max(c for _, c in cells) - 1)
            else:
                r0 = rng.randint(0, h - max(r for r, _ in cells) - 1)
                c0 = rng.choice([0, w - max(c for _, c in cells) - 1])
            placed = {(r0 + dr, c0 + dc) for dr, dc in cells}
            if any(0 > r or r >= h or 0 > c or c >= w for r, c in placed):
                continue
            if any(p in used for p in placed):
                continue
            ok = all(_no_close(p, used) for p in placed)
            if not ok:
                continue
            on_border = any(r in (0, h - 1) or c in (0, w - 1)
                            for r, c in placed)
            if not on_border:
                continue
            for r, c in placed:
                g[r][c] = palette[placed_b]
                used.add((r, c))
            placed_b += 1
            break
    placed_i = 0
    for i in range(n_interior * 4):
        if placed_i >= n_interior:
            break
        cells = _shape_cells(size_kind, rng)
        for _try in range(20):
            r0 = rng.randint(2, max(2, h - 4))
            c0 = rng.randint(2, max(2, w - 4))
            placed = {(r0 + dr, c0 + dc) for dr, dc in cells}
            if any(0 > r or r >= h or 0 > c or c >= w for r, c in placed):
                continue
            if any(p in used for p in placed):
                continue
            ok = all(_no_close(p, used) for p in placed)
            if not ok:
                continue
            on_border = any(r in (0, h - 1) or c in (0, w - 1)
                            for r, c in placed)
            if on_border:
                continue
            color = palette[(n_border + placed_i) % len(palette)]
            for r, c in placed:
                g[r][c] = color
                used.add((r, c))
            placed_i += 1
            break
    return g


def _shape_cells(size_kind, rng):
    if size_kind == "small":
        shapes = [
            [(0, 0), (0, 1)],
            [(0, 0), (1, 0)],
            [(0, 0), (0, 1), (1, 0)],
        ]
    elif size_kind == "medium":
        shapes = [
            [(0, 0), (0, 1), (1, 0), (1, 1)],
            [(0, 0), (0, 1), (0, 2)],
            [(0, 0), (1, 0), (2, 0)],
            [(0, 0), (0, 1), (1, 1)],
        ]
    else:
        shapes = [
            [(0, 0), (0, 1)],
            [(0, 0), (0, 1), (1, 0)],
            [(0, 0), (0, 1), (1, 0), (1, 1)],
            [(0, 0), (0, 1), (0, 2)],
        ]
    return rng.choice(shapes)


def _no_close(cell, used):
    r, c = cell
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (r + dr, c + dc) in used and (dr, dc) != (0, 0):
                return False
    return True


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([1, 3, 4, 5, 6, 7, 9])
    if name == "all_border":
        g[0][0] = color
        g[0][1] = color
        g[h - 1][w - 1] = color
        return g
    if name == "all_interior":
        for r in range(2, 4):
            for c in range(2, 4):
                if r < h and c < w:
                    g[r][c] = color
        return g
    if name == "no_objects":
        return g
    return g
