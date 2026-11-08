"""Generator for arc_puzzle_bank_21_set8:medium_h12 — slide objects left against blockers.

Rule: collect color-5 blockers; extract non-5 components (sorted by leftmost
column) and slide each LEFT until it hits a blocker, an already-placed object,
or the left edge (gravity-left with stationary + dynamic blockers).

(The stale "gallery pack" header was wrong; the SUMMARY below is authoritative.)

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8132e595372"
VERSION = "2.1.1"  # fixed stale 'gallery pack' header (rule is slide-left-against-blockers; SUMMARY was already correct). Added vertical 5-wall SEGMENT blockers (canonical uses wall-columns, not just single cells) for closer distribution + more varied sliding."
TASK_ID = "c8132e595372"

SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) with 3-4 ISOLATED motifs in "
    "distinct non-{0,5} colors AND a few color-5 (gray) "
    "BLOCKER cells scattered around. Motifs and blockers are "
    "separated. Rule: collect blockers (color-5 cells). "
    "Extract non-5 components, sort by leftmost column "
    "ascending. Start with a fresh empty grid containing only "
    "the blockers. For each component in left-to-right order: "
    "slide its cells LEFT (dr=0, dc=-1) until they hit a "
    "blocker, an already-placed cell, or the grid's left "
    "edge. Paint the slid cells with the component's color. "
    "Net: gravity-left with both stationary blockers (5) and "
    "stacking dynamic blockers from earlier-placed objects."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-{0,5} colors at distinct positions",
    "≥1 color-5 BLOCKER cell as obstacle",
    "motifs and blockers are placed with adequate space for sliding",
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
        # Place color-5 blockers: a mix of single cells and short vertical wall
        # segments (canonical uses wall-columns), scattered as obstacles.
        n_blockers = rng.randint(2, 4)
        for _ in range(n_blockers):
            seg = rng.randint(1, 3)                       # wall-segment height
            for _try in range(40):
                br = rng.randint(0, h - seg)
                bc = rng.randint(2, w - 2)
                if _free(g, br, bc, br + seg - 1, bc):
                    for r in range(br, br + seg):
                        g[r][bc] = 5
                    break
        # Then place colored components
        colors = rng.sample([2, 3, 4, 6, 7, 8, 9], n)
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(1, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid must have >=1 color-5 blocker and >=2 non-{0,5} colored components."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not fives:
        msgs.append("no color-5 blocker cells found")
    nonbg = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 5))
    if len(nonbg) < 2:
        msgs.append(f"expected >=2 distinct non-{{0,5}} colors, found {len(nonbg)}")
    return msgs


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
