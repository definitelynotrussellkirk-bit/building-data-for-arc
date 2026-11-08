"""Generator for 8731374e.

Rule: largest near-solid rectangle contains dots whose rows and
columns become a cross-hatch crop.

Combinatorial axes (8): grid_h/w, dot_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
rect_kind.
Degenerates: no_rect, no_dots, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "291a029461ba"
VERSION = "3.0.0"  # canonical-scale noise-field scenes (75%) with a prefix-sum RULE MIRROR verifying the intended rect wins; the mirror also fixed a latent clean-scene bug (empty margin band out-areaing the rect) and now backs self_check
TASK_ID = "291a029461ba"
SUMMARY = (
    "0-bg grid (h, w sized to fit) with: "
    "(a) ONE SOLID FILLED RECTANGLE of "
    "size rh × rw (rh ∈ {4..7}, rw ∈ {4.."
    "8}) placed at random interior "
    "position, painted entirely in "
    "BG_COLOR (the rectangle's "
    "background, drawn from a kind-keyed "
    "palette); (b) 1-5 OUTLIER DOTS "
    "placed at random distinct interior "
    "cells of the rectangle (NOT at "
    "the top-left corner), each painted "
    "in DOT_COLOR (distinct from "
    "bg_color, palette[1]). The rectangle "
    "is the largest near-solid region in "
    "the grid. The top-left of the "
    "rectangle keeps bg_color. Rule "
    "(CROSS-HATCH CROP: THE LARGEST "
    "NEAR-SOLID RECTANGLE'S DOTS YIELD "
    "ROWS × COLUMNS THAT FORM A CROSS-"
    "HATCH OUTPUT): identify the "
    "LARGEST near-solid RECTANGLE (the "
    "one with most uniformly-colored "
    "interior cells). EXTRACT the DOT "
    "ROWS (rows in the rectangle "
    "containing dot_color cells) and "
    "DOT COLS (cols containing them). "
    "PRODUCE a CROSS-HATCH OUTPUT: a "
    "small grid where row × col "
    "intersections from the dot rows/"
    "cols are painted dot_color and "
    "the rest are bg_color (or "
    "vice-versa per demos). Net: the "
    "outlier dots are projected into "
    "a cross-hatch pattern on a small "
    "bg_color × dot_color output."
)

INVARIANTS = [
    "one near-solid rectangle is larger than any competing near-solid region",
    "the rectangle top-left cell gives the crop background color",
    "one to four interior outlier dots share a single dot color",
    "rectangle and dot colors are distinct and non-zero",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_rect", "no_dots", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12-16 easy / 15-22 med / 19-26 hard (noisy); rect+4-6 clean",
                       "valid": "8..26"},
    "grid_w":         {"type": "int", "default": "12-16 easy / 15-22 med / 19-26 hard (noisy); rect+4-6 clean",
                       "valid": "8..26"},
    "dot_count":      {"type": "int", "default": "1-2 easy / 1-4 med / 3-5 hard",
                       "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "rect_kind":      {"type": "str", "default": "solid", "valid": "solid"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _find_best_rect(g):
    """Mirror the rule's search: the LARGEST rect >=4x4 whose top-left color
    covers >4/5 of it with <=5 foreign cells (same lexicographic scan order,
    same strict-greater tie handling). Returns (r1, c1, r2, c2, color) or None."""
    h, w = len(g), len(g[0])
    pre = {}
    for color in range(10):
        p = [[0] * (w + 1) for _ in range(h + 1)]
        for r in range(h):
            row, prow, grow = p[r + 1], p[r], g[r]
            for c in range(w):
                row[c + 1] = row[c] + prow[c + 1] - prow[c] + (grow[c] == color)
        pre[color] = p
    best, best_area = None, 0
    for r1 in range(h):
        for c1 in range(w):
            p = pre[g[r1][c1]]
            for r2 in range(r1 + 3, h):
                for c2 in range(c1 + 3, w):
                    area = (r2 - r1 + 1) * (c2 - c1 + 1)
                    if area <= best_area:
                        continue
                    count = p[r2 + 1][c2 + 1] - p[r1][c2 + 1] - p[r2 + 1][c1] + p[r1][c1]
                    if area - count <= 5 and count * 5 > area * 4:
                        best_area, best = area, (r1, c1, r2, c2, g[r1][c1])
    return best


def self_check(grid, *, difficulty=None, meta=None):
    """Mirror the rule: a winning near-solid rect must exist, carrying 1-5
    foreign DOTS of one shared color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    best = _find_best_rect(grid)
    if best is None:
        return ["no rect satisfies the rule's near-solid acceptance test"]
    r1, c1, r2, c2, color = best
    dots = [(r, c, grid[r][c]) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if grid[r][c] != color]
    errs = []
    if not dots:
        errs.append("winning rect has no dots — the output would be a solid block")
    if len({v for _, _, v in dots}) > 1:
        errs.append("dots carry multiple colors — the rule paints only the first's")
    if len(dots) > 5:
        errs.append(f"{len(dots)} foreign cells exceed the rule's <=5 acceptance bound")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        dc_lo, dc_hi = 1, 2
        s_lo, s_hi, r_lo, r_hi = 12, 16, 5, 7
    elif difficulty == "hard":
        dc_lo, dc_hi = 3, 5
        s_lo, s_hi, r_lo, r_hi = 19, 26, 7, 11
    else:
        dc_lo, dc_hi = 1, 4
        s_lo, s_hi, r_lo, r_hi = 15, 22, 6, 9
    dot_count = ctx.draw_int("dot_count", dc_lo, dc_hi)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, rng)
    if len(pool) < 2:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in pool]
    bg_color, dot_color = pool[0], pool[1]
    # Canonical demos hide the rect in a DENSE 10-color noise field (~256
    # objects, 19x23-27x23 canvases); the old clean 0-bg strips drifted hard
    # (defect-lint: area 72-132 vs 391, obj_count 4 vs 256, 3 vs 10 colors).
    # Keep the clean scene as a 25% minority — both are rule-valid.
    noisy = rng.random() < 0.75
    if noisy:
        for _layout in range(40):
            h = ctx.draw_int("grid_h", s_lo, s_hi) if _layout == 0 else rng.randint(s_lo, s_hi)
            w = ctx.draw_int("grid_w", s_lo, s_hi) if _layout == 0 else rng.randint(s_lo, s_hi)
            rh = rng.randint(r_lo, min(r_hi, h - 2))
            rw = rng.randint(r_lo, min(r_hi, w - 2))
            g = [[rng.randint(0, 9) for _ in range(w)] for _ in range(h)]
            r0 = rng.randint(0, h - rh)
            c0 = rng.randint(0, w - rw)
            draw_rect(g, r0, c0, rh, rw, bg_color)
            cand = [(r, c) for r in range(r0, r0 + rh) for c in range(c0, c0 + rw)
                    if (r, c) != (r0, c0)]
            rng.shuffle(cand)
            for r, c in cand[:dot_count]:
                g[r][c] = dot_color
            # the rule's search must pick EXACTLY our rect (noise can, rarely,
            # form a competing near-solid region or extend ours by a lucky row)
            if _find_best_rect(g) == (r0, c0, r0 + rh - 1, c0 + rw - 1, bg_color):
                return g
        raise ValueError("could not hide the rect uniquely in the noise field")
    # clean 0-bg minority scene — mirror-verified too: a >=4-tall empty margin
    # band can out-area the intended rect (the rule would output a solid block;
    # a real latent defect of the old unverified path)
    for _layout in range(40):
        rh = rng.randint(4, 7)
        rw = rng.randint(4, 8)
        h = rh + 4 + rng.randint(0, 2)
        w = rw + 4 + rng.randint(0, 2)
        r0 = rng.randint(1, h - rh - 1)
        c0 = rng.randint(1, w - rw - 1)
        g = full_grid(h, w, 0)
        draw_rect(g, r0, c0, rh, rw, bg_color)
        candidates = [
            (r, c)
            for r in range(r0, r0 + rh)
            for c in range(c0, c0 + rw)
            if (r, c) != (r0, c0)
        ]
        rng.shuffle(candidates)
        for r, c in candidates[:dot_count]:
            g[r][c] = dot_color
        if _find_best_rect(g) == (r0, c0, r0 + rh - 1, c0 + rw - 1, bg_color):
            return g
    raise ValueError("could not make the intended rect win the rule's search")


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_rect":
        g[3][3] = 2
        return g
    if name == "no_dots":
        draw_rect(g, 2, 2, 5, 6, 1)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
