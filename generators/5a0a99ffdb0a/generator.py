"""Generator for arc_puzzle_bank_seventeenth21:H118 — match query shape to a prototype, recolor.

Canonical rule: split the grid into EXACTLY 4 panels (separated by single
columns). Panels 1-3 are PROTOTYPES (each a distinct binary shape in a
distinct color = its max non-zero value). Panel 4 is the QUERY: its binary
shape equals one prototype's shape under some D8 transform (rotation/flip).
The rule finds the matching prototype and repaints the QUERY panel in that
prototype's color.

The old generator built n=4-6 panels (the rule always splits into 4, so n!=4
mis-parses every panel) and drew all motifs independently at random with no
enforced match — it only avoided crashing because 1-3 cell motifs collide
under D8 by pigeonhole. Now: EXACTLY 4 panels; 3 prototypes that are pairwise
NON-D8-equivalent (so the match is unambiguous); the query is a random D8
transform of one randomly chosen prototype -> the matched prototype + the
transform + colors + shapes + panel size all vary.

Combinatorial axes: panel size (output dims), the 3 prototype shapes, the 3
colors, which prototype the query matches, the query's D8 transform, the
in-panel placement of each shape.
Degenerates: single_cell, duplicate_protos, max_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a0a99ffdb0a"
VERSION = "2.0.0"  # rule splits into EXACTLY 4 panels + needs query to D8-match one of 3 prototypes (recolor query to its colour). Old gen made n=4-6 panels (n!=4 mis-parses) and never enforced a match (only worked via tiny-motif D8 collisions). Now exactly 4 panels, 3 pairwise-non-D8-equiv prototypes, query = random D8 transform of one -> matched proto/transform/shapes/colours/size all vary.
TASK_ID = "5a0a99ffdb0a"
SUMMARY = (
    "0-bg grid, h = ps (3-5). FOUR square ps x ps PANELS separated by single "
    "full-height color-9 columns. Panels 1-3 are PROTOTYPES: three pairwise "
    "NON-D8-EQUIVALENT connected binary shapes, each in a distinct color. "
    "Panel 4 is the QUERY: a random D8 transform (one of 8 rotations/flips) of "
    "one randomly chosen prototype's shape, in a throwaway color. Each shape "
    "is placed at a random offset inside its panel. Rule (MATCH + RECOLOR): "
    "split into 4 panels; for each prototype take its max-nonzero color as its "
    "label and its 8 D8 orientations as variants; find the prototype whose "
    "variant set contains the query's normalized shape; repaint the QUERY "
    "panel in that prototype's label color. Output = ps x ps query shape in "
    "the matched prototype's color."
)

INVARIANTS = [
    "exactly 4 square panels separated by single color-9 columns",
    "the 3 prototype shapes are pairwise non-D8-equivalent",
    "the query is a D8 transform of exactly one prototype's shape",
    "each prototype has a distinct single color (its max non-zero value)",
]

HELPFUL_TEXTURES = ("small", "medium", "large")
DEGENERATE_TEXTURES = ("single_cell", "duplicate_protos", "max_panel")

AXES = {
    "panel_size":     {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "n_panels":       {"type": "int", "default": "4 (rule-fixed)", "valid": "4"},
    "proto_shapes":   {"type": "str", "default": "rng connected", "valid": "varies"},
    "match_index":    {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "query_transform":{"type": "int", "default": "rng 0..7", "valid": "0..7"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "in_panel_offset",
                       "valid": "in_panel_offset"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..4"},
    "texture":        {"type": "str", "default": "alias for panel_size",
                       "valid": "small|medium|large|single_cell|duplicate_protos|max_panel"},
}


def _norm(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return sorted((r - r0, c - c0) for (r, c) in cells)


def _d8(cells, kind):
    out = []
    for (r, c) in cells:
        if kind == 0:   out.append((r, c))      # identity
        elif kind == 1: out.append((c, -r))     # rotate 90
        elif kind == 2: out.append((-r, -c))    # rotate 180
        elif kind == 3: out.append((-c, r))     # rotate 270
        elif kind == 4: out.append((r, -c))     # flip horizontal
        elif kind == 5: out.append((-r, c))     # flip vertical
        elif kind == 6: out.append((c, r))      # transpose
        else:           out.append((-c, -r))    # anti-transpose
    return _norm(out)


def _variants(cells):
    return {tuple(_d8(cells, k)) for k in range(8)}


def _rand_shape(rng, ps):
    """Connected binary shape, 2..min(5, ps*ps-1) cells, bbox within ps x ps."""
    n = rng.randint(2, min(5, ps * ps - 1))
    cells = {(rng.randint(0, ps - 1), rng.randint(0, ps - 1))}
    guard = 0
    while len(cells) < n and guard < 200:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < ps and 0 <= nc < ps:
            cells.add((nr, nc))
    return _norm(cells)


def _build(ps, panel_cells, panel_colors, rng):
    h = ps
    w = 4 * ps + 3
    g = full_grid(h, w, 0)
    for i in (1, 2, 3):                       # single-column separators
        sep = i * (ps + 1) - 1
        for r in range(h):
            g[r][sep] = 9
    for pi in range(4):
        left = pi * (ps + 1)
        cells = panel_cells[pi]
        color = panel_colors[pi]
        bh = max(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) + 1
        off_r = rng.randint(0, ps - bh)
        off_c = rng.randint(0, ps - bw)
        for (r, c) in cells:
            g[off_r + r][left + off_c + c] = color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    tx = overrides.get("texture")
    if tx == "small":
        ps = 3
    elif tx == "large":
        ps = 5
    elif tx == "medium":
        ps = 4
    elif difficulty == "easy":
        ps = ctx.draw_int("panel_size", 3, 3)
    elif difficulty == "hard":
        ps = ctx.draw_int("panel_size", 4, 5)
    else:
        ps = ctx.draw_int("panel_size", 3, 4)

    # three pairwise non-D8-equivalent prototype shapes
    shapes = []
    varsets = []
    guard = 0
    while len(shapes) < 3 and guard < 600:
        guard += 1
        s = _rand_shape(rng, ps)
        if any(tuple(s) in vs for vs in varsets):
            continue
        shapes.append(s)
        varsets.append(_variants(s))
    for fb in ([(0, 0)], [(0, 0), (0, 1)], [(0, 0), (0, 1), (1, 0)],
               [(0, 0), (0, 1), (0, 2)]):   # ps fallback (always reaches 3)
        if len(shapes) >= 3:
            break
        nfb = _norm(fb)
        if not any(tuple(nfb) in vs for vs in varsets):
            shapes.append(nfb)
            varsets.append(_variants(nfb))

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 4)
    k = ctx.draw_int("match_index", 0, 2)
    kind = ctx.draw_int("query_transform", 0, 7)
    query = _d8(shapes[k], kind)
    panel_cells = [shapes[0], shapes[1], shapes[2], query]
    panel_colors = [colors[0], colors[1], colors[2], colors[3]]
    return _build(ps, panel_cells, panel_colors, rng)


def _panel_shape_and_color(panel):
    cells = []
    colors = set()
    for r, row in enumerate(panel):
        for c, v in enumerate(row):
            if v != 0:
                cells.append((r, c))
                colors.add(v)
    return _norm(cells) if cells else [], colors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the four-panel D8 prototype-matching task."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    ps = len(grid)
    width = len(grid[0])
    if width != 4 * ps + 3:
        errors.append(f"expected width 4*panel_size+3, got panel_size={ps}, width={width}")
        return errors
    if not (3 <= ps <= 5):
        errors.append(f"panel_size should be 3..5, got {ps}")
    sep_cols = [i * (ps + 1) - 1 for i in (1, 2, 3)]
    for c in sep_cols:
        if any(row[c] != 9 for row in grid):
            errors.append(f"separator column {c} must be full-height color 9")
    panels = []
    for pi in range(4):
        left = pi * (ps + 1)
        panel = [[grid[r][left + c] for c in range(ps)] for r in range(ps)]
        panels.append(panel)
        if any(v == 9 for row in panel for v in row):
            errors.append(f"panel {pi + 1} contains separator color 9 inside the panel")
    shapes = []
    colors = []
    for pi, panel in enumerate(panels):
        shape, panel_colors = _panel_shape_and_color(panel)
        if not shape:
            errors.append(f"panel {pi + 1} is empty")
        if len(panel_colors) != 1:
            errors.append(f"panel {pi + 1} must contain exactly one nonzero color, found {sorted(panel_colors)}")
        shapes.append(shape)
        colors.append(next(iter(panel_colors)) if panel_colors else None)
    if any(c is None for c in colors):
        return errors
    if len(set(colors[:3])) != 3:
        errors.append("prototype panels must use three distinct label colors")
    if colors[3] in set(colors[:3]):
        errors.append("query panel should use a throwaway color distinct from prototype labels")
    proto_variants = []
    for i, shape in enumerate(shapes[:3]):
        variants = _variants(shape)
        if any(tuple(shape) in prev for prev in proto_variants):
            errors.append(f"prototype {i + 1} is D8-equivalent to an earlier prototype")
        proto_variants.append(variants)
    query = tuple(shapes[3])
    matches = [i for i, variants in enumerate(proto_variants) if query in variants]
    if len(matches) != 1:
        errors.append(f"query must D8-match exactly one prototype, matched {len(matches)}")
    return errors


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    if name == "single_cell":
        s = [(0, 0)]
        return _build(3, [s, s, s, s], [1, 2, 3, 4], rng)
    if name == "duplicate_protos":
        a = [(0, 0), (0, 1), (1, 0)]
        b = [(0, 0), (1, 0), (1, 1)]
        return _build(3, [a, a, b, _d8(a, 2)], [1, 2, 3, 5], rng)
    if name == "max_panel":
        a = [(0, 0), (0, 1), (0, 2), (1, 0)]
        b = [(0, 0), (1, 0), (2, 0), (2, 1)]
        c = [(0, 1), (1, 0), (1, 1), (1, 2)]
        return _build(5, [a, b, c, _d8(b, 3)], [2, 3, 4, 6], rng)
    return _build(3, [[(0, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 0), (1, 1)],
                      [(0, 0), (0, 1)]], [1, 2, 3, 4], rng)
