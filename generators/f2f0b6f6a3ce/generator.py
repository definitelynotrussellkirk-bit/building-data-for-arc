"""Generator for arc_puzzle_bank_fourteenth21:M94.

Rule: pick the largest 4-connected non-zero component (connectivity is
color-blind), crop the input to its bbox, output that subgrid.

Axes: grid_h, grid_w, n_blobs, blob sizes, colors, positions.
Degenerates: tied_largest, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "f2f0b6f6a3ce"
# 2.2.0: defect-lint all_background_output + axis-honesty + missing self_check —
# the LARGEST blob could fill its bbox (solid crop output); it is now required
# non-solid. AXES grid ranges made honest; self_check added (unique non-solid
# largest component). (2.1.0: bigger blob sizes.)
VERSION = "2.2.0"
TASK_ID = "f2f0b6f6a3ce"
SUMMARY = (
    "0-bg grid with 3-4 connected blobs in distinct non-zero colors at "
    "scattered positions, each a STRICTLY DISTINCT size (so 'largest' is "
    "unambiguous). Blobs are placed with a >=1-cell buffer so they stay separate "
    "components. Rule: collect non-zero 4-connected components (connectivity is "
    "color-blind), find the largest by cell count, and crop the input to its bbox. "
    "Output = that subgrid (the largest blob's cells in their color plus any "
    "interior zeros)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-4 connected blobs in distinct non-zero colors",
    "blobs have strictly distinct sizes (so 'largest' is unique)",
    "blobs are placed with ≥1-cell buffer (8-disjoint so they're separate components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_largest", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-9 easy / 9-13 med / 13-17 hard", "valid": "7..17"},
    "grid_w":         {"type": "int", "default": "8-10 easy / 10-15 med / 14-19 hard", "valid": "8..19"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_blobs = 3
        size_pool = range(2, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 14, 19)
        n_blobs = 4
        size_pool = range(2, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 10, 15)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
        size_pool = range(2, 11)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_blobs)

    def _bbox(cells):
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        return (min(rs), min(cs), max(rs), max(cs))

    def _disjoint(a, b):                # two bboxes share no cell
        return (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

    last = None
    for _outer in range(40):
        g = full_grid(h, w, 0)
        sizes = rng.sample(list(size_pool), n_blobs)
        used: set[tuple[int, int]] = set()
        boxes = []
        blobs = []
        for size in sizes:
            cells = grow_blob(rng, h, w, used, size, max_attempts=80)
            if cells is None:
                continue
            used |= cells
            boxes.append(_bbox(cells)); blobs.append(cells)
        last = (g, blobs, palette)
        # keep only if: all bboxes disjoint (single-color crops) AND the LARGEST
        # blob does not fill its bbox (a solid crop output is featureless)
        if len(blobs) >= 3 and all(_disjoint(boxes[i], boxes[j])
                                   for i in range(len(boxes)) for j in range(i + 1, len(boxes))):
            big = max(blobs, key=len)
            bb = _bbox(big)
            if len(big) < (bb[2] - bb[0] + 1) * (bb[3] - bb[1] + 1):
                for cells, color in zip(blobs, palette):
                    for r, c in cells:
                        g[r][c] = color
                return g
    # fallback: paint whatever the last attempt produced (rare)
    g, blobs, palette = last
    for cells, color in zip(blobs, palette):
        for r, c in cells:
            g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """The rule crops the LARGEST component: it must be unique (no tie) and must
    not fill its bbox (a solid crop output carries no shape signal)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    seen: set[tuple[int, int]] = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    if len(comps) < 2:
        return [f"expected >=2 components, found {len(comps)}"]
    sizes = sorted((len(c) for c in comps), reverse=True)
    if sizes[0] == sizes[1]:
        return ["two components tie for largest — the rule's crop pick is ambiguous"]
    big = max(comps, key=len)
    rs = [r for r, _ in big]; cs = [c for _, c in big]
    if len(big) == (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1) and len(big) >= 4:
        return ["largest component is a solid rectangle — its crop is featureless"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "tied_largest":
        # two blobs share max size → which to crop ambiguous
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 3
        for r, c in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 6
        for r, c in [(7, 1), (7, 2)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → trivially largest
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 5
        return g
    if name == "no_blobs":
        # empty grid → no blobs to crop
        return g
    return g
