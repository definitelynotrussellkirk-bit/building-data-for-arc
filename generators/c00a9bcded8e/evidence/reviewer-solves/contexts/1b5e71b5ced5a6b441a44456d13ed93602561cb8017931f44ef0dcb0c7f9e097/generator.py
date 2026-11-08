"""Generator for ARC task 0a1d4ef5 / content hash c00a9bcded8e.

The input is a 30x30 zero-background grid containing two, three, or four
spatial rows of three solid colored rectangles.  Two other colors form dense
small-component noise.  The output is the rectangle colors in spatial
row-major order, one output row per rectangle row.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "c00a9bcded8e"
VERSION = "2.2.0"
TASK_ID = "c00a9bcded8e"
# Pinned to the comment-preserving selected canonical rule shipped with this
# candidate.  The pin is whitespace-normalized sha256[:12].
RULE_HASH = "4732b1c1a64d"

SUMMARY = (
    "A 30x30 zero-background grid contains 2..4 spatial rows of exactly three "
    "spatially varied solid 3..8-cell-side colored rectangles using a "
    "canonical-scale target palette, plus dense two-color small-object noise "
    "whose colors are absent from the rectangles. Return the rectangle "
    "colors as an n-by-3 table in spatial row-major order."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "the input is a 30x30 ARC grid with background color 0",
    "there are 2..4 spatial rows of exactly three solid rectangles",
    "every target rectangle has area at least nine and side lengths 3..8",
    "five or six target colors are used across the rectangles",
    "the two noise colors are disjoint from all rectangle colors",
    "the output has one row per rectangle row and three columns",
]

SIZE_PROFILES = ("uniform", "mixed")
COLOR_PATTERNS = ("column_repeat", "row_repeat", "mixed")

AXES = {
    "n_rect_rows": {
        "type": "int",
        "default": "scheduled 2,3,4",
        "valid": "2..4",
    },
    "size_profile": {
        "type": "enum",
        "default": "scheduled mixed,uniform,mixed",
        "valid": "uniform|mixed",
    },
    "color_pattern": {
        "type": "enum",
        "default": "scheduled column_repeat,row_repeat,mixed",
        "valid": "column_repeat|row_repeat|mixed",
    },
    "noise_count": {
        "type": "int",
        "default": "difficulty- and slot-scheduled",
        "valid": "260..370",
    },
}

SCHEDULE_PROFILES = ("two_column", "three_row", "four_mixed")


def _validate_request_scalars(seed: Any, sample_index: Any) -> None:
    """Reject coercible request scalars before they reach GenCtx or modulo."""
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, got {seed!r}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be a nonnegative integer, got {sample_index!r}"
        )
    if sample_index < 0:
        raise ValueError(
            f"sample_index must be a nonnegative integer, got {sample_index!r}"
        )


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the three-slot sliding-window teaching schedule."""
    _validate_request_scalars(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[sample_index % 3]


def _validate_call(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> str:
    _validate_request_scalars(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name in ("n_rect_rows", "noise_count"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"override {name} must be an integer, got {value!r}")
    if "n_rect_rows" in overrides and overrides["n_rect_rows"] is not None:
        if not 2 <= overrides["n_rect_rows"] <= 4:
            raise ValueError("override n_rect_rows must be in 2..4")
    if "noise_count" in overrides and overrides["noise_count"] is not None:
        if not 260 <= overrides["noise_count"] <= 370:
            raise ValueError("override noise_count must be in 260..370")
    if "size_profile" in overrides and overrides["size_profile"] is not None:
        if overrides["size_profile"] not in SIZE_PROFILES:
            raise ValueError(
                f"override size_profile must be one of {SIZE_PROFILES}, "
                f"got {overrides['size_profile']!r}"
            )
    if "color_pattern" in overrides and overrides["color_pattern"] is not None:
        if overrides["color_pattern"] not in COLOR_PATTERNS:
            raise ValueError(
                f"override color_pattern must be one of {COLOR_PATTERNS}, "
                f"got {overrides['color_pattern']!r}"
            )
    return "medium" if difficulty is None else difficulty


def _scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _scheduled_choice(ctx, name: str, options: tuple[str, ...], scheduled: str) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return same-color 4-connected non-background components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
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
            rows = [r for r, _c in cells]
            cols = [c for _r, c in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            box_h, box_w = bottom - top + 1, right - left + 1
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "top": top,
                    "left": left,
                    "bottom": bottom,
                    "right": right,
                    "h": box_h,
                    "w": box_w,
                    "area": box_h * box_w,
                    "density": len(cells) / (box_h * box_w),
                    "center_r": (top + bottom) / 2,
                    "center_c": (left + right) / 2,
                }
            )
    return result


def _classify_color_pattern(output: list[list[int]]) -> str:
    """Recover the deliberately observable five-color teaching pattern."""
    if not output or any(len(row) != 3 for row in output):
        return "invalid"
    if (
        len(output) >= 2
        and output[0][0] == output[1][0]
        and all(row[0] != row[2] for row in output)
    ):
        return "column_repeat"
    if any(row[0] == row[2] for row in output):
        return "row_repeat"
    return "mixed"


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    """Analyze the complete teaching grammar and mirror the oracle grouping."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return {}, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {}, ["grid values must be integer ARC colors 0..9"]

    height = len(grid)
    if (height, width) != (30, 30):
        errors.append(f"expected a 30x30 canonical canvas, got {height}x{width}")

    components = _components(grid)
    rects = [
        component
        for component in components
        if component["size"] >= 9 and component["density"] >= 0.9
    ]
    rects.sort(key=lambda component: component["center_r"])

    row_groups: list[list[dict[str, Any]]] = []
    last_row: float | None = None
    for rectangle in rects:
        if last_row is None or rectangle["center_r"] - last_row < 4:
            if not row_groups:
                row_groups.append([])
            row_groups[-1].append(rectangle)
        else:
            row_groups.append([rectangle])
        last_row = rectangle["center_r"]
    for group in row_groups:
        group.sort(key=lambda component: component["center_c"])

    if len(row_groups) not in (2, 3, 4):
        errors.append(f"expected 2..4 rectangle rows, got {len(row_groups)}")
    if any(len(group) != 3 for group in row_groups):
        errors.append(
            "every rectangle row must contain exactly three targets; got "
            + repr([len(group) for group in row_groups])
        )

    for index, rectangle in enumerate(rects):
        if rectangle["size"] != rectangle["area"]:
            errors.append(f"target rectangle {index} is not solid")
        if not (3 <= rectangle["h"] <= 8 and 3 <= rectangle["w"] <= 8):
            errors.append(
                f"target rectangle {index} has unsupported bbox "
                f"{rectangle['h']}x{rectangle['w']}"
            )
    for row_index, group in enumerate(row_groups):
        centers = [rectangle["center_c"] for rectangle in group]
        if any(right <= left for left, right in zip(centers, centers[1:])):
            errors.append(f"rectangle row {row_index} is not strictly left-to-right")

    target_cells = {
        cell for rectangle in rects for cell in rectangle["cells"]
    }
    target_colors = {rectangle["color"] for rectangle in rects}
    noise_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0 and (row, col) not in target_cells
    ]
    noise_colors = {grid[row][col] for row, col in noise_cells}
    if len(noise_colors) != 2:
        errors.append(f"expected exactly two noise colors, got {sorted(noise_colors)}")
    if len(target_colors) not in (5, 6):
        errors.append(
            "expected five or six target colors, got "
            f"{sorted(target_colors)}"
        )
    overlap = target_colors & noise_colors
    if overlap:
        errors.append(f"noise colors overlap target colors: {sorted(overlap)}")

    output = [[rectangle["color"] for rectangle in group] for group in row_groups]
    size_profile = (
        "uniform"
        if rects and len({(rectangle["h"], rectangle["w"]) for rectangle in rects}) == 1
        else "mixed"
    )
    facts = {
        "height": height,
        "width": width,
        "components": components,
        "rects": rects,
        "row_groups": row_groups,
        "n_rect_rows": len(row_groups),
        "noise_count": len(noise_cells),
        "noise_colors": noise_colors,
        "target_colors": target_colors,
        "output": output,
        "size_profile": size_profile,
        "color_pattern": _classify_color_pattern(output),
    }
    return facts, errors


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every exact declared axis from returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "n_rect_rows": int(facts["n_rect_rows"]),
        "size_profile": str(facts["size_profile"]),
        "color_pattern": str(facts["color_pattern"]),
        "noise_count": int(facts["noise_count"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate target geometry, grouping, palette roles, and exact overrides."""
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
            if name in observed and expected is not None and observed[name] != expected:
                errors.append(
                    f"override {name} requested {expected!r}, "
                    f"observed {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked official manifold, including its dense noise."""
    facts, errors = _analyze(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if not 250 <= facts["noise_count"] <= 380:
        reasons.append(
            f"canonical noise support is 250..380 cells, got {facts['noise_count']}"
        )
    if any(rectangle["area"] < 9 or rectangle["area"] > 56 for rectangle in facts["rects"]):
        reasons.append("canonical target rectangle areas are in 9..56")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for tests; Racket remains the authority."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [row[:] for row in facts["output"]]


def _rival_sorted_colors(grid: list[list[int]]) -> list[list[int]]:
    return [sorted(row) for row in rule_mirror(grid)]


def _rival_frequency_echo(grid: list[list[int]]) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = Counter(value for row in grid for value in row if value != 0)
    top = [color for color, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3]]
    while len(top) < 3:
        top.append(top[-1] if top else 1)
    return [top[:] for _ in range(facts["n_rect_rows"])]


def _rival_fixed_two_rows(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    return [row[:] for row in output[:2]]


def _rival_column_major(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    n_rows = len(output)
    flattened = [output[row][col] for col in range(3) for row in range(n_rows)]
    return [flattened[index:index + 3] for index in range(0, len(flattened), 3)]


def _rival_fixed_anchor(grid: list[list[int]]) -> list[list[int]]:
    """Read the rectangle colors from the pre-v2.1 fixed top-left anchors."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    row_starts = {
        2: (4, 20),
        3: (2, 12, 22),
        4: (1, 8, 15, 22),
    }[facts["n_rect_rows"]]
    return [[grid[row][col] for col in (2, 12, 22)] for row in row_starts]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "sorted_colors": _rival_sorted_colors,
    "frequency_echo": _rival_frequency_echo,
    "fixed_two_rows": _rival_fixed_two_rows,
    "column_major": _rival_column_major,
    "fixed_anchor": _rival_fixed_anchor,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# These named competitors are useful teaching rivals but none reproduces every
# canonical pair, so none is truthfully a canonical shortcut.
CANONICAL_SHORTCUTS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {}


def _facts_or_none(grid):
    facts, errors = _analyze(grid)
    return None if errors else facts


def _witness_rows(expected: int):
    return lambda grid: (
        (facts := _facts_or_none(grid)) is not None
        and facts["n_rect_rows"] == expected
    )


def _witness_profile(expected: str):
    return lambda grid: (
        (facts := _facts_or_none(grid)) is not None
        and facts["size_profile"] == expected
    )


def _witness_rival(name: str):
    return lambda grid: rule_mirror(grid) != SEMANTIC_RIVALS[name](grid)


SEMANTIC_WITNESSES = {
    "spatial_order_refutes_sorted_colors": _witness_rival("sorted_colors"),
    "noise_refutes_frequency_echo": _witness_rival("frequency_echo"),
    "variable_height_refutes_fixed_two_rows": _witness_rival("fixed_two_rows"),
    "row_major_refutes_column_major": _witness_rival("column_major"),
    "variable_placement_refutes_fixed_anchor": _witness_rival("fixed_anchor"),
}

WITNESS_RIVALS = {
    "spatial_order_refutes_sorted_colors": ["sorted_colors"],
    "noise_refutes_frequency_echo": ["frequency_echo"],
    "variable_height_refutes_fixed_two_rows": ["fixed_two_rows"],
    "row_major_refutes_column_major": ["column_major"],
    "variable_placement_refutes_fixed_anchor": ["fixed_anchor"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any three-demo lesson still compatible with named shortcuts."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    demo_facts: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not isinstance(pair.get("input"), list):
            reasons.append(f"demonstration {index} is missing an input grid")
            continue
        facts, errors = _analyze(pair["input"])
        if errors:
            reasons.append(f"demonstration {index} violates the grammar: {'; '.join(errors)}")
            continue
        if pair.get("output") != facts["output"]:
            reasons.append(f"demonstration {index} output disagrees with row-major extraction")
        demo_facts.append(facts)
    if reasons:
        return reasons

    if {facts["n_rect_rows"] for facts in demo_facts} != {2, 3, 4}:
        reasons.append("demonstrations do not establish variable 2/3/4-row outputs")
    if {facts["size_profile"] for facts in demo_facts} != {"uniform", "mixed"}:
        reasons.append("demonstrations do not vary rectangle size profile")
    if {facts["color_pattern"] for facts in demo_facts} != set(COLOR_PATTERNS):
        reasons.append("demonstrations do not cover all three target-color patterns")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or not isinstance(query.get("input"), list):
        reasons.append("query is missing an input grid")
    else:
        query_facts, query_errors = _analyze(query["input"])
        if query_errors:
            reasons.append("query violates the teaching grammar: " + "; ".join(query_errors))
        elif query.get("output") is not None and query["output"] != query_facts["output"]:
            reasons.append("query output disagrees with row-major extraction")
    return reasons


def _rectangle_sizes(ctx, n_rows: int, size_profile: str) -> list[list[tuple[int, int]]]:
    """Draw canonical-scale sizes that still fit separated spatial rows."""
    rng = ctx.draw_rng("rectangle_sizes")
    max_height = {2: 7, 3: 6, 4: 5}[n_rows]
    if size_profile == "uniform":
        bands = {
            "easy": (3, min(4, max_height), 3, 5),
            "medium": (4, min(5, max_height), 4, 7),
            "hard": (max(3, max_height - 1), max_height, 6, 8),
        }
        h_lo, h_hi, w_lo, w_hi = bands.get(ctx.difficulty, bands["medium"])
        size = (rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi))
        return [[size for _ in range(3)] for _ in range(n_rows)]

    height_span = max_height - 2  # values 3..max_height
    offset_h = rng.randrange(height_span)
    offset_w = rng.randrange(6)   # values 3..8
    sizes = [
        [
            (
                3 + ((2 * row + col + offset_h) % height_span),
                3 + ((row + 2 * col + offset_w) % 6),
            )
            for col in range(3)
        ]
        for row in range(n_rows)
    ]
    if len({size for row in sizes for size in row}) == 1:
        sizes[-1][-1] = (max_height, 8)
    return sizes


def _allocate_slack(rng, total: int, slots: int) -> list[int]:
    """Randomly distribute integer slack without changing total extent."""
    parts = [0] * slots
    for _ in range(total):
        parts[rng.randrange(slots)] += 1
    return parts


def _rectangle_positions(
    ctx, sizes: list[list[tuple[int, int]]]
) -> list[list[tuple[int, int]]]:
    """Place rows and columns with deterministic jitter and blank separation."""
    rng = ctx.draw_rng("rectangle_positions")
    n_rows = len(sizes)
    row_heights = [max(height for height, _width in row) for row in sizes]
    vertical_free = 30 - sum(row_heights) - (n_rows - 1)
    if vertical_free < 0:
        raise ValueError("rectangle rows do not fit the 30-cell canvas")
    vertical_spaces = _allocate_slack(rng, vertical_free, n_rows + 1)

    band_tops: list[int] = []
    cursor = vertical_spaces[0]
    for row_index, row_height in enumerate(row_heights):
        band_tops.append(cursor)
        cursor += row_height
        if row_index < n_rows - 1:
            cursor += 1 + vertical_spaces[row_index + 1]

    result: list[list[tuple[int, int]]] = []
    for row_index, row_sizes in enumerate(sizes):
        row_height = row_heights[row_index]
        widths = [width for _height, width in row_sizes]
        horizontal_free = 30 - sum(widths) - 2
        if horizontal_free < 0:
            raise ValueError("rectangle columns do not fit the 30-cell canvas")
        horizontal_spaces = _allocate_slack(rng, horizontal_free, 4)
        lefts: list[int] = []
        col_cursor = horizontal_spaces[0]
        for col_index, width in enumerate(widths):
            lefts.append(col_cursor)
            col_cursor += width
            if col_index < 2:
                col_cursor += 1 + horizontal_spaces[col_index + 1]

        positions: list[tuple[int, int]] = []
        for (height, _width), left in zip(row_sizes, lefts):
            top = band_tops[row_index] + rng.randint(0, row_height - height)
            positions.append((top, left))
        result.append(positions)
    return result


def _target_color_table(
    ctx, n_rows: int, pattern: str, target_palette: list[int]
) -> list[list[int]]:
    """Build an observable pattern while matching canonical five-color roles."""
    rng = ctx.draw_rng("target_color_table")
    palette = target_palette[:]
    rng.shuffle(palette)
    a, b, c, d, e = palette[:5]

    # Each prefix for n_rows in 2..4 uses exactly five colors.  The three
    # templates remain distinguishable from pixels alone: column_repeat repeats
    # the first-column value across the first two rows; row_repeat mirrors the
    # first row's endpoints; mixed does neither.
    templates = {
        "column_repeat": (
            [a, b, c],
            [a, d, e],
            [b, e, d],
            [c, a, b],
        ),
        "row_repeat": (
            [a, b, a],
            [c, d, e],
            [b, c, d],
            [e, a, c],
        ),
        "mixed": (
            [a, b, c],
            [d, e, a],
            [b, c, d],
            [e, a, b],
        ),
    }
    return [row[:] for row in templates[pattern][:n_rows]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    slot = sample_index % 3
    n_rows = _scheduled_int(ctx, "n_rect_rows", 2, 4, (2, 3, 4)[slot])
    size_profile = _scheduled_choice(
        ctx, "size_profile", SIZE_PROFILES, ("mixed", "uniform", "mixed")[slot]
    )
    color_pattern = _scheduled_choice(
        ctx,
        "color_pattern",
        COLOR_PATTERNS,
        ("column_repeat", "row_repeat", "mixed")[slot],
    )
    noise_schedules = {
        "easy": (260, 285, 310),
        "medium": (290, 325, 350),
        "hard": (320, 350, 370),
    }
    noise_count = _scheduled_int(
        ctx, "noise_count", 260, 370, noise_schedules[band][slot]
    )

    palette_rng = ctx.draw_rng("palette")
    noise_colors = palette_rng.sample(list(range(1, 10)), 2)
    target_palette = [color for color in range(1, 10) if color not in noise_colors]
    sizes = _rectangle_sizes(ctx, n_rows, size_profile)
    color_table = _target_color_table(ctx, n_rows, color_pattern, target_palette)

    positions = _rectangle_positions(ctx, sizes)
    grid = full_grid(30, 30, 0)
    occupied: set[tuple[int, int]] = set()
    for row_index, row_positions in enumerate(positions):
        for col_index, (top, left) in enumerate(row_positions):
            rect_h, rect_w = sizes[row_index][col_index]
            color = color_table[row_index][col_index]
            draw_rect(grid, top, left, rect_h, rect_w, color)
            occupied.update(
                (row, col)
                for row in range(top, top + rect_h)
                for col in range(left, left + rect_w)
            )

    # Canonical noise has 292..366 cells but only 175..203 components: it is
    # sparse, irregular two-color texture, not a checkerboard of singletons.
    # Sample occupied noise cells uniformly and color them independently, then
    # retry deterministically if chance produces an accidental >=90%-filled
    # 9-cell component that the oracle would misclassify as another rectangle.
    empty_cells = [
        (row, col)
        for row in range(30)
        for col in range(30)
        if (row, col) not in occupied
    ]
    if noise_count > len(empty_cells):
        raise ValueError(
            f"noise_count={noise_count} exceeds {len(empty_cells)} empty cells"
        )
    recorded = ctx.recorded_draws()
    for attempt in range(32):
        candidate_grid = [row[:] for row in grid]
        noise_rng = ctx.draw_rng(f"noise_texture_{attempt}")
        positions = empty_cells[:]
        noise_rng.shuffle(positions)
        selected = positions[:noise_count]
        for index, (row, col) in enumerate(selected):
            if index < 2:
                color = noise_colors[index]
            else:
                color = noise_colors[noise_rng.randrange(2)]
            candidate_grid[row][col] = color
        errors = self_check(
            candidate_grid, difficulty=band, meta={"overrides": recorded}
        )
        if not errors:
            return candidate_grid
    raise RuntimeError(
        "could not draw valid irregular noise after 32 deterministic attempts: "
        + "; ".join(errors)
    )
