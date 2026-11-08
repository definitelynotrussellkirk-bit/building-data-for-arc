"""Input generator for ARC task b2862040.

Selected rule
-------------
The input uses color 9 as background and color 1 for 4-connected objects.
Recolor a whole object from 1 to 8 exactly when *one complete color-9
connected component* lies strictly inside that object's bounding box.

The public controls are deliberately small and exactly recoverable from the
returned pixels.  Geometry remains varied internally: every generated instance
contains an irregular positive object and an open-bounding-box negative object,
so demonstrations rule out two common visual shortcuts without exposing
negative fixtures as ordinary textures.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9af68e46cf69"
TASK_ID = GENERATOR_ID
RULE_HASH = "7fd2884c3200"
VERSION = "3.0.0"
SUMMARY = (
    "On a color-9 background, several disconnected color-1 objects are shown. "
    "An object changes to color 8 iff a complete background-9 region is wholly "
    "strictly inside that object's bounding box; no-hole objects stay color 1. "
    "Generated lessons include irregular hole-bearing objects and open-bbox "
    "decoys, not only rectangular frames."
)

INVARIANTS = [
    "rectangular 9..30 by 11..30 input using only colors 1 and 9",
    "1..3 color-1 components contain a complete interior background region",
    "1..4 color-1 components contain no such region",
    "at least one positive is not a rectangular outline",
    "at least one negative has background inside its bbox but open to outside",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 9..30", "valid": "9..30"},
    "grid_w": {"type": "int", "default": "canonical-weighted 11..30", "valid": "11..30"},
    "n_holey": {"type": "int", "default": "canonical-weighted 1..3", "valid": "1..3"},
    "n_solid": {"type": "int", "default": "canonical-weighted 1..4", "valid": "1..4"},
}

# All advertised endpoint and pairwise combinations are constructively
# supported, including a 9x11 canvas with 3 positive and 4 negative objects.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[object] = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_AXIS_BOUNDS = {
    "grid_h": (9, 30),
    "grid_w": (11, 30),
    "n_holey": (1, 3),
    "n_solid": (1, 4),
}
_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(set(cells))
    if not cells:
        raise ValueError("shape must contain at least one cell")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(
    cells: Sequence[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    """One of the eight dihedral transforms, normalized to nonnegative cells."""
    transformed = []
    for r, c in cells:
        if code == 0:
            point = (r, c)
        elif code == 1:
            point = (c, -r)
        elif code == 2:
            point = (-r, -c)
        elif code == 3:
            point = (-c, r)
        elif code == 4:
            point = (r, -c)
        elif code == 5:
            point = (-r, c)
        elif code == 6:
            point = (c, r)
        elif code == 7:
            point = (-c, -r)
        else:  # pragma: no cover - internal caller contract
            raise ValueError(code)
        transformed.append(point)
    return _normalize(transformed)


def _rect_ring(h: int, w: int) -> tuple[tuple[int, int], ...]:
    return _normalize(
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    )


# First entry is the mandatory irregular positive witness: a 3x3 ring with a
# side branch.  It has a real isolated center but is not any rectangle outline.
_HOLE_SHAPES = (
    _normalize((*_rect_ring(3, 3), (1, 3))),
    _rect_ring(3, 3),
    _rect_ring(4, 3),
    _rect_ring(3, 5),
    _normalize((*_rect_ring(4, 4), (2, 4), (3, 4))),
    _normalize((*_rect_ring(5, 4), (2, 4), (2, 5))),
    _normalize(
        {
            (0, 1), (1, 0), (1, 1), (1, 2), (1, 3),
            (2, 0), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3),
            (4, 3),
        }
    ),
)

# First entry is the mandatory open-bbox negative witness.  Its bbox contains
# background at (1,1), but the opening along the lower edge connects that cell
# to the exterior, so the selected rule must leave the object blue.
_SOLID_SHAPES = (
    _normalize({(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0)}),
    ((0, 0),),
    _normalize({(0, 0), (0, 1)}),
    _normalize({(0, 0), (0, 1), (0, 2)}),
    _normalize({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    _normalize({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)}),
    _normalize({(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)}),
    _normalize(set(_rect_ring(3, 4)) - {(2, 1)}),
    _normalize({(0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0)}),
)


def _literal_int(name: str, value: object, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a literal integer, not {type(value).__name__}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _validate_call(seed, sample_index, difficulty, overrides: dict) -> dict:
    _literal_int("seed", seed)
    _literal_int("sample_index", sample_index, minimum=0)
    if difficulty not in _DIFFICULTIES or (
        difficulty is not None and type(difficulty) is not str
    ):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    clean = dict(overrides)
    for name, value in clean.items():
        if value is None:
            continue
        value = _literal_int(name, value)
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in [{lo}, {hi}], got {value}")
    return clean


def _weighted_axis(ctx, name: str, difficulty: str | None, profile: str) -> int:
    lo, hi = _AXIS_BOUNDS[name]
    values = list(range(lo, hi + 1))
    canonical = {
        "grid_h": (9, 12, 12, 14, 16),
        "grid_w": (11, 11, 13, 15, 15),
        "n_holey": (1, 1, 2, 3, 3),
        "n_solid": (1, 2, 4, 4, 4),
    }[name]
    if profile == "canonical":
        values += list(canonical) * 12
    if difficulty == "easy":
        if name in ("grid_h", "grid_w"):
            values += list(range(lo, min(14, hi) + 1)) * 3
        else:
            values += [lo] * 12
    elif difficulty == "hard":
        if name in ("grid_h", "grid_w"):
            values += list(range(max(lo, 15), hi + 1)) * 3
        else:
            values += [hi] * 12
    return ctx.draw_choice(name, values)


def _shape_size(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _blocked_by(cells: set[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    blocked = set(cells)
    for r, c in tuple(cells):
        for dr, dc in _NEIGHBORS4:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                blocked.add((rr, cc))
    return blocked


def _place_shapes(
    h: int,
    w: int,
    shapes: Sequence[Sequence[tuple[int, int]]],
    rng,
    *,
    node_limit: int = 120_000,
) -> list[list[int]] | None:
    """Place every shape exactly, keeping distinct objects 4-disconnected.

    The search is finite and deterministic for a keyed RNG.  Largest shapes are
    placed first; a one-cell orthogonal moat prevents count drift and prevents a
    second object from occupying a true cavity.
    """
    records = []
    for index, shape in enumerate(shapes):
        shape = tuple(shape)
        sh, sw = _shape_size(shape)
        candidates = [
            tuple((r + dr, c + dc) for dr, dc in shape)
            for r in range(h - sh + 1)
            for c in range(w - sw + 1)
        ]
        rng.shuffle(candidates)
        records.append((index, shape, candidates))
    records.sort(key=lambda item: (-len(item[1]), len(item[2]), item[0]))

    placements: dict[int, tuple[tuple[int, int], ...]] = {}
    visited = 0

    def search(i: int, occupied: set[tuple[int, int]], blocked: set[tuple[int, int]]) -> bool:
        nonlocal visited
        if visited >= node_limit:
            return False
        if i == len(records):
            return True
        _, _, candidates = records[i]
        original_index = records[i][0]
        for cells_tuple in candidates:
            if visited >= node_limit:
                return False
            visited += 1
            cells = set(cells_tuple)
            if cells & blocked:
                continue
            placements[original_index] = cells_tuple
            next_occupied = occupied | cells
            next_blocked = blocked | _blocked_by(cells, h, w)
            if search(i + 1, next_occupied, next_blocked):
                return True
            placements.pop(original_index, None)
        return False

    if not search(0, set(), set()):
        return None
    grid = full_grid(h, w, 9)
    for index in range(len(shapes)):
        for r, c in placements[index]:
            grid[r][c] = 1
    return grid


def _select_shapes(ctx, h: int, w: int, n_holey: int, n_solid: int):
    rng = ctx.draw_rng("shape_catalog")
    crowded = h * w < 150 or n_holey + n_solid >= 6

    hole_pool = _HOLE_SHAPES[:4] if crowded else _HOLE_SHAPES
    solid_pool = _SOLID_SHAPES[:7] if crowded else _SOLID_SHAPES

    holey = [_transform(_HOLE_SHAPES[0], rng.randrange(8))]
    for _ in range(1, n_holey):
        holey.append(_transform(rng.choice(hole_pool), rng.randrange(8)))
    solid = [_transform(_SOLID_SHAPES[0], rng.randrange(8))]
    for _ in range(1, n_solid):
        solid.append(_transform(rng.choice(solid_pool), rng.randrange(8)))
    return holey + solid


def _compact_grid(ctx, h: int, w: int, n_holey: int, n_solid: int):
    """O(1) constructive basis for every advertised control combination.

    The occupied 9x11 block is a proof-of-feasibility for the public domain:
    three positive slots (irregular ring, two 3x3 rings) and four negative
    slots (open-U decoy, three isolated cells), all separated in 4-connectivity.
    Larger canvases receive a keyed translation and reflection of the block.
    """
    hole_slots = (
        (_HOLE_SHAPES[0], (0, 0)),
        (_HOLE_SHAPES[1], (0, 5)),
        (_HOLE_SHAPES[1], (4, 0)),
    )
    solid_slots = (
        (_SOLID_SHAPES[0], (4, 4)),
        (((0, 0),), (0, 9)),
        (((0, 0),), (4, 9)),
        (((0, 0),), (8, 0)),
    )
    local_cells = []
    for shape, (r0, c0) in hole_slots[:n_holey]:
        local_cells.extend((r0 + r, c0 + c) for r, c in shape)
    for shape, (r0, c0) in solid_slots[:n_solid]:
        local_cells.extend((r0 + r, c0 + c) for r, c in shape)

    rng = ctx.draw_rng("compact_layout")
    flip_r = bool(rng.randrange(2))
    flip_c = bool(rng.randrange(2))
    row_offset = rng.randrange(h - 9 + 1)
    col_offset = rng.randrange(w - 11 + 1)
    grid = full_grid(h, w, 9)
    for r, c in local_cells:
        if flip_r:
            r = 8 - r
        if flip_c:
            c = 10 - c
        grid[row_offset + r][col_offset + c] = 1
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "curriculum_profile", ("canonical", "canonical", "canonical", "broad")
    )
    h = _weighted_axis(ctx, "grid_h", difficulty, profile)
    w = _weighted_axis(ctx, "grid_w", difficulty, profile)
    n_holey = _weighted_axis(ctx, "n_holey", difficulty, profile)
    n_solid = _weighted_axis(ctx, "n_solid", difficulty, profile)

    # Dense/small combinations use the explicit feasibility construction;
    # roomy combinations first try richer shapes under a hard search budget.
    if h * w < 170 or n_holey + n_solid >= 6:
        return _compact_grid(ctx, h, w, n_holey, n_solid)
    shapes = _select_shapes(ctx, h, w, n_holey, n_solid)
    grid = _place_shapes(
        h, w, shapes, ctx.draw_rng("layout"), node_limit=3_000
    )
    return grid if grid is not None else _compact_grid(
        ctx, h, w, n_holey, n_solid
    )


def _components(grid: Sequence[Sequence[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS4:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def _bbox(component: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in component),
        min(c for _, c in component),
        max(r for r, _ in component),
        max(c for _, c in component),
    )


def _object_has_hole(
    component: set[tuple[int, int]],
    background_regions: Sequence[set[tuple[int, int]]],
) -> bool:
    r1, c1, r2, c2 = _bbox(component)
    return any(
        region
        and all(r1 < r < r2 and c1 < c < c2 for r, c in region)
        for region in background_regions
    )


def _classify_objects(grid):
    blue_components = _components(grid, 1)
    background_regions = _components(grid, 9)
    holey, solid = [], []
    for component in blue_components:
        (holey if _object_has_hole(component, background_regions) else solid).append(component)
    return holey, solid


def observe_overrides(grid):
    """Recover every exact public control from the returned grid pixels."""
    holey, solid = _classify_objects(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_holey": len(holey),
        "n_solid": len(solid),
    }


def _is_rectangular_outline(component: set[tuple[int, int]]) -> bool:
    r1, c1, r2, c2 = _bbox(component)
    if r2 - r1 < 2 or c2 - c1 < 2:
        return False
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return component == border


def _has_bbox_background(grid, component: set[tuple[int, int]]) -> bool:
    r1, c1, r2, c2 = _bbox(component)
    return any(
        grid[r][c] == 9
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
    )


def self_check(grid, *, difficulty=None, meta=None):
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if not 9 <= len(grid) <= 30:
        errors.append(f"grid height {len(grid)} outside [9,30]")
    if not 11 <= width <= 30:
        errors.append(f"grid width {width} outside [11,30]")
    bad_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or value not in (1, 9)
    ]
    if bad_cells:
        r, c, value = bad_cells[0]
        errors.append(f"cell ({r},{c})={value!r} is not literal color 1 or 9")
        return errors

    holey, solid = _classify_objects(grid)
    if not 1 <= len(holey) <= 3:
        errors.append(f"expected 1..3 hole-bearing objects, found {len(holey)}")
    if not 1 <= len(solid) <= 4:
        errors.append(f"expected 1..4 no-hole objects, found {len(solid)}")
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if isinstance(requested, dict):
            observed = {
                "grid_h": len(grid), "grid_w": width,
                "n_holey": len(holey), "n_solid": len(solid),
            }
            for axis, value in requested.items():
                if axis in observed and value is not None and observed[axis] != value:
                    errors.append(
                        f"requested {axis}={value!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid):
    """The selected training manifold, including all labeled canonical inputs."""
    return self_check(grid)


def _apply_rule(grid):
    """Independent Python oracle mirroring the pinned Racket authority."""
    out = [list(row) for row in grid]
    blue_components = _components(grid, 1)
    background_regions = _components(grid, 9)
    for component in blue_components:
        if _object_has_hole(component, background_regions):
            for r, c in component:
                out[r][c] = 8
    return out


def _rectangular_frames_only(grid):
    """Rival: recolor only exact rectangle outlines, missing irregular holes."""
    out = [list(row) for row in grid]
    background_regions = _components(grid, 9)
    for component in _components(grid, 1):
        if _is_rectangular_outline(component) and _object_has_hole(component, background_regions):
            for r, c in component:
                out[r][c] = 8
    return out


def _any_bbox_background(grid):
    """Rival: any interior 9-cell counts, even when connected to the exterior."""
    out = [list(row) for row in grid]
    for component in _components(grid, 1):
        if _has_bbox_background(grid, component):
            for r, c in component:
                out[r][c] = 8
    return out


def _has_irregular_hole(grid) -> bool:
    holey, _ = _classify_objects(grid)
    return any(not _is_rectangular_outline(component) for component in holey)


def _has_open_bbox_decoy(grid) -> bool:
    _, solid = _classify_objects(grid)
    return any(_has_bbox_background(grid, component) for component in solid)


SEMANTIC_WITNESSES = {
    "irregular_hole": _has_irregular_hole,
    "open_bbox_decoy": _has_open_bbox_decoy,
}
SEMANTIC_RIVALS = {
    "rectangular_frames_only": _rectangular_frames_only,
    "any_bbox_background": _any_bbox_background,
}
WITNESS_RIVALS = {
    "irregular_hole": ["rectangular_frames_only"],
    "open_bbox_decoy": ["any_bbox_background"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject mislabeled or rival-ambiguous generated lessons."""
    errors: list[str] = []
    for index, pair in enumerate(demos):
        try:
            selected = _apply_rule(pair["input"])
            labeled = pair["output"]
        except Exception as exc:  # pragma: no cover - checker supplies pairs
            errors.append(f"demo {index} is malformed: {type(exc).__name__}: {exc}")
            continue
        if selected != labeled:
            errors.append(f"demo {index} conflicts with the selected rule")
    try:
        query_selected = _apply_rule(query["input"])
        query_labeled = query["output"]
    except Exception as exc:  # pragma: no cover - checker supplies a pair
        return errors + [f"query is malformed: {type(exc).__name__}: {exc}"]
    if query_selected != query_labeled:
        errors.append("query label conflicts with the selected rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query_labeled
        except Exception as exc:
            errors.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            errors.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return errors
