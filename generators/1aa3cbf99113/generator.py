"""Generator for 52a5d390.

Rule: each non-bg 4-connected object recolored to 2 if size ≤ 3, else 8.

Combinatorial axes (8):
  * grid_h / grid_w        — outer canvas size
  * n_small_objects        — objects with ≤3 cells (will become 2)
  * n_large_objects        — objects with ≥4 cells (will become 8)
  * small_kind             — single / pair_h / pair_v / pair_diag /
                             triple_L / triple_line / triple_diag
  * large_kind             — rect / L / cross / line_h / line_v / blob /
                             hollow_ring / Z_shape
  * size_progression       — how large objects' sizes vary
                             (linear / mixed / large_only)
  * placement              — random / corners / row / column / grid
  * input_palette_mode     — same_color / all_distinct / per_size_group
  * caller-opt-in degenerates: only_small (rule paints all 2),
                               only_large (rule paints all 8),
                               touching_objects (4-conn merges)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1aa3cbf99113"
VERSION = "2.1.1"  # cap palette draw at 7 avail colors (hard n_small=4+n_large=3 wanted 8)
TASK_ID = "1aa3cbf99113"
SUMMARY = (
    "0-bg grid (h, w ~8-16) with N_small (1-4) SMALL "
    "objects of size ≤3 (singles, pairs, triples) and "
    "N_large (1-3) LARGE objects of size ≥4 (rectangles, "
    "L/cross/blob/Z shapes, hollow rings). All objects "
    "are 4-disconnected (1-cell buffer); input colors "
    "drawn from non-{0, 2, 8} palette so the rule's "
    "output colors are unambiguous. Rule: extract all "
    "4-conn non-bg objects. For each object: if "
    "obj-size ≤ 3 → recolor every cell to color 2 (red); "
    "if obj-size ≥ 4 → recolor to color 8 (cyan). Net: a "
    "size-thresholded recolor with cutoff at 3."
)

INVARIANTS = [
    "background is 0",
    "≥1 small object (size ≤ 3, becomes 2)",
    "≥1 large object (size ≥ 4, becomes 8)",
    "objects 4-disconnected",
]

SMALL_KINDS = ("single", "pair_h", "pair_v", "pair_diag",
               "triple_L", "triple_line", "triple_diag")
LARGE_KINDS = ("rect", "L_shape", "cross", "line_h", "line_v",
               "blob", "hollow_ring", "Z_shape")
SIZE_PROGRESSIONS = ("linear", "mixed", "large_only")
PLACEMENTS = ("random", "corners", "row", "column", "grid")
PALETTE_MODES = ("same_color", "all_distinct", "per_size_group")
DEGENERATE_TEXTURES = ("only_small", "only_large", "touching_objects")
HELPFUL_TEXTURES = LARGE_KINDS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 8..16", "valid": "6..22"},
    "grid_w":             {"type": "int", "default": "rng 8..16", "valid": "6..22"},
    "n_small_objects":    {"type": "int", "default": "rng 1..4", "valid": "0..8"},
    "n_large_objects":    {"type": "int", "default": "rng 1..3", "valid": "0..6"},
    "small_kind":         {"type": "str", "default": "rng helpful",
                           "valid": "single|pair_h|pair_v|pair_diag|triple_L|triple_line|triple_diag"},
    "large_kind":         {"type": "str", "default": "rng helpful",
                           "valid": "rect|L_shape|cross|line_h|line_v|blob|hollow_ring|Z_shape"},
    "size_progression":   {"type": "str", "default": "rng linear|mixed|large_only",
                           "valid": "linear|mixed|large_only"},
    "placement":          {"type": "str", "default": "rng helpful",
                           "valid": "random|corners|row|column|grid"},
    "input_palette_mode": {"type": "str", "default": "rng helpful",
                           "valid": "same_color|all_distinct|per_size_group"},
    "texture":            {"type": "str", "default": "alias for large_kind",
                           "valid": "rect|L_shape|cross|line_h|line_v|blob|hollow_ring|Z_shape|only_small|only_large|touching_objects"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, ns_lo, ns_hi, nl_lo, nl_hi = 8, 10, 1, 2, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, ns_lo, ns_hi, nl_lo, nl_hi = 13, 16, 3, 4, 2, 3
    else:
        h_lo, h_hi, ns_lo, ns_hi, nl_lo, nl_hi = 8, 16, 1, 4, 1, 3

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, ctx, rng)

    n_small = int(overrides.get("n_small_objects",
                                ctx.draw_int("n_small_objects", ns_lo, ns_hi)))
    n_large = int(overrides.get("n_large_objects",
                                ctx.draw_int("n_large_objects", nl_lo, nl_hi)))
    small_kind = overrides.get("small_kind",
                               ctx.draw_choice("small_kind", list(SMALL_KINDS)))
    large_kind = (overrides.get("texture") or overrides.get("large_kind")
                  or ctx.draw_choice("large_kind", list(LARGE_KINDS)))
    progression = overrides.get("size_progression",
                                ctx.draw_choice("size_progression", list(SIZE_PROGRESSIONS)))
    placement = overrides.get("placement",
                              ctx.draw_choice("placement", list(PLACEMENTS)))
    palette_mode = overrides.get("input_palette_mode",
                                 ctx.draw_choice("input_palette_mode", list(PALETTE_MODES)))

    # Excluding {0, 2, 8} leaves only 7 usable colors ({1,3,4,5,6,7,9}), so the
    # palette can hold at most 7. Hard draws n_small=4 + n_large=3 → the +1 made
    # this request 8 distinct → "draw_distinct_colors want 8". Cap at 7; the
    # color-assignment modes already reuse colors gracefully when objects > palette.
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=min(7, max(2, n_small + n_large + 1)),
                                            exclude={0, 2, 8}))
    g = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()

    n_total = n_small + n_large
    anchors = _anchors(placement, h, w, n_total, rng)
    colors = _colors_for_mode(palette_mode, palette, n_small, n_large, rng)
    color_idx = 0

    for i in range(n_large):
        for _try in range(20):
            sh, sw = _large_dims(progression, i, h, w, rng)
            ar, ac = (anchors[color_idx]
                      if color_idx < len(anchors) else (rng.randint(1, h - 4),
                                                       rng.randint(1, w - 4)))
            ar = min(max(0, ar), max(0, h - sh - 1))
            ac = min(max(0, ac), max(0, w - sw - 1))
            cells = _large_cells(large_kind, sh, sw)
            actual = [(ar + dr, ac + dc) for dr, dc in cells]
            buffer = set()
            for (r, c) in actual:
                for ddr in (-1, 0, 1):
                    for ddc in (-1, 0, 1):
                        buffer.add((r + ddr, c + ddc))
            if any(p in occupied for p in buffer):
                continue
            color = colors[color_idx % len(colors)]
            color_idx += 1
            for (r, c) in actual:
                if 0 <= r < h and 0 <= c < w:
                    g[r][c] = color
                    occupied.add((r, c))
            break

    for i in range(n_small):
        for _try in range(20):
            cells = _small_cells(small_kind, rng)
            ar = rng.randint(1, max(1, h - 4))
            ac = rng.randint(1, max(1, w - 4))
            actual = [(ar + dr, ac + dc) for dr, dc in cells]
            buffer = set()
            for (r, c) in actual:
                for ddr in (-1, 0, 1):
                    for ddc in (-1, 0, 1):
                        buffer.add((r + ddr, c + ddc))
            if any(p in occupied for p in buffer):
                continue
            color = colors[color_idx % len(colors)]
            color_idx += 1
            for (r, c) in actual:
                if 0 <= r < h and 0 <= c < w:
                    g[r][c] = color
                    occupied.add((r, c))
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one non-bg cell (skip degenerate textures)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    nonzero = [grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-bg cells found (expected small and large objects)")
    # check input colors are not 2 or 8 (reserved for output recoloring)
    bad = [v for v in nonzero if v in (2, 8)]
    if bad:
        errs.append(f"input contains reserved output colors 2/8: {set(bad)}")
    return errs


def _anchors(placement, h, w, n, rng):
    margin = 1
    if placement == "corners":
        return [(margin, margin), (margin, w - margin - 5),
                (h - margin - 5, margin), (h - margin - 5, w - margin - 5)][:n]
    if placement == "row":
        gap = max(1, (w - 2 * margin) // max(1, n))
        return [(rng.randint(margin, h // 2), margin + i * gap) for i in range(n)]
    if placement == "column":
        gap = max(1, (h - 2 * margin) // max(1, n))
        return [(margin + i * gap, rng.randint(margin, w // 2)) for i in range(n)]
    if placement == "grid":
        cols = 3 if n > 4 else 2
        return [(margin + (i // cols) * max(3, h // 4),
                 margin + (i % cols) * max(3, w // 4)) for i in range(n)]
    return [(rng.randint(margin, max(margin, h - 6)),
             rng.randint(margin, max(margin, w - 6))) for _ in range(n)]


def _large_dims(progression, idx, h, w, rng):
    if progression == "linear":
        s = 4 + idx
    elif progression == "large_only":
        s = rng.randint(5, 7)
    else:
        s = rng.randint(4, 7)
    sh = min(s, max(2, h // 4))
    sw = min(s, max(2, w // 4))
    return max(2, sh), max(2, sw)


def _colors_for_mode(mode, palette, n_small, n_large, rng):
    n_total = n_small + n_large
    if mode == "same_color":
        return [palette[0]] * n_total
    if mode == "per_size_group":
        a = palette[0]; b = palette[1] if len(palette) > 1 else palette[0]
        return [a] * n_large + [b] * n_small
    if mode == "all_distinct":
        if len(palette) >= n_total:
            return list(palette[:n_total])
        return list(palette) + [palette[0]] * (n_total - len(palette))
    return [rng.choice(palette) for _ in range(n_total)]


def _large_cells(kind, sh, sw):
    if kind == "rect":
        return [(dr, dc) for dr in range(sh) for dc in range(sw)]
    if kind == "L_shape":
        out = [(dr, 0) for dr in range(sh)]
        out += [(sh - 1, dc) for dc in range(1, sw)]
        return out
    if kind == "cross":
        mr, mc = sh // 2, sw // 2
        out = [(mr, dc) for dc in range(sw)]
        out += [(dr, mc) for dr in range(sh) if dr != mr]
        return list(set(out))
    if kind == "line_h":
        return [(0, dc) for dc in range(max(4, sw))]
    if kind == "line_v":
        return [(dr, 0) for dr in range(max(4, sh))]
    if kind == "blob":
        return [(dr, dc) for dr in range(sh) for dc in range(sw)
                if (dr + dc) % 2 == 0] or [(0, 0), (0, 1), (1, 0), (1, 1)]
    if kind == "hollow_ring":
        out = []
        for c in range(sw):
            out.append((0, c)); out.append((sh - 1, c))
        for r in range(sh):
            out.append((r, 0)); out.append((r, sw - 1))
        return list(set(out))
    if kind == "Z_shape":
        out = [(0, c) for c in range(sw)]
        out += [(sh - 1, c) for c in range(sw)]
        for k in range(1, sh - 1):
            out.append((k, k * (sw - 1) // max(1, sh - 1)))
        return out
    return [(dr, dc) for dr in range(sh) for dc in range(sw)]


def _small_cells(kind, rng):
    if kind == "single":
        return [(0, 0)]
    if kind == "pair_h":
        return [(0, 0), (0, 1)]
    if kind == "pair_v":
        return [(0, 0), (1, 0)]
    if kind == "pair_diag":
        return [(0, 0), (1, 1)]
    if kind == "triple_L":
        return [(0, 0), (1, 0), (1, 1)]
    if kind == "triple_line":
        return [(0, 0), (0, 1), (0, 2)]
    if kind == "triple_diag":
        return [(0, 0), (1, 1), (2, 2)]
    return [(0, 0)]


def _draw_from_degenerate(name, h, w, ctx, rng):
    color = rng.choice([1, 3, 4, 5, 6, 7, 9])
    g = full_grid(h, w, 0)
    if name == "only_small":
        for i, (r, c) in enumerate([(2, 2), (2, w - 3), (h - 3, 2), (h - 3, w - 3)]):
            g[r][c] = color
        return g
    if name == "only_large":
        for r in range(2, 5):
            for c in range(2, 6):
                g[r][c] = color
        return g
    if name == "touching_objects":
        # 4-conn merges into one big object.
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = color
        for r in range(2, 5):
            for c in range(5, 8):
                g[r][c] = color
        return g
    return g
