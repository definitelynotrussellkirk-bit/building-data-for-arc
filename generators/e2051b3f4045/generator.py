"""Generator for arc_puzzle_bank_21_set23_bundle:hard_p04 — area-rank frame assignment.

Rule: hollow gray(5) rectangles are frames; every other component is a
mover. Frames are ranked by interior area, movers by cell count (ties
by lexicographic bbox). On a blank canvas the frames are repainted and
each mover is stamped, shape preserved (normalize-cells + paint-cells),
centered into the same-rank frame's interior. Excess movers are
dropped; excess frames stay empty; oversized movers spill past the
frame (only the grid edge clips the stamp).

Combinatorial axes (5): grid_h, grid_w, n_pairs, palette_kind, texture.
Degenerates (real rule branches): extra_movers (largest mover dropped),
extra_frames (largest frame stays empty), tied_sizes (bbox-lexicographic
tie-break), oversized_mover (stamp spills outside the frame).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "e2051b3f4045"
RULE_HASH = "20152bc23fa9"  # canonical rule this generator was verified against
VERSION = "3.1.0"  # 3.0.0 shape-mover rebuild; 3.1.0 veto repairs: 30%/band exact canonical prior (strict family dims+square frames+[1,3,5]/[1,4,5] movers), silent canvas swap removed (drawn dims kept; structure adapts), exact tied_sizes/oversized_mover predicates, distinct frame areas enforced.
TASK_ID = "e2051b3f4045"

# Declared envelope (shared by AXES and self_check — single source of truth).
H_LO, H_HI = 10, 20
W_LO, W_HI = 12, 22
FAMILY_DIMS = ((12, 14), (13, 15), (12, 16), (13, 16))
FAMILY_FRAMES = (3, 4, 5)  # square outer frames: 3x3, 4x4, 5x5

SUMMARY = (
    "0-bg grid (h 10..20, w 12..22) with 2-4 hollow gray(5) rectangle "
    "frames (distinct interior areas) and 2-4 arbitrary-shaped movers "
    "(distinct non-5 colors, distinct cell counts 1..5; singletons, "
    "dominoes, bars, L/S/T tetrominoes, plus/T/V/W pentominoes). Rule: "
    "rank frames by interior area and movers by size, then stamp each "
    "mover's normalized shape centered into the same-rank frame's "
    "interior on a blank canvas."
)

# Rivals: 'movers stay put' refuted (blank canvas, only mover cells
# move). 'pair by position' refuted by rank reordering. 'pair by color'
# refuted by color-randomized movers. 'solid blocks only' refuted by
# L/plus/T movers in every canonical pair. 'largest mover vanishes when
# frames run out' and 'oversized spills' pinned by degenerate branches.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-4 hollow color-5 rectangle frames, distinct interior areas, mutually separated",
    "2-4 single-color movers, distinct colors (none is 5), distinct cell counts",
    "different-colored components may touch (canonical-true), frames never merge",
    "movers usually fit their frame's interior; some spill onto the border (canonical train pair 2)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTE_POOLS = {
    "default": (1, 2, 3, 4, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 9),
    "cool": (1, 3, 6, 8, 9),
    "varied": (1, 2, 3, 4, 6, 7, 8, 9),
}
DEGENERATE_TEXTURES = ("extra_movers", "extra_frames", "tied_sizes", "oversized_mover")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":       {"type": "int", "default": "rng 10..20 (band-skewed; >=14 when n_pairs=4)",
                     "valid": "10..20"},
    "grid_w":       {"type": "int", "default": "rng 12..22 (band-skewed; >=16 when n_pairs=4)",
                     "valid": "12..22"},
    "n_pairs":      {"type": "int", "default": "rng 2..4 (band-skewed)",
                     "valid": "2..4"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "texture":      {"type": "str", "default": "alias for palette_kind",
                     "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# Small polyomino shape library (normalized cells) grouped by cell count.
# Canonical movers are exactly such arbitrary shapes (L, plus, T, bar...).
SHAPES = {
    1: [[(0, 0)]],
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (1, 0), (1, 1)], [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (1, 0), (2, 0)], [(0, 0), (0, 1), (0, 2)]],
    4: [[(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)]],
    5: [[(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]],
}


def _dims(cells):
    return 1 + max(r for r, _ in cells), 1 + max(c for _, c in cells)


def _free(g, r1, c1, r2, c2):
    """8-neighborhood halo of NON-5 cells (frames must never merge) plus
    bbox overlap with anything. Different-colored components may still
    end up touching, exactly as canonical train pairs 1-2 show."""
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] == 5:
                return False
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if g[r][c] != 0:
                return False
    return True


def _free_mover(g, r1, c1, r2, c2):
    """Movers may touch frames or other movers (canonical-true), but their
    bbox may not overlap any occupied cell (also keeps them out of frame
    interiors)."""
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if g[r][c] != 0:
                return False
    return True


def _is_frame_cells(cells):
    """The rule's frame? predicate: complete hollow rect outline, 3x3+."""
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    h = max(rs) - min(rs) + 1
    w = max(cs) - min(cs) + 1
    if h < 3 or w < 3:
        return False
    if len(cells) != 2 * (h + w) - 4:
        return False
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    return all(r in (r1, r2) or c in (c1, c2) for r, c in cells)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0 or seen[r][c]:
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
                            and grid[nr][nc] == v):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((v, cells))
    return comps


def observe_overrides(grid):
    """Realized exact axes derived from the grid itself (KRF-0002):
    n_pairs = number of hollow gray(5) rectangle frames."""
    n = 0
    for v, cells in _components(grid):
        if v == 5 and _is_frame_cells(cells):
            n += 1
    return {"n_pairs": n}


def _pick_movers(rng, n, *, force_tie=False, max_dim=None):
    """n movers with distinct cell counts; with force_tie, two movers share
    one cell count to fire the rule's bbox tie-break (same shape allowed —
    different colors keep them distinct objects).
    Returns list of (cells, sh, sw) in cell-count order."""
    sizes = [1, 2, 3, 4, 5]
    rng.shuffle(sizes)
    chosen = sorted(sizes[:n])
    if force_tie and n >= 2:
        chosen = sorted(sizes[:n - 1] + [sizes[0]])  # duplicate an in-list size
    movers = []
    for size in chosen:
        options = SHAPES[size]
        if max_dim is not None:
            options = [s for s in options
                       if _dims(s)[0] <= max_dim and _dims(s)[1] <= max_dim]
        cells = rng.choice(options)
        sh, sw = _dims(cells)
        movers.append((cells, sh, sw))
    return movers


def _build_frames(rng, movers, fcap=(6, 6)):
    """One frame per mover, parallel to `movers` (cell-count order):
    interior bbox = mover bbox + padding, with interior AREAS strictly
    increasing so frame rank order == mover rank order. Padding is
    mostly 0..2 (exact fit), with a canonical-rate chance of -1 on one
    side: the stamp then spills onto the frame border, as in canonical
    train pair 2. Frame outer dims are capped by fcap for placement."""
    frames = []
    min_area = 0
    for cells, sh, sw in movers:
        frame = None
        for _ in range(80):
            ph = rng.choice((-1, 0, 0, 0, 1, 2))
            pw = rng.choice((-1, 0, 0, 0, 1, 2))
            ih, iw = sh + ph, sw + pw
            if ih < 1 or iw < 1 or ih > fcap[0] - 2 or iw > fcap[1] - 2:
                continue
            area = ih * iw
            if area > min_area:
                frame = (ih + 2, iw + 2)
                break
        if frame is None:
            ph, pw = 0, 0
            while (sh + ph) * (sw + pw) <= min_area:
                if sw + pw < min(4, fcap[1] - 2):
                    pw += 1
                else:
                    ph += 1
            frame = (sh + ph + 2, sw + pw + 2)
        min_area = (frame[0] - 2) * (frame[1] - 2)
        frames.append(frame)
    return frames


def _place(g, stamp, sh, sw, rng, tries=120, pred=None):
    h, w = len(g), len(g[0])
    ok = pred or _free
    for _ in range(tries):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if not ok(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        stamp(g, r0, c0)
        return True
    return False


def _assemble(h, w, frames, movers, colors, rng):
    """Place frames (color 5, mutually separated) then movers (bbox
    non-overlap; touching is allowed, per canonical)."""
    for _outer in range(60):
        g = full_grid(h, w, 0)
        ok = True
        for fh, fw in frames:
            def stamp(gg, r0, c0, fh=fh, fw=fw):
                draw_frame(gg, r0, c0, r0 + fh - 1, c0 + fw - 1, 5)
            if not _place(g, stamp, fh, fw, rng):
                ok = False
                break
        if not ok:
            continue
        for (cells, sh, sw), color in zip(movers, colors):
            def stamp(gg, r0, c0, cells=cells, color=color):
                for dr, dc in cells:
                    gg[r0 + dr][c0 + dc] = color
            if not _place(g, stamp, sh, sw, rng, pred=_free_mover):
                ok = False
                break
        if ok:
            return g
    return None


def _shelf_pack(h, w, frames, movers, colors):
    """Deterministic guaranteed layout: frames then movers packed onto
    horizontal shelves with 1-cell gaps. Used only when random placement
    fails and dimensions were not requested."""
    g = full_grid(h, w, 0)
    items = [("f", fh, fw, 5, None) for fh, fw in frames]
    items += [("m", sh, sw, color, cells)
              for (cells, sh, sw), color in zip(movers, colors)]
    r, c, shelf_h = 1, 1, 0
    for kind, ih, iw, color, cells in items:
        if c + iw > w:
            r += shelf_h + 1
            c = 1
            shelf_h = 0
        if r + ih > h:
            return None
        if kind == "f":
            draw_frame(g, r, c, r + ih - 1, c + iw - 1, 5)
        else:
            for dr, dc in cells:
                g[r + dr][c + dc] = color
        c += iw + 1
        shelf_h = max(shelf_h, ih)
    return g


def _palette(overrides, ctx, texture):
    tex_kind = texture if texture in PALETTE_KINDS else None
    pk = overrides.get("palette_kind")
    if tex_kind and pk and tex_kind != pk:
        raise ValueError(f"texture {tex_kind!r} conflicts with palette_kind {pk!r}")
    if tex_kind:
        return PALETTE_POOLS[tex_kind]
    return PALETTE_POOLS[ctx.draw_choice("palette_kind", list(PALETTE_KINDS))]


_FAMILY_PROFILES = {
    # Official linked (dims -> mover-shape multiset) profiles, extracted
    # executably from the four canonical inputs (singleton, L3, S4, plus5,
    # T5 in canonical chirality). Sizes/frames: singleton->3x3, mid->4x4,
    # big->5x5.
    (12, 14): ([(0, 0)], [(0, 0), (1, 0), (1, 1)],
               [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]),
    (13, 15): ([(0, 0)], [(0, 0), (1, 0), (1, 1), (2, 1)],
               [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]),
    (12, 16): ([(0, 0)], [(0, 0), (1, 0), (1, 1)],
               [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]),
    (13, 16): ([(0, 0)], [(0, 0), (1, 0), (1, 1)],
               [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]),
}

_CANONICAL_SIGNATURES = frozenset(
    (
        h,
        w,
        tuple((side, side) for side in FAMILY_FRAMES),
        tuple(
            sorted(
                (tuple(sorted(shape)) for shape in shapes),
                key=lambda shape: (len(shape), shape),
            )
        ),
    )
    for (h, w), shapes in _FAMILY_PROFILES.items()
)


def canonical_profile_signature(grid):
    """Extract the complete linked empirical profile from a returned grid.

    Colors and absolute placements are nuisance. Canvas dimensions, ranked
    frame dimensions, and the exact normalized mover-shape multiset remain
    linked so independently recombined official-looking parts do not count.
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return None

    frames = []
    movers = []
    for color, cells in _components(grid):
        if color == 5:
            if not _is_frame_cells(cells):
                return None
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            fh = max(rs) - min(rs) + 1
            fw = max(cs) - min(cs) + 1
            frames.append((fh, fw))
            continue
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        normalized = tuple(sorted((r - r0, c - c0) for r, c in cells))
        movers.append(normalized)

    frames.sort(key=lambda dims: ((dims[0] - 2) * (dims[1] - 2), dims))
    movers.sort(key=lambda shape: (len(shape), shape))
    return h, w, tuple(frames), tuple(movers)


def _canonical_family(ctx, rng, pool):
    """The strict empirical family (veto predicate): one COMPLETE official
    linked profile — exact canonical dims and the exact mover-shape multiset
    — recorded under its keyed axis labels. Colors and placements vary as
    nuisance; the linkage is never sampled independently."""
    key = sorted(_FAMILY_PROFILES)[rng.randrange(len(_FAMILY_PROFILES))]
    h, w = key
    for label, value in (("grid_h", h), ("grid_w", w), ("n_pairs", 3)):
        ctx.overrides[label] = value
        ctx.draw_int(label, value, value)
    shapes = _FAMILY_PROFILES[key]
    movers = [(cells, *_dims(cells)) for cells in shapes]
    frames = [(s, s) for s in FAMILY_FRAMES]
    colors = rng.sample(list(pool), len(movers))
    g = _assemble(h, w, frames, movers, colors, rng)
    if g is None:
        g = _shelf_pack(h, w, frames, movers, colors)
    if g is None:
        raise ValueError(f"canonical family does not fit {h}x{w}")
    return g


def _structure(texture, n_pairs, rng):
    """The (movers, frames) structure for a draw, normal or degenerate;
    n_pairs always counts the 5-frames so the observer stays exact."""
    if texture == "extra_movers":
        movers = _pick_movers(rng, n_pairs + 1)       # largest mover is dropped
        return movers, _build_frames(rng, movers)[:n_pairs]
    if texture == "extra_frames":
        movers = _pick_movers(rng, max(1, n_pairs - 1))
        frames = _build_frames(rng, movers)
        ih, iw = frames[-1][0] - 2, frames[-1][1] - 2  # trailing larger frame stays empty
        frames.append((ih + 2 + 2, iw + 1 + 2))
        return movers, frames
    if texture == "tied_sizes":
        movers = _pick_movers(rng, n_pairs, force_tie=True)
        return movers, _build_frames(rng, movers)
    if texture == "oversized_mover":
        movers = _pick_movers(rng, n_pairs, max_dim=3)
        plus = SHAPES[5][0]
        movers[-1] = (plus, *_dims(plus))              # 3x3 plus, 5 cells
        # EXACT branch predicate: the LARGEST-area frame (rank-paired with
        # the plus) is strictly smaller than the plus bbox in one dim, and
        # every frame interior area stays distinct.
        frames = []
        min_area = 0
        ladder = [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (3, 3), (2, 4), (3, 4)]
        for cells, sh, sw in movers[:-1]:
            for ih, iw in ladder:
                if ih >= sh and iw >= sw and ih * iw > min_area:
                    frames.append((ih + 2, iw + 2))
                    min_area = ih * iw
                    break
            else:
                for ih, iw in ladder:
                    if ih * iw > min_area:
                        frames.append((ih + 2, iw + 2))
                        min_area = ih * iw
                        break
        for iw in range(2, 9):          # interior < 3 in one dim -> plus spills
            for ih in (2, 1):
                if ih * iw > min_area:
                    frames.append((ih + 2, iw + 2))
                    break
            else:
                continue
            break
        return movers, frames
    movers = _pick_movers(rng, n_pairs)
    return movers, _build_frames(rng, movers)


def _compact_structure(texture, n, rng):
    """Last-resort small structure that provably shelf-packs onto the
    declared minimum canvas for its pair count (see _emit)."""
    small = {1: SHAPES[1][0], 2: SHAPES[2][0], 3: SHAPES[3][0],
             4: SHAPES[4][0], 5: SHAPES[5][0]}
    base = [1, 2, 3, 4]
    if texture == "extra_movers":
        sizes = (base + [5])[:n + 1]
        interiors = [(1, 1), (1, 2), (2, 2), (2, 3)][:n]
    elif texture == "extra_frames":
        sizes = base[:max(1, n - 1)]
        interiors = [(1, 1), (1, 2), (2, 2), (2, 3)][:n]
    elif texture == "tied_sizes":
        sizes = ([1, 1] + base)[:n]
        interiors = [(1, 1), (1, 2), (2, 2), (2, 3)][:n]
    elif texture == "oversized_mover":
        sizes = base[:n]
        interiors = [(1, 1), (1, 2), (2, 2), (2, 3)][:n]
    else:
        sizes = base[:n]
        interiors = [(1, 1), (1, 2), (2, 2), (2, 3)][:n]
    movers = [(small[s], *_dims(small[s])) for s in sizes]
    if texture == "oversized_mover":
        movers[-1] = (small[5], *_dims(small[5]))  # 3x3 plus spills on the last frame
    frames = [(ih + 2, iw + 2) for ih, iw in interiors]
    return movers, frames


def _emit(h, w, texture, n_pairs, pool, overrides, rng):
    """Build and place the structure. The DRAWN canvas is never swapped:
    placement failures adapt the unrequested pair count downward on the
    drawn dims, then rebuild a compact structure that provably
    shelf-packs onto the same drawn dims, and raise only when the
    failing constraints were caller-requested."""
    dims_requested = "grid_h" in overrides or "grid_w" in overrides
    count_requested = "n_pairs" in overrides
    n = n_pairs
    while True:
        movers, frames = _structure(texture, n, rng)
        colors = rng.sample(list(pool), len(movers))
        g = _assemble(h, w, frames, movers, colors, rng) or \
            _shelf_pack(h, w, frames, movers, colors)
        if g is not None:
            return g
        if count_requested or dims_requested:
            # requested values stand: rebuild compact and shelf-pack once
            # on the requested canvas; only a genuine conflict may raise
            movers, frames = _compact_structure(texture, n, rng)
            colors = rng.sample(list(pool), len(movers))
            g = _assemble(h, w, frames, movers, colors, rng) or \
                _shelf_pack(h, w, frames, movers, colors)
            if g is not None:
                return g
            raise ValueError(
                f"could not place {len(frames)} frame/mover pairs on a {h}x{w} grid")
        if n <= 2:
            # unrequested count and unrequested dims both bottomed out:
            # compact rebuild on the drawn dims must fit (see floors in
            # generate()); be loud if the guarantee ever breaks
            movers, frames = _compact_structure(texture, n, rng)
            colors = rng.sample(list(pool), len(movers))
            g = _shelf_pack(h, w, frames, movers, colors)
            if g is not None:
                return g
            raise ValueError(
                f"layout failed on drawn {h}x{w} for {len(frames)} pairs")
        n -= 1  # unrequested pair count is nuisance: adapt downward


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    texture = overrides.get("texture")

    # Explicit canonical-family mixture (veto target >=25% in EVERY band):
    # the strict empirical family on exact canonical dims. Default draws
    # only — any requested exact axis takes the general path instead.
    default_draw = not any(
        overrides.get(k) is not None
        for k in ("grid_h", "grid_w", "n_pairs", "palette_kind", "texture"))
    if default_draw:
        family_rng = ctx.draw_rng(f"family|{band}")
        if family_rng.random() < 0.30:
            return _canonical_family(ctx, family_rng, PALETTE_POOLS[
                ctx.draw_choice("palette_kind", list(PALETTE_KINDS))])

    n_pairs = ctx.draw_int_diff("n_pairs", 2, 4)
    # Feasibility floors: 4 pairs need room; when dims were requested the
    # unrequested pair count adapts down instead of rejecting the request.
    if "n_pairs" not in overrides:
        if "grid_h" in overrides and overrides["grid_h"] < 14 and n_pairs > 3:
            n_pairs = 3
        if "grid_w" in overrides and overrides["grid_w"] < 16 and n_pairs > 3:
            n_pairs = 3
    h_min = 14 if n_pairs == 4 else 10
    w_min = 16 if n_pairs == 4 else 12
    h = ctx.draw_int_diff("grid_h", h_min, 20)
    w = ctx.draw_int_diff("grid_w", w_min, 22)
    pool = _palette(overrides, ctx, texture)
    return _emit(h, w, texture, n_pairs, pool, overrides, rng)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of the declared distribution.

    0-bg rectangular grid inside the declared envelope (H_LO..H_HI x
    W_LO..W_HI shared with AXES); 2-4 color-5 components, EVERY one a
    complete hollow rectangle frame with a DISTINCT interior area
    (touching frames would merge and break the rule's frame? predicate,
    and equal-area frames defeat the rank order); 1-5 single-color
    movers with distinct non-5 colors. Different-colored components may
    touch (canonical train pairs 1-2 prove it lawful).
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular with nonzero width"]
    errors = []
    if not (H_LO <= h <= H_HI and W_LO <= w <= W_HI):
        errors.append(f"dims {h}x{w} outside declared envelope "
                      f"{H_LO}..{H_HI} x {W_LO}..{W_HI}")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errors.append("colors must be ints in 0..9")
    comps = _components(grid)
    five_comps = [cells for v, cells in comps if v == 5]
    if not (2 <= len(five_comps) <= 4):
        errors.append(f"{len(five_comps)} color-5 components outside declared 2..4")
    interiors = []
    for cells in five_comps:
        if not _is_frame_cells(cells):
            errors.append("a color-5 component is not a complete hollow frame")
            continue
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        interiors.append((max(rs) - min(rs) - 1) * (max(cs) - min(cs) - 1))
    if len(set(interiors)) != len(interiors):
        errors.append("frame interior areas are not distinct")
    movers = [(v, cells) for v, cells in comps if v != 5]
    if not (1 <= len(movers) <= 5):
        errors.append(f"{len(movers)} movers outside declared 1..5")
    colors = [v for v, _ in movers]
    if len(set(colors)) != len(colors):
        errors.append("mover colors are not distinct")
    return errors
