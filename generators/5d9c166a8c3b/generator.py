"""Generator for ARC task 5d9c166a8c3b.

The input contains disconnected, same-colored foreground objects on black.
Objects are merged to a fixed point whenever their bounding boxes overlap in
row span *or* column span.  Each merged group's bounding box is then filled
red (2), but original foreground cells are preserved.

Generation deliberately cycles through row-only, column-only, and transitive
row+column links so the fixed-point part of the rule is observable.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d9c166a8c3b"
TASK_ID = "5d9c166a8c3b"
VERSION = "3.0.0"
RULE_HASH = "020d87daf483"

SUMMARY = (
    "A black grid contains one non-red foreground color split into disconnected "
    "objects. Merge object groups to a fixed point whenever their bounding boxes "
    "share any row or any column. For every final group, fill background cells "
    "inside its merged bounding box red (2), preserving all original objects. "
    "Generated lessons rotate through row links, column links, and a three-object "
    "row-then-column chain that requires transitive fixed-point merging."
)

INVARIANTS = [
    "all cells are ARC colors on a rectangular grid",
    "background is color 0",
    "exactly one foreground color is used and it is neither 0 nor 2",
    "at least two disconnected foreground objects are present",
    "the canonical fill changes at least one background cell",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng, at least the selected cluster layout",
        "valid": "7..24 (must fit cluster_count)",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng, at least the selected cluster layout",
        "valid": "7..24 (must fit cluster_count)",
    },
    "cluster_count": {
        "type": "int",
        "default": "difficulty-aware rng 1..4",
        "valid": "1..4",
    },
    "color": {
        "type": "color",
        "default": "rng excluding 0 and 2",
        "valid": "1|3|4|5|6|7|8|9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("row", "column", "transitive")


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_call_indices(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle every three consecutive samples through all semantic branches."""
    del seed
    _validate_difficulty(difficulty)
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % len(SCHEDULE_PROFILES)]


def _shape_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], 0, 0
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"], len(grid), 0
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if h > 30 or w > 30:
        errors.append(f"grid dimensions {h}x{w} exceed ARC's 30x30 limit")
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != w:
            errors.append("grid rows must be rectangular")
            break
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    return errors, h, w


def _paint(grid: list[list[int]], cells, color: int) -> None:
    for r, c in cells:
        grid[r][c] = color


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return 4-connected nonzero same-color components, matching `objects g 0`."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _row_overlap(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0])


def _column_overlap(a, b) -> bool:
    return not (a[3] < b[1] or b[3] < a[1])


def _row_or_column_overlap(a, b) -> bool:
    return _row_overlap(a, b) or _column_overlap(a, b)


def _merge_fixed(
    components: list[list[tuple[int, int]]],
    overlaps: Callable[[tuple[int, int, int, int], tuple[int, int, int, int]], bool],
) -> list[list[tuple[int, int]]]:
    """Merge any overlapping pair and recompute bboxes until stable."""
    groups = [list(cells) for cells in components]
    while True:
        found: tuple[int, int] | None = None
        for i in range(len(groups)):
            box_i = _bbox(groups[i])
            for j in range(i + 1, len(groups)):
                if overlaps(box_i, _bbox(groups[j])):
                    found = (i, j)
                    break
            if found is not None:
                break
        if found is None:
            return groups
        i, j = found
        merged = groups[i] + groups[j]
        groups = [group for k, group in enumerate(groups) if k not in (i, j)]
        groups.insert(0, merged)


def _fill_groups(
    grid: list[list[int]], groups: list[list[tuple[int, int]]]
) -> list[list[int]]:
    output = [row[:] for row in grid]
    for group in groups:
        r0, c0, r1, c1 = _bbox(group)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if grid[r][c] == 0:
                    output[r][c] = 2
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    errors, _, _ = _shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _components(grid)
    return _fill_groups(grid, _merge_fixed(components, _row_or_column_overlap))


def _analysis(grid: Any) -> dict[str, Any]:
    errors, h, w = _shape_errors(grid)
    if errors:
        return {"errors": errors, "grid_h": h, "grid_w": w}

    foreground = sorted({value for row in grid for value in row if value != 0})
    if not foreground:
        errors.append("input must contain foreground objects")
    if 2 in foreground:
        errors.append("input foreground must not use red 2, which is the fill color")
    if len(foreground) != 1:
        errors.append(f"expected exactly one foreground color, got {foreground}")

    components = _components(grid)
    if len(components) < 2:
        errors.append(f"expected at least two disconnected objects, got {len(components)}")
    groups = _merge_fixed(components, _row_or_column_overlap) if components else []
    if components and len(groups) == len(components):
        errors.append("no object bounding boxes overlap in row span or column span")

    if not errors and rule_mirror(grid) == grid:
        errors.append("canonical fill must change at least one background cell")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "components": components,
        "groups": groups,
        "color": foreground[0] if len(foreground) == 1 else None,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "cluster_count": len(analysis["groups"]),
        "color": analysis["color"],
    }


def _draw_cluster_count(ctx, difficulty) -> int:
    if ctx.overrides.get("cluster_count") is not None:
        return ctx.draw_int_strict("cluster_count", 1, 4)
    lo, hi = {
        None: (1, 4),
        "easy": (1, 2),
        "medium": (2, 3),
        "hard": (3, 4),
    }[difficulty]
    return ctx.draw_int_strict("cluster_count", lo, hi)


def _draw_dimension(ctx, label: str, required: int, difficulty) -> int:
    if ctx.overrides.get(label) is not None:
        value = ctx.draw_int_strict(label, 7, 24)
    else:
        lower, upper = {
            None: (7, 24),
            "easy": (7, 14),
            "medium": (10, 19),
            "hard": (15, 24),
        }[difficulty]
        value = ctx.draw_int_strict(label, max(lower, required), upper)
    if value < required:
        raise ValueError(
            f"{label}={value} cannot fit cluster_count={ctx.axis_value('cluster_count')} "
            f"(requires at least {required})"
        )
    return value


def _largest_profile_span(min_dimension: int, cluster_count: int) -> int:
    span = 1
    while True:
        candidate = span + 1
        thickness = max(1, candidate - 1)
        footprint = 2 * candidate + thickness
        if footprint + cluster_count - 1 > min_dimension:
            return span
        span = candidate


def _rectangle(r0: int, c0: int, height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r in range(r0, r0 + height)
        for c in range(c0, c0 + width)
    )


def _profile_components(
    profile: str, span: int
) -> tuple[tuple[tuple[tuple[int, int], ...], ...], int]:
    thickness = max(1, span - 1)
    gap = span
    offset = thickness + gap
    footprint = 2 * span + thickness

    if profile == "row":
        components = (
            _rectangle(0, 0, span, thickness),
            _rectangle(0, offset, span, thickness),
        )
    elif profile == "column":
        components = (
            _rectangle(0, 0, thickness, span),
            _rectangle(offset, 0, thickness, span),
        )
    elif profile == "transitive":
        components = (
            _rectangle(0, 0, span, thickness),
            _rectangle(0, offset, span, thickness),
            _rectangle(span + gap, offset, thickness, span),
        )
    else:
        raise ValueError(f"unknown schedule profile: {profile!r}")
    return components, footprint


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_indices(seed, sample_index)
    _validate_difficulty(difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    cluster_count = _draw_cluster_count(ctx, difficulty)
    # A span-1 witness occupies 3x3; every extra final group consumes one
    # diagonal row and column.  This keeps the full cluster-count domain valid
    # even on the minimum 7x7 grid.
    minimum_required = cluster_count + 2
    h = _draw_dimension(ctx, "grid_h", minimum_required, difficulty)
    w = _draw_dimension(ctx, "grid_w", minimum_required, difficulty)
    color = ctx.draw_color_strict("color", exclude={0, 2})

    profile = schedule_profile(seed, sample_index, difficulty)
    span = _largest_profile_span(min(h, w), cluster_count)
    components, footprint = _profile_components(profile, span)
    required = footprint + cluster_count - 1
    rng = ctx.draw_rng("layout")
    row0 = rng.randint(0, h - required)
    col0 = rng.randint(0, w - required)

    grid = full_grid(h, w, 0)
    for component in components:
        _paint(
            grid,
            ((row0 + dr, col0 + dc) for dr, dc in component),
            color,
        )
    for index in range(1, cluster_count):
        offset = footprint + index - 1
        grid[row0 + offset][col0 + offset] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid bbox lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed.get(axis) != requested.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return grid


def _rival_row_only(grid):
    return _fill_groups(grid, _merge_fixed(_components(grid), lambda a, b: _row_overlap(a, b)))


def _rival_column_only(grid):
    return _fill_groups(
        grid, _merge_fixed(_components(grid), lambda a, b: _column_overlap(a, b))
    )


def _rival_direct_pairs_only(grid):
    components = _components(grid)
    output = [row[:] for row in grid]
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            if not _row_or_column_overlap(_bbox(components[i]), _bbox(components[j])):
                continue
            pair_fill = _fill_groups(grid, [components[i] + components[j]])
            for r, row in enumerate(pair_fill):
                for c, value in enumerate(row):
                    if output[r][c] == 0 and value == 2:
                        output[r][c] = 2
    return output


SEMANTIC_RIVALS = {
    "row_only": _rival_row_only,
    "column_only": _rival_column_only,
    "direct_pairs_only": _rival_direct_pairs_only,
}


def _has_row_only_link(grid) -> bool:
    boxes = [_bbox(cells) for cells in _components(grid)]
    return any(
        _row_overlap(boxes[i], boxes[j]) and not _column_overlap(boxes[i], boxes[j])
        for i in range(len(boxes))
        for j in range(i + 1, len(boxes))
    )


def _has_column_only_link(grid) -> bool:
    boxes = [_bbox(cells) for cells in _components(grid)]
    return any(
        _column_overlap(boxes[i], boxes[j]) and not _row_overlap(boxes[i], boxes[j])
        for i in range(len(boxes))
        for j in range(i + 1, len(boxes))
    )


def _needs_fixed_point_transitivity(grid) -> bool:
    components = _components(grid)
    groups = _merge_fixed(components, _row_or_column_overlap)
    comp_sets = [set(cells) for cells in components]
    for group in groups:
        group_set = set(group)
        members = [index for index, cells in enumerate(comp_sets) if cells <= group_set]
        if len(members) < 3:
            continue
        for pos, i in enumerate(members):
            for j in members[pos + 1 :]:
                if not _row_or_column_overlap(_bbox(components[i]), _bbox(components[j])):
                    return True
    return False


SEMANTIC_WITNESSES = {
    "row_overlap": _has_row_only_link,
    "column_overlap": _has_column_only_link,
    "fixed_point_transitive": _needs_fixed_point_transitivity,
}

WITNESS_RIVALS = {
    "row_overlap": ["column_only"],
    "column_overlap": ["row_only"],
    "fixed_point_transitive": ["direct_pairs_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    errors: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            errors.append(f"demo {index} output does not match the canonical rule")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        errors.append("query must contain input and output")
    elif query["output"] != rule_mirror(query["input"]):
        errors.append("query output does not match the canonical rule")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            errors.append(f"demonstrations do not eliminate rival {name!r}")
    return errors
