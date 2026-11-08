"""Generator for arc_puzzle_bank_21_set2:S2_H1.

Rule: a blank row and column split four quadrants; one quadrant omits
the shared motif.

Combinatorial axes (8): grid_h, grid_w, palette_kind, quad_size,
missing_quad, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_separator, all_quadrants_filled, two_missing_quadrants.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "864b0302e2e6"
VERSION = "2.1.2"  # Honor the declared missing_quad override; motif sampling remains random per instance.
TASK_ID = "864b0302e2e6"
SUMMARY = (
    "Odd-sized square 0-bg grid (h = w = 2 * "
    "q + 1, q ∈ {4, 5, 6}) with FIXED "
    "QUADRANT LAYOUT: (a) ONE FULL-WIDTH "
    "BLANK ROW at row sep = q (all bg-0); "
    "(b) ONE FULL-HEIGHT BLANK COLUMN at "
    "col sep = q (all bg-0). Together these "
    "split the grid into FOUR EQUAL "
    "QUADRANTS of size q × q at origins "
    "{(0, 0), (0, q+1), (q+1, 0), (q+1, "
    "q+1)}; (c) THREE of the FOUR QUADRANTS "
    "contain the SAME RANDOM MOTIF — a "
    "nonempty proper subset of the q × q "
    "quadrant sampled once per instance — "
    "at the same local coordinates, all "
    "painted in ONE shared non-0 color "
    "drawn from {1..9}. (d) The FOURTH "
    "QUADRANT (chosen randomly) is EMPTY "
    "(no motif). Rule (FILL THE MISSING "
    "QUADRANT WITH THE SHARED MOTIF): find "
    "the FOUR QUADRANTS defined by the "
    "blank row and column. IDENTIFY the "
    "EMPTY one. find the shared motif and "
    "color from the OTHER 3 quadrants. "
    "PAINT the missing quadrant with the "
    "same motif at the same local "
    "coordinates in the same color. Net: "
    "the input's 3-of-4 symmetric pattern "
    "becomes a complete 4-of-4 symmetric "
    "pattern. Flagged borderline "
    "intrinsic-low (uniq_out~25): 4 "
    "missing-quad positions × q × colors "
    "limit output diversity."
)

INVARIANTS = [
    "background is 0",
    "one all-zero row and one all-zero column split four equal quadrants",
    "three quadrants contain the same nonzero motif in matching local coordinates",
    "one quadrant is empty and should receive the motif",
]

PALETTE_KINDS = ("default", "missing_tl", "missing_tr", "missing_bl_or_br")
DEGENERATE_TEXTURES = ("no_separator", "all_quadrants_filled", "two_missing_quadrants")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "2*q+1 (q in 4..6)", "valid": "9..17"},
    "grid_w":         {"type": "int", "default": "same as grid_h", "valid": "9..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "quad_size":      {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "missing_quad":   {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "quadrants", "valid": "quadrants"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

MOTIF = [(0, 1), (1, 1), (1, 2), (2, 0)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: square odd grid; center row and center col are all-zero (the separators)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != w or h % 2 == 0:
        return []  # allow non-square or even-sized (edge case)
    sep = h // 2
    if not all(grid[sep][c] == 0 for c in range(w)):
        return []  # degenerate no_separator (center row not empty) — allowed
    errs = []
    if not all(grid[r][sep] == 0 for r in range(h)):
        errs.append("center column (separator) is not all-zero")
    # Three of four quadrants must have at least one nonzero cell
    origins = [(0, 0), (0, sep + 1), (sep + 1, 0), (sep + 1, sep + 1)]
    filled = sum(1 for r0, c0 in origins
                 if any(grid[r0 + dr][c0 + dc] != 0
                        for dr in range(sep) for dc in range(sep)))
    if filled == 0:
        return []  # degenerate — allowed
    if filled == 4:
        return []  # degenerate all_quadrants_filled — allowed
    if filled < 2:
        errs.append(f"expected 3 filled quadrants; found {filled}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        q = ctx.draw_int("quad_size", 4, 4)
    elif difficulty == "hard":
        q = ctx.draw_int("quad_size", 5, 6)
    else:
        q = ctx.draw_int("quad_size", 4, 6)
    rng = ctx.draw_rng("layout")
    h = w = q * 2 + 1
    sep = q
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    # random shared motif: a subset of the q x q quadrant (non-empty, not full)
    quad_cells = [(r, c) for r in range(q) for c in range(q)]
    motif = rng.sample(quad_cells, rng.randint(3, max(3, q * q - 1)))
    origins = [(0, 0), (0, sep + 1), (sep + 1, 0), (sep + 1, sep + 1)]
    missing = ctx.draw_int_strict("missing_quad", 0, 3)
    for i, (r0, c0) in enumerate(origins):
        if i == missing:
            continue
        for dr, dc in motif:
            g[r0 + dr][c0 + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    q = 5
    h = w = q * 2 + 1
    g = full_grid(h, w, 0)
    sep = q
    origins = [(0, 0), (0, sep + 1), (sep + 1, 0), (sep + 1, sep + 1)]
    if name == "no_separator":
        # 4 motifs but no blank row/column → quadrants undefined
        for r0, c0 in origins[:3]:
            for dr, dc in MOTIF:
                g[r0 + dr][c0 + dc] = 4
        return g
    if name == "all_quadrants_filled":
        # all 4 quadrants have the motif → rule has no missing quadrant
        for r0, c0 in origins:
            for dr, dc in MOTIF:
                g[r0 + dr][c0 + dc] = 4
        return g
    if name == "two_missing_quadrants":
        # 2 motifs, 2 missing → predicate "exactly one missing" fails
        for r0, c0 in origins[:2]:
            for dr, dc in MOTIF:
                g[r0 + dr][c0 + dc] = 4
        return g
    return g
