"""Generator for arc_additional_puzzle_bank_volume13:H87.

Rule: codes = values in {1,2,3,4} in scan order (1=identity, 2=rot90cw,
3=flip-lr, 4=flip-ud, each normalized). The cyan-8 source shape is
transformed by the FIRST code and by the SECOND code; the CELL-WISE
INTERSECTION of the two normalized variants is stamped in color 2 at
the first color-9 anchor (anchor = top-left of the stamp); OOB stamp
cells clip; everything else stays.

Combinatorial axes: grid_h/w, code pair, texture
(plain|same_codes|clip). empty-overlap boards are IMPOSSIBLE for
connected sources: a shape and its flip/rotation both span the bbox
corner-to-corner, so the variants always share a cell.
Degenerates: one_control (missing second code degrades: (second '(x))
-> #f -> cond else -> flip-ud). no_source was DROPPED (verified crash).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "07975597e370"
VERSION = "2.0.2"
TASK_ID = "07975597e370"
SUMMARY = (
    "Two transform codes (identity/rot90/flip-lr/flip-ud) act on an "
    "ASYMMETRIC cyan source; the intersection of the two variants is "
    "stamped red at the maroon anchor. (Was: source always PLUS_5 - "
    "symmetric under ALL four transforms, so the codes were "
    "completely invisible and every output was a full plus stamp; "
    "controls/anchor/source at fixed positions; no_source degenerate "
    "crashed the rule.)"
)

# Rivals: 'codes are irrelevant' refuted by asymmetric sources whose
# intersections genuinely differ per code pair. 'stamp the whole
# shape' refuted by proper-subset intersections. 'same code twice is
# invalid' refuted by same_codes (full-shape stamp). 'output always
# has a stamp' refuted by empty_overlap (identity). 4 demos.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one cyan-8 source, asymmetric (4 transform variants pairwise distinct)",
    "exactly two control cells in {1,2,3,4} and exactly one color-9 anchor",
    "main-path stamps are non-empty, land in-bounds on empty cells",
]

DEGENERATE_TEXTURES = ("one_control",)
HELPFUL_TEXTURES = ("plain", "same_codes", "clip")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 11..15", "valid": "9..20"},
    "grid_w":  {"type": "int", "default": "rng 13..18", "valid": "11..22"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|same_codes|clip|one_control",
                "doc": "same_codes: both controls equal (full-shape stamp); "
                       "clip: anchor near the edge (stamp clips)."},
}


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _transform(cells, code):
    if code == 2:
        return _norm([(c, -r) for r, c in cells])
    if code == 3:
        return _norm([(r, -c) for r, c in cells])
    if code == 4:
        return _norm([(-r, c) for r, c in cells])
    return _norm(cells)


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    return _norm(cells)


def _asym_shape(rng, lo=4, hi=6):
    for _ in range(300):
        s = _grow(rng, rng.randint(lo, hi))
        if len({tuple(_transform(s, k)) for k in (1, 2, 3, 4)}) == 4:
            return s
    return [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]


def _mirror(g):
    h, w = len(g), len(g[0])
    src = None
    seen = [[False] * w for _ in range(h)]
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] != 8 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and not seen[rr][cc] \
                            and g[rr][cc] == 8:
                        seen[rr][cc] = True
                        stack.append((rr, cc))
            src = cells
            break
        if src:
            break
    if src is None:
        return None
    shape = _norm(src)
    codes = [g[r][c] for r in range(h) for c in range(w)
             if g[r][c] in (1, 2, 3, 4)]
    anchor = next(((r, c) for r in range(h) for c in range(w)
                   if g[r][c] == 9), None)
    if anchor is None or not codes:
        return None
    a = _transform(shape, codes[0])
    b = _transform(shape, codes[1] if len(codes) > 1 else 4)  # #f -> flip-ud
    overlap = [p for p in a if p in set(b)]
    out = [row[:] for row in g]
    for r, c in overlap:
        rr, cc = anchor[0] + r, anchor[1] + c
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = 2
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 cyan(8) source, exactly 2 controls in {1,2,3,4}, exactly 1 maroon(9) anchor."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    # find 4-connected components of color 8
    seen: set = set()
    cyan_comps = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 8 and (r, c) not in seen:
                cyan_comps += 1
                stack = [(r, c)]
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 8
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
    if cyan_comps != 1:
        errs.append(f"expected exactly 1 cyan(8) source component, found {cyan_comps}")
    else:
        # Recover the source and ensure controls can actually matter.
        src_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
        shape = _norm(src_cells)
        if len({tuple(_transform(shape, k)) for k in (1, 2, 3, 4)}) != 4:
            errs.append("cyan source is symmetric under at least one transform; codes are hidden")
    controls = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2, 3, 4)]
    if len(controls) != 2:
        errs.append(f"expected exactly 2 control cells in {{1..4}}, found {len(controls)}")
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 1:
        errs.append(f"expected exactly 1 maroon(9) anchor, found {len(anchors)}")
    mirrored = _mirror(grid)
    if mirrored is None or mirrored == grid:
        errs.append("transform-intersection stamp is empty or invisible")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "plain", "same_codes", "clip"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 16, 18)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 18)
    rng = ctx.draw_rng("layout")

    for _attempt in range(200):
        shape = _asym_shape(rng)
        if texture == "same_codes":
            k = rng.randint(1, 4)
            codes = (k, k)
        else:
            codes = tuple(rng.sample([1, 2, 3, 4], 2))
        a = _transform(shape, codes[0])
        b = _transform(shape, codes[1])
        overlap = [p for p in a if p in set(b)]
        if not overlap:
            continue
        if texture == "plain" and len(overlap) == len(shape):
            continue  # want a PROPER subset so the codes visibly matter

        g = full_grid(h, w, 0)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        sr = rng.randint(0, h - sh)
        sc = rng.randint(0, w - sw)
        src_cells = {(sr + r, sc + c) for r, c in shape}
        for r, c in src_cells:
            g[r][c] = 8
        taken = {(r + dr, c + dc) for r, c in src_cells
                 for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

        # anchor with the full overlap bbox free (or clipping for clip)
        oh = max(r for r, _ in overlap) + 1
        ow = max(c for _, c in overlap) + 1
        if texture == "clip" and oh < 2 and ow < 2:
            continue  # a 1-cell stamp cannot partially clip
        anchor = None
        for _try in range(150):
            if texture == "clip":
                if oh >= 2 and (ow < 2 or rng.random() < 0.5):
                    ar = rng.randint(h - oh + 1, h - 1)
                    ac = rng.randint(0, max(0, w - ow))
                else:
                    ar = rng.randint(0, max(0, h - oh))
                    ac = rng.randint(w - ow + 1, w - 1)
            else:
                ar = rng.randint(0, h - oh)
                ac = rng.randint(0, w - ow)
            stamp = [(ar + r, ac + c) for r, c in overlap]
            inb = [(r, c) for r, c in stamp if 0 <= r < h and 0 <= c < w]
            if texture == "clip" and (len(inb) == len(stamp) or not inb):
                continue
            if (ar, ac) in taken or g[ar][ac] != 0:
                continue
            if any(p in taken or g[p[0]][p[1]] != 0 for p in inb):
                continue
            anchor = (ar, ac)
            break
        if anchor is None:
            continue
        g[anchor[0]][anchor[1]] = 9
        taken |= {(anchor[0] + r, anchor[1] + c) for r, c in overlap
                  if 0 <= anchor[0] + r < h and 0 <= anchor[1] + c < w}
        taken.add(anchor)

        # two control cells; SCAN ORDER defines (first, second)
        ctrl_spots = []
        for _try in range(300):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] != 0 or (r, c) in taken:
                continue
            ctrl_spots.append((r, c))
            taken.add((r, c))
            if len(ctrl_spots) == 2:
                break
        if len(ctrl_spots) < 2:
            continue
        ctrl_spots.sort()
        g[ctrl_spots[0][0]][ctrl_spots[0][1]] = codes[0]
        g[ctrl_spots[1][0]][ctrl_spots[1][1]] = codes[1]
        exp = _mirror(g)
        if exp is None or exp == g:
            continue
        return g
    raise ValueError("could not realize transform-intersection board")


def _draw_from_degenerate(name, ctx):
    """one_control — a single code: (second codes) degrades to #f and
    the cond's else branch applies FLIP-UD as the second transform.
    rng-varied. (no_source dropped: verified crash.)"""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 11, 14)
    w = ctx.draw_int("grid_w", 13, 16)
    g = full_grid(h, w, 0)
    shape = _asym_shape(rng)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for r, c in shape:
        g[h - sh - 1 + r][w - sw - 1 + c] = 8
    g[1][2] = rng.randint(1, 4)
    g[3][w // 2] = 9
    return g
