"""Generator for arc_puzzle_bank_twentyfirst21:H147 — row-token program over a tiny body.

Canonical rule: read the nonzero TOKEN cells in row 0 from left to right.
Crop the nonzero BODY from rows 2..end, then execute the token sequence:
color 2 = rotate clockwise, color 3 = flip left/right, any other token = transpose.
The output is the final transformed body shape.

Canonical examples are tiny 5×4/5×5 boards: row 1 is an ignored color-8
separator, row 0 has one or two sparse program tokens, and rows 2..end contain
a single connected monochrome body on black background.  Keep generated inputs in
that regime; large multicolor bodies teach a different distribution.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6dc5e7b03042"
VERSION = "2.2.0"
TASK_ID = "6dc5e7b03042"

SUMMARY = (
    "Tiny 5×4/5×5 0-bg grid. Row 0 holds 1–2 sparse program tokens: "
    "2 rotates the body 90° clockwise, 3 flips it left-right, and any other "
    "token transposes it. Row 1 is an ignored color-8 separator. Rows 2..end "
    "hold one connected monochrome body. Output is the transformed body crop."
)

INVARIANTS = [
    "background is 0",
    "row 0 contains one or two nonzero program tokens",
    "row 1 is a solid color-8 separator",
    "rows 2..end contain exactly one connected monochrome body",
    "the input area stays in the canonical tiny-board range",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5"},
    "grid_w":         {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "token_count":    {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "token_order":    {"type": "str", "default": "rng canonical branch token(s)",
                       "valid": "uses 2, 3, or other-token transpose"},
    "body_size":      {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "body_palette":   {"type": "int", "default": "1 body color", "valid": "1"},
    "position_bias":  {"type": "str", "default": "row0_program_8_separator_body_below",
                       "valid": "row0_program_8_separator_body_below"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|all_same_color"},
}


_BODY_TEMPLATES = [
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)],      # canonical train-0 style
    [(0, 1), (0, 2), (1, 2), (2, 2), (2, 3)],      # canonical train-1 style
    [(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
]


def _token_sequence(rng, sample_index, n):
    # Rotate through branches across episode pairs so a normal 3+demo task sees
    # rotate, flip, and transpose, while each individual input stays canonical.
    base = [2, 3, rng.choice([4, 5, 6, 7, 8, 9])]
    first = base[sample_index % len(base)]
    if n == 1:
        return [first]
    # Pair a geometric token with a transpose token or with the other geometric
    # token, matching the two-token canonical examples.
    if first == 2:
        second = rng.choice([3, 4, 5, 6, 7, 8, 9])
    elif first == 3:
        second = rng.choice([2, 4, 5, 6, 7, 8, 9])
    else:
        second = rng.choice([2, 3])
    return [first, second]


def _components_nonzero(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(2, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    h = 5
    if difficulty == "hard":
        w = ctx.draw_int("grid_w", 5, 5)
        token_count = ctx.draw_int("token_count", 2, 2)
    elif difficulty == "easy":
        w = ctx.draw_int("grid_w", 4, 4)
        token_count = ctx.draw_int("token_count", 1, 1)
    else:
        w = ctx.draw_int("grid_w", 4, 5)
        token_count = ctx.draw_int("token_count", 1, 2)

    g = full_grid(h, w, 0)
    for c in range(w):
        g[1][c] = 8

    tokens = _token_sequence(rng, sample_index, token_count)
    cols = sorted(rng.sample(range(w), token_count))
    for c, tok in zip(cols, tokens):
        g[0][c] = tok

    body = [p for p in rng.choice(_BODY_TEMPLATES) if p[1] < w]
    if len(body) < 3:
        body = [(0, 1), (1, 1), (2, 1)]
    color = rng.choice([5, 6, 7, 9])
    for r, c in body:
        g[2 + r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 4, 0)
    for c in range(4):
        g[1][c] = 8
    if name == "no_motifs":
        return g
    if name == "single_motif":
        g[2][1] = 5
        return g
    if name == "all_same_color":
        g[0][0] = 2
        for r, c in [(0, 1), (1, 1), (2, 1)]:
            g[2 + r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not (h == 5 and 4 <= w <= 5):
        errs.append(f"expected canonical tiny 5x4/5 board, got {h}x{w}")
    tokens = [v for v in grid[0] if v != 0]
    if not (1 <= len(tokens) <= 2):
        errs.append(f"expected 1..2 row-0 tokens, got {len(tokens)}")
    if any(t < 2 or t > 9 for t in tokens):
        errs.append(f"program tokens must be nonzero ARC colors 2..9: {tokens}")
    if any(grid[1][c] != 8 for c in range(w)):
        errs.append("row 1 must be a solid color-8 separator")
    comps = _components_nonzero(grid)
    if len(comps) != 1:
        errs.append(f"expected one connected body below row 1, got {len(comps)}")
    elif len(comps[0][1]) < 3:
        errs.append("body is too small to teach a visible transform")
    body_colors = {grid[r][c] for r in range(2, h) for c in range(w) if grid[r][c] != 0}
    if len(body_colors) != 1:
        errs.append(f"canonical body should be monochrome, got colors {sorted(body_colors)}")
    return errs
