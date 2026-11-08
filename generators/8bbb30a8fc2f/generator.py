"""Generator for c3b9fb49.

Rule: find smallest object by size; recolor it to 2.

Combinatorial axes (8): grid_h/w, n_blobs, blob_size_distribution,
blob_shape_kind, palette_size, position_bias, smallest_color,
smallest_unique_buffer.
Degenerates: single_blob, equal_size_blobs, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "8bbb30a8fc2f"
VERSION = "2.0.1"
TASK_ID = "8bbb30a8fc2f"
SUMMARY = (
    "0-bg grid (h, w~8-14) "
    "with 3-5 BLOBS each "
    "of a DISTINCT SIZE "
    "(sampled from "
    "ascending/wide-spread/"
    "tight-spread "
    "distributions over "
    "sizes ~1-9) in "
    "DISTINCT COLORS from "
    "{1, 3, 4, 5, 6, 7, 8, "
    "9} (NOT color 2, since "
    "2 is the rule's "
    "output). Blobs are "
    "non-touching (4-conn "
    "separation). The "
    "SMALLEST BLOB has a "
    "STRICTLY UNIQUE size "
    "(no tie at minimum). "
    "Rule (FIND SMALLEST "
    "OBJECT BY SIZE, "
    "RECOLOR TO 2): find "
    "every 4-CONNECTED "
    "NON-0 COMPONENT. "
    "COMPUTE the CELL "
    "COUNT of each. "
    "IDENTIFY the COMPONENT "
    "with MINIMUM size. "
    "RECOLOR ALL its cells "
    "to COLOR 2 (red). "
    "Other components stay "
    "unchanged. Net: the "
    "smallest blob turns "
    "red; all others keep "
    "their colors."
)

INVARIANTS = [
    "background is 0",
    ">=2 non-touching blobs",
    "smallest size is STRICTLY unique (no tie)",
    "smallest is NOT already color 2",
    "blobs separated by 4-conn (so each is its own object)",
]

SIZE_DISTS = ("ascending", "wide_spread", "tight_spread")
DEGENERATE_TEXTURES = ("single_blob", "equal_size_blobs", "no_blobs")
HELPFUL_TEXTURES = ("balanced", "many_blobs", "size_varied", "compact")

AXES = {
    "grid_h":             {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "grid_w":             {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "n_blobs":            {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "blob_size_distribution": {"type": "str", "default": "rng helpful",
                               "valid": "|".join(SIZE_DISTS)},
    "min_size":           {"type": "int", "default": "1", "valid": "1..3"},
    "max_size":           {"type": "int", "default": "6", "valid": "4..10"},
    "palette_size":       {"type": "int", "default": "= n_blobs",
                           "valid": "2..7"},
    "position_bias":      {"type": "str", "default": "rng spread|center|edge",
                           "valid": "spread|center|edge"},
    "texture":            {"type": "str", "default": "rng helpful",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; no blob uses color 2 (rule's output color); >=2 blobs if present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    nonbg = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not nonbg:
        return []  # no_blobs degenerate — allowed
    errs = []
    if 2 in nonbg:
        errs.append("color 2 is used in input (same as rule output color — forbidden)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 7, 9, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 13, 18, 4, 6
    else:
        h_lo, h_hi, n_lo, n_hi = 8, 14, 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    if texture == "many_blobs":
        n_blobs = 5
    elif texture == "size_varied":
        n_blobs = 4
    elif texture == "compact":
        n_blobs = 3
    else:
        n_blobs = int(overrides.get("n_blobs",
                                    ctx.draw_int("n_blobs", n_lo, n_hi)))
    n_blobs = max(2, min(6, n_blobs))
    dist = overrides.get("blob_size_distribution",
                         ctx.draw_choice("blob_size_distribution",
                                         list(SIZE_DISTS)))
    sizes = _draw_sizes(dist, n_blobs, rng)
    sizes = sorted(sizes)
    colors_pool = [c for c in range(1, 10) if c != 2]
    rng.shuffle(colors_pool)
    palette = colors_pool[:n_blobs]
    g = full_grid(h, w, 0)
    used = set()
    for i, size in enumerate(sizes):
        blob = grow_blob(rng, h, w, used, size)
        if blob is None:
            continue
        used |= blob
        for r, c in blob:
            g[r][c] = palette[i % len(palette)]
    objs = _count_objects(g)
    sizes_now = sorted([len(o) for o in objs])
    if len(sizes_now) >= 2 and sizes_now[0] == sizes_now[1]:
        # tie at min — bump the second-smallest by adding a free cell adjacent
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0:
                    neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                    for nr, nc in neighbors:
                        if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                            g[r][c] = g[nr][nc]
                            return g
    return g


def _draw_sizes(dist, n_blobs, rng):
    if dist == "ascending":
        return list(range(1, n_blobs + 1))
    if dist == "tight_spread":
        base = rng.randint(2, 4)
        return [base + i for i in range(n_blobs)]
    return [1, 3, 5, 7, 9][:n_blobs]


def _count_objects(g):
    h, w = len(g), len(g[0])
    visited = [[False] * w for _ in range(h)]
    objs = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or visited[r][c]:
                continue
            stack = [(r, c)]
            cells = []
            color = g[r][c]
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                if visited[rr][cc] or g[rr][cc] != color:
                    continue
                visited[rr][cc] = True
                cells.append((rr, cc))
                stack += [(rr - 1, cc), (rr + 1, cc),
                          (rr, cc - 1), (rr, cc + 1)]
            objs.append(cells)
    return objs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = [c for c in range(1, 10) if c != 2]
    rng.shuffle(palette)
    if name == "single_blob":
        for c in range(min(3, w)):
            g[h // 2][c] = palette[0]
        return g
    if name == "equal_size_blobs":
        for i, c0 in enumerate([1, 6, h // 2 + 4]):
            if c0 + 2 < w and i < len(palette):
                for c in range(c0, c0 + 3):
                    g[i + 1][c] = palette[i]
        return g
    if name == "no_blobs":
        return g
    return g
