"""Generator for a2d9d069c7d5 (ARC task 22806e14) -- block-parity cross decision.

Rule (canonical): on an orange(7) background there are exactly two other
colors: the MARKER color (least cells -- always a single 5-cell plus shape)
and the BLOCK color (most cells -- a set of solid squares with side lengths
1..7). For each 4-connected block object, check whether its bounding box
has BOTH dimensions odd (squares with odd side). If odd-sided blocks
outnumber even-sided ones (odd-count > even-count), the plus is KEPT;
otherwise the plus is erased to the background. Either way, the center cell
of every odd-sided block is painted with the marker color.

Canonical demos are always 16x16: one plus, 5..11 solid squares of side
1..7 (1x1 included), and both decision branches witnessed (two erasures,
two keeps). The generator reproduces that envelope and exposes the
keep_cross branch as an exact, grid-observable axis.

Combinatorial axes: grid_h, grid_w, n_blocks, max_block_size (bound),
keep_cross (exact bool), palette_kind, texture.
Branches witnessed: keep (odd > even) and erase (odd <= even) decisions,
1x1 odd blocks (self-marking), large 5..7-sided squares, palette variation.
Degenerates: min_blocks, max_density, one_big_square.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "a2d9d069c7d5"
VERSION = "3.0.0"  # canonical envelope: 5..11 solid squares sized 1..7 + one plus on 16x16-ish grids; self_check; RULE_HASH
TASK_ID = "a2d9d069c7d5"
RULE_HASH = "e2513b1ebd3d"
SUMMARY = (
    "16x16-ish orange(7) grid with exactly two other colors: the MARKER "
    "color (least cells: one 5-cell plus shape) and the BLOCK color (most "
    "cells: 4..12 solid squares, side lengths 1..max_block_size, "
    "canonically 1..7). Rule: if odd-sided blocks outnumber even-sided "
    "ones, the plus is kept, else it is erased to 7; either way every "
    "odd-sided block's center cell is painted with the marker color. "
    "keep_cross (the parity decision) is an exact observable axis; both "
    "branches are witnessed at healthy rates."
)

INVARIANTS = [
    "background is 7; exactly two other colors appear",
    "the least-frequent (marker) color forms exactly one 5-cell plus shape",
    "the most-frequent (block) color forms solid squares of side 1..max_block_size",
    "block cells strictly outnumber marker cells (roles are tie-free)",
    "the rule always changes the grid (odd blocks get marked, or the plus is erased)",
]

PALETTE_KINDS = ("canonical", "broad", "vivid")
DEGENERATE_TEXTURES = ("min_blocks", "max_density", "one_big_square")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "band rng 15..20 (16x16-biased)", "valid": "14..20"},
    "grid_w":         {"type": "int", "default": "band rng 15..20 (16x16-biased)", "valid": "14..20"},
    "n_blocks":       {"type": "int", "default": "band rng 5..11", "valid": "4..12"},
    "max_block_size": {"type": "int", "default": "band 5..7", "valid": "5..7"},
    "keep_cross":     {"type": "bool", "default": "natural mix",
                       "valid": "true|false"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# canonical side-length profile across the four demos (1x1 most common)
_SIZE_WEIGHTS = ((1, 30), (2, 25), (3, 20), (4, 12), (5, 6), (6, 4), (7, 3))
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid, color):
    """Maximal 4-connected components of `color` -> list of (r, c) lists."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == color):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _roles(grid):
    """(marker_color, block_color): least/most frequent non-7 colors."""
    counts = {}
    for row in grid:
        for v in row:
            if v != 7:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return None, None
    marker = min(counts, key=lambda c: (counts[c], c))
    block = max(counts, key=lambda c: (counts[c], -c))
    return marker, block


def _block_parity(grid):
    """(odd_count, even_count) over block-color objects."""
    _marker, block = _roles(grid)
    if block is None:
        return 0, 0
    odd = even = 0
    for cells in _components(grid, block):
        bh = max(r for r, c in cells) - min(r for r, c in cells) + 1
        bw = max(c for r, c in cells) - min(c for r, c in cells) + 1
        if bh % 2 == 1 and bw % 2 == 1:
            odd += 1
        else:
            even += 1
    return odd, even


def _rule_output(grid):
    """Independent Python re-implementation of the canonical oracle:
    keep the plus when odd-sided blocks outnumber even-sided ones (else
    erase it to 7); paint every odd-sided block's center with the marker."""
    marker, block = _roles(grid)
    out = [row[:] for row in grid]
    if marker is None:
        return out
    objs = _components(grid, block)
    odd_objs = []
    for cells in objs:
        bh = max(r for r, c in cells) - min(r for r, c in cells) + 1
        bw = max(c for r, c in cells) - min(c for r, c in cells) + 1
        if bh % 2 == 1 and bw % 2 == 1:
            odd_objs.append(cells)
    keep = len(odd_objs) > len(objs) - len(odd_objs)
    if not keep:
        out = [[7 if v == marker else v for v in row] for row in out]
    for cells in odd_objs:
        r1 = min(r for r, c in cells); r2 = max(r for r, c in cells)
        c1 = min(c for r, c in cells); c2 = max(c for r, c in cells)
        out[(r1 + r2) // 2][(c1 + c2) // 2] = marker
    return out


def _is_plus(cells):
    if len(cells) != 5:
        return False
    r1 = min(r for r, c in cells); r2 = max(r for r, c in cells)
    c1 = min(c for r, c in cells); c2 = max(c for r, c in cells)
    if r2 - r1 != 2 or c2 - c1 != 2:
        return False
    cr, cc = r1 + 1, c1 + 1
    return set(cells) == {(cr, cc), (cr - 1, cc), (cr + 1, cc),
                          (cr, cc - 1), (cr, cc + 1)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared 14..20 envelope; background 7 with exactly two other
    colors; the least-frequent (marker) color is a single 5-cell plus; the
    most-frequent (block) color forms only solid squares (bbox side ==
    cell count side) and strictly outnumbers the marker; and the rule
    visibly fires (odd blocks are center-marked or the plus is erased), so
    identity draws and destructive mutations (broken plus, non-square
    block, merged squares, third color, count tie) are rejected."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 20 or w > 20:
        errs.append(f"outside declared 14..20 envelope: {h}x{w}")
    if h < 14 or w < 14:
        errs.append(f"below 14x14 envelope floor: {h}x{w}")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errs.append("color outside 0..9")
    colors = {v for v in flat if v != 7}
    if len(colors) != 2:
        errs.append(f"expected exactly 2 non-7 colors, got {len(colors)}")
    if errs:
        return errs
    marker, block = _roles(grid)
    counts = {c: flat.count(c) for c in colors}
    if counts[marker] >= counts[block]:
        errs.append(f"marker count {counts[marker]} not strictly below "
                    f"block count {counts[block]} (ambiguous roles)")
    marker_objs = _components(grid, marker)
    if len(marker_objs) != 1 or not _is_plus(marker_objs[0]):
        errs.append("marker color does not form exactly one 5-cell plus shape")
    block_objs = _components(grid, block)
    if not 4 <= len(block_objs) <= 12:
        errs.append(f"block count {len(block_objs)} outside declared 4..12")
    for cells in block_objs:
        bh = max(r for r, c in cells) - min(r for r, c in cells) + 1
        bw = max(c for r, c in cells) - min(c for r, c in cells) + 1
        if bh != bw or len(cells) != bh * bh:
            errs.append(f"block object at ({min(r for r, c in cells)},"
                        f"{min(c for r, c in cells)}) is not a solid square")
        elif bh > 7:
            errs.append(f"block side {bh} exceeds the canonical 1..7 profile")
    if errs:
        return errs
    if _rule_output(grid) == grid:
        errs.append("identity draw: the rule changes nothing")
    return errs


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0001/0002),
    derived from the grid itself: block-object count and the parity
    decision (keep_cross = odd-sided blocks outnumber even-sided ones)."""
    _marker, block = _roles(grid)
    n_blocks = len(_components(grid, block)) if block is not None else 0
    odd, even = _block_parity(grid)
    return {"n_blocks": n_blocks, "keep_cross": odd > even}


def _banded_dim(ctx, overrides, label, lo, hi, valid_lo, valid_hi, p16):
    """Dimension draw biased onto the all-canonical 16 (the demos are always
    16x16); an override must execute exactly on any band (KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    if ctx.draw_rng(label + "_exact16").random() < p16:
        # KRF-0004 provenance: the all-canonical-16 shortcut must still record
        # the realized dimension under its declared axis label (typed
        # degenerate draw; no RNG consumed, distribution unchanged).
        ctx.overrides[label] = 16
        return ctx.draw_int(label, 16, 16)
    return ctx.draw_int(label, lo, hi)


# (marker, block) pairs exactly as witnessed by the four canonical demos
_CANONICAL_PAIRS = ((8, 9), (1, 8), (3, 1), (4, 8))


def _pick_pair(rng, kind):
    """(marker_color, block_color): the exact demo pairs, any pair from the
    canonical color union, or any non-7 pair (generalized extension)."""
    if kind == "canonical":
        return list(rng.choice(_CANONICAL_PAIRS))
    pool = [1, 3, 4, 8, 9] if kind == "broad" else [1, 2, 3, 4, 5, 6, 8, 9]
    return rng.sample(pool, 2)


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an override must execute exactly on any
    band, so it is validated against the full declared range (KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _band_params(difficulty):
    """(dim range, n_blocks range, max square side, p(draw exactly 16)).
    The returned count ALWAYS equals the drawn band count (no silent
    shedding), so the stated ranges are honest; component count (blocks +
    plus) stays inside the canonical 6..12 in every band; dims are biased
    onto the all-canonical 16x16 (0.6), with generalized canvases retained."""
    if difficulty == "easy":
        return (15, 16), (5, 7), 5, 0.6
    if difficulty == "hard":
        return (16, 20), (8, 11), 7, 0.6
    return (15, 17), (6, 9), 6, 0.6     # medium / default: centered on 16x16


def _draw_sizes(rng, n, max_side):
    pool = [(s, w) for s, w in _SIZE_WEIGHTS if s <= max_side]
    total = sum(w for s, w in pool)
    sizes = []
    for _ in range(n):
        u = rng.uniform(0, total)
        for s, wt in pool:
            u -= wt
            if u <= 0:
                sizes.append(s)
                break
    return sizes


def _force_parity(rng, sizes, want_keep, max_side):
    """Greedily flip square sides (odd<->even neighbors within 1..max_side)
    until odd-sided count > even-sided count iff want_keep. Each flip moves
    the (odd - even) gap by two, so this always terminates when n >= 1 and
    both parities are available (max_side >= 2)."""
    sizes = list(sizes)
    for _ in range(4 * len(sizes) + 8):
        odd = sum(1 for s in sizes if s % 2 == 1)
        if (odd > len(sizes) - odd) == want_keep:
            return sizes
        need_more_odd = want_keep
        idxs = list(range(len(sizes)))
        rng.shuffle(idxs)
        flipped = False
        for i in idxs:
            s = sizes[i]
            if need_more_odd and s % 2 == 0:
                cands = [t for t in (s - 1, s + 1) if 1 <= t <= max_side and t % 2 == 1]
            elif not need_more_odd and s % 2 == 1:
                cands = [t for t in (s - 1, s + 1) if 1 <= t <= max_side and t % 2 == 0]
            else:
                continue
            if cands:
                sizes[i] = rng.choice(cands)
                flipped = True
                break
        if not flipped:
            break
    return sizes   # unreachable in practice; caller's self_check is the guard


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            extra = sorted(k for k, v in overrides.items()
                           if k != "texture" and v is not None)
            if extra:
                raise ValueError(
                    f"degenerate texture {texture!r} is a fixed diagnostic "
                    f"layout; it takes no other overrides, got {extra}")
            return _draw_from_degenerate(texture, rng)
        if texture in PALETTE_KINDS:
            if overrides.get("palette_kind") is not None and \
                    overrides["palette_kind"] != texture:
                raise ValueError(
                    f"texture={texture!r} conflicts with "
                    f"palette_kind={overrides['palette_kind']!r}")
            overrides = dict(overrides, palette_kind=texture)
        else:
            raise ValueError(f"unknown texture {texture!r}; valid: "
                             f"{PALETTE_KINDS + DEGENERATE_TEXTURES}")

    dr, br, max_side_default, p16 = _band_params(difficulty)
    h = _banded_dim(ctx, overrides, "grid_h", dr[0], dr[1], 14, 20, p16)
    w = _banded_dim(ctx, overrides, "grid_w", dr[0], dr[1], 14, 20, p16)
    n_blocks = _banded_int(ctx, overrides, "n_blocks", br[0], br[1], 4, 12)
    max_side = _banded_int(ctx, overrides, "max_block_size",
                           max_side_default, max_side_default, 5, 7)

    keep_ov = overrides.get("keep_cross")
    if keep_ov is not None:
        if not isinstance(keep_ov, bool):
            raise ValueError(f"keep_cross must be a bool, got {keep_ov!r}")
        # KRF-0001/0004: record the pinned exact value under its axis label.
        ctx.draw_choice("keep_cross", [True, False])
        want_keep = keep_ov
    else:
        want_keep = None

    palette_kind = (overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    if palette_kind not in ("canonical", "broad", "vivid"):
        raise ValueError(f"unknown palette_kind {palette_kind!r}")
    marker_color, block_color = _pick_pair(rng, palette_kind)

    # Layout: place squares and the plus with >=1 empty cardinal cell
    # between any two pieces (diagonal contact allowed), so same-color
    # squares stay separate objects. Square sizes are redrawn per layout
    # attempt (they are a distribution, not an exact axis); when keep_cross
    # is pinned, parity is forced per attempt. The chosen block count is
    # NEVER silently shed -- the band ranges are honest; only an explicit
    # override combination that cannot fit fails loudly.
    for _layout in range(80):
        sizes = _draw_sizes(rng, n_blocks, max_side)
        # marker has 5 cells; blocks must strictly outnumber it (tie-free)
        while sum(s * s for s in sizes) <= 5:
            sizes[rng.randrange(len(sizes))] += 1
        if want_keep is not None:
            sizes = _force_parity(rng, sizes, want_keep, max_side)
            while sum(s * s for s in sizes) <= 5:
                sizes[rng.randrange(len(sizes))] += 1
        g = full_grid(h, w, 7)
        occupied = []
        ok = True
        for side in sorted(sizes, reverse=True):
            if not _place_square(g, rng, occupied, side, block_color):
                ok = False
                break
        if ok:
            ok = _place_plus(g, rng, occupied, marker_color)
        if ok:
            errs = self_check(g, difficulty=difficulty)
            if not errs:
                if want_keep is None:
                    # KRF-0004 provenance: keep_cross is emergent on the
                    # default path (natural mix). Record the REALIZED parity
                    # under its declared axis label before returning; the
                    # sizes are final at this point, so this is exactly the
                    # value observe_overrides recovers from the grid.
                    realized = (sum(1 for s in sizes if s % 2 == 1)
                                > sum(1 for s in sizes if s % 2 == 0))
                    ctx.overrides["keep_cross"] = realized
                    ctx.draw_choice("keep_cross", [realized])
                return g
    raise ValueError(
        f"could not place {n_blocks} squares + plus on {h}x{w}")


def _place_square(g, rng, occupied, side, color):
    h, w = len(g), len(g[0])
    for _try in range(200):
        r0 = rng.randint(0, h - side)
        c0 = rng.randint(0, w - side)
        cells = {(r0 + dr, c0 + dc) for dr in range(side) for dc in range(side)}
        clash = False
        for other in occupied:
            for (r, c) in cells:
                if (r, c) in other or any((r + dr, c + dc) in other
                                          for dr, dc in _CARD):
                    clash = True
                    break
            if clash:
                break
        if clash:
            continue
        draw_rect(g, r0, c0, side, side, color)
        occupied.append(cells)
        return True
    return False


def _place_plus(g, rng, occupied, color):
    h, w = len(g), len(g[0])
    for _try in range(200):
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        cells = {(r + dr, c + dc) for dr, dc in _PLUS}
        # canonical plus is isolated: its whole 3x3 neighborhood stays clear
        hood = {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        if any(hood & other for other in occupied):
            continue
        for (pr, pc) in cells:
            g[pr][pc] = color
        occupied.append(cells)
        return True
    return False


def _draw_from_degenerate(name, rng):
    """Fixed minimal layouts; every one is a lawful, self_check-clean draw."""
    g = full_grid(16, 16, 7)
    if name == "min_blocks":
        for (r0, c0) in ((1, 1), (1, 5), (5, 1), (5, 5)):
            draw_rect(g, r0, c0, 2, 2, 3)
        _draw_plus(g, 10, 10, 2)
        return g
    if name == "max_density":
        spots = [(1, 1), (1, 5), (1, 9), (1, 13), (5, 1), (5, 13),
                 (9, 1), (9, 5), (9, 9), (9, 13), (13, 1), (13, 13)]
        for r0, c0 in spots:
            draw_rect(g, r0, c0, 2, 2, 4)
        _draw_plus(g, 7, 8, 2)
        return g
    if name == "one_big_square":
        draw_rect(g, 1, 1, 7, 7, 8)
        for (r0, c0) in ((1, 10), (1, 13), (10, 1)):
            draw_rect(g, r0, c0, 1, 1, 8)
        _draw_plus(g, 11, 11, 4)
        return g
    raise ValueError(f"unknown degenerate texture {name!r}")


def _draw_plus(g, r, c, color):
    for dr, dc in _PLUS:
        g[r + dr][c + dc] = color
