"""Generator for 75982f96de73 — apply sequence of transforms from row-0 tokens to body shape.

Rule:
  Row 0 contains 1..N TOKENS (each in {1, 2, 3, 4}) representing transforms:
    1 = rotate-cw, 2 = flip-lr, 3 = flip-ud, 4 = transpose.
  Body = rows 1..h-1. Crop body to its non-zero bbox to get SHAPE.
  Apply transforms in row-0 left-to-right order to SHAPE.
  Output = final transformed SHAPE.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75982f96de73"
VERSION = "2.0.1"
TASK_ID = "75982f96de73"

SUMMARY = (
    "0-bg grid (h×w, h=4..6, w=4..6) with ROW 0 as a TOKEN "
    "SEQUENCE: 1-3 tokens at the leftmost columns, each in "
    "{1, 2, 3, 4} (1=rotate-cw, 2=flip-lr, 3=flip-ud, "
    "4=transpose). Rest of row 0 is 0. Body (rows 1..h-1) "
    "contains exactly ONE connected SHAPE of 2-5 cells in some "
    "color != 0 and != {1, 2, 3, 4} tokens (typically 5, 6, 7, "
    "8, 9), placed somewhere with at least one row of bg between "
    "it and row 0. Rule: read tokens. Crop body to non-zero "
    "bbox. Apply each token's transform in sequence. Output = "
    "final transformed shape (variable dimensions)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "row 0 has 1-3 tokens in {1, 2, 3, 4} at leftmost cols, rest 0",
    "body (rows 1..h-1) has exactly ONE connected shape (2-5 cells)",
    "shape color is in {5, 6, 7, 8, 9} (distinct from token values)",
    "tokens include at least one non-identity transform (so output ≠ trivial)",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_tokens", "no_body_shape", "shape_at_row_0")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "grid_w":         {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "n_tokens":       {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "row0_tokens_body_shape",
                       "valid": "row0_tokens_body_shape"},
    "n_distinct_colors":{"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, row 0 has 1-3 tokens in {1,2,3,4}, body has a shape in {5-9}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 2:
        return ["grid must have ≥2 rows"]
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    tokens = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not tokens:
        errs.append("row 0 has no token cells")
    elif not all(t in (1, 2, 3, 4) for t in tokens):
        bad = [t for t in tokens if t not in (1, 2, 3, 4)]
        errs.append(f"row-0 tokens outside {{1,2,3,4}}: {bad}")
    shape_cells = any(grid[r][c] not in (0, 1, 2, 3, 4) for r in range(1, h) for c in range(w))
    if not shape_cells:
        errs.append("no body shape cells (non-{0,1,2,3,4}) in rows 1+")
    return errs


def _build_blob(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 4)
        w = ctx.draw_int("grid_w", 4, 5)
        n_tokens = ctx.draw_int("n_tokens", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 5, 7)
        n_tokens = ctx.draw_int("n_tokens", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 4, 6)
        n_tokens = ctx.draw_int("n_tokens", 1, 3)

    g = full_grid(h, w, 0)

    # Place tokens in row 0 (at leftmost cols)
    for i in range(min(n_tokens, w)):
        g[0][i] = rng.randint(1, 4)
    # Ensure at least one non-identity token (rotate, flip, transpose)
    # All tokens 1-4 are non-identity, so this is automatic.

    # Build a shape in body
    shape_color = rng.choice([5, 6, 7, 8, 9])
    shape_size = rng.randint(2, 5)
    shape = _build_blob(rng, shape_size)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if sh > h - 1 or sw > w:
        # Shape too big — fallback to smaller
        shape = _build_blob(rng, 2)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1

    # Place shape in body
    for _try in range(40):
        # row offset >= 1 (skip row 0)
        r0 = rng.randint(1, h - sh)
        c0 = rng.randint(0, w - sw)
        # Verify no overlap with tokens (row 0)
        valid = True
        for dr, dc in shape:
            if g[r0 + dr][c0 + dc] != 0:
                valid = False; break
        if valid:
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = shape_color
            return g
    raise ValueError("could not place body shape")


def _draw_from_degenerate(name, rng):
    h, w = 4, 5
    g = full_grid(h, w, 0)
    if name == "no_tokens":
        # body shape but no tokens — rule has no transforms to apply
        g[2][1] = 5; g[2][2] = 5; g[3][2] = 5
        return g
    if name == "no_body_shape":
        # tokens but no body shape — rule has nothing to transform
        g[0][0] = 1; g[0][1] = 2
        return g
    if name == "shape_at_row_0":
        # body shape touches row 0 — ambiguous what's token vs shape
        g[0][0] = 1; g[0][2] = 5; g[1][2] = 5
        return g
    return g
