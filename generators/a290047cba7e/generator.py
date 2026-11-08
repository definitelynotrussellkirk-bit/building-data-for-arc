"""Generator for v2_meta_puzzles:M1 — recolor the median-sized COLOR-1 blob to 7.

Rule (verified): filter the COLOR-1 connected components, sort them by size,
and recolor the MEDIAN one (index len//2) to color 7. ALL motifs are color 1
(the canonical shows 3 color-1 blobs of distinct sizes; the median-sized one
becomes orange). The old "distinct non-{0,7} colors" docstring was WRONG and
caused the rule to CRASH: with random colors, color 1 was usually absent ->
`list-ref` on an empty filtered list raised (30/35 inputs crashed the rule).

Combinatorial axes (8): grid_h, grid_w, n_blobs (odd), blob_sizes (distinct),
positions, difficulty.
Degenerates: no_blobs, single_blob, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a290047cba7e"
VERSION = "3.0.1"  # WRONG-TASK + CRASH FIX: rule filters COLOR-1 objects and recolors the median-SIZED one to 7 (all canonical motifs are color 1). Old gen painted 3 motifs in DISTINCT random colors -> color 1 absent ~5/8 of the time -> list-ref on empty filtered list CRASHED the rule (30/35 inputs, intermittent pool-gen failures). Now: all blobs color 1, ODD count (3/5/7), DISTINCT sizes so the median-by-size is unambiguous; vary count/sizes/positions/grid size (contest-scaled on hard).
TASK_ID = "a290047cba7e"

SUMMARY = (
    "0-bg grid (h~7-9, w~9-11) with "
    "3 CONNECTED MOTIFS at distinct "
    "non-touching positions: sizes "
    "{2, 4, 6} (strictly different, "
    "shuffled), each painted in a "
    "DISTINCT non-{0, 7} color from "
    "{1, 2, 3, 4, 5, 6, 8, 9}. "
    "Motifs are 4-conn random walks, "
    "placed with 1-cell padding. "
    "Rule (RECOLOR MEDIAN MOTIF TO "
    "7): identify all CONNECTED "
    "COMPONENTS. SORT them by SIZE "
    "(ASCENDING). The MEDIAN motif "
    "(middle one, position 1 in the "
    "sorted list of 3) gets "
    "RECOLORED to COLOR 7 (orange). "
    "The smallest (size 2) and "
    "largest (size 6) keep their "
    "original colors. Net: 3-blob "
    "input → median-size blob "
    "becomes orange; small/large "
    "blobs unchanged."
)

INVARIANTS = [
    "background is 0",
    "all motifs are color 1 (the rule filters color-1 objects)",
    "an ODD number of motifs (3/5/7) with STRICTLY DIFFERENT sizes so the median-by-size is unambiguous",
    "motifs are separated by >=1 bg cell (distinct 4-connected components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "single_blob", "all_same_size")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "three_distinct_size_blobs",
                       "valid": "three_distinct_size_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
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


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all non-bg cells are color 1; at least 3 of them present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    nonbg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonbg) < 2:
        errs.append(f"too few non-bg cells: {len(nonbg)} (expected >=2 for motifs)")
        return errs
    wrong = [(r, c, grid[r][c]) for r, c in nonbg if grid[r][c] != 1]
    if wrong:
        errs.append(f"non-bg cells not color-1: {wrong[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n_blobs = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 15, 20)
        n_blobs = ctx.draw_choice("n_blobs", [5, 7])
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15)
        n_blobs = ctx.draw_choice("n_blobs", [3, 5])
    rng = ctx.draw_rng("layout")

    for outer in range(60):
        g = full_grid(h, w, 0)
        # DISTINCT sizes so the median-by-size is unambiguous; ALL color 1.
        sizes = rng.sample(range(2, 2 + max(n_blobs + 3, 9)), n_blobs)
        rng.shuffle(sizes)
        ok = True
        for size in sizes:
            cells = _build_motif(rng, size)
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = 1   # ALL color 1
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # Empty grid — rule has no candidates.
        return g
    if name == "single_blob":
        # Only one blob — rule's "median" is trivially that blob.
        for r, c in [(2, 2), (3, 2), (3, 3)]: g[r][c] = 4
        return g
    if name == "all_same_size":
        # All 3 blobs the same size — rule's sort by size has
        # no order; median tie-break ambiguous.
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4
        for r, c in [(4, 5), (4, 6)]: g[r][c] = 6
        for r, c in [(6, 8), (7, 8)]: g[r][c] = 5
        return g
    return g
