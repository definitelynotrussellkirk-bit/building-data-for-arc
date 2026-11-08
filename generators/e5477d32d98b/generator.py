"""Generator for arc_puzzle_bank_eighteenth21:H122 — before:after :: query:output analogy.

Rule (verified against canonical): split the grid column-wise into 3 panels
(separated by single divider columns). Read the single object in each panel:
BEFORE (panel0), AFTER (panel1), QUERY (panel2). Compute the DELTA = the cells
AFTER has that BEFORE lacks (both normalized to their top-left). The output is
the QUERY panel with that same DELTA painted (in the query's color) at the
query object's top-left. So before:after :: query:output — the growth from
before→after is applied to query.

This generator builds a base shape, a delta (extra connected cells), and:
panel0 = base (color A), panel1 = base+delta (color A), panel2 = base (color B,
same shape as before). The rule then derives output = base+delta in color B.

Combinatorial axes: panel_w, panel_h, base_shape, delta, color_a, color_b.
Degenerates: no_dividers, empty_panels, identity_delta.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e5477d32d98b"
VERSION = "2.0.0"  # WRONG-TASK rewrite. Docstring claimed '6 panels separated by 9-cols, find pair' but the rule splits into exactly 3 panels (single dividers) as a before:after::query:output analogy: delta = after-before, output = query+delta. Old gen made 4-7 panels with color-9 width-4 dividers and independent random motifs -> no analogy structure, rule produced incoherent (but non-erroring) output. Now builds the real 3-panel analogy with divider color 5 (matches canonical).
TASK_ID = "e5477d32d98b"

SUMMARY = (
    "0-bg grid of 3 PANELS (each panel_w wide, panel_h tall) separated by single "
    "DIVIDER COLUMNS (color 5). panel0=BEFORE (a base shape in color A), "
    "panel1=AFTER (base + a connected DELTA of extra cells, color A), panel2="
    "QUERY (the SAME base shape in color B). Rule: read the object in each panel; "
    "DELTA = cells AFTER has that BEFORE lacks (both normalized); output = the "
    "QUERY panel with DELTA painted in color B at the query's top-left. Net: "
    "before→after growth applied to query (before:after :: query:output)."
)

INVARIANTS = [
    "background is 0; single divider columns are color 5",
    "each panel holds exactly one 4-connected object",
    "after = before + a connected delta (after still one component, same top-left)",
    "query has the same shape as before (in a different color) so output = query+delta",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "identity_delta")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_w":        {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "panel_h":        {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "three_panel_analogy",
                       "valid": "three_panel_analogy"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_DELTAS4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _connected(cells):
    if not cells:
        return False
    start = next(iter(cells))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in _DELTAS4:
            n = (r + dr, c + dc)
            if n in cells and n not in seen:
                seen.add(n)
                stack.append(n)
    return len(seen) == len(cells)


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return {(r - mr, c - mc) for r, c in cells}


def _grow(rng, k, maxh, maxw):
    """Connected polyomino of k cells fitting maxh×maxw, normalized."""
    for _ in range(80):
        cells = {(0, 0)}
        tries = 0
        while len(cells) < k and tries < 300:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice(_DELTAS4)
            cells.add((r + dr, c + dc))
            tries += 1
        norm = _norm(cells)
        hh = max(r for r, _ in norm) + 1
        ww = max(c for _, c in norm) + 1
        if len(norm) == k and hh <= maxh and ww <= maxw:
            return norm
    return {(0, 0), (0, 1), (1, 1)}


def _split(rng, after):
    """Pick a delta subset (1-3) so base=after-delta is connected, nonempty,
    and keeps the same top-left as after (so the rule's normalize aligns)."""
    movable = [c for c in after if c != (0, 0)]
    for _ in range(80):
        kd = rng.randint(1, min(3, max(1, len(after) - 1)))
        if kd > len(movable):
            continue
        delta = set(rng.sample(movable, kd))
        base = after - delta
        if (0, 0) in base and base and _connected(base):
            nb = _norm(base)
            # base must keep origin (0,0) so its normalized form is a subset of after
            if (0, 0) in base and min(r for r, _ in base) == 0 and min(c for _, c in base) == 0:
                return base, delta
    return None


def _paste(g, cells, top, left, color):
    for r, c in cells:
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        pw = ctx.draw_int("panel_w", 4, 4)
        ph = ctx.draw_int("panel_h", 4, 4)
    elif difficulty == "hard":
        pw = ctx.draw_int("panel_w", 5, 7)
        ph = ctx.draw_int("panel_h", 5, 7)
    else:
        pw = ctx.draw_int("panel_w", 4, 6)
        ph = ctx.draw_int("panel_h", 4, 6)
    rng = ctx.draw_rng("layout")

    for _ in range(60):
        k = rng.randint(3, min(6, pw * ph - 1))
        after = _grow(rng, k, ph, pw)
        split = _split(rng, after)
        if split is None:
            continue
        base, delta = split
        # delta in after's frame; for output, applied at query bbox origin.
        # Ensure delta cells fit within a query panel when query placed at (0,0).
        bh = max(r for r, _ in base) + 1
        bw = max(c for _, c in base) + 1
        dmax_r = max([r for r, _ in delta] + [bh - 1])
        dmax_c = max([c for _, c in delta] + [bw - 1])
        if dmax_r >= ph or dmax_c >= pw:
            continue
        color_a, color_b = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)

        w = 3 * pw + 2
        g = full_grid(ph, w, 0)
        for r in range(ph):                      # single divider columns, color 5
            g[r][pw] = 5
            g[r][2 * pw + 1] = 5
        panel_left = [0, pw + 1, 2 * pw + 2]

        # BEFORE = base (color A), AFTER = base+delta (color A), QUERY = base (color B).
        # Place each at a random in-panel offset (rule normalizes, so offset is free).
        def place(shape, panel_idx, color):
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            top = rng.randint(0, ph - sh)
            left = rng.randint(0, pw - sw)
            _paste(g, shape, top, panel_left[panel_idx] + left, color)

        place(base, 0, color_a)
        place(base | delta, 1, color_a)
        # query at top-left so query+delta stays in-bounds for the rule
        _paste(g, base, 0, panel_left[2], color_b)
        return g
    # fallback: minimal valid instance
    g = full_grid(4, 14, 0)
    for r in range(4):
        g[r][4] = 5
        g[r][9] = 5
    for (r, c) in [(0, 0), (0, 1), (1, 1)]:
        g[r][c] = 2
    for (r, c) in [(0, 0), (0, 1), (1, 1), (0, 2)]:
        g[r][10 + c] = 2
    for (r, c) in [(0, 0), (0, 1), (1, 1)]:
        g[r][10 + c] = 6
    g[0][5] = g[0][6] = g[1][6] = 2
    g[0][7] = 2
    return g


def _draw_from_degenerate(name, rng):
    pw, ph = 4, 4
    w = 3 * pw + 2
    g = full_grid(ph, w, 0)
    base = [(0, 0), (0, 1), (1, 1)]
    if name == "no_dividers":
        # no divider columns; the rule slices by fixed position anyway, but the
        # before/after/query separation is undefined.
        _paste(g, base, 0, 0, 2)
        _paste(g, base + [(0, 2)], 0, 5, 2)
        _paste(g, base, 0, 10, 6)
        return g
    for r in range(ph):
        g[r][pw] = 5
        g[r][2 * pw + 1] = 5
    if name == "empty_panels":
        return g
    if name == "identity_delta":
        # before == after (empty delta) -> output == query unchanged.
        _paste(g, base, 0, 0, 2)
        _paste(g, base, 0, 5, 2)
        _paste(g, base, 0, 10, 6)
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(divs) != 2:
        return [f"expected two full-height divider columns, got {divs}"]
    d1, d2 = divs
    if d2 - d1 != d1 + 1:
        errs.append("three panels are not equal width")
    panels = [(0, d1 - 1), (d1 + 1, d2 - 1), (d2 + 1, w - 1)]
    shapes = []; colors = []
    for left, right in panels:
        cells = [(r, c - left) for r in range(h) for c in range(left, right + 1) if grid[r][c] not in (0, 5)]
        vals = {grid[r][c] for r in range(h) for c in range(left, right + 1) if grid[r][c] not in (0, 5)}
        if not cells:
            errs.append("empty analogy panel")
            shapes.append(set()); colors.append(None); continue
        if len(vals) != 1:
            errs.append("analogy panel contains multiple object colors")
        r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
        shapes.append({(r - r0, c - c0) for r, c in cells})
        colors.append(next(iter(vals)) if vals else None)
    if shapes[0] and shapes[1] and not shapes[0] < shapes[1]:
        errs.append("after panel should be a strict growth of before panel")
    if shapes[0] != shapes[2]:
        errs.append("query panel should match before-panel shape")
    if colors[0] == colors[2]:
        errs.append("query color should differ from before/after color")
    return errs
