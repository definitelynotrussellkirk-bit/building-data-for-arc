"""Input sampler for arc_puzzle_bank_21_set21_bundle:medium_p02 — bbox-outline every object.

The unchanged Racket authority redraws, on a blank canvas, the perimeter of each
same-color 4-connected object's bounding box in that object's color. Outputs are
NOT generated here.

Every grid contains at least one HOLLOW object (bbox at least 3x3) whose blob
crosses the bbox interior, so each demonstration separates the outline rule from
"fill the bbox" and from "keep the blob and add its outline". The canonical pairs
cannot: every canonical bbox has a side of 2, where outline and fill coincide.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "61f255726e2e"
VERSION = "3.0.0"
TASK_ID = "61f255726e2e"
RULE_HASH = "afb437709cc6"
SUMMARY = (
    "0-background grid with 1-5 objects, each a 4-connected non-rectangular blob in "
    "its own color whose blob touches all four sides of its bounding box. At least "
    "one object is HOLLOW (bbox at least 3x3) with blob cells inside the bbox "
    "interior; the others are thin (one bbox side is 2), as in the canonical pairs. "
    "Bounding boxes are disjoint and separated by at least one background cell. "
    "Rule: on a blank canvas, draw each object's bbox perimeter in its color; bbox "
    "interiors become 0, so interior blob cells are erased."
)

INVARIANTS = [
    "background is 0; every object has a distinct color in 1..9",
    "each object is one 4-connected component with fewer cells than its bbox area",
    "each blob touches all four sides of its bbox, so the drawn bbox is exact",
    "bboxes are disjoint with at least one background cell between any two",
    "at least one object is hollow (bbox >= 3x3) with a blob cell strictly inside the bbox",
    "thin objects have a bbox side of exactly 2; their outline equals their filled bbox",
]

AXES = {
    "grid_h": {"type": "int", "default": "easy favors 7..9, medium 7..11, hard 9..13",
               "valid": "7..14"},
    "grid_w": {"type": "int", "default": "easy favors 9..10, medium 9..12, hard 10..14",
               "valid": "9..16"},
    "n_hollow": {"type": "int", "default": "1; hard favors 2", "valid": "1..2"},
    "n_thin": {"type": "int", "default": "1..2; hard favors 2..3", "valid": "0..3"},
}
# Every advertised combination is constructive, including 5 objects on 7x9.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_FAVORED = {
    "grid_h": {"easy": (7, 8, 9), "medium": (7, 8, 9, 10, 11), "hard": (9, 10, 11, 12, 13)},
    "grid_w": {"easy": (9, 10), "medium": (9, 10, 11, 12), "hard": (10, 11, 12, 13, 14)},
    "n_hollow": {"easy": (1,), "medium": (1, 1, 1, 2), "hard": (1, 2, 2)},
    "n_thin": {"easy": (1, 2), "medium": (1, 2), "hard": (2, 3)},
}
_HOLLOW_MAX = {"easy": 4, "medium": 4, "hard": 5}
_THIN_MAX = 4
_GAP = 1
# (h, w, objects) of the four canonical inputs. A "core" draw anchors on one of
# them in every band; "broad" draws use the band weights above.
_CANONICAL_PROFILES = ((8, 9, 2), (9, 9, 3), (7, 10, 2), (8, 10, 2))
_CORE_SHARE = {"easy": ("core",) * 3 + ("broad",), "medium": ("core", "broad"),
               "hard": ("core",) + ("broad",) * 3}


def _draw_axis(ctx, name, lo, hi, difficulty, anchor=None):
    # The whole documented domain stays drawable in every band and mode, so an
    # override anywhere in `valid` is honored exactly; bands only reweight it.
    if anchor is not None:
        favored = (anchor,) * 8
    else:
        favored = _FAVORED[name].get(difficulty or "medium", _FAVORED[name]["medium"])
    choices = list(range(lo, hi + 1)) + [v for v in favored for _ in range(12)]
    return ctx.draw_choice(name, choices)


def _path(rng, start, end):
    """Random monotone 4-connected lattice path from start to end, inclusive."""
    (r, c), (er, ec) = start, end
    steps = ["r"] * abs(er - r) + ["c"] * abs(ec - c)
    rng.shuffle(steps)
    cells = [(r, c)]
    for step in steps:
        if step == "r":
            r += 1 if er > r else -1
        else:
            c += 1 if ec > c else -1
        cells.append((r, c))
    return cells


def _shape(rng, bh, bw, *, crosses_interior):
    """A 4-connected, non-rectangular blob touching all four sides of a bh x bw box.

    Each side contributes an anchor joined to a hub by a monotone path. A hub in
    the strict interior guarantees an interior cell. Up to two extra adjacent
    cells add texture without completing the rectangle.
    """
    interior = [(r, c) for r in range(1, bh - 1) for c in range(1, bw - 1)]
    for _ in range(24):
        hub = rng.choice(interior) if crosses_interior else (rng.randrange(bh), rng.randrange(bw))
        anchors = [(0, rng.randrange(bw)), (bh - 1, rng.randrange(bw)),
                   (rng.randrange(bh), 0), (rng.randrange(bh), bw - 1)]
        cells = set()
        for anchor in anchors:
            cells.update(_path(rng, anchor, hub))
        for _extra in range(rng.randint(0, 2)):
            frontier = sorted({(r + dr, c + dc) for r, c in cells
                               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                               if 0 <= r + dr < bh and 0 <= c + dc < bw} - cells)
            if frontier and len(cells) + 1 < bh * bw:
                cells.add(rng.choice(frontier))
        if len(cells) < bh * bw:
            return sorted(cells)
    # Deterministic fallback: a plus/T through the box, never the full rectangle.
    mid_r, mid_c = (bh - 1) // 2 if crosses_interior else 0, (bw - 1) // 2
    return sorted({(mid_r, c) for c in range(bw)} | {(r, mid_c) for r in range(bh)})


def _ring_shape(rng, bh, bw):
    """An arc of the bbox perimeter (C, U, L or full ring): hollow with an empty interior."""
    ring = ([(0, c) for c in range(bw)] + [(r, bw - 1) for r in range(1, bh)]
            + [(bh - 1, c) for c in range(bw - 2, -1, -1)] + [(r, 0) for r in range(bh - 2, 0, -1)])
    for _ in range(12):
        gap = rng.randint(0, bh + bw - 3)
        start = rng.randrange(len(ring))
        removed = {ring[(start + i) % len(ring)] for i in range(gap)}
        cells = [p for p in ring if p not in removed]
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if {0, bh - 1} <= rows and {0, bw - 1} <= cols:
            return sorted(cells)
    return sorted(ring[1:])


def _place(rng, h, w, dims, budget=4000):
    """Backtracking placement of bboxes with a background gap; None if exhausted."""
    order = sorted(range(len(dims)), key=lambda i: -dims[i][0] * dims[i][1])
    spots = [None] * len(dims)
    nodes = [0]

    def clash(i, r, c):
        bh, bw = dims[i]
        for j, spot in enumerate(spots):
            if spot is None:
                continue
            jr, jc = spot
            jh, jw = dims[j]
            if (r < jr + jh + _GAP and jr < r + bh + _GAP
                    and c < jc + jw + _GAP and jc < c + bw + _GAP):
                return True
        return False

    def search(k):
        if k == len(order):
            return True
        i = order[k]
        bh, bw = dims[i]
        options = [(r, c) for r in range(h - bh + 1) for c in range(w - bw + 1)]
        rng.shuffle(options)
        for r, c in options:
            nodes[0] += 1
            if nodes[0] > budget:
                return False
            if clash(i, r, c):
                continue
            spots[i] = (r, c)
            if search(k + 1):
                return True
            spots[i] = None
        return False

    return spots if search(0) else None


def _dims(rng, n_hollow, n_thin, difficulty):
    top = _HOLLOW_MAX.get(difficulty or "medium", 4)
    dims = [(rng.randint(3, top), rng.randint(3, top)) for _ in range(n_hollow)]
    for _ in range(n_thin):
        k = rng.randint(2, _THIN_MAX)
        dims.append((2, k) if rng.random() < 0.5 else (k, 2))
    return dims


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    mode = ctx.draw_choice("curriculum_profile", _CORE_SHARE.get(difficulty or "medium", _CORE_SHARE["medium"]))
    anchor = ctx.draw_choice("canonical_anchor", _CANONICAL_PROFILES) if mode == "core" else (None, None, None)
    h = _draw_axis(ctx, "grid_h", 7, 14, difficulty, anchor[0])
    w = _draw_axis(ctx, "grid_w", 9, 16, difficulty, anchor[1])
    n_hollow = _draw_axis(ctx, "n_hollow", 1, 2, difficulty, 1 if mode == "core" else None)
    n_thin = _draw_axis(ctx, "n_thin", 0, 3, difficulty, anchor[2] - 1 if mode == "core" else None)

    dims = _dims(ctx.draw_rng("object_dims"), n_hollow, n_thin, "easy" if mode == "core" else difficulty)
    spots = _place(ctx.draw_rng("placement"), h, w, dims)
    if spots is None:
        # Minimal boxes always pack for the declared domain (see tests); this is a
        # size change of unexposed draws, never a change to an exact axis.
        dims = [(3, 3)] * n_hollow + [(2, 2)] * n_thin
        spots = _place(ctx.draw_rng("placement_minimal"), h, w, dims, budget=200000)
    if spots is None:
        raise RuntimeError(f"cannot place {n_hollow}+{n_thin} objects on {h}x{w}")

    colors = ctx.draw_rng("colors").sample(range(1, 10), len(dims))
    shape_rng = ctx.draw_rng("shapes")
    grid = full_grid(h, w, 0)
    for index, ((bh, bw), (r0, c0), color) in enumerate(zip(dims, spots, colors)):
        # The first hollow object always crosses its interior; a second one is an
        # empty-interior perimeter arc half the time.
        if index == 0:
            cells = _shape(shape_rng, bh, bw, crosses_interior=True)
        elif index < n_hollow and shape_rng.random() < 0.5:
            cells = _ring_shape(shape_rng, bh, bw)
        else:
            cells = _shape(shape_rng, bh, bw, crosses_interior=False)
        for r, c in cells:
            grid[r0 + r][c0 + c] = color
    return grid


def _objects(grid):
    """Same-color 4-connected components in row-major order (prelude `objects`)."""
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack, cells = [(r, c)], []
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr + 1, cc), (cr - 1, cc), (cr, cc + 1), (cr, cc - 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            found.append({"color": color, "cells": cells,
                          "bbox": (min(rs), min(cs), max(rs), max(cs))})
    return found


def _bbox_hw(obj):
    r1, c1, r2, c2 = obj["bbox"]
    return r2 - r1 + 1, c2 - c1 + 1


def _crosses_interior(obj):
    r1, c1, r2, c2 = obj["bbox"]
    return any(r1 < r < r2 and c1 < c < c2 for r, c in obj["cells"])


def observe_overrides(grid):
    """Recover every exact axis from pixels."""
    objs = _objects(grid)
    hollow = sum(min(_bbox_hw(o)) >= 3 for o in objs)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_hollow": hollow, "n_thin": len(objs) - hollow}


def self_check(grid, *, difficulty=None, meta=None):
    """Lawful instance of the task manifold. Canonical pairs (no hollow object) pass."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9"]
    objs = _objects(grid)
    if not objs:
        return ["no object"]
    errors = []
    colors = [o["color"] for o in objs]
    if len(set(colors)) != len(colors):
        errors.append("two objects share a color")
    for o in objs:
        bh, bw = _bbox_hw(o)
        if len(o["cells"]) >= bh * bw:
            errors.append(f"color {o['color']} object is a solid rectangle; output would equal input there")
    for i, a in enumerate(objs):
        for b in objs[i + 1:]:
            ar1, ac1, ar2, ac2 = a["bbox"]
            br1, bc1, br2, bc2 = b["bbox"]
            if ar1 <= br2 + _GAP and br1 <= ar2 + _GAP and ac1 <= bc2 + _GAP and bc1 <= ac2 + _GAP:
                errors.append(f"bboxes of colors {a['color']} and {b['color']} overlap or touch")
    return errors


def strict_canonical_like(grid):
    """Lawful manifold instance; canonical pairs pass. The hollow guarantee is a witness."""
    return self_check(grid)


def _has_interior_erasure(grid):
    return any(min(_bbox_hw(o)) >= 3 and _crosses_interior(o) for o in _objects(grid))


def _has_empty_hollow(grid):
    return any(min(_bbox_hw(o)) >= 3 and not _crosses_interior(o) for o in _objects(grid))


def _draw(grid, *, hollow, keep_input):
    out = [list(row) for row in grid] if keep_input else [[0] * len(grid[0]) for _ in grid]
    for o in _objects(grid):
        r1, c1, r2, c2 = o["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if not hollow or r in (r1, r2) or c in (c1, c2):
                    out[r][c] = o["color"]
    return out


def _fill_bbox(grid):
    """RIVAL, not label authority: paints the whole bbox."""
    return _draw(grid, hollow=False, keep_input=False)


def _outline_over_input(grid):
    """RIVAL, not label authority: adds the outline but never erases blob cells."""
    return _draw(grid, hollow=True, keep_input=True)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(d["input"]) == d["output"] for d in demos) and rival(query["input"]) != query["output"]:
            reasons.append(f"rival {name} fits every demo but answers the query differently")
    return reasons


SEMANTIC_WITNESSES = {
    "interior_erased": _has_interior_erasure,
    "empty_hollow": _has_empty_hollow,
}
SEMANTIC_RIVALS = {"fill_bbox": _fill_bbox, "outline_over_input": _outline_over_input}
WITNESS_RIVALS = {"interior_erased": ["fill_bbox", "outline_over_input"],
                  "empty_hollow": ["fill_bbox"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
