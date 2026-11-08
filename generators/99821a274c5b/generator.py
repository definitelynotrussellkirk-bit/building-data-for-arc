"""Generator for arc_puzzle_bank_21_set19_bundle:medium_p06 — object column histogram.

Rule: take the first non-bg object. For each column of its bbox, count
how many cells are filled. Output is a bar histogram (height = max
count, columns = bbox width); each column's bar rises from the bottom.

Combinatorial axes (8): grid_h, grid_w, palette_kind, stair_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blob, multiple_blobs, uniform_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99821a274c5b"
VERSION = "2.0.1"  # self_check; distinct 18 / out_sh=2: blob was a FIXED staircase (counts always [1..sw], sw in {3,4}) so only 2 output shapes + constant content. Rule histograms per-column fill counts of the largest blob -> use a RANDOM connected blob with VARYING column counts so output height (=max count) and width (=bbox cols) and content all vary.
TASK_ID = "99821a274c5b"
SUMMARY = "One random connected blob; the rule histograms its per-column fill counts (output height = max count, width = bbox columns). Blob shape, span and per-column counts all vary."

INVARIANTS = [
    "background is 0",
    "exactly one non-bg blob (the largest, which the rule selects)",
    "the blob's per-column fill counts are not all equal (so the output is not a flat/identity bar)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blob", "multiple_blobs", "uniform_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "stair_w":        {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "single_staircase_blob",
                       "valid": "single_staircase_blob"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        sw = ctx.draw_int("stair_w", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        sw = ctx.draw_int("stair_w", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        sw = ctx.draw_int("stair_w", 3, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    # Random connected blob whose per-column fill counts vary, so the
    # histogram output (height = max count, width = bbox columns) differs
    # across instances in shape, span AND content. sw scales the cell budget.
    poly, ph, pw = [(0, 0)], 1, 1
    for _ in range(80):
        cand = _rand_poly(rng, rng.randint(sw + 1, sw * 3))
        ch = max(r for r, _ in cand) + 1
        cw = max(c for _, c in cand) + 1
        counts = [sum(1 for r, cc in cand if cc == c) for c in range(cw)]
        if cw < 2 or ch > h or cw > w:
            continue
        if len(set(counts)) < 2:   # all columns equal -> flat/identity output
            continue
        poly, ph, pw = cand, ch, cw
        break
    r0 = rng.randint(0, h - ph)
    c0 = rng.randint(0, w - pw)
    for r, c in poly:
        g[r0 + r][c0 + c] = color
    return g


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_blob":
        # blank → no blob to histogram
        return g
    if name == "multiple_blobs":
        # 2 separate blobs → "first non-bg blob" is ambiguous
        for k in range(3):
            for j in range(k + 1):
                g[3 - j][1 + k] = 4
        for k in range(3):
            for j in range(k + 1):
                g[6 - j][6 + k] = 6
        return g
    if name == "uniform_columns":
        # solid rectangle → all column counts equal, output is identity (no signal)
        for r in range(2, 5):
            for c in range(3, 7):
                g[r][c] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    h, w = len(grid), len(grid[0])
    nz = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not nz:
        return ["no blob"]
    colors = {grid[r][c] for r, c in nz}
    if len(colors) != 1:
        errs.append("blob is not monochrome")
    seen = set(); comps = []
    for cell in list(nz):
        if cell in seen: continue
        stack = [cell]; seen.add(cell); comp=[]
        while stack:
            r,c = stack.pop(); comp.append((r,c))
            for nr,nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr,nc) in nz and (nr,nc) not in seen:
                    seen.add((nr,nc)); stack.append((nr,nc))
        comps.append(comp)
    if len(comps) != 1:
        errs.append(f"expected one connected non-bg blob, got {len(comps)}")
    comp = comps[0]
    cs = [c for _, c in comp]
    counts = [sum(1 for _r, cc in comp if cc == c) for c in range(min(cs), max(cs) + 1)]
    if len(counts) < 2:
        errs.append("blob bbox has fewer than two columns")
    if len(set(counts)) < 2:
        errs.append("blob per-column counts are uniform; histogram rule is hidden")
    return errs
