"""Generator for arc_puzzle_bank_21_set7:hard_g19 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3809855f9eac"
VERSION = "2.1.0"  # enforce non-empty XOR for the two rule-selected motifs; add self_check
TASK_ID = "3809855f9eac"

SUMMARY = (
    "0-bg grid with ≥2 connected motifs in distinct non-zero colors "
    "(≥1-cell buffer, 3-5 cells each, varied shapes). The rule "
    "consumes the FIRST TWO components in bbox-top-left sort order; "
    "any additional motifs are ignored by the rule but add visual "
    "variety. Rule: sort all connected components by bbox top-left "
    "(row-major). Take the first two. Crop each to its bbox. "
    "Normalize the pair to a common (max-h × max-w) bounding box. "
    "Compute symmetric difference between the two binary masks: "
    "output cell = 8 if exactly one of the two masks has a non-zero "
    "cell there, else 0. Output size = (max-h × max-w)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 connected motifs in distinct non-zero colors",
    "≥1-cell buffer between motifs (no 8-neighborhood touch)",
    "the first two motifs (by bbox top-left) have non-trivial XOR (not identical shape)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _norm_mask(cells):
    r1, c1, _, _ = _bbox(cells)
    return frozenset((r - r1, c - c1) for r, c in cells)


def _first_two_xor_nonempty(placed_cells):
    ordered = sorted(placed_cells, key=lambda cells: _bbox(cells)[:2])
    return len(ordered) >= 2 and _norm_mask(ordered[0]) != _norm_mask(ordered[1])


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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        placed_cells = []
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                abs_cells = []
                for r, c in cells:
                    ar, ac = r0 + r - min(rs), c0 + c - min(cs)
                    g[ar][ac] = color
                    abs_cells.append((ar, ac))
                placed_cells.append(abs_cells)
                placed = True; break
            if not placed:
                ok = False; break
        if ok and _first_two_xor_nonempty(placed_cells):
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components, components_have_clearance
    errors = []
    comps = sorted(components(grid), key=lambda comp: comp["bbox"][:2])
    min_count = {"easy": 2, "hard": 4}.get(difficulty, 3)
    if len(comps) < min_count:
        errors.append(f"expected at least {min_count} motifs, found {len(comps)}")
    if len({c["color"] for c in comps}) != len(comps):
        errors.append("motif colors are not distinct")
    if not components_have_clearance(grid, comps, diagonal=True):
        errors.append("motifs lack a one-cell 8-neighborhood moat")
    if len(comps) >= 2 and comps[0]["norm"] == comps[1]["norm"]:
        errors.append("first two row-major motifs have empty XOR")
    return errors
