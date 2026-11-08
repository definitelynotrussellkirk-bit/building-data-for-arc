"""Generator for b25e450b — edge-hole mirror + orange sweep.

Rule: find every 4-connected zero component. A hole touching the top or
bottom edge is mirrored vertically (row-flipped to the opposite side);
a hole touching the left or right edge is mirrored horizontally
(col-flipped). The hole's full column band (top/bottom holes) or row
band (left/right holes) is then painted 7, with mirrored hole cells
taking precedence as 0. Floating holes are skipped by the mirror but
their cells can still be consumed by another hole's sweep.

Combinatorial axes (7): grid_h, grid_w, edge, hole_len, hole_depth,
hole_count, texture.  Degenerates: corner_hole (hole at a corner touches two
edges; the rule's top/bottom mirror priority fires), floating_hole
(one interior hole that the mirror skips plus at least one edge hole).
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9b2cd53e36fb"
RULE_HASH = "7f60c228b0fa"  # canonical rule this generator was verified against
VERSION = "3.4.1"  # 3.4.1 validates the public override contract; 3.4.0 reserves the floating component during feasibility and uses an exact constructive fallback.
TASK_ID = "9b2cd53e36fb"

# Exact official (h, w, hole_count) tuples from the canonical rows.
OFFICIAL_TUPLES = ((6, 8, 1), (10, 10, 3), (12, 12, 3), (18, 14, 8))
# Full LINKED hole signatures per official canvas: sorted (edge, span,
# depth) multisets, verified executably from the canonical records.
ARCHETYPES = {
    (6, 8): (("right", 3, 3),),
    (10, 10): (("bottom", 2, 2), ("bottom", 2, 3), ("left", 3, 3)),
    (12, 12): (("bottom", 1, 2), ("right", 2, 4), ("top", 4, 3)),
    (18, 14): (("bottom", 1, 4), ("bottom", 4, 3), ("left", 2, 3),
               ("left", 3, 6), ("right", 1, 3), ("right", 2, 2),
               ("right", 2, 3), ("top", 1, 2)),
}

SUMMARY = (
    "Grid (h 6..18, w 8..14) textured with a random 5/7 mix, carrying "
    "1..8 rectangular zero holes (along-edge span 1..6, "
    "perpendicular depth 1..6), "
    "each touching exactly one edge and placed clear of corners "
    "(margin >=1). Rule: every edge-touching zero component is "
    "mirrored to the opposite edge (row-flip for top/bottom holes, "
    "col-flip for left/right holes), then the hole's full column band "
    "(top/bottom) or row band (left/right) is painted 7; mirrored "
    "zeros take precedence over the sweep. Floating holes are not "
    "mirrored but may be consumed by other sweeps."
)

# Rivals: 'single hole only' refuted by canonical demos with 3-7 holes.
# 'mirror without sweep' refuted by the full 7 band. 'sweep only the
# hole rows/cols partially' refuted by full-height/full-width bands.
# 'bg is flat 8' refuted by the 5/7 texture in every canonical pair.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background texture is a random mix of 5 and 7",
    "1..8 rectangular zero components",
    "each edge-touching hole touches exactly one edge, clear of corners",
    "holes are separated by >=1 cell so each is its own component",
]

EDGES = ("top", "bottom", "left", "right")
DEGENERATE_TEXTURES = ("corner_hole", "floating_hole")
HELPFUL_TEXTURES = EDGES

AXES = {
    "grid_h":     {"type": "int", "default": "rng 6..18 (band-skewed)",
                   "valid": "6..18"},
    "grid_w":     {"type": "int", "default": "rng 8..14 (band-skewed)",
                   "valid": "8..14"},
    "edge":       {"type": "str", "default": "rng helpful",
                   "valid": "|".join(EDGES)},
    "hole_len":   {"type": "int", "default": "rng 1..6 per hole",
                   "valid": "1..6"},
    "hole_depth": {"type": "int", "default": "rng 1..6 per hole",
                   "valid": "1..6"},
    "hole_count": {"type": "int", "default": "rng 1..8 (band-skewed)",
                   "valid": "1..8"},
    "texture":    {"type": "str", "default": "alias for edge",
                   "valid": "|".join(HELPFUL_TEXTURES)},
}


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    texture = overrides.get("texture")
    valid_textures = set(HELPFUL_TEXTURES) | set(DEGENERATE_TEXTURES)
    if texture is not None and texture not in valid_textures:
        raise ValueError(
            f"unknown texture {texture!r}; valid: {sorted(valid_textures)}"
        )


def _zero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or seen[r][c]:
                continue
            cells = []
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == 0):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _edge_of(bbox, h, w):
    r1, c1, r2, c2 = bbox
    if r1 == 0: return "top"
    if r2 == h - 1: return "bottom"
    if c1 == 0: return "left"
    if c2 == w - 1: return "right"
    return None


def _free_with_halo(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] == 0:
                return False
    return True


def _paint_hole(g, edge, span, depth, pos, *, at_corner=False):
    """Paint one rectangular zero hole. Returns True on success.

    span = along-edge length, depth = perpendicular thickness, pos =
    offset of the hole's near end along the edge (>=1 keeps corner margin).
    """
    h, w = len(g), len(g[0])
    if edge in ("top", "bottom"):
        if pos + span > w - (0 if at_corner else 1) or pos < (0 if at_corner else 1):
            return False
        r1 = 0 if edge == "top" else h - depth
        c1 = pos
        r2, c2 = r1 + depth - 1, c1 + span - 1
    else:
        if pos + span > h - (0 if at_corner else 1) or pos < (0 if at_corner else 1):
            return False
        c1 = 0 if edge == "left" else w - depth
        r1 = pos
        r2, c2 = r1 + span - 1, c1 + depth - 1
    if not _free_with_halo(g, r1, c1, r2, c2):
        return False
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            g[r][c] = 0
    return True


def _paint_floating(g, rng):
    """One interior zero rect (1..2 per side) that touches no edge."""
    h, w = len(g), len(g[0])
    for _ in range(200):
        rh = rng.randint(1, 2)
        rw = rng.randint(1, 2)
        r1 = rng.randint(1, h - rh - 1)
        c1 = rng.randint(1, w - rw - 1)
        if _free_with_halo(g, r1, c1, r1 + rh - 1, c1 + rw - 1):
            for r in range(r1, r1 + rh):
                for c in range(c1, c1 + rw):
                    g[r][c] = 0
            return True
    return False


def _hole_bboxes(h, w, span, depth, edges=EDGES):
    """Return every legal, corner-clear bbox for one edge-hole geometry."""
    boxes = []
    for edge in edges:
        along = w if edge in ("top", "bottom") else h
        perp = h if edge in ("top", "bottom") else w
        if span > along - 2 or depth > perp - 1:
            continue
        for pos in range(1, along - span):
            if edge == "top":
                box = (0, pos, depth - 1, pos + span - 1)
            elif edge == "bottom":
                box = (h - depth, pos, h - 1, pos + span - 1)
            elif edge == "left":
                box = (pos, 0, pos + span - 1, depth - 1)
            else:
                box = (pos, w - depth, pos + span - 1, w - 1)
            boxes.append(box)
    return tuple(boxes)


def _boxes_conflict(left, right):
    """Whether two rectangles violate the one-cell nonzero halo."""
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    return not (
        lr2 + 1 < rr1
        or rr2 + 1 < lr1
        or lc2 + 1 < rc1
        or rc2 + 1 < lc1
    )


def _pack_compatible(boxes, count):
    """Find ``count`` pairwise halo-separated boxes, or return ``None``."""
    if count == 0:
        return ()
    if len(boxes) < count:
        return None

    conflicts = []
    for i, box in enumerate(boxes):
        mask = 1 << i
        for j, other in enumerate(boxes):
            if i != j and _boxes_conflict(box, other):
                mask |= 1 << j
        conflicts.append(mask)

    @lru_cache(maxsize=None)
    def search(mask, needed):
        if needed == 0:
            return ()
        if mask.bit_count() < needed:
            return None
        while mask:
            bit = mask & -mask
            index = bit.bit_length() - 1
            tail = search(mask & ~conflicts[index], needed - 1)
            if tail is not None:
                return (index,) + tail
            mask ^= bit
        return None

    indexes = search((1 << len(boxes)) - 1, count)
    if indexes is None:
        return None
    return tuple(boxes[index] for index in indexes)


@lru_cache(maxsize=None)
def _floating_layout_bboxes(
    h,
    w,
    edge,
    primary_span,
    primary_depth,
    edge_count,
    secondary_span,
    secondary_depth,
):
    """Construct edge holes plus one reserved interior hole exactly.

    The primary edge and geometry remain keyed. Remaining edge holes use the
    requested geometry on requested axes and 1x1 nuisance geometry otherwise.
    Feasibility and final placement share this function, so an accepted count
    cannot later lose its floating component.
    """
    if edge_count < 1:
        return None
    primaries = _hole_bboxes(
        h, w, primary_span, primary_depth, edges=(edge,)
    )
    secondaries = _hole_bboxes(
        h, w, secondary_span, secondary_depth
    )
    center_r2 = h - 1
    center_c2 = w - 1
    floating = sorted(
        ((r, c, r, c) for r in range(1, h - 1) for c in range(1, w - 1)),
        key=lambda box: (
            abs(2 * box[0] - center_r2) + abs(2 * box[1] - center_c2),
            box[0],
            box[1],
        ),
    )
    for floating_box in floating:
        for primary_box in primaries:
            if _boxes_conflict(floating_box, primary_box):
                continue
            candidates = tuple(
                box
                for box in secondaries
                if not _boxes_conflict(box, floating_box)
                and not _boxes_conflict(box, primary_box)
            )
            packed = _pack_compatible(candidates, edge_count - 1)
            if packed is not None:
                return (floating_box, primary_box) + packed
    return None


def _floating_edge_capacity(
    h, w, edge, primary_span, primary_depth, secondary_span, secondary_depth
):
    """Largest exact edge-hole count that still leaves one floating hole."""
    for edge_count in range(7, 0, -1):
        if _floating_layout_bboxes(
            h,
            w,
            edge,
            primary_span,
            primary_depth,
            edge_count,
            secondary_span,
            secondary_depth,
        ) is not None:
            return edge_count
    return 0


def _paint_bboxes(g, boxes):
    for r1, c1, r2, c2 in boxes:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                g[r][c] = 0


def _textured_grid(ctx, h, w):
    rng = ctx.draw_rng("texture")
    return [[5 if rng.random() < 0.5 else 7 for _ in range(w)] for _ in range(h)]


def _ensure_texture(g, rng):
    """Guarantee both texture colors survive hole painting (self_check contract)."""
    flat = [v for row in g for v in row]
    for needed in (5, 7):
        if needed in flat:
            continue
        textured = [(r, c) for r in range(len(g)) for c in range(len(g[0]))
                    if g[r][c] != 0]
        r, c = textured[rng.randrange(len(textured))]
        g[r][c] = needed
        flat.append(needed)
    return g


def _edge_capacity(L, span):
    """Max holes of along-edge `span` on one edge of length L, with corner
    margins >=1 and >=2 cells between holes (halo-safe pitch)."""
    if span > L - 2:
        return 0
    return (L - 2 - span) // (span + 2) + 1


def _edge_capacity_tight(L, span):
    """Tighter per-edge capacity used for nuisance geometry (1-cell gaps,
    as the deterministic 1x1 last-resort packs them)."""
    if span > L - 2:
        return 0
    return (L - 2 - span) // (span + 1) + 1


def _cap_after_primary(h, w, edge, span, depth, *, corner=False, corner_side=1):
    """Exact capacity after the primary hole: 1 (the primary) plus the
    halo-free 1x1 perimeter slots left on a scratch grid, consumed in
    last-resort order. This mirrors the hybrid fallback exactly, so a
    count drawn within this cap is always realizable."""
    g = [[7] * w for _ in range(h)]
    limit = (w if edge in ("top", "bottom") else h)
    placed = False
    if corner:
        for pos in (0, limit - corner_side):
            if _paint_hole(g, edge, corner_side, corner_side, pos, at_corner=True):
                placed = True
                break
    else:
        for pos in range(1, limit - span + 1):
            if _paint_hole(g, edge, span, depth, pos):
                placed = True
                break
    if not placed:
        return 0
    spots = ([(0, c) for c in range(1, w - 1)] +
             [(h - 1, c) for c in range(1, w - 1)] +
             [(r, 0) for r in range(1, h - 1)] +
             [(r, w - 1) for r in range(1, h - 1)])
    free = 0
    for r, c in spots:
        if _free_with_halo(g, r, c, r, c):
            g[r][c] = 0
            free += 1
    return 1 + free


def _place_exact(g, span, depth, count, rng):
    """Deterministic exact-count placement: fixed slot order on each edge,
    skipping halo conflicts. Returns True when every hole was placed."""
    h, w = len(g), len(g[0])
    placed = 0
    for edge, L, perp in (("top", w, h), ("bottom", w, h),
                          ("left", h, w), ("right", h, w)):
        if placed >= count:
            break
        if depth > perp - 1:
            continue
        for j in range(_edge_capacity(L, span)):
            if placed >= count:
                break
            pos = 1 + j * (span + 2)
            if _paint_hole(g, edge, span, depth, pos):
                placed += 1
    return placed == count


def _uniform_cap(h, w, span, depth):
    """Exact achievable uniform-geometry capacity: mirrors _place_exact on
    a scratch grid, so a count drawn within this cap always fills."""
    g = [[7] * w for _ in range(h)]
    placed = 0
    for edge, L, perp in (("top", w, h), ("bottom", w, h),
                          ("left", h, w), ("right", h, w)):
        if depth > perp - 1:
            continue
        for j in range(_edge_capacity(L, span)):
            pos = 1 + j * (span + 2)
            if _paint_hole(g, edge, span, depth, pos):
                placed += 1
    return placed


def _resolve_edge(overrides, ctx, texture, feasible):
    """Edge axis with texture-as-alias; conflicting aliases rejected loudly."""
    tex_edge = texture if texture in EDGES else None
    req = overrides.get("edge")
    if tex_edge and req and tex_edge != req:
        raise ValueError(f"texture {tex_edge!r} conflicts with edge {req!r}")
    edge = tex_edge or req
    if edge is not None:
        if edge not in feasible:
            raise ValueError(
                f"edge {edge!r} cannot fit the requested hole span here")
        return edge
    return ctx.draw_choice("edge", list(feasible))


def _official_profile(ctx, rng):
    """One exact official LINKED hole profile: an official (h, w) canvas
    carrying its full sorted (edge, span, depth) signature multiset, with
    along-edge positions and the 5/7 texture varying as nuisance."""
    h, w = rng.choice(sorted(ARCHETYPES))
    sig = ARCHETYPES[(h, w)]
    # keyed provenance: dims, exact count, and the first signature hole's
    # geometry recorded as typed draws on this default prior path.
    h = ctx.draw_int("grid_h", h, h)
    w = ctx.draw_int("grid_w", w, w)
    count = ctx.draw_int("hole_count", len(sig), len(sig))
    pe, ps, pd = sig[0]
    _ = ctx.draw_int("hole_len", ps, ps)
    _ = ctx.draw_int("hole_depth", pd, pd)
    for _attempt in range(50):
        g = _textured_grid(ctx, h, w)
        ok = True
        for edge, span, depth in sig:
            limit = w if edge in ("top", "bottom") else h
            done = False
            for _ in range(120):
                pos = rng.randint(1, limit - span - 1)
                if _paint_hole(g, edge, span, depth, pos):
                    done = True
                    break
            if not done:
                ok = False
                break
        if ok:
            return _ensure_texture(g, rng)
    # deterministic fallback: scan every position for each signature hole
    g = _textured_grid(ctx, h, w)
    for edge, span, depth in sig:
        limit = w if edge in ("top", "bottom") else h
        for pos in range(1, limit - span + 1):
            if _paint_hole(g, edge, span, depth, pos):
                break
        else:
            raise ValueError(
                f"archetype hole {(edge, span, depth)} does not fit {h}x{w}")
    return _ensure_texture(g, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"

    # Explicit exact-profile prior (veto target: strict official-tuple
    # coverage above the 5% floor in EVERY band). Default draws only —
    # any requested exact axis takes the general path instead.
    default_draw = not any(
        overrides.get(k) is not None
        for k in ("grid_h", "grid_w", "edge", "hole_len", "hole_depth",
                  "hole_count", "texture"))
    if default_draw:
        profile_rng = ctx.draw_rng(f"profile|{band}")
        if profile_rng.random() < 0.12:
            return _official_profile(ctx, profile_rng)

    # Dimensions on the FULL declared range in every band so any globally-
    # valid override is honored on every band (difficulty only skews draws).
    h = ctx.draw_int_diff("grid_h", 6, 18)
    w = ctx.draw_int_diff("grid_w", 8, 14)
    texture = overrides.get("texture")

    # hole_len/hole_depth/hole_count are always drawn through GenCtx (v5
    # provenance). Requested values constrain the BOUNDS of the keyed
    # draws that follow them, so every keyed value is realizable: the
    # feasible count/geometry is chosen BEFORE each keyed draw, and the
    # returned grid always realizes the keyed values exactly.
    corner = texture == "corner_hole"
    floating = texture == "floating_hole"
    margin = 0 if corner else 1
    requested_edge = (texture if texture in EDGES else None) or overrides.get("edge")
    hole_len_req = overrides.get("hole_len")
    hole_depth_req = overrides.get("hole_depth")
    hole_count_req = overrides.get("hole_count")

    if corner:
        # The corner hole is a SQUARE: hole_len and hole_depth are the same
        # physical side, so both axes are keyed to one value up front.
        if hole_len_req is not None and hole_depth_req is not None:
            primary_span = ctx.draw_int("hole_len", 1, 6)
            primary_depth = ctx.draw_int("hole_depth", 1, 6)
            if primary_span != primary_depth:
                raise ValueError(
                    f"texture='corner_hole' needs hole_len == hole_depth for "
                    f"its square corner hole (got {primary_span} vs "
                    f"{primary_depth})")
        elif hole_depth_req is not None:
            primary_depth = ctx.draw_int("hole_depth", 1, 6)
            primary_span = ctx.draw_int("hole_len", primary_depth, primary_depth)
        elif hole_len_req is not None:
            primary_span = ctx.draw_int("hole_len", 1, 6)
            primary_depth = ctx.draw_int("hole_depth", primary_span, primary_span)
        else:
            primary_span = ctx.draw_int("hole_len", 1,
                                        min(6, max(w, h) - 2))
            primary_depth = ctx.draw_int("hole_depth", primary_span, primary_span)
        corner_side = primary_span
    else:
        corner_side = None

    def fits(edge_, span):
        return span <= (w - 2 * margin) if edge_ in ("top", "bottom") \
            else span <= (h - 2 * margin)

    def depth_fits(edge_, dep):
        return dep <= (h - 1) if edge_ in ("top", "bottom") else dep <= (w - 1)

    def hybrid_cap(edge_, span, depth):
        return _cap_after_primary(h, w, edge_, span, depth,
                                  corner=corner, corner_side=span)

    if hole_count_req is not None:
        count = ctx.draw_int("hole_count", 1, 8)   # declared-range validation
        if floating and count < 2:
            raise ValueError(
                "hole_count=1 conflicts with texture='floating_hole' "
                "(needs one edge hole plus one floating hole)")
        n_edge_holes = count - 1 if floating else count
        if floating:
            # With an explicit total count, choose nuisance geometry before
            # accepting the request and reserve the interior component in the
            # same exact constructor used for the returned grid. Requested
            # length/depth axes remain uniform across all edge holes.
            primary_span = (
                ctx.draw_int("hole_len", 1, 6)
                if hole_len_req is not None
                else ctx.draw_int("hole_len", 1, 1)
            )
            primary_depth = (
                ctx.draw_int("hole_depth", 1, 6)
                if hole_depth_req is not None
                else ctx.draw_int("hole_depth", 1, 1)
            )
            secondary_span = primary_span if hole_len_req is not None else 1
            secondary_depth = primary_depth if hole_depth_req is not None else 1
            feasible = [
                candidate_edge
                for candidate_edge in EDGES
                if _floating_layout_bboxes(
                    h,
                    w,
                    candidate_edge,
                    primary_span,
                    primary_depth,
                    n_edge_holes,
                    secondary_span,
                    secondary_depth,
                ) is not None
            ]
            if not feasible:
                raise ValueError(
                    f"floating hole plus hole_count={count} cannot fit "
                    f"the requested geometry on a {h}x{w} grid"
                )
            edge = _resolve_edge(overrides, ctx, texture, feasible)
            boxes = _floating_layout_bboxes(
                h,
                w,
                edge,
                primary_span,
                primary_depth,
                n_edge_holes,
                secondary_span,
                secondary_depth,
            )
            if boxes is None:  # guarded by the exact feasibility query above
                raise AssertionError("floating-hole feasibility drift")
            g = _textured_grid(ctx, h, w)
            _paint_bboxes(g, boxes)
            return _ensure_texture(g, rng)
        edges_avail = [requested_edge] if requested_edge else list(EDGES)
        if requested_edge in ("top", "bottom"):
            s_bound = w - 2 * margin
        elif requested_edge in ("left", "right"):
            s_bound = h - 2 * margin
        else:
            s_bound = max(w - 2 * margin, h - 2 * margin)
        # keyed span must leave room for the requested count on EVERY
        # candidate edge (worst-edge bound, so the edge draw stays free)
        if corner:
            if _uniform_cap(h, w, corner_side, corner_side) < n_edge_holes:
                raise ValueError(
                    f"corner side {corner_side} leaves no room for "
                    f"hole_count={count} on {h}x{w}")
        elif hole_len_req is not None:
            primary_span = ctx.draw_int("hole_len", 1, 6)
            if primary_span > min(6, s_bound):
                raise ValueError(
                    f"hole_len={primary_span} fits the requested geometry "
                    f"on a {h}x{w} grid")
            if _uniform_cap(h, w, primary_span, 1) < n_edge_holes:
                raise ValueError(
                    f"hole_len={primary_span} leaves no room for "
                    f"hole_count={count} on {h}x{w}")
        else:
            s_hi = 0
            for s in range(min(6, s_bound), 0, -1):
                cap_s = min((_cap_after_primary(h, w, e, s, 1,
                                                corner=corner, corner_side=s)
                             for e in edges_avail), default=0)
                if cap_s >= n_edge_holes:
                    s_hi = s
                    break
            if s_hi < 1:
                raise ValueError(
                    f"hole_count={count} cannot fit on a {h}x{w} grid")
            primary_span = ctx.draw_int("hole_len", 1, s_hi)
        # keyed depth must keep that room
        if not corner:
            if hole_depth_req is not None:
                primary_depth = ctx.draw_int("hole_depth", 1, 6)
                if _uniform_cap(h, w, primary_span, primary_depth) < n_edge_holes:
                    raise ValueError(
                        f"hole_depth={primary_depth} leaves no room for "
                        f"hole_count={count} on {h}x{w}")
            else:
                d_hi = 0
                for d in range(6, 0, -1):
                    if hole_len_req is not None:
                        cap_d = _uniform_cap(h, w, primary_span, d)
                    else:
                        cap_d = min((_cap_after_primary(h, w, e, primary_span, d,
                                                        corner=corner,
                                                        corner_side=primary_span)
                                     for e in edges_avail), default=0)
                    if cap_d >= n_edge_holes:
                        d_hi = d
                        break
                if d_hi < 1:
                    raise ValueError(
                        f"hole_count={count} with span {primary_span} cannot "
                        f"fit on a {h}x{w} grid")
                primary_depth = ctx.draw_int("hole_depth", 1, d_hi)
        feasible = [e for e in EDGES
                    if fits(e, primary_span) and depth_fits(e, primary_depth)]
        edge = _resolve_edge(overrides, ctx, texture, feasible)
    else:
        # unrequested count: bounded-realizable keyed geometry first
        if floating and hole_len_req is None and hole_depth_req is None:
            # A floating texture requested by itself is a declared/default
            # case and must always succeed. Keep the nuisance primary compact;
            # the exact capacity calculation below still varies total count.
            primary_span = ctx.draw_int("hole_len", 1, 2)
            primary_depth = ctx.draw_int("hole_depth", 1, 2)
        elif not corner:
            if requested_edge in ("top", "bottom"):
                span_hi = min(6, w - 2 * margin)
            elif requested_edge in ("left", "right"):
                span_hi = min(6, h - 2 * margin)
            else:
                span_hi = min(6, max(w - 2 * margin, h - 2 * margin))
            if hole_depth_req is not None and requested_edge is None:
                # the span draw must leave an orientation for the requested depth
                span_hi = min(span_hi,
                              max((w - 2 * margin) if hole_depth_req <= h - 1 else 0,
                                  (h - 2 * margin) if hole_depth_req <= w - 1 else 0))
                if span_hi < 1:
                    raise ValueError(
                        f"hole_depth={hole_depth_req} fits no edge of a {h}x{w} grid")
            if hole_len_req is not None:
                primary_span = ctx.draw_int("hole_len", 1, 6)
                if primary_span > span_hi:
                    raise ValueError(
                        f"hole_len={primary_span} fits the requested geometry "
                        f"on a {h}x{w} grid")
            else:
                primary_span = ctx.draw_int("hole_len", 1, max(1, span_hi))
            if requested_edge in ("top", "bottom"):
                depth_hi = min(6, h - 1)
            elif requested_edge in ("left", "right"):
                depth_hi = min(6, w - 1)
            else:
                depth_hi = max((h - 1) if primary_span <= w - 2 * margin else 0,
                               (w - 1) if primary_span <= h - 2 * margin else 0)
                depth_hi = min(6, depth_hi)
            if hole_depth_req is not None:
                primary_depth = ctx.draw_int("hole_depth", 1, 6)
                if primary_depth > depth_hi:
                    raise ValueError(
                        f"hole_depth={primary_depth} with span {primary_span} "
                        f"fits the requested geometry on a {h}x{w} grid")
            else:
                primary_depth = ctx.draw_int("hole_depth", 1, max(1, depth_hi))
        feasible = [e for e in EDGES
                    if fits(e, primary_span) and depth_fits(e, primary_depth)]
        if floating:
            secondary_span = primary_span if hole_len_req is not None else 1
            secondary_depth = primary_depth if hole_depth_req is not None else 1
            feasible = [
                candidate_edge
                for candidate_edge in feasible
                if _floating_layout_bboxes(
                    h,
                    w,
                    candidate_edge,
                    primary_span,
                    primary_depth,
                    1,
                    secondary_span,
                    secondary_depth,
                ) is not None
            ]
            if not feasible:
                raise ValueError(
                    f"floating hole cannot fit the requested geometry "
                    f"on a {h}x{w} grid"
                )
        edge = _resolve_edge(overrides, ctx, texture, feasible)
        # the count is keyed inside the exact simulated capacity
        if floating:
            edge_capacity = _floating_edge_capacity(
                h,
                w,
                edge,
                primary_span,
                primary_depth,
                secondary_span,
                secondary_depth,
            )
            cap = 1 + edge_capacity
        elif corner:
            cap = _uniform_cap(h, w, corner_side, corner_side)
        elif hole_len_req is not None or hole_depth_req is not None:
            cap = _uniform_cap(h, w, primary_span, primary_depth)
        else:
            cap = hybrid_cap(edge, primary_span, primary_depth)
        cap = max(1, cap)
        lo = 2 if floating else 1
        if min(8, cap) < lo:
            raise ValueError(
                f"texture='floating_hole' needs room for 2 holes on {h}x{w}")
        count = ctx.draw_int_diff("hole_count", lo, min(8, cap))
        n_edge_holes = count - 1 if floating else count

    n_holes = n_edge_holes
    span_live, depth_live = primary_span, primary_depth
    for _attempt in range(60):
        g = _textured_grid(ctx, h, w)
        placed = 0
        # primary hole on the drawn/requested edge
        for _ in range(80):
            if corner:
                span = depth = corner_side
                pos = 0 if rng.random() < 0.5 else (
                    (w if edge in ("top", "bottom") else h) - span)
            else:
                span = span_live
                depth = depth_live
                limit = (w if edge in ("top", "bottom") else h)
                pos = rng.randint(1, limit - span - 1)
            if _paint_hole(g, edge, span, depth, pos, at_corner=corner):
                placed += 1
                break
        ok = placed == 1
        # remaining edge holes
        while ok and placed < n_holes:
            e2 = rng.choice(EDGES)
            span2 = span_live if hole_len_req is not None else rng.randint(1, 6)
            depth2 = depth_live if hole_depth_req is not None else rng.randint(1, 6)
            limit = w if e2 in ("top", "bottom") else h
            dep_limit = h if e2 in ("top", "bottom") else w
            # unrequested spans/depths are nuisance: shrink to fit this grid
            if span2 > limit - 2:
                if hole_len_req is not None:
                    ok = False
                    break
                span2 = limit - 2
            if depth2 > dep_limit - 1:
                if hole_depth_req is not None:
                    ok = False
                    break
                depth2 = dep_limit - 1
            done = False
            for _ in range(80):
                pos2 = rng.randint(1, limit - span2 - 1)
                if _paint_hole(g, e2, span2, depth2, pos2):
                    placed += 1
                    done = True
                    break
            if not done:
                if hole_count_req is not None:
                    ok = False   # requested count: retry the whole layout
                break
        if ok and floating:
            ok = _paint_floating(g, rng)
        if ok and placed == n_holes:
            g = _ensure_texture(g, rng)
            return g
    # Exact-count last resorts. The keyed hole_count and the keyed primary
    # span/depth are always realized; nothing keyed is ever replaced.
    g = _textured_grid(ctx, h, w)
    if floating:
        boxes = _floating_layout_bboxes(
            h,
            w,
            edge,
            span_live,
            depth_live,
            n_holes,
            secondary_span,
            secondary_depth,
        )
        if boxes is None:
            raise ValueError(
                f"could not place floating hole plus {n_holes} edge holes "
                f"(primary span {primary_span}, depth {primary_depth}) "
                f"on a {h}x{w} grid"
            )
        _paint_bboxes(g, boxes)
        return _ensure_texture(g, rng)
    if hole_len_req is not None or hole_depth_req is not None:
        # requested geometry: uniform holes via the deterministic slot fill
        if _place_exact(g, span_live, depth_live, n_holes, rng):
            if not floating or _paint_floating(g, rng):
                return _ensure_texture(g, rng)
        raise ValueError(
            f"could not place requested holes (span {primary_span}, "
            f"depth {primary_depth}, count {count}) on a {h}x{w} grid")
    # unrequested secondary geometry: primary hole at the keyed span/depth,
    # remaining holes as 1x1 perimeter slots (nuisance geometry only)
    limit = (w if edge in ("top", "bottom") else h)
    made = 0
    if corner:
        for pos in (0, limit - corner_side):
            if _paint_hole(g, edge, corner_side, corner_side, pos, at_corner=True):
                made = 1
                break
    else:
        # deterministic first-slot fill: mirrors _cap_after_primary exactly
        for pos in range(1, limit - span_live + 1):
            if _paint_hole(g, edge, span_live, depth_live, pos):
                made = 1
                break
    if not made:
        raise ValueError(
            f"keyed primary hole {primary_span}x{primary_depth} does not "
            f"fit the drawn edge on a {h}x{w} grid")
    spots = ([(0, c) for c in range(1, w - 1)] +
             [(h - 1, c) for c in range(1, w - 1)] +
             [(r, 0) for r in range(1, h - 1)] +
             [(r, w - 1) for r in range(1, h - 1)])
    for r, c in spots:
        if made >= n_holes:
            break
        if _free_with_halo(g, r, c, r, c):
            g[r][c] = 0
            made += 1
    if made < n_holes:
        raise ValueError(
            f"grid {h}x{w} cannot host the keyed hole_count={count}")
    return _ensure_texture(g, rng)


def observe_overrides(grid):
    """Report realized exact semantic axes for the override contract.

    hole_count — number of 4-connected zero components.
    hole_len   — common along-edge span of the edge-touching holes
                 (reported only when uniform, which is guaranteed
                 whenever hole_len was requested).
    hole_depth — common perpendicular depth of the edge-touching holes
                 (same uniformity rule; requested hole_depth forces it).
    """
    comps = _zero_components(grid)
    h, w = len(grid), len(grid[0])
    observed = {"hole_count": len(comps)}
    spans = []
    depths = []
    for cells in comps:
        r1, c1, r2, c2 = _bbox(cells)
        edge = _edge_of((r1, c1, r2, c2), h, w)
        if edge is None:
            continue
        if edge in ("top", "bottom"):
            spans.append(c2 - c1 + 1)
            depths.append(r2 - r1 + 1)
        else:
            spans.append(r2 - r1 + 1)
            depths.append(c2 - c1 + 1)
    if spans and all(s == spans[0] for s in spans):
        observed["hole_len"] = spans[0]
    if depths and all(d == depths[0] for d in depths):
        observed["hole_depth"] = depths[0]
    return observed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of the declared distribution.

    Rectangular grid inside the declared 6..18 x 8..14 envelope; palette
    a 5/7 texture with both colors present plus zeros; 1..8 zero
    components, each a solid rectangle; at most one floating (non
    edge-touching) hole — the declared floating_hole degenerate.
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular with nonzero width"]
    errors = []
    if not (6 <= h <= 18 and 8 <= w <= 14):
        errors.append(f"dims {h}x{w} outside declared envelope 6..18 x 8..14")
    flat = [v for row in grid for v in row]
    if any(v not in (0, 5, 7) for v in flat):
        errors.append("palette must be a 5/7 texture with zero holes")
    if 5 not in flat or 7 not in flat:
        errors.append("background texture must contain both 5 and 7")
    comps = _zero_components(grid)
    if not (1 <= len(comps) <= 8):
        errors.append(f"{len(comps)} zero components outside declared 1..8")
    floating = 0
    for cells in comps:
        bbox = _bbox(cells)
        r1, c1, r2, c2 = bbox
        if (r2 - r1 + 1) * (c2 - c1 + 1) != len(cells):
            errors.append("zero component is not a solid rectangle")
        if _edge_of(bbox, h, w) is None:
            floating += 1
    if floating > 1:
        errors.append(f"{floating} floating holes; at most one is declared")
    return errors
