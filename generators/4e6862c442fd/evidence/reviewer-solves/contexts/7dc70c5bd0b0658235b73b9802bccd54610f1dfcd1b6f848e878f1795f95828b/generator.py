"""Generator for orientation-aware transport of a local color-8 motif.

A source L-frame uses colors 2/3/4 to define an origin and an ordered pair of
perpendicular cardinal basis vectors.  A target L-frame uses colors 5/6/7 in
the same way.  Color-8 cells near the source are expressed in source-local
coordinates and copied to those same coordinates in the target basis.

Version 3 replaces the former retry/fallback distribution and dead palette /
texture metadata with a finite, observable contract.  Eight scheduled profiles
cover every signed-permutation relation between source and target bases, three
canonical motif shapes, larger sparse motifs, and canonical 12x18 scale.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e6862c442fd"
TASK_ID = "4e6862c442fd"
VERSION = "3.0.0"
RULE_HASH = "1e279b7f949b"

SUMMARY = (
    "A sparse 0-background grid contains one SOURCE L-frame: color 2 is its "
    "origin, color 3 marks its local u direction, and color 4 marks its "
    "perpendicular local v direction. A non-rectangular color-8 motif lies at "
    "signed local offsets around that source. A TARGET L-frame similarly uses "
    "colors 5,6,7. Copy every source motif offset to the same (u,v) coordinate "
    "around the target, so the copied motif rotates or reflects with the "
    "target basis. The source, both frames, and all existing cells remain."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are 2,3,4,5,6,7,8",
    "colors 2/3/4 form exactly one ordered perpendicular cardinal source frame",
    "colors 5/6/7 form exactly one ordered perpendicular cardinal target frame",
    "the source motif is one catalogued asymmetric set of 3..5 signed local offsets",
    "every true target-copy cell is in bounds, empty, and disjoint from both frames",
    "source and target teaching clusters are separated by at least one background cell",
]

# Ordered cardinal frames.  The order is stable and therefore a lawful exact
# override codomain.  Each pair is an orthonormal signed-permutation basis.
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BASES = tuple(
    (vx, vy)
    for vx in _CARDINAL
    for vy in _CARDINAL
    if vx[0] * vy[0] + vx[1] * vy[1] == 0
)
_BASIS_MATRICES = tuple(
    ((vx[0], vy[0]), (vx[1], vy[1])) for vx, vy in _BASES
)
_FRAME_LOCAL = frozenset({(0, 0), (1, 0), (0, 1)})

# The first three shapes are the three canonical train/test motifs.  Every
# shape is sparse, signed, asymmetric under u/v swap, and differs from its
# absolute-coordinate image.  Those properties make the intended local-frame
# operation identifiable rather than allowing count, bbox, or sign shortcuts.
_MOTIFS = (
    ((-1, 2), (1, -1), (2, 1)),
    ((-1, 1), (1, 2), (2, 1)),
    ((-2, 1), (1, 2), (2, -1)),
    ((-2, -1), (-1, 2), (1, -2), (2, 2)),
    ((-2, 2), (-1, -2), (1, 1), (2, -1)),
    ((-3, 1), (-1, -2), (1, 3), (2, -1), (3, 2)),
    ((-3, -1), (-2, 2), (1, -3), (2, 1), (3, 3)),
    ((-2, -2), (-1, 3), (1, -1), (2, 2)),
)
_MOTIF_TO_ID = {tuple(sorted(motif)): index for index, motif in enumerate(_MOTIFS)}

# Each profile uses a different relative D4 transform.  Profiles 0..2 remain
# at canonical 12x18 scale and use the exact canonical motif geometries.
_PROFILES = (
    {"grid_h": 12, "grid_w": 18, "relative_transform": 0, "motif_id": 0},
    {"grid_h": 12, "grid_w": 18, "relative_transform": 1, "motif_id": 1},
    {"grid_h": 12, "grid_w": 18, "relative_transform": 2, "motif_id": 2},
    {"grid_h": 12, "grid_w": 18, "relative_transform": 3, "motif_id": 3},
    {"grid_h": 14, "grid_w": 20, "relative_transform": 4, "motif_id": 4},
    {"grid_h": 15, "grid_w": 22, "relative_transform": 5, "motif_id": 5},
    {"grid_h": 16, "grid_w": 24, "relative_transform": 6, "motif_id": 6},
    {"grid_h": 18, "grid_w": 26, "relative_transform": 7, "motif_id": 7},
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "18..26",
    },
    "source_basis": {
        "type": "int",
        "default": "scheduled ordered cardinal basis",
        "valid": "0..7",
    },
    "target_basis": {
        "type": "int",
        "default": "scheduled ordered cardinal basis",
        "valid": "0..7",
    },
    "motif_id": {
        "type": "int",
        "default": "scheduled asymmetric motif",
        "valid": "0..7",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the seed-phased semantic profile for a sequential lesson draw."""
    offsets = {None: 0, "easy": 0, "medium": 2, "hard": 4}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return (int(seed) + int(sample_index) + offsets[difficulty]) % len(_PROFILES)


def _draw_profile_int(ctx, overrides, label, default, lo, hi):
    """Use a pinned profile default while keeping the full override domain."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _add(origin, u, v, basis):
    vx, vy = basis
    return (
        origin[0] + u * vx[0] + v * vy[0],
        origin[1] + u * vx[1] + v * vy[1],
    )


def _cluster_cells(origin, basis, motif):
    frame = tuple(_add(origin, u, v, basis) for u, v in ((0, 0), (1, 0), (0, 1)))
    motif_cells = tuple(_add(origin, u, v, basis) for u, v in motif)
    return frame, motif_cells


def _in_bounds(cell, h, w):
    r, c = cell
    return 0 <= r < h and 0 <= c < w


def _guard(cells, h, w):
    return {
        (rr, cc)
        for r, c in cells
        for rr in range(max(0, r - 1), min(h, r + 2))
        for cc in range(max(0, c - 1), min(w, c + 2))
    }


def _legal_origins(h, w, basis, motif):
    origins = []
    for r in range(h):
        for c in range(w):
            frame, motif_cells = _cluster_cells((r, c), basis, motif)
            cells = frame + motif_cells
            if len(set(cells)) == len(cells) and all(_in_bounds(x, h, w) for x in cells):
                origins.append((r, c))
    return origins


def _place_origins(rng, h, w, source_basis, target_basis, motif):
    source_origins = _legal_origins(h, w, source_basis, motif)
    target_origins = _legal_origins(h, w, target_basis, motif)
    rng.shuffle(source_origins)
    rng.shuffle(target_origins)
    for source_origin in source_origins:
        source_frame, source_motif = _cluster_cells(source_origin, source_basis, motif)
        source_guard = _guard(source_frame + source_motif, h, w)
        for target_origin in target_origins:
            target_frame, target_footprint = _cluster_cells(target_origin, target_basis, motif)
            target_cells = set(target_frame + target_footprint)
            if source_guard.isdisjoint(target_cells):
                return source_origin, target_origin
    raise ValueError(
        "no separated placement for requested axes: "
        f"grid={h}x{w}, source_basis={_BASES.index(source_basis)}, "
        f"target_basis={_BASES.index(target_basis)}, motif={motif!r}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    profile_id = schedule_profile(seed, sample_index, difficulty)
    profile = _PROFILES[profile_id]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", profile["grid_h"], 12, 18)
    w = _draw_profile_int(ctx, overrides, "grid_w", profile["grid_w"], 18, 26)
    # The profile schedule is seed-phased, so ordinary episodes beginning at
    # sample index zero cover every relation across seeds.  Rotate the source
    # basis by a second seed phase so motif identity is not an orientation proxy.
    source_default = (profile_id + (int(seed) % 8)) % 8
    source_basis_id = _draw_profile_int(
        ctx, overrides, "source_basis", source_default, 0, 7
    )
    target_default = _target_basis_for_relation(
        source_basis_id, profile["relative_transform"]
    )
    target_basis_id = _draw_profile_int(
        ctx, overrides, "target_basis", target_default, 0, 7
    )
    motif_id = _draw_profile_int(ctx, overrides, "motif_id", profile["motif_id"], 0, 7)

    source_basis = _BASES[source_basis_id]
    target_basis = _BASES[target_basis_id]
    motif = _MOTIFS[motif_id]
    source_origin, target_origin = _place_origins(
        ctx.draw_rng("placement"), h, w, source_basis, target_basis, motif
    )

    grid = full_grid(h, w, 0)
    source_frame, source_motif = _cluster_cells(source_origin, source_basis, motif)
    target_frame, _ = _cluster_cells(target_origin, target_basis, motif)
    for cell, color in zip(source_frame, (2, 3, 4)):
        grid[cell[0]][cell[1]] = color
    for r, c in source_motif:
        grid[r][c] = 8
    for cell, color in zip(target_frame, (5, 6, 7)):
        grid[cell[0]][cell[1]] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid orientation lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, requested in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != requested:
            raise AssertionError(
                f"axis {axis!r} requested {requested!r}, observed {observed.get(axis)!r}"
            )
    return grid


def _single_position(grid, color, errors):
    positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if len(positions) != 1:
        errors.append(f"expected exactly one color-{color} frame marker, got {len(positions)}")
        return None
    return positions[0]


def _basis_from_markers(origin, u_marker, v_marker, label, errors):
    if origin is None or u_marker is None or v_marker is None:
        return None
    basis = (
        (u_marker[0] - origin[0], u_marker[1] - origin[1]),
        (v_marker[0] - origin[0], v_marker[1] - origin[1]),
    )
    if basis not in _BASES:
        errors.append(
            f"{label} markers do not form an ordered perpendicular cardinal L-frame: {basis!r}"
        )
        return None
    return basis


def _local(origin, basis, point):
    dr = point[0] - origin[0]
    dc = point[1] - origin[1]
    vx, vy = basis
    return (
        dr * vx[0] + dc * vx[1],
        dr * vy[0] + dc * vy[1],
    )


def _matmul(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2))
        for i in range(2)
    )


def _transpose(a):
    return ((a[0][0], a[1][0]), (a[0][1], a[1][1]))


def _target_basis_for_relation(source_basis_id, relation_id):
    target_matrix = _matmul(
        _BASIS_MATRICES[relation_id], _BASIS_MATRICES[source_basis_id]
    )
    return _BASIS_MATRICES.index(target_matrix)


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 12 <= h <= 18:
        errors.append(f"grid height {h} outside 12..18")
    if not 18 <= w <= 26:
        errors.append(f"grid width {w} outside 18..26")

    allowed = {0, 2, 3, 4, 5, 6, 7, 8}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or value not in allowed:
                errors.append(f"cell ({r},{c}) has invalid task color {value!r}")
    if any("invalid task color" in error for error in errors):
        return {"errors": errors}

    positions = {color: _single_position(grid, color, errors) for color in range(2, 8)}
    source_basis = _basis_from_markers(
        positions[2], positions[3], positions[4], "source", errors
    )
    target_basis = _basis_from_markers(
        positions[5], positions[6], positions[7], "target", errors
    )
    motif_cells = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    )
    if not 3 <= len(motif_cells) <= 5:
        errors.append(f"expected 3..5 source motif cells, got {len(motif_cells)}")

    motif: tuple[tuple[int, int], ...] = ()
    motif_id = None
    target_footprint: tuple[tuple[int, int], ...] = ()
    if source_basis is not None and positions[2] is not None:
        motif = tuple(sorted(_local(positions[2], source_basis, point) for point in motif_cells))
        if any(max(abs(u), abs(v)) > 3 for u, v in motif):
            errors.append("source motif has a local offset outside Chebyshev radius 3")
        if any(uv in _FRAME_LOCAL for uv in motif):
            errors.append("source motif overlaps a source frame marker in local coordinates")
        motif_id = _MOTIF_TO_ID.get(motif)
        if motif_id is None:
            errors.append(f"source motif is not a catalogued teaching shape: {motif!r}")

    if target_basis is not None and positions[5] is not None and motif:
        target_footprint = tuple(
            _add(positions[5], u, v, target_basis) for u, v in motif
        )
        for cell in target_footprint:
            if not _in_bounds(cell, h, w):
                errors.append(f"target copy cell {cell} is out of bounds")
            elif grid[cell[0]][cell[1]] != 0:
                errors.append(
                    f"target copy cell {cell} must be empty, found {grid[cell[0]][cell[1]]}"
                )

    source_cells = set(motif_cells)
    source_cells.update(p for p in (positions[2], positions[3], positions[4]) if p is not None)
    target_cells = set(target_footprint)
    target_cells.update(p for p in (positions[5], positions[6], positions[7]) if p is not None)
    if source_cells and target_cells and not _guard(tuple(source_cells), h, w).isdisjoint(target_cells):
        errors.append("source and target clusters must have a one-cell background separation")

    relative_transform = None
    if source_basis is not None and target_basis is not None:
        relative_matrix = _matmul(
            _BASIS_MATRICES[_BASES.index(target_basis)],
            _transpose(_BASIS_MATRICES[_BASES.index(source_basis)]),
        )
        relative_transform = _BASIS_MATRICES.index(relative_matrix)

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "source_origin": positions.get(2),
        "target_origin": positions.get(5),
        "source_basis_value": source_basis,
        "target_basis_value": target_basis,
        "source_basis": _BASES.index(source_basis) if source_basis in _BASES else None,
        "target_basis": _BASES.index(target_basis) if target_basis in _BASES else None,
        "motif": motif,
        "motif_id": motif_id,
        "motif_cells": motif_cells,
        "target_footprint": target_footprint,
        "relative_transform": relative_transform,
    }


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {axis: analysis[axis] for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def _paint_local(grid, origin, basis, offsets):
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    for u, v in offsets:
        r, c = _add(origin, u, v, basis)
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = 8
    return out


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _paint_local(
        grid,
        analysis["target_origin"],
        analysis["target_basis_value"],
        analysis["motif"],
    )


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    motif = set(analysis["motif"])
    us = [u for u, _ in motif]
    vs = [v for _, v in motif]
    bbox_area = (max(us) - min(us) + 1) * (max(vs) - min(vs) + 1)
    return {
        **observe_overrides(grid),
        "relative_transform": analysis["relative_transform"],
        "motif_size": len(motif),
        "has_negative_u": any(u < 0 for u, _ in motif),
        "has_negative_v": any(v < 0 for _, v in motif),
        "mixed_quadrants": len({(u > 0, v > 0) for u, v in motif}) >= 3,
        "sparse_bbox": len(motif) < bbox_area,
        "canonical_scale": analysis["grid_h"] == 12 and analysis["grid_w"] == 18,
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons = []
    if (analysis["grid_h"], analysis["grid_w"]) != (12, 18):
        reasons.append("canonical inputs are 12x18")
    if len(analysis["motif"]) != 3:
        reasons.append("canonical inputs contain a three-cell source motif")
    return reasons


def _valid_obs(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


def _rival_global_translation(grid):
    a = _analyze(grid)
    if a["errors"]:
        raise ValueError("; ".join(a["errors"]))
    offsets = [
        (r - a["source_origin"][0], c - a["source_origin"][1])
        for r, c in a["motif_cells"]
    ]
    return _paint_local(grid, a["target_origin"], _BASES[3], offsets)


def _rival_ignore_source_basis(grid):
    a = _analyze(grid)
    if a["errors"]:
        raise ValueError("; ".join(a["errors"]))
    offsets = [
        (r - a["source_origin"][0], c - a["source_origin"][1])
        for r, c in a["motif_cells"]
    ]
    return _paint_local(grid, a["target_origin"], a["target_basis_value"], offsets)


def _rival_swap_local_axes(grid):
    a = _analyze(grid)
    if a["errors"]:
        raise ValueError("; ".join(a["errors"]))
    return _paint_local(
        grid,
        a["target_origin"],
        a["target_basis_value"],
        [(v, u) for u, v in a["motif"]],
    )


def _rival_absolute_offsets(grid):
    a = _analyze(grid)
    if a["errors"]:
        raise ValueError("; ".join(a["errors"]))
    return _paint_local(
        grid,
        a["target_origin"],
        a["target_basis_value"],
        [(abs(u), abs(v)) for u, v in a["motif"]],
    )


def _rival_bbox_fill(grid):
    a = _analyze(grid)
    if a["errors"]:
        raise ValueError("; ".join(a["errors"]))
    us = [u for u, _ in a["motif"]]
    vs = [v for _, v in a["motif"]]
    offsets = [
        (u, v)
        for u in range(min(us), max(us) + 1)
        for v in range(min(vs), max(vs) + 1)
    ]
    return _paint_local(grid, a["target_origin"], a["target_basis_value"], offsets)


def _rival_fixed_motif_zero(grid):
    a = _analyze(grid)
    if a["errors"]:
        raise ValueError("; ".join(a["errors"]))
    return _paint_local(grid, a["target_origin"], a["target_basis_value"], _MOTIFS[0])


def _rival_positive_quadrant_only(grid):
    a = _analyze(grid)
    if a["errors"]:
        raise ValueError("; ".join(a["errors"]))
    offsets = [(u, v) for u, v in a["motif"] if u >= 0 and v >= 0]
    return _paint_local(grid, a["target_origin"], a["target_basis_value"], offsets)


SEMANTIC_RIVALS = {
    "global_translation": _rival_global_translation,
    "ignore_source_basis": _rival_ignore_source_basis,
    "swap_local_axes": _rival_swap_local_axes,
    "absolute_offsets": _rival_absolute_offsets,
    "bbox_fill": _rival_bbox_fill,
    "fixed_motif_zero": _rival_fixed_motif_zero,
    "positive_quadrant_only": _rival_positive_quadrant_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These are deliberately lesson competitors, not canonical shortcuts: each is
# refuted by at least one labeled canonical pair.
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], Any]] = {}

SEMANTIC_WITNESSES = {
    **{
        f"relative_transform_{index}": (
            lambda grid, index=index: _valid_obs(
                grid, lambda obs: obs["relative_transform"] == index
            )
        )
        for index in range(8)
    },
    "source_basis_is_read": lambda grid: _valid_obs(
        grid, lambda obs: obs["source_basis"] != 3
    ),
    "signed_offsets_preserved": lambda grid: _valid_obs(
        grid, lambda obs: obs["has_negative_u"] and obs["has_negative_v"]
    ),
    "axis_order_preserved": lambda grid: _valid_obs(grid, lambda obs: True),
    "sparse_shape_not_bbox": lambda grid: _valid_obs(
        grid, lambda obs: obs["sparse_bbox"]
    ),
    "nonfixed_motif": lambda grid: _valid_obs(
        grid, lambda obs: obs["motif_id"] != 0
    ),
    "canonical_scale": lambda grid: _valid_obs(
        grid, lambda obs: obs["canonical_scale"] and obs["motif_size"] == 3
    ),
    "five_cell_motif": lambda grid: _valid_obs(
        grid, lambda obs: obs["motif_size"] == 5
    ),
}
WITNESS_RIVALS = {
    **{f"relative_transform_{index}": ["global_translation"] for index in range(8) if index != 3},
    "relative_transform_3": ["swap_local_axes"],
    "source_basis_is_read": ["ignore_source_basis"],
    "signed_offsets_preserved": ["absolute_offsets", "positive_quadrant_only"],
    "axis_order_preserved": ["swap_local_axes"],
    "sparse_shape_not_bbox": ["bbox_fill"],
    "nonfixed_motif": ["fixed_motif_zero"],
    "canonical_scale": ["swap_local_axes"],
    "five_cell_motif": ["bbox_fill"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful local-frame lesson: " + "; ".join(query_errors)]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with local-frame transport")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
            else:
                reasons.append(
                    f"demos fail to refute competitor {name!r}, even though "
                    "it happens to agree on this query"
                )
    return reasons
