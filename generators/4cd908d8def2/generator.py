"""Generator for arc_additional_puzzles_21_set10_bundle:H69 — find transform-matching candidate.

Rule: full-height color-5 cols split the grid into N panels. Panel 0 is the
template; among panels[1:] the first one whose cropped binary shape matches
the template under any rotation/reflection is returned (whole panel grid).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers (no color-5 columns → rule cannot identify
panels); no_template (panel 0 empty → rule has nothing to match
against); no_match (no panel matches template's dihedral class →
rule's selector returns nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4cd908d8def2"
VERSION = "1.3.1"  # robustness: clamp N panels to <=30 cols (hard reached 39)
TASK_ID = "4cd908d8def2"

SUMMARY = "N panels split by full-height color-5 columns; panel 0 = template; rule outputs the FIRST other panel whose shape matches template under any of 8 dihedral transforms (rotation/reflection)."

# Rivals: 'output first non-template panel' refuted by ≥2 demos where
# match is later. 'output template' refuted by any demo (output is a
# matching panel). 'output last panel' refuted similarly. 'use 5
# color in output' refuted by any demo (output panel doesn't have
# 5s).
# 4 demos with varied templates + panel layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "N-1 full-height color-5 separator columns split the grid into N equal-width panels (N in 3..4)",
    "panel 0 holds a non-trivial template shape (3-5 cells)",
    "exactly one of panels[1:] matches the template under rotation/reflection",
    "non-matching panels have a different cell count or non-equivalent shape",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "no_template", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_w":           {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "panel_h":           {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "n_panels":          {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "position_bias":     {"type": "str", "default": "panels_with_template_match",
                          "valid": "panels_with_template_match"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_dividers|no_template|no_match"},
}


def _normalize(cells):
    cells = list(cells)
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _rot90(cells):
    norm = _normalize(cells)
    h = max(r for r, _ in norm) + 1
    return _normalize((c, h - 1 - r) for r, c in norm)


def _flip_lr(cells):
    norm = _normalize(cells)
    w = max(c for _, c in norm) + 1
    return _normalize((r, w - 1 - c) for r, c in norm)


def _all_transforms(cells):
    res = set()
    cur = _normalize(cells)
    for _ in range(4):
        res.add(cur)
        cur = _rot90(cur)
    cur = _flip_lr(cells)
    for _ in range(4):
        res.add(cur)
        cur = _rot90(cur)
    return res


_TEMPLATE_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (1, 0)],
]


def _random_connected(rng, k, ph, pw, max_tries=120):
    for _ in range(max_tries):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                cells.append((nr, nc)); seen.add((nr, nc))
        norm = _normalize(cells)
        h_n = max(r for r, _ in norm) + 1
        w_n = max(c for _, c in norm) + 1
        if h_n <= ph and w_n <= pw:
            return list(norm)
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        pw = ctx.draw_int("panel_w", 4, 5)
        ph = ctx.draw_int("panel_h", 4, 5)
        n_panels = ctx.draw_int("n_panels", 3, 3)
    elif difficulty == "hard":
        pw = ctx.draw_int("panel_w", 6, 7)
        ph = ctx.draw_int("panel_h", 6, 7)
        n_panels = ctx.draw_int("n_panels", 4, 5)
    else:
        pw = ctx.draw_int("panel_w", 5, 6)
        ph = ctx.draw_int("panel_h", 5, 6)
        n_panels = ctx.draw_int("n_panels", 3, 4)
    rng = ctx.draw_rng("layout")
    # Keep N panels + (N-1) separators within the 30-col ARC canvas (hard could
    # reach n=5 x pw=7 = 39). The rule needs >=2 panels (template + candidates).
    n_panels = min(n_panels, 31 // (pw + 1))
    h = ph
    w = pw * n_panels + (n_panels - 1)

    for outer in range(40):
        g = full_grid(h, w, 0)
        sep_cols = [pw + i * (pw + 1) for i in range(n_panels - 1)]
        for sc in sep_cols:
            for r in range(h):
                g[r][sc] = 5
        starts = [0] + [s + 1 for s in sep_cols]

        template = rng.choice(_TEMPLATE_SHAPES)
        template_norm = _normalize(template)
        template_ts = _all_transforms(template)
        match_cells = list(rng.sample(list(template_ts), 1)[0])

        match_idx = rng.randint(1, n_panels - 1)

        colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_panels)

        if max(r for r, _ in template_norm) >= ph or max(c for _, c in template_norm) >= pw:
            continue
        max_dr = ph - 1 - max(r for r, _ in template_norm)
        max_dc = pw - 1 - max(c for _, c in template_norm)
        dr0 = rng.randint(0, max_dr) if max_dr > 0 else 0
        dc0 = rng.randint(0, max_dc) if max_dc > 0 else 0
        for r, c in template_norm:
            g[dr0 + r][starts[0] + dc0 + c] = colors[0]

        match_h = max(r for r, _ in match_cells) + 1
        match_w = max(c for _, c in match_cells) + 1
        if match_h > ph or match_w > pw:
            continue
        mdr = rng.randint(0, ph - match_h) if ph - match_h > 0 else 0
        mdc = rng.randint(0, pw - match_w) if pw - match_w > 0 else 0
        for r, c in match_cells:
            g[mdr + r][starts[match_idx] + mdc + c] = colors[match_idx]

        ok = True
        tk = len(template_norm)
        for pi in range(1, n_panels):
            if pi == match_idx:
                continue
            other_k = tk + rng.choice([-1, 1, 2])
            if other_k < 2: other_k = tk + 1
            other_cells = _random_connected(rng, other_k, ph, pw)
            if other_cells is None:
                ok = False
                break
            o_h = max(r for r, _ in other_cells) + 1
            o_w = max(c for _, c in other_cells) + 1
            odr = rng.randint(0, ph - o_h) if ph - o_h > 0 else 0
            odc = rng.randint(0, pw - o_w) if pw - o_w > 0 else 0
            for r, c in other_cells:
                g[odr + r][starts[pi] + odc + c] = colors[pi]
        if ok:
            return g
    raise ValueError("could not realize template/match panel layout in 40 attempts")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify N-panel layout with color-5 separators invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    problems = []
    sep_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(sep_cols) < 2:
        problems.append(f"expected >=2 full-height color-5 separator columns, found {len(sep_cols)}")
    return problems


def _draw_from_degenerate(name, rng):
    pw, ph, n_panels = 5, 5, 3
    h = ph
    w = pw * n_panels + (n_panels - 1)
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        # No color-5 separator columns — rule cannot identify panels.
        for r, c in [(0, 0), (1, 0), (2, 0), (2, 1)]:
            g[r][c] = 4
        for r, c in [(0, 0), (1, 0), (2, 0), (2, 1)]:
            g[r][8 + c] = 6
        return g
    if name == "no_template":
        # Panel 0 empty — rule has nothing to match against.
        for r in range(h):
            g[r][pw] = 5
            g[r][2 * pw + 1] = 5
        for r, c in [(0, 0), (1, 0), (2, 0)]:
            g[r][pw + 1 + c] = 6
        return g
    if name == "no_match":
        # Panel 0 = L-tromino, all other panels are 2x2 squares.
        for r in range(h):
            g[r][pw] = 5
            g[r][2 * pw + 1] = 5
        for r, c in [(0, 0), (0, 1), (1, 0)]:
            g[r][c] = 4
        for r, c in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[r][pw + 1 + c] = 6
        for r, c in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[r][2 * pw + 2 + c] = 7
        return g
    return g
