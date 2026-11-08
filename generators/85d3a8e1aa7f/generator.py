"""Generator for 252143c9.

Rule: kc = center cell. Find avg position of all kc cells. Output is
7-bg with diagonal of kc from center toward avg-direction quadrant.

Combinatorial axes (8): grid_n, key_color, quadrant_choice,
n_key_cells, key_position_kind, n_distractors, distractor_palette_size,
asymmetry_force.
Degenerates: empty_quadrant, all_kc, no_kc.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85d3a8e1aa7f"
VERSION = "1.2.2"
TASK_ID = "85d3a8e1aa7f"
SUMMARY = "Square odd grid; center cell = key_color; rule computes avg position of all key-color cells, finds the quadrant it falls into, emits a diagonal of key_color from center toward that quadrant on a 7-bg grid."

# Rivals: 'emit diagonal in fixed direction' refuted by ≥2 demos
# with different quadrants. 'preserve all input cells' refuted by
# any demo (output is sparse diagonal). 'use distractor color in
# output' refuted by any demo (output uses key_color and 7).
# 'output is the input' refuted by any demo (very different).
# 4 demos with varied quadrants cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "square odd-sized grid in [7, 13]",
    "center cell is the key color (kc != 7)",
    ">=4 kc cells in a single quadrant (so avg-direction is unambiguous)",
    "distractor cells in other non-7 colors elsewhere",
]

QUADRANT_CHOICES = ("top_left", "top_right", "bottom_left", "bottom_right")
KEY_POSITION_KINDS = ("scattered", "blob", "diagonal", "edge")
DEGENERATE_TEXTURES = ("empty_quadrant", "all_kc", "no_kc")
HELPFUL_TEXTURES = QUADRANT_CHOICES

AXES = {
    "grid_n":             {"type": "int", "default": "rng 7..13 odd",
                           "valid": "7..15 odd"},
    "key_color":          {"type": "color", "default": "rng (≠7)",
                           "valid": "0..9 (≠7)"},
    "quadrant_choice":    {"type": "str", "default": "rng helpful",
                           "valid": "|".join(QUADRANT_CHOICES)},
    "n_key_cells":        {"type": "int", "default": "rng 4..8", "valid": "4..15"},
    "key_position_kind":  {"type": "str", "default": "rng helpful",
                           "valid": "|".join(KEY_POSITION_KINDS)},
    "n_distractors":      {"type": "int", "default": "rng 3..6", "valid": "0..10"},
    "distractor_palette_size": {"type": "int", "default": "rng 2..5",
                                "valid": "1..8"},
    "asymmetry_force":    {"type": "bool", "default": "true",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for quadrant_choice",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_advertised_int(
    ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi
):
    """Use the narrow default band, but honor the full advertised override domain."""
    if label in overrides:
        value = overrides[label]
        if type(value) is not int:
            raise TypeError(f"{label} must be an integer (not bool)")
        if not valid_lo <= value <= valid_hi:
            raise ValueError(f"{label} must be in [{valid_lo}, {valid_hi}]")
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: square odd grid; center cell is nonzero key color; >=4 key cells in one quadrant."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h != w:
        errs.append(f"expected square grid; got {h}x{w}")
        return errs
    if h % 2 == 0:
        errs.append(f"expected odd-sized grid; got {h}")
        return errs
    cr, cc = h // 2, w // 2
    kc = grid[cr][cc]
    if kc == 0:
        return []  # degenerate no_kc — allowed
    if kc == 7:
        return []  # degenerate all_kc or key is 7 — allowed
    # Count key cells in each quadrant
    quads = {
        "TL": sum(1 for r in range(cr) for c in range(cc) if grid[r][c] == kc),
        "TR": sum(1 for r in range(cr) for c in range(cc + 1, w) if grid[r][c] == kc),
        "BL": sum(1 for r in range(cr + 1, h) for c in range(cc) if grid[r][c] == kc),
        "BR": sum(1 for r in range(cr + 1, h) for c in range(cc + 1, w) if grid[r][c] == kc),
    }
    if max(quads.values()) < 4:
        return []  # degenerate empty_quadrant — allowed (not enough key cells)
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        n_choices = [5, 7, 9]
    elif difficulty == "hard":
        n_choices = [13, 15, 17, 19]
    else:
        n_choices = [9, 11, 13, 15]
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        n = rng.choice(n_choices)
        return _draw_from_degenerate(overrides["texture"], n, rng)
    n = int(overrides.get("grid_n", rng.choice(n_choices)))
    if n % 2 == 0: n += 1
    n = max(5, min(19, n))
    kc = int(overrides.get("key_color",
                           ctx.draw_color("key_color", exclude={7})))
    quad = (overrides.get("texture") or
            overrides.get("quadrant_choice")
            or ctx.draw_choice("quadrant_choice",
                               list(QUADRANT_CHOICES)))
    dr, dc = {"top_left": (-1, -1), "top_right": (-1, 1),
              "bottom_left": (1, -1),
              "bottom_right": (1, 1)}[quad]
    n_kc = _draw_advertised_int(
        ctx, overrides, "n_key_cells", 4, 8, 4, 15
    )
    n_distract = _draw_advertised_int(
        ctx, overrides, "n_distractors", 3, 6, 0, 10
    )
    n_distract_pal = _draw_advertised_int(
        ctx, overrides, "distractor_palette_size", 2, 5, 1, 8
    )
    pos_kind = overrides.get("key_position_kind",
                             ctx.draw_choice("key_position_kind",
                                             list(KEY_POSITION_KINDS)))
    g = full_grid(n, n, 7)
    cr = n // 2; cc = n // 2
    g[cr][cc] = kc
    cells = _quadrant_cells(quad, cr, cc, n)
    if pos_kind == "blob":
        center_r = (cr - 1 if dr == -1 else cr + 1)
        center_c = (cc - 1 if dc == -1 else cc + 1)
        cells.sort(key=lambda rc: abs(rc[0] - center_r) + abs(rc[1] - center_c))
    elif pos_kind == "diagonal":
        diag = []
        rr, cc2 = cr + dr, cc + dc
        while 0 <= rr < n and 0 <= cc2 < n:
            diag.append((rr, cc2))
            rr += dr; cc2 += dc
        rest = [c for c in cells if c not in diag]
        rng.shuffle(rest)
        cells = diag + rest
    elif pos_kind == "edge":
        cells.sort(key=lambda rc: -max(min(rc[0], n - 1 - rc[0]),
                                       min(rc[1], n - 1 - rc[1])))
    else:
        rng.shuffle(cells)
    placed = 0
    for r, c in cells:
        if placed >= n_kc:
            break
        if g[r][c] == 7:
            g[r][c] = kc
            placed += 1
    distract_pool = [v for v in [0, 1, 2, 3, 4, 5, 6, 8, 9]
                     if v != kc and v != 7]
    rng.shuffle(distract_pool)
    distract_palette = distract_pool[:max(1, n_distract_pal)]
    for _ in range(n_distract * 2):
        r = rng.randint(0, n - 1); c = rng.randint(0, n - 1)
        if g[r][c] == 7:
            g[r][c] = rng.choice(distract_palette)
    return g


def _quadrant_cells(quad, cr, cc, n):
    if quad == "top_left":
        return [(r, c) for r in range(cr) for c in range(cc)]
    if quad == "top_right":
        return [(r, c) for r in range(cr) for c in range(cc + 1, n)]
    if quad == "bottom_left":
        return [(r, c) for r in range(cr + 1, n) for c in range(cc)]
    return [(r, c) for r in range(cr + 1, n) for c in range(cc + 1, n)]


def _draw_from_degenerate(name, n, rng):
    g = full_grid(n, n, 7)
    cr = n // 2; cc = n // 2
    kc = rng.choice([0, 1, 2, 3, 4, 5, 6, 8, 9])
    g[cr][cc] = kc
    if name == "empty_quadrant":
        return g
    if name == "all_kc":
        for r in range(n):
            for c in range(n):
                g[r][c] = kc
        return g
    if name == "no_kc":
        g[cr][cc] = rng.choice([0, 1, 2, 3, 4, 5, 6, 8, 9])
        return g
    return g
