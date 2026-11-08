"""Generator for arc_additional_puzzles_21_set11_bundle:H77 — hole-count packing.

Rule: each 4-connected nonzero component is cropped to its bbox; the
hole-count is the number of enclosed zero regions inside the crop
(4-connected zero regions that do not touch the crop border). Components
are sorted by (hole_count asc, reading-order index asc) and the crops are
packed left-to-right with one blank column between consecutive crops.

Combinatorial axes (5): grid_h, grid_w, n_components, palette_kind,
texture.  Degenerates: single_component (pack of one crop), all_solid
(every component 0 holes -> primary key collapses to reading order).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "deeb1eaf6197"
RULE_HASH = "a6de82106b47"  # canonical rule this generator was verified against
VERSION = "3.0.0"  # honest axes (dropped vacuous palette_size/position_bias/n_distinct_colors/density), live palette_kind pools, exact-dimension degenerates+fallback, structural self_check, RULE_HASH pin, rule-source resync.
TASK_ID = "deeb1eaf6197"

SUMMARY = (
    "0-bg grid (h 10..19, w 12..22) with 2-4 4-connected same-color "
    "components, each a distinct color (different-colored components "
    "may touch edge-to-edge, as in canonical train pair 2; their "
    "bboxes never overlap). Each component is one of: solid rect "
    "(0 holes), open/notched rect (0 holes but zeros inside the crop "
    "touch the crop border), ring (1 enclosed hole), or double-ring "
    "(2 enclosed holes). Rule: crop each component to its bbox, count "
    "ENCLOSED interior 0-regions, sort by (hole_count asc, "
    "reading-order index asc), and pack the crops LEFT-TO-RIGHT with "
    "one blank column between consecutive crops. Output height = max "
    "crop height; width = sum of crop widths + (n-1) gap columns."
)

# Rivals: 'pack in input position order' refuted by draws where hole-count
# reordering applies. 'pack vertically' refuted by horizontal packing.
# 'count border-touching crop zeros as holes' refuted by open/notched
# 0-hole components. 'output entire grid' refuted (output is small packed
# crops). Canonical pairs always show 3 components with distinct hole
# counts {0,1,2}; generated ties witness the reading-order tie-break.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "1-4 4-connected same-color components, colors distinct per component",
    "different-colored components may touch (canonical train pair 2 does)",
    "components span 0, 1, and 2 enclosed-hole shape families",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTE_POOLS = {
    "default": (1, 2, 3, 4, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 8),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}
DEGENERATE_TEXTURES = ("single_component", "all_solid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":       {"type": "int", "default": "rng 10..19 (band-skewed)",
                     "valid": "10..19"},
    "grid_w":       {"type": "int", "default": "rng 12..22 (band-skewed)",
                     "valid": "12..22"},
    "n_components": {"type": "int", "default": "rng 2..4 (band-skewed)",
                     "valid": "2..4"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "texture":      {"type": "str", "default": "alias for palette_kind",
                     "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    """Placement gate: inside the grid and no overlap with placed cells.

    Adjacency is allowed on purpose: objects are per-color 4-connected
    components (verified against the prelude), and canonical train pair 2
    shows two different-colored components touching edge-to-edge."""
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if g[r][c] != 0: return False
    return True


def _solid(rng, color):
    sh, sw = rng.choice([(2, 2), (2, 3), (3, 2)])
    return [(r, c, color) for r in range(sh) for c in range(sw)], sh, sw


def _open(rng, color):
    """0-hole shapes whose crop contains zeros touching the crop border —
    the disambiguating witness against 'count any interior crop zero'."""
    variant = rng.choice(("l3", "l4", "u5", "u5v", "notch"))
    if variant == "l3":      # 2x2 minus a corner (canonical 77/70)
        sh, sw = 2, 2
        cells = [(0, 0), (1, 0), (1, 1)]
    elif variant == "l4":    # 2x3 with one arm (canonical 444/400)
        sh, sw = 2, 3
        cells = [(0, 0), (0, 1), (0, 2), (1, 0)]
    elif variant == "u5":    # 2x3 U opening up
        sh, sw = 2, 3
        cells = [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)]
    elif variant == "u5v":   # 3x2 U opening right
        sh, sw = 3, 2
        cells = [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)]
    else:                    # 3x3 ring with a notch: almost a ring, 0 holes
        sh, sw = 3, 3
        cells = [(r, c) for r in range(3) for c in range(3)
                 if (r in (0, 2) or c in (0, 2)) and (r, c) != (0, 1)]
    if rng.random() < 0.5:   # horizontal flip for orientation variety
        cells = [(r, sw - 1 - c) for r, c in cells]
    return [(r, c, color) for r, c in cells], sh, sw


def _ring(rng, color):
    sh, sw = rng.choice([(3, 3), (3, 4), (4, 3), (4, 4)])
    cells = []
    for r in range(sh):
        for c in range(sw):
            if r in (0, sh - 1) or c in (0, sw - 1):
                cells.append((r, c, color))
    return cells, sh, sw


def _double_ring(rng, color):
    sh, sw = rng.choice([(3, 5), (3, 6), (5, 5)])
    cells = []
    if sw == 5 and sh == 3:
        holes = {(1, 1), (1, 3)}
    elif sw == 6:
        holes = {(1, 1), (1, 4)}
    else:
        holes = set()  # 5x5: perimeter + middle column (canonical pattern)
    for r in range(sh):
        for c in range(sw):
            if sh == 5:
                if r in (0, sh - 1) or c in (0, sw - 1) or c == 2:
                    cells.append((r, c, color))
            else:
                is_perim = (r in (0, sh - 1) or c in (0, sw - 1))
                middle = (r == 1 and 0 < c < sw - 1)
                if is_perim or (middle and (r, c) not in holes):
                    cells.append((r, c, color))
    return cells, sh, sw


_BUILDERS = (_solid, _open, _ring, _double_ring)


def _draw_colors(ctx, pool, n):
    exclude = set(range(10)) - set(pool)
    return ctx.draw_distinct_colors("colors", n=n, exclude=exclude)


def _place_components(g, builders, colors, rng, tries=80):
    h, w = len(g), len(g[0])
    for builder, color in zip(builders, colors):
        cells, sh, sw = builder(rng, color)
        placed = False
        for _ in range(tries):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
            for dr, dc, cc in cells:
                g[r0 + dr][c0 + dc] = cc
            placed = True
            break
        if not placed:
            return False
    return True


def _fallback(h, w, colors, rng):
    """Guaranteed-valid exact-size board: one 2x2 solid per requested color
    spread over corner slots (always fits the 10x12 minimum)."""
    g = full_grid(h, w, 0)
    slots = [(1, 1), (1, w - 3), (h - 3, 1), (h - 3, w - 3)]
    for color, (r0, c0) in zip(colors, slots):
        for dr in range(2):
            for dc in range(2):
                g[r0 + dr][c0 + dc] = color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    # Dimensions are drawn on the FULL declared range in every band so any
    # globally-valid override is honored on every band (difficulty only
    # skews the sampling distribution).
    h = ctx.draw_int_diff("grid_h", 10, 19)
    w = ctx.draw_int_diff("grid_w", 12, 22)
    texture = overrides.get("texture")
    kind = _palette_kind(overrides, ctx, texture)
    pool = PALETTE_POOLS[kind]
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, h, w, pool, overrides, ctx, rng)
    n_components = ctx.draw_int_diff("n_components", 2, 4)
    colors = _draw_colors(ctx, pool, n_components)

    for _outer in range(40):
        g = full_grid(h, w, 0)
        # with replacement: hole-count ties exercise the reading-order tie-break
        builders = [rng.choice(_BUILDERS) for _ in range(n_components)]
        if _place_components(g, builders, colors, rng):
            return g
    # exact-size, exact-count fallback (never grows/truncates the request)
    return _fallback(h, w, colors, rng)


def _palette_kind(overrides, ctx, texture):
    """Resolve the palette pool, honoring texture-as-alias and palette_kind.

    A palette-kind texture and an explicit palette_kind must agree when both
    are supplied; conflicting combinations are rejected explicitly."""
    tex_kind = texture if texture in PALETTE_KINDS else None
    pk = overrides.get("palette_kind")
    if tex_kind and pk and tex_kind != pk:
        raise ValueError(
            f"texture {tex_kind!r} conflicts with palette_kind {pk!r}")
    if tex_kind:
        return tex_kind
    return ctx.draw_choice("palette_kind", list(PALETTE_KINDS))


def _draw_from_degenerate(name, h, w, pool, overrides, ctx, rng):
    """Rule-valid edge cases on the exact requested canvas.

    single_component — one ring; the pack is just its crop. palette_kind
        selects the color pool; n_components is contradictory and rejected.
    all_solid        — n_components solids (2..4 honored); the hole-count
        key collapses to reading order.
    """
    g = full_grid(h, w, 0)
    if name == "single_component":
        if overrides.get("n_components") is not None:
            raise ValueError(
                "n_components conflicts with texture='single_component' "
                "(exactly one component by definition)")
        cells, sh, sw = _ring(rng, rng.choice(list(pool)))
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        for dr, dc, cc in cells:
            g[r0 + dr][c0 + dc] = cc
        return g
    if name == "all_solid":
        n = ctx.draw_int_diff("n_components", 2, 4)
        colors = _draw_colors(ctx, pool, n)
        for _attempt in range(40):
            g = full_grid(h, w, 0)
            if _place_components(g, [_solid] * n, colors, rng):
                return g
        return _fallback(h, w, colors, rng)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of the declared distribution.

    0-bg rectangular grid inside the declared 10..19 x 12..22 envelope;
    1-4 4-connected same-color components with distinct colors (touching
    different-colored components are allowed, per canonical train pair 2).
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular with nonzero width"]
    errors = []
    if not (10 <= h <= 19 and 12 <= w <= 22):
        errors.append(f"dims {h}x{w} outside declared envelope 10..19 x 12..22")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errors.append("colors must be ints in 0..9")
    if not any(v == 0 for v in flat):
        errors.append("no background 0 cells")
    # 4-connected same-color components over background 0
    seen = [[False] * w for _ in range(h)]
    colors = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0 or seen[r][c]:
                continue
            colors.append(v)
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == v):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
    if not colors:
        errors.append("no components found (empty inputs crash the oracle)")
    if len(colors) > 4:
        errors.append(f"{len(colors)} components exceeds declared max 4")
    if len(set(colors)) != len(colors):
        errors.append("component colors are not distinct")
    return errors
