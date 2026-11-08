"""Generator for 27a77e38.

Rule: find separator row (all 5s); mode color above; bottom-row middle
cell = that mode.

Combinatorial axes (8): grid_h/w, separator_row, top_density,
mode_dominance, palette_kind, palette_size, position_bias,
asymmetry_force.
Degenerates: no_separator, multiple_separators, all_zeros_above.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bb986b5228fb"
VERSION = "1.2.0"  # FIX identity_demo (2/18): the canonical rule computes the mode over ALL cells above the separator INCLUDING background 0, but the generator left 0s above (top_density<1) and computed its own mode EXCLUDING 0. When 0 was the rule's actual mode, it wrote 0 to the bottom-middle cell (already 0) -> output==input. Now fill the top region fully (no 0s above the separator) so the mode is a real color. + self_check.
TASK_ID = "bb986b5228fb"
SUMMARY = "Top region + 5-separator + empty bottom; rule emits mode at last-row middle."

INVARIANTS = [
    "exactly one full-width row of 5s",
    "above separator: rows filled with non-5 colors and a clear mode",
    "below separator: empty (all 0s)",
    "the mode color above is STRICTLY more common than any other above",
]

PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("no_separator", "multiple_separators", "all_zeros_above")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 5..10", "valid": "4..14"},
    "grid_w":            {"type": "int", "default": "rng 5..10", "valid": "3..14"},
    "separator_row":     {"type": "int", "default": "rng 2..h/2",
                          "valid": "1..h-2"},
    "top_density":       {"type": "float", "default": "rng 0.7..1",
                          "valid": "0.3..1"},
    "mode_dominance":    {"type": "float", "default": "rng 0.4..0.6",
                          "valid": "0.3..0.8"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "anchor_corner":     {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 6, 3, 6
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 9, 14, 9, 14
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 10, 5, 10
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 7, 8]
    elif palette_kind == "small":
        pool = [1, 2, 3]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 3, 6)))
    palette = pool[:max(2, n_palette)]
    sep = int(overrides.get("separator_row",
                            ctx.draw_int("separator_row", 2,
                                         max(2, h // 2))))
    sep = max(1, min(h - 2, sep))
    top_density = float(overrides.get("top_density",
                                      ctx.draw_rng("top_density")
                                      .uniform(0.7, 1.0)))
    mode_dom = float(overrides.get("mode_dominance",
                                   ctx.draw_rng("mode_dominance")
                                   .uniform(0.4, 0.6)))
    g = full_grid(h, w, 0)
    mode_color = palette[0]
    # Fill the top region COMPLETELY (no 0s above the separator): the rule
    # takes the mode over ALL cells above it, counting 0 too, so a 0 left here
    # could win the mode and make the output a no-op. (top_density retained as
    # an accepted axis but the main path keeps the region dense.)
    for r in range(sep):
        for c in range(w):
            if rng.random() < mode_dom:
                g[r][c] = mode_color
            else:
                g[r][c] = rng.choice(palette[1:]) if len(palette) > 1 else mode_color
    counts = {}
    for r in range(sep):
        for c in range(w):
            v = g[r][c]
            if v not in (0, 5):
                counts[v] = counts.get(v, 0) + 1
    sorted_c = sorted(counts.items(), key=lambda kv: -kv[1])
    if not sorted_c or sorted_c[0][0] != mode_color or \
            (len(sorted_c) > 1 and sorted_c[0][1] <= sorted_c[1][1]):
        # Force mode dominance: bump mode_color count
        cells_to_swap = [(r, c) for r in range(sep) for c in range(w)
                         if g[r][c] != mode_color and g[r][c] != 0]
        rng.shuffle(cells_to_swap)
        for r, c in cells_to_swap[:3]:
            g[r][c] = mode_color
    for c in range(w):
        g[sep][c] = 5
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """One full-width 5-separator; the mode over ALL cells above it (counting 0,
    as the rule does) is a non-zero color that differs from the current
    bottom-row middle cell, so the rule visibly changes the grid.
    Returns a list of violations (empty == pass)."""
    h, w = len(grid), len(grid[0])
    seps = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    msgs = []
    if len(seps) != 1:
        msgs.append(f"need exactly one 5-separator row, got {len(seps)}")
        return msgs
    sep = seps[0]
    if sep >= h - 1:
        msgs.append("separator is the last row (no bottom region)")
        return msgs
    vals = [grid[r][c] for r in range(sep) for c in range(w)]
    if not vals:
        msgs.append("no cells above the separator")
        return msgs
    # rule's mode: max count over unique values, ties -> first seen (pick-max)
    best = max(dict.fromkeys(vals), key=lambda v: vals.count(v))
    if best == 0:
        msgs.append("mode above separator is 0 (rule writes 0 -> identity)")
    mid = (w - 1) // 2
    if grid[h - 1][mid] == best:
        msgs.append("bottom-row middle already equals the mode -> identity")
    return msgs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_separator":
        for r in range(h // 2):
            for c in range(w):
                g[r][c] = rng.choice([1, 2, 3, 4])
        return g
    if name == "multiple_separators":
        for c in range(w):
            g[1][c] = 5
            g[h - 2][c] = 5
        return g
    if name == "all_zeros_above":
        for c in range(w):
            g[h // 2][c] = 5
        return g
    return g
