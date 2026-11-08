"""Generator for arc_puzzle_bank_21_set17_bundle:medium_p04 — bbox of 2 same-color markers.

Rule: for EACH color that appears as exactly 2 connected components, fill the
combined bounding box of the two with that color.

Coverage gap (prior): the generator placed only ONE color-pair per grid (one
filled bbox), but the canonical has MULTIPLE colors each as a pair -> multiple
filled bboxes. This version places K color-pairs (1-4) with non-overlapping
bboxes (so the output is clean) on bigger grids.

Rule-safe diversity: grid size, number of color-pairs, motif shapes/sizes,
colors, positions.
Degenerates: no_motifs, single_motif, three_motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f507744a2873"
VERSION = "2.0.0"  # multiple color-pairs (was 1) -> multiple filled bboxes (matches canonical) + bigger grids
TASK_ID = "f507744a2873"
SUMMARY = (
    "0-bg grid (size varies) with K (1-4) COLORS, each appearing as EXACTLY 2 "
    "separated motifs in non-overlapping regions. Rule: for each color with "
    "exactly 2 components, fill the combined bounding box of the two with that "
    "color. Net: each color-pair becomes a solid rectangle spanning its two "
    "markers. (Was: a single color-pair per grid -> one filled bbox.)"
)

INVARIANTS = [
    "background is 0",
    "each active color appears as exactly 2 separated components",
    "different colors' combined bboxes do not overlap (clean, deterministic output)",
    "motifs are separated by a 1-cell halo (each a distinct component)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "three_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":   {"type": "int", "default": "6-9 easy / 8-13 med / 11-18 hard", "valid": "4..20"},
    "grid_w":   {"type": "int", "default": "7-10 easy / 9-14 med / 12-20 hard", "valid": "5..22"},
    "n_pairs":  {"type": "int", "default": "1-2 easy / 2-3 med / 3-4 hard", "valid": "1..5"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_distinct_colors": {"type": "int", "default": "= n_pairs", "valid": "1..5"},
    "density":  {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _free(g, r0, c0, sh, sw):
    h, w = len(g), len(g[0])
    for r in range(r0 - 1, r0 + sh + 1):
        for c in range(c0 - 1, c0 + sw + 1):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return True


def _overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, kr = (6, 9), (7, 10), (1, 2)
    elif difficulty == "hard":
        hr, wr, kr = (11, 18), (12, 20), (3, 4)
    else:
        hr, wr, kr = (8, 13), (9, 14), (2, 3)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        K = min(rng.randint(*kr), 5)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], K)
        g = full_grid(h, w, 0)
        bboxes = []          # combined bbox per placed color
        ok = True
        for color in colors:
            placed_cells = []
            good = True
            for _ in range(2):     # exactly 2 motifs
                cells = _build_motif(rng, rng.randint(2, 4))
                rs = [r for r, _ in cells]; cs = [c for _, c in cells]
                sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
                done = False
                for _ in range(60):
                    r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                    if _free(g, r0, c0, sh, sw):
                        abs_cells = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
                        placed_cells += abs_cells
                        for (r, c) in abs_cells:
                            g[r][c] = color
                        done = True
                        break
                if not done:
                    good = False; break
            if not good:
                ok = False; break
            rs = [r for r, _ in placed_cells]; cs = [c for _, c in placed_cells]
            bb = (min(rs), min(cs), max(rs), max(cs))
            if any(_overlap(bb, ob) for ob in bboxes):
                ok = False; break        # combined bboxes must not overlap
            bboxes.append(bb)
        if ok and bboxes:
            return g

    # deterministic fallback: one color-pair
    g = full_grid(7, 9, 0)
    g[1][1] = 4; g[3][4] = 4
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        for r, c in [(2, 2), (2, 3), (3, 3)]: g[r][c] = 4
        return g
    if name == "three_motifs":
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4
        for r, c in [(4, 5), (4, 6)]: g[r][c] = 4
        for r, c in [(6, 1), (6, 2)]: g[r][c] = 4
        return g
    return g
