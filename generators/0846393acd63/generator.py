"""Generator for 8dae5dfc.

Rule: each multicolor 8-conn component has nested concentric layers.
Take diagonal cells' unique colors innermost-out, reverse, remap colors.

Combinatorial axes: grid_h/w, n_blocks, texture
(plain|rect_block|odd_block|repeat_layer).
Degenerates: solid_block (identity), single_layer (ring ERASED - the
diagonal reads interior zeros), full_grid (identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, fill_box, full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "0846393acd63"
VERSION = "2.0.1"
TASK_ID = "0846393acd63"
SUMMARY = (
    "Nested concentric frame blocks; the rule reads layer colors down "
    "the bbox diagonal, dedups, reverses, and remaps the whole "
    "component. Blocks are square OR rectangular, even OR odd sized "
    "(single-cell center), with optionally REPEATED layer colors "
    "(dedup makes the swap asymmetric). (Was: square even-size blocks "
    "with all-distinct layers only.)"
)

# Rivals: 'reverse layers positionally' refuted by repeat_layer
# (dedup-then-reverse remaps colors, not rings). 'blocks are square'
# refuted by rect blocks (layer count from the MIN dimension).
# 'hollow frames survive' refuted by the single_layer degenerate
# (the diagonal reads interior ZEROS; frame-color swaps with 0 and
# the ring is ERASED). 3 demos incl. >=1 rect or odd block.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "blocks are SOLID nested frames (the bbox diagonal never hits 0 on main path)",
    "blocks never touch (8-connectivity merges adjacent blocks)",
    "layer colors distinct unless texture=repeat_layer",
]

DEGENERATE_TEXTURES = ("solid_block", "single_layer", "full_grid")
HELPFUL_TEXTURES = ("plain", "rect_block", "odd_block", "repeat_layer")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 14..20", "valid": "12..28"},
    "grid_w":   {"type": "int", "default": "rng 14..20", "valid": "12..28"},
    "n_blocks": {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "texture":  {"type": "str", "default": "rng helpful",
                 "valid": "plain|rect_block|odd_block|repeat_layer|"
                          "solid_block|single_layer|full_grid",
                 "doc": "rect_block: non-square nests; odd_block: 1-cell "
                        "center; repeat_layer: a color repeats so the "
                        "dedup-reverse map is asymmetric."},
}


def _draw_nested_rect(g, r0, c0, bh, bw, layers):
    """Nested frames in a bh x bw box; len(layers) = 1+(min-1)//2."""
    n = len(layers)
    for i, color in enumerate(layers):
        rr0, cc0 = r0 + i, c0 + i
        rr1, cc1 = r0 + bh - 1 - i, c0 + bw - 1 - i
        if i == n - 1:
            fill_box(g, rr0, cc0, rr1, cc1, color)
        else:
            draw_frame(g, rr0, cc0, rr1, cc1, color)


def _mirror(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = [row[:] for row in g]
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < h and 0 <= cc < w \
                                and not seen[rr][cc] and g[rr][cc] != 0:
                            seen[rr][cc] = True
                            stack.append((rr, cc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            n_layers = 1 + min(r2 - r1, c2 - c1) // 2
            layer_colors = [g[r1 + i][c1 + i] for i in range(n_layers)]
            uniq = list(dict.fromkeys(layer_colors))
            cmap = dict(zip(uniq, reversed(uniq)))
            for r, c in cells:
                out[r][c] = cmap.get(g[r][c], g[r][c])
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 non-bg cell (nested frame block exists)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    nz = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nz == 0:
        errs.append("no non-background cells: no nested frame blocks to reverse")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "rect_block", "odd_block",
                        "repeat_layer"))
    if difficulty == "easy":
        h_lo, h_hi = 12, 16
        nb_lo, nb_hi = 1, 1
        nl_lo, nl_hi = 2, 3
    elif difficulty == "hard":
        h_lo, h_hi = 18, 24
        nb_lo, nb_hi = 2, 3
        nl_lo, nl_hi = 3, 5
    else:
        h_lo, h_hi = 14, 20
        nb_lo, nb_hi = 1, 2
        nl_lo, nl_hi = 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    n_blocks = max(1, min(3, int(overrides.get(
        "n_blocks", ctx.draw_int("n_blocks", nb_lo, nb_hi)))))

    placed = 0
    for bi in range(n_blocks):
        n_layers = rng.randint(nl_lo, nl_hi)
        min_dim = 2 * n_layers - (1 if (texture == "odd_block" and bi == 0)
                                  else 0)
        if texture == "odd_block" and bi == 0 and min_dim % 2 == 0:
            min_dim += 1
        bh = bw = min_dim
        if texture == "rect_block" and bi == 0:
            if rng.random() < 0.5:
                bw = min_dim + rng.randint(2, 5)
            else:
                bh = min_dim + rng.randint(2, 5)
        if bh + 2 > h or bw + 2 > w:
            n_layers = max(2, min(h, w) // 2 - 2)
            bh = bw = 2 * n_layers
            if bh + 2 > h or bw + 2 > w:
                continue
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        rng.shuffle(pool)
        layers = pool[:n_layers]
        if texture == "repeat_layer" and bi == 0 and n_layers >= 3:
            layers[-1] = layers[0]  # innermost repeats the outermost
        footprint = [(r, c) for r in range(bh) for c in range(bw)]
        pos = place_no_overlap(rng, g, footprint, layers[0],
                               padding=1, max_tries=60)
        if pos is not None:
            _draw_nested_rect(g, pos[0], pos[1], bh, bw, layers)
            placed += 1
    if placed == 0:
        _draw_nested_rect(g, 1, 1, 6, 6, [3, 6, 8])
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    solid_block  — one color: dedup gives a single color, identity.
    single_layer — hollow frame: the bbox diagonal reads interior
                   ZEROS, so unique = [color, 0] and the swap ERASES
                   the ring (verified: 28 cells -> 0).
    full_grid    — one color everywhere: identity.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 13, 17)
    w = ctx.draw_int("grid_w", 13, 17)
    g = full_grid(h, w, 0)
    color = rng.randint(1, 9)
    if name == "solid_block":
        s = rng.randint(4, 7)
        r0 = rng.randint(1, h - s - 1)
        c0 = rng.randint(1, w - s - 1)
        fill_box(g, r0, c0, r0 + s - 1, c0 + s - 1, color)
        return g
    if name == "single_layer":
        s = rng.randint(5, 8)
        r0 = rng.randint(1, h - s - 1)
        c0 = rng.randint(1, w - s - 1)
        draw_frame(g, r0, c0, r0 + s - 1, c0 + s - 1, color)
        return g
    return full_grid(h, w, color)
