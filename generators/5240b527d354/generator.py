"""Generator for 5240b527d354 / 67636eac.

Rule: separated same-color motifs are cropped to their per-color bounding boxes and
concatenated along the dominant spatial axis.

Canonical train examples use compact 3x3 motifs (connected plus/U shapes or
diagonal X-shapes) placed far apart horizontally or vertically.  The rule groups by
color, not by connected component, so an X-shaped color may appear as five
4-neighbor objects while still being one cropped motif.  This generator stays in
that canonical regime instead of emitting only connected tetrominoes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5240b527d354"
VERSION = "2.3.0"  # canonical compact 3x3 motif regime; allows disconnected X motifs by color
TASK_ID = "5240b527d354"
SUMMARY = (
    "0-bg grid with 2-3 compact same-color 3x3 motifs, placed far apart along one "
    "dominant axis.  Each nonzero color defines one motif by its bounding box; the "
    "motif may be an X with diagonally separated cells, matching canonical examples "
    "where color-shapes are not necessarily 4-connected.  Rule: crop each color's "
    "bbox, sort motifs by their spatial centers along the dominant axis, and "
    "concatenate the crops horizontally or vertically."
)

INVARIANTS = [
    "background is color 0",
    "2-3 nonzero colors, each defining one compact 3x3 motif",
    "motifs are separated and their centers have a clear horizontal or vertical order",
    "motifs may be disconnected by 4-neighborhood; the task groups cells by color",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "single_shape", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..16", "valid": "8..22"},
    "grid_w":         {"type": "int", "default": "rng 10..18", "valid": "8..22"},
    "shape_count":    {"type": "int", "default": "rng 2 / hard 3", "valid": "2..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "dominant_axis", "valid": "dominant_axis"},
    "n_distinct_colors":{"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# Canonical compact motifs.  X is intentionally not 4-connected; the canonical rule
# still treats it as one shape because it groups by color and crops a color bbox.
_X3 = ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2))
_PLUS3 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_U3 = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2))
_PATTERNS = (_X3, _X3, _PLUS3, _U3)  # bias toward X so object-count matches canonical medians


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "hard":
        n_lo, n_hi = 3, 3
    else:
        n_lo, n_hi = 2, 2
    n = max(2, min(3, ctx.draw_int("shape_count", n_lo, n_hi)))
    horizontal = ((seed + sample_index) % 2 == 0)

    if horizontal:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", max(12, 5 * n + 4), min(22, 5 * n + 8))
        r_base = rng.randint(1, h - 4)
        starts = [(r_base + (i % 2), 1 + i * 5) for i in range(n)]
    else:
        h = ctx.draw_int("grid_h", max(12, 5 * n + 4), min(22, 5 * n + 8))
        w = ctx.draw_int("grid_w", 10, 14)
        c_base = rng.randint(1, w - 4)
        starts = [(1 + i * 5, c_base + (i % 2)) for i in range(n)]

    g = full_grid(h, w, 0)
    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude={0}))
    for i, color in enumerate(colors):
        r0, c0 = starts[i]
        pattern = _PATTERNS[(sample_index + seed + i) % len(_PATTERNS)]
        for dr, dc in pattern:
            g[r0 + dr][c0 + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_shapes":
        return g
    if name == "single_shape":
        for dr, dc in _PLUS3:
            g[3 + dr][3 + dc] = 2
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 2
        return g
    return g


def _color_infos(grid):
    colors = sorted({v for row in grid for v in row if v != 0})
    infos = []
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        infos.append({
            "color": color,
            "cells": cells,
            "r1": min(rs), "r2": max(rs),
            "c1": min(cs), "c2": max(cs),
            "cr": (min(rs) + max(rs)) / 2.0,
            "cc": (min(cs) + max(cs)) / 2.0,
        })
    return infos


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty rectangular list-of-lists"]
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("grid colors should be ARC digits 0..9")

    infos = _color_infos(grid)
    if not (2 <= len(infos) <= 3):
        errs.append(f"expected 2..3 nonzero color motifs, got {len(infos)}")
    centers = []
    for info in infos:
        sh = info["r2"] - info["r1"] + 1
        sw = info["c2"] - info["c1"] + 1
        n_cells = len(info["cells"])
        if sh != 3 or sw != 3:
            errs.append(f"color {info['color']} should have a compact 3x3 bbox, got {sh}x{sw}")
        if n_cells < 4:
            errs.append(f"color {info['color']} should have a visible multi-cell motif, got {n_cells} cells")
        centers.append((info["cr"], info["cc"]))

    if len(centers) >= 2:
        row_spread = max(r for r, _ in centers) - min(r for r, _ in centers)
        col_spread = max(c for _, c in centers) - min(c for _, c in centers)
        if max(row_spread, col_spread) < 4:
            errs.append(f"motif centers need a clear dominant axis, got {centers}")
        if min(row_spread, col_spread) > max(row_spread, col_spread) / 2.0:
            errs.append(f"motifs should vary mainly along one axis, got centers {centers}")
    return errs
