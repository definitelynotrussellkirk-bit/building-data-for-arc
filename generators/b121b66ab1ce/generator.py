"""Generator for next_b:m11 — keep shape matching template.

Rule: a color-1 template shape; among color-3 shapes, keep those
whose normalized binary mask exactly matches the template; recolor
those to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_match, all_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b121b66ab1ce"
VERSION = "2.0.1"  # out_shapes 9: grid 9..11 x 10..12. Output=same dims; widen toward valid (8..14 x 9..14).
TASK_ID = "b121b66ab1ce"

SUMMARY = (
    "0-bg grid (h ∈ 9-13, w ∈ 10-14) "
    "with: (a) ONE COLOR-1 (BLUE) "
    "TEMPLATE SHAPE drawn from "
    "base_shapes bank (4 variants of "
    "3-4 cell shapes: S, Z, T, L) "
    "placed at a random non-"
    "overlapping interior position via "
    "_free check; (b) ONE MATCHING "
    "COLOR-3 (GREEN) SHAPE — same "
    "variant as the template — placed "
    "at another random position; "
    "(c) WITH 70% PROBABILITY ONE "
    "ADDITIONAL DIFFERENT COLOR-3 "
    "SHAPE — a different variant "
    "from base_shapes (acts as a "
    "distractor). Rule (FIND THE "
    "UNIQUE COLOR-1 TEMPLATE; "
    "AMONG COLOR-3 SHAPES, KEEP "
    "ONLY THOSE WHOSE NORMALIZED "
    "BINARY MASK EXACTLY MATCHES "
    "THE TEMPLATE; RECOLOR KEPT "
    "ONES TO COLOR 8): EXTRACT the "
    "COLOR-1 component → normalize "
    "its cells (subtract min r/c). "
    "EXTRACT every color-3 "
    "component. For EACH: "
    "normalize its cells; CHECK if "
    "EQUAL to template's "
    "normalized cells. IF YES: "
    "RECOLOR every cell of that "
    "component to COLOR 8 (cyan). "
    "ELSE: ERASE it to 0. The "
    "color-1 template stays. Net: "
    "the matching green copy "
    "becomes cyan; non-matching "
    "green distractors vanish."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-1 template shape",
    "1-2 color-3 shapes; exactly one's normalized cells match the template's",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_match", "all_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "template_with_candidates",
                       "valid": "template_with_candidates"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place_or_raise(g, rng, shape, color, label):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(60):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return
    raise ValueError(f"could not place {label}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 9, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    base_shapes = [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 0), (1, 0), (1, 1)],
    ]
    template = rng.choice(base_shapes)
    other = rng.choice([s for s in base_shapes if s != template])
    _place_or_raise(g, rng, template, 1, "template (color 1)")
    _place_or_raise(g, rng, template, 3, "matching color-3 shape")
    if rng.random() < 0.7:
        _place_or_raise(g, rng, other, 3, "different color-3 shape")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_template":
        # Color-3 shapes but no color-1 template — rule's match
        # criterion has no reference; keep branch never fires.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 3
        for r, c in [(7, 7), (8, 7), (8, 8)]: g[r][c] = 3
        return g
    if name == "no_match":
        # Template + only non-matching color-3 shapes — rule's
        # keep branch finds no matches; output erases everything.
        for r, c in [(1, 1), (1, 2), (2, 2), (2, 3)]: g[r][c] = 1
        for r, c in [(6, 6), (7, 6), (7, 7)]: g[r][c] = 3
        return g
    if name == "all_match":
        # Template + only matching color-3 shapes — rule's keep
        # branch keeps all; rule's discrimination invisible.
        for r, c in [(1, 1), (1, 2), (2, 2), (2, 3)]: g[r][c] = 1
        for r, c in [(5, 5), (5, 6), (6, 6), (6, 7)]: g[r][c] = 3
        for r, c in [(7, 1), (7, 2), (8, 2), (8, 3)]: g[r][c] = 3
        return g
    return g


def _selfcheck_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop(); comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    return comps


def _selfcheck_norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    blue = _selfcheck_components(grid, 1)
    green = _selfcheck_components(grid, 3)
    if len(blue) != 1:
        errors.append(f"expected exactly one color-1 template component, found {len(blue)}")
        return errors
    if not (1 <= len(green) <= 2):
        errors.append(f"expected 1..2 color-3 candidate components, found {len(green)}")
    tmpl = _selfcheck_norm(blue[0])
    matches = [comp for comp in green if _selfcheck_norm(comp) == tmpl]
    if len(matches) != 1:
        errors.append(f"expected exactly one green component matching the template, found {len(matches)}")
    return errors

