"""Input sampler for the four-diagonal ray task (ARC 623ea044).

Each lawful input contains one to three well-separated markers of one color on a
zero background.  The unchanged canonical Racket authority preserves every
marker and paints every still-zero cell on all four diagonals in that marker's
color.  Generated markers never lie on one another's diagonal, so the teaching
manifold avoids the written-description ambiguity about rays meeting blockers.

The semantic rivals at the bottom are diagnostics only; labels remain owned by
the canonical Racket program pinned by ``RULE_HASH``.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9ce2dcf587b8"
TASK_ID = GENERATOR_ID
RULE_HASH = "e635bf3ddbe0"
VERSION = "4.0.0"
SUMMARY = (
    "One to three interior markers of one color emit same-color rays along all "
    "four diagonals. Markers remain present; generated markers are separated "
    "and never block one another. A 1/2/3-marker schedule, nine-color cycle, "
    "and exact 7x7, 15x15, and 17x17 anchors teach the complete rule."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0 and all 1..3 markers share one nonzero color",
    "dimensions are 7..17 in each direction",
    "every marker is at least one cell from every edge, exposing all four rays",
    "marker pairs have Chebyshev distance at least 3 and never share a diagonal",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "exact 7x7/15x15/17x17 anchors on even sample indexes; difficulty-skewed broad draws otherwise",
        "valid": "7..17",
    },
    "grid_w": {
        "type": "int",
        "default": "exact 7x7/15x15/17x17 anchors on even sample indexes; difficulty-skewed broad draws otherwise",
        "valid": "7..17",
    },
    "fgc": {
        "type": "color",
        "default": "deterministic 1..9 cycle by sample_index",
        "valid": "1..9",
    },
    "n_dots": {
        "type": "int",
        "default": "deterministic 1,2,3 cycle by sample_index",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

SCHEDULE_PROFILES = ("single", "double", "triple")
LESSON_SCHEDULE_PERIOD = 9
_CANONICAL_PROFILES = ((7, 7), (15, 15), (17, 17))
_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Finite teaching profile; every four consecutive demos contain 1/2/3 dots."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _broad_bounds(difficulty: Any) -> tuple[int, int]:
    if difficulty == "easy":
        return 7, 11
    if difficulty == "hard":
        return 13, 17
    if difficulty == "medium":
        return 9, 15
    return 7, 17


def _compatible(point: tuple[int, int], chosen: Sequence[tuple[int, int]]) -> bool:
    r, c = point
    for rr, cc in chosen:
        dr, dc = abs(r - rr), abs(c - cc)
        if max(dr, dc) < 3 or dr == dc:
            return False
    return True


def _select_positions(h: int, w: int, count: int, rng) -> list[tuple[int, int]]:
    """Construct a readable marker set without retry caps or silent shortening."""
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(candidates)

    chosen: list[tuple[int, int]] = []

    def search(start: int) -> bool:
        if len(chosen) == count:
            return True
        needed = count - len(chosen)
        for index in range(start, len(candidates) - needed + 1):
            point = candidates[index]
            if not _compatible(point, chosen):
                continue
            chosen.append(point)
            if search(index + 1):
                return True
            chosen.pop()
        return False

    if not search(0):  # mathematically unreachable for 7..17 and count <= 3
        raise RuntimeError(f"could not place {count} nonblocking markers on {h}x{w}")
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Every band receives deterministic exact canonical-size support.  Odd
    # sample indexes retain broad, difficulty-skewed geometry.  Caller values
    # always win and are validated against the full declared domain.
    if sample_index % 2 == 0:
        anchor_h, anchor_w = _CANONICAL_PROFILES[(sample_index // 2) % 3]
        ctx.overrides.setdefault("grid_h", anchor_h)
        ctx.overrides.setdefault("grid_w", anchor_w)
    else:
        lo, hi = _broad_bounds(difficulty)
        shape_rng = ctx.draw_rng("broad_dimensions")
        ctx.overrides.setdefault("grid_h", shape_rng.randint(lo, hi))
        ctx.overrides.setdefault("grid_w", shape_rng.randint(lo, hi))

    ctx.overrides.setdefault("n_dots", 1 + sample_index % 3)
    ctx.overrides.setdefault("fgc", 1 + sample_index % 9)

    h = ctx.draw_int_strict("grid_h", 7, 17)
    w = ctx.draw_int_strict("grid_w", 7, 17)
    fgc = ctx.draw_int_strict("fgc", 1, 9)
    n_dots = ctx.draw_int_strict("n_dots", 1, 3)

    grid = full_grid(h, w, 0)
    positions = _select_positions(h, w, n_dots, ctx.draw_rng("marker_positions"))
    for r, c in positions:
        grid[r][c] = fgc
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"errors": [], "markers": []}
    if not isinstance(grid, (list, tuple)) or not grid:
        result["errors"].append("expected a nonempty rectangular grid")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        result["errors"].append("rows must be nonempty lists or tuples")
        return result

    h, w = len(grid), len(grid[0])
    result.update({"h": h, "w": w})
    if not 7 <= h <= 17:
        result["errors"].append(f"height {h} outside 7..17")
    if not 7 <= w <= 17:
        result["errors"].append(f"width {w} outside 7..17")

    rectangular = True
    for r, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != w:
            result["errors"].append(f"row {r} has invalid width")
            rectangular = False
            continue
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                result["errors"].append(f"cell ({r},{c}) is not an integer ARC color 0..9")
    if not rectangular or any("ARC color" in error for error in result["errors"]):
        return result

    markers = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    result["markers"] = markers
    colors = {value for _, _, value in markers}
    result["colors"] = colors
    if not 1 <= len(markers) <= 3:
        result["errors"].append(f"expected 1..3 markers, found {len(markers)}")
    if len(colors) != 1:
        result["errors"].append(f"expected exactly one nonzero color, found {len(colors)}")

    for r, c, _ in markers:
        if not (0 < r < h - 1 and 0 < c < w - 1):
            result["errors"].append(f"marker {(r, c)} must be at least one cell from every edge")

    for index, (r1, c1, _) in enumerate(markers):
        for r2, c2, _ in markers[index + 1 :]:
            dr, dc = abs(r1 - r2), abs(c1 - c2)
            if max(dr, dc) < 3:
                result["errors"].append(
                    f"markers {(r1, c1)} and {(r2, c2)} are closer than Chebyshev distance 3"
                )
            if dr == dc:
                result["errors"].append(
                    f"markers {(r1, c1)} and {(r2, c2)} share a diagonal"
                )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The generated manifold, broad enough to include every canonical input."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe invalid grid: {analysis['errors']}")
    markers = analysis["markers"]
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "fgc": markers[0][2],
        "n_dots": len(markers),
    }


def _shoot(
    grid: Sequence[Sequence[int]],
    directions: Sequence[tuple[int, int]],
    *,
    markers: Sequence[tuple[int, int, int]] | None = None,
    ray_color: int | None = None,
    preserve_sources: bool = True,
) -> list[list[int]]:
    """Pure diagnostic implementation of the selected rule family."""
    h, w = len(grid), len(grid[0])
    source = [list(row) for row in grid]
    out = [list(row) for row in grid]
    active = list(markers) if markers is not None else [
        (r, c, value)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value != 0
    ]
    for r, c, value in active:
        paint = value if ray_color is None else ray_color
        for dr, dc in directions:
            for distance in range(1, max(h, w)):
                nr, nc = r + dr * distance, c + dc * distance
                if not (0 <= nr < h and 0 <= nc < w):
                    continue
                if source[nr][nc] == 0 and out[nr][nc] == 0:
                    out[nr][nc] = paint
    if not preserve_sources:
        for r, c, _ in active:
            out[r][c] = 0
    return out


def _orthogonal_cross(grid):
    """Rival: use horizontal/vertical rays rather than diagonals."""
    return _shoot(grid, _ORTHOGONALS)


def _one_diagonal(grid):
    """Rival: emit only the NW-SE diagonal."""
    return _shoot(grid, ((-1, -1), (1, 1)))


def _first_marker_only(grid):
    """Rival: transform only the lexicographically first marker."""
    first = next(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    )
    return _shoot(grid, _DIAGONALS, markers=[first])


def _fixed_color_one(grid):
    """Rival: paint all ray cells color 1 regardless of source color."""
    return _shoot(grid, _DIAGONALS, ray_color=1)


def _erase_sources(grid):
    """Rival: draw the correct rays but erase the original marker cells."""
    return _shoot(grid, _DIAGONALS, preserve_sources=False)


def _all_markers_have_four_direction_room(grid) -> bool:
    return not self_check(grid) and all(
        0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1
        for r, c, _ in _analyze(grid)["markers"]
    )


def _has_multiple_markers(grid) -> bool:
    return not self_check(grid) and len(_analyze(grid)["markers"]) >= 2


def _has_non_one_color(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid)["fgc"] != 1


def _has_source_marker(grid) -> bool:
    return not self_check(grid) and bool(_analyze(grid)["markers"])


SEMANTIC_RIVALS: dict[str, Callable] = {
    "orthogonal_cross": _orthogonal_cross,
    "one_diagonal": _one_diagonal,
    "first_marker_only": _first_marker_only,
    "fixed_color_one": _fixed_color_one,
    "erase_sources": _erase_sources,
}
SEMANTIC_WITNESSES: dict[str, Callable] = {
    "four_direction_room": _all_markers_have_four_direction_room,
    "multiple_markers": _has_multiple_markers,
    "non_one_color": _has_non_one_color,
    "source_preserved": _has_source_marker,
}
WITNESS_RIVALS = {
    "four_direction_room": ["orthogonal_cross", "one_diagonal"],
    "multiple_markers": ["first_marker_only"],
    "non_one_color": ["fixed_color_one"],
    "source_preserved": ["erase_sources"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Finite declared-rival check; not a proof over all possible hypotheses."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        changes_query = "output" not in query or rival(query["input"]) != query["output"]
        if fits and changes_query:
            reasons.append(f"declared competitor {name!r} fits all demonstrations")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    blank = full_grid(7, 7, 0)

    multicolor = full_grid(7, 7, 0)
    multicolor[2][2] = 3
    multicolor[4][3] = 4

    edge_marker = full_grid(7, 7, 0)
    edge_marker[0][3] = 5

    adjacent = full_grid(7, 7, 0)
    adjacent[2][2] = adjacent[3][3] = 6

    diagonal_blockers = full_grid(7, 7, 0)
    diagonal_blockers[1][1] = diagonal_blockers[4][4] = 7

    too_many = full_grid(7, 7, 0)
    for r, c in ((1, 1), (1, 4), (4, 2), (5, 5)):
        too_many[r][c] = 8

    return [
        ("blank_grid", blank),
        ("multiple_marker_colors", multicolor),
        ("edge_marker", edge_marker),
        ("markers_too_close", adjacent),
        ("diagonal_blockers", diagonal_blockers),
        ("too_many_markers", too_many),
    ]
