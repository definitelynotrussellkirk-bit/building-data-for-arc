"""Generator for ARC task a5e17b975ae0 — fill keyed chambers.

Two hollow color-9 frames contain color-5 dividers.  One or two colored
single-cell keys identify which 4-connected chamber regions to flood.  The
selected Racket rule is authoritative; ``rule_mirror`` exists only for local
semantic contracts and regression tests.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a5e17b975ae0"
TASK_ID = "a5e17b975ae0"
VERSION = "3.0.0"
# Whitespace-normalized sha256[:12] of the selected canonical Racket rule.
RULE_HASH = "ced8e283e2c4"

SUMMARY = (
    "A 12..14 by 17..20 zero-background grid contains exactly two detached "
    "hollow color-9 rectangular frames. Color-5 dividers split frame "
    "interiors into chambers. One or two distinct non-{0,5,9} key cells sit "
    "in separate 4-connected open regions, while at least one region remains "
    "unkeyed. Flood each key through original 0/same-color cells, stopping at "
    "both color-5 and color-9 walls; leave all walls and unkeyed chambers "
    "unchanged."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0",
    "exactly two detached hollow color-9 rectangular frames",
    "all color-5 divider cells lie strictly inside a frame",
    "one or two distinct key colors, with at most one key per open region",
    "at least one keyed and one unkeyed open region",
]

SEED_PROFILES = ("single", "separate", "partitioned")
WALL_PROFILES = ("cross_gap", "dual_cross", "cross_tee")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-slot canonical-profile schedule",
        "valid": "12..14",
    },
    "grid_w": {
        "type": "int",
        "default": "five-slot canonical-profile schedule",
        "valid": "17..20",
    },
    "seed_profile": {
        "type": "enum",
        "default": "scheduled single|separate|partitioned",
        "valid": "single|separate|partitioned",
    },
    "wall_profile": {
        "type": "enum",
        "default": "scheduled cross_gap|dual_cross|cross_tee",
        "valid": "cross_gap|dual_cross|cross_tee",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Every five consecutive ordinary draws cover all five canonical
# (height, width, palette-size) profiles.  The names are also the public
# schedule-profile space consumed by the semantic gate.
_SCHEDULE = (
    ("p13x20_separate_gap", 13, 20, "separate", "cross_gap"),
    ("p12x18_partitioned_dual", 12, 18, "partitioned", "dual_cross"),
    ("p14x19_single_tee", 14, 19, "single", "cross_tee"),
    ("p12x17_separate_dual", 12, 17, "separate", "dual_cross"),
    ("p13x19_partitioned_gap", 13, 19, "partitioned", "cross_gap"),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _SCHEDULE)
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}
CANONICAL_PROFILES = {
    (12, 17, 5),
    (12, 18, 5),
    (13, 19, 5),
    (13, 20, 5),
    (14, 19, 4),
}
_KEY_COLORS = (1, 2, 3, 4, 6, 7, 8)
_ALLOWED_COLORS = {0, 5, 9, *_KEY_COLORS}


def _schedule_index(sample_index: int, difficulty: str | None) -> int:
    if difficulty not in _BAND_OFFSETS:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    return (sample_index + _BAND_OFFSETS[difficulty]) % len(_SCHEDULE)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic, band-rotated five-slot curriculum."""
    del seed
    return SCHEDULE_PROFILES[_schedule_index(sample_index, difficulty)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name, lo, hi in (("grid_h", 12, 14), ("grid_w", 17, 20)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"override {name} must be an integer, got {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"override {name} must be in {lo}..{hi}, got {value}")

    for name, options in (
        ("seed_profile", SEED_PROFILES),
        ("wall_profile", WALL_PROFILES),
    ):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if value not in options:
                raise ValueError(
                    f"override {name} must be one of {options}, got {value!r}"
                )


def _scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _scheduled_choice(
    ctx, name: str, options: tuple[str, ...], scheduled: str
) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for point in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def _frame_boxes(grid: list[list[int]]) -> tuple[list[tuple[int, int, int, int]], list[str]]:
    nine_cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    }
    errors: list[str] = []
    boxes: list[tuple[int, int, int, int]] = []
    for component in _components(nine_cells):
        r0 = min(row for row, _ in component)
        r1 = max(row for row, _ in component)
        c0 = min(col for _, col in component)
        c1 = max(col for _, col in component)
        border = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if row in (r0, r1) or col in (c0, c1)
        }
        if component != border:
            errors.append(
                f"color-9 component at rows {r0}..{r1}, cols {c0}..{c1} "
                "is not one complete hollow rectangle"
            )
        boxes.append((r0, c0, r1, c1))
    return sorted(boxes, key=lambda box: (box[1], box[0])), errors


def _inside(box: tuple[int, int, int, int], row: int, col: int) -> bool:
    r0, c0, r1, c1 = box
    return r0 < row < r1 and c0 < col < c1


def _open_regions(
    grid: list[list[int]], box: tuple[int, int, int, int]
) -> list[set[tuple[int, int]]]:
    r0, c0, r1, c1 = box
    cells = {
        (row, col)
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
        if grid[row][col] not in (5, 9)
    }
    return _components(cells)


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {}, ["every row must be a non-empty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid is not rectangular"]
    height = len(grid)
    if not 12 <= height <= 14:
        errors.append(f"grid height must be 12..14, got {height}")
    if not 17 <= width <= 20:
        errors.append(f"grid width must be 17..20, got {width}")

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"cell ({row},{col}) is not an integer ARC color")
            elif value not in _ALLOWED_COLORS:
                errors.append(f"cell ({row},{col}) has unsupported color {value}")

    boxes, frame_errors = _frame_boxes(grid)
    errors.extend(frame_errors)
    if len(boxes) != 2:
        errors.append(f"expected exactly two color-9 frames, got {len(boxes)}")
    for index, (r0, c0, r1, c1) in enumerate(boxes):
        if r0 < 1 or c0 < 1 or r1 >= height - 1 or c1 >= width - 1:
            errors.append(f"frame {index} must have at least one outer zero margin")
        if r1 - r0 + 1 < 6 or c1 - c0 + 1 < 6:
            errors.append(f"frame {index} is too small for nontrivial chambers")

    # Do not continue geometry analysis against malformed/partial frame sets.
    if frame_errors or len(boxes) != 2:
        return {
            "height": height,
            "width": width,
            "boxes": boxes,
            "palette_size": len({value for row in grid for value in row}),
        }, errors

    # Frames may not overlap or touch orthogonally; every non-background role
    # cell must be owned by exactly one frame interior/border.
    first, second = boxes
    if not (first[3] + 1 < second[1] or second[3] + 1 < first[1]):
        errors.append("the two frames must be horizontally detached by a zero gap")

    five_cells: list[tuple[int, int]] = []
    seeds: list[tuple[int, int, int]] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 5:
                five_cells.append((row, col))
                owners = [index for index, box in enumerate(boxes) if _inside(box, row, col)]
                if len(owners) != 1:
                    errors.append(
                        f"color-5 divider at ({row},{col}) is not strictly inside one frame"
                    )
            elif value not in (0, 9):
                seeds.append((row, col, value))
                owners = [index for index, box in enumerate(boxes) if _inside(box, row, col)]
                if len(owners) != 1:
                    errors.append(f"key at ({row},{col}) is not strictly inside one frame")

    if not five_cells:
        errors.append("expected color-5 chamber dividers")
    for index, box in enumerate(boxes):
        if not any(_inside(box, row, col) for row, col in five_cells):
            errors.append(f"frame {index} has no internal color-5 divider")

    if not 1 <= len(seeds) <= 2:
        errors.append(f"expected one or two key cells, got {len(seeds)}")
    seed_colors = [value for _, _, value in seeds]
    if len(seed_colors) != len(set(seed_colors)):
        errors.append("key colors must be distinct")

    region_records: list[dict[str, Any]] = []
    seed_locations: list[tuple[int, int]] = []
    for frame_index, box in enumerate(boxes):
        regions = _open_regions(grid, box)
        if len(regions) < 2:
            # Canonical examples sometimes leave one frame connected, but at
            # least one of the pair must contain a real chamber partition.
            pass
        for region_index, region in enumerate(regions):
            region_seeds = [
                (row, col, grid[row][col])
                for row, col in region
                if grid[row][col] not in (0, 5, 9)
            ]
            if len(region_seeds) > 1:
                errors.append(
                    f"frame {frame_index} region {region_index} contains "
                    f"{len(region_seeds)} keys"
                )
            if region_seeds and not any(grid[row][col] == 0 for row, col in region):
                errors.append(
                    f"frame {frame_index} region {region_index} has no fillable zero"
                )
            for row, col, _ in region_seeds:
                seed_locations.append((frame_index, region_index))
            region_records.append(
                {
                    "frame": frame_index,
                    "region": region_index,
                    "cells": region,
                    "seed_count": len(region_seeds),
                }
            )

    if len(seed_locations) != len(seeds):
        errors.append("one or more keys are not part of an open frame region")
    counts = [record["seed_count"] for record in region_records]
    if counts and 1 not in counts:
        errors.append("no keyed open region")
    if counts and 0 not in counts:
        errors.append("no intentionally unkeyed open region")
    if not any(
        len(_open_regions(grid, box)) >= 2
        for box in boxes
    ):
        errors.append("color-5 dividers do not partition either frame")

    facts = {
        "height": height,
        "width": width,
        "boxes": boxes,
        "five_cells": five_cells,
        "seeds": seeds,
        "seed_locations": seed_locations,
        "regions": region_records,
        "palette_size": len({value for row in grid for value in row}),
    }
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete observable grammar and requested exact axes."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and not errors and requested:
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if expected is not None and name in observed and observed[name] != expected:
                errors.append(
                    f"override {name} requested {expected!r}, observed {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the linked canonical manifold and the scheduled production set."""
    facts, errors = _analyze(grid)
    if errors:
        return errors
    profile = (facts["height"], facts["width"], facts["palette_size"])
    if profile not in CANONICAL_PROFILES:
        return [f"profile {profile} is outside the five linked canonical profiles"]
    return []


def _draw_frame(
    grid: list[list[int]], box: tuple[int, int, int, int]
) -> None:
    r0, c0, r1, c1 = box
    for col in range(c0, c1 + 1):
        grid[r0][col] = 9
        grid[r1][col] = 9
    for row in range(r0, r1 + 1):
        grid[row][c0] = 9
        grid[row][c1] = 9


def _draw_dual_cross(
    grid: list[list[int]], box: tuple[int, int, int, int], row: int, col: int
) -> None:
    r0, c0, r1, c1 = box
    for current_col in range(c0 + 1, c1):
        grid[row][current_col] = 5
    for current_row in range(r0 + 1, r1):
        grid[current_row][col] = 5


def _draw_right_walls(
    grid: list[list[int]], box: tuple[int, int, int, int], profile: str, rng
) -> None:
    r0, c0, r1, c1 = box
    rows = list(range(r0 + 2, r1 - 1)) or list(range(r0 + 1, r1))
    cols = list(range(c0 + 2, c1 - 1)) or list(range(c0 + 1, c1))
    cross_row = rng.choice(rows)
    cross_col = rng.choice(cols)

    if profile == "dual_cross":
        _draw_dual_cross(grid, box, cross_row, cross_col)
        return
    if profile == "cross_gap":
        # Full horizontal wall plus a vertical wall with a one-cell gap below
        # the intersection: three/four real regions, but no full 5-column.
        for col in range(c0 + 1, c1):
            grid[cross_row][col] = 5
        gap_row = min(r1 - 1, cross_row + 1)
        for row in range(r0 + 1, r1):
            if row != gap_row:
                grid[row][cross_col] = 5
        return
    if profile == "cross_tee":
        # Full vertical wall plus a one-sided horizontal arm: no full 5-row.
        for row in range(r0 + 1, r1):
            grid[row][cross_col] = 5
        for col in range(c0 + 1, cross_col + 1):
            grid[cross_row][col] = 5
        return
    raise ValueError(f"unknown wall profile: {profile!r}")


def _pick_seed_cell(region: set[tuple[int, int]], rng) -> tuple[int, int]:
    candidates = sorted(region)
    # Prefer a non-wall-adjacent-ish point when the component has room, but
    # retain every component as a valid source of teaching variation.
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile_name, default_h, default_w, default_seed, default_wall = _SCHEDULE[
        _schedule_index(sample_index, difficulty)
    ]
    del profile_name
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, "grid_h", 12, 14, default_h)
    width = _scheduled_int(ctx, "grid_w", 17, 20, default_w)
    seed_profile = _scheduled_choice(
        ctx, "seed_profile", SEED_PROFILES, default_seed
    )
    wall_profile = _scheduled_choice(
        ctx, "wall_profile", WALL_PROFILES, default_wall
    )

    grid = full_grid(height, width, 0)
    layout_rng = ctx.draw_rng("layout")

    left_width = 7 + int(width >= 19)
    right_width = width - 4 - left_width
    left_height = min(10, height - 3)
    right_height = min(10, height - 3)
    left_top = 1 + layout_rng.randrange(max(1, height - left_height - 1))
    right_top = 1 + layout_rng.randrange(max(1, height - right_height - 1))
    left = (left_top, 1, left_top + left_height - 1, left_width)
    right_col0 = left_width + 3
    right = (
        right_top,
        right_col0,
        right_top + right_height - 1,
        right_col0 + right_width - 1,
    )
    _draw_frame(grid, left)
    _draw_frame(grid, right)

    # A true four-way divider in the left frame guarantees enough distinct
    # regions for every seed profile and for an unkeyed counterexample region.
    lr0, lc0, lr1, lc1 = left
    left_row = layout_rng.choice(list(range(lr0 + 2, lr1 - 1)))
    left_col = layout_rng.choice(list(range(lc0 + 2, lc1 - 1)))
    _draw_dual_cross(grid, left, left_row, left_col)
    _draw_right_walls(grid, right, wall_profile, layout_rng)

    left_regions = [region for region in _open_regions(grid, left) if len(region) >= 2]
    right_regions = [region for region in _open_regions(grid, right) if len(region) >= 2]
    if len(left_regions) < 2 or not right_regions:
        raise RuntimeError("internal layout failed to create seedable chambers")

    if seed_profile == "single":
        targets = [(0, layout_rng.choice(left_regions))]
    elif seed_profile == "separate":
        targets = [
            (0, layout_rng.choice(left_regions)),
            (1, layout_rng.choice(right_regions)),
        ]
    elif seed_profile == "partitioned":
        chosen = layout_rng.sample(left_regions, 2)
        targets = [(0, chosen[0]), (0, chosen[1])]
    else:  # defensive; _validate_call and draw_choice already reject this.
        raise ValueError(f"unknown seed profile: {seed_profile!r}")

    color_rng = ctx.draw_rng("key_colors")
    colors = color_rng.sample(list(_KEY_COLORS), len(targets))
    for (_, region), color in zip(targets, colors):
        row, col = _pick_seed_cell(region, layout_rng)
        grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid chamber puzzle: " + "; ".join(errors))
    return grid


def _classify_wall_profile(
    grid: list[list[int]], box: tuple[int, int, int, int]
) -> str:
    r0, c0, r1, c1 = box
    full_rows = [
        row
        for row in range(r0 + 1, r1)
        if all(grid[row][col] == 5 for col in range(c0 + 1, c1))
    ]
    full_cols = [
        col
        for col in range(c0 + 1, c1)
        if all(grid[row][col] == 5 for row in range(r0 + 1, r1))
    ]
    if full_rows and full_cols:
        return "dual_cross"
    if full_rows and not full_cols:
        return "cross_gap"
    if full_cols and not full_rows:
        return "cross_tee"
    raise ValueError("right-frame divider does not encode a known wall profile")


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every public exact control from returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    seeds = facts["seeds"]
    locations = facts["seed_locations"]
    if len(seeds) == 1:
        seed_profile = "single"
    elif len({frame for frame, _ in locations}) == 2:
        seed_profile = "separate"
    else:
        seed_profile = "partitioned"
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "seed_profile": seed_profile,
        "wall_profile": _classify_wall_profile(grid, facts["boxes"][1]),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected row-major keyed flood rule."""
    original = [list(row) for row in grid]
    output = deepcopy(original)
    height, width = len(original), len(original[0])
    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] not in (0, 5, 9)
    ]
    for start_row, start_col in seeds:
        color = original[start_row][start_col]
        queue = deque([(start_row, start_col)])
        seen = {(start_row, start_col)}
        while queue:
            row, col = queue.popleft()
            output[row][col] = color
            for next_row, next_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                if (next_row, next_col) in seen:
                    continue
                value = original[next_row][next_col]
                if value in (5, 9) or value not in (0, color):
                    continue
                seen.add((next_row, next_col))
                queue.append((next_row, next_col))
    return output


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_ignore_color5(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: treat 5 as traversable/fillable and only 9 as a wall."""
    original = [list(row) for row in grid]
    output = deepcopy(original)
    height, width = len(original), len(original[0])
    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] not in (0, 5, 9)
    ]
    for start_row, start_col in seeds:
        color = original[start_row][start_col]
        queue = deque([(start_row, start_col)])
        seen = {(start_row, start_col)}
        while queue:
            row, col = queue.popleft()
            output[row][col] = color
            for next_row, next_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                if (next_row, next_col) in seen:
                    continue
                value = original[next_row][next_col]
                if value == 9 or value not in (0, 5, color):
                    continue
                seen.add((next_row, next_col))
                queue.append((next_row, next_col))
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "ignore_color5": _rival_ignore_color5,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def _valid(grid) -> bool:
    return self_check(grid) == []


def _witness_fillable_region(grid) -> bool:
    return _valid(grid) and rule_mirror(grid) != _rival_identity(grid)


def _witness_five_wall_partition(grid) -> bool:
    return _valid(grid) and rule_mirror(grid) != _rival_ignore_color5(grid)


SEMANTIC_WITNESSES = {
    "fillable_region": _witness_fillable_region,
    "five_wall_partition": _witness_five_wall_partition,
}
WITNESS_RIVALS = {
    "fillable_region": ["identity"],
    "five_wall_partition": ["ignore_color5"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared wrong rule that survives every demonstration."""
    query_grid = query["input"] if isinstance(query, dict) else query
    target = rule_mirror(query_grid)
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query_grid) != target:
                reasons.append(f"{name} fits every demo but changes the query answer")
    return reasons
