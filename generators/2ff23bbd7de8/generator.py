"""Generator for ``quadrant_count_strip`` (task 2ff23bbd7de8).

Canonical rule
==============
A three-cell L-frame defines an oriented local coordinate system:

* colour 2 is the origin;
* colour 3 is one cardinal step along local ``+u``;
* colour 4 is one perpendicular cardinal step along local ``+v``.

Only colour-8 cells with ``max(abs(u), abs(v)) <= 3`` and with both coordinates
non-zero are counted.  The output is a 1x4 strip containing the counts in local
quadrants ``(++), (-+), (--), (+-)``.  Axis cells are not in any quadrant, and
the selected canonical Racket source clamps its nominal radius argument to 3.

The four-position sample schedule deliberately alternates canonical-style
scenes, axis-boundary distractors, radius-four distractors, and scenes carrying
both.  Thus every materialized four-demo lesson contains counterexamples to
three plausible shortcuts: counting axis cells, ignoring the radius clamp, and
using fixed global rather than frame-local axes.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2ff23bbd7de8"
TASK_ID = GENERATOR_ID
VERSION = "4.0.2"
RULE_HASH = "2bd7a3052519"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A colour-2/3/4 L-frame defines oriented local axes. Count only colour-8 "
    "cells strictly inside the four local quadrants and within Chebyshev "
    "radius 3; output (++,-+,--,+-) as a 1x4 count strip."
)

INVARIANTS = [
    "the grid is square, uses only colours 0/2/3/4/8, and has exactly one cell of each frame colour",
    "colour 3 and colour 4 are orthogonal cardinal neighbours of the colour-2 origin",
    "every colour-8 cell lies within local Chebyshev radius 4",
    "at least one colour-8 cell is off-axis within radius 3 and therefore contributes to the output",
    "axis cells and radius-four cells are lawful distractors but are not counted",
]

# Only a control that is exactly recoverable from the returned grid is exposed.
# Frame orientation, count distribution, and distractor schedule still vary, but
# they are curriculum internals rather than override promises.
AXES = {
    "grid_n": {
        "type": "int",
        "default": "canonical-anchored, difficulty-skewed 11..17",
        "valid": "11..17",
    },
}

# Ordered orthonormal cardinal bases (u, v).  All eight rotations/reflections
# are represented; local coordinates are dot products against these vectors.
_BASES = (
    ((1, 0), (0, 1)),
    ((1, 0), (0, -1)),
    ((-1, 0), (0, 1)),
    ((-1, 0), (0, -1)),
    ((0, 1), (1, 0)),
    ((0, 1), (-1, 0)),
    ((0, -1), (1, 0)),
    ((0, -1), (-1, 0)),
)
_BASE_TO_INDEX = {basis: index for index, basis in enumerate(_BASES)}
_QUADRANT_SIGNS = ((1, 1), (-1, 1), (-1, -1), (1, -1))
_SCHEDULE_PROFILES = ("canonical_style", "axis_boundary", "radius_four", "both_distractors")
SCHEDULE_PROFILES = _SCHEDULE_PROFILES


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Four consecutive sample indexes cover every decisive scene profile."""
    del seed, difficulty
    return _SCHEDULE_PROFILES[int(sample_index) % len(_SCHEDULE_PROFILES)]


def _place(
    grid: list[list[int]],
    origin: tuple[int, int],
    vx: tuple[int, int],
    vy: tuple[int, int],
    u: int,
    v: int,
    color: int,
) -> None:
    r = origin[0] + u * vx[0] + v * vy[0]
    c = origin[1] + u * vx[1] + v * vy[1]
    if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
        raise ValueError(f"local coordinate {(u, v)} leaves the grid")
    if grid[r][c] != 0:
        raise ValueError(f"local coordinate {(u, v)} collides with colour {grid[r][c]}")
    grid[r][c] = color


def _local(
    origin: tuple[int, int],
    vx: tuple[int, int],
    vy: tuple[int, int],
    point: tuple[int, int],
) -> tuple[int, int]:
    dr, dc = point[0] - origin[0], point[1] - origin[1]
    return (
        dr * vx[0] + dc * vx[1],
        dr * vy[0] + dc * vy[1],
    )


def _quadrant(u: int, v: int) -> int | None:
    if u > 0 and v > 0:
        return 0
    if u < 0 and v > 0:
        return 1
    if u < 0 and v < 0:
        return 2
    if u > 0 and v < 0:
        return 3
    return None


def _find_frame(grid: list[list[int]]) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    cells: dict[int, list[tuple[int, int]]] = {2: [], 3: [], 4: []}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in cells:
                cells[value].append((r, c))
    if any(len(cells[color]) != 1 for color in (2, 3, 4)):
        raise ValueError("expected exactly one cell of each frame colour 2, 3, and 4")
    origin = cells[2][0]
    p3, p4 = cells[3][0], cells[4][0]
    vx = (p3[0] - origin[0], p3[1] - origin[1])
    vy = (p4[0] - origin[0], p4[1] - origin[1])
    if vx not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        raise ValueError("colour 3 is not one cardinal step from the origin")
    if vy not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        raise ValueError("colour 4 is not one cardinal step from the origin")
    if vx[0] * vy[0] + vx[1] * vy[1] != 0:
        raise ValueError("frame arms are not perpendicular")
    return origin, vx, vy


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {}, ["empty or non-list grid"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return {}, ["ragged grid"]
    h, w = len(grid), len(grid[0])
    if h != w:
        errors.append(f"grid must be square, got {h}x{w}")
    if not (11 <= h <= 17 and 11 <= w <= 17):
        errors.append(f"grid dimensions {h}x{w} are outside 11..17")

    allowed = {0, 2, 3, 4, 8}
    illegal = sorted({value for row in grid for value in row if value not in allowed})
    if illegal:
        errors.append(f"illegal colours present: {illegal}")

    try:
        origin, vx, vy = _find_frame(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return {}, errors

    orientation = _BASE_TO_INDEX.get((vx, vy))
    if orientation is None:
        errors.append(f"unsupported frame basis vx={vx}, vy={vy}")
        return {}, errors

    qcounts = [0, 0, 0, 0]
    axis_points: list[tuple[int, int]] = []
    far_points: list[tuple[int, int]] = []
    signal_points: list[tuple[int, int]] = []
    all_eights: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            all_eights.append((r, c))
            u, v = _local(origin, vx, vy, (r, c))
            radius = max(abs(u), abs(v))
            if radius > 4:
                errors.append(f"colour-8 cell {(r, c)} lies outside local radius 4 at {(u, v)}")
                continue
            q = _quadrant(u, v)
            if radius <= 3 and q is not None:
                qcounts[q] += 1
                signal_points.append((r, c))
            elif radius <= 3:
                axis_points.append((r, c))
            else:
                far_points.append((r, c))

    if not signal_points:
        errors.append("no off-axis colour-8 point within radius 3 is countable")
    if not all_eights:
        errors.append("no colour-8 cells found")

    return {
        "grid_n": h,
        "origin": origin,
        "vx": vx,
        "vy": vy,
        "orientation": orientation,
        "qcounts": tuple(qcounts),
        "signal_count": len(signal_points),
        "axis_count": len(axis_points),
        "far_count": len(far_points),
        "all_eight_count": len(all_eights),
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {"grid_n": info["grid_n"]}


def _allocate_quadrants(total: int, profile: str, rng) -> list[int]:
    """Create a capacity-safe count tuple with profile-specific semantics."""
    counts = [0, 0, 0, 0]
    if profile == "canonical_style":
        counts = [1, 1, 1, 1]
        fixed_one = rng.randrange(4)
        targets = [q for q in range(4) if q != fixed_one]
    elif profile == "axis_boundary":
        empty = rng.randrange(4)
        nonempty = [q for q in range(4) if q != empty]
        for q in nonempty:
            counts[q] = 1
        fixed_one = rng.choice(nonempty)
        targets = [q for q in nonempty if q != fixed_one]
    elif profile == "radius_four":
        dominant = rng.randrange(4)
        fixed_one = rng.choice([q for q in range(4) if q != dominant])
        counts[dominant] = min(9, max(2, total // 2))
        counts[fixed_one] = 1
        targets = [q for q in range(4) if q != fixed_one]
    else:
        first = rng.randrange(4)
        second = (first + 2) % 4
        fixed_one = first
        counts[first] = 1
        counts[second] = 1
        targets = [q for q in range(4) if q != fixed_one]

    remaining = total - sum(counts)
    while remaining > 0:
        choices = [q for q in targets if counts[q] < 9]
        if not choices:
            raise ValueError(f"cannot allocate {total} points under profile {profile}")
        q = rng.choice(choices)
        counts[q] += 1
        remaining -= 1
    return counts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Keep an explicit canonical-scale anchor in every difficulty band while
    # retaining larger-grid variation.  Repeated 11s are intentional weights;
    # exact overrides still accept every integer in 11..17 below.
    if "grid_n" in overrides and overrides["grid_n"] is not None:
        n = ctx.draw_int("grid_n", 11, 17)
    else:
        grid_options = {
            "easy": (11, 11, 11, 12, 13),
            "medium": (11, 11, 13, 14, 15),
            "hard": (11, 11, 15, 16, 17),
        }.get(difficulty, (11, 11, 12, 13, 14, 15, 16, 17))
        n = ctx.draw_choice("grid_n", grid_options)
    rng = ctx.draw_rng("layout")
    profile = schedule_profile(seed, sample_index, difficulty)

    if difficulty == "easy":
        total = rng.randint(4, 7)
    elif difficulty == "hard":
        total = rng.randint(10, 16)
    else:
        total = rng.randint(6, 11)

    qcounts = _allocate_quadrants(total, profile, rng)
    orientation = int(sample_index) % len(_BASES)
    vx, vy = _BASES[orientation]
    origin = (rng.randint(4, n - 5), rng.randint(4, n - 5))

    grid = full_grid(n, n, 0)
    grid[origin[0]][origin[1]] = 2
    _place(grid, origin, vx, vy, 1, 0, 3)
    _place(grid, origin, vx, vy, 0, 1, 4)

    for q, count in enumerate(qcounts):
        su, sv = _QUADRANT_SIGNS[q]
        candidates = [(su * au, sv * av) for au in range(1, 4) for av in range(1, 4)]
        rng.shuffle(candidates)
        for u, v in candidates[:count]:
            _place(grid, origin, vx, vy, u, v, 8)

    if profile in {"axis_boundary", "both_distractors"}:
        axis_candidates = [
            (u, 0) for u in range(-3, 4)
            if u != 0 and (u, 0) != (1, 0)
        ] + [
            (0, v) for v in range(-3, 4)
            if v != 0 and (0, v) != (0, 1)
        ]
        rng.shuffle(axis_candidates)
        axis_count = 2 if profile == "axis_boundary" else 3
        for u, v in axis_candidates[:axis_count]:
            _place(grid, origin, vx, vy, u, v, 8)

    if profile in {"radius_four", "both_distractors"}:
        far_candidates = [
            (u, v)
            for u in range(-4, 5)
            for v in range(-4, 5)
            if max(abs(u), abs(v)) == 4 and u != 0 and v != 0
        ]
        rng.shuffle(far_candidates)
        far_count = 2 if profile == "radius_four" else 3
        for u, v in far_candidates[:far_count]:
            _place(grid, origin, vx, vy, u, v, 8)

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid grid: " + "; ".join(errors))
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python transcription of the selected canonical Racket rule."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [list(info["qcounts"])]


def _rival_ignore_radius(grid: list[list[int]]) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = [0, 0, 0, 0]
    origin, vx, vy = info["origin"], info["vx"], info["vy"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 8:
                q = _quadrant(*_local(origin, vx, vy, (r, c)))
                if q is not None:
                    counts[q] += 1
    return [counts]


def _rival_include_axes(grid: list[list[int]]) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = [0, 0, 0, 0]
    origin, vx, vy = info["origin"], info["vx"], info["vy"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            u, v = _local(origin, vx, vy, (r, c))
            if max(abs(u), abs(v)) > 3:
                continue
            if u >= 0 and v >= 0:
                counts[0] += 1
            elif u < 0 and v >= 0:
                counts[1] += 1
            elif u < 0 and v < 0:
                counts[2] += 1
            else:
                counts[3] += 1
    return [counts]


def _rival_global_axes(grid: list[list[int]]) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = [0, 0, 0, 0]
    orow, ocol = info["origin"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            u, v = r - orow, c - ocol
            if max(abs(u), abs(v)) <= 3:
                q = _quadrant(u, v)
                if q is not None:
                    counts[q] += 1
    return [counts]


def _rival_total_only(grid: list[list[int]]) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [[info["all_eight_count"], 0, 0, 0]]


SEMANTIC_RIVALS = {
    "ignore_radius_three_clamp": _rival_ignore_radius,
    "include_axis_boundary_cells": _rival_include_axes,
    "fixed_global_quadrants": _rival_global_axes,
    "total_marker_count_only": _rival_total_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_radius_three_clamp": _rival_ignore_radius,
    "include_axis_boundary_cells": _rival_include_axes,
}


def _refutes(name: str, grid: list[list[int]]) -> bool:
    return rule_mirror(grid) != SEMANTIC_RIVALS[name](grid)


SEMANTIC_WITNESSES = {
    "axis_boundary_counterexample": lambda grid: _refutes("include_axis_boundary_cells", grid),
    "radius_clamp_counterexample": lambda grid: _refutes("ignore_radius_three_clamp", grid),
    "local_frame_counterexample": lambda grid: _refutes("fixed_global_quadrants", grid),
    "quadrant_structure_counterexample": lambda grid: _refutes("total_marker_count_only", grid),
}
WITNESS_RIVALS = {
    "axis_boundary_counterexample": ["include_axis_boundary_cells"],
    "radius_clamp_counterexample": ["ignore_radius_three_clamp"],
    "local_frame_counterexample": ["fixed_global_quadrants"],
    "quadrant_structure_counterexample": ["total_marker_count_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Verify that a materialized four-demo lesson rules out named shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    lawful_inputs: list[list[list[int]]] = []
    profiles: set[str] = set()
    outputs: set[tuple[int, ...]] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the canonical rule")
            continue
        lawful_inputs.append(pair["input"])
        outputs.add(tuple(expected[0]))
        if info["axis_count"] and info["far_count"]:
            profiles.add("both_distractors")
        elif info["axis_count"]:
            profiles.add("axis_boundary")
        elif info["far_count"]:
            profiles.add("radius_four")
        else:
            profiles.add("canonical_style")

    missing_profiles = sorted(set(_SCHEDULE_PROFILES) - profiles)
    if missing_profiles:
        reasons.append(f"demonstrations omit scheduled profiles: {missing_profiles}")
    if len(outputs) < 3:
        reasons.append(f"demonstrations expose only {len(outputs)} distinct quadrant tuples")

    for name, competitor in LESSON_COMPETITORS.items():
        if lawful_inputs and all(competitor(grid) == rule_mirror(grid) for grid in lawful_inputs):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        qerrors = self_check(query["input"])
        if qerrors:
            reasons.append(f"query input is unlawful: {qerrors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the canonical rule")
    return reasons
