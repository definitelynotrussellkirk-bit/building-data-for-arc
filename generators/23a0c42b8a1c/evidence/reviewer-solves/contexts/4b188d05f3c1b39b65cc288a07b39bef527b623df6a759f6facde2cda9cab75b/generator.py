"""Marker-adjacent minimum selection, target-only crop, fixed cyan output.

Authoritative labels come from canonical Racket 5af80c67d390. The sampler
supports one or two marker neighbors; all adjacent sizes must be distinct,
because the retained Racket comparator's tie branch is not executable.
"""
from __future__ import annotations

from itertools import combinations
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "23a0c42b8a1c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5af80c67d390"
SUMMARY = "Crop the smallest shape cardinally adjacent to the color-1 marker and recolor its cells to 8."
INVARIANTS = [
    "rectangular integer colors 0..9 with background 0",
    "exactly one single-cell color-1 marker",
    "at least one non-marker component cardinally adjacent to the marker",
    "all marker-adjacent component sizes are distinct; the retained rule has an unsafe tie branch",
]
AXES = {
    "grid_h": {"type": "int", "default": "weighted 8/9 plus 7..20", "valid": "7..20"},
    "grid_w": {"type": "int", "default": "weighted canonical widths plus 8..19", "valid": "8..19"},
    "small_size": {"type": "int", "default": "difficulty-weighted 4..7", "valid": "1..7"},
    "n_distinct_colors": {"type": "int", "default": "weighted 5, with 4 and 6", "valid": "4..6"},
    "palette_kind": {"type": "str", "default": "rng over default|warm|cool|varied", "valid": "default|warm|cool|varied",
                     "probe": "diagnostic", "description": "Color-pool preference; supports overlap, not an exact identifiable output class."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
SCHEDULE_PROFILES = ("first", "last", "single")
MIN_STRICT_FRAC = 1.0
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PALETTES = {"default": (2, 3, 4, 6, 7, 9), "warm": (2, 4, 6, 9),
             "cool": (3, 5, 7, 8), "varied": (2, 3, 4, 5, 6, 7, 8, 9)}


def _norm(cells):
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _area(cells):
    return ((max(r for r, c in cells) - min(r for r, c in cells) + 1) *
            (max(c for r, c in cells) - min(c for r, c in cells) + 1))


def _connected(cells):
    remaining = set(cells)
    pending = [min(remaining)]
    remaining.remove(pending[0])
    while pending:
        r, c = pending.pop()
        for dr, dc in _CARD:
            if (r + dr, c + dc) in remaining:
                remaining.remove((r + dr, c + dc))
                pending.append((r + dr, c + dc))
    return not remaining


def _shape_bank():
    # Enumerate the bounded 3x3 support exactly; no unbounded growth or clipped fallback.
    cells = tuple((r, c) for r in range(3) for c in range(3))
    return {k: tuple(sorted({_norm(shape) for shape in combinations(cells, k)
                             if _connected(shape)})) for k in range(1, 9)}


_SHAPES = _shape_bank()


def schedule_profile(seed, sample_index, difficulty=None):
    return ("first", "last", "single", "first", "last")[sample_index % 5]


def _draw_exact(ctx, overrides, key, legal, defaults):
    value = overrides.get(key)
    if value is not None and type(value) is not int:
        raise TypeError(f"{key} requires an integer, not {type(value).__name__}")
    # Choice draws retain the actual returned value as public GenCtx provenance.
    return ctx.draw_choice(key, legal if value is not None else defaults)


def _relative(cells, direction, rng):
    dr, dc = direction
    # Choose a boundary cell to touch the marker; all object cells stay in one half-plane.
    if dr:
        edge = max(r for r, c in cells) if dr < 0 else min(r for r, c in cells)
        anchors = [(r, c) for r, c in cells if r == edge]
    else:
        edge = max(c for r, c in cells) if dc < 0 else min(c for r, c in cells)
        anchors = [(r, c) for r, c in cells if c == edge]
    ar, ac = rng.choice(anchors)
    return tuple((r + dr - ar, c + dc - ac) for r, c in cells)


def _place(h, w, small, big, profile, rng):
    for _ in range(80):
        direction = rng.choice(_CARD)
        target = _relative(small, direction, rng)
        other = (() if profile == "single" else
                 _relative(big, (-direction[0], -direction[1]), rng))
        if other and ((min(target) < min(other)) != (profile == "first")):
            continue
        occupied = ((0, 0),) + target + other
        rlo, rhi = -min(r for r, c in occupied), h - 1 - max(r for r, c in occupied)
        clo, chi = -min(c for r, c in occupied), w - 1 - max(c for r, c in occupied)
        if rlo > rhi or clo > chi:
            continue
        mr, mc = rng.randint(rlo, rhi), rng.randint(clo, chi)
        return ((mr, mc), [(r + mr, c + mc) for r, c in target],
                [(r + mr, c + mc) for r, c in other])
    raise RuntimeError("bounded placement failed; no altered-size fallback is permitted")


def _paint(grid, cells, color):
    for r, c in cells:
        if grid[r][c] != 0:
            raise RuntimeError("placement overlap")
        grid[r][c] = color


def _distractor(grid, marker, target, color, inside, rng):
    mr, mc = marker
    r0, r1 = min(r for r, c in target), max(r for r, c in target)
    c0, c1 = min(c for r, c in target), max(c for r, c in target)
    candidates = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            in_box = r0 <= r <= r1 and c0 <= c <= c1
            if value or abs(r - mr) + abs(c - mc) <= 1 or (inside and not in_box):
                continue
            if not inside and in_box:
                continue
            if any(0 <= r + dr < len(grid) and 0 <= c + dc < len(row) and
                   grid[r + dr][c + dc] == color for dr, dc in _CARD):
                continue
            candidates.append((r, c))
    if inside:
        placements = [((r, c),) for r, c in candidates]
    else:
        # Ordinary distractors are dominoes, preserving canonical examples'
        # useful single-cell-marker role. Interior mask witnesses need one cell.
        valid = set(candidates)
        placements = [((r, c), (r + dr, c + dc))
                      for r, c in candidates for dr, dc in ((0, 1), (1, 0))
                      if (r + dr, c + dc) in valid]
    if not placements:
        raise RuntimeError("no lawful distractor location; requested support is not silently changed")
    _paint(grid, rng.choice(placements), color)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed requires an integer, excluding bool")
    if type(sample_index) is not int:
        raise TypeError("sample_index requires an integer, excluding bool")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and (type(difficulty) is not str or
                                   difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unknown override axes: {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = _draw_exact(ctx, overrides, "grid_h", tuple(range(7, 21)),
                    (8,) * 24 + (9,) * 12 + tuple(range(7, 21)))
    preferred = (11, 13) if h == 8 else ((12,) if h == 9 else ())
    w = _draw_exact(ctx, overrides, "grid_w", tuple(range(8, 20)),
                    preferred * 28 + tuple(range(8, 20)))
    defaults = {"easy": (4, 4, 5), "medium": (4, 5, 6), "hard": (5, 6, 7)}
    k = _draw_exact(ctx, overrides, "small_size", tuple(range(1, 8)),
                    defaults.get(difficulty, (4, 5, 6, 7)))
    ncolors = _draw_exact(ctx, overrides, "n_distinct_colors", (4, 5, 6), (5,) * 12 + (4, 6))
    palette = ctx.draw_choice("palette_kind", tuple(_PALETTES))
    rng = ctx.draw_rng("layout")
    # Default targets have missing bbox cells, as do the canonical target shapes.
    candidates = [s for s in _SHAPES[k] if k < 3 or _area(s) > k]
    small = rng.choice(candidates)
    big_size = {1: 2, 2: 3, 3: 4, 4: 6, 5: 6, 6: 8, 7: 8}[k]
    min_area = min(_area(s) for s in _SHAPES[big_size])
    big = rng.choice([s for s in _SHAPES[big_size] if _area(s) == min_area])
    profile = schedule_profile(seed, sample_index, difficulty)
    marker, target, other = _place(h, w, small, big, profile, rng)
    pool = list(_PALETTES[palette])
    target_color = rng.choice([c for c in pool if c != 8])
    pool.remove(target_color)
    rng.shuffle(pool)
    colors = [target_color] + pool[:ncolors - 3]
    grid = full_grid(h, w, 0)
    grid[marker[0]][marker[1]] = 1
    _paint(grid, target, colors[0])
    if other:
        _paint(grid, other, colors[1])
        remaining_colors = colors[2:] or [colors[1]]
    else:
        remaining_colors = colors[1:]
    for i, color in enumerate(remaining_colors):
        _distractor(grid, marker, target, color,
                    inside=(profile == "first" and i == 0 and _area(target) > k), rng=rng)
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed input failed domain check: " + "; ".join(errors))
    return grid


def _parts(grid):
    comps = components(grid)
    marker = next(c for c in comps if c["color"] == 1)
    mr, mc = marker["cells"][0]
    objects = [c for c in comps if c["color"] != 1]
    adjacent = [c for c in objects if any(abs(r - mr) + abs(col - mc) == 1
                                        for r, col in c["cells"])]
    return marker, objects, adjacent


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not all(isinstance(r, list) and r for r in grid):
        return ["expected a nonempty grid of nonempty row lists"]
    if len({len(r) for r in grid}) != 1:
        return ["expected rectangular rows"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be integers in 0..9, excluding bool"]
    if not any(v == 0 for row in grid for v in row):
        return ["expected background 0"]
    markers = [c for c in components(grid) if c["color"] == 1]
    if len(markers) != 1 or len(markers[0]["cells"]) != 1:
        return ["expected exactly one single-cell color-1 marker"]
    adjacent = _parts(grid)[2]
    if not adjacent:
        return ["marker must touch at least one non-marker component"]
    sizes = [len(c["cells"]) for c in adjacent]
    if len(set(sizes)) != len(sizes):
        return ["all adjacent sizes must differ: the retained Racket tie comparator is unsafe"]
    return []


def _target(grid):
    return min(_parts(grid)[2], key=lambda c: len(c["cells"]))


def _crop(obj, color=8):
    cells = obj["cells"]
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    points = set(cells)
    return [[color if (r, c) in points else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "small_size": len(_target(grid)["cells"]),
            "n_distinct_colors": len({v for row in grid for v in row})}


def strict_canonical_like(grid):
    return self_check(grid)


def _first_neighbor(grid):
    return _crop(min(_parts(grid)[2], key=lambda c: min(c["cells"])))


def _last_neighbor(grid):
    return _crop(max(_parts(grid)[2], key=lambda c: min(c["cells"])))


def _largest_neighbor(grid):
    return _crop(max(_parts(grid)[2], key=lambda c: len(c["cells"])))


def _bbox_area_neighbor(grid):
    return _crop(min(_parts(grid)[2], key=lambda c: (_area(c["cells"]), min(c["cells"]))))


def _global_smallest(grid):
    return _crop(min(_parts(grid)[1], key=lambda c: (len(c["cells"]), min(c["cells"]))))


def _keep_color(grid):
    obj = _target(grid)
    return _crop(obj, obj["color"])


def _fill_bbox(grid):
    crop = _crop(_target(grid))
    return [[8] * len(crop[0]) for _ in crop]


def _unmasked_bbox(grid):
    r0, c0, r1, c1 = _target(grid)["bbox"]
    return [[8 if grid[r][c] else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


SEMANTIC_RIVALS = {
    "first_neighbor": _first_neighbor, "last_neighbor": _last_neighbor,
    "largest_neighbor": _largest_neighbor, "bbox_area_neighbor": _bbox_area_neighbor,
    "global_smallest": _global_smallest, "keep_color": _keep_color,
    "fill_bbox": _fill_bbox, "unmasked_bbox": _unmasked_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("first_neighbor", "last_neighbor", "largest_neighbor", "bbox_area_neighbor", "unmasked_bbox")}


def _witness_first(grid):
    return _first_neighbor(grid) != _crop(_target(grid))


def _witness_last(grid):
    return _last_neighbor(grid) != _crop(_target(grid))


def _witness_size(grid):
    return _largest_neighbor(grid) != _crop(_target(grid))


def _witness_bbox(grid):
    return _bbox_area_neighbor(grid) != _crop(_target(grid))


def _witness_marker(grid):
    return _global_smallest(grid) != _crop(_target(grid))


def _witness_mask(grid):
    return _unmasked_bbox(grid) != _crop(_target(grid))


SEMANTIC_WITNESSES = {"not_first": _witness_first, "not_last": _witness_last,
                      "minimum_not_maximum": _witness_size,
                      "cell_count_not_bbox_area": _witness_bbox,
                      "marker_filters_distractors": _witness_marker,
                      "target_only_mask": _witness_mask}
WITNESS_RIVALS = {"not_first": ["first_neighbor"], "not_last": ["last_neighbor"],
                  "minimum_not_maximum": ["largest_neighbor"],
                  "cell_count_not_bbox_area": ["bbox_area_neighbor"],
                  "marker_filters_distractors": ["global_smallest"],
                  "target_only_mask": ["unmasked_bbox"]}


def lesson_identifiable(demos, query):
    if len(demos) < EXAMPLES_NEEDED:
        return [f"requires {EXAMPLES_NEEDED} demonstrations for the declared curriculum"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
