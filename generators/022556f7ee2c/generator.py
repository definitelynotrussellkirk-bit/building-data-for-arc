"""Generator for 13b:m87 — cast rays from emitters until wall.

Rule: each emitter cell (color 2) casts 4 cardinal rays (color 8)
that travel until they hit a wall cell (color 5) or the grid edge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_emitters, no_walls, emitter_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "022556f7ee2c"
VERSION = "2.1.1"
TASK_ID = "022556f7ee2c"
SUMMARY = (
    "0-bg grid with 2-3 red(2) emitters and 1-2 gray(5) wall "
    "segments. Rule: each emitter casts 4 cardinal cyan(8) rays over "
    "0-cells, stopping at ORIGINAL non-zero cells (walls, other "
    "emitters) or the edge — rays pass freely THROUGH other rays' "
    "painted cells (the stop test reads the input, not the output). "
    "Emitters and walls preserved."
)

# Rivals: 'rays block each other' refuted by crossing rays that both
# complete. 'rays always travel >=1 cell' refuted by wall-adjacent
# emitters whose ray paints nothing in that direction. 'rays pass
# emitters' refuted by aligned emitters whose rays stop between them.
# 3 demos incl. >=1 crossing and >=1 aligned or adjacent board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-3 color-2 emitter cells; 1-2 color-5 axis-aligned wall segments",
    "adjacent_wall boards: an emitter touches a wall (zero-length ray)",
    "aligned_emitters boards: two emitters share a row/col with a clear path",
]

DEGENERATE_TEXTURES = ("no_emitters", "no_walls", "emitter_at_corner")
HELPFUL_TEXTURES = ("plain", "adjacent_wall", "aligned_emitters")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 9..11 (hard 11..13)",
                "valid": "8..14", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 9..11 (hard 11..13)",
                "valid": "8..14", "doc": "Grid width."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|adjacent_wall|aligned_emitters|"
                         "no_emitters|no_walls|emitter_at_corner",
                "doc": "Edge-case flavor or a degenerate name."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "adjacent_wall", "aligned_emitters"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    n_walls = rng.randint(1, 2)
    for _ in range(n_walls):
        for _ in range(40):
            if rng.random() < 0.5:
                r = rng.randint(2, h - 3)
                c1 = rng.randint(1, w - 5)
                length = rng.randint(4, min(7, w - 1 - c1))
                cells = [(r, c) for c in range(c1, c1 + length)]
            else:
                c = rng.randint(2, w - 3)
                r1 = rng.randint(1, h - 5)
                length = rng.randint(4, min(7, h - 1 - r1))
                cells = [(r, c) for r in range(r1, r1 + length)]
            if any(p in used for p in cells): continue
            for r, c in cells: g[r][c] = 5
            used |= set(cells); break
    n_emitters = rng.randint(2, 3)
    emitters = []
    for i in range(n_emitters):
        for _ in range(60):
            if texture == "adjacent_wall" and i == 0 and used:
                # first emitter TOUCHES a wall: that direction's ray
                # has zero length (previously excluded by construction)
                wr, wc = sorted(used)[rng.randrange(len(used))]
                dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
                r, c = wr + dr, wc + dc
                if not (0 <= r < h and 0 <= c < w) or g[r][c] != 0:
                    continue
            elif texture == "aligned_emitters" and i == 1 and emitters:
                # share a row/col with the first emitter, clear between:
                # the ray stops AT the other emitter
                er, ec = emitters[0]
                if rng.random() < 0.5:
                    r, c = er, rng.randrange(w)
                    lo, hi = min(c, ec), max(c, ec)
                    if abs(c - ec) < 3 or any(g[er][x] != 0 for x in range(lo + 1, hi)):
                        continue
                else:
                    r, c = rng.randrange(h), ec
                    lo, hi = min(r, er), max(r, er)
                    if abs(r - er) < 3 or any(g[x][ec] != 0 for x in range(lo + 1, hi)):
                        continue
                if (r, c) in used:
                    continue
            else:
                r = rng.randint(0, h - 1)
                c = rng.randint(0, w - 1)
                if (r, c) in used:
                    continue
                if texture != "adjacent_wall" and any(
                        0 <= r + dr < h and 0 <= c + dc < w and g[r + dr][c + dc] == 5
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                    continue
            g[r][c] = 2
            used.add((r, c))
            emitters.append((r, c))
            break
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_emitters       — walls only: nothing radiates.
    no_walls          — rays always reach the edges.
    emitter_at_corner — only 2 of 4 rays have length.
    """
    h = ctx.draw_int("grid_h", 9, 11)
    w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_emitters":
        r = rng.randint(2, h - 3)
        c1 = rng.randint(1, w - 6)
        for c in range(c1, c1 + rng.randint(4, 5)):
            g[r][c] = 5
        return g
    if name == "no_walls":
        g[rng.randint(1, h - 2)][rng.randint(1, w - 2)] = 2
        return g
    # emitter_at_corner
    corner = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))[rng.randrange(4)]
    g[corner[0]][corner[1]] = 2
    r = rng.randint(2, h - 3)
    for c in range(2, 2 + rng.randint(4, 5)):
        if c < w:
            g[r][c] = 5
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: 2-3 color-2 emitter cells; >=1 color-5 wall cell."""
    msgs = []
    h, w = len(grid), len(grid[0])
    emitters = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    walls = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    if not (2 <= emitters <= 3):
        msgs.append(f"expected 2-3 color-2 emitter cells, got {emitters}")
    if walls < 1:
        msgs.append(f"expected >=1 color-5 wall cell, got {walls}")
    return msgs
