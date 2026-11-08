"""Generator for 652646ff.

Rule: on a DOMINANT canvas color (bg = the most-frequent non-zero color),
several 6x6 hex outlines (a fixed 12-cell hexagon stencil) are drawn in other
colors and may partially OVERLAP/occlude each other. The rule detects each
hex color (fitting its remaining cells to the stencil; colors that don't fit
or have <4 cells are dropped as noise), resolves the occlusion z-order from
which color covers each hex's missing cells (blocker dependencies), and
restacks the hexes as COMPLETE outlines vertically: an (n*6) x 6 grid on the
canvas color, one full hex per 6-row band, ordered so blockers come after the
hexes they occlude.

v1.1.0 used a 0-background with 2-3 COMPLETE non-overlapping hexes at 3 fixed
positions on a fixed 17x18 grid. That mis-modelled the rule (bg = mode = the
most-frequent *hex* color, so a hex was arbitrarily treated as background) and
exercised no occlusion. v2.0.0 fills the grid with a dominant canvas color,
draws 2-5 OVERLAPPING hexes (back-to-front z-order) plus light noise, with a
Python mirror of the rule's hex-detection gating every instance so exactly the
intended n hexes are detected.

Combinatorial axes: grid size, canvas color, hex count, positions, occlusion
z-order, hex colors, noise.
Degenerates: no_hexes, single_hex, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fa874c2eb1d1"
RULE_HASH = "06230def3911"  # canonical rule this generator was written against
VERSION = "2.1.1"  # literal AXES valid-domains so lint_generator can validate types (repo_help patch); self_check + canvas/occlusion behavior unchanged
TASK_ID = "fa874c2eb1d1"
SUMMARY = (
    "Grid filled with a DOMINANT CANVAS color (the most-frequent non-zero "
    "color) on which 2-5 colored 6x6 HEX OUTLINES (a fixed 12-cell hexagon "
    "stencil) are drawn, each a distinct color != canvas. The hexes may "
    "OVERLAP: drawn back-to-front, a front hex overwrites cells of hexes "
    "behind it, so back hexes appear PARTIALLY OCCLUDED. A little NOISE "
    "(stray <4-cell fragments) may also appear. Rule: bg = the dominant "
    "canvas color; detect every other color's hex outline (fit remaining "
    "cells to the stencil; colors with <4 cells or no fit are dropped as "
    "noise); infer the occlusion z-order from which color covers each hex's "
    "missing cells (blocker dependencies); and OUTPUT the hexes restacked as "
    "COMPLETE outlines — an (n*6) x 6 grid on the canvas color, one full hex "
    "per 6-row band, ordered so blockers follow the hexes they occlude. (Was "
    "a 0-bg fixed 17x18 grid with 3 complete non-overlapping hexes.)"
)

INVARIANTS = [
    "the grid is filled with a dominant non-zero canvas color (the rule's bg)",
    "each hex color != canvas and has >=4 cells fitting the 6x6 hex stencil (detectable)",
    "no hex is fully occluded — exactly the intended n hexes are detected",
    "hexes may partially overlap, creating a resolvable occlusion z-order",
    "noise fragments have <4 cells so the rule drops them",
]

HEX_COUNT_KINDS = ("h2", "h3", "h4", "h5")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_hexes", "single_hex", "full_grid")
HELPFUL_TEXTURES = HEX_COUNT_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "14-18 easy / 16-22 med / 18-28 hard", "valid": "12..30"},
    "grid_w":         {"type": "int", "default": "14-18 easy / 16-22 med / 18-28 hard", "valid": "12..30"},
    "hex_count":      {"type": "choice", "default": "rng helpful", "valid": "2|3|4|5"},
    "canvas_color":   {"type": "color", "default": "rng non-0", "valid": "1..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       # literal so lint_generator can validate the domain (keep in sync with PALETTE_KINDS)
                       "valid": "warm|cool|broad|primary"},
    "allow_overlap":  {"type": "bool", "default": "rng", "valid": "true|false"},
    "noise":          {"type": "bool", "default": "rng", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "= hex count + 1", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors":{"type": "int", "default": "= hex count + canvas", "valid": "3..7"},
    "texture":        {"type": "str", "default": "alias for hex_count",
                       # literal so lint validates domain (keep in sync with HELPFUL_TEXTURES+DEGENERATE_TEXTURES)
                       "valid": "h2|h3|h4|h5|no_hexes|single_hex|full_grid"},
}

HEX = [(0, 2), (0, 3), (1, 1), (1, 4), (2, 0), (2, 5),
       (3, 0), (3, 5), (4, 1), (4, 4), (5, 2), (5, 3)]
_HEXSET = set(HEX)


def _draw_hex(g, r0, c0, color):
    for dr, dc in HEX:
        g[r0 + dr][c0 + dc] = color


def _fits_hex(cells):
    """Mirror of the rule's detection: cells (>=4) fit the hex stencil at some
    translation, with bbox span <= 5 in each dim."""
    if len(cells) < 4:
        return False
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    mnr, mxr, mnc, mxc = min(rs), max(rs), min(cs), max(cs)
    if mxr - mnr > 5 or mxc - mnc > 5:
        return False
    for tr in range(max(0, mxr - 5), mnr + 1):
        for tc in range(max(0, mxc - 5), mnc + 1):
            if all((r - tr, c - tc) in _HEXSET for r, c in cells):
                return True
    return False


def _color_cells(g, col):
    return [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == col]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    tx = overrides.get("texture")
    if tx in HEX_COUNT_KINDS:
        count = int(tx[1])
    elif difficulty == "easy":
        count = rng.randint(2, 3)
    elif difficulty == "hard":
        count = rng.randint(4, 5)
    else:
        count = ctx.draw_choice("hex_count", [2, 3, 4])

    if difficulty == "easy":
        hr, wr = (14, 18), (14, 18)
    elif difficulty == "hard":
        hr, wr = (18, 28), (18, 28)
    else:
        hr, wr = (16, 22), (16, 22)

    allow_overlap = bool(overrides.get("allow_overlap", rng.choice([True, True, False])))
    add_noise = bool(overrides.get("noise", rng.choice([True, False])))

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        # canvas color (the dominant bg) + count distinct hex colors, all distinct.
        pal = list(ctx.draw_distinct_colors("colors", n=count + 1, exclude={0}))
        canvas, hex_colors = pal[0], pal[1:]
        g = full_grid(h, w, canvas)

        positions = []
        ok = True
        for _i in range(count):
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - 6); c0 = rng.randint(0, w - 6)
                if allow_overlap:
                    if (r0, c0) in positions:
                        continue
                    placed = True
                else:
                    if any(abs(r0 - pr) < 7 and abs(c0 - pc) < 7 for pr, pc in positions):
                        continue
                    placed = True
                if placed:
                    positions.append((r0, c0)); break
            if not placed:
                ok = False; break
        if not ok:
            continue

        for (r0, c0), color in zip(positions, hex_colors):   # back -> front
            _draw_hex(g, r0, c0, color)

        # light noise: a few stray cells in a fresh color (<4 -> rule drops them)
        if add_noise:
            noise_pool = [c for c in range(1, 10) if c not in pal]
            if noise_pool:
                ncol = rng.choice(noise_pool)
                for _ in range(rng.randint(1, 3)):
                    g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = ncol

        # GATE: every hex color must remain detectable (>=4 cells fitting the
        # stencil) so the rule restacks exactly `count` hexes; canvas stays bg.
        if all(_fits_hex(_color_cells(g, col)) for col in hex_colors):
            return g

    # deterministic fallback: 2 complete non-overlapping hexes on a canvas.
    g = full_grid(14, 14, 2)
    _draw_hex(g, 1, 1, 3)
    _draw_hex(g, 1, 8, 4)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify dominant-canvas hex gallery instances are detectable."""
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30 or h < 12 or w < 12:
        errors.append(f"grid {h}x{w} outside expected 12..30 bounds")
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    if 0 in counts:
        errors.append("default canvas task should not use 0; bg is the dominant non-zero canvas color")
    nonzero_counts = {k: v for k, v in counts.items() if k != 0}
    if not nonzero_counts:
        return errors + ["no non-zero canvas/hex colors"]
    canvas = max(nonzero_counts, key=nonzero_counts.get)
    area = h * w
    if nonzero_counts[canvas] <= area // 2:
        errors.append(f"canvas color {canvas} is not dominant enough ({nonzero_counts[canvas]}/{area})")
    hex_colors = []
    for color in sorted(c for c in nonzero_counts if c != canvas):
        cells = _color_cells(grid, color)
        if len(cells) < 4:
            continue  # intended droppable noise fragment
        if not _fits_hex(cells):
            errors.append(f"color {color} has {len(cells)} cells but does not fit the 6x6 hex stencil")
        else:
            hex_colors.append(color)
    if not (2 <= len(hex_colors) <= 5):
        errors.append(f"expected 2..5 detectable hex colors, found {len(hex_colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(17, 18, 2)            # canvas color 2
    if name == "no_hexes":
        return g                        # canvas only — no hexes to restack
    if name == "single_hex":
        _draw_hex(g, 1, 1, 3)
        return g
    if name == "full_grid":
        for r in range(17):
            for c in range(18):
                g[r][c] = 3
        return g
    return g
