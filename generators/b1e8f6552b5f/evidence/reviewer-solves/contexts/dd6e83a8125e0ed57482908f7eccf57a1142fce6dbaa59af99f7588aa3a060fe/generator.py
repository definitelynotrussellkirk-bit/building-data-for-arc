"""Generator for ``b1e8f6552b5f`` — stamp hollow 3x3 rings.

Every nonzero input cell is an isolated interior marker.  The canonical rule
creates a fresh background-0 grid and, for each marker, paints the eight cells
in its 3x3 neighborhood while leaving the marker's original center empty.

The four-example schedule is deliberately lesson-level rather than marginal:

* an aligned same-color pair whose ring reaches the canvas edge;
* a separated distinct-color pair on the canonical 9x9 profile;
* a mixed-color triple containing both edge-touching and interior rings; and
* four distinct markers on a larger canvas.

Together those examples rebut fixed marker-count, unique-color-only,
first-marker/first-two-marker, center-preserving, plus-only, corners-only,
border-only, and color-blind shortcuts while retaining the Racket program as
the sole output authority.
"""
from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b1e8f6552b5f"
TASK_ID = "b1e8f6552b5f"
VERSION = "3.0.1"
RULE_HASH = "94525d5f470a"

SUMMARY = (
    "Expand each isolated interior nonzero marker into an empty-centered "
    "hollow 3x3 ring in the marker's own color."
)

INVARIANTS = [
    "the rectangular canvas uses background 0 and marker colors 1..9",
    "there are 2-4 isolated nonzero marker cells, each at least one cell from the border",
    "marker centers have Chebyshev distance at least 3, so 3x3 ring footprints never overlap",
    "marker colors may repeat or differ; every marker is transformed independently",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 7, 9, band-rng 8..12, or 13",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 7, 9, band-rng 8..12, or 13",
        "valid": "7..13",
    },
    "n_markers": {
        "type": "int",
        "default": "four-example schedule 2,2,3,4",
        "valid": "2..4",
    },
}

_VALID_H = (7, 13)
_VALID_W = (7, 13)
_VALID_N = (2, 4)
_PROFILE_NAMES = (
    "aligned_same_pair",
    "canonical_distinct_pair",
    "mixed_triple",
    "distinct_quad",
)
_PROFILE_MARKER_COUNTS = {
    "aligned_same_pair": 2,
    "canonical_distinct_pair": 2,
    "mixed_triple": 3,
    "distinct_quad": 4,
}
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

_OFFSETS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_OFFSETS_PLUS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_OFFSETS_CORNERS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic four-example semantic schedule."""
    del seed, difficulty
    return _PROFILE_NAMES[sample_index % len(_PROFILE_NAMES)]


def _marker_cells(grid) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _ring_touches_border(r: int, c: int, h: int, w: int) -> bool:
    return r in (1, h - 2) or c in (1, w - 2)


def _ring_is_interior(r: int, c: int, h: int, w: int) -> bool:
    return 2 <= r <= h - 3 and 2 <= c <= w - 3


def _far_enough(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) >= 3


def _layout_ok(
    centers: tuple[tuple[int, int], ...],
    *,
    profile: str,
    h: int,
    w: int,
    strict_profile: bool,
) -> bool:
    if not centers:
        return False
    if not all(_far_enough(a, b) for i, a in enumerate(centers) for b in centers[i + 1 :]):
        return False
    if not strict_profile:
        return True

    if profile == "aligned_same_pair":
        return (
            len(centers) == 2
            and (centers[0][0] == centers[1][0] or centers[0][1] == centers[1][1])
            and any(_ring_touches_border(r, c, h, w) for r, c in centers)
        )
    if profile == "canonical_distinct_pair":
        return (
            len(centers) == 2
            and centers[0][0] != centers[1][0]
            and centers[0][1] != centers[1][1]
            and all(_ring_is_interior(r, c, h, w) for r, c in centers)
        )
    if profile == "mixed_triple":
        rows = {r for r, _ in centers}
        cols = {c for _, c in centers}
        return (
            len(centers) == 3
            and len(rows) > 1
            and len(cols) > 1
            and any(_ring_touches_border(r, c, h, w) for r, c in centers)
            and any(_ring_is_interior(r, c, h, w) for r, c in centers)
        )
    if profile == "distinct_quad":
        return len(centers) == 4 and all(
            _ring_is_interior(r, c, h, w) for r, c in centers
        )
    raise ValueError(f"unknown schedule profile: {profile!r}")


def _choose_centers(
    *,
    h: int,
    w: int,
    n_markers: int,
    profile: str,
    rng,
    strict_profile: bool,
) -> tuple[tuple[int, int], ...]:
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]

    # Profile-aware ordering makes the intended branch common while the keyed
    # shuffle preserves substantial positional variation across seeds.
    rng.shuffle(candidates)
    if strict_profile and profile == "aligned_same_pair":
        candidates.sort(key=lambda p: (not _ring_touches_border(*p, h, w), rng.random()))
    elif strict_profile and profile in ("canonical_distinct_pair", "distinct_quad"):
        candidates.sort(key=lambda p: (not _ring_is_interior(*p, h, w), rng.random()))
    elif strict_profile and profile == "mixed_triple":
        candidates.sort(
            key=lambda p: (
                not (_ring_touches_border(*p, h, w) or _ring_is_interior(*p, h, w)),
                rng.random(),
            )
        )

    chosen: list[tuple[int, int]] = []

    def search(start: int) -> tuple[tuple[int, int], ...] | None:
        if len(chosen) == n_markers:
            result = tuple(chosen)
            return result if _layout_ok(
                result,
                profile=profile,
                h=h,
                w=w,
                strict_profile=strict_profile,
            ) else None
        needed = n_markers - len(chosen)
        for index in range(start, len(candidates) - needed + 1):
            point = candidates[index]
            if any(not _far_enough(point, prior) for prior in chosen):
                continue
            chosen.append(point)
            result = search(index + 1)
            if result is not None:
                return result
            chosen.pop()
        return None

    result = search(0)
    if result is not None:
        return result

    # Exact overrides may request a small canvas that cannot realize the
    # ordinary profile's extra branch predicate.  The core task grammar is
    # still feasible for every declared boundary tuple, so retry without the
    # schedule-only constraints rather than silently changing an exact axis.
    if strict_profile:
        return _choose_centers(
            h=h,
            w=w,
            n_markers=n_markers,
            profile=profile,
            rng=rng,
            strict_profile=False,
        )
    raise ValueError(
        f"cannot place {n_markers} disjoint interior markers in {h}x{w}"
    )


def _choose_colors(n_markers: int, profile: str, rng) -> tuple[int, ...]:
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if profile == "aligned_same_pair":
        return tuple([palette[0]] * n_markers)
    if profile == "canonical_distinct_pair" or profile == "distinct_quad":
        return tuple(palette[:n_markers])
    if profile == "mixed_triple":
        if n_markers == 2:
            return (palette[0], palette[0])
        colors = [palette[0], palette[0], palette[1]]
        colors.extend(palette[2:n_markers - 1])
        rng.shuffle(colors)
        return tuple(colors)
    raise ValueError(f"unknown schedule profile: {profile!r}")


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_markers": len(_marker_cells(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes; accept every canonical input."""
    del difficulty, meta
    if not grid or not grid[0]:
        return ["grid must be nonempty"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"grid width {w} outside {_VALID_W[0]}..{_VALID_W[1]}")

    invalid = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
        },
        key=repr,
    )
    if invalid:
        errors.append(f"cell values must be integer ARC colors 0..9, got {invalid}")
        return errors

    markers = _marker_cells(grid)
    if not (_VALID_N[0] <= len(markers) <= _VALID_N[1]):
        errors.append(
            f"expected {_VALID_N[0]}..{_VALID_N[1]} nonzero markers, found {len(markers)}"
        )
    for r, c, _ in markers:
        if not (1 <= r <= h - 2 and 1 <= c <= w - 2):
            errors.append(
                f"marker at ({r},{c}) must be at least one cell from every border"
            )
            break

    centers = [(r, c) for r, c, _ in markers]
    for i, first in enumerate(centers):
        for second in centers[i + 1 :]:
            if not _far_enough(first, second):
                errors.append(
                    f"marker centers {first} and {second} have overlapping 3x3 footprints"
                )
                return errors
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The teaching grammar is a strict, count-bounded canonical extension."""
    return self_check(grid)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    profile_index = _PROFILE_NAMES.index(profile)

    if profile_index == 0:
        default_h = default_w = (7, 7)
        default_n = (2, 2)
    elif profile_index == 1:
        default_h = default_w = (9, 9)
        default_n = (2, 2)
    elif profile_index == 2:
        band = difficulty or "medium"
        ranges = {
            "easy": ((8, 10), (8, 10)),
            "medium": ((9, 11), (9, 11)),
            "hard": ((10, 12), (10, 12)),
        }
        default_h, default_w = ranges.get(band, ranges["medium"])
        default_n = (3, 3)
    else:
        default_h = default_w = (13, 13)
        default_n = (4, 4)

    h = ctx.draw_int(
        "grid_h",
        *(_VALID_H if "grid_h" in overrides else default_h),
    )
    w = ctx.draw_int(
        "grid_w",
        *(_VALID_W if "grid_w" in overrides else default_w),
    )
    n_markers = ctx.draw_int(
        "n_markers",
        *(_VALID_N if "n_markers" in overrides else default_n),
    )

    layout_rng = ctx.draw_rng("layout")
    # Exact size controls should not silently erase a still-compatible teaching
    # profile.  A marker-count override that changes the profile cardinality is
    # intentionally non-strict; infeasible strict layouts fall back inside
    # _choose_centers without changing any requested exact axis.
    strict_profile = n_markers == _PROFILE_MARKER_COUNTS[profile]
    centers = _choose_centers(
        h=h,
        w=w,
        n_markers=n_markers,
        profile=profile,
        rng=layout_rng,
        strict_profile=strict_profile,
    )
    colors = _choose_colors(n_markers, profile, ctx.draw_rng("colors"))

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(centers, colors):
        grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _stamp_prediction(
    grid,
    *,
    offsets=_OFFSETS_8,
    include_center: bool = False,
    marker_limit: int | None = None,
    fixed_color: int | None = None,
    unique_colors_only: bool = False,
    border_policy: str = "all",
):
    h = len(grid)
    w = len(grid[0]) if h else 0
    output = full_grid(h, w, 0)
    markers = _marker_cells(grid)
    counts = Counter(value for _, _, value in markers)
    if marker_limit is not None:
        markers = markers[:marker_limit]
    for r, c, color in markers:
        if unique_colors_only and counts[color] != 1:
            continue
        touches = _ring_touches_border(r, c, h, w)
        if border_policy == "skip_touching" and touches:
            continue
        if border_policy == "touching_only" and not touches:
            continue
        paint_color = fixed_color if fixed_color is not None else color
        cells = list(offsets)
        if include_center:
            cells.append((0, 0))
        for dr, dc in cells:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                output[rr][cc] = paint_color
    return output


def _identity(grid):
    return copy.deepcopy(grid)


def _solid_3x3(grid):
    return _stamp_prediction(grid, include_center=True)


def _plus_only(grid):
    return _stamp_prediction(grid, offsets=_OFFSETS_PLUS)


def _corners_only(grid):
    return _stamp_prediction(grid, offsets=_OFFSETS_CORNERS)


def _first_marker_only(grid):
    return _stamp_prediction(grid, marker_limit=1)


def _first_two_only(grid):
    return _stamp_prediction(grid, marker_limit=2)


def _color_blind(grid):
    return _stamp_prediction(grid, fixed_color=1)


def _unique_color_only(grid):
    return _stamp_prediction(grid, unique_colors_only=True)


def _skip_border_touching(grid):
    return _stamp_prediction(grid, border_policy="skip_touching")


def _border_touching_only(grid):
    return _stamp_prediction(grid, border_policy="touching_only")


SEMANTIC_RIVALS = {
    "identity": _identity,
    "solid_3x3": _solid_3x3,
    "plus_only": _plus_only,
    "corners_only": _corners_only,
    "first_marker_only": _first_marker_only,
    "first_two_only": _first_two_only,
    "color_blind": _color_blind,
    "unique_color_only": _unique_color_only,
    "skip_border_touching": _skip_border_touching,
    "border_touching_only": _border_touching_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "unique_color_only": _unique_color_only,
}


def _analysis(grid) -> dict:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    markers = _marker_cells(grid)
    counts = Counter(value for _, _, value in markers)
    return {
        "errors": [],
        "markers": markers,
        "n_markers": len(markers),
        "repeated_color": any(count > 1 for count in counts.values()),
        "non_one_color": any(color != 1 for _, _, color in markers),
        "border_touching": any(_ring_touches_border(r, c, h, w) for r, c, _ in markers),
        "interior_marker": any(_ring_is_interior(r, c, h, w) for r, c, _ in markers),
    }


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid):
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[name])

    return predicate


SEMANTIC_WITNESSES = {
    "multiple_markers": lambda grid: not self_check(grid) and len(_marker_cells(grid)) >= 2,
    "three_or_more_markers": lambda grid: not self_check(grid) and len(_marker_cells(grid)) >= 3,
    "repeated_marker_color": _witness("repeated_color"),
    "marker_color_preserved": _witness("non_one_color"),
    "border_touching_ring": _witness("border_touching"),
    "interior_ring": _witness("interior_marker"),
    "orthogonal_ring_cells": lambda grid: not self_check(grid),
    "diagonal_ring_cells": lambda grid: not self_check(grid),
    "empty_center": lambda grid: not self_check(grid),
}

WITNESS_RIVALS = {
    "multiple_markers": ["first_marker_only"],
    "three_or_more_markers": ["first_two_only"],
    "repeated_marker_color": ["unique_color_only"],
    "marker_color_preserved": ["color_blind"],
    "border_touching_ring": ["skip_border_touching"],
    "interior_ring": ["border_touching_only"],
    "orthogonal_ring_cells": ["corners_only"],
    "diagonal_ring_cells": ["plus_only"],
    "empty_center": ["solid_3x3"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits every demo but changes query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but predicts a different query output"
                )
    return reasons
