"""Generator for fcabbbbdfc11 (bank 64addfdad75c task M149, "Assemble Components by Legend Order").

Rule (canonical, color-generic): row 0 is an ordering legend -- its non-zero
cells, read left-to-right, list distinct colors. Rows 2..h-1 (row 1 is an
empty separator) hold small 4-connected polyomino pieces. For each legend
color, take the LAST piece of that color (latest in reading order, i.e.
bottom-most then right-most), crop it to its bounding box (keeping internal
zeros), and pack the crops horizontally in legend order with 1-column zero
gaps, top-aligned, painting only non-zero cells. Output dims:
max(piece bbox heights) x (sum of bbox widths + n-1). Duplicate-color pieces
make "last" beat "first"; pieces of non-legend colors are ignored.

Canonical demos are tiny: 5-6 rows x 14-16 cols, 3 legend colors, pieces of
1-5 cells (L/Z/S/U polyominoes, singletons, one 1x2 domino -- never a solid
rectangle larger than 1x2), legend cells at columns 1,3,5 with the legend
order ALWAYS different from the below reading order, and same-color
duplicates witnessing the "last" selection. The generator reproduces that
envelope with a linked role/reading-order prior and extends it (more colors,
duplicates, distractors, palettes) along declared axes.

Combinatorial axes: grid_h, grid_w, n_colors, n_duplicates, n_distractors,
palette_kind, texture.
Branches witnessed: legend order != below order (always, when >=2 colors),
duplicate-color "last" selection, non-legend distractor ignored, singleton
pieces, polyomino crops with internal zeros, palette variation.
Degenerates: one_color, no_extras, all_singletons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fcabbbbdfc11"
VERSION = "3.4.0"
TASK_ID = "fcabbbbdfc11"
RULE_HASH = "e6db69a05de7"

# Exact official linked profiles live in _LINKED_PROFILES below.  They retain
# each component's legend-role index, below-grid reading order, and D4 shape
# class, so duplicate-color "last" selection and final packing order remain
# answer-bearing facts rather than an unordered morphology multiset.
FAMILY_SHAPES = {
    # Exactly the observed normalized piece forms (extracted executably from
    # the five official inputs; orientation variants of the same piece are
    # kept as separate representatives for diversity). Nothing else: an
    # unobserved shape in the bank is a fabricated canonical claim.
    1: [[(0, 0)]],
    2: [[(0, 0), (0, 1)]],
    3: [[(0, 0), (0, 1), (1, 0)],   # L3 (canonical orientations)
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 1), (1, 0), (1, 1)]],
    4: [[(0, 0), (0, 1), (1, 1), (1, 2)],   # S4
        [(0, 0), (0, 1), (0, 2), (1, 0)],   # L4
        [(0, 0), (1, 0), (1, 1), (2, 1)]],  # J4
    5: [[(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],   # U5
        [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)]],  # Z5
}

# (h, w, ordered below components), where a component is
# (legend_role, normalized cells).  Legend roles 0,1,2 are output order.
_LINKED_PROFILES = (
    (5, 14, (
        (1, ((0, 0), (0, 1), (1, 0))),
        (0, ((0, 0), (0, 1), (1, 1), (1, 2))),
        (2, ((0, 0), (1, 0), (1, 1))),
    )),
    (5, 15, (
        (2, ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))),
        (1, ((0, 0), (0, 1), (1, 1))),
        (0, ((0, 0), (1, 0), (1, 1))),
    )),
    (6, 16, (
        (2, ((0, 0), (0, 1), (1, 0))),
        (0, ((0, 0), (0, 1), (0, 2), (1, 0))),
        (2, ((0, 0),)),
        (1, ((0, 0), (1, 0), (1, 1), (2, 1))),
    )),
    (6, 15, (
        (1, ((0, 0), (1, 0), (1, 1))),
        (0, ((0, 0),)),
        (0, ((0, 0),)),
        (2, ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1))),
        (0, ((0, 0),)),
    )),
    (5, 16, (
        (2, ((0, 0), (0, 1))),
        (0, ((0, 0),)),
        (0, ((0, 1), (1, 0), (1, 1))),
        (2, ((0, 0),)),
        (1, ((0, 0), (1, 0), (1, 1))),
    )),
)
SUMMARY = (
    "0-bg grid (h 5..14, w 12..22): row 0 is a legend listing 2..5 distinct "
    "non-zero colors by default (1..5 including the one_color edge) at "
    "scattered columns (left-to-right = pack order, "
    "always different from the below reading order when >=2 colors); row 1 "
    "is empty; rows 2..h-1 hold one 4-connected polyomino piece (1..5 "
    "cells canonical, up to 6 on generalized draws; bbox <= 3x3) per "
    "legend color, plus optional duplicate-color "
    "pieces (rule selects the LAST per color) and non-legend distractor "
    "pieces (rule ignores them). Output: the last piece per legend color "
    "cropped to its bbox and packed horizontally in legend order with "
    "1-column zero gaps."
)

# Rivals refuted by construction: 'pack pieces in below reading order' is
# refuted on every draw with >=2 colors (legend order is forced different);
# 'pack ALL pieces' is refuted by distractor draws; 'use FIRST piece per
# color' is refuted by duplicate draws whose two same-color pieces have
# different crops; 'pieces are solid rectangles' is refuted by polyomino
# pieces (solid pieces are only singletons and 1x2/2x1 dominoes, matching
# canonical which contains no solid rectangle larger than a 1x2 domino).
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "row 0 lists distinct non-zero legend colors at scattered ascending columns",
    "row 1 is entirely zero (separator)",
    "every legend color has at least one 4-connected piece in rows 2..h-1",
    "with >=2 legend colors, legend order differs from the below reading order",
    "pieces are 4-connected, 1..5 cells canonical (generalized to 6), "
    "bbox <= 3x3, never cardinally "
    "adjacent, and never solid rectangles larger than 1x2 (canonical "
    "test[0] has one 1x2 domino; the generator emits singletons and "
    "1x2/2x1 dominoes but no larger solid piece)",
    "rule selects the LAST piece per color (bottom-most, then right-most)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("one_color", "no_extras", "all_singletons")
HELPFUL_TEXTURES = PALETTE_KINDS

_PALETTES = {
    "warm": (2, 3, 4, 9),
    "cool": (1, 5, 8),
    "broad": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "primary": (1, 2, 3, 4),
}

AXES = {
    "grid_h":       {"type": "int", "default": "band rng 5..12", "valid": "5..14"},
    "grid_w":       {"type": "int", "default": "band rng 12..22", "valid": "12..22"},
    "n_colors":     {"type": "int", "default": "band rng 2..5", "valid": "1..5"},
    "n_duplicates": {"type": "int", "default": "band rng 0..2", "valid": "0..2"},
    "n_distractors": {"type": "int", "default": "band rng 0..2", "valid": "0..2"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "warm|cool|broad|primary"},
    "texture":      {"type": "str", "default": "none",
                     "valid": "none|warm|cool|broad|primary|one_color|no_extras|all_singletons"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _validate_call(difficulty, overrides):
    """Reject unsupported controls instead of silently coercing/falling back."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in (
        "grid_h", "grid_w", "n_colors", "n_duplicates", "n_distractors",
    ):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    for label in ("palette_kind", "texture"):
        value = overrides.get(label)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{label} must be a string")


def _polyomino(rng, k):
    """Random 4-connected polyomino of k cells as (r, c) list, normalized."""
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in sorted(cells)]


def _piece(rng, k_lo, k_hi):
    """Random piece of k_lo..k_hi cells with bbox <= 3x3 (canonical shapes:
    singletons, 1x2/2x1 dominoes, L/Z/S/U polyominoes -- never a solid
    rectangle larger than the canonical 1x2 domino)."""
    for _ in range(60):
        cells = _polyomino(rng, rng.randint(k_lo, k_hi))
        h = max(r for r, c in cells) + 1
        w = max(c for r, c in cells) + 1
        if h <= 3 and w <= 3 and (len(cells) <= 2 or len(cells) != h * w):
            return cells
    return [(0, 0)]   # singleton fallback always fits


def _components(grid, r_lo):
    """Maximal 4-connected non-zero components in rows >= r_lo."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(r_lo, h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            color = grid[r][c]
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (r_lo <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == color):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _normalize_shape(cells):
    cells = tuple(cells)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _d4_variants(cells):
    """All distinct rotations/reflections, normalized to the origin."""
    cells = tuple(cells)
    transforms = (
        lambda r, c: (r, c),
        lambda r, c: (r, -c),
        lambda r, c: (-r, c),
        lambda r, c: (-r, -c),
        lambda r, c: (c, r),
        lambda r, c: (c, -r),
        lambda r, c: (-c, r),
        lambda r, c: (-c, -r),
    )
    return tuple(sorted({
        _normalize_shape(transform(r, c) for r, c in cells)
        for transform in transforms
    }))


def _d4_class(cells):
    return min(_d4_variants(cells))


def _coerce_grid(grid):
    out = []
    for row in grid:
        out.append([
            int(value) if isinstance(value, str) and value.isdigit() else value
            for value in row
        ])
    return out


def linked_profile_signature(grid):
    """Complete color-invariant selection profile of a returned input.

    Absolute placement, color labels, and each piece's D4 orientation are
    lawful nuisances.  Component reading order, legend-role assignment, and
    the shape class of every component stay linked because they determine
    which duplicate is last and which crops are packed in output order.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    g = _coerce_grid(grid)
    if any(type(v) is not int for row in g for v in row):
        return None
    legend = [v for v in g[0] if v != 0]
    if not legend or len(legend) != len(set(legend)):
        return None
    roles = {color: index for index, color in enumerate(legend)}
    sequence = tuple(
        (
            roles.get(color, -1),
            _d4_class(_normalize_shape(cells)),
        )
        for color, cells in _components(g, 2)
    )
    return len(g), len(g[0]), len(legend), sequence


def _canonical_linked_signatures():
    return frozenset(
        (
            h,
            w,
            3,
            tuple((role, _d4_class(shape)) for role, shape in sequence),
        )
        for h, w, sequence in _LINKED_PROFILES
    )


_CANONICAL_LINKED_SIGNATURES = _canonical_linked_signatures()


def is_canonical_linked_profile(grid):
    signature = linked_profile_signature(grid)
    return (
        signature is not None
        and signature in _CANONICAL_LINKED_SIGNATURES
    )


def selected_shape_signature(grid):
    """Legend-ordered D4 shape classes selected by the rule's LAST policy."""
    signature = linked_profile_signature(grid)
    if signature is None:
        return None
    _, _, n_colors, sequence = signature
    selected = []
    for role in range(n_colors):
        candidates = [
            shape for component_role, shape in sequence
            if component_role == role
        ]
        if not candidates:
            return None
        selected.append(candidates[-1])
    return tuple(selected)


def rule_mirror(grid):
    """Python spelling of the stored Racket rule for real-backend parity."""
    g = _coerce_grid(grid)
    legend = [v for v in g[0] if v != 0]
    comps = _components(g, 2)
    crops = []
    for color in legend:
        matches = [cells for value, cells in comps if value == color]
        if not matches:
            raise ValueError(f"legend color {color} has no piece")
        cells = matches[-1]
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        crops.append([
            [g[r][c] for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)
        ])
    out_h = max(len(crop) for crop in crops)
    out_w = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    out = full_grid(out_h, out_w, 0)
    left = 0
    for crop in crops:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][left + c] = value
        left += len(crop[0]) + 1
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance. Accepts int grids and the
    bank's string-digit canonical storage (values are coerced for analysis).
    Enforces, in order: rectangular grid; the declared dimension envelope
    h 5..14 x w 12..22; colors 0..9; row 1 entirely zero; row 0 carries >=1
    non-zero legend cell and 1..5 distinct legend colors; every below-row
    non-zero component (piece) is 4-connected with 1..6 cells and bbox <=
    3x3, and is never a solid rectangle larger than 1x2 (canonical test[0]
    has a 1x2 domino, nothing larger); no two pieces are cardinally adjacent
    (diagonal contact is canonical); every legend color owns at least one
    piece (otherwise the oracle crashes); duplicates/distractors each stay
    in 0..2; and multi-color legend order differs from below reading order.
    Rejects width 23, solid 3x3 pieces, excess components, and the formerly
    accepted legend==reading shortcut."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    coerced = []
    for row in grid:
        out_row = []
        for v in row:
            if isinstance(v, bool):
                return ["boolean cell value"]
            if isinstance(v, int):
                out_row.append(v)
            elif isinstance(v, str) and v.isdigit():
                out_row.append(int(v))
            else:
                return [f"non-integer cell value {v!r}"]
        coerced.append(out_row)
    g = coerced
    errs = []
    if any(not 0 <= v <= 9 for row in g for v in row):
        errs.append("color outside 0..9")
    if not 5 <= h <= 14:
        errs.append(f"height {h} outside declared envelope 5..14")
    if not 12 <= w <= 22:
        errs.append(f"width {w} outside declared envelope 12..22")
    if any(v != 0 for v in g[1]):
        errs.append("row 1 is not an empty separator")
    if errs:
        return errs
    legend = [v for v in g[0] if v != 0]
    if not legend:
        errs.append("row 0 has no legend colors")
    if len(set(legend)) != len(legend):
        errs.append("legend colors are not distinct")
    if not 1 <= len(legend) <= 5:
        errs.append(
            f"legend has {len(legend)} colors outside the declared 1..5"
        )
    if errs:
        return errs
    comps = [(color, cells) for color, cells in _components(g, 2)
             if color != 0]
    comp_id = {}
    for idx, (color, cells) in enumerate(comps):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        bh = max(rs) - min(rs) + 1
        bw = max(cs) - min(cs) + 1
        if not 1 <= len(cells) <= 6:
            errs.append(
                f"piece of color {color} has {len(cells)} cells (declared 1..6)")
        if bh > 3 or bw > 3:
            errs.append(
                f"piece of color {color} has bbox {bh}x{bw} (declared <= 3x3)")
        if len(cells) > 2 and len(cells) == bh * bw:
            errs.append(
                f"piece of color {color} is a solid {bh}x{bw} rectangle "
                "(only 1x1/1x2 solid pieces are canonical)")
        for cell in cells:
            comp_id[cell] = idx
    for idx, (color, cells) in enumerate(comps):
        for (r, c) in cells:
            for dr, dc in _CARD:
                other = comp_id.get((r + dr, c + dc))
                if other is not None and other != idx:
                    errs.append(
                        f"pieces {idx} and {other} are cardinally adjacent "
                        f"at ({r},{c}) (declared separation)")
                    return errs
    below_colors = {color for color, _cells in comps}
    for color in set(legend):
        if color not in below_colors:
            errs.append(f"legend color {color} has no piece below (rule crashes)")
    n_legend_pieces = sum(
        1 for color, _cells in comps if color in set(legend)
    )
    n_duplicates = n_legend_pieces - len(legend)
    n_distractors = sum(
        1 for color, _cells in comps if color not in set(legend)
    )
    if not 0 <= n_duplicates <= 2:
        errs.append(
            f"duplicate count {n_duplicates} outside the declared 0..2"
        )
    if not 0 <= n_distractors <= 2:
        errs.append(
            f"distractor count {n_distractors} outside the declared 0..2"
        )
    reading = []
    for color, _cells in comps:
        if color in set(legend) and color not in reading:
            reading.append(color)
    if len(legend) >= 2 and reading == legend:
        errs.append(
            "legend order matches below reading order "
            "(canonical branch requires a different order)"
        )
    return errs


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0001):
    legend color count from row 0, and below-region component counts split
    by legend membership (pieces never merge: placement keeps them
    cardinal-separated, so component counts equal placed counts)."""
    legend = [v for v in grid[0] if v != 0]
    legend_set = set(legend)
    comps = _components(grid, 2)
    n_legend_pieces = sum(1 for color, _cells in comps if color in legend_set)
    n_distractors = sum(1 for color, _cells in comps if color not in legend_set)
    return {
        "n_colors": len(legend),
        "n_duplicates": n_legend_pieces - len(legend),
        "n_distractors": n_distractors,
    }


def _place_pieces(ctx, rng, h, w, pieces):
    """Place (color, cells) pieces in rows 2..h-1 with cardinal separation
    (diagonal contact allowed, per canonical). Exact counts ALWAYS:
    retries random positions, then falls back to a deterministic pitch-2
    lattice stamping singletons (nuisance shape only — keyed counts are
    never shed)."""
    for _layout in range(30):
        g = full_grid(h, w, 0)
        placed = []
        ok = True
        for color, cells in pieces:
            ph = max(r for r, c in cells) + 1
            pw = max(c for r, c in cells) + 1
            done = False
            for _try in range(200):
                r1 = rng.randint(2, max(2, h - ph))
                c1 = rng.randint(0, w - pw)
                abs_cells = {(r1 + r, c1 + c) for r, c in cells}
                clash = False
                for other in placed:
                    for (r, c) in abs_cells:
                        if (r, c) in other or any(
                                (r + dr, c + dc) in other for dr, dc in _CARD):
                            clash = True
                            break
                    if clash:
                        break
                if clash:
                    continue
                for (r, c) in abs_cells:
                    g[r][c] = color
                placed.append(abs_cells)
                done = True
                break
            if not done:
                ok = False
                break
        if ok:
            return g
    # deterministic guaranteed fallback: pitch-2 singleton lattice
    g = full_grid(h, w, 0)
    slots = [(r, c) for ri, r in enumerate(range(2, h))
             for c in range(ri % 2, w, 2)]
    for (color, cells), (r, c) in zip(pieces, slots):
        g[r][c] = color
    return g


def _write_legend(g, rng, colors):
    """Row 0 legend: shuffled order ALWAYS different from the below reading
    order (with >=2 colors), at scattered ascending columns."""
    h, w = len(g), len(g[0])
    reading = []
    for r in range(2, h):
        for c in range(w):
            if g[r][c] in colors and g[r][c] not in reading:
                reading.append(g[r][c])
    order = list(colors)
    for _ in range(20):
        rng.shuffle(order)
        if len(order) < 2 or order != reading:
            break
    if order == reading and len(order) >= 2:
        order[0], order[1] = order[1], order[0]
    n_leg = len(order)
    if n_leg > 1:
        gap_choices = [x for x in (1, 2, 3) if (w - 1) - (n_leg - 1) * x >= 0]
        gap = rng.choice(gap_choices)
    else:
        gap = 0
    start = rng.randint(0, min(2, (w - 1) - (n_leg - 1) * gap))
    for i, color in enumerate(order):
        g[0][start + i * gap] = color
    return g


def _write_ordered_legend(g, rng, colors):
    """Write an exact legend-role order at varied, non-adjacent columns."""
    w = len(g[0])
    for _ in range(100):
        columns = sorted(rng.sample(range(w), len(colors)))
        if all(b - a >= 2 for a, b in zip(columns, columns[1:])):
            break
    else:
        columns = list(range(1, 1 + 2 * len(colors), 2))
    for column, color in zip(columns, colors):
        g[0][column] = color
    return g


def _place_linked_profile(rng, h, w, colors, role_sequence):
    """Place a linked role/shape sequence without changing reading order."""
    pieces = [
        (colors[role], rng.choice(_d4_variants(shape)))
        for role, shape in role_sequence
    ]
    widths = [max(c for _, c in shape) + 1 for _, shape in pieces]
    heights = [max(r for r, _ in shape) + 1 for _, shape in pieces]
    required = sum(widths) + len(pieces) - 1
    if required > w or max(heights) > h - 2:
        raise ValueError(
            f"linked profile pieces do not fit {h}x{w}"
        )
    extras = [0] * (len(pieces) + 1)
    for _ in range(w - required):
        extras[rng.randrange(len(extras))] += 1
    top = rng.randint(2, h - max(heights))
    left = extras[0]
    g = full_grid(h, w, 0)
    for index, ((color, shape), width) in enumerate(zip(pieces, widths)):
        for r, c in shape:
            g[top + r][left + c] = color
        if index < len(pieces) - 1:
            left += width + 1 + extras[index + 1]
    return g


def _official_profile(ctx, rng, band):
    """Construct a complete linked role/reading-order profile.

    Each piece may take any D4 orientation, but its legend role, component
    reading order, and shape class stay linked.  Thus the duplicate-color
    LAST choice and final packed output sequence match a public archetype.
    """
    h, w, role_sequence = ctx.draw_choice(
        f"canonical_form|{band}",
        list(_LINKED_PROFILES),
    )
    n_colors = 3
    n_dups = len(role_sequence) - n_colors
    n_dist = 0
    h = ctx.draw_int("grid_h", h, h)
    w = ctx.draw_int("grid_w", w, w)
    n_colors = ctx.draw_int("n_colors", n_colors, n_colors)
    n_dups = ctx.draw_int("n_duplicates", n_dups, n_dups)
    n_dist = ctx.draw_int("n_distractors", n_dist, n_dist)
    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    pool = list(_PALETTES[palette_kind])
    rng.shuffle(pool)
    colors = pool[:n_colors]
    g = _place_linked_profile(
        rng,
        h,
        w,
        colors,
        role_sequence,
    )
    g = _write_ordered_legend(g, rng, colors)
    if linked_profile_signature(g) not in _CANONICAL_LINKED_SIGNATURES:
        raise AssertionError("linked profile constructor lost its signature")
    errs = self_check(g)
    if errs:
        raise AssertionError(f"linked profile failed self_check: {errs}")
    return g


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an override must execute exactly on any
    band, so it is validated against the full declared range (KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _band_params(difficulty):
    """(h range, w range, colors range, dups range, distractors range, piece cells)."""
    if difficulty == "easy":
        return (5, 6), (12, 16), (2, 3), (0, 1), (0, 1), (1, 4)
    if difficulty == "hard":
        return (7, 12), (16, 22), (3, 5), (0, 2), (0, 2), (2, 6)
    return (5, 8), (13, 18), (3, 4), (0, 1), (0, 1), (1, 6)   # medium / default


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    raw_texture = overrides.get("texture")
    effective_overrides = dict(overrides)
    if raw_texture in PALETTE_KINDS:
        palette_override = overrides.get("palette_kind")
        if (
            palette_override is not None
            and palette_override != raw_texture
        ):
            raise ValueError(
                f"texture={raw_texture!r} conflicts with "
                f"palette_kind={palette_override!r}"
            )
        effective_overrides["palette_kind"] = raw_texture
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=effective_overrides)
    overrides = effective_overrides
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    if raw_texture is not None:
        texture_name = ctx.draw_choice(
            "texture",
            ["none", *PALETTE_KINDS, *DEGENERATE_TEXTURES],
        )
    else:
        texture_name = ctx.draw_choice("texture", ["none"])
    texture = None if texture_name == "none" else texture_name
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            extra = sorted(k for k, v in overrides.items()
                           if k != "texture" and v is not None)
            if extra:
                raise ValueError(
                    f"degenerate texture {texture!r} is a fixed diagnostic "
                    f"layout; it takes no other overrides, got {extra}")
            return _draw_from_degenerate(texture, ctx, rng)

    # Default-only exact-profile prior (veto target >=25% in every band):
    # the five complete role/reading-order profiles. Any exact axis request
    # or named palette takes the generalized path instead.
    default_draw = not any(
        overrides.get(k) is not None
        for k in ("grid_h", "grid_w", "n_colors", "n_duplicates",
                  "n_distractors", "palette_kind"))
    if default_draw:
        profile_rng = ctx.draw_rng(f"profile|{band}")
        if profile_rng.random() < 0.28:
            return _official_profile(ctx, profile_rng, band)

    hr, wr, cr, dr_, er, pr = _band_params(difficulty)
    h = _banded_int(ctx, overrides, "grid_h", hr[0], hr[1], 5, 14)
    w = _banded_int(ctx, overrides, "grid_w", wr[0], wr[1], 12, 22)

    # Palette: helpful textures pick a real color pool; the legend needs
    # n_colors distinct colors from it. An explicit palette clamps the
    # n_colors band (never a silent failure); an explicit (palette,
    # n_colors) pair that cannot fit fails loudly.
    if overrides.get("palette_kind") is not None:
        palette_kind = ctx.draw_choice(
            "palette_kind",
            list(PALETTE_KINDS),
        )
        pool = list(_PALETTES[palette_kind])
        n_colors = _banded_int(ctx, overrides, "n_colors",
                               cr[0], min(cr[1], len(pool)), 1, 5)
        if len(pool) < n_colors:
            raise ValueError(
                f"palette_kind={palette_kind} has {len(pool)} colors < "
                f"n_colors={n_colors}")
    else:
        n_colors = _banded_int(ctx, overrides, "n_colors", cr[0], cr[1], 1, 5)
        palette_kind = ctx.draw_choice(
            "palette_kind",
            [k for k in PALETTE_KINDS if len(_PALETTES[k]) >= n_colors])
        pool = list(_PALETTES[palette_kind])
    n_dups = _banded_int(ctx, overrides, "n_duplicates", dr_[0], dr_[1], 0, 2)
    n_dist = _banded_int(ctx, overrides, "n_distractors", er[0], er[1], 0, 2)
    rng.shuffle(pool)
    colors = pool[:n_colors]

    # Layout: legend pieces first (every legend color must land), then
    # duplicate-color pieces, then non-legend distractors. Bounded retries
    # with the deterministic lattice backstop; keyed counts are never shed.
    pieces = [(c, False) for c in colors]
    dup_colors = [rng.choice(colors) for _ in range(n_dups)]
    pieces += [(c, True) for c in dup_colors]
    dist_pool = [c for c in pool[n_colors:]] or \
                [c for c in range(1, 10) if c not in colors]
    pieces += [(rng.choice(dist_pool), True) for _ in range(n_dist)]
    duplicate_colors = {
        color for color in colors
        if sum(piece_color == color for piece_color, _ in pieces) > 1
    }
    for _scene_attempt in range(30):
        seen_shapes = {}
        shape_pieces = []
        shape_ok = True
        for color, _ in pieces:
            forbidden = seen_shapes.setdefault(color, set())
            for _shape_attempt in range(100):
                shape = _piece(rng, pr[0], pr[1])
                key = tuple(shape)
                if color not in duplicate_colors or key not in forbidden:
                    forbidden.add(key)
                    shape_pieces.append((color, shape))
                    break
            else:
                shape_ok = False
                break
        if not shape_ok:
            continue
        candidate = _place_pieces(ctx, rng, h, w, shape_pieces)
        components = _components(candidate, 2)
        if all(
            len({
                _normalize_shape(cells)
                for value, cells in components
                if value == color
            })
            == sum(
                value == color for value, _cells in components
            )
            for color in duplicate_colors
        ):
            g = candidate
            break
    else:
        raise ValueError(
            "could not realize distinguishable duplicate-color pieces"
        )
    g = _write_legend(g, rng, colors)

    errs = self_check(g, difficulty=difficulty)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, ctx, rng):
    """Fixed minimal layouts; every one is a lawful, self_check-clean draw."""
    if name == "one_color":
        g = full_grid(6, 12, 0)
        g[0][1] = 2
        g[3][4] = 2
    elif name == "no_extras":
        g = full_grid(6, 14, 0)
        for (r, c) in [(2, 1), (2, 2), (3, 1)]:
            g[r][c] = 2
        for (r, c) in [(3, 6), (3, 7), (4, 7)]:
            g[r][c] = 4
        for (r, c) in [(2, 10), (3, 10), (3, 11)]:
            g[r][c] = 7
        for i, color in enumerate((4, 2, 7)):
            g[0][1 + 2 * i] = color
    elif name == "all_singletons":
        g = full_grid(5, 13, 0)
        g[2][2] = 3
        g[3][7] = 5
        g[4][11] = 8
        for i, color in enumerate((5, 3, 8)):
            g[0][1 + 2 * i] = color
    else:
        raise ValueError(f"unknown degenerate texture {name!r}")
    observed = observe_overrides(g)
    ctx.draw_int("grid_h", len(g), len(g))
    ctx.draw_int("grid_w", len(g[0]), len(g[0]))
    ctx.draw_int(
        "n_colors", observed["n_colors"], observed["n_colors"]
    )
    ctx.draw_int(
        "n_duplicates",
        observed["n_duplicates"],
        observed["n_duplicates"],
    )
    ctx.draw_int(
        "n_distractors",
        observed["n_distractors"],
        observed["n_distractors"],
    )
    ctx.draw_choice("palette_kind", ["broad"])
    errs = self_check(g)
    if errs:
        raise AssertionError(f"degenerate texture failed self_check: {errs}")
    return g
