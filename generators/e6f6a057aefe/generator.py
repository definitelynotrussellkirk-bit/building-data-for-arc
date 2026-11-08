"""Generator for arc_puzzle_bank_tenth_21_bundle:hard_67_select_ranked_component_scale_and_place.

The value at (0,0) chooses the size-ranked object. A color-9 marker gives the
paste location for a 2x upscaled crop of that object.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rank,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rank, no_marker, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e6f6a057aefe"
VERSION = "2.0.1"  # add executable invariants for rank/object/marker contract
TASK_ID = "e6f6a057aefe"
SUMMARY = (
    "Fixed 12×14 0-bg grid with: (a) RANK "
    "CELL at (0, 0) painted with a value "
    "rank ∈ {1, 2, 3} encoding which "
    "size-ranked object to select; "
    "(b) ONE COLOR-9 MARKER placed in the "
    "lower-right region at (6+jitter, "
    "8+jitter) (random ±1 perturbation); "
    "(c) THREE SOURCE OBJECTS at fixed "
    "positions sorted ASCENDING BY SIZE — "
    "_OBJECTS[0]=2-cell horizontal pair at "
    "(2, 1); _OBJECTS[1]=3-cell L-shape at "
    "(5, 1); _OBJECTS[2]=5-cell pentomino "
    "at (2, 5). Each object painted in a "
    "DISTINCT non-{0, 9} color drawn from "
    "{2..8}. Sizes are strictly distinct: "
    "{2, 3, 5}. Rule (THE RANK AT (0, 0) "
    "PICKS A SIZE-RANKED SOURCE, UPSCALE "
    "IT 2×, PASTE AT THE 9-MARKER): READ "
    "the RANK at (0, 0) — 1→smallest, "
    "2→middle, 3→largest. SELECT the "
    "corresponding source object. CROP it "
    "to its bbox. UPSCALE the crop by "
    "factor 2 (each cell → 2×2 block in "
    "same color). find the COLOR-9 "
    "MARKER position (mr, mc). PASTE the "
    "upscaled crop with its top-left at "
    "(mr, mc) on a FRESH OUTPUT GRID. "
    "The rank cell, marker, and original "
    "source objects are discarded. Net: "
    "a 2×-enlarged copy of the rank-"
    "selected object appears at the "
    "marker's location. Flagged intrinsic-"
    "low (uniq_out=33): 3 ranks × 3 fixed "
    "objects × marker positions × colors."
)

INVARIANTS = [
    "cell (0,0) is a rank from 1 to 3",
    "there is one color-9 marker away from the source objects",
    "objects have distinct sizes and are sorted ascending by size",
    "the selected object's 2x crop fits at the marker location",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rank", "no_marker", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12..20"},
    "grid_w":         {"type": "int", "default": "14", "valid": "13..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rank":           {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "rank_plus_marker_plus_objects",
                       "valid": "rank_plus_marker_plus_objects"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_OBJECTS = [
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)],
]
_POSITIONS = [(2, 1), (5, 1), (2, 5)]


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


def _poly(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 14); w = ctx.draw_int("grid_w", 13, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 20); w = ctx.draw_int("grid_w", 17, 22)
    else:
        h = ctx.draw_int("grid_h", 14, 17); w = ctx.draw_int("grid_w", 15, 18)
    rank = int(overrides.get("rank", ctx.draw_int("rank", 1, 3)))
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8], 3)
    ksizes = rng.sample([2, 3, 4, 5, 6], 3)            # distinct sizes -> unambiguous rank
    objs = [(_poly(rng, k), col) for k, col in zip(ksizes, colors)]
    # selected (by size rank) determines the 2x paste footprint
    order = sorted(range(3), key=lambda i: ksizes[i])
    sel = objs[order[rank - 1]][0]
    sbh = (max(r for r, _ in sel) + 1) * 2; sbw = (max(c for _, c in sel) + 1) * 2

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        g[0][0] = rank; occ[0][0] = True
        ok = True
        for cells, color in objs:
            bh = max(r for r, _ in cells) + 1; bw = max(c for _, c in cells) + 1
            done = False
            for _ in range(60):
                r0 = rng.randint(1, h - bh); c0 = rng.randint(1, w - bw)
                if any(occ[r0 + dr + a][c0 + dc + b]
                       for dr, dc in cells for a in (-1, 0, 1) for b in (-1, 0, 1)
                       if 0 <= r0 + dr + a < h and 0 <= c0 + dc + b < w):
                    continue
                for dr, dc in cells:
                    g[r0 + dr][c0 + dc] = color; occ[r0 + dr][c0 + dc] = True
                done = True; break
            if not done:
                ok = False; break
        if not ok:
            continue
        # marker where the selected object's 2x crop fits
        for _ in range(60):
            mr = rng.randint(0, h - sbh); mc = rng.randint(0, w - sbw)
            if not occ[mr][mc] and not (mr == 0 and mc == 0):
                g[mr][mc] = 9; ok = True; break
        else:
            ok = False
        if ok:
            return g
    return g  # fallback


def _components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append({"color": color, "cells": cells})
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    rank = grid[0][0]
    if rank not in (1, 2, 3):
        errors.append(f"cell (0,0) must be rank 1..3, got {rank}")

    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(markers) != 1:
        errors.append(f"expected exactly one color-9 marker, found {len(markers)}")

    clean = [row[:] for row in grid]
    clean[0][0] = 0
    for r, c in markers:
        clean[r][c] = 0
    comps = [c for c in _components_by_color(clean) if c["color"] not in (0, 9)]
    if len(comps) != 3:
        errors.append(f"expected exactly three source objects after removing rank/marker, found {len(comps)}")
        return errors
    colors = [c["color"] for c in comps]
    sizes = [len(c["cells"]) for c in comps]
    if len(colors) != len(set(colors)):
        errors.append(f"source object colors must be distinct, got {colors}")
    if len(sizes) != len(set(sizes)):
        errors.append(f"source object sizes must be distinct for rank selection, got {sorted(sizes)}")
    owner = {}
    for idx, comp in enumerate(comps):
        for cell in comp["cells"]:
            owner[cell] = idx
    for idx, comp in enumerate(comps):
        for r, c in comp["cells"]:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nb = (r + dr, c + dc)
                    if nb in owner and owner[nb] != idx:
                        errors.append("source objects must have diagonal clearance")
                        return errors
    if rank in (1, 2, 3) and len(markers) == 1 and len(comps) == 3:
        sel = sorted(comps, key=lambda c: len(c["cells"]))[rank - 1]
        rs = [r for r, _ in sel["cells"]]
        cs = [c for _, c in sel["cells"]]
        out_h = (max(rs) - min(rs) + 1) * 2
        out_w = (max(cs) - min(cs) + 1) * 2
        mr, mc = markers[0]
        if mr + out_h > h or mc + out_w > w:
            errors.append(f"selected 2x crop {out_h}x{out_w} does not fit at marker {(mr, mc)} in {h}x{w}")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    if name == "no_rank":
        # marker + objects but no rank at (0,0) → no selection signal
        g[7][9] = 9
        for cells, pos, color in zip(_OBJECTS, _POSITIONS, [4, 6, 7]):
            _paint(g, pos[0], pos[1], cells, color)
        return g
    if name == "no_marker":
        # rank + objects but no 9-marker → no paste location
        g[0][0] = 2
        for cells, pos, color in zip(_OBJECTS, _POSITIONS, [4, 6, 7]):
            _paint(g, pos[0], pos[1], cells, color)
        return g
    if name == "no_objects":
        # rank + marker but no source objects → nothing to scale
        g[0][0] = 2
        g[7][9] = 9
        return g
    return g
