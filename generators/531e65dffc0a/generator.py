"""Anchor-coded rotation stamps with exact controls and teaching witnesses.

Racket selects the prototype, normalizes its bounding box, and stamps rotations
2=id, 3=cw90, 4=180, 5=ccw90 onto a fresh grid. Pixels outside the canvas are
clipped; overlapping same-color stamps form a union. This sampler deliberately
uses one monochrome connected prototype and isolated anchors. The authority's
larger multiple-object domain is not sampled.

Default even indices distinguish every declared canonical shortcut and all
twelve single-code mapping errors in one scene. Odd indices explore ordinary
scenes, including symmetric prototypes and a canonical-profile component.
Every three consecutive default demonstrations contain a teaching scene, as
does every three-of-four query rotation. Exact overrides select the broad
sampler and make no lesson-level teaching promise. Racket remains the label
authority; Python predictions below are executable rival contracts.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "531e65dffc0a"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "4acd30f1e03a"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "One monochrome prototype and isolated anchors: 2=id, 3=cw90, 4=180, "
    "5=ccw90. Stamp bounding-box-normalized shapes in the prototype color on "
    "a fresh grid, clipping at edges and taking the union of overlaps. "
    "Alternating teaching and broad scenes expose canonical-fitting shortcuts."
)
INVARIANTS = [
    "background is 0; cells are ARC integer colors 0..9",
    "exactly one monochrome 4-connected prototype with at least two cells",
    "prototype color is one of 1,6,7,8,9; anchors use only 2,3,4,5",
    "one or more anchors; no anchor 4-touches another nonzero input cell",
    "clipping, output overlap, empty bounding-box corners, and source overlap are lawful",
]
AXES = {
    "grid_h": {"type": "int", "default": "teaching 11..12; core 10..12; broad 8..18", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "teaching/core match height; broad 8..18", "valid": "8..18"},
    "proto_size": {"type": "int", "default": "teaching 4..6; core 3..4; broad 2..6", "valid": "2..6"},
    "n_anchors": {"type": "int", "default": "teaching 4; core 2..3; broad 1..6", "valid": "1..6"},
    "proto_color": {"type": "color", "default": "uniform 1,6,7,8,9", "valid": "1|6|7|8|9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("teaching", "broad")
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CODES = (2, 3, 4, 5)
_COLORS = (1, 6, 7, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Default layout schedule; non-null exact overrides choose broad layout."""
    return SCHEDULE_PROFILES[sample_index % 2]


def _normalize(cells):
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return tuple(sorted((r-r0, c-c0) for r, c in cells))


@lru_cache(maxsize=6)
def _polyominoes(size):
    """All fixed polyominoes of size <=6; finite frontier expansion, no retries."""
    if size == 1:
        return (((0, 0),),)
    result = set()
    for smaller in _polyominoes(size-1):
        occupied = set(smaller)
        frontier = {(r+dr, c+dc) for r, c in smaller for dr, dc in _STEPS} - occupied
        for point in sorted(frontier):
            result.add(_normalize((*smaller, point)))
    return tuple(sorted(result))


def _rotated(cells, code):
    h, w = max(r for r, c in cells)+1, max(c for r, c in cells)+1
    if code == 2:
        return tuple(sorted(cells))
    if code == 3:
        return tuple(sorted((c, h-1-r) for r, c in cells))
    if code == 4:
        return tuple(sorted((h-1-r, w-1-c) for r, c in cells))
    if code == 5:
        return tuple(sorted((w-1-c, r) for r, c in cells))
    raise ValueError(f"unknown rotation code: {code}")


def _scene(grid):
    source = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value in _COLORS]
    anchors = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value in _CODES]
    if not source:
        raise ValueError("missing prototype")
    return source, _normalize(source), grid[source[0][0]][source[0][1]], anchors


def observe_overrides(grid):
    source, _, color, anchors = _scene(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "proto_size": len(source), "n_anchors": len(anchors), "proto_color": color}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid exceeds ARC 30x30 limit"]
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9"]
    source = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value in _COLORS}
    anchors = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value in _CODES}
    errors = []
    if len(source) < 2:
        errors.append("prototype must contain at least two cells")
    if len({grid[r][c] for r, c in source}) != 1:
        errors.append("prototype must have exactly one non-anchor color")
    if source:
        todo = [min(source)]
        reached = set(todo)
        for r, c in todo:
            for dr, dc in _STEPS:
                point = r+dr, c+dc
                if point in source and point not in reached:
                    reached.add(point)
                    todo.append(point)
        if reached != source:
            errors.append("prototype must be one 4-connected component")
    if not anchors:
        errors.append("missing rotation anchors")
    occupied = source | anchors
    if any((r+dr, c+dc) in occupied for r, c in anchors for dr, dc in _STEPS):
        errors.append("anchors must not 4-touch any nonzero input cell")
    return errors


def strict_canonical_like(grid):
    """The declared one-prototype task domain, not an exact silhouette filter."""
    return self_check(grid)


def _prediction(grid, rival=None):
    """Contract prediction only; Racket remains the label authority."""
    source, shape, color, anchors = _scene(grid)
    h, w = len(grid), len(grid[0])
    counts = Counter()
    for ar, ac, code in anchors:
        transformed = _rotated(shape, 2 if rival == "yellow_identity" and code == 4 else code)
        if rival == "absolute_source_offsets":
            r0, c0 = min(r for r, c in source), min(c for r, c in source)
            transformed = tuple((r+r0, c+c0) for r, c in transformed)
        if rival == "shift_stamp_to_fit":
            ar = min(ar, h-1-max(r for r, c in transformed))
            ac = min(ac, w-1-max(c for r, c in transformed))
        positions = {(ar+r, ac+c) for r, c in transformed}
        visible = {(r, c) for r, c in positions if 0 <= r < h and 0 <= c < w}
        if rival == "suppress_clipped_stamps" and visible != positions:
            continue
        counts.update(visible)
    out = full_grid(h, w, 0)
    for (r, c), count in counts.items():
        if rival != "xor_overlap" or count % 2:
            out[r][c] = color
    if rival == "erase_source_after_stamping":
        for r, c in source:
            out[r][c] = 0
    return out


def _rival(name):
    def predict(grid):
        return _prediction(grid, name)
    predict.__name__ = name
    return predict


CANONICAL_SHORTCUTS = {name: _rival(name) for name in (
    "yellow_identity", "suppress_clipped_stamps", "shift_stamp_to_fit",
    "xor_overlap", "erase_source_after_stamping", "absolute_source_offsets",
)}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)


def _mapping_rival(code, replacement):
    def predict(grid):
        recoded = [[replacement if value == code else value for value in row] for row in grid]
        return _prediction(recoded)
    predict.__name__ = f"code_{code}_as_{replacement}"
    return predict


LESSON_COMPETITORS.update({f"code_{code}_as_{other}": _mapping_rival(code, other)
                          for code in _CODES for other in _CODES if other != code})
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _witness(name):
    def distinguishes(grid):
        return _prediction(grid) != SEMANTIC_RIVALS[name](grid)
    distinguishes.__name__ = f"distinguishes_{name}"
    return distinguishes


SEMANTIC_WITNESSES = {name: _witness(name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; not a claim of universal identifiability."""
    query_grid = query["input"] if isinstance(query, dict) else query
    expected = _prediction(query_grid)
    return [f"declared rival {name} fits all demonstrations and disagrees on query"
            for name, predict in LESSON_COMPETITORS.items()
            if all(predict(pair["input"]) == pair["output"] for pair in demos)
            and predict(query_grid) != expected]


def _make_grid(h, w, shape, origin, color, anchors):
    grid = full_grid(h, w, 0)
    for r, c in shape:
        grid[origin[0]+r][origin[1]+c] = color
    for r, c, code in anchors:
        grid[r][c] = code
    return grid


def _broad(ctx, h, w, size, color, n_anchors, *, distinct_codes=False):
    rng = ctx.draw_rng("broad_layout")
    shape = rng.choice(_polyominoes(size))
    ph, pw = max(r for r, c in shape)+1, max(c for r, c in shape)+1
    origin = rng.randrange(h-ph+1), rng.randrange(w-pw+1)
    occupied = {(origin[0]+r, origin[1]+c) for r, c in shape}
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if (r, c) not in occupied
                  and all((r+dr, c+dc) not in occupied for dr, dc in _STEPS)]
    anchors = []
    codes = rng.sample(_CODES, n_anchors) if distinct_codes else [rng.choice(_CODES) for _ in range(n_anchors)]
    for _ in range(n_anchors):
        # On an 8x8 canvas, <=6 prototype cells exclude <=30 locations.
        # Each selected anchor excludes <=5 more, so all six anchors fit.
        if not candidates:
            raise RuntimeError("anchor capacity invariant failed; refusing a short scene")
        r, c = rng.choice(candidates)
        anchors.append((r, c, codes[len(anchors)]))
        candidates = [(a, b) for a, b in candidates if abs(a-r)+abs(b-c) > 1]
    return _make_grid(h, w, shape, origin, color, anchors)


def _teaching(ctx, h, w, size, color):
    """All four codes, overlapping interior stamps, clipping, and source overlap."""
    rng = ctx.draw_rng("teaching_layout")
    shapes = [s for s in _polyominoes(size) if _rotated(s, 4) != s]
    for _ in range(256):
        shape = rng.choice(shapes)
        other_code, edge_code = rng.sample((2, 3, 5), 2)
        yellow, other, edge = (_rotated(shape, code) for code in (4, other_code, edge_code))
        shifts = sorted({(r-a, c-b) for r, c in yellow for a, b in other
                         if abs(r-a)+abs(c-b) > 1})
        if not shifts:
            continue
        dr, dc = rng.choice(shifts)
        offsets = (*yellow, *((r+dr, c+dc) for r, c in other), (0, 0), (dr, dc))
        rlo, rhi = -min(r for r, c in offsets), h-1-max(r for r, c in offsets)
        clo, chi = -min(c for r, c in offsets), w-1-max(c for r, c in offsets)
        if rlo > rhi or clo > chi:
            continue
        ar, ac = rng.randint(rlo, rhi), rng.randint(clo, chi)
        anchors = [(ar, ac, 4), (ar+dr, ac+dc, other_code)]
        edge_candidates = sorted({(h-1, c) for c in range(w)} | {(r, w-1) for r in range(h)})
        rng.shuffle(edge_candidates)
        placed_edge = None
        for er, ec in edge_candidates:
            if any(abs(er-r)+abs(ec-c) <= 1 for r, c, code in anchors):
                continue
            visible = {(er+r, ec+c) for r, c in edge if er+r < h and ec+c < w}
            if 0 < len(visible) < size:
                placed_edge = er, ec, edge_code
                break
        if placed_edge is None:
            continue
        anchors.append(placed_edge)
        support = {(r+a, c+b) for r, c, code in anchors for a, b in _rotated(shape, code)
                   if r+a < h and c+b < w}
        fourth_code = next(code for code in _CODES if code not in (4, other_code, edge_code))
        fourth_shape = _rotated(shape, fourth_code)
        fourth_h = max(r for r, c in fourth_shape)+1
        fourth_w = max(c for r, c in fourth_shape)+1
        fourth_origins = [(r, c) for r in range(h-fourth_h+1) for c in range(w-fourth_w+1)]
        rng.shuffle(fourth_origins)
        fourth = None
        for r, c in fourth_origins:
            if any(abs(r-a)+abs(c-b) <= 1 for a, b, code in anchors):
                continue
            added = {(r+a, c+b) for a, b in fourth_shape}
            if not added & support:
                fourth = (r, c, fourth_code)
                support.update(added)
                break
        if fourth is None:
            continue
        anchors.append(fourth)
        ph, pw = max(r for r, c in shape)+1, max(c for r, c in shape)+1
        origins = sorted({(r-a, c-b) for r, c in support for a, b in shape
                          if 0 <= r-a <= h-ph and 0 <= c-b <= w-pw})
        rng.shuffle(origins)
        for origin in origins:
            source = {(origin[0]+r, origin[1]+c) for r, c in shape}
            if any(abs(r-a)+abs(c-b) <= 1 for r, c in source for a, b, code in anchors):
                continue
            grid = _make_grid(h, w, shape, origin, color, anchors)
            expected = _prediction(grid)
            if all(predict(grid) != expected for predict in LESSON_COMPETITORS.values()):
                return grid
    raise RuntimeError("bounded teaching construction exhausted; refusing an untaught fallback")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    explicit = any(value is not None for value in overrides.values())
    teaching = schedule_profile(seed, sample_index, difficulty) == "teaching" and not explicit
    core = not explicit and not teaching and ctx.draw_choice(
        "ordinary_profile", ("core", "core", "core", "broad")) == "core"
    side = ctx.draw_choice("profile_side", (10, 11, 12)) if core else None
    favored = {"easy": tuple(range(8, 13)), "medium": tuple(range(9, 15)),
               "hard": tuple(range(12, 19)), None: tuple(range(9, 15))}[difficulty]
    dimensions = tuple(range(8, 19)) + favored*3
    h = ctx.draw_choice("grid_h", (11, 12) if teaching else ((side,) if core else dimensions))
    w = ctx.draw_choice("grid_w", (h,) if teaching or core else dimensions)
    size = ctx.draw_choice("proto_size", (4, 5, 6) if teaching else ((3, 4) if core else tuple(range(2, 7))))
    counts = (4,) if teaching else (((2,) if side == 10 else (3,)) if core else tuple(range(1, 7)))
    n_anchors = ctx.draw_choice("n_anchors", counts)
    color = ctx.draw_choice("proto_color", _COLORS)
    return (_teaching(ctx, h, w, size, color) if teaching else
            _broad(ctx, h, w, size, color, n_anchors, distinct_codes=core))
