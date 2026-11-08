"""Generator for ``easy_41_stamp_x_at_markers``.

The input is a 0-background grid containing blue (1) marker cells.  The
canonical Racket rule emits a fresh same-size grid and stamps an orange (7)
X at every marker: the center plus four diagonal neighbours, clipped at the
boundary.  Overlapping stamps are a lawful union because every painted cell
uses the same color.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d02691ffb818"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"
RULE_HASH = "3eec1d7807b1"

SUMMARY = (
    "A 0-background grid contains 2..14 blue (1) markers.  The three-slot "
    "default curriculum cycles through canonical interior-separated layouts, "
    "boundary markers whose orange X is clipped, and nearby markers whose "
    "orange X stamps overlap by union.  The rule emits a fresh same-size grid "
    "and paints color 7 at each marker and its four in-bounds diagonal "
    "neighbours."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "input background is 0 and marker color is 1",
    "output is a fresh same-size 0-background grid",
    "each marker paints its center and four in-bounds diagonal neighbours color 7",
    "boundary clipping and same-color overlap are lawful rule behavior",
]

# Only observable, exact public controls are advertised.  Difficulty changes
# defaults, never the validity of an explicit override.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled/rng", "valid": "5..20"},
    "grid_w": {"type": "int", "default": "scheduled/rng", "valid": "5..20"},
    "markers": {"type": "int", "default": "profile+difficulty", "valid": "2..14"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

CANONICAL_SHAPES = ((8, 8), (9, 11), (10, 9), (11, 8))
SCHEDULE_PROFILES = ("canonical", "edge", "clustered")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the deterministic profile used by an ordinary draw.

    Every three consecutive sample indexes contain all three profiles, so any
    three-demonstration lesson contains canonical support plus counterexamples
    to the two shortcuts that fit every canonical pair.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {"grid_h": (5, 20), "grid_w": (5, 20), "markers": (2, 14)}
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, got {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _default_dimension_bounds(difficulty: str | None) -> tuple[int, int]:
    if difficulty == "easy":
        return 7, 11
    if difficulty == "hard":
        return 10, 20
    return 8, 15


def _default_marker_bounds(profile: str, difficulty: str | None) -> tuple[int, int]:
    if profile == "canonical":
        return 2, 4
    if difficulty == "easy":
        return 2, 4
    if difficulty == "hard":
        return 8, 14
    return 4, 8


def _canonical_lattice(h: int, w: int, target: int, rng: Any) -> list[tuple[int, int]]:
    """Choose up to ``target`` interior markers with Chebyshev spacing >= 3."""
    lattices: list[list[tuple[int, int]]] = []
    for roff in (1, 2, 3):
        for coff in (1, 2, 3):
            cells = [
                (r, c)
                for r in range(roff, h - 1, 3)
                for c in range(coff, w - 1, 3)
            ]
            if len(cells) >= target:
                lattices.append(cells)
    if not lattices:
        return []
    cells = list(lattices[rng.randrange(len(lattices))])
    rng.shuffle(cells)
    return cells[:target]


def _points_have_output_relevant_border_stamp(
    points: list[tuple[int, int]],
    h: int,
    w: int,
) -> bool:
    """Return whether border markers paint any cell not painted by interior markers."""
    border_cells: set[tuple[int, int]] = set()
    interior_cells: set[tuple[int, int]] = set()
    for r, c in points:
        destination = (
            border_cells
            if r in (0, h - 1) or c in (0, w - 1)
            else interior_cells
        )
        for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                destination.add((rr, cc))
    return bool(border_cells - interior_cells)


def _edge_layout(h: int, w: int, target: int, rng: Any) -> list[tuple[int, int]]:
    border = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    ]
    rng.shuffle(border)
    anchor = border[0]
    # Reserve the anchor's center as an observable clipped-stamp contribution.
    # Any other marker that could paint that center must be diagonally adjacent.
    blockers = {
        (anchor[0] + dr, anchor[1] + dc)
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
        if 0 <= anchor[0] + dr < h and 0 <= anchor[1] + dc < w
    }
    chosen = [anchor]
    remaining = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) != anchor and (r, c) not in blockers
    ]
    rng.shuffle(remaining)
    chosen.extend(remaining[: max(0, target - 1)])
    return chosen


def _clustered_layout(h: int, w: int, target: int, rng: Any) -> list[tuple[int, int]]:
    anchors = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(anchors)
    anchor = anchors[0]
    neighbours = [
        (anchor[0] + dr, anchor[1] + dc)
        for dr in (-2, -1, 0, 1, 2)
        for dc in (-2, -1, 0, 1, 2)
        if (dr or dc)
        and 0 <= anchor[0] + dr < h
        and 0 <= anchor[1] + dc < w
    ]
    rng.shuffle(neighbours)
    chosen = [anchor]
    if target >= 2:
        chosen.append(neighbours[0])
    remaining = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in set(chosen)
    ]
    rng.shuffle(remaining)
    chosen.extend(remaining[: max(0, target - len(chosen))])
    return chosen


def _minimal_teaching_impostor(points: list[tuple[int, int]]) -> str | None:
    """Name tiny low-information layouts excluded from the teaching grammar.

    The total Racket rule is defined on these inputs, but singleton, solid-2x2,
    and four-cell-line scenes are generic mutation probes rather than useful
    demonstrations of independent marker stamping.
    """
    if len(points) == 1:
        return "singleton marker"
    if len(points) != 4:
        return None
    cells = set(points)
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    if len(rows) == 1 and len(cols) == 4 and cols == list(range(cols[0], cols[0] + 4)):
        return "four-cell horizontal line"
    if len(cols) == 1 and len(rows) == 4 and rows == list(range(rows[0], rows[0] + 4)):
        return "four-cell vertical line"
    if len(rows) == 2 and len(cols) == 2 and len(cells) == 4:
        return "solid 2x2 marker block"
    return None


def _repair_minimal_teaching_impostor(
    profile: str,
    points: list[tuple[int, int]],
    h: int,
    w: int,
    rng: Any,
) -> list[tuple[int, int]]:
    """Move one non-witness marker if a draw hits a rejected tiny layout."""
    if _minimal_teaching_impostor(points) is None:
        return points

    protected = {0} if profile == "edge" else ({0, 1} if profile == "clustered" else set())
    candidates = [(r, c) for r in range(h) for c in range(w) if (r, c) not in set(points)]
    rng.shuffle(candidates)
    for index in reversed(range(len(points))):
        if index in protected:
            continue
        for candidate in candidates:
            trial = list(points)
            trial[index] = candidate
            if len(set(trial)) != len(trial):
                continue
            if _minimal_teaching_impostor(trial) is not None:
                continue
            if profile == "edge" and not _points_have_output_relevant_border_stamp(
                trial, h, w
            ):
                continue
            if profile == "clustered" and not any(
                max(abs(r - rr), abs(c - cc)) <= 2
                for i, (r, c) in enumerate(trial)
                for rr, cc in trial[i + 1 :]
            ):
                continue
            return trial
    raise RuntimeError("could not repair a minimal teaching impostor")


def _complete_layout(
    profile: str,
    h: int,
    w: int,
    target: int,
    rng: Any,
) -> list[tuple[int, int]]:
    if profile == "canonical":
        chosen = _canonical_lattice(h, w, target, rng)
        # Explicit high-count/small-canvas overrides may exceed the separated
        # lattice capacity.  Preserve the requested exact count rather than
        # silently changing it; such a draw simply leaves the strict profile.
        if len(chosen) < target:
            remaining = [
                (r, c)
                for r in range(h)
                for c in range(w)
                if (r, c) not in set(chosen)
            ]
            rng.shuffle(remaining)
            chosen.extend(remaining[: target - len(chosen)])
        return chosen
    if profile == "edge":
        return _edge_layout(h, w, target, rng)
    if profile == "clustered":
        return _clustered_layout(h, w, target, rng)
    raise AssertionError(f"unknown internal profile: {profile}")


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides: Any):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    if profile == "canonical":
        shape_rng = ctx.draw_rng("canonical_shape")
        base_h, base_w = CANONICAL_SHAPES[shape_rng.randrange(len(CANONICAL_SHAPES))]
        # Even a scheduled fixed dimension must flow through the public keyed
        # draw so the exact-axis provenance contract can verify the default
        # path.  Explicit overrides retain the full advertised domain.
        h = ctx.draw_int("grid_h", 5, 20) if "grid_h" in overrides else ctx.draw_int("grid_h", base_h, base_h)
        w = ctx.draw_int("grid_w", 5, 20) if "grid_w" in overrides else ctx.draw_int("grid_w", base_w, base_w)
    else:
        lo, hi = _default_dimension_bounds(difficulty)
        h = ctx.draw_int("grid_h", 5, 20) if "grid_h" in overrides else ctx.draw_int("grid_h", lo, hi)
        w = ctx.draw_int("grid_w", 5, 20) if "grid_w" in overrides else ctx.draw_int("grid_w", lo, hi)

    if "markers" in overrides:
        target = ctx.draw_int("markers", 2, 14)
    else:
        marker_lo, marker_hi = _default_marker_bounds(profile, difficulty)
        target = ctx.draw_int("markers", marker_lo, marker_hi)

    layout_rng = ctx.draw_rng("layout")
    points = _complete_layout(profile, h, w, target, layout_rng)
    points = _repair_minimal_teaching_impostor(profile, points, h, w, layout_rng)
    if len(points) != target or len(set(points)) != target:
        raise RuntimeError(
            f"internal placement error: requested {target}, produced {len(set(points))} unique markers"
        )

    grid = full_grid(h, w, 0)
    for r, c in points:
        grid[r][c] = 1
    return grid


def _markers(grid: Any) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]


def observe_overrides(grid: Any) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "markers": len(_markers(grid)),
    }


def self_check(grid: Any, *, difficulty: str | None = None, meta: Any = None) -> list[str]:
    """Validate the selected generator's lawful input domain.

    Boundary markers and nearby markers are deliberately accepted: clipping and
    same-color stencil overlap are explicit behavior of the pinned rule.
    """
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 1) for row in grid for value in row):
        return ["cells must be integer colors 0 or 1"]

    h, w = len(grid), width
    errors: list[str] = []
    if not (5 <= h <= 20 and 5 <= w <= 20):
        errors.append(f"grid shape {h}x{w} outside selected domain 5..20 by 5..20")
    points = _markers(grid)
    count = len(points)
    if not 2 <= count <= 14:
        errors.append(f"expected 2..14 markers, got {count}")
    impostor = _minimal_teaching_impostor(points)
    if impostor is not None:
        errors.append(f"excluded low-information teaching layout: {impostor}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    points = _markers(grid)
    reasons: list[str] = []
    if (h, w) not in CANONICAL_SHAPES:
        reasons.append("shape is outside the four observed canonical profiles")
    if not 2 <= len(points) <= 4:
        reasons.append("canonical examples contain 2..4 markers")
    if any(r in (0, h - 1) or c in (0, w - 1) for r, c in points):
        reasons.append("canonical examples keep markers off the border")
    if any(
        max(abs(r - rr), abs(c - cc)) <= 2
        for i, (r, c) in enumerate(points)
        for rr, cc in points[i + 1 :]
    ):
        reasons.append("canonical examples keep X stencils non-overlapping")
    return reasons


# ---------------------------------------------------------------------------
# Executable semantic contract.  These are competitors and witnesses only;
# the canonical Racket program remains the label authority.
# ---------------------------------------------------------------------------

_X_OFFSETS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
_CARDINAL_OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def _render(
    grid: Any,
    *,
    offsets: tuple[tuple[int, int], ...] = _X_OFFSETS,
    marker_filter: Callable[[tuple[int, int], list[tuple[int, int]], int, int], bool] | None = None,
    preserve_blue_center: bool = False,
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    points = _markers(grid)
    out = full_grid(h, w, 0)
    for point in points:
        r, c = point
        if marker_filter is not None and not marker_filter(point, points, h, w):
            continue
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 7
        if preserve_blue_center:
            out[r][c] = 1
    return out


def _correct_x(grid: Any) -> list[list[int]]:
    return _render(grid)


def _ignore_border_markers(grid: Any) -> list[list[int]]:
    return _render(
        grid,
        marker_filter=lambda p, points, h, w: p[0] not in (0, h - 1) and p[1] not in (0, w - 1),
    )


def _drop_clustered_markers(grid: Any) -> list[list[int]]:
    def isolated(point: tuple[int, int], points: list[tuple[int, int]], h: int, w: int) -> bool:
        del h, w
        r, c = point
        return not any(
            other != point and max(abs(r - other[0]), abs(c - other[1])) <= 2
            for other in points
        )

    return _render(grid, marker_filter=isolated)


def _center_only(grid: Any) -> list[list[int]]:
    return _render(grid, offsets=((0, 0),))


def _cardinal_cross(grid: Any) -> list[list[int]]:
    return _render(grid, offsets=_CARDINAL_OFFSETS)


def _preserve_blue_center(grid: Any) -> list[list[int]]:
    return _render(grid, preserve_blue_center=True)


def _has_output_relevant_border_marker(grid: Any) -> bool:
    """True only when dropping border markers actually changes the rule output."""
    return _correct_x(grid) != _ignore_border_markers(grid)


def _has_clustered_pair(grid: Any) -> bool:
    points = _markers(grid)
    return any(
        max(abs(r - rr), abs(c - cc)) <= 2
        for i, (r, c) in enumerate(points)
        for rr, cc in points[i + 1 :]
    )


def _has_interior_marker(grid: Any) -> bool:
    h, w = len(grid), len(grid[0])
    return any(0 < r < h - 1 and 0 < c < w - 1 for r, c in _markers(grid))


SEMANTIC_RIVALS = {
    "ignore_border_markers": _ignore_border_markers,
    "drop_clustered_markers": _drop_clustered_markers,
    "center_only": _center_only,
    "cardinal_cross": _cardinal_cross,
    "preserve_blue_center": _preserve_blue_center,
}
SEMANTIC_WITNESSES = {
    "clipped_border_x": _has_output_relevant_border_marker,
    "overlapping_x_union": _has_clustered_pair,
    "diagonal_orange_x": _has_interior_marker,
}
WITNESS_RIVALS = {
    "clipped_border_x": ["ignore_border_markers"],
    "overlapping_x_union": ["drop_clustered_markers"],
    "diagonal_orange_x": ["center_only", "cardinal_cross", "preserve_blue_center"],
}
CANONICAL_SHORTCUTS = {
    "ignore_border_markers": _ignore_border_markers,
    "drop_clustered_markers": _drop_clustered_markers,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Require the demonstrations to refute every declared competitor."""
    del query
    survivors = [
        name
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(demo["input"]) == demo["output"] for demo in demos)
    ]
    if survivors:
        return ["declared competitors fit every demonstration: " + ", ".join(sorted(survivors))]
    return []
