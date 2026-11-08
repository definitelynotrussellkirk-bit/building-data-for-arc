"""Generator for 1acc24af.

Rule: a blue(1) wall has gap OPENINGS — 0-pockets under its top edge,
walled in on both sides. Gray(5) pieces are keys: a piece turns red(2)
if it BRANCHES (some cell has 3+ gray neighbors) or if its top rows
(as tall as an opening) match that opening's shape, directly or
mirrored. All other cells stay as they are.

The v2.x distribution predated the current semantic rule: it emitted a
single gray 7x7 patch on a blank grid, so the rule's `(apply min
wall-rows)` crashed on every draw (blacklisted, valid_rate 0.0).
v3.0.0 rebuilds the distribution around the real task structure: a
3-row blue wall with 1-3 controlled opening pockets in the top half,
and gray pieces below covering every rule branch — direct opening
match, mirrored match, taller-piece top-row match, branching, and
near-miss negatives (including rotated, non-mirrored opening copies).

Combinatorial axes: grid_size, wall_top, n_openings, n_match,
n_negative, opening shapes, piece shapes/positions, match style.
Degenerates: no_pieces, solid_wall (both edge-but-valid for the rule;
a wall-less grid crashes it, so no_wall is NOT a declared texture).

v3.1.0 (KRF-0001 follow-up): declared degenerate modes are accepted by
self_check as lawful edge cases (0 gray pieces; a wall with no opening
pockets); every declared single-axis boundary override is accepted
without raising on every difficulty band (difficulty-skewed full-range
draws instead of narrow per-band ranges); the no_wall texture was
dropped (the rule's `(apply min wall-rows)` cannot run on a wall-less
grid, so it is not edge-but-valid).

v3.2.0 (orchestrator semantic review): overrides are honored EXACTLY or
rejected with ValueError — no silent clamps. Free (non-overridden)
parameters adapt around exact requests (grid grows for a high wall_top,
piece counts re-draw within placement capacity); infeasible override
combinations raise. n_openings is exact: shape widths adapt to the grid
so the requested count always fits. Removed the non-executable constant
axes (position_bias, opening_shapes).

v4.0.0 (parametric source review): exact-type override validation now
precedes every draw, unknown/dead controls are rejected, and the lawful
square domain extends through 30x30.  The formerly declared match_style
axis was removed because a requested style was not always observable and
could silently fall back when the sampled openings did not support it.
The semantic analyzer below exposes the realized role counts used by both
tests and authoring evidence.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b6c499e1fa78"
RULE_HASH = "4786a7fd9b5c"  # canonical rule this generator was written against
VERSION = "4.0.0"
TASK_ID = "b6c499e1fa78"
SUMMARY = (
    "0-bg SQUARE grid (size 10-30). Top half holds a BLUE (color 1) "
    "WALL spanning exactly 3 consecutive rows and the full width. The "
    "wall contains 1-3 OPENING pockets: 0-cells with blue somewhere "
    "above them inside the wall rows and blue somewhere on both sides "
    "in their row (gap shapes: dominoes, squares, L/T/S pieces, ...). "
    "Below the wall (>= 1 blank row) sit 3-6 GRAY (color 5) PIECES — "
    "4-connected blobs such as bars, L-shapes, 2x2 blocks, T/plus "
    "clusters. Rule (GRAY KEYS THAT FIT A WALL OPENING OR BRANCH TURN "
    "RED): every gray piece turns RED (color 2) iff (a) it BRANCHES — "
    "some cell has 3+ gray 4-neighbors — or (b) its top rows, taken as "
    "tall as some opening, match that opening's shape directly or "
    "left-right mirrored. All other cells stay unchanged. Net: keys "
    "that fit a lock (or that branch) are marked red; the rest stay "
    "gray."
)

INVARIANTS = [
    "background is 0; inputs use only colors 0, 1 (wall) and 5 (gray keys)",
    "the blue wall spans exactly 3 consecutive rows in the top half (a wall is always present)",
    "normal draws contain 1-3 opening pockets and 3-6 gray pieces below the wall with a blank row between",
    "on normal draws at least one piece is selected (branched or opening-matching) and at least one stays gray",
    "declared degenerate modes are edge-but-valid: no_pieces (no gray keys) and solid_wall (no opening pockets) still let the rule run",
]

HELPFUL_TEXTURES = ("compact", "spread")
DEGENERATE_TEXTURES = ("no_pieces", "solid_wall")

AXES = {
    "grid_size":   {"type": "int", "default": "difficulty-skewed 10..30 (easy low, hard high)", "valid": "10..30"},
    "wall_top":    {"type": "int", "default": "difficulty-skewed 1..12; must leave the 3-row wall in the top half", "valid": "1..12"},
    "n_openings":  {"type": "int", "default": "difficulty-skewed 1..3; exact count, shape widths adapt to grid size", "valid": "1..3"},
    "n_match":     {"type": "int", "default": "difficulty-skewed 1..2", "valid": "1..2"},
    "n_negative":  {"type": "int", "default": "difficulty-skewed 1..3", "valid": "1..3"},
    "texture":     {"type": "str", "default": "none",
                    "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_overrides(overrides):
    """Reject controls that cannot be observed exactly.

    GenCtx's legacy integer draws intentionally coerce values; this generator's
    reviewed contract is stricter.  Booleans, floats and numeric strings must
    not masquerade as exact integer controls, and stale/dead axes must fail
    loudly instead of being ignored.
    """
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    for name in ("grid_size", "wall_top", "n_openings", "n_match", "n_negative"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an exact integer (not bool)")
    texture = overrides.get("texture")
    if texture is not None:
        if type(texture) is not str:
            raise TypeError("texture override must be a string")
        allowed = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
        if texture not in allowed:
            raise ValueError(f"texture must be one of {allowed!r}")


# ---------------------------------------------------------------------------
# Cell-set geometry (mirrors the Racket prelude semantics the rule uses)
# ---------------------------------------------------------------------------

def _normalize(cells):
    """Shift cells so min row = min col = 0; return a sorted tuple."""
    cells = [tuple(x) for x in cells]
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _cells_equal(a, b):
    """Mirror of prelude `cells-equal?` (normalize + set compare)."""
    return _normalize(a) == _normalize(b)


def _flip_lr(cells):
    """Mirror of `normalize-cells (flip-cells-lr ...)`: negate col, renormalize."""
    return _normalize({(r, -c) for r, c in cells})


def _rot90(cells):
    """90-degree rotation (NOT a flip — used for near-miss negative witnesses)."""
    return _normalize({(c, -r) for r, c in cells})


def _orientations(shape):
    outs = set()
    cur = _normalize(shape)
    for _ in range(4):
        outs.add(cur)
        cur = _rot90(cur)
    return sorted(outs)


def _components(cells):
    """4-connected components of a cell set (mirrors prelude `objects`)."""
    remaining = set(cells)
    comps = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        comp = {seed}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARD:
                nb = (r + dr, c + dc)
                if nb in remaining:
                    remaining.discard(nb)
                    comp.add(nb)
                    stack.append(nb)
        comps.append(comp)
    return comps


def _branched(piece):
    """True iff some cell of the piece has 3+ gray 4-neighbors (rule branch (a))."""
    s = set(piece)
    return any(sum(((r + dr, c + dc) in s) for dr, dc in _CARD) >= 3 for r, c in piece)


# ---------------------------------------------------------------------------
# Shape banks
# ---------------------------------------------------------------------------

# Opening pocket shapes (height <= 2 so they fit the two lower wall rows).
_OPENING_BANK = [
    ((0, 0),),                                              # singleton
    ((0, 0), (0, 1)),                                       # h-domino
    ((0, 0), (0, 1), (0, 2)),                               # h-triple
    ((0, 0), (1, 0)),                                       # v-domino
    ((0, 0), (0, 1), (1, 0), (1, 1)),                       # 2x2 square
    ((0, 0), (1, 0), (1, 1)),                               # L triomino
    ((0, 1), (1, 0), (1, 1)),                               # L triomino (mirrored)
    ((0, 0), (0, 1), (1, 0)),                               # L triomino
    ((0, 0), (0, 1), (1, 1)),                               # L triomino
    ((0, 1), (1, 0), (1, 1), (1, 2)),                       # T tetromino (canonical)
    ((0, 0), (0, 1), (1, 1), (1, 2)),                       # S tetromino
    ((0, 1), (0, 2), (1, 0), (1, 1)),                       # Z tetromino
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),       # 2x3 rectangle
]
_OPENING_BANK = sorted({_normalize(s) for s in _OPENING_BANK})
# Openings whose matching key piece is not itself branched (keeps the two
# selection branches cleanly separable on easy draws).
_OPENING_CLEAN = [s for s in _OPENING_BANK if not _branched(s)]

_BASE_BRANCHED = [
    ((0, 0), (0, 1), (0, 2), (1, 1)),                               # T
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),                       # plus
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),               # 2x3
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),                       # P pentomino
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),  # 3x3
]
_BRANCHED_BANK = sorted({o for b in _BASE_BRANCHED for o in _orientations(b)})
assert all(_branched(s) for s in _BRANCHED_BANK)

_BASE_NEUTRAL = [
    ((0, 0),),                                      # singleton
    ((0, 0), (0, 1)),                               # h-domino
    ((0, 0), (0, 1), (0, 2)),                       # h-triple
    ((0, 0), (0, 1), (0, 2), (0, 3)),               # h-bar4
    ((0, 0), (1, 0)),                               # v-domino
    ((0, 0), (1, 0), (2, 0)),                       # v-triple
    ((0, 0), (1, 0), (2, 0), (3, 0)),               # v-bar4
    ((0, 0), (0, 1), (1, 0), (1, 1)),               # 2x2 square
    ((0, 0), (1, 0), (1, 1)),                       # L triomino
    ((0, 0), (1, 0), (2, 0), (2, 1)),               # L tetromino
    ((0, 1), (1, 1), (2, 1), (2, 0)),               # J tetromino
    ((0, 0), (0, 1), (1, 1), (1, 2)),               # S tetromino
    ((0, 1), (0, 2), (1, 0), (1, 1)),               # Z tetromino
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),       # U pentomino
    ((0, 0), (1, 0), (1, 1), (2, 1)),               # staircase
]
_NEUTRAL_BANK = sorted({o for b in _BASE_NEUTRAL for o in _orientations(b)})
assert all(not _branched(s) for s in _NEUTRAL_BANK)


# ---------------------------------------------------------------------------
# Rule mirror (used for construction validation and self_check)
# ---------------------------------------------------------------------------

def _find_openings(g):
    """Opening pockets of the blue wall, mirroring the Racket rule exactly."""
    h = len(g)
    w = len(g[0]) if g else 0
    wall_rows = [r for r in range(h) if any(g[r][c] == 1 for c in range(w))]
    if not wall_rows:
        return []
    rmin, rmax = wall_rows[0], wall_rows[-1]
    opencells = set()
    for r in range(rmin, rmax + 1):
        for c in range(w):
            if g[r][c] != 0:
                continue
            if not any(g[r2][c] == 1 for r2 in range(rmin, r)):
                continue
            if not any(g[r][c2] == 1 for c2 in range(0, c)):
                continue
            if not any(g[r][c2] == 1 for c2 in range(c + 1, w)):
                continue
            opencells.add((r, c))
    openings = []
    for comp in _components(opencells):
        height = max(r for r, _ in comp) - min(r for r, _ in comp) + 1
        openings.append({
            "cells": comp,
            "norm": _normalize(comp),
            "flip": _flip_lr(comp),
            "height": height,
        })
    return openings


def _gray_pieces(g):
    cells = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 5}
    return _components(cells)


def _matches(piece, openings):
    """Rule branch (b): the piece's top op-height rows match an opening or its mirror."""
    top = min(r for r, _ in piece)
    for op in openings:
        tn = _normalize({(r, c) for r, c in piece if r < top + op["height"]})
        if _cells_equal(tn, op["norm"]) or _cells_equal(tn, op["flip"]):
            return True
    return False


def _is_red(piece, openings):
    return _branched(piece) or _matches(piece, openings)


# ---------------------------------------------------------------------------
# Wall / piece construction
# ---------------------------------------------------------------------------
# Draws use ctx.draw_int_diff over the FULL declared axis range so every
# single-axis boundary override is accepted on every difficulty band (the
# band only skews the default sampling). Size-dependent feasibility is then
# enforced with effective caps rather than narrow per-band ranges that would
# raise ValueError on lawful overrides.


def _place_openings(rng, shapes, size, wall_top):
    """Place opening shapes inside the two lower wall rows, separated so the
    pockets cannot merge into one object. Returns absolute cell sets or None."""
    placed = []
    intervals = []  # occupied bbox column ranges (lo, hi) inclusive
    for sh in shapes:
        oh = max(r for r, _ in sh) + 1
        ow = max(c for _, c in sh) + 1
        orow = wall_top + 1 if oh == 2 else wall_top + rng.randint(1, 2)
        ok = False
        for _ in range(60):
            c0 = rng.randint(1, size - 1 - ow)
            lo, hi = c0, c0 + ow - 1
            # keep at least one free column between opening bboxes
            if all(hi + 1 < l2 or lo > h2 + 1 for l2, h2 in intervals):
                intervals.append((lo, hi))
                placed.append({(orow + r, c0 + c) for r, c in sh})
                ok = True
                break
        if not ok:
            return None
    return placed


def _build_wall(g, wall_top, placed, rng):
    """Paint the 3-row blue wall around the carved opening pockets.

    The two lower rows are solid blue except the openings. The top row is
    forced blue above every opening column (the rule's 'blue above' clause)
    and random elsewhere. Extra texture gaps are carved only where they can
    never become openings themselves (no blue above) and never touch an
    opening (which would change its shape)."""
    size = len(g)
    opencells = set().union(*placed) if placed else set()
    for r in (wall_top + 1, wall_top + 2):
        for c in range(size):
            g[r][c] = 0 if (r, c) in opencells else 1
    open_cols = {c for _, c in opencells}
    for c in range(size):
        g[wall_top][c] = 1 if c in open_cols or rng.random() < 0.7 else 0
    adj = set()
    for (r, c) in opencells:
        for dr, dc in _CARD:
            adj.add((r + dr, c + dc))
    for c in range(size):
        if g[wall_top][c] == 0 and (wall_top + 1, c) not in adj and rng.random() < 0.25:
            g[wall_top + 1][c] = 0
        if (g[wall_top][c] == 0 and g[wall_top + 1][c] == 0
                and (wall_top + 2, c) not in adj and rng.random() < 0.2):
            g[wall_top + 2][c] = 0


def _taller_variants(norm_shape):
    """Opening shape + a short downward tail: the piece's top rows still match
    the opening (rule branch (b) on a taller piece) without adding branching."""
    maxr = max(r for r, _ in norm_shape)
    variants = []
    for c in sorted({c for r, c in norm_shape if r == maxr}):
        for tail in (1, 2):
            ext = set(norm_shape) | {(maxr + k, c) for k in range(1, tail + 1)}
            if not _branched(ext):
                variants.append(_normalize(ext))
    return variants


def _piece_capacity(size, wall_top):
    """Conservative piece-slot capacity below the wall: 2-tall lanes packed
    with pieces at most 3 wide separated by one free column. Used only to
    decide override feasibility; the placer itself is free-form."""
    avail = size - (wall_top + 4)
    if avail < 2:
        return 0
    return (avail // 2) * max(1, (size + 1) // 4)


def _resolve_params(ctx, difficulty, tex):
    """Draw all layout parameters over the full declared ranges (difficulty
    only skews free draws). Overrides are honored EXACTLY: when the drawn
    free parameters cannot fit an override, the free parameters adapt
    (larger grid, lower wall, fewer drawn pieces); only a combination whose
    overridden values are mutually infeasible raises ValueError."""
    ov = ctx.overrides
    size_ov = ov.get("grid_size")
    wt_ov = ov.get("wall_top")
    nm_ov = ov.get("n_match")
    nn_ov = ov.get("n_negative")

    if tex == "compact":
        size = ctx.draw_int("grid_size", 10, 14)
    elif tex == "spread":
        size = ctx.draw_int("grid_size", 20, 30)
    else:
        size = ctx.draw_int_diff("grid_size", 10, 30)
    wall_top = ctx.draw_int_diff("wall_top", 1, 12)
    n_openings = ctx.draw_int_diff("n_openings", 1, 3)
    n_match = ctx.draw_int_diff("n_match", 1, 2)
    n_neg = ctx.draw_int_diff("n_negative", 1, 3)

    if wt_ov is None and wall_top > size // 2 - 3:
        wall_top = size // 2 - 3      # free draw adapts to the drawn grid

    def fits(s, w, m, n):
        return 1 <= w <= s // 2 - 3 and _piece_capacity(s, w) >= m + 1 + n

    if fits(size, wall_top, n_match, n_neg):
        return size, wall_top, n_openings, n_match, n_neg
    size_pinned = size_ov is not None or tex in ("compact", "spread")
    if not size_pinned:
        for cand in range(size + 1, 31):
            if fits(cand, wall_top, n_match, n_neg):
                return cand, wall_top, n_openings, n_match, n_neg
    if wt_ov is None:
        for cand in range(wall_top - 1, 0, -1):
            if fits(size, cand, n_match, n_neg):
                return size, cand, n_openings, n_match, n_neg
    if nn_ov is None:
        for cand in range(n_neg - 1, 0, -1):
            if fits(size, wall_top, n_match, cand):
                return size, wall_top, n_openings, n_match, cand
    if nm_ov is None and fits(size, wall_top, 1, n_neg):
        return size, wall_top, n_openings, 1, n_neg
    raise ValueError(
        f"infeasible override combination: grid_size={size_ov} "
        f"wall_top={wt_ov} n_match={nm_ov} n_negative={nn_ov}")


def _opening_shapes(rng, n_op, size, difficulty):
    """Draw n_op opening shapes whose total width (plus one-column gaps)
    provably fits the grid, so the requested opening count is exact."""
    bank = _OPENING_BANK
    clean = _OPENING_CLEAN
    if n_op >= 2:
        max_w = max(1, ((size - 2) - (n_op - 1)) // n_op)
        bank = [s for s in bank if max(c for _, c in s) + 1 <= max_w] or bank
        clean = [s for s in clean if max(c for _, c in s) + 1 <= max_w] or clean
    shapes = []
    for _ in range(n_op):
        if difficulty != "easy" and rng.random() < 0.25:
            shapes.append(rng.choice(bank))   # sometimes branched-shaped locks
        else:
            shapes.append(rng.choice(clean))
    return shapes


def _try_build(ctx, rng, difficulty, tex):
    size, wall_top, n_openings, n_match, n_neg = _resolve_params(ctx, difficulty, tex)

    placed = _place_openings(rng, _opening_shapes(rng, n_openings, size, difficulty),
                             size, wall_top)
    if placed is None:
        return None
    g = full_grid(size, size, 0)
    _build_wall(g, wall_top, placed, rng)
    openings = _find_openings(g)
    if len(openings) != len(placed):
        return None  # construction drift — reject rather than teach a wrong lock

    # --- piece specs, one per rule branch ---------------------------------
    # When the piece region is tight, restrict every bank to pieces that fit
    # the conservative capacity model (<=2 tall, <=3 wide) so the exact
    # requested piece counts remain placeable.
    avail_rows = size - (wall_top + 4)
    tight = avail_rows < 4
    if tight:
        br_bank = [s for s in _BRANCHED_BANK if max(r for r, _ in s) + 1 <= 2]
        neg_bank = [s for s in _NEUTRAL_BANK
                    if max(r for r, _ in s) + 1 <= 2 and max(c for _, c in s) + 1 <= 3]
    else:
        br_bank = _BRANCHED_BANK
        neg_bank = _NEUTRAL_BANK
    specs = []
    # Exact role separation (observe_overrides must recover the requested
    # counts): match witnesses are built only from non-branched openings, the
    # branched witness never matches, negatives neither match nor branch.
    clean_ops = [op for op in openings if not _branched(op["norm"])]
    if not clean_ops:
        return None  # every opening is branch-shaped — redraw the wall
    asym = [op for op in clean_ops if op["flip"] != op["norm"]]
    for i in range(n_match):
        op = rng.choice(clean_ops)
        styles = ["direct", "direct"]
        if asym:
            styles.append("flip")
        tall = [] if tight else _taller_variants(op["norm"])
        if tall:
            styles.append("taller")
        if difficulty == "hard" and i == 1 and asym:
            style = "flip"
        else:
            style = rng.choice(styles)
        if style == "flip":
            specs.append(("match_flip", rng.choice(asym)["flip"]))
        elif style == "taller":
            specs.append(("match_taller", rng.choice(tall)))
        else:
            specs.append(("match_direct", op["norm"]))
    branched_shape = None
    for cand in rng.sample(br_bank, min(12, len(br_bank))):
        if not _matches(cand, openings):
            branched_shape = cand          # red via branching only — clean witness
            break
    if branched_shape is None:
        return None
    specs.append(("branched", branched_shape))
    for j in range(n_neg):
        neg = None
        if difficulty == "hard" and j == 0 and rng.random() < 0.5:
            rot = _rot90(rng.choice(openings)["norm"])
            rot_fits = (max(r for r, _ in rot) + 1 <= (2 if tight else 5)
                        and max(c for _, c in rot) + 1 <= (3 if tight else 5))
            if rot_fits and not _branched(rot) and not _matches(rot, openings):
                neg = rot                  # rotated (not mirrored) lock — near-miss
        if neg is None:
            for cand in rng.sample(neg_bank, min(40, len(neg_bank))):
                if not _matches(cand, openings):
                    neg = cand
                    break
        if neg is None:
            return None
        specs.append(("negative", neg))

    # --- place pieces below the wall, never 4-adjacent (would merge objects)
    row_lo = wall_top + 4   # wall bottom is wall_top+2; keep >= 1 blank row
    tries = 200 if tight else 80
    blocked = set()
    for role, shape in specs:
        ph = max(r for r, _ in shape) + 1
        pw = max(c for _, c in shape) + 1
        if row_lo + ph > size:
            return None
        ok = False
        for _ in range(tries):
            r0 = rng.randint(row_lo, size - ph)
            c0 = rng.randint(0, size - pw)
            cells = {(r0 + r, c0 + c) for r, c in shape}
            if cells & blocked:
                continue
            for (r, c) in cells:
                g[r][c] = 5
            blocked |= cells
            for (r, c) in cells:
                for dr, dc in _CARD:
                    blocked.add((r + dr, c + dc))
            ok = True
            break
        if not ok:
            return None

    # --- final structural verification through the rule mirror ------------
    # The realized role counts must equal the requested ones exactly.
    pieces = _gray_pieces(g)
    roles = [(_matches(p, openings), _branched(p)) for p in pieces]
    if (sum(1 for m, b in roles if m and not b) != n_match
            or sum(1 for m, b in roles if not m and not b) != n_neg
            or sum(1 for m, b in roles if b and not m) != 1
            or any(m and b for m, b in roles)):
        return None
    return g


def _scatter_pieces(g, rng, shapes, row_lo):
    """Gray piece placement for degenerate textures. Returns True only when
    every requested shape was placed (exact piece counts). Pieces are never
    4-adjacent, so each placed shape stays one observable object."""
    size = len(g)
    used = set()
    for shape in shapes:
        ph = max(r for r, _ in shape) + 1
        pw = max(c for _, c in shape) + 1
        for _ in range(60):
            r0 = rng.randint(row_lo, size - ph)
            c0 = rng.randint(0, size - pw)
            cells = {(r0 + r, c0 + c) for r, c in shape}
            if cells & used:
                continue
            for (r, c) in cells:
                g[r][c] = 5
            used |= cells
            for (r, c) in cells:
                for dr, dc in _CARD:
                    used.add((r + dr, c + dc))
            break
        else:
            return False
    return True


def _draw_degenerate(name, ctx, rng):
    """Edge-but-valid modes: the rule still runs on these inputs (identity or
    partial output), so self_check accepts them as lawful edge cases."""
    size = ctx.draw_int_diff("grid_size", 10, 30)
    g = full_grid(size, size, 0)
    wall_top = ctx.draw_int_diff("wall_top", 1, 12)
    if wall_top > size // 2 - 3:
        if ctx.overrides.get("wall_top") is not None:
            raise ValueError(
                f"wall_top={wall_top} infeasible on grid_size={size} "
                f"(degenerate modes keep the wall in the top half)")
        wall_top = size // 2 - 3     # free draw adapts to the drawn grid
    if name == "no_pieces":
        # wall with opening(s) but no gray keys — rule output is the identity
        n_op = ctx.draw_int_diff("n_openings", 1, 3)
        placed = None
        for _ in range(4):
            placed = _place_openings(
                rng, _opening_shapes(rng, n_op, size, None), size, wall_top)
            if placed is not None:
                break
        if placed is None:
            if ctx.overrides.get("n_openings") is not None:
                raise ValueError(
                    f"could not place n_openings={n_op} on grid_size={size}")
            placed = _place_openings(rng, [rng.choice(_OPENING_CLEAN)], size, wall_top)
        _build_wall(g, wall_top, placed or [], rng)
        return g
    if name == "solid_wall":
        # 3-row wall with no opening pockets, plus gray keys below — only a
        # branched piece could recolor, and neutral pieces leave the identity
        n_neg = ctx.draw_int_diff("n_negative", 1, 3)
        for r in (wall_top + 1, wall_top + 2):
            for c in range(size):
                g[r][c] = 1
        for c in range(size):
            g[wall_top][c] = 1 if rng.random() < 0.7 else 0
        shapes = [rng.choice(_NEUTRAL_BANK) for _ in range(n_neg)]
        ok = False
        for _ in range(4):
            trial = [row[:] for row in g]
            if _scatter_pieces(trial, rng, shapes, wall_top + 4):
                g = trial
                ok = True
                break
        if not ok:
            if ctx.overrides.get("n_negative") is not None:
                raise ValueError(
                    f"could not place n_negative={n_neg} pieces on grid_size={size}")
            _scatter_pieces(g, rng, shapes[:1], wall_top + 4)
        return g
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be exact integers (not bool)")
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    tex = overrides.get("texture")
    rng = ctx.draw_rng("layout" if tex is None else f"layout:{tex}")
    if tex in DEGENERATE_TEXTURES:
        # Degenerate modes honor grid_size/wall_top (plus n_openings for
        # no_pieces and n_negative for solid_wall); any other axis override
        # is meaningless there, so reject the combination explicitly.
        honored = {"texture", "grid_size", "wall_top"}
        if tex == "no_pieces":
            honored.add("n_openings")
        if tex == "solid_wall":
            honored.add("n_negative")
        extra = sorted(k for k, v in overrides.items()
                       if v is not None and k not in honored)
        if extra:
            raise ValueError(f"texture={tex} does not honor overrides {extra}")
        return _draw_degenerate(tex, ctx, rng)
    for _attempt in range(40):
        g = _try_build(ctx, rng, difficulty, tex)
        if g is not None:
            return g
    raise RuntimeError(
        f"{TASK_ID}: could not place wall/pieces after 40 attempts")


def observe_overrides(grid) -> dict:
    """Report the realized per-draw values of the exact semantic axes.

    The boundary contract compares these against requested overrides:
    an accepted override must materialize exactly (exact-or-loud). Role
    separation is enforced at construction time, so the counts recover
    the requested composition: n_match = pieces matching an opening
    without branching; n_negative = pieces that neither match nor branch.
    """
    out: dict = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return out
    h, w = len(grid), len(grid[0])
    out["grid_size"] = h
    wall_rows = [r for r in range(h)
                 if any(isinstance(grid[r][c], int) and grid[r][c] == 1 for c in range(w))]
    if wall_rows:
        out["wall_top"] = wall_rows[0]
    openings = _find_openings(grid)
    out["n_openings"] = len(openings)
    pieces = _gray_pieces(grid)
    out["n_match"] = sum(
        1 for p in pieces if _matches(p, openings) and not _branched(p))
    out["n_negative"] = sum(
        1 for p in pieces if not _matches(p, openings) and not _branched(p))
    return out


def analyze(grid) -> dict:
    """Return the realized canonical semantic roles for a lawful input.

    This is intentionally a mirror, not a second generator: it exposes exactly
    which gray components match, branch, satisfy both, or remain negative.
    Review tests use it to prevent a visually plausible draw from silently
    collapsing one of the reference rule's branches.
    """
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0] or any(type(row) is not list or len(row) != len(grid[0])
                                  for row in grid)):
        raise ValueError("grid must be nonempty and rectangular")
    if any(type(cell) is not int for row in grid for cell in row):
        raise ValueError("grid cells must be exact integers")
    openings = _find_openings(grid)
    pieces = _gray_pieces(grid)
    roles = []
    selected_cells = set()
    surviving_gray_cells = set()
    for piece in pieces:
        matched = _matches(piece, openings)
        branched = _branched(piece)
        role = {
            "cells": tuple(sorted(piece)),
            "area": len(piece),
            "matches": matched,
            "branched": branched,
        }
        roles.append(role)
        if matched or branched:
            selected_cells.update(piece)
        else:
            surviving_gray_cells.update(piece)
    return {
        "openings": [tuple(sorted(op["cells"])) for op in openings],
        "opening_shapes": [op["norm"] for op in openings],
        "pieces": roles,
        "n_match": sum(1 for row in roles if row["matches"] and not row["branched"]),
        "n_negative": sum(1 for row in roles if not row["matches"] and not row["branched"]),
        "n_branch_only": sum(1 for row in roles if row["branched"] and not row["matches"]),
        "n_match_and_branch": sum(1 for row in roles if row["branched"] and row["matches"]),
        "selected_cells": tuple(sorted(selected_cells)),
        "surviving_gray_cells": tuple(sorted(surviving_gray_cells)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants for the blue-wall / gray-key samples.

    Accepts the declared degenerate modes as lawful edge cases (the rule
    still runs on them): no_pieces (0 gray pieces) and solid_wall (a wall
    with no opening pockets). Still rejects genuinely broken grids: ragged
    or off-envelope shapes, foreign colors, a MISSING wall (the rule
    crashes on `(apply min wall-rows)` without one), a wall that is not
    exactly 3 rows, pieces invading the wall, and normal-mode draws with
    no red target or no surviving gray negative."""
    errors: list[str] = []
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0] or any(type(row) is not list or len(row) != len(grid[0])
                                  for row in grid)):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h != w:
        errors.append(f"grid should be square, got {h}x{w}")
    if not (10 <= h <= 30):
        errors.append(f"grid size {h} outside declared envelope 10..30")
    if any(type(v) is not int for row in grid for v in row):
        errors.append("grid cells must be exact integers (not bool)")
        return errors
    colors = {v for row in grid for v in row}
    if not colors <= {0, 1, 5}:
        errors.append(f"input may only contain colors 0/1/5, got {sorted(colors)}")
    wall_rows = [r for r in range(h) if any(grid[r][c] == 1 for c in range(w))]
    if not wall_rows:
        errors.append("grid must contain a blue (1) wall (the rule needs one)")
        return errors
    rmin, rmax = wall_rows[0], wall_rows[-1]
    if rmax - rmin != 2:
        errors.append(f"wall must span exactly 3 consecutive rows, got rows {rmin}..{rmax}")
    if rmin < 1:
        errors.append("wall must keep a one-cell top margin")
    if rmin > h // 2 - 3:
        errors.append("wall must remain in the top half")
    openings = _find_openings(grid)
    pieces = _gray_pieces(grid)
    if len(pieces) > 6:
        errors.append(f"expected at most 6 gray pieces, got {len(pieces)}")
    if pieces:
        top_piece_row = min(r for p in pieces for r, _ in p)
        if top_piece_row <= rmax + 1:
            errors.append("gray pieces must sit below the wall with at least one blank row")
    if openings and pieces:
        # Normal-mode draws: selection must actually fire and keep a negative.
        # (solid_wall has no openings and no_pieces has no keys — both are
        # lawful declared edge cases and skip this pedagogy check.)
        reds = [p for p in pieces if _is_red(p, openings)]
        if not reds:
            errors.append("no gray piece is selected (rule would be a no-op)")
        elif len(reds) == len(pieces):
            errors.append("no negative witness: every gray piece is selected")
    return errors
