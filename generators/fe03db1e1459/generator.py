"""Generator for fe03db1e1459 — copy a blue object by a marker vector.

Colors 2 and 3 define the displacement ``(dr, dc) = pos(3) - pos(2)``.
The Racket oracle copies each color-1 cell by that displacement as color 8,
leaving the input otherwise unchanged except where the copy overwrites it.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fe03db1e1459"
TASK_ID = "fe03db1e1459"
VERSION = "3.0.0"
RULE_HASH = "b6f49ccc5f81"

SUMMARY = (
    "A sparse 9..11 by 12..15 grid contains one connected blue (1) object, "
    "one red (2) marker, and one green (3) marker. The vector from 2 to 3 "
    "is applied to every blue cell, and the translated copy is painted cyan "
    "(8). Canonical-linked profiles cover axis-aligned and diagonal vectors, "
    "positive and negative directions, and both overlapping and disjoint copies."
)

INVARIANTS = [
    "background is color 0 and the only foreground input colors are 1, 2, and 3",
    "there is exactly one color-2 marker and exactly one color-3 marker",
    "the color-1 cells form one 4-connected canonical-shape-class object of 4..6 cells",
    "the 2-to-3 displacement is nonzero and lies in dr=-1..2, dc=-3..2",
    "the entire translated blue object remains in bounds",
    "the translated object does not cover either marker",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "9..11",
    },
    "grid_w": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "12..15",
    },
    "blue_object_size": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "4..6",
    },
    "marker_dr": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "-1..2",
    },
    "marker_dc": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "-3..2",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

# Normalized canonical object masks. Orientation is not answer-bearing, so the
# generator lawfully ranges over each mask's D4 orbit.
_T5 = ((0, 2), (1, 0), (1, 1), (1, 2), (1, 3))
_L4 = ((0, 0), (1, 0), (1, 1), (1, 2))
_RECT6 = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))
_STAIR6 = ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2))

# Every tuple is observed in one of the four train examples or the test input.
# The default schedule cycles these linked profiles in every difficulty band.
_CANONICAL_PROFILES = (
    {"grid_h": 9, "grid_w": 12, "blue_object_size": 5,
     "shape_class": "t5", "mask": _T5, "marker_dr": 1, "marker_dc": 0},
    {"grid_h": 9, "grid_w": 15, "blue_object_size": 4,
     "shape_class": "l4", "mask": _L4, "marker_dr": 2, "marker_dc": 2},
    {"grid_h": 11, "grid_w": 15, "blue_object_size": 6,
     "shape_class": "rect6", "mask": _RECT6, "marker_dr": 1, "marker_dc": -1},
    {"grid_h": 11, "grid_w": 13, "blue_object_size": 6,
     "shape_class": "stair6", "mask": _STAIR6, "marker_dr": 0, "marker_dc": 2},
    {"grid_h": 10, "grid_w": 14, "blue_object_size": 6,
     "shape_class": "rect6", "mask": _RECT6, "marker_dr": -1, "marker_dc": -3},
)


def _normalize(cells) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate(mask: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, -r) for r, c in mask)


def _reflect(mask: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return _normalize((r, -c) for r, c in mask)


def _d4_orbit(mask: tuple[tuple[int, int], ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = set()
    current = _normalize(mask)
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


_SHAPE_ORBITS = {
    "t5": _d4_orbit(_T5),
    "l4": _d4_orbit(_L4),
    "rect6": _d4_orbit(_RECT6),
    "stair6": _d4_orbit(_STAIR6),
}
_SHAPE_CLASS_BY_MASK = {
    mask: name for name, orbit in _SHAPE_ORBITS.items() for mask in orbit
}
_CANONICAL_LINKED_KEYS = {
    (
        profile["grid_h"],
        profile["grid_w"],
        profile["blue_object_size"],
        profile["shape_class"],
        profile["marker_dr"],
        profile["marker_dc"],
    )
    for profile in _CANONICAL_PROFILES
}


def _draw_profile_axis(ctx, overrides, label, default, lo, hi):
    """Use the full declared domain for explicit overrides, otherwise pin the
    keyed draw to the selected linked-profile value."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _shape_for_size(size: int, profile_index: int, rng):
    if size == 4:
        shape_class = "l4"
    elif size == 5:
        shape_class = "t5"
    elif size == 6:
        shape_class = "stair6" if profile_index == 3 else "rect6"
    else:  # guarded by the axis draw; kept loud for direct helper misuse
        raise ValueError(f"unsupported blue_object_size {size}")
    mask = rng.choice(_SHAPE_ORBITS[shape_class])
    return shape_class, mask


def _place_scene(rng, h, w, mask, dr, dc):
    max_r = max(r for r, _ in mask)
    max_c = max(c for _, c in mask)
    rlo = max(0, -dr)
    rhi = min(h - 1 - max_r, h - 1 - max_r - dr)
    clo = max(0, -dc)
    chi = min(w - 1 - max_c, w - 1 - max_c - dc)
    if rlo > rhi or clo > chi:
        raise ValueError(
            f"shape cannot fit with marker delta ({dr},{dc}) in {h}x{w}"
        )

    anchors = [(r, c) for r in range(rlo, rhi + 1) for c in range(clo, chi + 1)]
    rng.shuffle(anchors)
    for ar, ac in anchors:
        obj = {(ar + r, ac + c) for r, c in mask}
        shifted = {(r + dr, c + dc) for r, c in obj}
        avoid = obj | shifted
        marker_pairs = []
        for r in range(h):
            for c in range(w):
                p2 = (r, c)
                p3 = (r + dr, c + dc)
                if (
                    0 <= p3[0] < h
                    and 0 <= p3[1] < w
                    and p2 not in avoid
                    and p3 not in avoid
                ):
                    marker_pairs.append((p2, p3))
        if marker_pairs:
            p2, p3 = rng.choice(marker_pairs)
            return obj, p2, p3
    raise ValueError("could not place object and unobstructed marker pair")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    band_offset = {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    profile_index = (sample_index + band_offset) % len(_CANONICAL_PROFILES)
    profile = _CANONICAL_PROFILES[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_profile_axis(ctx, overrides, "grid_h", profile["grid_h"], 9, 11)
    w = _draw_profile_axis(ctx, overrides, "grid_w", profile["grid_w"], 12, 15)
    size = _draw_profile_axis(
        ctx, overrides, "blue_object_size", profile["blue_object_size"], 4, 6
    )

    dr_over = "marker_dr" in overrides and overrides["marker_dr"] is not None
    dc_over = "marker_dc" in overrides and overrides["marker_dc"] is not None
    dr_default = profile["marker_dr"]
    dc_default = profile["marker_dc"]
    if dr_over:
        dr = ctx.draw_int("marker_dr", -1, 2)
    else:
        # An explicit dc=0 paired with profile dr=0 would be degenerate; choose
        # a lawful deterministic counterpart and record that actual keyed value.
        if dc_over and int(overrides["marker_dc"]) == 0 and dr_default == 0:
            dr_default = 1
        dr = ctx.draw_int("marker_dr", dr_default, dr_default)
    if dc_over:
        dc = ctx.draw_int("marker_dc", -3, 2)
    else:
        if dr_over and int(overrides["marker_dr"]) == 0 and dc_default == 0:
            dc_default = 1
        dc = ctx.draw_int("marker_dc", dc_default, dc_default)
    if (dr, dc) == (0, 0):
        raise ValueError("marker_dr=0 and marker_dc=0 define no displacement")

    shape_rng = ctx.draw_rng("shape_orientation")
    _shape_class, mask = _shape_for_size(size, profile_index, shape_rng)
    layout_rng = ctx.draw_rng("layout")
    obj, p2, p3 = _place_scene(layout_rng, h, w, mask, dr, dc)

    grid = full_grid(h, w, 0)
    for r, c in obj:
        grid[r][c] = 1
    grid[p2[0]][p2[1]] = 2
    grid[p3[0]][p3[1]] = 3
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid marker-vector lesson: " + "; ".join(errors))
    return grid


def _count_components(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if (rr, cc) in remaining:
                    remaining.remove((rr, cc))
                    stack.append((rr, cc))
    return count


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 9 <= h <= 11:
        errors.append(f"grid height {h} outside 9..11")
    if not 12 <= w <= 15:
        errors.append(f"grid width {w} outside 12..15")

    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                continue
            by_color.setdefault(value, []).append((r, c))
    if errors and any("invalid ARC color" in error for error in errors):
        return {"errors": errors}

    foreign = sorted(set(by_color) - {0, 1, 2, 3})
    if foreign:
        errors.append(f"input contains foreign/output colors: {foreign}")
    ones = set(by_color.get(1, []))
    twos = by_color.get(2, [])
    threes = by_color.get(3, [])
    if len(twos) != 1:
        errors.append(f"expected exactly one color-2 marker, got {len(twos)}")
    if len(threes) != 1:
        errors.append(f"expected exactly one color-3 marker, got {len(threes)}")
    if not 4 <= len(ones) <= 6:
        errors.append(f"expected 4..6 blue cells, got {len(ones)}")
    if ones and _count_components(ones) != 1:
        errors.append("blue cells must form exactly one 4-connected object")

    normalized = _normalize(ones)
    shape_class = _SHAPE_CLASS_BY_MASK.get(normalized)
    if ones and shape_class is None:
        errors.append("blue object morphology is outside the canonical D4 shape classes")

    dr = dc = None
    shifted: set[tuple[int, int]] = set()
    if len(twos) == 1 and len(threes) == 1:
        (r2, c2), (r3, c3) = twos[0], threes[0]
        dr, dc = r3 - r2, c3 - c2
        if (dr, dc) == (0, 0):
            errors.append("marker vector must be nonzero")
        if not -1 <= dr <= 2:
            errors.append(f"marker row delta {dr} outside -1..2")
        if not -3 <= dc <= 2:
            errors.append(f"marker column delta {dc} outside -3..2")
        shifted = {(r + dr, c + dc) for r, c in ones}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in shifted):
            errors.append("the entire translated object must remain in bounds")
        if twos[0] in shifted or threes[0] in shifted:
            errors.append("translated copy must not overwrite either marker")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "blue_object_size": len(ones),
        "shape_class": shape_class,
        "marker_dr": dr,
        "marker_dc": dc,
        "object_cells": ones,
        "shifted_cells": shifted,
    }


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "blue_object_size": analysis["blue_object_size"],
        "marker_dr": analysis["marker_dr"],
        "marker_dc": analysis["marker_dc"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    overlap = bool(analysis["object_cells"] & analysis["shifted_cells"])
    linked_key = (
        analysis["grid_h"],
        analysis["grid_w"],
        analysis["blue_object_size"],
        analysis["shape_class"],
        analysis["marker_dr"],
        analysis["marker_dc"],
    )
    return {
        **observe_overrides(grid),
        "shape_class": analysis["shape_class"],
        "copy_overlaps_original": overlap,
        "copy_is_disjoint": not overlap,
        "axis_aligned_vector": (
            analysis["marker_dr"] == 0 or analysis["marker_dc"] == 0
        ),
        "diagonal_vector": (
            analysis["marker_dr"] != 0 and analysis["marker_dc"] != 0
        ),
        "linked_profile_key": linked_key,
        "linked_profile_index": next(
            (
                index
                for index, profile in enumerate(_CANONICAL_PROFILES)
                if linked_key
                == (
                    profile["grid_h"],
                    profile["grid_w"],
                    profile["blue_object_size"],
                    profile["shape_class"],
                    profile["marker_dr"],
                    profile["marker_dc"],
                )
            ),
            None,
        ),
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    key = (
        analysis["grid_h"],
        analysis["grid_w"],
        analysis["blue_object_size"],
        analysis["shape_class"],
        analysis["marker_dr"],
        analysis["marker_dc"],
    )
    if key not in _CANONICAL_LINKED_KEYS:
        return [f"linked profile {key!r} is not one of the five canonical profiles"]
    return []


def _witness(grid, predicate) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


SEMANTIC_WITNESSES = {
    **{
        f"canonical_profile_{index + 1}": (
            lambda grid, index=index: _witness(
                grid, lambda obs: obs["linked_profile_index"] == index
            )
        )
        for index in range(len(_CANONICAL_PROFILES))
    },
    "axis_aligned_vector": lambda grid: _witness(
        grid, lambda obs: obs["axis_aligned_vector"]
    ),
    "diagonal_vector": lambda grid: _witness(
        grid, lambda obs: obs["diagonal_vector"]
    ),
    "copy_overlaps_original": lambda grid: _witness(
        grid, lambda obs: obs["copy_overlaps_original"]
    ),
    "copy_is_disjoint": lambda grid: _witness(
        grid, lambda obs: obs["copy_is_disjoint"]
    ),
    "negative_row_delta": lambda grid: _witness(
        grid, lambda obs: obs["marker_dr"] < 0
    ),
    "positive_row_delta": lambda grid: _witness(
        grid, lambda obs: obs["marker_dr"] > 0
    ),
    "negative_column_delta": lambda grid: _witness(
        grid, lambda obs: obs["marker_dc"] < 0
    ),
    "positive_column_delta": lambda grid: _witness(
        grid, lambda obs: obs["marker_dc"] > 0
    ),
}


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyze(grid)
    out = [row[:] for row in grid]
    dr = analysis["marker_dr"]
    dc = analysis["marker_dc"]
    for r, c in analysis["object_cells"]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = 8
    return out


def _reverse_vector(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = [row[:] for row in grid]
    for r, c in analysis["object_cells"]:
        nr = r - analysis["marker_dr"]
        nc = c - analysis["marker_dc"]
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = 8
    return out


def _move_instead_of_copy(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = [row[:] for row in grid]
    for r, c in analysis["object_cells"]:
        out[r][c] = 0
    for r, c in analysis["shifted_cells"]:
        out[r][c] = 8
    return out


def _copy_bounding_box(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    cells = analysis["object_cells"]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    out = [row[:] for row in grid]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            nr = r + analysis["marker_dr"]
            nc = c + analysis["marker_dc"]
            if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
                out[nr][nc] = 8
    return out


def _recolor_original(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = [row[:] for row in grid]
    for r, c in analysis["object_cells"]:
        out[r][c] = 8
    return out


_COMPETITORS = {
    "reverse the marker vector": _reverse_vector,
    "move rather than copy the object": _move_instead_of_copy,
    "copy the object's bounding box": _copy_bounding_box,
    "recolor the original object in place": _recolor_original,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    if self_check(query_input):
        return ["query input is not a lawful marker-vector scene"]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        if self_check(demo_input):
            reasons.append(f"demo {index} input is not a lawful marker-vector scene")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the marker-vector rule")
    if reasons:
        return reasons

    for name, competitor in _COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            query_alt = competitor(query_input)
            if query_alt != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor '{name}', "
                    "which changes the query answer"
                )
    return reasons
