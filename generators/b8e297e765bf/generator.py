"""Generator for puzzle de1cd16c.

Rule: scan colors 0..9. Among those with cells filling >=50% of their
bbox, pick the one with most foreign (non-color) cells. Output 1x1 of
that color.

Combinatorial axes (8): grid_h/w, n_quadrants, palette_kind,
winner_noise_min, loser_noise_max, noise_color, anchor_corner,
asymmetry_force.
Degenerates: tied_noise, no_noise, monochrome.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b8e297e765bf"
VERSION = "2.2.0"  # fix low_output_diversity: choose the winner color first from the full non-noise palette, then draw distractor colors around it.
TASK_ID = "b8e297e765bf"
SUMMARY = (
    "EVEN-DIM grid (h, w~"
    "12-18, both even) "
    "split into 4 QUADRANTS "
    "(TL/TR/BL/BR). Each "
    "QUADRANT filled with "
    "one of 4 DISTINCT "
    "BASE COLORS from a "
    "palette (warm/cool/"
    "broad/primary, "
    "excluding noise "
    "color). Each quadrant "
    "has scattered NOISE "
    "(COLOR-4 by default) "
    "cells: 7-10 noise "
    "cells in the WINNING "
    "quadrant, 1-3 in the "
    "others. EXACTLY ONE "
    "quadrant has the "
    "highest noise count "
    "(unambiguous winner). "
    "Output uniq_out=8 "
    "(intrinsic — output "
    "is a 1×1 grid of the "
    "winning quadrant's "
    "color, with ~8 "
    "palette × few "
    "winner colors). "
    "Rule (EMIT 1×1 OF "
    "MOST-NOISY "
    "QUADRANT's COLOR): "
    "For EACH non-zero, "
    "non-noise color C in "
    "the grid: COUNT "
    "noise cells in C's "
    "filled region. Pick "
    "the C with MAX noise "
    "count. EMIT a 1×1 "
    "grid of color C. "
    "Net: most-noisy "
    "quadrant's color "
    "wins; output is a "
    "single cell."
)

INVARIANTS = [
    "h, w both even and >=12",
    "4 quadrants each filled with one of 4 distinct non-noise colors",
    "scattered noise(=4) cells in each quadrant",
    "exactly one quadrant has strictly more noise than others",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("tied_noise", "no_noise", "monochrome")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 12..18 (even)",
                         "valid": "10..22"},
    "grid_w":           {"type": "int", "default": "rng 12..18 (even)",
                         "valid": "10..22"},
    "palette_kind":     {"type": "str", "default": "rng helpful",
                         "valid": "warm|cool|broad|primary"},
    "winner_noise_min": {"type": "int", "default": "7", "valid": "5..15"},
    "winner_noise_max": {"type": "int", "default": "rng 8..10",
                         "valid": "6..18"},
    "loser_noise_max":  {"type": "int", "default": "3", "valid": "1..5"},
    "noise_color":      {"type": "color", "default": "4", "valid": "1..9"},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for palette_kind",
                         "valid": "warm|cool|broad|primary|tied_noise|no_noise|monochrome"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 12
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    if h % 2:
        h += 1
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    if w % 2:
        w += 1
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    noise_color = int(overrides.get("noise_color", 4))
    # The rule emits a 1x1 grid containing the most-noisy quadrant's base
    # color, so output diversity is label diversity.  The old path chose the
    # four quadrant colors first from kind-restricted palettes and then tried to
    # overwrite the winner.  The overwrite was often blocked by distractor
    # collisions, leaving only five distinct labels across the standard 24-seed
    # defect-lint probe.  Pick the winner label FIRST from the full non-noise
    # palette, then draw distractors from the remaining colors.
    non_noise = [c for c in range(1, 10) if c != noise_color]
    winner_color = non_noise[(sample_index - 1) % len(non_noise)]
    distractors = _build_palette(palette_kind, 3, rng, exclude={0, noise_color, winner_color})

    win_min = int(overrides.get("winner_noise_min", 7))
    win_max = int(overrides.get("winner_noise_max",
                                ctx.draw_int("winner_noise_max", 8, 10)))
    lose_max = int(overrides.get("loser_noise_max", 3))
    win_min = max(1, win_min)
    win_max = max(win_min, win_max)
    g = full_grid(h, w, 0)
    mr = h // 2
    mc = w // 2
    quads = [(0, 0, mr, mc), (0, mc, mr, w),
             (mr, 0, h, mc), (mr, mc, h, w)]
    winner_idx = rng.randint(0, 3)
    palette = []
    distractor_iter = iter(distractors)
    for i in range(4):
        palette.append(winner_color if i == winner_idx else next(distractor_iter))
    for i, (r0, c0, r1, c1) in enumerate(quads):
        color = palette[i]
        for r in range(r0, r1):
            for c in range(c0, c1):
                g[r][c] = color
        if i == winner_idx:
            n_noise = rng.randint(win_min, win_max)
        else:
            n_noise = rng.randint(1, max(1, lose_max))
        placed = 0
        for _ in range(120):
            if placed >= n_noise:
                break
            r = rng.randint(r0, r1 - 1)
            c = rng.randint(c0, c1 - 1)
            if g[r][c] == color:
                g[r][c] = noise_color
                placed += 1
    return g


def _build_palette(kind, n, rng, exclude):
    if kind == "warm":
        pool = [2, 3, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c not in exclude]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 5, 6, 7, 8, 9]:
            if c not in pool and c not in exclude:
                pool.append(c)
    return pool[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 5, 6, 7, 8, 9], 4)
    mr = h // 2; mc = w // 2
    quads = [(0, 0, mr, mc), (0, mc, mr, w),
             (mr, 0, h, mc), (mr, mc, h, w)]
    if name == "tied_noise":
        for i, (r0, c0, r1, c1) in enumerate(quads):
            for r in range(r0, r1):
                for c in range(c0, c1):
                    g[r][c] = palette[i]
            for _ in range(3):
                r = rng.randint(r0, r1 - 1)
                c = rng.randint(c0, c1 - 1)
                g[r][c] = 4
        return g
    if name == "no_noise":
        for i, (r0, c0, r1, c1) in enumerate(quads):
            for r in range(r0, r1):
                for c in range(c0, c1):
                    g[r][c] = palette[i]
        return g
    if name == "monochrome":
        for r in range(h):
            for c in range(w):
                g[r][c] = palette[0]
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errors = []
    if h % 2 or w % 2:
        errors.append("grid dimensions must be even")
    mr, mc = h // 2, w // 2
    quads = [(0, 0, mr, mc), (0, mc, mr, w), (mr, 0, h, mc), (mr, mc, h, w)]
    base_colors = []
    noise_counts = []
    for r0, c0, r1, c1 in quads:
        vals = [grid[r][c] for r in range(r0, r1) for c in range(c0, c1)]
        non_noise = [v for v in vals if v not in (0, 4)]
        if not non_noise:
            errors.append("quadrant lacks a base color")
            continue
        base = max(set(non_noise), key=non_noise.count)
        base_colors.append(base)
        noise_counts.append(vals.count(4))
    if len(base_colors) == 4 and len(set(base_colors)) != 4:
        errors.append("quadrant base colors must be distinct")
    if len(noise_counts) == 4:
        if min(noise_counts) < 1:
            errors.append("each quadrant should contain at least one noise cell")
        if noise_counts.count(max(noise_counts)) != 1:
            errors.append(f"winner noise count must be unique, got {noise_counts}")
    return sorted(set(errors))
