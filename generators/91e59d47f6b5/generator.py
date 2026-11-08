"""Generator for 91e59d47f6b5 — translate the red object by a marker vector.

A blue singleton (1) and a green singleton (3) define a displacement.  The
connected red object (2) is erased from its source cells and painted cyan (8)
after that displacement.  One connected, non-answer-bearing distractor in
color 4..7 is preserved.  The default schedule mixes all five canonical linked
profiles with three lawful recombinations that disprove a dimensions-only
lookup rule while retaining the canonical palette, scale, and morphologies.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "91e59d47f6b5"
TASK_ID = "91e59d47f6b5"
VERSION = "2.0.0"
RULE_HASH = "9ae485786735"

SUMMARY = (
    "A sparse 8..10 by 10..12 grid contains a connected red (2) object, a "
    "blue (1) marker, a green (3) marker, and one preserved distractor. Move "
    "the red object by the blue-to-green vector: erase its source cells to "
    "background 0 and paint its translated cells cyan 8."
)

INVARIANTS = [
    "the input palette is exactly 0, 1, 2, 3, and one distractor color in 4..7",
    "blue and green are singleton markers defining a nonzero in-range vector",
    "red is one 4-connected corner-triomino or stair-tetromino",
    "the translated red object remains in bounds and avoids markers and distractor",
    "the connected distractor has one or two cells and is not transformed",
]

AXES = {
    "grid_h": {"type": "int", "default": "linked schedule", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "linked schedule", "valid": "10..12"},
    "shape_class": {
        "type": "str",
        "default": "linked schedule",
        "valid": "corner3|stair4",
    },
    "marker_dr": {
        "type": "int",
        "default": "linked schedule",
        "valid": "-2..4",
    },
    "marker_dc": {
        "type": "int",
        "default": "linked schedule",
        "valid": "-2..3",
    },
    "distractor_color": {
        "type": "color",
        "default": "linked schedule",
        "valid": "4..7",
    },
    "distractor_size": {
        "type": "int",
        "default": "linked schedule",
        "valid": "1..2",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"marker_dr": 0, "marker_dc": 0},
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.55

_CORNER3 = ((0, 0), (1, 0), (1, 1))
_STAIR4 = ((0, 0), (1, 0), (1, 1), (2, 1))


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
    variants: set[tuple[tuple[int, int], ...]] = set()
    current = _normalize(mask)
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


_SHAPE_ORBITS = {
    "corner3": _d4_orbit(_CORNER3),
    "stair4": _d4_orbit(_STAIR4),
}
_SHAPE_CLASS_BY_MASK = {
    mask: shape_class
    for shape_class, orbit in _SHAPE_ORBITS.items()
    for mask in orbit
}

# Five exact canonical profiles plus three lawful counterprofiles.  The cycle is
# arranged so every run of three demonstrations includes a counterprofile.
_SCHEDULE = (
    {"name": "canonical_1", "grid_h": 8, "grid_w": 10, "shape_class": "corner3",
     "marker_dr": 2, "marker_dc": 1, "distractor_color": 7, "distractor_size": 1,
     "canonical_index": 0},
    {"name": "canonical_2", "grid_h": 9, "grid_w": 11, "shape_class": "corner3",
     "marker_dr": 1, "marker_dc": 3, "distractor_color": 4, "distractor_size": 1,
     "canonical_index": 1},
    {"name": "counter_8x10", "grid_h": 8, "grid_w": 10, "shape_class": "corner3",
     "marker_dr": -2, "marker_dc": 2, "distractor_color": 4, "distractor_size": 2,
     "canonical_index": None},
    {"name": "canonical_3", "grid_h": 10, "grid_w": 10, "shape_class": "stair4",
     "marker_dr": -2, "marker_dc": 2, "distractor_color": 6, "distractor_size": 1,
     "canonical_index": 2},
    {"name": "canonical_4", "grid_h": 9, "grid_w": 12, "shape_class": "corner3",
     "marker_dr": -2, "marker_dc": -1, "distractor_color": 5, "distractor_size": 1,
     "canonical_index": 3},
    {"name": "counter_10x10", "grid_h": 10, "grid_w": 10, "shape_class": "stair4",
     "marker_dr": 1, "marker_dc": 3, "distractor_color": 5, "distractor_size": 2,
     "canonical_index": None},
    {"name": "canonical_5", "grid_h": 10, "grid_w": 12, "shape_class": "stair4",
     "marker_dr": 4, "marker_dc": -2, "distractor_color": 7, "distractor_size": 2,
     "canonical_index": 4},
    {"name": "counter_9x12", "grid_h": 9, "grid_w": 12, "shape_class": "stair4",
     "marker_dr": 2, "marker_dc": 1, "distractor_color": 6, "distractor_size": 2,
     "canonical_index": None},
)

SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))
_BAND_OFFSETS = {None: 1, "easy": 0, "medium": 3, "hard": 5}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    if difficulty not in _BAND_OFFSETS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return (int(sample_index) + _BAND_OFFSETS[difficulty]) % len(_SCHEDULE)


_CANONICAL_LINKED_KEYS = {
    (
        profile["grid_h"],
        profile["grid_w"],
        profile["shape_class"],
        profile["marker_dr"],
        profile["marker_dc"],
        profile["distractor_color"],
        profile["distractor_size"],
    )
    for profile in _SCHEDULE
    if profile["canonical_index"] is not None
}

# All canonical dimensions are unique, so this wrong lookup reproduces every
# official output.  The three counterprofiles reuse those dimensions with a
# different marker vector and therefore provide generated falsifiers.
_DIMENSION_VECTOR = {
    (8, 10): (2, 1),
    (9, 11): (1, 3),
    (10, 10): (-2, 2),
    (9, 12): (-2, -1),
    (10, 12): (4, -2),
}


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _distractor_candidates(
    free: set[tuple[int, int]], size: int
) -> list[tuple[tuple[int, int], ...]]:
    if size == 1:
        return [((r, c),) for r, c in sorted(free)]
    candidates: set[tuple[tuple[int, int], ...]] = set()
    for r, c in free:
        for rr, cc in ((r + 1, c), (r, c + 1)):
            if (rr, cc) in free:
                candidates.add(tuple(sorted(((r, c), (rr, cc)))))
    return sorted(candidates)


def _place_scene(rng, h: int, w: int, shape_class: str, dr: int, dc: int, distractor_size: int):
    orientations = list(_SHAPE_ORBITS[shape_class])
    rng.shuffle(orientations)
    all_cells = {(r, c) for r in range(h) for c in range(w)}

    for mask in orientations:
        max_r = max(r for r, _ in mask)
        max_c = max(c for _, c in mask)
        rlo = max(0, -dr)
        rhi = min(h - 1 - max_r, h - 1 - max_r - dr)
        clo = max(0, -dc)
        chi = min(w - 1 - max_c, w - 1 - max_c - dc)
        if rlo > rhi or clo > chi:
            continue
        anchors = [(r, c) for r in range(rlo, rhi + 1) for c in range(clo, chi + 1)]
        rng.shuffle(anchors)
        for ar, ac in anchors:
            obj = {(ar + r, ac + c) for r, c in mask}
            shifted = {(r + dr, c + dc) for r, c in obj}
            occupied = obj | shifted
            marker_pairs = [
                ((r, c), (r + dr, c + dc))
                for r in range(h)
                for c in range(w)
                if 0 <= r + dr < h
                and 0 <= c + dc < w
                and (r, c) not in occupied
                and (r + dr, c + dc) not in occupied
            ]
            rng.shuffle(marker_pairs)
            for blue, green in marker_pairs:
                free = all_cells - occupied - {blue, green}
                distractors = _distractor_candidates(free, distractor_size)
                if distractors:
                    distractor = rng.choice(distractors)
                    return obj, shifted, blue, green, set(distractor)
    raise ValueError(
        "could not place shape_class, marker vector, and distractor together: "
        f"shape_class={shape_class!r}, marker_dr={dr}, marker_dc={dc}, "
        f"grid_h={h}, grid_w={w}, distractor_size={distractor_size}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_OFFSETS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    profile_index = schedule_profile(seed, sample_index, difficulty)
    profile = _SCHEDULE[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_int_axis(ctx, overrides, "grid_h", profile["grid_h"], 8, 10)
    w = _draw_int_axis(ctx, overrides, "grid_w", profile["grid_w"], 10, 12)
    shape_class = _draw_choice_axis(
        ctx, overrides, "shape_class", profile["shape_class"], ("corner3", "stair4")
    )
    dr = _draw_int_axis(ctx, overrides, "marker_dr", profile["marker_dr"], -2, 4)
    dc = _draw_int_axis(ctx, overrides, "marker_dc", profile["marker_dc"], -2, 3)
    distractor_color = _draw_int_axis(
        ctx, overrides, "distractor_color", profile["distractor_color"], 4, 7
    )
    distractor_size = _draw_int_axis(
        ctx, overrides, "distractor_size", profile["distractor_size"], 1, 2
    )
    if (dr, dc) == (0, 0):
        raise ValueError(
            "marker_dr=0 and marker_dc=0 are incompatible: the marker vector must be nonzero"
        )

    obj, _shifted, blue, green, distractor = _place_scene(
        ctx.draw_rng("layout"), h, w, shape_class, dr, dc, distractor_size
    )
    grid = full_grid(h, w, 0)
    for r, c in obj:
        grid[r][c] = 2
    grid[blue[0]][blue[1]] = 1
    grid[green[0]][green[1]] = 3
    for r, c in distractor:
        grid[r][c] = distractor_color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid marker-vector scene: " + "; ".join(errors))
    return grid


def _count_components(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 8 <= h <= 10:
        errors.append(f"grid height {h} outside 8..10")
    if not 10 <= w <= 12:
        errors.append(f"grid width {w} outside 10..12")

    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                continue
            by_color.setdefault(value, []).append((r, c))
    if any("invalid ARC color" in error for error in errors):
        return {"errors": errors}

    present = set(by_color)
    foreign = sorted(present - set(range(8)))
    if foreign:
        errors.append(f"input contains output/foreign colors: {foreign}")
    if 0 not in present:
        errors.append("background color 0 must be present")

    blue = by_color.get(1, [])
    red = set(by_color.get(2, []))
    green = by_color.get(3, [])
    distractor_colors = sorted(color for color in range(4, 8) if by_color.get(color))
    if len(blue) != 1:
        errors.append(f"expected exactly one blue marker, got {len(blue)}")
    if len(green) != 1:
        errors.append(f"expected exactly one green marker, got {len(green)}")
    if len(distractor_colors) != 1:
        errors.append(
            "expected exactly one distractor color from 4..7, got "
            f"{distractor_colors}"
        )

    if len(red) not in (3, 4):
        errors.append(f"expected 3 or 4 red object cells, got {len(red)}")
    if red and _count_components(red) != 1:
        errors.append("red cells must form exactly one 4-connected object")
    normalized = _normalize(red)
    shape_class = _SHAPE_CLASS_BY_MASK.get(normalized)
    if red and shape_class is None:
        errors.append("red object morphology is not a corner3 or stair4 D4 variant")

    distractor_color = distractor_colors[0] if len(distractor_colors) == 1 else None
    distractor = set(by_color.get(distractor_color, [])) if distractor_color is not None else set()
    if distractor and len(distractor) not in (1, 2):
        errors.append(f"expected distractor size 1 or 2, got {len(distractor)}")
    if distractor and _count_components(distractor) != 1:
        errors.append("distractor cells must form one 4-connected object")

    dr = dc = None
    shifted: set[tuple[int, int]] = set()
    if len(blue) == 1 and len(green) == 1:
        dr = green[0][0] - blue[0][0]
        dc = green[0][1] - blue[0][1]
        if (dr, dc) == (0, 0):
            errors.append("marker vector must be nonzero")
        if not -2 <= dr <= 4:
            errors.append(f"marker row delta {dr} outside -2..4")
        if not -2 <= dc <= 3:
            errors.append(f"marker column delta {dc} outside -2..3")
        shifted = {(r + dr, c + dc) for r, c in red}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in shifted):
            errors.append("the translated red object must remain in bounds")
        if blue[0] in shifted or green[0] in shifted:
            errors.append("the translated red object must not overwrite either marker")
        if shifted & distractor:
            errors.append("the translated red object must not overwrite the distractor")

    if len(present) != 5 or not {0, 1, 2, 3}.issubset(present):
        errors.append(
            "input palette must contain exactly 0,1,2,3 and one distractor color"
        )

    linked_key = (
        h,
        w,
        shape_class,
        dr,
        dc,
        distractor_color,
        len(distractor),
    )
    canonical_index = next(
        (
            profile["canonical_index"]
            for profile in _SCHEDULE
            if profile["canonical_index"] is not None
            and linked_key
            == (
                profile["grid_h"],
                profile["grid_w"],
                profile["shape_class"],
                profile["marker_dr"],
                profile["marker_dc"],
                profile["distractor_color"],
                profile["distractor_size"],
            )
        ),
        None,
    )
    expected_delta = _DIMENSION_VECTOR.get((h, w))
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "shape_class": shape_class,
        "marker_dr": dr,
        "marker_dc": dc,
        "distractor_color": distractor_color,
        "distractor_size": len(distractor),
        "red_cells": red,
        "shifted_cells": shifted,
        "blue_cell": blue[0] if len(blue) == 1 else None,
        "green_cell": green[0] if len(green) == 1 else None,
        "distractor_cells": distractor,
        "linked_key": linked_key,
        "canonical_index": canonical_index,
        "dimension_expected_delta": expected_delta,
        "dimension_shortcut_refuted": expected_delta is not None and expected_delta != (dr, dc),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {axis: analysis[axis] for axis in AXES}


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "linked_profile_key": analysis["linked_key"],
        "canonical_profile_index": analysis["canonical_index"],
        "strict_canonical_profile": analysis["linked_key"] in _CANONICAL_LINKED_KEYS,
        "dimension_expected_delta": analysis["dimension_expected_delta"],
        "dimension_shortcut_refuted": analysis["dimension_shortcut_refuted"],
        "positive_row_delta": analysis["marker_dr"] > 0,
        "negative_row_delta": analysis["marker_dr"] < 0,
        "positive_column_delta": analysis["marker_dc"] > 0,
        "negative_column_delta": analysis["marker_dc"] < 0,
        "source_destination_overlap": bool(analysis["red_cells"] & analysis["shifted_cells"]),
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    if analysis["linked_key"] not in _CANONICAL_LINKED_KEYS:
        return [f"linked profile {analysis['linked_key']!r} is not one of the five canonical profiles"]
    return []


def _witness(grid, predicate: Callable[[dict[str, object]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


SEMANTIC_WITNESSES = {
    **{
        f"canonical_profile_{index + 1}": (
            lambda grid, index=index: _witness(
                grid, lambda obs: obs["canonical_profile_index"] == index
            )
        )
        for index in range(5)
    },
    "counterprofile_refutes_dimension_lookup": lambda grid: _witness(
        grid, lambda obs: obs["dimension_shortcut_refuted"]
    ),
    "corner_triomino": lambda grid: _witness(
        grid, lambda obs: obs["shape_class"] == "corner3"
    ),
    "stair_tetromino": lambda grid: _witness(
        grid, lambda obs: obs["shape_class"] == "stair4"
    ),
    "singleton_distractor": lambda grid: _witness(
        grid, lambda obs: obs["distractor_size"] == 1
    ),
    "domino_distractor": lambda grid: _witness(
        grid, lambda obs: obs["distractor_size"] == 2
    ),
    "positive_row_delta": lambda grid: _witness(
        grid, lambda obs: obs["positive_row_delta"]
    ),
    "negative_row_delta": lambda grid: _witness(
        grid, lambda obs: obs["negative_row_delta"]
    ),
    "positive_column_delta": lambda grid: _witness(
        grid, lambda obs: obs["positive_column_delta"]
    ),
    "negative_column_delta": lambda grid: _witness(
        grid, lambda obs: obs["negative_column_delta"]
    ),
    "marker_order_controls_direction": lambda grid: _witness(grid, lambda obs: True),
    "move_requires_source_erasure": lambda grid: _witness(grid, lambda obs: True),
    "nonrectangular_object_refutes_bbox": lambda grid: _witness(grid, lambda obs: True),
    "move_is_not_recolor_in_place": lambda grid: _witness(grid, lambda obs: True),
}


def _paint_translation(grid, dr: int, dc: int):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = [row[:] for row in grid]
    for r, c in analysis["red_cells"]:
        out[r][c] = 0
    for r, c in analysis["red_cells"]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = 8
    return out


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _paint_translation(grid, analysis["marker_dr"], analysis["marker_dc"])


def _reverse_marker_vector(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return _paint_translation(grid, -analysis["marker_dr"], -analysis["marker_dc"])


def _copy_instead_of_move(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = [row[:] for row in grid]
    for r, c in analysis["shifted_cells"]:
        out[r][c] = 8
    return out


def _move_bounding_box(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    cells = analysis["red_cells"]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    out = [row[:] for row in grid]
    for r, c in cells:
        out[r][c] = 0
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            nr = r + analysis["marker_dr"]
            nc = c + analysis["marker_dc"]
            if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
                out[nr][nc] = 8
    return out


def _recolor_source_in_place(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = [row[:] for row in grid]
    for r, c in analysis["red_cells"]:
        out[r][c] = 8
    return out


def _dimension_lookup_vector(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    delta = _DIMENSION_VECTOR.get((analysis["grid_h"], analysis["grid_w"]))
    if delta is None:
        return [row[:] for row in grid]
    return _paint_translation(grid, delta[0], delta[1])


SEMANTIC_RIVALS = {
    "reverse_marker_vector": _reverse_marker_vector,
    "copy_instead_of_move": _copy_instead_of_move,
    "move_bounding_box": _move_bounding_box,
    "recolor_source_in_place": _recolor_source_in_place,
    "dimension_lookup_vector": _dimension_lookup_vector,
}

WITNESS_RIVALS = {
    "counterprofile_refutes_dimension_lookup": ["dimension_lookup_vector"],
    "marker_order_controls_direction": ["reverse_marker_vector"],
    "move_requires_source_erasure": ["copy_instead_of_move"],
    "nonrectangular_object_refutes_bbox": ["move_bounding_box"],
    "move_is_not_recolor_in_place": ["recolor_source_in_place"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"dimension_lookup_vector": _dimension_lookup_vector}


def _fixed_vector_solver(dr: int, dc: int):
    return lambda grid: _paint_translation(grid, dr, dc)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["lesson must contain at least one demonstration"]
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

    competitors = dict(LESSON_COMPETITORS)
    first = _analyze(demos[0]["input"])
    competitors["fixed_vector_from_first_demo"] = _fixed_vector_solver(
        first["marker_dr"], first["marker_dc"]
    )
    for name, competitor in competitors.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            alternate = competitor(query_input)
            if alternate != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
    return reasons
