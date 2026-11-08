"""Generator for e8593010.

Rule: 4-connected components of 0-cells are recolored by size: 1->3, 2->2,
3->1, size >= 4 stays 0.  Non-0 (wall) cells keep their value.

Canonical form: a 10x10 field of one wall color (5) with 15-16 separated
0-pockets of sizes 1..3 (L triominoes dominate; straight triominoes
appear; distinct pockets may touch diagonally, and some official draws
have zero diagonal contacts).  This generator emits that manifold: single
wall color from 4..9 (5-weighted), 8..20 pockets with a guaranteed
size-1/2/3 presence, an exact diagonal_contact branch (true = at least
one diagonal pocket contact, false = pockets are 8-neighbor separated),
plus an optional declared >=4 pocket branch (the rule's stay-0 case).
Textures: with_big, dense, no_diagonal (all rule-valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bb75d495c809"
VERSION = "3.2.2"  # prior fidelity (semantic re-review): the exact official-
# histogram branch is now exactly 30% in every band — an unoverridden big draw
# inside the prior records big_pockets=False, and an explicit big_pockets=True
# bypasses the prior (previously 10% of medium/hard prior draws added a 4..6
# pocket, diluting the exact branch to 26.5%). 3.2.1: pause-wave provenance.
# 3.2.0: exact-histogram prior for the strict component-multiset veto.
# 30% of plain draws redraw an official joint profile (10x10, wall 5, one of the
# four official pocket-size histograms {1:8,2:6,3:2}/{1:7,2:6,3:2}/{1:8,2:5,3:3}/
# {1:6,2:5,3:4}, nothing shrinkable), raising the strict all-band multiset rate
# toward the >=25% target; generalized diagonal/big-pocket branches retained
# outside it. 3.1.1: compact-rule adoption + 8..20 count guard. 3.1.0:
# diagonal_contact axis + canonical counts + self_check teeth. 3.0.0: manifold
# rewrite.
TASK_ID = "bb75d495c809"
RULE_HASH = "804e7e565f32"
SUMMARY = "Recolor each 0-pocket by its size: 1->3, 2->2, 3->1, >=4 stays 0."

INVARIANTS = [
    "nonzero cells are a single wall color in 4..9 (canonical: 5); the wall "
    "color is strictly modal",
    "0-pockets are separated 4-connected components; distinct pockets may "
    "touch diagonally (an exact diagonal_contact axis controls this)",
    "pocket count stays inside the declared 8..20 range",
    "at least two size-3 pockets, three dominoes, and two singletons "
    "(canonical multiset); at most one declared pocket of size 4..6 stays 0",
]

DEGENERATE_TEXTURES = ("with_big", "dense", "no_diagonal")

AXES = {
    "grid_h":      {"type": "int", "default": "band rng 10..12 (10 dominant)",
                    "valid": "10..12"},
    "grid_w":      {"type": "int", "default": "band rng 10..12 (10 dominant)",
                    "valid": "10..12"},
    "n_pockets":   {"type": "int", "default": "band 12..16 easy, 13..17 "
                    "medium, 14..18 hard; capped by grid capacity",
                    "valid": "8..20"},
    "wall_color":  {"type": "color", "default": "5-weighted rng (p 0.5)",
                    "valid": "4..9"},
    "big_pockets": {"type": "bool", "default": "false easy; band rng "
                    "(p 0.1 medium/hard); true = exactly one 4..6-cell pocket",
                    "valid": "true|false"},
    "diagonal_contact": {"type": "bool", "default": "band rng (p 0.75); "
                    "true = at least one diagonal pocket contact, false = "
                    "8-neighbor separation; a non-overridden false yields to "
                    "exact n_pockets requests beyond strict capacity",
                    "valid": "true|false"},
    "texture":     {"type": "str", "default": "none (plain draw)",
                    "valid": "|".join(DEGENERATE_TEXTURES)},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_H = (10, 12)
_VALID_W = (10, 12)
_VALID_POCKETS = (8, 20)
_WALLS = (4, 5, 6, 7, 8, 9)
# Official pocket-size histograms (singles, dominoes, triominoes) — every
# official input has >=6 singletons, >=5 dominoes, >=2 triominoes.
_HISTOGRAMS = ((8, 6, 2), (7, 6, 2), (8, 5, 3), (6, 5, 4))
_HISTOGRAM_PRIOR = 0.3


def _comps0(grid):
    """4-connected components of 0-cells -> list of (r, c) cell lists."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == 0):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _has_diagonal_contact(comps):
    """Whether two distinct pockets touch diagonally (Chebyshev 1, not 4-adj)."""
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            if any(abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1
                   for a in comps[i] for b in comps[j]):
                return True
    return False


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002):
    n_pockets = number of 0-components; wall_color = the single nonzero
    value; big_pockets = whether any 0-component has size >= 4;
    diagonal_contact = whether two distinct pockets touch diagonally."""
    comps = _comps0(grid)
    walls = sorted({v for row in grid for v in row if v != 0})
    return {
        "n_pockets": len(comps),
        "wall_color": walls[0] if len(walls) == 1 else -1,
        "big_pockets": any(len(c) >= 4 for c in comps),
        "diagonal_contact": _has_diagonal_contact(comps),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared envelope (_VALID_H x _VALID_W, matching AXES grid_h/grid_w)
    of colors 0..9; nonzero cells are exactly one wall color in 4..9 and
    strictly modal; at least one 0-pocket of EACH size 1, 2, 3 (every
    recolor branch fires); at most one pocket of size >= 4 and none larger
    than 6."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
    if not (_VALID_H[0] <= h <= _VALID_H[1] and _VALID_W[0] <= w <= _VALID_W[1]):
        errs.append(f"dims {h}x{w} outside the declared envelope "
                    f"{_VALID_H[0]}..{_VALID_H[1]} x {_VALID_W[0]}..{_VALID_W[1]}")
    flat = [v for row in grid for v in row]
    walls = sorted({v for v in flat if v != 0})
    if len(walls) != 1:
        errs.append(f"expected exactly one wall color, found {walls}")
    elif walls[0] not in _WALLS:
        errs.append(f"wall color {walls[0]} outside 4..9")
    elif flat.count(walls[0]) * 2 <= len(flat):
        errs.append("wall color is not modal")
    comps = _comps0(grid)
    if not comps:
        errs.append("no 0-pockets: the oracle has nothing to recolor")
        return errs
    if not (_VALID_POCKETS[0] <= len(comps) <= _VALID_POCKETS[1]):
        errs.append(f"{len(comps)} pockets outside the declared "
                    f"{_VALID_POCKETS[0]}..{_VALID_POCKETS[1]} range")
    sizes = sorted(len(c) for c in comps)
    # Canonical multiset structure (every official pair has >=2 triominoes,
    # >=3 dominoes, >=6 singletons): a flat shuffle of a lawful grid almost
    # never reproduces it.
    if sizes.count(3) < 2:
        errs.append(f"only {sizes.count(3)} pockets of size 3 (< 2)")
    if sizes.count(2) < 3:
        errs.append(f"only {sizes.count(2)} pockets of size 2 (< 3)")
    if sizes.count(1) < 2:
        errs.append(f"only {sizes.count(1)} pockets of size 1 (< 2)")
    big = [s for s in sizes if s >= 4]
    if len(big) > 1:
        errs.append(f"{len(big)} pockets of size >= 4 (at most one declared)")
    if big and big[0] > 6:
        errs.append(f"a 0-pocket has {big[0]} cells (> 6)")
    return errs


def _triomino(rng):
    """L triomino (dominant, canonical) or straight triomino, normalized."""
    if rng.random() < 0.75:
        base = [(0, 0), (1, 0), (1, 1)]
        rot = rng.randrange(4)
        cells = base
        for _ in range(rot):
            cells = [(c, -r) for r, c in cells]
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        return [(r - mr, c - mc) for r, c in cells]
    if rng.random() < 0.5:
        return [(0, 0), (0, 1), (0, 2)]
    return [(0, 0), (1, 0), (2, 0)]


def _blob(rng, size):
    """Random compact 4-connected blob of `size` cells (>=4 branch)."""
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = _DIRS4[rng.randrange(4)]
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _shape_for(rng, size):
    if size == 1:
        return [(0, 0)]
    if size == 2:
        return [(0, 0), (0, 1)] if rng.random() < 0.5 else [(0, 0), (1, 0)]
    if size == 3:
        return _triomino(rng)
    return _blob(rng, size)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")
    if band == "easy":
        n_lo, n_hi, big_p, diag_p = 12, 16, 0.0, 0.7
    elif band == "hard":
        n_lo, n_hi, big_p, diag_p = 14, 18, 0.1, 0.8
    else:
        n_lo, n_hi, big_p, diag_p = 13, 17, 0.1, 0.75

    if texture == "with_big":
        if overrides.get("big_pockets") is not None:
            raise ValueError("texture=with_big conflicts with big_pockets override")
        big = ctx.draw_choice("big_pockets", [True])
    elif overrides.get("big_pockets") is not None:
        big = ctx.draw_choice("big_pockets", [False, True])
    else:
        big = ctx.draw_choice("big_pockets", [True] * int(big_p * 20)
                              + [False] * (20 - int(big_p * 20)))
    if texture == "no_diagonal":
        if overrides.get("diagonal_contact") is not None:
            raise ValueError("texture=no_diagonal conflicts with diagonal_contact override")
        diag = ctx.draw_choice("diagonal_contact", [False])
    elif overrides.get("diagonal_contact") is not None:
        diag = ctx.draw_choice("diagonal_contact", [False, True])
    else:
        diag = ctx.draw_choice("diagonal_contact", [True] * int(diag_p * 20)
                               + [False] * (20 - int(diag_p * 20)))

    # Exact-histogram prior: redraw an official joint profile (10x10, wall 5,
    # one of the four official pocket-size histograms) at a declared exact
    # 30% rate.  Skipped whenever an exact override keys the same axes OR
    # big_pockets is explicitly True (the generalized big branch lives
    # outside the prior); an unoverridden big draw inside the prior is
    # recorded False so the advertised branch is exactly the official
    # histogram branch in every band.
    hist = None
    pinned_axes = {"grid_h", "grid_w", "wall_color", "n_pockets"}
    if (not (pinned_axes & {k for k, v in overrides.items() if v is not None}
             or texture
             or (overrides.get("big_pockets") is not None
                 and overrides["big_pockets"]))
            and rng.random() < _HISTOGRAM_PRIOR):
        hist = _HISTOGRAMS[rng.randrange(len(_HISTOGRAMS))]
        if big and overrides.get("big_pockets") is None:
            big = ctx.draw_choice("big_pockets", [False])

    # Exact overrides execute over the full declared valid range (or reject
    # loudly); band ranges apply to plain draws only.  Every exact axis keeps
    # keyed GenCtx provenance, including prior-pinned and texture-forced
    # values (pause-wave default-path audit).
    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", *_VALID_H)
    elif hist:
        h = ctx.draw_int("grid_h", 10, 10)
    else:
        h = ctx.draw_choice("grid_h", [10, 10, 10, 11, 12])
    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", *_VALID_W)
    elif hist:
        w = ctx.draw_int("grid_w", 10, 10)
    else:
        w = ctx.draw_choice("grid_w", [10, 10, 10, 11, 12])
    if overrides.get("wall_color") is not None:
        wall = ctx.draw_color("wall_color", exclude={0, 1, 2, 3})
    elif hist:
        wall = ctx.draw_choice("wall_color", [5])
    else:
        wall = ctx.draw_choice("wall_color", [5] * 5 + [4, 6, 7, 8, 9])
    # Strict 8-neighbor capacity is what a no-diagonal layout can actually
    # host (singletons block ~7 cells each with their halo).  With a declared
    # big pocket the band draw is capped one lower so eff_n = n+1 can never
    # force a flip against an overridden diagonal_contact=False.
    strict_cap = max(_VALID_POCKETS[0], (h * w) // 7)
    capacity = (max(_VALID_POCKETS[0], (h * w) // 5) if diag
                else max(_VALID_POCKETS[0], strict_cap - (1 if big else 0)))
    capacity = max(_VALID_POCKETS[0], capacity)
    # Under the histogram prior the official multiset pins the count (the
    # band draw is skipped); the big branch adds one extra pocket.
    if hist:
        n_pockets = ctx.draw_int("n_pockets", hist[0] + hist[1] + hist[2],
                                 hist[0] + hist[1] + hist[2])
    elif texture == "dense":
        n_pockets = (ctx.draw_int("n_pockets", *_VALID_POCKETS)
                     if overrides.get("n_pockets") is not None
                     else ctx.draw_int("n_pockets", min(_VALID_POCKETS[1], capacity),
                                       min(_VALID_POCKETS[1], capacity)))
    elif overrides.get("n_pockets") is not None:
        n_pockets = ctx.draw_int("n_pockets", *_VALID_POCKETS)
    else:
        cap_hi = min(n_hi, max(_VALID_POCKETS[0], capacity))
        n_pockets = ctx.draw_int("n_pockets", min(n_lo, cap_hi), cap_hi)
    # Capacity coupling: an exact n_pockets request always wins.  When it
    # exceeds the strict 8-neighbor capacity of the grid, a non-overridden
    # diagonal_contact flips to True (denser packing); if diagonal_contact
    # was itself explicitly set False the combination rejects loudly.
    eff_n = n_pockets + (1 if big else 0)
    if not diag and eff_n > strict_cap:
        if (overrides.get("diagonal_contact") is not None
                and overrides.get("n_pockets") is not None):
            raise ValueError(
                f"diagonal_contact=False cannot host {eff_n} pockets on "
                f"a {h}x{w} grid")
        if texture == "no_diagonal" and overrides.get("n_pockets") is not None:
            raise ValueError(
                f"texture=no_diagonal cannot host {eff_n} pockets on a "
                f"{h}x{w} grid")
        if overrides.get("diagonal_contact") is None and texture != "no_diagonal":
            # A naturally drawn False may flip to dense packing (provenance-
            # kept) — exact n_pockets always wins.
            diag = ctx.draw_choice("diagonal_contact", [True])
        elif big and overrides.get("big_pockets") is None and texture != "with_big":
            # diagonal_contact is forced False: the natural big branch yields
            # (provenance-kept); 15-16 strict-separated pockets still fit with
            # retries, while an exact big=True + diagonal_contact=False
            # combination beyond capacity fails loudly at placement.
            big = ctx.draw_choice("big_pockets", [False])
            eff_n = n_pockets

    # Pocket sizes: canonical multiset guarantees (>=2 triominoes, >=3
    # dominoes, >=3 singletons — every official pair has them), then weighted
    # extras; one 4..6 pocket when the declared branch is on.  The big and
    # guaranteed pockets are placed FIRST so crowding fallbacks can never
    # silently drop a declared/guaranteed branch (KRF-0002).  Under the
    # exact-histogram prior the whole size multiset is guaranteed (nothing
    # may shrink).
    head, tail = [], []
    if big:
        head.append(rng.randint(4, 6))
    if hist:
        head += [1] * hist[0] + [2] * hist[1] + [3] * hist[2]
        rng.shuffle(head)
        n_pockets = len(head)
    else:
        head += [3, 3, 2, 2, 2, 1, 1, 1]
        while len(head) + len(tail) < n_pockets:
            tail.append(rng.choice([1, 1, 1, 2, 2, 3]))
        rng.shuffle(tail)
    sizes = (head + tail)[:n_pockets]

    for _attempt in range(40):
        g = _fill(rng, h, w, wall, sizes, diag, n_guaranteed=len(head))
        if g is not None:
            if diag and not _has_diagonal_contact(_comps0(g)):
                continue            # exact axis: true must show a contact
            return g
    raise ValueError(
        f"cannot place {n_pockets} separated pockets (diagonal_contact="
        f"{diag}) on a {h}x{w} grid")


def _fill(rng, h, w, wall, sizes, diag, *, n_guaranteed):
    """One placement attempt; None when a pocket cannot be placed.  Only
    tail pockets (index >= n_guaranteed) may shrink to singletons under
    crowding — the big and size-1/2/3 guarantee pockets never shrink."""
    g = full_grid(h, w, wall)
    blocked = [[False] * w for _ in range(h)]
    halo = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)] \
        if not diag else list(_DIRS4)

    def try_place(shape):
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h or sw > w:
            return False
        positions = [(rng.randint(0, h - sh), rng.randint(0, w - sw))
                     for _ in range(60)]
        positions += [(t, l) for t in range(0, h - sh + 1)
                      for l in range(0, w - sw + 1)]
        for top, left in positions:
            pts = [(top + r, left + c) for r, c in shape]
            if any(blocked[r][c] for r, c in pts):
                continue
            for r, c in pts:
                g[r][c] = 0
                for dr, dc in halo:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        blocked[nr][nc] = True
                blocked[r][c] = True
            return True
        return False

    for i, sz in enumerate(sizes):
        if try_place(_shape_for(rng, sz)):
            continue
        # Crowded grids: only non-guaranteed tail pockets may shrink to
        # singletons (sizes are generator-chosen, never an exact claim).
        if i >= n_guaranteed and sz != 1 and try_place([(0, 0)]):
            continue
        return None
    return g
