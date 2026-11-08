"""Generator for arc_puzzle_bank_21_set15_bundle:hard_o04 — sketch + prototypes slot-pack.

Rule: a small cluster of single-cell markers in distinct colors forms a
'sketch'. For each color used in the sketch, a multi-cell prototype motif of
that color exists elsewhere in the grid. The output is a slot-grid where
each single's position selects the matching prototype.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_sketch (no top-left sketch markers → rule's slot-grid
has no positions), no_prototypes (sketch present but no multi-cell
prototypes for sketch colors → rule's selector finds no prototypes),
sketch_color_no_proto (a sketch color has no prototype → rule's
selector returns nothing for that slot).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f0b1cb87615"
VERSION = "1.1.1"
TASK_ID = "2f0b1cb87615"

SUMMARY = "Top-left sketch of single cells (2-3 colors) + matching multi-cell prototypes elsewhere."

INVARIANTS = [
    "background is 0",
    "2-3 colors used in the sketch (top-left region) as single-cell markers",
    "each sketch color has exactly one multi-cell prototype (size ≥ 2) elsewhere",
    "no other non-bg cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_sketch", "no_prototypes", "sketch_color_no_proto")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 12..14", "valid": "10..16"},
    "n_colors":          {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":     {"type": "str", "default": "sketch_plus_prototypes",
                          "valid": "sketch_plus_prototypes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Sketch region (rows 0-1, cols 0-2) has ≥1 single-cell marker; ≥1 multi-cell prototype elsewhere."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Sketch markers: single non-zero cells in rows 0-1, cols 0-2
    sketch_colors = set()
    for r in range(min(2, h)):
        for c in range(min(3, w)):
            if grid[r][c] != 0:
                sketch_colors.add(grid[r][c])
    if not sketch_colors:
        errs.append("no sketch markers found in rows 0-1, cols 0-2")
    # At least one multi-cell component outside sketch region
    visited = [[False] * w for _ in range(h)]
    has_prototype = False
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] != 0 and not (r < 2 and c < 3):
                # BFS to find component
                comp = []
                stack = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= h or cc < 0 or cc >= w:
                        continue
                    if visited[cr][cc] or grid[cr][cc] != grid[r][c]:
                        continue
                    visited[cr][cc] = True
                    comp.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((cr + dr, cc + dc))
                if len(comp) >= 2:
                    has_prototype = True
    if not has_prototype:
        errs.append("no multi-cell prototype (size >=2) found outside sketch region")
    return errs


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
        w = ctx.draw_int("grid_w", 12, 12)
        n_colors = ctx.draw_int("n_colors", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 14, 14)
        n_colors = ctx.draw_int("n_colors", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
        n_colors = ctx.draw_int("n_colors", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7], n_colors)
        sketch_cells = []
        n_sketch = rng.randint(max(n_colors, 2), n_colors + 1)
        used_color = {c: False for c in colors}
        for _ in range(n_sketch):
            for _t in range(40):
                r = rng.randint(0, 1); c = rng.randint(0, 2)
                if g[r][c] != 0: continue
                color = rng.choice(colors)
                g[r][c] = color
                used_color[color] = True
                sketch_cells.append((r, c, color))
                break
        for color in colors:
            if not used_color[color]:
                for _t in range(40):
                    r = rng.randint(0, 1); c = rng.randint(0, 2)
                    if g[r][c] != 0: continue
                    g[r][c] = color
                    used_color[color] = True
                    break
                else:
                    pass
        if not all(used_color.values()):
            continue
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(2, 4))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(4, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize set15 o04 layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_sketch":
        # No top-left sketch markers — rule's slot-grid is empty.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][3 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[7 + dr][8 + dc] = 6
        return g
    if name == "no_prototypes":
        # Sketch present but no multi-cell prototypes.
        g[0][0] = 4
        g[1][1] = 6
        return g
    if name == "sketch_color_no_proto":
        # Sketch has color 4 with no color-4 prototype (only color-6 has a proto).
        g[0][0] = 4
        g[1][2] = 6
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[7 + dr][8 + dc] = 6   # only color-6 prototype, color-4 has none
        return g
    return g
