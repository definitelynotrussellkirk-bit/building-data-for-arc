"""Generator for arc_puzzle_bank_fifth21:H32 — stamp the 9-anchored template at each marker.

Rule (verified from canonical Racket): the SOURCE is the color-9 cell whose non-zero
4-connected component has >1 cell; that component is the TEMPLATE (cell offsets relative
to the 9). Every OTHER non-zero cell is a MARKER. The template shape is stamped at each
marker, painted in that marker's color. Output = the union of stamped templates.

The previous body built a "6 panels separated by 9-columns" layout (a different task)
whose 9-columns became one huge template — off-distribution. This rewrite CONSTRUCTS the
canonical shape: one 9-anchored multi-cell template blob plus several isolated single
marker cells in distinct non-{0,9} colors.

Axes: grid size, template shape/size, marker count/colors/positions.
Degenerates: no_template (no multi-cell 9-component), no_markers, single_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cc0f491ea771"
VERSION = "2.0.1"  # WRONG-TASK: gen built '6 panels / 9-columns' but the rule stamps a 9-anchored template blob at each scattered marker in the marker's colour. Now construct the canonical: one 9-anchored multi-cell template + isolated single markers (distinct non-{0,9} colours); output = template stamped at each marker.
TASK_ID = "cc0f491ea771"

SUMMARY = ("A multi-cell template blob anchored by a color-9 cell, plus several isolated "
           "single marker cells in distinct colors. The rule stamps the template shape at "
           "each marker, recolored to the marker's color.")

INVARIANTS = [
    "background is 0",
    "exactly one color-9 cell, part of a multi-cell connected template component",
    "several isolated single marker cells in distinct non-{0,9} colors",
    "markers are separated from the template and each other (each its own size-1 component)",
]

DEGENERATE_TEXTURES = ("no_template", "no_markers", "single_marker")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "grid_w":     {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "tmpl_size":  {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "n_markers":  {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|no_template|no_markers|single_marker"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at most one color-9 cell; all values 0-9."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(nines) > 1:
        errs.append(f"expected at most 1 color-9 cell; found {len(nines)}")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, cells):
    """True iff all cells (and their 1-ring) are bg and in-bounds."""
    h, w = len(g), len(g[0])
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one 9-anchored template plus isolated marker cells."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 1:
        errs.append(f"expected exactly one color-9 anchor, found {len(anchors)}")
        return errs
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in seen:
                stack = [(r, c)]
                seen.add((r, c))
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                comps.append(comp)
    anchor = anchors[0]
    source = next((comp for comp in comps if anchor in comp), [])
    if len(source) <= 1:
        errs.append("anchor is not part of a multi-cell template")
    source_set = set(source)
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0 and (r, c) not in source_set]
    min_markers = 2 if difficulty != "hard" else 3
    if len(markers) < min_markers:
        errs.append(f"only {len(markers)} markers; expected at least {min_markers}")
    for r, c in markers:
        if grid[r][c] == 9:
            errs.append("marker cannot be color 9")
        if any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0
               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            errs.append("marker cells must be isolated from all nonzero cells")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 9, 11)
        tsz = ctx.draw_int("tmpl_size", 2, 4); nm = ctx.draw_int("n_markers", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        tsz = ctx.draw_int("tmpl_size", 4, 6); nm = ctx.draw_int("n_markers", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 9, 13)
        tsz = ctx.draw_int("tmpl_size", 3, 5); nm = ctx.draw_int("n_markers", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # template: a connected blob; one cell is the color-9 anchor, the rest a 2nd color
    tmpl = _poly(rng, tsz)
    th = max(r for r, _ in tmpl) + 1; tw = max(c for _, c in tmpl) + 1
    body_color = rng.choice([1, 2, 3, 4, 5, 6, 7])
    placed = False
    for _ in range(200):
        r0 = rng.randint(0, h - th); c0 = rng.randint(0, w - tw)
        abs_cells = [(r0 + dr, c0 + dc) for dr, dc in tmpl]
        if _free(g, abs_cells):
            for (r, c) in abs_cells:
                g[r][c] = body_color
            anchor = rng.choice(abs_cells)          # one template cell becomes the 9
            g[anchor[0]][anchor[1]] = 9
            placed = True
            break
    if not placed:
        return g
    # rels of the template relative to its 9 anchor (what the rule stamps)
    rels = [(r - anchor[0], c - anchor[1]) for (r, c) in abs_cells]
    rmin = min(dr for dr, _ in rels); rmax = max(dr for dr, _ in rels)
    cmin = min(dc for _, dc in rels); cmax = max(dc for _, dc in rels)
    # markers: isolated single cells in distinct non-{0,9} colors, positioned so the
    # stamped template mostly fits in-bounds (rule clips OOB but in-bounds reads cleaner)
    marker_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], min(nm, 8))
    for col in marker_colors:
        for _ in range(150):
            mr = rng.randint(max(0, -rmin), min(h - 1, h - 1 - rmax))
            mc = rng.randint(max(0, -cmin), min(w - 1, w - 1 - cmax))
            if _free(g, [(mr, mc)]):
                g[mr][mc] = col
                break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 10, 0)
    # template: 9 at (1,2) + a small body
    g[1][2] = 9; g[2][1] = 6; g[2][2] = 6; g[3][2] = 6
    if name == "no_template":
        # the 9 is isolated -> no multi-cell 9-component -> rule returns input
        g2 = full_grid(9, 10, 0)
        g2[1][2] = 9; g2[5][5] = 2; g2[7][3] = 3
        return g2
    if name == "no_markers":
        return g                                    # template only, nothing to stamp
    # single_marker
    g[6][6] = 2
    return g
