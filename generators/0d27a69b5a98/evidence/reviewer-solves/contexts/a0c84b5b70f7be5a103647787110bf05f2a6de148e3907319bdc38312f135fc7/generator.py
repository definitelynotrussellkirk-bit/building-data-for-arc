"""Curriculum sampler for 0d27a69b5a98: complete reflection across a 9-line.

The selected Racket authority finds a full-height color-9 column (preferred) or
full-width color-9 row, then copies every non-background, non-axis cell to its
in-bounds mirror.  Source objects may be on either side.  This sampler cycles
a four-slot lesson cycle with the bilateral witness repeated so neither ordered
nor query-rotated three-example lessons can be solved by the canonical shortcut "always copy top/left into an empty bottom/right".
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d27a69b5a98"
TASK_ID = GENERATOR_ID
RULE_HASH = "84d7043f128c"
VERSION = "2.1.0"
SUMMARY = (
    "A full color-9 row or column is a reflection axis. Copy every colored "
    "cell to its in-bounds mirror, regardless of which side supplied it."
)

INVARIANTS = [
    "background is 0 and exactly one full-grid row or column is color 9",
    "at least one non-{0,9} source cell has a missing in-bounds mirror",
    "generated source objects stay one cell away from the axis",
    "generated mirror orbits do not conflict, so original source cells survive",
    "the four-slot curriculum is primary, bilateral, secondary, bilateral",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchor in 7..10", "valid": "7..10"},
    "grid_w": {"type": "int", "default": "canonical anchor in 8..10", "valid": "8..10"},
    "axis_orientation": {
        "type": "str",
        "default": "canonical anchor",
        "valid": "vertical|horizontal",
    },
    "n_colors": {"type": "int", "default": "2 (canonical palette size)", "valid": "1..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# All four public input profiles.  Default sampling rotates through exact
# canonical (height, width, palette-size) anchors in every difficulty band;
# explicit overrides still expose the full documented rectangular domain.
_CANONICAL_PROFILES = (
    (7, 9, "vertical"),
    (9, 8, "horizontal"),
    (8, 10, "vertical"),
    (10, 9, "horizontal"),
)
_CANONICAL_AXIS = {
    (7, 9, "vertical"): 4,
    (9, 8, "horizontal"): 4,
    (8, 10, "vertical"): 6,
    (10, 9, "horizontal"): 5,
}

SCHEDULE_PROFILES = ("primary_only", "bilateral", "secondary_only", "bilateral")
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
# Three demonstrations are assembled with one held-out query.  Repeating the
# bilateral profile guarantees every three-of-four query rotation retains a
# witness against both canonical shortcuts.
EXAMPLES_NEEDED = 3

# Connected polyominoes.  Every profile first searches without the monomino;
# the one-cell shape is a constructive fallback for the smallest legal canvas.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
)
_SINGLETON = ((0, 0),)

Grid = list[list[int]]
Point = tuple[int, int]
Shape = tuple[Point, ...]


def _is_grid(grid: Any) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _find_axis(grid: Grid) -> tuple[str, int]:
    """Return the unique full color-9 axis, rejecting ambiguous inputs."""
    if not _is_grid(grid):
        raise ValueError("grid must be a nonempty rectangular list of rows")
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(rows) + len(cols) != 1:
        raise ValueError(
            f"expected exactly one full color-9 row or column, found {len(rows)} row(s) "
            f"and {len(cols)} column(s)"
        )
    return ("horizontal", rows[0]) if rows else ("vertical", cols[0])


def _mirror(point: Point, orientation: str, axis: int) -> Point:
    r, c = point
    if orientation == "vertical":
        return r, 2 * axis - c
    return 2 * axis - r, c


def _in_bounds(grid: Grid, point: Point) -> bool:
    r, c = point
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def _intended_output(grid: Grid) -> Grid:
    """Independent Python mirror of the selected Racket authority.

    The iteration reads the original input and writes row-major into a copy,
    matching ``fold-cells g g`` even for broader inputs with occupied mirrors.
    """
    orientation, axis = _find_axis(grid)
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            target = _mirror((r, c), orientation, axis)
            if _in_bounds(original, target):
                tr, tc = target
                output[tr][tc] = value
    return output


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the semantic input domain while accepting every public input."""
    del difficulty, meta
    if not _is_grid(grid):
        return ["grid must be a nonempty rectangular list of rows"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not (0 <= value <= 9):
                errors.append(f"cell ({r},{c}) must be an integer color in 0..9")
                if len(errors) >= 4:
                    return errors
    try:
        orientation, axis = _find_axis(grid)
    except ValueError as exc:
        return [str(exc)]

    # A full axis is the only lawful use of 9.  This excludes accidental
    # secondary axis fragments while retaining all canonical examples.
    stray_nines: list[Point] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 9:
                continue
            on_axis = c == axis if orientation == "vertical" else r == axis
            if not on_axis:
                stray_nines.append((r, c))
    if stray_nines:
        errors.append(f"color 9 must occur only on the full axis; found stray cells {stray_nines[:3]}")

    object_cells = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 9)
    ]
    if not object_cells:
        errors.append("at least one non-{0,9} object cell is required")
        return errors

    copy_witness = False
    for point in object_cells:
        target = _mirror(point, orientation, axis)
        if _in_bounds(grid, target):
            tr, tc = target
            if grid[tr][tc] != grid[point[0]][point[1]]:
                copy_witness = True
                break
    if not copy_witness:
        errors.append("input has no output-changing in-bounds reflection witness")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Generated inputs and public inputs share this validated rule domain."""
    return self_check(grid)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Four-slot cycle; every three consecutive slots retain a bilateral witness."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _strict_int_override(name: str, value: Any, lo: int, hi: int) -> None:
    if value is None:
        return
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not {type(value).__name__})")
    if not lo <= value <= hi:
        raise ValueError(f"{name}={value} is outside [{lo}, {hi}]")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise KeyError(f"unknown override axes: {sorted(unknown)}")
    _strict_int_override("grid_h", overrides.get("grid_h"), 7, 10)
    _strict_int_override("grid_w", overrides.get("grid_w"), 8, 10)
    _strict_int_override("n_colors", overrides.get("n_colors"), 1, 3)
    orientation = overrides.get("axis_orientation")
    if orientation is not None:
        if type(orientation) is not str:
            raise TypeError("axis_orientation must be a string")
        if orientation not in ("vertical", "horizontal"):
            raise ValueError("axis_orientation must be 'vertical' or 'horizontal'")


def _draw_int(ctx: Any, name: str, lo: int, hi: int, default: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _draw_choice(ctx: Any, name: str, legal: Sequence[str], default: str) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, tuple(legal))
    return ctx.draw_choice(name, (default,))


def _shape_cells(shape: Shape, r0: int, c0: int) -> frozenset[Point]:
    return frozenset((r0 + dr, c0 + dc) for dr, dc in shape)


def _on_side(point: Point, orientation: str, axis: int, side: str) -> bool:
    r, c = point
    coordinate = c if orientation == "vertical" else r
    if side == "primary":
        return coordinate <= axis - 2
    return coordinate >= axis + 2


def _candidate_placements(
    h: int,
    w: int,
    orientation: str,
    axis: int,
    side: str,
    shapes: Sequence[Shape],
) -> list[tuple[frozenset[Point], frozenset[Point]]]:
    grid = full_grid(h, w, 0)
    candidates: list[tuple[frozenset[Point], frozenset[Point]]] = []
    seen: set[tuple[frozenset[Point], frozenset[Point]]] = set()
    for shape in shapes:
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h or sw > w:
            continue
        for r0 in range(h - sh + 1):
            for c0 in range(w - sw + 1):
                cells = _shape_cells(shape, r0, c0)
                if not all(_on_side(point, orientation, axis, side) for point in cells):
                    continue
                mirrors = frozenset(_mirror(point, orientation, axis) for point in cells)
                if not all(_in_bounds(grid, point) for point in mirrors):
                    continue
                orbit = cells | mirrors
                item = (cells, orbit)
                if item not in seen:
                    seen.add(item)
                    candidates.append(item)
    return candidates


def _adjacent(left: frozenset[Point], right: frozenset[Point]) -> bool:
    return any(
        (r + dr, c + dc) in right
        for r, c in left
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def _search_placements(
    specs: Sequence[tuple[str, int]],
    candidate_sets: dict[str, list[tuple[frozenset[Point], frozenset[Point]]]],
    rng: Any,
) -> list[tuple[frozenset[Point], int]] | None:
    """Tiny exhaustive backtracker: no capped retry can silently drop an object."""
    ordered: dict[str, list[tuple[frozenset[Point], frozenset[Point]]]] = {}
    for side in sorted(candidate_sets):
        candidates = candidate_sets[side]
        candidates = list(candidates)
        rng.shuffle(candidates)
        # Prefer richer shapes while retaining random layout within each size.
        candidates.sort(key=lambda item: len(item[0]), reverse=True)
        ordered[side] = candidates

    chosen: list[tuple[frozenset[Point], int]] = []
    occupied_orbits: set[Point] = set()
    occupied_sources: set[Point] = set()

    def visit(index: int) -> bool:
        if index == len(specs):
            return True
        side, color = specs[index]
        for cells, orbit in ordered[side]:
            if occupied_orbits.intersection(orbit):
                continue
            cell_set = frozenset(cells)
            if _adjacent(cell_set, frozenset(occupied_sources)):
                continue
            occupied_orbits.update(orbit)
            occupied_sources.update(cells)
            chosen.append((cells, color))
            if visit(index + 1):
                return True
            chosen.pop()
            occupied_sources.difference_update(cells)
            occupied_orbits.difference_update(orbit)
        return False

    return chosen[:] if visit(0) else None


def _object_specs(profile: str, colors: Sequence[int]) -> list[tuple[str, int]]:
    if profile == "primary_only":
        return [("primary", color) for color in colors]
    if profile == "secondary_only":
        return [("secondary", color) for color in colors]
    count = max(2, len(colors))
    return [
        ("primary" if index % 2 == 0 else "secondary", colors[index % len(colors)])
        for index in range(count)
    ]


def _shape_order(difficulty: Any) -> tuple[Shape, ...]:
    # Difficulty changes visual complexity only; it never narrows an AXES domain.
    if difficulty == "easy":
        preferred = tuple(shape for shape in _SHAPES if len(shape) <= 3)
    elif difficulty == "hard":
        preferred = _SHAPES
    else:
        preferred = tuple(shape for shape in _SHAPES if len(shape) <= 4)
    return preferred


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> Grid:
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor_h, anchor_w, anchor_orientation = _CANONICAL_PROFILES[
        (seed + sample_index) % len(_CANONICAL_PROFILES)
    ]
    h = _draw_int(ctx, "grid_h", 7, 10, anchor_h)
    w = _draw_int(ctx, "grid_w", 8, 10, anchor_w)
    orientation = _draw_choice(
        ctx,
        "axis_orientation",
        ("vertical", "horizontal"),
        anchor_orientation,
    )
    n_colors = _draw_int(ctx, "n_colors", 1, 3, 2)

    axis_limit = w if orientation == "vertical" else h
    legal_axes = tuple(range(3, axis_limit - 3))
    if not legal_axes:
        raise ValueError("chosen canvas cannot leave a one-cell gap on both sides of the axis")
    preferred_axis = _CANONICAL_AXIS.get((h, w, orientation))
    axis_options = legal_axes + ((preferred_axis,) * 3 if preferred_axis in legal_axes else ())
    axis = ctx.draw_choice("axis_position", axis_options)

    grid = full_grid(h, w, 0)
    if orientation == "vertical":
        for r in range(h):
            grid[r][axis] = 9
    else:
        for c in range(w):
            grid[axis][c] = 9

    colors = ctx.draw_distinct_colors("object_colors", n=n_colors, exclude={0, 9})
    profile = schedule_profile(seed, sample_index, difficulty)
    specs = _object_specs(profile, colors)
    shapes = _shape_order(difficulty)

    sides = sorted({side for side, _ in specs})
    candidate_sets = {
        side: _candidate_placements(h, w, orientation, axis, side, shapes)
        for side in sides
    }
    placements = _search_placements(specs, candidate_sets, ctx.draw_rng("object_layout"))
    if placements is None:
        # Constructive fallback, still exact and non-degenerate.  The fallback
        # is explicit rather than silently returning fewer objects.
        fallback_shapes = shapes + (_SINGLETON,)
        candidate_sets = {
            side: _candidate_placements(h, w, orientation, axis, side, fallback_shapes)
            for side in sides
        }
        placements = _search_placements(specs, candidate_sets, ctx.draw_rng("object_layout_fallback"))
    if placements is None:
        raise RuntimeError(
            f"no lawful placement for h={h}, w={w}, orientation={orientation}, "
            f"axis={axis}, profile={profile}, colors={n_colors}"
        )

    for cells, color in placements:
        for r, c in cells:
            if grid[r][c] != 0:
                raise RuntimeError("constructive placement collision")
            grid[r][c] = color

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError(f"generator constructed an invalid input: {findings}")
    return grid


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Recover every exact advertised axis from returned pixels."""
    orientation, _ = _find_axis(grid)
    colors = {value for row in grid for value in row if value not in (0, 9)}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "axis_orientation": orientation,
        "n_colors": len(colors),
    }


def _copy_from_side(grid: Grid, source_side: str) -> Grid:
    orientation, axis = _find_axis(grid)
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            coordinate = c if orientation == "vertical" else r
            side = "primary" if coordinate < axis else "secondary"
            if side != source_side:
                continue
            target = _mirror((r, c), orientation, axis)
            if _in_bounds(original, target):
                tr, tc = target
                output[tr][tc] = value
    return output


def _rival_primary_only(grid: Grid) -> Grid:
    """Canonical shortcut: only top/left cells are ever sources."""
    return _copy_from_side(grid, "primary")


def _occupied_sides(grid: Grid) -> set[str]:
    orientation, axis = _find_axis(grid)
    sides: set[str] = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            coordinate = c if orientation == "vertical" else r
            sides.add("primary" if coordinate < axis else "secondary")
    return sides


def _rival_empty_side_only(grid: Grid) -> Grid:
    """Shortcut: mirror only when one entire half is empty; otherwise do nothing."""
    sides = _occupied_sides(grid)
    if sides == {"primary"}:
        return _copy_from_side(grid, "primary")
    if sides == {"secondary"}:
        return _copy_from_side(grid, "secondary")
    return [row[:] for row in grid]


def _witness_secondary_source(grid: Grid) -> bool:
    try:
        return (
            not self_check(grid)
            and _occupied_sides(grid) == {"secondary"}
            and _rival_primary_only(grid) != _intended_output(grid)
        )
    except (TypeError, ValueError, IndexError):
        return False


def _witness_bilateral_source(grid: Grid) -> bool:
    try:
        return (
            not self_check(grid)
            and _occupied_sides(grid) == {"primary", "secondary"}
            and _rival_empty_side_only(grid) != _intended_output(grid)
        )
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "secondary_source": _witness_secondary_source,
    "bilateral_source": _witness_bilateral_source,
}
SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "primary_only_copy": _rival_primary_only,
    "empty_side_only_copy": _rival_empty_side_only,
}
WITNESS_RIVALS = {
    "secondary_source": ["primary_only_copy"],
    "bilateral_source": ["empty_side_only_copy"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Both rivals fit every canonical demonstration and are therefore the exact
# shortcuts that generated lessons must distinguish.
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Reject a lesson only when a declared rival survives and changes the query."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Grid]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        findings = self_check(demo["input"])
        if findings:
            reasons.append(f"demo {index} input is outside the rule domain: {findings}")
            continue
        expected = _intended_output(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with axis-reflection semantics")
            continue
        valid_demos.append(demo)

    query_findings = self_check(query["input"])
    if query_findings:
        reasons.append(f"query input is outside the rule domain: {query_findings}")
        return reasons
    query_answer = _intended_output(query["input"])

    for name, rival in LESSON_COMPETITORS.items():
        survives = bool(valid_demos) and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if survives and rival(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons
