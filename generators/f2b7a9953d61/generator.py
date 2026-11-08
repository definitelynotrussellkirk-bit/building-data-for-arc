"""Generator for arc_additional_puzzle_bank_volume6:H39.

Rule: the bottom row holds transform CODES (values 1-4, read left-to-right):
1=rotate-90, 2=rotate-180, 3=flip-horizontal, 4=flip-vertical. Compose them in
order onto the color-2 (blue) template (the topmost color-2 object), then stamp the
result at the color-9 (maroon) anchor, repainted COLOR 3 (green), on a blank grid.
The original template, codes, and anchor are absent from the output.

Prior generator: fixed L-template at (1,1), fixed anchor at (h//2,w-5), and op
codes drawn only from {1,3,4} -- so code 2 (rotate-180) was NEVER generated (dead
branch) and the docstring mislabelled the codes (claimed 1=identity/3=180/4=ccw90).
Canonical uses code 2 (pair1 ops=[2]) and varies template shape/position + anchor.
This version emits all four codes and varies template/anchor.

Rule-safe diversity: grid size, op count/codes, template shape/position, anchor.
Degenerates: no_template, no_anchor, no_ops.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f2b7a9953d61"
VERSION = "3.0.0"  # emit all 4 op codes (was {1,3,4} -> code-2 dead) + varied template/anchor + correct code docs
TASK_ID = "f2b7a9953d61"
SUMMARY = (
    "0-bg grid: (a) ONE color-2 (blue) TEMPLATE (3-6 cell connected shape) in the "
    "upper-left area; (b) ONE color-9 (maroon) ANCHOR with room for the stamp; "
    "(c) bottom row holds 1-3 transform CODES (1=rot90, 2=rot180, 3=flip-h, "
    "4=flip-v) at distinct columns, read left-to-right. Rule: compose the codes "
    "onto the template, stamp the result at the anchor in COLOR 3 (green) on a "
    "blank grid. (Was: fixed L-template/anchor and codes {1,3,4} -> code 2 never "
    "generated.)"
)

INVARIANTS = [
    "exactly one color-2 template (topmost color-2 object) above the bottom row",
    "bottom row holds 1-3 transform codes in {1,2,3,4} at distinct columns",
    "exactly one color-9 anchor; the stamp at the anchor fits in-bounds",
    "output contains only the transformed green (3) stamp",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_anchor", "no_ops")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":   {"type": "int", "default": "10-11 easy / 10-14 med / 13-18 hard", "valid": "8..24"},
    "grid_w":   {"type": "int", "default": "12-13 easy / 12-17 med / 15-20 hard", "valid": "10..24"},
    "n_ops":    {"type": "int", "default": "1-2 easy / 1-3 med / 2-3 hard", "valid": "1..4"},
    "template_size": {"type": "int", "default": "3-5", "valid": "3..6"},
    "density":  {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "default|warm|cool|varied|no_template|no_anchor|no_ops"},
}

_CODES = (1, 2, 3, 4)


def _poly(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, nr, tsz = (10, 11), (12, 13), (1, 2), (3, 4)
    elif difficulty == "hard":
        hr, wr, nr, tsz = (13, 18), (15, 20), (2, 3), (4, 6)
    else:
        hr, wr, nr, tsz = (10, 14), (12, 17), (1, 3), (3, 5)
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        tmpl = _poly(rng, rng.randint(*tsz))
        th = max(r for r, _ in tmpl) + 1; tw = max(c for _, c in tmpl) + 1
        M = max(th, tw)
        if th + 1 >= h - 1 or tw + 1 >= w:
            continue
        # template in the upper-left region (above the bottom row)
        tr = rng.randint(1, max(1, (h - 2) // 2)); tc = rng.randint(1, max(1, w // 2 - tw))
        tcells = {(tr + dr, tc + dc) for dr, dc in tmpl}
        for r, c in tcells:
            g[r][c] = 2
        # anchor: color 9, room for an M x M stamp, not in bottom row, off the template
        anchor_ok = False
        for _ in range(120):
            ar = rng.randint(0, h - 1 - M); ac = rng.randint(0, w - M)
            if ar == h - 1:
                continue
            if (ar, ac) in tcells or g[ar][ac] != 0:
                continue
            g[ar][ac] = 9
            anchor_ok = True
            break
        if not anchor_ok:
            continue
        # bottom-row transform codes at distinct columns (left-to-right order applies)
        n_ops = rng.randint(*nr)
        cols = sorted(rng.sample(range(w), min(n_ops, w)))
        for c in cols:
            g[h - 1][c] = rng.choice(_CODES)
        return g
    raise ValueError("could not realize template/anchor/ops layout")


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    tmpl = [(0, 0), (1, 0), (2, 0), (2, 1)]
    if name == "no_template":
        g[h // 2][w - 5] = 9
        g[h - 1][1] = 1; g[h - 1][3] = 3
        return g
    if name == "no_anchor":
        for dr, dc in tmpl:
            g[1 + dr][1 + dc] = 2
        g[h - 1][1] = 1; g[h - 1][3] = 4
        return g
    if name == "no_ops":
        for dr, dc in tmpl:
            g[1 + dr][1 + dc] = 2
        g[h // 2][w - 5] = 9
        return g
    return g

def _self_components(grid, color, *, rows=None):
    h = len(grid); w = len(grid[0]) if h else 0
    allowed_rows = set(range(h)) if rows is None else set(rows)
    seen = set(); comps = []
    for r in range(h):
        if r not in allowed_rows:
            continue
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and nr in allowed_rows
                            and grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h < 3:
        errs.append("grid must have a non-bottom template/anchor region and a bottom code row")
    bad = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
           if v not in (0, 1, 2, 3, 4, 9)]
    if bad:
        errs.append(f"unexpected colors outside 0/1/2/3/4/9: {bad[:3]}")
    template_comps = _self_components(grid, 2, rows=range(max(0, h - 1)))
    if len(template_comps) != 1:
        errs.append(f"expected exactly one non-bottom color-2 template component, got {len(template_comps)}")
    elif not (3 <= len(template_comps[0]) <= 6):
        errs.append(f"template should have 3-6 cells, got {len(template_comps[0])}")
    anchors = [(r, c) for r in range(max(0, h - 1)) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 1:
        errs.append(f"expected exactly one non-bottom color-9 anchor, got {len(anchors)}")
    codes = [(c, grid[h - 1][c]) for c in range(w) if grid[h - 1][c] != 0]
    if not (1 <= len(codes) <= 3):
        errs.append(f"expected 1-3 bottom-row transform codes, got {len(codes)}")
    if any(v not in _CODES for _, v in codes):
        errs.append(f"bottom row contains non-code values: {codes}")
    if codes != sorted(codes):
        errs.append("bottom-row codes should be read left-to-right at distinct columns")
    if template_comps and anchors:
        cells = template_comps[0]
        th = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        tw = max(c for _, c in cells) - min(c for _, c in cells) + 1
        stamp = max(th, tw)
        ar, ac = anchors[0]
        if ar + stamp > h - 1 or ac + stamp > w:
            errs.append("anchor does not leave room for the transformed square stamp above the code row")
    return errs
