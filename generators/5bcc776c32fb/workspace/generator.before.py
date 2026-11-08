"""Generator for arc_additional_puzzle_bank_volume20:E134 — Mark middle of horizontal 1-line of odd length ≥3.

Rule: each 1-blob that is a single row of size ≥3 and odd → set
middle cell to 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_lines,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: only_even_lengths, only_vertical, no_lines.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5bcc776c32fb"
VERSION = "2.1.0"  # fix identity_demo: lines on adjacent rows/cols 4-merged into one object (obj-h>1) so no clean horizontal odd line survived -> rule never fired -> output==input. Place every line with a 1-cell margin (stays a separate object) and guarantee >=1 odd line lands.
TASK_ID = "5bcc776c32fb"
SUMMARY = "Mix of color-1 lines (horizontal, vertical, various lengths). Rule paints the MIDDLE cell of each horizontal 1-line of odd length ≥ 3 with color 2; lines of even length, vertical lines, and isolated cells stay unchanged."

# Rivals: 'mark middle of every line' refuted by ≥2 demos where
# vertical lines stay unchanged. 'mark every odd cell' refuted by any
# demo where only the strict middle becomes 2. 'use color 1 for the
# mark' refuted by any demo (mark is 2). 'mark length-2 lines too'
# refuted by ≥1 demo where length-4 line stays unchanged. 3 demos
# with mixed line types cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "≥2 horizontal 1-lines of odd length ≥3",
    "1 horizontal 1-line of even length (won't qualify)",
    "1 vertical 1-line",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("only_even_lengths", "only_vertical", "no_lines")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "8..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_lines":        {"type": "int", "default": "2", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "row_lines_with_distractors",
                       "valid": "row_lines_with_distractors"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "1..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear(g, cells):
    """True if every cell AND its 8-neighbours are bg, so a line placed here
    stays an isolated object (won't 4-merge with another color-1 line)."""
    h, w = len(g), len(g[0])
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 9, 12)
        n_odd, n_even, n_vert = 1, 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 15, 20)
        n_odd = rng.randint(3, 5)
        n_even = rng.randint(2, 3)
        n_vert = rng.randint(2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15)
        n_odd, n_even, n_vert = 2, 1, 2
    g = full_grid(h, w, 0)
    used_rows = set()
    placed_odd = 0
    # Place odd-length horizontal lines (3, 5, or 7), isolated.
    for _ in range(n_odd):
        for _ in range(60):
            r = rng.randint(0, h - 1)
            length = rng.choice([3, 5, 7])
            if r in used_rows or length > w: continue
            c = rng.randint(0, w - length)
            cells = [(r, c + i) for i in range(length)]
            if not _clear(g, cells): continue
            for (rr, cc) in cells:
                g[rr][cc] = 1
            used_rows.add(r); placed_odd += 1; break
    # Guarantee at least one odd line (else the rule never fires -> identity).
    if placed_odd == 0:
        done = False
        for r in range(h):
            if done:
                break
            for c in range(0, w - 2):
                cells = [(r, c), (r, c + 1), (r, c + 2)]
                if _clear(g, cells):
                    for (rr, cc) in cells:
                        g[rr][cc] = 1
                    used_rows.add(r); placed_odd += 1; done = True
                    break
    # Place even-length horizontal lines (2 or 4), isolated.
    for _ in range(n_even):
        for _ in range(60):
            r = rng.randint(0, h - 1)
            length = rng.choice([2, 4])
            if r in used_rows or length > w: continue
            c = rng.randint(0, w - length)
            cells = [(r, c + i) for i in range(length)]
            if not _clear(g, cells): continue
            for (rr, cc) in cells:
                g[rr][cc] = 1
            used_rows.add(r); break
    # Place vertical lines (will not match the rule), isolated.
    for _ in range(n_vert):
        for _ in range(60):
            cv = rng.randint(0, w - 1)
            length = rng.randint(3, 5)
            if length > h: continue
            rv = rng.randint(0, h - length)
            cells = [(rv + dr, cv) for dr in range(length)]
            if not _clear(g, cells): continue
            for (rr, cc) in cells:
                g[rr][cc] = 1
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least one color-1 object must be a single-row horizontal line of
    odd length >=3 (the only shape the rule marks)."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or seen[r][c]:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < h and 0 <= cc < w) or seen[cr][cc] or grid[cr][cc] != 1:
                    continue
                seen[cr][cc] = True
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    stack.append((cr + dr, cc + dc))
            rs = {p[0] for p in cells}
            if len(rs) == 1 and len(cells) >= 3 and len(cells) % 2 == 1:
                return []
    return ["no horizontal color-1 line of odd length >=3 -> rule is a no-op"]


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "only_even_lengths":
        # only even-length horizontal 1-lines → no odd-length lines, rule fires zero times
        for c in range(1, 5): g[2][c] = 1   # length 4
        for c in range(3, 7): g[5][c] = 1   # length 4
        return g
    if name == "only_vertical":
        # only vertical 1-lines → predicate "single row" fails, rule fires zero times
        for r in range(1, 5): g[r][2] = 1
        for r in range(3, 7): g[r][7] = 1
        return g
    if name == "no_lines":
        # blank grid → no 1-cells at all, rule fires zero times
        return g
    return g
