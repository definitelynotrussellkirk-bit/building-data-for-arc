"""Generator for "Expand Singletons to Plus Shapes" (bfa4f83b9dbd).

Canonical rule: every isolated interior nonzero cell is preserved and its four
cardinal neighbours are painted with the same color, producing a radius-1 plus.

The teaching grammar deliberately uses 2-3 differently colored singleton
markers.  Their radius-1 plus footprints are disjoint, so every marker has an
unambiguous local answer and no marker can hide another marker's arm.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bfa4f83b9dbd"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "45804b5cdffe"

SUMMARY = (
    "On a zero background, expand every isolated interior colored singleton "
    "into a five-cell plus by painting its four cardinal neighbours with the "
    "same color. Every generated lesson contains 2-3 differently colored "
    "markers with disjoint plus footprints."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "there are 2 or 3 nonzero singleton markers",
    "every marker is strictly interior and has four zero cardinal neighbours",
    "the radius-1 plus footprints of distinct markers are disjoint",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Every declared axis is exact and recoverable from the returned grid.  The
# ranges are the canonical dimension/count envelope, so every difficulty band
# remains anchored to the public task while draw_int_diff still changes the
# within-envelope distribution by difficulty.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 7..9", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "difficulty-aware 8..11", "valid": "8..11"},
    "n_markers": {"type": "int", "default": "difficulty-aware 2..3", "valid": "2..3"},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PLUS = ((0, 0), *_DIRS4)

# Linked public profile prior.  Normal draws stay exactly on one of the five
# canonical (height, width, marker-count) profiles; explicit overrides may
# independently explore every declared boundary combination.
_CANONICAL_PROFILES = (
    (7, 9, 2),
    (8, 8, 2),
    (9, 10, 3),
    (7, 11, 2),
    (8, 10, 3),
)


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _validate_matrix(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad:
        r, c, value = bad[0]
        return [f"cell ({r},{c})={value!r} is not an ARC color 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_matrix(grid)
    if errors:
        return {"errors": errors}

    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])
    markers = sorted(
        (r, c, g[r][c])
        for r in range(h)
        for c in range(w)
        if g[r][c] != 0
    )

    if not (7 <= h <= 9 and 8 <= w <= 11):
        errors.append(f"dims {h}x{w} outside canonical envelope 7..9 x 8..11")
    if not 2 <= len(markers) <= 3:
        errors.append(f"expected 2 or 3 singleton markers, found {len(markers)}")

    footprints: list[set[tuple[int, int]]] = []
    for r, c, color in markers:
        if r in (0, h - 1) or c in (0, w - 1):
            errors.append(f"marker {color} at ({r},{c}) touches the outer border")
            continue
        occupied_neighbours = [
            (r + dr, c + dc)
            for dr, dc in _DIRS4
            if g[r + dr][c + dc] != 0
        ]
        if occupied_neighbours:
            errors.append(
                f"marker {color} at ({r},{c}) is not isolated; "
                f"occupied cardinal neighbours={occupied_neighbours}"
            )
        footprint = {(r + dr, c + dc) for dr, dc in _PLUS}
        footprints.append(footprint)

    for i, first in enumerate(footprints):
        for j, second in enumerate(footprints[i + 1 :], i + 1):
            overlap = sorted(first & second)
            if overlap:
                errors.append(
                    f"markers {i} and {j} have overlapping plus footprints at {overlap}"
                )

    return {
        "errors": errors,
        "grid": g,
        "h": h,
        "w": w,
        "markers": markers,
        "colors": [color for _r, _c, color in markers],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the structural teaching grammar and exact requested axes."""
    if difficulty not in _VALID_DIFFICULTIES:
        return ["difficulty must be one of None, 'easy', 'medium', or 'hard'"]
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors or not isinstance(meta, dict):
        return errors

    requested = meta.get("overrides")
    if not isinstance(requested, dict):
        requested = meta
    try:
        observed = observe_overrides(grid)
    except ValueError:
        return errors
    for key in AXES:
        if requested.get(key) is not None and observed[key] != requested[key]:
            errors.append(
                f"override {key} requested {requested[key]!r}, observed {observed[key]!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the canonical input manifold plus color-separated markers."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    colors = analysis["colors"]
    if len(set(colors)) != len(colors):
        reasons.append("canonical teaching scenes use a distinct color per marker")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a returned valid grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "n_markers": len(analysis["markers"]),
    }


def semantic_observables(grid) -> dict[str, Any]:
    """Task-linked observables for count-backed semantic review."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    markers = analysis["markers"]
    return {
        **observe_overrides(grid),
        "distinct_marker_colors": len(set(analysis["colors"])),
        "marker_positions": [[r, c] for r, c, _color in markers],
        "all_interior": all(0 < r < analysis["h"] - 1 and 0 < c < analysis["w"] - 1
                            for r, c, _color in markers),
        "disjoint_plus_footprints": True,
    }


def _choose_centers(rng, h: int, w: int, count: int) -> list[tuple[int, int]]:
    """Choose `count` interior centers whose radius-1 pluses do not overlap."""
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(candidates)

    def search(start: int, chosen: list[tuple[int, int]], reserved: set[tuple[int, int]]):
        if len(chosen) == count:
            return chosen[:]
        need = count - len(chosen)
        if len(candidates) - start < need:
            return None
        for index in range(start, len(candidates)):
            r, c = candidates[index]
            footprint = {(r + dr, c + dc) for dr, dc in _PLUS}
            if footprint & reserved:
                continue
            chosen.append((r, c))
            found = search(index + 1, chosen, reserved | footprint)
            if found is not None:
                return found
            chosen.pop()
        return None

    result = search(0, [], set())
    if result is None:
        raise ValueError(f"cannot place {count} disjoint plus centers on {h}x{w}")
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    band_offset = {"easy": 0, "medium": 1, "hard": 2}[band]
    profile_offset = ctx.draw_rng("profile_schedule").randrange(len(_CANONICAL_PROFILES))
    scheduled = _CANONICAL_PROFILES[
        (profile_offset + int(sample_index) + band_offset) % len(_CANONICAL_PROFILES)
    ]
    h = _draw_scheduled_int(ctx, "grid_h", 7, 9, scheduled[0])
    w = _draw_scheduled_int(ctx, "grid_w", 8, 11, scheduled[1])
    n_markers = _draw_scheduled_int(ctx, "n_markers", 2, 3, scheduled[2])

    rng = ctx.draw_rng("layout")
    centers = _choose_centers(rng, h, w, n_markers)
    colors = rng.sample(range(1, 10), n_markers)
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(centers, colors):
        grid[r][c] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_markers": n_markers}
    if observed != expected:
        raise AssertionError(f"constructed axes drifted: expected {expected}, observed {observed}")
    return grid


def _expected_output(grid: Any) -> list[list[int]]:
    """Python mirror for evidence only; canonical Racket remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [row[:] for row in analysis["grid"]]
    for r, c, color in analysis["markers"]:
        for dr, dc in _DIRS4:
            out[r + dr][c + dc] = color
    return out


def _rival_horizontal_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [row[:] for row in analysis["grid"]]
    for r, c, color in analysis["markers"]:
        out[r][c - 1] = color
        out[r][c + 1] = color
    return out


def _rival_first_marker_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [row[:] for row in analysis["grid"]]
    r, c, color = analysis["markers"][0]
    for dr, dc in _DIRS4:
        out[r + dr][c + dc] = color
    return out


def _rival_fixed_color_arms(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [row[:] for row in analysis["grid"]]
    fixed = analysis["markers"][0][2]
    for r, c, _color in analysis["markers"]:
        for dr, dc in _DIRS4:
            out[r + dr][c + dc] = fixed
    return out


def _rival_fill_3x3(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [row[:] for row in analysis["grid"]]
    for r, c, color in analysis["markers"]:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                out[r + dr][c + dc] = color
    return out


SEMANTIC_RIVALS = {
    "horizontal_only": _rival_horizontal_only,
    "first_marker_only": _rival_first_marker_only,
    "fixed_color_arms": _rival_fixed_color_arms,
    "fill_3x3": _rival_fill_3x3,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "both_cardinal_axes_required": lambda grid: not strict_canonical_like(grid),
    "every_marker_is_transformed": lambda grid: (
        not strict_canonical_like(grid) and len(_analyze(grid)["markers"]) >= 2
    ),
    "marker_color_controls_its_arms": lambda grid: (
        not strict_canonical_like(grid)
        and len(set(_analyze(grid)["colors"])) == len(_analyze(grid)["colors"])
    ),
    "diagonals_remain_background": lambda grid: not strict_canonical_like(grid),
}

WITNESS_RIVALS = {
    "both_cardinal_axes_required": ["horizontal_only"],
    "every_marker_is_transformed": ["first_marker_only"],
    "marker_color_controls_its_arms": ["fixed_color_arms"],
    "diagonals_remain_background": ["fill_3x3"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to reject each named plausible rival before the query."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demo_inputs: list[Any] = []
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        strict_errors = strict_canonical_like(grid)
        if strict_errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = _expected_output(grid)
        if output != expected:
            reasons.append(f"demo {index} output disagrees with the canonical rule")
            continue
        valid_demo_inputs.append(grid)

    if valid_demo_inputs:
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(grid) == _expected_output(grid) for grid in valid_demo_inputs):
                reasons.append(f"named rival {name!r} survives every demonstration")

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = strict_canonical_like(query_grid)
    if query_errors:
        reasons.append("query input is outside the teaching grammar")
    elif query_output != _expected_output(query_grid):
        reasons.append("query output disagrees with the canonical rule")

    return sorted(set(reasons))
