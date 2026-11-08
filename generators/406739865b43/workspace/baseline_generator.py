"""Generator for arc_additional_puzzles_21_set3:M20 — Crop first marker-color blob (rows ≥ 1).

Rule: target = first non-zero color in row 0. Find blob(s) below row 0 in that
color; pick the first (top-left order); output its bbox crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_decoys, target_shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker_in_row0, no_matching_body, multiple_matching_bodies.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "406739865b43"
VERSION = "2.0.0"  # distinct=73: target/decoys from 11 FIXED shapes -> the chosen-object crop (output) had limited variety. Now random polyominoes (3-6 cells) for target + decoys -> output crop dims/patterns vary.
TASK_ID = "406739865b43"
SUMMARY = "Row 0 has one marker color cell. Body (rows ≥ 1) has at least one blob in that color plus decoy blobs in other colors. Rule outputs the bbox crop of the matching blob (top-left in tie-break)."

# Rivals: 'output the largest blob' refuted by ≥2 demos where the
# marker color picks a non-largest blob. 'output a decoy' refuted by
# any demo where the marker color appears below. 'output the full
# grid' refuted by any demo (output is small crop). 'use marker color
# globally' refuted by ≥1 demo with multiple distractor colors.
# 3 demos with varied target colors + decoy counts cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "row 0 has exactly one non-zero cell (the marker)",
    "exactly one body object matches marker color",
    "1-3 decoy body objects of other colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker_in_row0", "no_matching_body", "multiple_matching_bodies")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_decoys":       {"type": "int", "default": "rng 1..3", "valid": "0..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "marker_top_body_random",
                       "valid": "marker_top_body_random"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _rand_poly(rng, n):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        n_decoys = ctx.draw_int("n_decoys", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 17)
        w = ctx.draw_int("grid_w", 13, 18)
        n_decoys = ctx.draw_int("n_decoys", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 10, 14)
        n_decoys = ctx.draw_int("n_decoys", 1, 3)
    marker = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    decoy_colors = rng.sample([c for c in [2, 3, 4, 5, 6, 7, 8, 9] if c != marker], n_decoys)
    for _ in range(60):
        g = full_grid(h, w, 0)
        # Marker in row 0 at random column
        marker_col = rng.randint(0, w - 1)
        g[0][marker_col] = marker
        # Target blob in body.  Random walks can be too tall for easy grids;
        # redraw instead of letting randint(2, h-sh_h) crash.
        for _shape_try in range(30):
            target_shape = _rand_poly(rng, rng.randint(3, 6))
            ts_h = max(r for r, _ in target_shape) + 1
            ts_w = max(c for _, c in target_shape) + 1
            if ts_h <= h - 2 and ts_w <= w:
                break
        else:
            continue
        placed = False
        for _ in range(60):
            r0 = rng.randint(2, h - ts_h)
            c0 = rng.randint(0, w - ts_w)
            if not _free(g, r0, c0, r0 + ts_h - 1, c0 + ts_w - 1): continue
            for dr, dc in target_shape:
                g[r0 + dr][c0 + dc] = marker
            placed = True
            break
        if not placed: continue
        # Decoys
        ok = True
        for color in decoy_colors:
            for _shape_try in range(30):
                shape = _rand_poly(rng, rng.randint(3, 6))
                sh_h = max(r for r, _ in shape) + 1
                sh_w = max(c for _, c in shape) + 1
                if sh_h <= h - 2 and sh_w <= w:
                    break
            else:
                ok = False; break
            decoy_placed = False
            for _ in range(60):
                r0 = rng.randint(2, h - sh_h)
                c0 = rng.randint(0, w - sh_w)
                if not _free(g, r0, c0, r0 + sh_h - 1, c0 + sh_w - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                decoy_placed = True
                break
            if not decoy_placed:
                ok = False; break
        if ok:
            return g
    # Fallback to original layout
    g = full_grid(h, w, 0)
    g[0][3] = marker
    paint_at(g, 5, w - 4, [(0, 0), (1, -2), (1, -1), (1, 0)], marker)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_marker_in_row0":
        paint_at(g, 5, w - 4, [(0, 0), (1, -2), (1, -1), (1, 0)], 4)
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 6)
        return g
    if name == "no_matching_body":
        g[0][3] = 4
        paint_at(g, 5, w - 4, [(0, 0), (1, -2), (1, -1), (1, 0)], 6)
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 7)
        return g
    if name == "multiple_matching_bodies":
        g[0][3] = 4
        paint_at(g, 5, w - 4, [(0, 0), (1, -2), (1, -1), (1, 0)], 4)
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 4)
        return g
    return g

def _sc_components(grid):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0: continue
            col = grid[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == col:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((col, cells))
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    markers = [v for v in grid[0] if v != 0]
    if len(markers) != 1: return [f"expected one row-0 marker, got {len(markers)}"]
    marker = markers[0]
    body = [row[:] for row in grid]
    body[0] = [0] * len(body[0])
    comps = _sc_components(body)
    matches = [c for c in comps if c[0] == marker]
    decoys = [c for c in comps if c[0] != marker]
    if len(matches) != 1: errs.append(f"expected one matching body blob, got {len(matches)}")
    if not (1 <= len(decoys) <= 5): errs.append(f"expected 1..5 decoys, got {len(decoys)}")
    return errs
