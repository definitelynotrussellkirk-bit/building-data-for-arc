"""Generator for 1c786137.

Rule: scan colors 1..9. The first color whose cells form >=80% of an
axis-aligned bbox border (>=8 cells total) is the "frame" — output is
its cropped interior.

Combinatorial axes (8): grid_h/w, frame_h/w, noise_density, frame_color,
palette_kind, position_bias.
Degenerates: no_frame, partial_frame, full_grid_noise.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a9e74ff84cae"
VERSION = "2.0.1"
TASK_ID = "a9e74ff84cae"
SUMMARY = (
    "0-bg grid (h~11-14, w~12-16) "
    "with: (a) ONE FRAME of "
    "border_color drawn as a "
    "full rectangle outline at "
    "(r0, c0)..(r1, c1) of size "
    "frame_h × frame_w (6-8 × "
    "5-7), placed by "
    "POSITION_BIAS "
    "(centered/corner/near_edge/"
    "anywhere); (b) NOISE CELLS "
    "in palette colors (warm/"
    "cool/broad/primary) at "
    "density 0.3-0.55, "
    "EXCLUDING the border. The "
    "border color uniquely "
    "forms a ≥80%-complete "
    "rectangular border ≥8 "
    "cells. Rule (FIND FRAME "
    "COLOR + CROP INTERIOR): "
    "SCAN colors 1..9 in order. "
    "For each color, COMPUTE "
    "its cells' bbox. CHECK "
    "if the cells form ≥80% of "
    "the bbox perimeter (border "
    "match count * 5 > 4 * "
    "perimeter) AND have ≥8 "
    "cells. The FIRST color "
    "satisfying this is the "
    "FRAME COLOR. CROP to the "
    "INTERIOR of the frame's "
    "bbox (excluding border "
    "cells). Output: the "
    "cropped interior of the "
    "frame's bbox. Net: locate "
    "the boundary color, crop "
    "out its interior."
)

# Rivals: 'output is input' refuted by demos (output is small).
# 'output is bbox including border' refuted by demos (border drops).
# 'output is bbox of any color' refuted by demos with non-frame
# colors. 'recolor on crop' refuted by demos preserving cell colors.
# 3 demos with varied frame colors + noise cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one color forms a full rectangular border (>=80% of perimeter, >=8 cells)",
    "border color does not appear elsewhere in the grid",
    "noise cells use other colors and don't form a competing 8+ rectangle border",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "anywhere")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "partial_frame", "full_grid_noise")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "frame_h":        {"type": "int", "default": "rng 6..8", "valid": "5..10"},
    "frame_w":        {"type": "int", "default": "rng 5..7", "valid": "5..9"},
    "noise_density":  {"type": "float", "default": "rng 0.3..0.55", "valid": "0.1..0.7"},
    "frame_color":    {"type": "color", "default": "rng 1..9", "valid": "1..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color forms ≥8 cells that outline a rectangular border (≥80% perimeter)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    from collections import defaultdict
    color_cells: dict[int, list] = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                color_cells[grid[r][c]].append((r, c))
    # Look for a frame color
    found_frame = False
    for color, cells in color_cells.items():
        if len(cells) < 8:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r0, c0, r1, c1 = min(rs), min(cs), max(rs), max(cs)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        # Perimeter cells
        perim = set()
        for c in range(c0, c1 + 1): perim.add((r0, c)); perim.add((r1, c))
        for r in range(r0 + 1, r1): perim.add((r, c0)); perim.add((r, c1))
        match = sum(1 for cell in cells if cell in perim)
        if match * 5 > 4 * len(perim):
            found_frame = True
            break
    if not found_frame:
        return errs  # degenerate (no_frame / partial_frame / full_grid_noise) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 9, 11, 10, 12
        fh_lo, fh_hi, fw_lo, fw_hi = 5, 6, 5, 6
        d_lo, d_hi = 0.25, 0.40
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 18, 15, 20
        fh_lo, fh_hi, fw_lo, fw_hi = 7, 9, 6, 8
        d_lo, d_hi = 0.45, 0.65
    else:
        h_lo, h_hi, w_lo, w_hi = 11, 14, 12, 16
        fh_lo, fh_hi, fw_lo, fw_hi = 6, 8, 5, 7
        d_lo, d_hi = 0.30, 0.55
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    border_color = int(overrides.get("frame_color",
                                     rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])))
    rh = int(overrides.get("frame_h",
                           rng.randint(fh_lo, min(fh_hi, h - 2))))
    rw = int(overrides.get("frame_w",
                           rng.randint(fw_lo, min(fw_hi, w - 2))))
    rh = max(3, min(rh, h - 2))
    rw = max(3, min(rw, w - 2))
    r0, c0 = _pick_frame_pos(bias, h, w, rh, rw, rng)
    r1 = r0 + rh - 1
    c1 = c0 + rw - 1
    border_set = set()
    for c in range(c0, c1 + 1):
        g[r0][c] = border_color
        g[r1][c] = border_color
        border_set.add((r0, c))
        border_set.add((r1, c))
    for r in range(r0 + 1, r1):
        g[r][c0] = border_color
        g[r][c1] = border_color
        border_set.add((r, c0))
        border_set.add((r, c1))
    palette = _build_palette(palette_kind, border_color, rng)
    density = float(overrides.get("noise_density", rng.uniform(d_lo, d_hi)))
    n_noise = int(h * w * density)
    for _ in range(n_noise):
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if (r, c) in border_set:
            continue
        if g[r][c] != 0:
            continue
        g[r][c] = rng.choice(palette)
    return g


def _pick_frame_pos(bias, h, w, rh, rw, rng):
    max_r = h - rh - 1
    max_c = w - rw - 1
    if bias == "centered":
        r0 = max(1, (h - rh) // 2 + rng.randint(-1, 1))
        c0 = max(1, (w - rw) // 2 + rng.randint(-1, 1))
    elif bias == "corner":
        r0 = rng.choice([1, max(1, max_r)])
        c0 = rng.choice([1, max(1, max_c)])
    elif bias == "near_edge":
        if rng.random() < 0.5:
            r0 = rng.choice([1, max(1, max_r)])
            c0 = rng.randint(1, max(1, max_c))
        else:
            r0 = rng.randint(1, max(1, max_r))
            c0 = rng.choice([1, max(1, max_c)])
    else:
        r0 = rng.randint(1, max(1, max_r))
        c0 = rng.randint(1, max(1, max_c))
    r0 = max(1, min(r0, max(1, max_r)))
    c0 = max(1, min(c0, max(1, max_c)))
    return r0, c0


def _build_palette(kind, exclude_color, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    palette = [c for c in pool if c != exclude_color]
    if not palette:
        palette = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != exclude_color]
    rng.shuffle(palette)
    return palette


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_frame":
        for _ in range(int(0.4 * h * w)):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        return g
    if name == "partial_frame":
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        r0, c0, rh, rw = 2, 3, 6, 7
        r1, c1 = r0 + rh - 1, c0 + rw - 1
        for c in range(c0, c1 + 1):
            g[r0][c] = color
        for r in range(r0, r1 + 1):
            g[r][c0] = color
        return g
    if name == "full_grid_noise":
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        return g
    return g
