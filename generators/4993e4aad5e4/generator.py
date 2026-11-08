"""Generator for arc_puzzle_bank_21_set15:S15_H7 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4993e4aad5e4"
VERSION = "3.0.1"  # distinct=62/dup-outputs 43%: odd shape was only 3-6 cells in a FIXED orientation, and output = that shape's exact orientation (crop normalizes by translation only). Now LARGER odd/common shapes + each object placed in a random DIHEDRAL orientation. The rule's signature is dihedral-INVARIANT so oddness is preserved (odd keeps a distinct cell count), but the output orientation of the odd shape now varies -> more distinct.
TASK_ID = "4993e4aad5e4"

SUMMARY = (
    "0-bg grid with several monochrome 4-connected motifs in colours from "
    "{2,3,4,5} (the rule's candidate set). N-1 motifs share one shape; exactly "
    "ONE motif has a different shape (the odd one out). Rule: of the {2,3,4,5} "
    "objects, take the canonical dihedral shape signature of each and CROP the "
    "object whose signature is least common (the odd one out), recoloured 8. "
    "Motif shapes, count, colours and positions vary."
)

INVARIANTS = [
    "motifs use colours in {2,3,4,5} (the rule only considers those)",
    "N-1 motifs share one dihedral shape; exactly one differs (the odd one out)",
    "motifs are 4-connected, non-touching (8-conn buffer)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "n":              {"type": "int", "default": "3 easy / 3-4 med / 4-5 hard", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "colours from {2,3,4,5}", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "<=4", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|all_same_color"},
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


def _orient(rng, cells):
    """Apply a random dihedral transform. The rule's signature is dihedral-
    invariant (so this does not change which object is odd), but the OUTPUT is
    the odd object's drawn orientation -> orienting adds output variety."""
    k = rng.randint(0, 7)
    out = []
    for (r, c) in cells:
        if k & 1:
            r, c = c, r
        if k & 2:
            r = -r
        if k & 4:
            c = -c
        out.append((r, c))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 3, 3)
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
        # N-1 motifs share one shape; ONE is a different shape (odd one out).
        # Different cell counts guarantee different dihedral signatures.
        k_common = rng.randint(4, 6)
        common = _build_motif(rng, k_common)
        # odd has a DIFFERENT cell count (guarantees a different dihedral sig)
        odd_k = rng.choice([x for x in range(3, 8) if x != k_common])
        odd = _build_motif(rng, odd_k)
        # each placement gets its own random dihedral orientation (commons keep
        # their shared signature; the odd's drawn orientation varies the output)
        shapes = [_orient(rng, common) for _ in range(n - 1)] + [_orient(rng, odd)]
        rng.shuffle(shapes)
        # colours from the rule's candidate set {2,3,4,5} (shape, not colour,
        # drives the rule); distinct where possible, else repeat.
        pool = [2, 3, 4, 5]; rng.shuffle(pool)
        colors = [pool[i % 4] for i in range(n)]
        ok = True
        for color, cells in zip(colors, shapes):
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
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
    """bg=0; >=3 distinct non-0 colors (motifs in {2,3,4,5}); >=3 non-0 cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 3:
        errors.append(f"expected >=3 distinct non-0 motif colors, found {len(colors)}")
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonzero) < 3:
        errors.append(f"expected >=3 non-zero cells, found {len(nonzero)}")
    return errors
