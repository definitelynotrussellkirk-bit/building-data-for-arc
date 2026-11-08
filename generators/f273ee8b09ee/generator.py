"""Generator for arc_additional_puzzle_bank_volume5:M32.

Rule: sort objects by (r1, c1); concat their bbox crops horizontally
with 1-col gaps. Output is max-h × total-w.

Combinatorial axes (8): grid_h/w, palette_kind, n_blobs, palette_size,
position_bias, n_distinct_colors, blob_size_variation, texture.
Degenerates: only_one_blob, all_same_size, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "f273ee8b09ee"
VERSION = "2.1.1"  # strengthen 8-isolation self_check + fix touching degenerate
TASK_ID = "f273ee8b09ee"
SUMMARY = (
    "0-bg grid (h×w, ~8-14 by ~11-16) with 3 connected "
    "BLOBS normally and 3-4 at hard difficulty, in distinct non-zero colors, varied shapes (2-4 cells "
    "each). Blobs 8-conn isolated. Rule: detect all components. "
    "Sort by bbox top-left (row asc, then col asc). For each "
    "blob, crop to its bbox. Horizontally concatenate the crops "
    "(left-to-right in sort order) with 1-col gaps. Output "
    "height = max(crop heights); width = sum(crop widths) + "
    "(n-1) gaps. Each blob's color preserved in its slot."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 3 connected blobs normally, or 3-4 in hard mode, in distinct non-zero colors",
    "blobs 8-conn isolated (≥1-cell buffer)",
    "blobs have varied bbox dimensions for visual interest",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("only_one_blob", "blobs_touching", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3 (hard rng 3..4)", "valid": "3..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "blob_size_variation": {"type": "str", "default": "varied",
                            "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
        n_blobs = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 16)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 15)
        n_blobs = 3
    rng = ctx.draw_rng("layout")
    from puzzle_generators.helpers.blobs import grow_blob

    palette = list(range(1, 10)); rng.shuffle(palette)
    palette = palette[:n_blobs]
    sizes = [rng.randint(2, 4) for _ in range(n_blobs)]

    for _outer in range(40):
        g = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        ok = True
        for size, color in zip(sizes, palette):
            cells = grow_blob(rng, h, w, used, size, max_attempts=40)
            if cells is None:
                ok = False; break
            for r, c in cells:
                g[r][c] = color
            for r, c in cells:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            used.add((nr, nc))
        if ok:
            return g
    raise ValueError("could not place 3 blobs")


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "only_one_blob":
        # only 1 blob — concat is trivially that blob's crop
        paint_at(g, 2, 2, [(0, 0), (1, 0), (1, 1)], 4)
        return g
    if name == "blobs_touching":
        # blobs touching each other — would merge into one component
        paint_at(g, 2, 2, [(0, 0), (1, 0)], 4)
        paint_at(g, 2, 3, [(0, 0), (0, 1)], 6)  # 8-adjacent to first blob
        paint_at(g, 6, 8, [(0, 0)], 7)
        return g
    if name == "no_blobs":
        # empty grid — no objects to crop and concat
        return g
    return g

def _self_components_8(g):
    h, w = len(g), len(g[0])
    seen = set(); comps = []
    dirs = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or g[r][c] == 0:
                continue
            color = g[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                x, y = stack.pop(); cells.append((x, y))
                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen and g[nx][ny] == color:
                        seen.add((nx, ny)); stack.append((nx, ny))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    comps = _self_components_8(grid)
    errs = []
    max_count = 4 if difficulty == "hard" else 3
    if not (3 <= len(comps) <= max_count):
        errs.append(f"expected 3-{max_count} isolated blobs, found {len(comps)}")
    if len({color for color, _ in comps}) != len(comps):
        errs.append("blob colors are not distinct")
    for color, cells in comps:
        if not (2 <= len(cells) <= 4):
            errs.append(f"blob {color} has size {len(cells)}, expected 2-4")
    for i, (color_a, cells_a) in enumerate(comps):
        for color_b, cells_b in comps[i + 1:]:
            if any(max(abs(ar - br), abs(ac - bc)) <= 1
                   for ar, ac in cells_a for br, bc in cells_b):
                errs.append(f"blobs {color_a} and {color_b} are not 8-isolated")
                return errs
    return errs
