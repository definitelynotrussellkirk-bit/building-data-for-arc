"""Generator for arc_puzzle_bank_21_set11_s:S11_M5 — Mirror largest shape.

Rule: take the largest object. Normalize its cells. Mirror horizontally.
Output = (original ∪ mirror), cropped to bbox, painted in the largest
object's color.

Combinatorial axes (10): grid_h, grid_w, palette_kind, big_size,
n_small, palette_size, position_bias, n_distinct_colors, density,
texture.

Degenerates: no_shapes, equal_size, single_shape, symmetric_big.

Fairness:
  * Big-shape size is drawn uniformly from a difficulty-banded set so
    output bbox varies across demos — without this every output is
    `output_w × output_w` (1.1.0 emitted 20/20 outputs at 3×3).
  * The shape bank holds multiple asymmetric shapes per size; choice
    is uniform within the size.
  * Position is decorrelated from "largest": the big shape is placed
    in any of 4 half-grid regions or anywhere with clearance, so the
    model cannot use position as a "largest" shortcut.
  * Color pairs are drawn without replacement from the 8-color
    non-background palette (uniform).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c2996845ede0"
# 2.2.0: defect-lint all_background_output — a big shape whose mirror-union fills
# its bbox (e.g. a solid block) made the symmetrized output a featureless solid
# rect. The polyomino draw (and the curated fallback) now reject solid unions.
# (2.1.1: random asymmetric polyomino for output-shape variety.)
VERSION = "2.2.0"
TASK_ID = "c2996845ede0"
SUMMARY = (
    "0-bg grid (h~6-12, w~10-16) with: (a) ONE "
    "LARGE ASYMMETRIC OBJECT (4-8 cells) "
    "drawn from a hand-curated shape bank in "
    "some big_color; (b) 1-(big_size-2) "
    "ISOLATED SINGLETON CELLS as distractors "
    "in a different small_color. The big "
    "object is strictly larger than all "
    "singletons (size delta ≥2). The big "
    "object is horizontally ASYMMETRIC (so "
    "mirror differs from original). Objects "
    "are 4-conn isolated (no shared "
    "neighborhoods). Position bias varies "
    "(big_left/right/top/bottom_small or "
    "big_any). Rule: identify the LARGEST "
    "object (the big asymmetric one). "
    "NORMALIZE its cells. MIRROR HORIZONTALLY. "
    "COMPUTE the UNION (original cells ∪ "
    "mirrored cells). CROP to that union's "
    "BBOX. PAINT in the big object's color. "
    "Output: the cropped mirror-union subgrid. "
    "Singletons are discarded. Net: largest "
    "object gets symmetrized via horizontal "
    "mirror-union."
)

# Smallest demo count that lets the learner distinguish this rule from
# rivals: (a) copy largest (no mirror), (b) mirror smallest, (c)
# rotate largest, (d) emit a fixed-size shape. Each rival needs
# different signal:
#   - (a) refuted by any demo where mirror(big) != big.
#   - (b) refuted by ≥1 demo where smallest object exists and its
#     mirror differs from output.
#   - (c) refuted by ≥1 demo where rotate90(big) != mirror(big).
#   - (d) refuted by ≥2 demos whose outputs have different bboxes.
# With shape sizes varying in {4,5,6,7,8} and bboxes spanning 2×3 to
# 4×5, 4 demos are enough to cover all four refutations.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly 1 large asymmetric object (the target) + N isolated singleton cells",
    "the target is strictly larger than any other component (size delta >= 2)",
    "the target is horizontally asymmetric (so mirror union differs from target)",
    "no two objects share a 4-adjacent cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "equal_size", "single_shape", "symmetric_big")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":          {"type": "int", "default": "by difficulty", "valid": "5..14"},
    "grid_w":          {"type": "int", "default": "by difficulty", "valid": "8..18"},
    "palette_kind":    {"type": "str", "default": "rng helpful",
                        "valid": "|".join(PALETTE_KINDS)},
    "big_size":        {"type": "int", "default": "by difficulty", "valid": "4..8"},
    "n_small":         {"type": "int", "default": "rng 1..(big_size-2)",
                        "valid": "1..(big_size-2)"},
    "palette_size":    {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":   {"type": "str", "default": "rng",
                        "valid": "big_left_small_right|big_right_small_left|"
                                 "big_top_small_bottom|big_bottom_small_top|big_any"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":         {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":         {"type": "str", "default": "alias for palette_kind",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# Hand-curated asymmetric (under horizontal mirror) connected shapes,
# grouped by cell count. Each list is filtered at import to keep only
# the genuinely asymmetric entries — guards against typos.
_SHAPES_RAW = {
    4: [
        [(0, 0), (1, 0), (2, 0), (2, 1)],                    # J  3×2
        [(0, 1), (1, 1), (2, 0), (2, 1)],                    # L  3×2
        [(0, 1), (0, 2), (1, 0), (1, 1)],                    # S  2×3
        [(0, 0), (0, 1), (1, 1), (1, 2)],                    # Z  2×3
        [(0, 0), (0, 1), (0, 2), (1, 2)],                    # ⌐  2×3
    ],
    5: [
        [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],            # P  3×3
        [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],            # L  4×2
        [(0, 1), (1, 0), (1, 1), (2, 1), (3, 1)],            # Y  4×2
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],            # stair  3×3
        [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)],            # ⌐ wide 2×4
    ],
    6: [
        [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)],    # original [0]  3×3
        [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)],    # original [2]  3×3
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)],    # 6-stair       3×4
        [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)],    # L             4×3
        [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3)],    # T-rot         3×4
    ],
    7: [
        [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (3, 1)],   # 4×3
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 2), (3, 3)],   # 4×4 zigzag
        [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 4)],   # 3×5
    ],
    8: [
        [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3)],  # 4×4 spiral
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4)],  # 4×5 stair
        [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)],  # 4×3 hook
    ],
}


def _mirror_union_solid(cells):
    """True when shape UNION its horizontal mirror fills the union bbox — the
    rule's symmetrized output would be a featureless solid block."""
    norm = list(_normalize_cells(cells))
    maxc = max(c for _, c in norm)
    union = set(norm) | {(r, maxc - c) for r, c in norm}
    bh = max(r for r, _ in union) + 1
    bw = max(c for _, c in union) + 1
    return len(union) == bh * bw


def _rand_asym_poly(rng, k):
    """Random connected k-cell polyomino that is horizontally asymmetric and
    whose mirror-union is NOT a solid rectangle (defect-lint: solid outputs).
    Returns a normalized cell list, or None if none found."""
    for _ in range(60):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nb = (r + dr, c + dc)
            if nb not in seen:
                cells.append(nb)
                seen.add(nb)
        if _is_asym_lr(cells) and not _mirror_union_solid(cells):
            return list(_normalize_cells(cells))
    return None


def _normalize_cells(cells):
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return tuple(sorted((r - minr, c - minc) for r, c in cells))


def _is_asym_lr(cells):
    n = _normalize_cells(cells)
    maxc = max(c for _, c in n)
    m = tuple(sorted((r, maxc - c) for r, c in n))
    return n != m


SHAPES_BY_SIZE = {
    size: [shape for shape in shapes if _is_asym_lr(shape)]
    for size, shapes in _SHAPES_RAW.items()
}
assert all(len(v) >= 2 for v in SHAPES_BY_SIZE.values()), (
    f"need >=2 asymmetric shapes per size; got "
    f"{[(k, len(v)) for k, v in SHAPES_BY_SIZE.items()]}"
)


def _difficulty_sizes(difficulty):
    if difficulty == "easy":
        return (4, 5)
    if difficulty == "hard":
        return (6, 7, 8)
    return (5, 6, 7)


def _grid_bounds(difficulty):
    if difficulty == "easy":
        return 6, 8, 10, 12
    if difficulty == "hard":
        return 9, 12, 13, 16
    return 7, 10, 11, 14


def _adjacent_to_nonzero(g, r, c, h, w):
    for ar, ac in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + ar, c + ac
        if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
            return True
    return False


def _try_place(g, cells, color, rng, *, max_tries, region):
    """Place a normalized shape so that no cell is 4-adjacent to existing
    non-zero. region is (r_lo, r_hi, c_lo, c_hi) or None for whole grid."""
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if region is None:
        r_lo, r_hi, c_lo, c_hi = 0, h - sh, 0, w - sw
    else:
        r_lo, r_hi, c_lo, c_hi = region
        r_hi = min(r_hi, h - sh)
        c_hi = min(c_hi, w - sw)
    if r_hi < r_lo or c_hi < c_lo:
        return False
    for _ in range(max_tries):
        r0 = rng.randint(r_lo, r_hi)
        c0 = rng.randint(c_lo, c_hi)
        ok = True
        for dr, dc in cells:
            r, c = r0 + dr, c0 + dc
            if g[r][c] != 0 or _adjacent_to_nonzero(g, r, c, h, w):
                ok = False
                break
        if ok:
            for dr, dc in cells:
                g[r0 + dr][c0 + dc] = color
            return True
    return False


def _region_for_bias(bias, h, w, sh, sw):
    """Return (big_region, small_region) rectangles for the given bias.
    Each region is (r_lo, r_hi, c_lo, c_hi) inclusive, or None for
    'anywhere in grid'."""
    if bias == "big_left_small_right":
        return (0, h - sh, 0, max(0, w // 2 - sw)), (0, h - 1, w // 2 + 1, w - 1)
    if bias == "big_right_small_left":
        return (0, h - sh, w // 2 + 1, w - sw), (0, h - 1, 0, w // 2 - 1)
    if bias == "big_top_small_bottom":
        return (0, max(0, h // 2 - sh), 0, w - sw), (h // 2 + 1, h - 1, 0, w - 1)
    if bias == "big_bottom_small_top":
        return (h // 2 + 1, h - sh, 0, w - sw), (0, h // 2 - 1, 0, w - 1)
    return None, None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has multiple non-zero components of different sizes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-zero cells found")
        return errs
    # Find connected components
    visited = [[False] * w for _ in range(h)]
    components = []
    for r0, c0 in nonzero:
        if not visited[r0][c0]:
            comp = []
            stack = [(r0, c0)]
            visited[r0][c0] = True
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))
            components.append(comp)
    if len(components) < 2:
        errs.append(f"expected ≥2 components; found {len(components)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    h_lo, h_hi, w_lo, w_hi = _grid_bounds(difficulty)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")

    big_color, small_color = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)

    # Big-shape size and shape. v2.0.0 drew from a hand-curated bank of
    # ~3-5 shapes/size -> only ~7 distinct output bboxes (out_shapes=7).
    # Now generate a RANDOM connected horizontally-asymmetric polyomino of
    # big_size cells -> varied bboxes (incl. non-square) -> the mirror-union
    # output shape varies widely. Fall back to the curated bank on the rare
    # seed where no asymmetric poly is found.
    big_size = rng.choice(_difficulty_sizes(difficulty))
    shape = _rand_asym_poly(rng, big_size)
    if shape is None:
        bank = [s for s in SHAPES_BY_SIZE[big_size] if not _mirror_union_solid(s)] \
            or list(SHAPES_BY_SIZE[big_size])
        shape = list(rng.choice(bank))
        if rng.random() < 0.5:
            maxc = max(c for _, c in shape)
            shape = sorted((r, maxc - c) for r, c in shape)

    # Distractor: n_small isolated singleton cells. Capped so 'largest'
    # is unambiguous even if every singleton is its own component.
    n_small_hi = max(1, big_size - 2)
    n_small = rng.randint(1, n_small_hi)

    bias = rng.choice([
        "big_left_small_right", "big_right_small_left",
        "big_top_small_bottom", "big_bottom_small_top",
        "big_any",
    ])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    big_region, small_region = _region_for_bias(bias, h, w, sh, sw)

    if not _try_place(g, shape, big_color, rng, max_tries=60, region=big_region):
        # Region too tight for this seed → retry anywhere on the grid.
        if not _try_place(g, shape, big_color, rng, max_tries=80, region=None):
            # Last resort: top-left (kept for total-failure safety; the
            # rule still works, the bias is just lost for this sample).
            for dr, dc in shape:
                g[dr][dc] = big_color

    placed = 0
    for _ in range(80):
        if placed >= n_small:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if small_region is not None:
            r_lo, r_hi, c_lo, c_hi = small_region
            if not (r_lo <= r <= r_hi and c_lo <= c <= c_hi):
                continue
        if g[r][c] != 0 or _adjacent_to_nonzero(g, r, c, h, w):
            continue
        g[r][c] = small_color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    if name == "no_shapes":
        return g
    if name == "equal_size":
        # both shapes are 3-cell L's of different color — tie under "largest"
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][1 + dc] = 4
            g[3 + dr][7 + dc] = 6
        return g
    if name == "single_shape":
        for dr, dc in SHAPES_BY_SIZE[6][0]:
            g[1 + dr][1 + dc] = 4
        return g
    if name == "symmetric_big":
        # symmetric big shape → mirror(big) == big → output bbox == input
        # bbox, so the mirror operation is invisible. Pathological for
        # rule learning even though the rule is technically applied.
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)]:
            g[1 + dr][2 + dc] = 4
        g[5][8] = 6
        return g
    return g
