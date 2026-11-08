"""Generator for 8b:m55 — recolor template stamp.

Rule: a color-1 multi-cell template + single-cell markers in other
colors. Output stamps the template (recolored to each marker's color)
at each marker's position.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template (no color-1 multi-cell shape → rule's
template selector returns nothing), no_markers (template present
but no single-cell markers → rule has no positions to stamp at),
template_at_marker (a marker lands inside the template's bbox →
rule's stamp overlaps template, output ambiguous).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "94eda9b4c2fe"
VERSION = "2.0.1"  # add self_check
TASK_ID = "94eda9b4c2fe"

SUMMARY = (
    "0-bg grid (h~11-14, w~12-14) "
    "with: (a) ONE COLOR-1 (blue) "
    "TEMPLATE — a 3-5 cell shape "
    "(L-tromino/2x2 square/T-"
    "tetromino) placed at some "
    "interior position; (b) 2-3 "
    "ISOLATED SINGLE-CELL "
    "MARKERS in DISTINCT non-"
    "{0, 1} colors at scattered "
    "positions with enough room "
    "for template stamping. Rule "
    "(STAMP TEMPLATE AT EACH "
    "MARKER, RECOLORED TO "
    "MARKER): identify the "
    "COLOR-1 template and its "
    "anchor (top-left of bbox). "
    "For EACH MARKER cell at "
    "(mr, mc) with color C, "
    "STAMP the template shape "
    "at (mr, mc) (as the anchor "
    "or offset position) in "
    "COLOR C. Net: each marker "
    "becomes a copy of the "
    "template recolored to "
    "that marker's color."
)

INVARIANTS = [
    "background is 0",
    "exactly one connected color-1 template (3-5 cells)",
    "2-3 isolated single-cell markers in distinct non-{0,1} colors",
    "each marker has space to stamp the template in-bounds without overlapping other markers/template",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_markers", "template_at_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "grid_w":            {"type": "int", "default": "rng 12..14", "valid": "11..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "template_plus_markers",
                          "valid": "template_plus_markers"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥3 color-1 template cells; ≥2 non-{0,1} marker cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    n1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    n_markers = sum(1 for r in range(h) for c in range(w) if grid[r][c] not in (0, 1))
    if n1 < 3:
        errs.append(f"expected ≥3 color-1 template cells; got {n1}")
    if n_markers < 2:
        errs.append(f"expected ≥2 marker cells (non-{{0,1}}); got {n_markers}")
    return errs


_TEMPLATES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
        n_lo, n_hi = 2, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 13, 14)
        n_lo, n_hi = 3, 3
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 14)
        n_lo, n_hi = 2, 3
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    template = rng.choice(_TEMPLATES)
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    placed_template = False
    for _ in range(40):
        r0 = rng.randint(0, h - th); c0 = rng.randint(0, w - tw)
        if not _free(g, r0, c0, r0 + th - 1, c0 + tw - 1): continue
        for dr, dc in template:
            g[r0 + dr][c0 + dc] = 1
        placed_template = True; break
    if not placed_template:
        raise ValueError("could not place template")
    n_marks = rng.randint(n_lo, n_hi)
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n_marks)
    placed = 0; attempts = 0
    while placed < n_marks and attempts < 80:
        attempts += 1
        r = rng.randint(0, h - th); c = rng.randint(0, w - tw)
        if not _free(g, r, c, r + th - 1, c + tw - 1): continue
        g[r][c] = palette[placed]
        placed += 1
    if placed < n_marks:
        raise ValueError(f"could only place {placed}/{n_marks} markers")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "no_template":
        # No color-1 — rule's template selector returns nothing.
        g[3][3] = 4
        g[7][8] = 6
        return g
    if name == "no_markers":
        # Template present but no markers — rule has no positions
        # to stamp at; output equals input.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 1
        return g
    if name == "template_at_marker":
        # Marker lands inside template's bbox — stamp overlaps template;
        # output ambiguous.
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1)]:
            g[3 + dr][3 + dc] = 1
        g[3][4] = 6   # marker inside template
        return g
    return g
