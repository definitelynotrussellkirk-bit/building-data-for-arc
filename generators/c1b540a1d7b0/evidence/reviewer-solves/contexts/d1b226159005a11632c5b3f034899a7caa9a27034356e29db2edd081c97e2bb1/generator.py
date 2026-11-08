"""Generator for 150deff5 -- gray blob decomposed into 2x2 rooms and 3-cell arms.

Rule (canonical, semantic): a gray(5) blob is made of 2x2 "rooms" joined by
1-wide arms.  Tip arms: a degree-1 cell grows a straight 3-cell run toward
its only neighbor.  Bridge arms: a thin cell (in no 2x2) not yet covered
grows a 3-cell run toward a thick (in-2x2) neighbor, tie-break up/left/
down/right.  Arm cells recolor to red(2) -- including room cells the run
overlaps -- every other gray cell recolors to cyan(8).

Canonical demos are compact single blobs on small grids (8-9 x 9-11):
2x2-ish rooms linked by short bridges, dangling 3-cell arms, and 1-cell
tips.  This generator builds exactly that grammar: rooms on a loose lattice
linked by 1-2-cell bridges, plus deliberate dangling arms/tips, then
validates every draw with a Python mirror of the oracle (single component,
room count == output 8-regions, degree-1 count == placed tips, both output
colors present).  An earlier version of this module stamped windows of the
old memorized radius-2 table; the canonical rule has since been re-solved
compositionally and the distribution is rebuilt here.

Combinatorial axes (5): grid_h, grid_w, n_rooms, n_tips, texture.
Branches witnessed: multi-room blobs, bridge-linked rooms, dangling 3-cell
arms, 1-cell tips, 2x2 and 2x3 rooms, tip-arm overwrites of room-edge
cells, and the held-out T-cap whose two leaves are degree-1 tips.
Degenerates (crash-free for the total rule): empty, all_five, single_room.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c1b540a1d7b0"
VERSION = "3.3.0"
TASK_ID = "c1b540a1d7b0"
RULE_HASH = "e925582a7078"
SUMMARY = ("Single gray(5) blob of 2x2 rooms linked by bridges plus dangling "
           "arms/tips; oracle recolors 3-cell arm runs to 2 and remaining "
           "gray to 8.")

# Rivals refuted by construction: 'recolor by local density only' is refuted
# by arm runs overwriting room-edge cells (a cell in a 2x2 can turn red);
# 'every 5-cell in a 2x2 turns 8' is refuted by those same overwrites;
# 'thin cells turn 2' is refuted by dangling bars whose far cells sit among
# thick rooms; 'output is input' is refuted on every normal draw (>=2 red
# and >=2 cyan cells guaranteed by mirror validation).
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "cells are 0 (bg) or 5 (blob)",
    "5-cells form 1..2 4-connected components (canonical train[2] has two blobs)",
    "the blob decomposes into 2x2 rooms joined by 1-wide bridges/arms",
    "every 3-cell arm run is straight (tip arms toward the only neighbor, "
    "bridge arms toward the up/left/down/right-first thick neighbor)",
    "grid envelope h 6..14 x w 8..16 (canonical 8..9 x 9..11)",
]

DEGENERATE_TEXTURES = ("empty", "all_five", "single_room")

AXES = {
    "grid_h":  {"type": "int", "default": "band rng 6..14", "valid": "6..14"},
    "grid_w":  {"type": "int", "default": "band rng 8..16", "valid": "8..16"},
    "n_rooms": {"type": "int", "default": "band 1..4", "valid": "1..5"},
    "n_tips":  {"type": "int", "default": "band 0..2", "valid": "0..4"},
    "texture": {"type": "str", "default": "none",
                "valid": "none|" + "|".join(DEGENERATE_TEXTURES)},
}

_DIRS = ((-1, 0), (0, -1), (1, 0), (0, 1))


# --------------------------------------------------------------------------
# Python mirror of the canonical oracle (validation only -- outputs for
# training always come from the Racket rule).
# --------------------------------------------------------------------------

def rule_mirror(g):
    """Exact port of the canonical rooms+arms rule: returns the output grid."""
    h, w = len(g), len(g[0])

    def sh(a, b):
        return 0 <= a < h and 0 <= b < w and g[a][b] == 5

    def in2x2(a, b):
        for da in (-1, 0):
            for db in (-1, 0):
                if (sh(a + da, b + db) and sh(a + da, b + db + 1)
                        and sh(a + da + 1, b + db) and sh(a + da + 1, b + db + 1)):
                    return True
        return False

    red = set()

    def add_arm(a, b, da, db):
        for k in range(3):
            if sh(a + da * k, b + db * k):
                red.add((a + da * k, b + db * k))

    for a in range(h):
        for b in range(w):
            if sh(a, b):
                nb = [d for d in _DIRS if sh(a + d[0], b + d[1])]
                if len(nb) == 1:
                    add_arm(a, b, *nb[0])
    for a in range(h):
        for b in range(w):
            if sh(a, b) and not in2x2(a, b) and (a, b) not in red:
                for da, db in _DIRS:
                    if sh(a + da, b + db) and in2x2(a + da, b + db):
                        add_arm(a, b, da, db)
                        break
    return [[2 if (r, c) in red else (8 if g[r][c] == 5 else g[r][c])
             for c in range(w)] for r in range(h)]


def _components5(g):
    """4-connected components of value-5 cells."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 5 or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and g[nr][nc] == 5):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _degree1_cells(g):
    h, w = len(g), len(g[0])
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 5:
                deg = sum(1 for dr, dc in _DIRS
                          if 0 <= r + dr < h and 0 <= c + dc < w
                          and g[r + dr][c + dc] == 5)
                if deg == 1:
                    out.append((r, c))
    return out


def _regions8(g):
    """4-connected components of value-8 cells (post-rule room regions)."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    n = 0
    for r in range(h):
        for c in range(w):
            if g[r][c] != 8 or seen[r][c]:
                continue
            n += 1
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                for dr, dc in _DIRS:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and g[nr][nc] == 8):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
    return n


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): n_rooms as the number of
    8-regions in the mirrored oracle output (construction keeps rooms
    non-merging, so this equals placed rooms), n_tips as the number of
    degree-1 gray cells (construction leaves only deliberate tips)."""
    out = rule_mirror(grid)
    return {"n_rooms": _regions8(out), "n_tips": len(_degree1_cells(grid))}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all four canonical pairs
    satisfy them): rectangular grid over {0,5} inside the declared envelope
    h 6..14 x w 8..16; 5-cells form 1..2 4-connected components (canonical
    train[2] has two blobs) or none (the exact declared 'empty' texture).
    Ordinary instances contain both answer colors and their cells outside
    2x2 rooms form straight runs or the held-out T-cap. The only answer-free
    nonempty controls are the exact all-five texture and a lawful pure
    2x2/2x3/3x2 room. Rejects foreign colors, malformed arms, 3+ scattered
    components, and out-of-envelope dims."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    bad = sorted({v for row in grid for v in row} - {0, 5})
    if bad:
        errs.append(f"colors outside {{0,5}}: {bad}")
        return errs
    if not 6 <= h <= 14:
        errs.append(f"height {h} outside declared envelope 6..14")
    if not 8 <= w <= 16:
        errs.append(f"width {w} outside declared envelope 8..16")
    comps = _components5(grid)
    if len(comps) > 2:
        errs.append(f"blob is {len(comps)} disconnected components (canonical allows 1..2)")
    if errs:
        return errs
    # The two uniform degenerates are fixed 8x10 layouts, not permission for
    # arbitrary uniform grids throughout the declared size envelope.
    if not comps:
        if (h, w) != (8, 10):
            errs.append("uniform-zero grid is only lawful as the fixed 8x10 "
                        "'empty' texture")
        return errs
    if sum(len(c) for c in comps) == h * w:
        if (h, w) != (8, 10):
            errs.append("uniform-five grid is only lawful as the fixed 8x10 "
                        "'all_five' texture")
        return errs

    # A single pure room is a lawful n_rooms=1,n_tips=0 edge case. All other
    # nondegenerate instances must exercise both answer branches.
    if len(comps) == 1:
        cellset = set(comps[0])
        rs = {r for r, _ in cellset}
        cs = {c for _, c in cellset}
        if (len(cellset), len(rs), len(cs)) in {
                (4, 2, 2), (6, 2, 3), (6, 3, 2)}:
            if all((r, c) in cellset for r in range(min(rs), max(rs) + 1)
                   for c in range(min(cs), max(cs) + 1)):
                return errs

    reds, cyans = _mirror_totals(grid)
    if reds == 0 or cyans == 0:
        errs.append("normal room+arm grid must exercise both oracle colors "
                    f"(red={reds}, cyan={cyans})")
        return errs

    from collections import deque
    for cells in comps:
        cellset = set(cells)
        room = set()
        for r, c in cells:
            block = [(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)]
            if all(b in cellset for b in block):
                room.update(block)
        if not room:
            errs.append("blob has no 2x2 room; the room+arm grammar requires "
                        "at least one solid 2x2 room per component")
            continue
        # A component that IS one solid square of side >= 3 is not the
        # room+arm grammar (rooms are 2x2-ish). Larger canonical blobs may
        # still CONTAIN 3x3-solid neighborhoods — only the standalone form
        # is an impostor.
        k = int(len(cellset) ** 0.5)
        if k >= 3 and k * k == len(cellset):
            rows_ = {r for r, _ in cellset}
            cols_ = {c for _, c in cellset}
            if len(rows_) == k and len(cols_) == k:
                errs.append(f"blob is exactly a solid {k}x{k} square, not a "
                            "room+arm structure")
                continue
        dist = {rc: 0 for rc in room}
        dq = deque(room)
        while dq:
            r, c = dq.popleft()
            for dr, dc in _DIRS:
                nb = (r + dr, c + dc)
                if nb in cellset and nb not in dist:
                    dist[nb] = dist[(r, c)] + 1
                    dq.append(nb)
        far = [nb for nb in cellset if dist.get(nb, 99) > 3]
        if far:
            errs.append(f"arm/tip cell(s) beyond distance 3 from any room: "
                        f"{far[:2]}")
            continue

        # Remove every cell supported by at least one 2x2 room. Each residual
        # component must be either a 1..3-cell straight bridge/dangling run or
        # the held-out four-cell T-cap. Merely being close to a room is too
        # weak: it admits bent and forked pseudo-arms that generate() never
        # constructs and that are absent from the canonical grammar.
        thin = cellset - room
        thin_seen = set()
        for start in thin:
            if start in thin_seen:
                continue
            stack = [start]
            thin_seen.add(start)
            segment = set()
            while stack:
                here = stack.pop()
                segment.add(here)
                for dr, dc in _DIRS:
                    nxt = (here[0] + dr, here[1] + dc)
                    if nxt in thin and nxt not in thin_seen:
                        thin_seen.add(nxt)
                        stack.append(nxt)
            if not _valid_thin_segment(segment, room):
                errs.append("thin cells are not a straight 1..3-cell run or "
                            f"held-out T-cap: {sorted(segment)[:5]}")
    return errs


def _valid_thin_segment(segment, room):
    """Whether one non-room component has canonical arm/bridge geometry."""
    if not segment:
        return True
    contacts = [
        (cell, (cell[0] + dr, cell[1] + dc))
        for cell in segment
        for dr, dc in _DIRS
        if (cell[0] + dr, cell[1] + dc) in room
    ]
    if not contacts:
        return False

    if len(segment) == 1:
        directions = {
            (thick[0] - cell[0], thick[1] - cell[1])
            for cell, thick in contacts
        }
        return (
            len(contacts) == 1
            or len(contacts) == 2
            and len(directions) == 2
            and all((-dr, -dc) in directions for dr, dc in directions)
        )

    rows = {r for r, _ in segment}
    cols = {c for _, c in segment}
    if len(segment) <= 3 and (len(rows) == 1 or len(cols) == 1):
        if len(rows) == 1:
            ordered = sorted(segment, key=lambda p: p[1])
            outward = {
                ordered[0]: (0, -1),
                ordered[-1]: (0, 1),
            }
        else:
            ordered = sorted(segment, key=lambda p: p[0])
            outward = {
                ordered[0]: (-1, 0),
                ordered[-1]: (1, 0),
            }
        if not 1 <= len(contacts) <= 2:
            return False
        seen_ends = set()
        for cell, thick in contacts:
            direction = (thick[0] - cell[0], thick[1] - cell[1])
            expected = outward.get(cell)
            if expected is None or direction != expected:
                return False
            seen_ends.add(cell)
        return len(seen_ends) == len(contacts)

    if len(segment) == 4:
        degree = {
            cell: sum(
                (cell[0] + dr, cell[1] + dc) in segment
                for dr, dc in _DIRS
            )
            for cell in segment
        }
        centers = [cell for cell, value in degree.items() if value == 3]
        leaves = {cell for cell, value in degree.items() if value == 1}
        if len(centers) != 1 or len(leaves) != 3 or len(contacts) != 1:
            return False
        center = centers[0]
        leaf, thick = contacts[0]
        if leaf not in leaves:
            return False
        stem_direction = (leaf[0] - center[0], leaf[1] - center[1])
        return thick == (
            leaf[0] + stem_direction[0],
            leaf[1] + stem_direction[1],
        )
    return False


# --------------------------------------------------------------------------
# Blob construction
# --------------------------------------------------------------------------

def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute exactly on any band, KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _room_cells(r0, c0, rh, rw):
    return {(r, c) for r in range(r0, r0 + rh) for c in range(c0, c0 + rw)}


def _edge_cells(room, side):
    rs = [r for r, _ in room]
    cs = [c for _, c in room]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if side == "L":
        return [(r, c0) for r in range(r0, r1 + 1)], (0, -1)
    if side == "R":
        return [(r, c1) for r in range(r0, r1 + 1)], (0, 1)
    if side == "U":
        return [(r0, c) for c in range(c0, c1 + 1)], (-1, 0)
    return [(r1, c) for c in range(c0, c1 + 1)], (1, 0)


def _build_blob(rng, h, w, n_rooms, n_tips, forbidden=frozenset(),
                allow_pure=False):
    """Union of rooms + bridges + dangling arms/tips as a grid, or None when
    no layout passes the mirror validation. New attachments may only touch
    the room they grow from (keeps components and 8-region counts exact).
    `forbidden` cells must stay empty and untouched (two-blob separation).
    allow_pure permits a lone armless room (explicit n_tips=0, n_rooms=1)."""
    for _attempt in range(120):
        cells = set()
        rooms = []
        ok = True

        def free(cell_set):
            return all(0 <= r < h and 0 <= c < w and (r, c) not in cells
                       and (r, c) not in forbidden for r, c in cell_set)

        def touches_only(new_cells, allowed):
            """Every cardinal neighbor of new_cells that is occupied (by the
            blob or a forbidden cell) must lie inside `allowed`."""
            for (r, c) in new_cells:
                for dr, dc in _DIRS:
                    n = (r + dr, c + dc)
                    if n in new_cells:
                        continue
                    if (n in cells or n in forbidden) and n not in allowed:
                        return False
            return True

        def add_room(r0, c0):
            rh, rw = (2, 2) if rng.random() < 0.7 else rng.choice(((2, 3), (3, 2)))
            room = _room_cells(r0, c0, rh, rw)
            if not free(room) or not touches_only(room, room):
                return None
            cells.update(room)
            rooms.append(room)
            return room

        first = add_room(rng.randint(0, max(0, h - 2)), rng.randint(0, max(0, w - 2)))
        if first is None:
            continue
        # attach remaining rooms via 1-2-cell bridges
        for _ in range(n_rooms - 1):
            placed = False
            for _try in range(40):
                base = rng.choice(rooms)
                side = rng.choice(("L", "R", "U", "D"))
                edge, (dr, dc) = _edge_cells(base, side)
                er, ec = rng.choice(edge)
                gap = rng.randint(1, 2)
                bridge = {(er + dr * k, ec + dc * k) for k in range(1, gap + 1)}
                for (rh, rw) in (((2, 2), (2, 3), (3, 2))
                                 if rng.random() < 0.7 else ((2, 3), (3, 2), (2, 2))):
                    # room edge nearest the base sits gap cells away from (er, ec)
                    nr0 = (er + gap + 1) if dr == 1 else \
                          (er - gap - rh) if dr == -1 else er - (rh - 1) // 2
                    nc0 = (ec + gap + 1) if dc == 1 else \
                          (ec - gap - rw) if dc == -1 else ec - (rw - 1) // 2
                    cand = _room_cells(nr0, nc0, rh, rw)
                    new = bridge | cand
                    if free(new) and touches_only(new, base | cand):
                        cells.update(new)
                        rooms.append(cand)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        # Dangling straight arms contribute one degree-1 tip. A T-cap
        # contributes two tips and generalizes the distinctive held-out
        # topology instead of leaving it solely to the canonical bitmap prior.
        tips_left = n_tips
        while tips_left:
            placed = False
            for _try in range(40):
                base = rng.choice(rooms)
                side = rng.choice(("L", "R", "U", "D"))
                edge, (dr, dc) = _edge_cells(base, side)
                er, ec = rng.choice(edge)
                use_t_cap = tips_left >= 2 and rng.random() < 0.25
                if use_t_cap:
                    pr, pc = -dc, dr
                    stem = (er + dr, ec + dc)
                    center = (er + 2 * dr, ec + 2 * dc)
                    run = {
                        stem,
                        center,
                        (center[0] + pr, center[1] + pc),
                        (center[0] - pr, center[1] - pc),
                    }
                else:
                    length = rng.choice((1, 3))
                    run = {
                        (er + dr * k, ec + dc * k)
                        for k in range(1, length + 1)
                    }
                if free(run) and touches_only(run, base):
                    cells.update(run)
                    placed = True
                    tips_left -= 2 if use_t_cap else 1
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        g = [[5 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]
        out = rule_mirror(g)
        reds = sum(1 for row in out for v in row if v == 2)
        cyans = sum(1 for row in out for v in row if v == 8)
        if _regions8(out) == n_rooms and len(_degree1_cells(g)) == n_tips:
            if reds >= 2 and cyans >= 2:
                return g
            if allow_pure and reds == 0 and cyans >= 2:
                return g
    return None


def _mirror_totals(g):
    """(reds, cyans) of the rule-mirror output — the answer-bearing totals."""
    out = rule_mirror(g)
    reds = sum(1 for row in out for v in row if v == 2)
    cyans = sum(1 for row in out for v in row if v == 8)
    return reds, cyans


def profile_signature(grid):
    """Complete linked semantic profile used by the canonical-prior audit."""
    out = rule_mirror(grid)
    reds = sum(1 for row in out for value in row if value == 2)
    cyans = sum(1 for row in out for value in row if value == 8)
    return (
        len(grid),
        len(grid[0]),
        len(_components5(grid)),
        _regions8(out),
        len(_degree1_cells(grid)),
        reds,
        cyans,
    )


def _build_canonical(rng, h, w, ccomp, crooms, ctips, reds_want, cyans_want):
    """Stamp the complete extracted official blob bitmap(s) at a random free
    offset (translation is the only nuisance), so the linked profile — dims,
    components, rooms, tips, and the mirror's red/cyan totals — is exact by
    construction. Returns None when the bitmap does not fit the canvas."""
    patterns = _CANONICAL_BITMAPS.get((h, w, ccomp))
    if patterns is None:
        return None
    for _attempt in range(60):
        g = full_grid(h, w, 0)
        occupied = set()
        ok = True
        for pattern in patterns:
            ph = max(r for r, _ in pattern) + 1
            pw = max(c for _, c in pattern) + 1
            placed = False
            for _try in range(40):
                r0 = rng.randint(0, h - ph)
                c0 = rng.randint(0, w - pw)
                cells = {(r0 + r, c0 + c) for r, c in pattern}
                if any((r + dr, c + dc) in occupied
                       for r, c in cells for dr, dc in _DIRS):
                    continue
                occupied |= cells
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        for r, c in occupied:
            g[r][c] = 5
        if profile_signature(g) == (
            h,
            w,
            ccomp,
            crooms,
            ctips,
            reds_want,
            cyans_want,
        ):
            return g
    return None


# Extracted official blob bitmaps (translated to origin), keyed by
# (h, w, n_components). The two-component form stamps both bitmaps apart.
_CANONICAL_BITMAPS = {
    (8, 9, 2): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 3), (1, 4)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (8, 10, 1): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
         (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
         (2, 2), (2, 5), (3, 3), (3, 4), (3, 5), (4, 3), (4, 4), (4, 5),
         (5, 3)),
    ),
    (8, 11, 1): (
        ((0, 1), (0, 2), (0, 4), (0, 5), (0, 6),
         (1, 1), (1, 2), (1, 5),
         (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
         (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4),
         (5, 4), (5, 5), (6, 4), (6, 5)),
    ),
    (9, 11, 1): (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
         (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5),
         (4, 1), (4, 4), (4, 5), (5, 3), (5, 4), (5, 5)),
    ),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    extra = sorted(k for k, v in overrides.items()
                   if k != "texture" and v is not None)
    if texture in DEGENERATE_TEXTURES:
        if extra:
            raise ValueError(
                f"degenerate texture {texture!r} is a fixed edge layout; it "
                f"takes no other overrides, got {extra}")
        return _draw_from_degenerate(texture)
    if texture not in (None, "none"):
        raise ValueError(f"unknown texture {texture!r}; valid: "
                         f"none|{'|'.join(DEGENERATE_TEXTURES)}")
    band = difficulty or "medium"
    if band == "easy":
        hr, wr, rr, tr = (6, 8), (8, 10), (1, 2), (0, 1)
    elif band == "hard":
        hr, wr, rr, tr = (10, 14), (12, 16), (3, 4), (1, 3)
    else:
        hr, wr, rr, tr = (8, 11), (9, 13), (2, 3), (0, 2)

    # Canonical-form prior (KRF-0003): ~25% of fully-unoverridden draws pin
    # one of the four complete official linked profiles through a translated
    # extracted bitmap. The other ~75% remains the generalized constructor.
    if not any(k in overrides for k in ("grid_h", "grid_w", "n_rooms", "n_tips")):
        if ctx.draw_rng("canonical_prior").random() < 0.25:
            # Complete linked profile: (h, w, components, rooms, tips,
            # answer-bearing red/cyan totals verified via the rule mirror).
            ch, cw, ccomp, crooms, ctips, creds, ccyans = ctx.draw_choice(
                "canonical_form", [(8, 9, 2, 2, 2, 6, 8),
                                   (8, 10, 1, 3, 2, 9, 12),
                                   (8, 11, 1, 3, 4, 12, 12),
                                   (9, 11, 1, 2, 3, 9, 12)])
            for label, value in (("grid_h", ch), ("grid_w", cw),
                                 ("n_rooms", crooms), ("n_tips", ctips)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
            g = _build_canonical(rng, ch, cw, ccomp, crooms, ctips,
                                 creds, ccyans)
            if g is not None:
                return g
            # totals could not be realized: fall through to the general path

    h = _banded_int(ctx, overrides, "grid_h", hr[0], hr[1], 6, 14)
    w = _banded_int(ctx, overrides, "grid_w", wr[0], wr[1], 8, 16)
    rooms_over = "n_rooms" in overrides and overrides["n_rooms"] is not None
    tips_over = "n_tips" in overrides and overrides["n_tips"] is not None
    n_rooms = _banded_int(ctx, overrides, "n_rooms", rr[0], rr[1], 1, 5)
    # A lone room with no tip is a lawful pure-cyan edge case, honored only
    # for an explicit n_tips=0 override (allow_pure below). Internal draws
    # draw the tip count from the FEASIBLE domain up front (>=1 tip for a
    # lone room) rather than drawing 0 and silently replacing it with 1.
    tips_lo = tr[0] if (tips_over or n_rooms > 1) else max(tr[0], 1)
    n_tips = _banded_int(ctx, overrides, "n_tips", tips_lo, tr[1], 0, 4)
    allow_pure = tips_over and n_rooms == 1 and n_tips == 0
    # two-blob mode (canonical train[2]): split the plan across two
    # separated blobs; internal draws only so explicit axes stay exact. The
    # drawn n_tips is distributed, never inflated: blob A gets all but at
    # most one tip, so a multi-tip plan keeps the red branch on both blobs
    # while the realized total always equals the keyed draw.
    if (not rooms_over and not tips_over and n_rooms >= 2 and n_tips >= 2
            and rng.random() < 0.25):
        tips_b = 1 if n_tips >= 1 else 0
        tips_a = n_tips - tips_b
        ga = _build_blob(rng, h, w, n_rooms - 1, tips_a,
                         allow_pure=(tips_a == 0))
        if ga is not None:
            forbidden = {(r + dr, c + dc)
                         for r, row in enumerate(ga) for c, v in enumerate(row)
                         if v == 5 for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            gb = _build_blob(rng, h, w, 1, tips_b, forbidden=forbidden,
                             allow_pure=(tips_b == 0))
            if gb is not None:
                for r in range(h):
                    for c in range(w):
                        if gb[r][c] == 5:
                            ga[r][c] = 5
                return ga
    g = _build_blob(rng, h, w, n_rooms, n_tips, allow_pure=allow_pure)
    if g is not None:
        return g
    if rooms_over or tips_over:
        raise ValueError(
            f"could not realize n_rooms={n_rooms}, n_tips={n_tips} on {h}x{w} "
            "within the rooms+arms grammar (layout retries exhausted)")
    # internal draw: shrink the plan and retry
    for rooms2 in range(n_rooms - 1, 0, -1):
        g = _build_blob(rng, h, w, rooms2, max(1, n_tips - 1))
        if g is not None:
            return g
    return _draw_from_degenerate("single_room")


def _draw_from_degenerate(name):
    h, w = 8, 10
    if name == "empty":
        return full_grid(h, w, 0)
    if name == "all_five":
        return full_grid(h, w, 5)
    g = full_grid(h, w, 0)
    for r in (3, 4):
        for c in (4, 5):
            g[r][c] = 5
    return g
