"""Generator for arc_additional_puzzles_21_set12_bundle:H84 — ranked component with composed transforms.

Rule: row 0 cell 0 = k (1-indexed selector by area-desc / color-asc tiebreaker);
row 0 cells (w-2) and (w-1) = transform codes t1 and t2 (1=cw, 2=180, 3=flip-lr,
4=flip-ud). Sort components by (area desc, color asc), pick the k-th, crop, apply
t1 then t2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes (≥2 components share size → "k-th by area-desc"
falls back to color-asc tiebreaker, no clear cross-candidate contrast),
no_k (cell (0,0) is bg → rule's k-selector returns nothing, no
component chosen), identity_transforms (t1=t2=identity-like, e.g.,
both 4 = flip-ud-then-flip-ud = identity → rule's transform composition
is identity, output equals cropped target).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cc9cb1d8bea8"
VERSION = "2.1.0"
TASK_ID = "cc9cb1d8bea8"

SUMMARY = (
    "0-bg grid (h~11-13, w~12-14) "
    "with TOP-ROW anchor cells and "
    "3-4 BODY COMPONENTS: (a) cell "
    "(0, 0) = k (1-indexed selector "
    "in [1..n]); (b) cell (0, w-2) "
    "= t1 (transform code 1-4); (c) "
    "cell (0, w-1) = t2 (second "
    "transform code 1-4); (d) "
    "remaining row 0 = 0; (e) BODY "
    "(rows 1..h-1) has n (3-4) "
    "isolated 4-conn components, "
    "each in a DISTINCT color from "
    "{2..9} with STRICTLY DISTINCT "
    "SIZES from {2, 3, 4, 5, 6, "
    "7}. Rule (RANKED COMPONENT + "
    "COMPOSED TRANSFORM): SORT "
    "body components by (AREA "
    "DESC, COLOR ASC). PICK the "
    "k-th component in sorted "
    "order. CROP to its BBOX. "
    "APPLY transform t1 then t2 "
    "(transform codes: 1=rotate "
    "CW 90°, 2=rotate 180°, 3="
    "flip-LR, 4=flip-UD). Output: "
    "the transformed crop. Net: "
    "k picks ranked blob, t1∘t2 "
    "applies composed geometric "
    "transform."
)

INVARIANTS = [
    "background is 0",
    "(0, 0) holds k in [1..n_components], (0, w-2) and (0, w-1) hold transform codes 1..4",
    "the rest of row 0 is 0",
    "body has 3-4 isolated 4-conn components in distinct colors and distinct sizes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "no_k", "identity_transforms")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "n_components":      {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":     {"type": "str", "default": "k_t1_t2_plus_components",
                          "valid": "k_t1_t2_plus_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|tied_sizes|no_k|identity_transforms"},
}


_SHAPES_BY_SIZE = {
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (0, 1), (0, 2)], [(0, 0), (1, 0), (2, 0)], [(0, 0), (0, 1), (1, 0)]],
    4: [[(0, 0), (0, 1), (0, 2), (1, 1)], [(0, 0), (1, 0), (1, 1), (2, 1)], [(0, 0), (0, 1), (1, 0), (1, 1)]],
    5: [[(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)], [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)]],
    6: [[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]],
    7: [[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)]],
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _shape_mask(shape):
    r0 = min(r for r, _ in shape); c0 = min(c for _, c in shape)
    r1 = max(r for r, _ in shape); c1 = max(c for _, c in shape)
    cells = {(r - r0, c - c0) for r, c in shape}
    return tuple(tuple(1 if (r, c) in cells else 0 for c in range(c1 - c0 + 1))
                 for r in range(r1 - r0 + 1))


def _transform_mask(mask, code):
    if code == 1:      # rotate CW
        return tuple(tuple(mask[len(mask) - 1 - r][c] for r in range(len(mask)))
                     for c in range(len(mask[0])))
    if code == 2:      # rotate 180
        return tuple(tuple(reversed(row)) for row in reversed(mask))
    if code == 3:      # flip LR
        return tuple(tuple(reversed(row)) for row in mask)
    return tuple(reversed(mask))  # flip UD


def _visible_transform_pairs(shape):
    """Pairs whose composed transform visibly changes this normalized shape."""
    mask = _shape_mask(shape)
    out = []
    for t1 in range(1, 5):
        for t2 in range(1, 5):
            if _transform_mask(_transform_mask(mask, t1), t2) != mask:
                out.append((t1, t2))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 12, 12)
        n = ctx.draw_int("n_components", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 13)
        w = ctx.draw_int("grid_w", 14, 14)
        n = ctx.draw_int("n_components", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_components", 3, 4)
    rng = ctx.draw_rng("layout")

    sizes = rng.sample([2, 3, 4, 5, 6, 7], n)
    sizes.sort(reverse=True)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
    k = rng.randint(1, n)

    for outer in range(40):
        g = full_grid(h, w, 0)
        shapes = [rng.choice(_SHAPES_BY_SIZE[sz]) for sz in sizes]
        visible_pairs = _visible_transform_pairs(shapes[k - 1])
        if not visible_pairs:
            continue
        t1, t2 = rng.choice(visible_pairs)
        g[0][0] = k
        g[0][w - 2] = t1
        g[0][w - 1] = t2
        ok = True
        for shape, color in zip(shapes, colors):
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(1, h - sh)
                c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place {0} distinct-area components".format(n))


from puzzle_generators.helpers.selfcheck import components as _components


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0])
    k = grid[0][0]
    t1 = grid[0][w - 2]
    t2 = grid[0][w - 1]
    if not (1 <= k <= 4):
        msgs.append("top-left selector k must be in range")
    if t1 not in {1, 2, 3, 4} or t2 not in {1, 2, 3, 4}:
        msgs.append("transform codes must be in 1..4")
    if any(grid[0][c] != 0 for c in range(w) if c not in {0, w - 2, w - 1}):
        msgs.append("non-control cells in row 0 must be background")
    clean = [row[:] for row in grid]
    clean[0][0] = clean[0][w - 2] = clean[0][w - 1] = 0
    comps = _components(clean)
    if not (3 <= len(comps) <= 4):
        msgs.append("body must contain 3-4 components")
    sizes = [len(comp["cells"]) for comp in comps]
    colors = [comp["color"] for comp in comps]
    if len(set(sizes)) != len(sizes):
        msgs.append("component sizes must be strictly distinct")
    if len(set(colors)) != len(colors):
        msgs.append("component colors must be distinct")
    ordered = sorted(comps, key=lambda comp: (-len(comp["cells"]), comp["color"]))
    if 1 <= k <= len(ordered):
        target = ordered[k - 1]
        mask = _shape_mask(target["cells"])
        if _transform_mask(_transform_mask(mask, t1), t2) == mask:
            msgs.append("selected component's composed transform must be visible")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # Two components share the same size — area-desc rank breaks
        # to color-asc tiebreaker; no clear cross-candidate contrast.
        g[0][0] = 1
        g[0][w - 2] = 1
        g[0][w - 1] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][1 + dc] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][5 + dc] = 4   # tied size with prev
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]:
            g[8 + dr][3 + dc] = 6
        return g
    if name == "no_k":
        # (0,0) is bg — rule's k-selector returns nothing.
        g[0][w - 2] = 1
        g[0][w - 1] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][1 + dc] = 3
        for dr, dc in [(0, 0), (1, 0), (2, 0)]:
            g[5 + dr][5 + dc] = 4
        return g
    if name == "identity_transforms":
        # Both transforms cancel (4=flip-ud applied twice = identity);
        # rule's composed transform is identity.
        g[0][0] = 1
        g[0][w - 2] = 4
        g[0][w - 1] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][2 + dc] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[7 + dr][5 + dc] = 4
        return g
    return g
