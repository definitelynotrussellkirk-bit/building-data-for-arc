"""Generator for arc_puzzle_bank_21_set13_bundle:hard_m05 — set-op of two largest shapes by key.

Rule: cell (0, 0) is the key (1=union, 2=intersection, else=symmetric difference).
Two largest non-key components are aligned to a common origin; the output is
their set-operation cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_op_key (cell (0,0) is bg → rule's op selector returns
nothing), single_component (only one non-key motif → rule's "two
largest" has no second operand), tied_sizes (≥2 components share max
size → "two largest" tie-break decides which pair to use).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fa103c7aa88b"
VERSION = "2.0.2"  # bigger partially-overlapping main shapes (all 3 ops distinct) + smaller distractor components (rule picks two largest) + more colors/grids
TASK_ID = "fa103c7aa88b"

SUMMARY = (
    "0-bg grid (size varies). Cell (0,0) holds the OP KEY: 1=union, "
    "2=intersection, 3=symmetric-difference. Elsewhere are TWO LARGE partially-"
    "overlapping component shapes (when each is cropped to its bbox top-left "
    "they share some cells and each has private cells) plus 0-2 SMALLER "
    "distractor components. Every component is a distinct color != the key. "
    "Rule: read the key at (0,0); zero out all key-valued cells; find the TWO "
    "LARGEST remaining components; crop each to its bbox; apply the set op of "
    "their cell sets (union / intersection / symmetric difference); CROP to the "
    "result bbox and paint it color 8. Smaller distractors are ignored. (Was "
    "two tiny 3-5 cell shapes with no guaranteed overlap.)"
)

# Rivals: 'output is input' refuted by any demo (output is small).
# 'always intersection' refuted by ≥2 demos with non-2 keys producing
# different cell sets. 'use component colors in output' refuted by
# any demo (output is 8). 'pick wrong component pair' refuted by ≥1
# demo where there's a clear smaller distractor. 3 demos covering
# all 3 keys cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "cell (0, 0) holds the key (1, 2, or 3)",
    "the two LARGEST components partially overlap (share + private cells when bbox-aligned)",
    "any distractor components are strictly smaller than both main components",
    "components are isolated from each other and from (0, 0); colors != key",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_op_key", "single_component", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..20"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "10..22"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": 'default|warm|cool|varied'},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "key_plus_two_largest",
                          "valid": "key_plus_two_largest"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": 'default|warm|cool|varied|no_op_key|single_component|tied_sizes'},
}


def _components_for_check(grid, key):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or color == key or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append({"color": color, "cells": cells, "size": len(cells)})
    return comps


def _norm_cells(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    key = grid[0][0]
    if key not in (1, 2, 3):
        errs.append(f"cell (0,0) must be key 1/2/3, got {key}")
    if sum(1 for r in range(h) for c in range(w) if grid[r][c] == key) != 1:
        errs.append("key color appears outside the selector cell")
    comps = _components_for_check(grid, key)
    if len(comps) < 2:
        errs.append(f"expected at least two non-key components, got {len(comps)}")
        return errs
    comps.sort(key=lambda x: x["size"], reverse=True)
    if len(comps) > 2 and comps[2]["size"] >= comps[1]["size"]:
        errs.append("distractor/tied component is not strictly smaller than the second main component")
    a = _norm_cells(comps[0]["cells"])
    b = _norm_cells(comps[1]["cells"])
    if not (a & b):
        errs.append("two largest normalized shapes have empty intersection")
    if not (a - b):
        errs.append("first main shape has no private cells")
    if not (b - a):
        errs.append("second main shape has no private cells")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _box_shapes(rng):
    """Return two connected, bbox-aligned shapes with real overlap and
    private cells on both sides. The previous random cell partition could create
    disconnected same-color fragments, so the canonical `objects` call sometimes
    selected the wrong components."""
    bh = rng.randint(3, 6)
    bw = rng.randint(3, 6)
    a = {(r, c) for r in range(bh) for c in range(bw - 1)}
    b = {(r, c) for r in range(bh - 1) for c in range(bw)}
    return sorted(a), sorted(b)


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    stack = [next(iter(cells))]
    seen = {stack[0]}
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (r + dr, c + dc)
            if nb in cells and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return len(seen) == len(cells)


def _rand_blob(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _place(g, cells, color, rng):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
    for _ in range(150):
        r0 = rng.randint(1, h - sh); c0 = rng.randint(1, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for r, c in cells:
            g[r0 + r][c0 + c] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14); ndr = (0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 16, 22); ndr = (1, 2)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 13, 18); ndr = (0, 2)
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        g = full_grid(h, w, 0)
        key = rng.choice([1, 2, 3])
        g[0][0] = key
        colors = rng.sample([c for c in range(1, 10) if c != key], 9 - 1)
        a_cells, b_cells = _box_shapes(rng)
        main_min = min(len(a_cells), len(b_cells))
        if not (_place(g, a_cells, colors[0], rng) and _place(g, b_cells, colors[1], rng)):
            continue
        # distractor components, each STRICTLY smaller than both mains.
        ci = 2
        for _ in range(rng.randint(*ndr)):
            dsz = rng.randint(2, max(2, main_min - 1))
            if dsz >= main_min:
                continue
            if ci < len(colors) and _place(g, _rand_blob(rng, dsz), colors[ci], rng):
                ci += 1
        return g
    raise ValueError("could not realize hard_m05 layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_op_key":
        # (0,0) is bg — rule's op selector returns nothing.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[5 + dr][7 + dc] = 6
        return g
    if name == "single_component":
        # Only one non-key component — "two largest" has no second
        # operand.
        g[0][0] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[3 + dr][3 + dc] = 4
        return g
    if name == "tied_sizes":
        # Two components share max size — "two largest" tie-break
        # decides which pair.
        g[0][0] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][6 + dc] = 6   # tied with prev
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[7 + dr][2 + dc] = 7   # tied
        return g
    return g
