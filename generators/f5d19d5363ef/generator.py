"""Generator for arc_additional_puzzles_21_set17_bundle:H116 — Recolor nested 1-frames by depth from palette.

Rule: sort 1-frames by bbox-area desc; recolor by depth using palette
[2 4 6 7 3 9].

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, single_frame, non_nested.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f5d19d5363ef"
VERSION = "3.1.0"  # POISON FIX: inset could be 1 -> rings 4-adjacent -> MERGED into one component (rule recolored a blob, not nested rings). Inset now >=2 (1-cell gap, matches canonical).
TASK_ID = "f5d19d5363ef"
SUMMARY = (
    "0-bg grid (h, w ∈ 9-18) with: "
    "N_FRAMES ∈ 3-6 NESTED COLOR-1 "
    "RECTANGULAR FRAMES (concentric, "
    "each smaller than the last) "
    "with RANDOMIZED OUTER POSITION "
    "and OFFSETS — outermost frame "
    "anchored at random (or0, oc0) "
    "with size (oh, ow), each "
    "inner frame inset by a random "
    "(dr, dc) ≥ 1 from the previous "
    "on each side. All frames have "
    "STRICTLY DISTINCT bbox areas. "
    "Rule (SORT 1-FRAMES BY BBOX "
    "AREA DESCENDING; ASSIGN EACH "
    "FRAME (BY DEPTH RANK 0 = "
    "OUTERMOST) A COLOR FROM "
    "PALETTE [2,4,6,7,3,9]; "
    "RECOLOR EVERY CELL OF THAT "
    "FRAME TO THE ASSIGNED COLOR): "
    "EXTRACT all 1-frames. SORT by "
    "bbox area descending. For rank "
    "i: RECOLOR frame i with "
    "palette[i] ∈ [2,4,6,7,3,9]. "
    "Net: nested 1-frames recolored "
    "by nesting depth."
)

INVARIANTS = [
    "between 3 and 5 nested 1-frames",
    "all bboxes have distinct areas",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "non_nested")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9-12 easy / 12-18 med / 16-26 hard", "valid": "7..28"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 12-18 med / 16-26 hard", "valid": "7..28"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "as many as fit, up to 6 (palette size)", "valid": "2..6"},
    "inset":          {"type": "int", "default": "2-3 per side (gap 1-2, >=2 keeps rings separate)", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "nested_concentric_frames",
                       "valid": "nested_concentric_frames"},
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
        hr, wr = (11, 14), (11, 14)
    elif difficulty == "hard":
        hr, wr = (16, 26), (16, 26)
    else:
        hr, wr = (12, 18), (12, 18)
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*wr)
    g = full_grid(h, w, 0)
    # outer frame: the full grid border (matches canonical) with a small random
    # margin sometimes, so the onion has the most rings.
    m = rng.choice([0, 0, 0, 1])
    r1, c1, r2, c2 = m, m, h - 1 - m, w - 1 - m

    placed = 0
    while placed < 5 and (r2 - r1) >= 2 and (c2 - c1) >= 2:   # >=3x3 ring
        for c in range(c1, c2 + 1):
            g[r1][c] = 1; g[r2][c] = 1
        for r in range(r1, r2 + 1):
            g[r][c1] = 1; g[r][c2] = 1
        placed += 1
        # inset >=2 per side => a >=1-cell gap so the next ring is a SEPARATE
        # 4-connected component (inset 1 would merge them; that was the poison).
        # Bias to 2 (gap 1) like the canonical so more rings fit.
        r1 += rng.choice([2, 2, 3]); r2 -= rng.choice([2, 2, 3])
        c1 += rng.choice([2, 2, 3]); c2 -= rng.choice([2, 2, 3])
    if placed < 3:                                            # ensure >=3 rings
        g = full_grid(11, 11, 0)
        for c in range(11): g[0][c] = 1; g[10][c] = 1
        for r in range(11): g[r][0] = 1; g[r][10] = 1
        for c in range(2, 9): g[2][c] = 1; g[8][c] = 1
        for r in range(2, 9): g[r][2] = 1; g[r][8] = 1
        for c in range(4, 7): g[4][c] = 1; g[6][c] = 1
        for r in range(4, 7): g[r][4] = 1; g[r][6] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # blank → no frames to recolor by depth
        return g
    if name == "single_frame":
        # only one frame → trivial: depth 0, gets palette[0] = 2
        for c in range(w): g[0][c] = 1; g[h - 1][c] = 1
        for r in range(h): g[r][0] = 1; g[r][w - 1] = 1
        return g
    if name == "non_nested":
        # two side-by-side (non-nested) frames → depth ordering ill-defined
        for c in range(0, 5): g[1][c] = 1; g[5][c] = 1
        for r in range(1, 6): g[r][0] = 1; g[r][4] = 1
        for c in range(6, 11): g[1][c] = 1; g[5][c] = 1
        for r in range(1, 6): g[r][6] = 1; g[r][10] = 1
        return g
    return g


def _components(grid, color):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    comps = []
    while cells:
        start = cells.pop()
        stack = [start]
        comp = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells:
                    cells.remove(nb)
                    stack.append(nb)
                    comp.append(nb)
        comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    comps = _components(grid, 1)
    if not (3 <= len(comps) <= 5):
        errors.append(f"expected 3..5 separated nested frames, got {len(comps)}")
    boxes = []
    for comp in comps:
        rs = [r for r, _ in comp]; cs = [c for _, c in comp]
        boxes.append((min(rs), min(cs), max(rs), max(cs)))
        r1, c1, r2, c2 = boxes[-1]
        expected = (
            {(r1, c) for c in range(c1, c2 + 1)}
            | {(r2, c) for c in range(c1, c2 + 1)}
            | {(r, c1) for r in range(r1, r2 + 1)}
            | {(r, c2) for r in range(r1, r2 + 1)}
        )
        if set(comp) != expected:
            errors.append("a color-1 component is not a clean rectangular frame")
    areas = [(r2 - r1 + 1) * (c2 - c1 + 1) for r1, c1, r2, c2 in boxes]
    if len(areas) != len(set(areas)):
        errors.append("nested frame bbox areas should be distinct")
    for outer, inner in zip(sorted(boxes), sorted(boxes)[1:]):
        pass
    return sorted(set(errors))
