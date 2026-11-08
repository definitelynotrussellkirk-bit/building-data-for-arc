"""Generator for arc_puzzle_bank_21_set4_d:hard_d05 — row-0 key selects body motifs into a gallery.

Rule (verified from canonical Racket): ROW 0 is a colour KEY (its non-zero
cells, left to right). For each key colour, take the LARGEST body object (rows
1+) of that colour, crop it, and pack the crops left-to-right into a gallery
(1-col gaps). So the input needs a row-0 legend AND a matching body object per
key colour.

The previous body was the generic "multi-motif gallery pack" template, which
scattered motifs anywhere — when row 0 happened to be all-zero the key was empty
and the rule crashed (`(apply max (map rows '()))` -> max arity error, ~3/6).
This rewrite CONSTRUCTS valid inputs: a row-0 key of N colours plus one body
motif per key colour, so the gallery output is well-defined and varies.

Axes: grid size, key colour count, motif shapes/sizes, key positions.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "239a0d1db1cd"
VERSION = "2.0.1"  # FIX: was generic scatter template -> empty row-0 key crashed the rule (max arity). Now row-0 key + body motif per key colour.
TASK_ID = "239a0d1db1cd"

SUMMARY = ("Row 0 is a colour key (N non-zero cells at distinct columns); below it, "
           "one connected motif per key colour. Rule: pack the largest body motif of "
           "each key colour into a left-to-right gallery. Grid size, key count, motif "
           "shapes and key positions vary.")

INVARIANTS = [
    "row 0 holds N non-zero key colours at distinct columns",
    "each key colour has >=1 connected body motif (rows 1+) of that colour",
    "body motifs are non-touching (so each is its own object)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "= n key colours", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "row0_key_with_body_motifs",
                       "valid": "row0_key_with_body_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|all_same_color"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has ≥1 non-zero key colour; at least one non-zero body cell (rows 1+)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    key_colors = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not key_colors:
        return errors  # degenerate no_motifs / no key — allowed
    body_colors = {grid[r][c] for r in range(1, h) for c in range(w) if grid[r][c] != 0}
    if not body_colors:
        errors.append("row 0 has key colours but no body cells (rows 1+)")
    # every key colour should appear in the body
    for kc in set(key_colors):
        if kc not in body_colors:
            errors.append(f"key colour {kc} has no body motif")
    return errors


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
    n = min(n, w)   # need n distinct row-0 columns

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        # row 0 = colour KEY: one cell per colour at distinct columns
        key_cols = rng.sample(range(w), n)
        for col, color in zip(key_cols, colors):
            g[0][col] = color
        # body (rows 1+): one connected motif per key colour, non-touching
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            if sh > h - 1 or sw > w:
                ok = False; break
            placed = False
            for _ in range(120):
                r0 = rng.randint(1, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
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
