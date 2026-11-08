"""Generator for arc_additional_puzzle_bank_volume18:M126.

Rule: find each same-color nonzero 4-connected object, crop it to its own
bounding box, sort the crops by object cell count from smallest to largest,
and concatenate them left-to-right with one zero separator column.

The four-sample curriculum schedule alternates exact canonical linked profiles,
broad free-polyomino morphology, and a guaranteed size-7/8/9 counterexample to
bounding-box, max-span, boundary-perimeter, boundary-cell, adjacency-edge, and
finite-template ordering.
Every ordinary board also places the objects in a row-major order different from
size order. Thus each four-demo lesson refutes the declared shortcut family while
retaining substantial support for the empirical canonical manifold.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "056999828b88"
TASK_ID = "056999828b88"
VERSION = "6.1.0"
RULE_HASH = "d2d58f482c81"
SUMMARY = (
    "Three or four separated, single-color objects have distinct cell counts. "
    "The oracle crops them and packs them left-to-right by increasing cell "
    "count with one zero gutter. A four-sample schedule preserves exact "
    "canonical linked profiles, ranges across free polyominoes through size "
    "six, and uses a dedicated size-nine branch to guarantee counterexamples "
    "to scan-, color-, bounding-box-, max-span-, boundary-perimeter-, "
    "adjacency-edge-, boundary-cell-, descending-size-, and finite-template "
    "ordering."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.08

INVARIANTS = [
    "background is 0 and remains the strict majority color",
    "3-4 single-color 4-connected objects have distinct sizes in 1..9; colors may repeat",
    "objects are separated by at least one cell in 8-neighborhood",
    "ordinary row-major discovery order differs from increasing-size order",
    "the packed output is a lawful 1..30 by 1..30 ARC grid",
    "sample_index modulo four covers exact canonical, repeated-color morphology, and multi-rival counterexamples",
]

AXES = {
    "grid_h": {"type": "int", "default": "uniform 8..10", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "uniform 10..12", "valid": "10..12"},
    "n_objects": {
        "type": "int",
        "default": "uniform 3..4",
        "valid": "3..4",
        "doc": "Number of separated objects with distinct cell counts.",
    },
}

_VALID_H = (8, 10)
_VALID_W = (10, 12)
_VALID_N = (3, 4)

_MONO = ((0, 0),)
_DOMINO = ((0, 0), (0, 1))
_L3 = ((0, 0), (1, 0), (1, 1))
_LINE3 = ((0, 0), (0, 1), (0, 2))
_SQUARE4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_ZIG4 = ((0, 0), (1, 0), (1, 1), (2, 1))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_LINE4 = ((0, 0), (0, 1), (0, 2), (0, 3))
_CROSS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_P5 = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))
_RECT6 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))
_L6 = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 1))
_BRANCHED7 = ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 3))
_DOUBLE_CORE8 = (
    (0, 1),
    (0, 2),
    (1, 0),
    (1, 1),
    (1, 2),
    (1, 3),
    (2, 1),
    (2, 2),
)
_BRIDGE9 = (
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 5),
    (1, 1),
    (1, 3),
    (1, 4),
    (1, 5),
)

_SHAPES_BY_SIZE = {
    1: (_MONO,),
    2: (_DOMINO,),
    3: (_L3, _LINE3),
    4: (_SQUARE4, _ZIG4, _T4),
    5: (_CROSS5, _P5),
    6: (_RECT6, _L6),
}


def _normalize(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _d4_variants(cells):
    pts = tuple(cells)
    variants = set()
    for reflect in (False, True):
        for turns in range(4):
            transformed = []
            for r, c in pts:
                x, y = r, -c if reflect else c
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            variants.add(_normalize(transformed))
    return tuple(sorted(variants))


def _shape_key(cells):
    return min(_d4_variants(cells))


def _orient(cells, rng):
    return rng.choice(_d4_variants(cells))


def _narrow_orient(cells, rng):
    """Choose a D4 orientation with the minimum crop width."""
    variants = _d4_variants(cells)
    widths = {
        shape: max(c for _, c in shape) + 1
        for shape in variants
    }
    minimum = min(widths.values())
    return rng.choice(tuple(shape for shape in variants if widths[shape] == minimum))


@lru_cache(maxsize=None)
def _free_polyominoes(size):
    """Return all free polyominoes of ``size`` as normalized D4 keys."""
    if type(size) is not int or not 1 <= size <= 6:
        raise ValueError(f"polyomino size must be an integer in 1..6, got {size!r}")
    if size == 1:
        return (_MONO,)

    shapes = set()
    for smaller in _free_polyominoes(size - 1):
        cells = set(smaller)
        frontier = {
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if (r + dr, c + dc) not in cells
        }
        for cell in frontier:
            shapes.add(_shape_key(cells | {cell}))
    return tuple(sorted(shapes))


@lru_cache(maxsize=None)
def _teaching_shapes(size):
    """Broad, placement-friendly morphology pool used by ordinary draws."""
    return tuple(
        shape
        for shape in _free_polyominoes(size)
        if max(
            max(r for r, _ in shape) + 1,
            max(c for _, c in shape) + 1,
        )
        <= 4
    )


_MONO_KEY = _shape_key(_MONO)
_DOMINO_KEY = _shape_key(_DOMINO)
_L3_KEY = _shape_key(_L3)
_SQUARE4_KEY = _shape_key(_SQUARE4)
_ZIG4_KEY = _shape_key(_ZIG4)
_LEGACY_SHAPE_KEYS = frozenset(
    _shape_key(shape)
    for shapes in _SHAPES_BY_SIZE.values()
    for shape in shapes
)
_LEGACY_SHAPE_RANK = {
    _shape_key(shape): size
    for size, shapes in _SHAPES_BY_SIZE.items()
    for shape in shapes
}

# Exact linked empirical profiles from all four train inputs and the held-out
# test input.  Shape keys are quotiented by D4 because orientation does not
# affect the rule; dimensions, color-to-size linkage, and morphology remain
# linked rather than being split into permissive marginals.
_CANONICAL_LINKED_PROFILES = {
    (8, 12, ((2, 1, _MONO_KEY), (3, 2, _DOMINO_KEY), (4, 3, _L3_KEY))),
    (9, 11, ((2, 2, _DOMINO_KEY), (3, 1, _MONO_KEY), (4, 4, _SQUARE4_KEY))),
    (10, 12, ((2, 3, _L3_KEY), (3, 1, _MONO_KEY), (4, 2, _DOMINO_KEY))),
    (8, 10, ((2, 4, _ZIG4_KEY), (3, 2, _DOMINO_KEY), (4, 1, _MONO_KEY))),
    (9, 12, ((2, 1, _MONO_KEY), (3, 3, _L3_KEY), (4, 2, _DOMINO_KEY))),
}
_CANONICAL_BY_DIMS = {
    (h, w): profile
    for h, w, profile in _CANONICAL_LINKED_PROFILES
}


def _components(grid):
    """Same-color 4-connected objects in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"color": color, "cells": tuple(sorted(cells))})
    return out


def _component_signature(obj):
    cells = obj["cells"]
    return (obj["color"], len(cells), _shape_key(cells))


def _linked_profile(grid):
    comps = _components(grid)
    linked = tuple(sorted(_component_signature(obj) for obj in comps))
    return (len(grid), len(grid[0]), linked)


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _crop_piece(obj):
    r1, c1, r2, c2 = _bbox(obj["cells"])
    cells = tuple(sorted((r - r1, c - c1) for r, c in obj["cells"]))
    return {
        "color": obj["color"],
        "cells": cells,
        "size": len(cells),
        "h": r2 - r1 + 1,
        "w": c2 - c1 + 1,
        "first": min(obj["cells"]),
    }


def _pack_with_key(grid, key):
    pieces = [_crop_piece(obj) for obj in _components(grid)]
    pieces.sort(key=key)
    if not pieces:
        return [[0]]
    out_h = max(piece["h"] for piece in pieces)
    out_w = sum(piece["w"] for piece in pieces) + len(pieces) - 1
    out = full_grid(out_h, out_w, 0)
    offset = 0
    for piece in pieces:
        for r, c in piece["cells"]:
            out[r][offset + c] = piece["color"]
        offset += piece["w"] + 1
    return out


def _size_pack(grid):
    return _pack_with_key(grid, lambda p: (p["size"], p["color"]))


def _color_pack(grid):
    return _pack_with_key(grid, lambda p: p["color"])


def _scan_pack(grid):
    return _pack_with_key(grid, lambda p: p["first"])


def _bbox_area_pack(grid):
    return _pack_with_key(grid, lambda p: (p["h"] * p["w"], p["color"]))


def _bbox_semiperimeter_pack(grid):
    return _pack_with_key(grid, lambda p: (p["h"] + p["w"], p["color"]))


def _boundary_perimeter(piece):
    cells = set(piece["cells"])
    return sum(
        (r + dr, c + dc) not in cells
        for r, c in cells
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def _boundary_perimeter_pack(grid):
    return _pack_with_key(grid, lambda p: (_boundary_perimeter(p), p["color"]))


def _adjacency_edges(piece):
    cells = set(piece["cells"])
    return sum(
        (r + 1, c) in cells for r, c in cells
    ) + sum(
        (r, c + 1) in cells for r, c in cells
    )


def _adjacency_edges_pack(grid):
    return _pack_with_key(grid, lambda p: (_adjacency_edges(p), p["color"]))


def _boundary_cells(piece):
    cells = set(piece["cells"])
    return sum(
        any(
            (r + dr, c + dc) not in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        for r, c in cells
    )


def _boundary_cells_pack(grid):
    return _pack_with_key(grid, lambda p: (_boundary_cells(p), p["color"]))


def _max_span_shape_pack(grid):
    return _pack_with_key(
        grid,
        lambda p: (
            max(p["h"], p["w"]),
            _shape_key(p["cells"]),
            p["color"],
        ),
    )


def _min_span_shape_pack(grid):
    return _pack_with_key(
        grid,
        lambda p: (
            min(p["h"], p["w"]),
            _shape_key(p["cells"]),
            p["color"],
        ),
    )


def _descending_size_pack(grid):
    return _pack_with_key(grid, lambda p: (-p["size"], p["color"]))


def _legacy_shape_pack(grid):
    """Rival: rank memorized legacy templates; send unseen shapes last."""
    return _pack_with_key(
        grid,
        lambda p: (
            _LEGACY_SHAPE_RANK.get(_shape_key(p["cells"]), 99),
            p["color"],
        ),
    )


def _place_one(grid, rng, cells, color, *, margin):
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if h - 2 * margin < sh or w - 2 * margin < sw:
        return False
    for _ in range(160):
        r0 = rng.randint(margin, h - margin - sh)
        c0 = rng.randint(margin, w - margin - sw)
        spots = [(r0 + r, c0 + c) for r, c in cells]
        if any(
            grid[rr][cc] != 0
            for r, c in spots
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 1), min(w, c + 2))
        ):
            continue
        for r, c in spots:
            grid[r][c] = color
        return True
    return False


def _exact_profile_pieces(h, w, rng):
    profile = _CANONICAL_BY_DIMS[(h, w)]
    key_to_base = {
        _MONO_KEY: _MONO,
        _DOMINO_KEY: _DOMINO,
        _L3_KEY: _L3,
        _SQUARE4_KEY: _SQUARE4,
        _ZIG4_KEY: _ZIG4,
    }
    return [
        {
            "color": color,
            "size": size,
            "shape": _orient(key_to_base[key], rng),
        }
        for color, size, key in sorted(profile, key=lambda item: item[1])
    ]


_GENERAL_SIZE_PROFILES = {
    3: (
        (1, 2, 3),
        (1, 2, 4),
        (1, 3, 5),
        (2, 4, 6),
        (3, 5, 6),
    ),
    4: (
        (1, 2, 3, 4),
        (1, 2, 4, 5),
        (1, 3, 5, 6),
        (2, 3, 5, 6),
    ),
}


def _generalized_morphology_pieces(
    n, rng, *, color_conflict, max_packed_width
):
    sizes = rng.choice(_GENERAL_SIZE_PROFILES[n])
    colors = rng.sample(range(1, 10), n)
    if color_conflict and colors == sorted(colors):
        colors[-1], colors[-2] = colors[-2], colors[-1]
    for _ in range(240):
        shapes = [
            _narrow_orient(rng.choice(_teaching_shapes(size)), rng)
            for size in sizes
        ]
        packed_width = sum(max(c for _, c in shape) + 1 for shape in shapes) + n - 1
        if packed_width <= max_packed_width:
            return [
                {"color": color, "size": size, "shape": shape}
                for size, color, shape in zip(sizes, colors, shapes)
            ]
    raise ValueError(
        f"could not choose {n} compact crops within packed width {max_packed_width}"
    )


def _shortcut_conflict_pieces(n, rng):
    """Guarantee disagreements with every declared canonical shortcut."""
    sizes = [7, 8, 9] if n == 3 else [1, 7, 8, 9]
    fixed = {1: _MONO, 7: _BRANCHED7, 8: _DOUBLE_CORE8, 9: _BRIDGE9}
    colors = rng.sample(range(1, 10), n)
    index7, index8 = sizes.index(7), sizes.index(8)
    if colors[index8] > colors[index7]:
        colors[index7], colors[index8] = colors[index8], colors[index7]
    return [
        {"color": color, "size": size, "shape": _narrow_orient(fixed[size], rng)}
        for size, color in zip(sizes, colors)
    ]


def _build_board(h, w, pieces, rng, *, margin):
    """Place pieces with a gap and force row-major order != size order."""
    for _ in range(240):
        grid = full_grid(h, w, 0)
        order = list(pieces)
        rng.shuffle(order)
        if not all(
            _place_one(grid, rng, piece["shape"], piece["color"], margin=margin)
            for piece in order
        ):
            continue
        comps = _components(grid)
        scan_sizes = [len(obj["cells"]) for obj in comps]
        if scan_sizes == sorted(scan_sizes):
            continue
        return grid
    raise ValueError(
        f"could not place {len(pieces)} separated objects on {h}x{w} "
        "with a scan-order conflict"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", *_VALID_H)
    w = ctx.draw_int("grid_w", *_VALID_W)
    n = ctx.draw_int("n_objects", *_VALID_N)
    rng = ctx.draw_rng("scene")

    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    slot = (sample_index + band_offset) % 4
    if slot in (0, 1) and n == 3 and (h, w) in _CANONICAL_BY_DIMS:
        pieces = _exact_profile_pieces(h, w, rng)
        margin = 1
    elif slot == 2:
        pieces = _generalized_morphology_pieces(n, rng, color_conflict=True, max_packed_width=w)
        pieces[-1]["color"] = pieces[0]["color"]
        margin = 0
    elif slot == 3:
        pieces = _shortcut_conflict_pieces(n, rng)
        margin = 0
    else:
        pieces = _generalized_morphology_pieces(
            n,
            rng,
            color_conflict=True,
            max_packed_width=w,
        )
        margin = 0

    return _build_board(h, w, pieces, rng, margin=margin)


SCHEDULE_PROFILES = ("slot_0", "slot_1", "slot_2", "slot_3")


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic four-slot curriculum schedule to the gate."""
    del seed
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return f"slot_{(sample_index + band_offset) % 4}"


def observe_overrides(grid):
    """Recover every declared exact semantic axis from the returned grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_objects": len(_components(grid)) if grid and grid[0] else 0,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed/rule-hiding scenes while accepting all canonical inputs."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid is ragged"]
    h = len(grid)
    errors = []
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"grid width {w} outside {_VALID_W[0]}..{_VALID_W[1]}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors

    comps = _components(grid)
    if not (_VALID_N[0] <= len(comps) <= _VALID_N[1]):
        errors.append(f"expected 3-4 objects, got {len(comps)}")
        return errors

    # Color is component-local; disconnected objects may share it.
    sizes = [len(obj["cells"]) for obj in comps]
    if len(set(sizes)) != len(sizes):
        errors.append(f"object sizes must be distinct, got {sorted(sizes)}")
    if any(not 1 <= size <= 9 for size in sizes):
        errors.append(f"object sizes must stay in 1..9, got {sorted(sizes)}")

    owner = {}
    for index, obj in enumerate(comps):
        for cell in obj["cells"]:
            owner[cell] = index
    touching = False
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != index:
                    touching = True
                    break
            if touching:
                break
        if touching:
            break
    if touching:
        errors.append("distinct objects must have a one-cell 8-neighborhood gap")

    nonzero = sum(value != 0 for row in grid for value in row)
    if nonzero * 2 >= h * w:
        errors.append("background 0 must be the strict majority")

    pieces = [_crop_piece(obj) for obj in comps]
    packed_h = max(piece["h"] for piece in pieces)
    packed_w = sum(piece["w"] for piece in pieces) + len(pieces) - 1
    if not (1 <= packed_h <= 30 and 1 <= packed_w <= 30):
        errors.append(f"packed output would be out of ARC bounds: {packed_h}x{packed_w}")
    return errors


def strict_canonical_like(grid):
    """Exact linked empirical manifold, with D4 orientation treated as nuisance."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = _linked_profile(grid)
    if profile not in _CANONICAL_LINKED_PROFILES:
        return [f"linked profile {profile!r} is not one of the five canonical profiles"]
    h, w = len(grid), len(grid[0])
    if any(
        value != 0 and (r in (0, h - 1) or c in (0, w - 1))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
    ):
        return ["canonical objects do not touch the input border"]
    return []


def _has_color_order_conflict(grid):
    return _size_pack(grid) != _color_pack(grid)


def _has_scan_order_conflict(grid):
    return _size_pack(grid) != _scan_pack(grid)


def _has_bbox_area_conflict(grid):
    return _size_pack(grid) != _bbox_area_pack(grid)


def _has_bbox_semiperimeter_conflict(grid):
    return _size_pack(grid) != _bbox_semiperimeter_pack(grid)


def _has_boundary_perimeter_conflict(grid):
    return _size_pack(grid) != _boundary_perimeter_pack(grid)


def _has_adjacency_edges_conflict(grid):
    return _size_pack(grid) != _adjacency_edges_pack(grid)


def _has_boundary_cells_conflict(grid):
    return _size_pack(grid) != _boundary_cells_pack(grid)


def _has_max_span_shape_conflict(grid):
    return _size_pack(grid) != _max_span_shape_pack(grid)


def _has_min_span_shape_conflict(grid):
    return _size_pack(grid) != _min_span_shape_pack(grid)


def _has_descending_size_conflict(grid):
    return _size_pack(grid) != _descending_size_pack(grid)


def _has_legacy_shape_lookup_conflict(grid):
    return _size_pack(grid) != _legacy_shape_pack(grid)


def _has_three_objects(grid):
    return len(_components(grid)) == 3


def _has_four_objects(grid):
    return len(_components(grid)) == 4


def _has_123_profile(grid):
    return sorted(len(obj["cells"]) for obj in _components(grid)) == [1, 2, 3]


def _has_124_profile(grid):
    return sorted(len(obj["cells"]) for obj in _components(grid)) == [1, 2, 4]


def _has_edge_object(grid):
    h, w = len(grid), len(grid[0])
    return any(
        value != 0 and (r in (0, h - 1) or c in (0, w - 1))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
    )


def _pack_pieces(pieces, key):
    pieces = sorted(pieces, key=key)
    if not pieces:
        return [[0]]
    out_h = max(piece["h"] for piece in pieces)
    out_w = sum(piece["w"] for piece in pieces) + len(pieces) - 1
    out = full_grid(out_h, out_w, 0)
    offset = 0
    for piece in pieces:
        for r, c in piece["cells"]:
            out[r][offset + c] = piece["color"]
        offset += piece["w"] + 1
    return out

def _color_union_pack(grid):
    """Rival: treat all cells of one color as one object, ignoring connectivity."""
    grouped = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                grouped[color].append((r, c))
    pieces = [
        _crop_piece({"color": color, "cells": tuple(cells)})
        for color, cells in grouped.items()
    ]
    return _pack_pieces(pieces, lambda p: (p["size"], p["color"]))

def _global_color_frequency_pack(grid):
    """Rival: crop components, but rank them by whole-board color frequency."""
    counts = defaultdict(int)
    for row in grid:
        for color in row:
            if color:
                counts[color] += 1
    return _pack_with_key(grid, lambda p: (counts[p["color"]], p["color"]))

def _has_color_union_conflict(grid):
    return _size_pack(grid) != _color_union_pack(grid)

def _has_global_color_frequency_conflict(grid):
    return _size_pack(grid) != _global_color_frequency_pack(grid)

def _has_repeated_color_objects(grid):
    comps = _components(grid)
    return len({obj["color"] for obj in comps}) < len(comps)


SEMANTIC_WITNESSES = {
    "strict_canonical_profile": lambda grid: not strict_canonical_like(grid),
    "three_objects": _has_three_objects,
    "four_objects": _has_four_objects,
    "canonical_sizes_1_2_3": _has_123_profile,
    "canonical_sizes_1_2_4": _has_124_profile,
    "color_order_conflict": _has_color_order_conflict,
    "scan_order_conflict": _has_scan_order_conflict,
    "bbox_area_conflict": _has_bbox_area_conflict,
    "bbox_semiperimeter_conflict": _has_bbox_semiperimeter_conflict,
    "boundary_perimeter_conflict": _has_boundary_perimeter_conflict,
    "adjacency_edges_conflict": _has_adjacency_edges_conflict,
    "boundary_cells_conflict": _has_boundary_cells_conflict,
    "max_span_shape_conflict": _has_max_span_shape_conflict,
    "min_span_shape_conflict": _has_min_span_shape_conflict,
    "descending_size_conflict": _has_descending_size_conflict,
    "legacy_shape_lookup_conflict": _has_legacy_shape_lookup_conflict,
    "edge_placement_generalization": _has_edge_object,
    "repeated_color_objects": _has_repeated_color_objects,
    "color_union_conflict": _has_color_union_conflict,
    "global_color_frequency_conflict": _has_global_color_frequency_conflict,
}

SEMANTIC_RIVALS = {
    "color_order": _color_pack,
    "scan_order": _scan_pack,
    "bbox_area_order": _bbox_area_pack,
    "bbox_semiperimeter_order": _bbox_semiperimeter_pack,
    "boundary_perimeter_order": _boundary_perimeter_pack,
    "adjacency_edges_order": _adjacency_edges_pack,
    "boundary_cells_order": _boundary_cells_pack,
    "max_span_shape_order": _max_span_shape_pack,
    "min_span_shape_order": _min_span_shape_pack,
    "descending_size": _descending_size_pack,
    "legacy_shape_lookup": _legacy_shape_pack,
    "color_union": _color_union_pack,
    "global_color_frequency": _global_color_frequency_pack,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "bbox_area_order": _bbox_area_pack,
    "bbox_semiperimeter_order": _bbox_semiperimeter_pack,
    "boundary_perimeter_order": _boundary_perimeter_pack,
    "adjacency_edges_order": _adjacency_edges_pack,
    "boundary_cells_order": _boundary_cells_pack,
    "max_span_shape_order": _max_span_shape_pack,
    "min_span_shape_order": _min_span_shape_pack,
    "legacy_shape_lookup": _legacy_shape_pack,
    "color_union": _color_union_pack,
    "global_color_frequency": _global_color_frequency_pack,
}

WITNESS_RIVALS = {
    "color_order_conflict": ["color_order"],
    "scan_order_conflict": ["scan_order"],
    "bbox_area_conflict": ["bbox_area_order"],
    "bbox_semiperimeter_conflict": ["bbox_semiperimeter_order"],
    "boundary_perimeter_conflict": ["boundary_perimeter_order"],
    "adjacency_edges_conflict": ["adjacency_edges_order"],
    "boundary_cells_conflict": ["boundary_cells_order"],
    "max_span_shape_conflict": ["max_span_shape_order"],
    "min_span_shape_conflict": ["min_span_shape_order"],
    "descending_size_conflict": ["descending_size"],
    "legacy_shape_lookup_conflict": ["legacy_shape_lookup"],
    "color_union_conflict": ["color_union"],
    "global_color_frequency_conflict": ["global_color_frequency"],
}

BRANCH_WITNESSES = {
    "strict_canonical_profile",
    "three_objects",
    "four_objects",
    "canonical_sizes_1_2_3",
    "canonical_sizes_1_2_4",
    "edge_placement_generalization",
    "repeated_color_objects",
}


def lesson_identifiable(demos, query):
    """Reject lessons unless every declared wrong rule is refuted by a demo."""
    errors = []
    if not demos:
        return ["lesson has no demonstrations"]
    for index, pair in enumerate(demos):
        inp, out = pair["input"], pair["output"]
        expected = _size_pack(inp)
        if out != expected:
            errors.append(f"demo {index} does not match increasing cell-count packing")
    if errors:
        return errors

    for name, candidate in LESSON_COMPETITORS.items():
        if all(candidate(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competing rule {name!r} fits every demonstration")
    query_input = query["input"]
    official = query["output"]
    if _size_pack(query_input) != official:
        errors.append("query output does not match increasing cell-count packing")

    linked_shapes = {
        tuple(sorted((len(obj["cells"]), _shape_key(obj["cells"])) for obj in _components(pair["input"])))
        for pair in demos
    }
    if len(linked_shapes) < 2:
        errors.append("demos do not vary the linked size/morphology profile")
    color_size_maps = {
        tuple(sorted((len(obj["cells"]), obj["color"]) for obj in _components(pair["input"])))
        for pair in demos
    }
    if len(color_size_maps) < 2:
        errors.append("demos do not vary color-to-size linkage")
    if not any(_has_scan_order_conflict(pair["input"]) for pair in demos):
        errors.append("demos never refute row-major scan-order packing")
    if not any(_has_color_order_conflict(pair["input"]) for pair in demos):
        errors.append("demos never refute color-order packing")
    if not any(_has_bbox_area_conflict(pair["input"]) for pair in demos):
        errors.append("demos never refute bbox-area packing")
    if not any(_has_legacy_shape_lookup_conflict(pair["input"]) for pair in demos):
        errors.append("demos never refute finite-template shape lookup")
    return errors
