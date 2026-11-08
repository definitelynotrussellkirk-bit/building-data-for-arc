"""Semantic generator for ARC task 1f3e27c86f7a.

Nested colored templates decorate same-color plain rectangles. Complete
templates scale their payload proportionally; a missing border side aligns
the payload to the opposite side. When no template exists, a symmetric
multicolor stripe is stretched through the center run into a plain rectangle.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1f3e27c86f7a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a3f0a934419a"
SUMMARY = (
    "Copy a nested template payload into same-color plain rectangles, using "
    "border presence for proportional or edge-aligned mapping; without a "
    "template, stretch a symmetric stripe's center run into the rectangle."
)
EXAMPLES_NEEDED = 4

BRANCHES = (
    "proportional",
    "top_align",
    "bottom_align",
    "left_align",
    "right_align",
    "stripe",
)
AXES = {
    "rule_branch": {
        "type": "str",
        "default": "rng across all semantic branches",
        "valid": "|".join(BRANCHES),
        "doc": "the observable border/alignment or stripe-fallback branch",
    },
}
INVARIANTS = [
    "background is black and every grid is rectangular",
    "nested branches contain one multicolor template and a separate same-color plain target",
    "the target is large enough for the template border depths and payload",
    "open-border branches omit exactly the side named by their alignment mode",
    "stripe scenes have no template for the target color and contain a symmetric odd-run source row",
    "every ordinary draw changes under the canonical Racket rule",
]

DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
COLORS = tuple(range(1, 10))


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            cells = []
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    neighbor = (row + delta_row, col + delta_col)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": _bbox(cells),
                }
            )
    return result


def _has_inner(grid, component):
    row1, col1, row2, col2 = component["bbox"]
    color = component["color"]
    return any(
        grid[row][col] not in (0, color)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
    )


def _depth(limit, predicate):
    result = 0
    while result < limit and predicate(result):
        result += 1
    return result


def _border_depths(grid, component):
    row1, col1, row2, col2 = component["bbox"]
    color = component["color"]
    obj_height = row2 - row1 + 1
    obj_width = col2 - col1 + 1

    def full_row(row):
        return all(grid[row][col] == color for col in range(col1, col2 + 1))

    def full_col(col):
        return all(grid[row][col] == color for row in range(row1, row2 + 1))

    return (
        _depth(obj_height, lambda offset: full_row(row1 + offset)),
        _depth(obj_height, lambda offset: full_row(row2 - offset)),
        _depth(obj_width, lambda offset: full_col(col1 + offset)),
        _depth(obj_width, lambda offset: full_col(col2 - offset)),
    )


def _runs(values):
    result = []
    for value in values:
        if result and result[-1][0] == value:
            result[-1][1] += 1
        else:
            result.append([value, 1])
    return result


def _stripe_candidates(grid):
    candidates = []
    for row in grid:
        nonzero = [col for col, value in enumerate(row) if value]
        if not nonzero:
            continue
        values = row[min(nonzero) : max(nonzero) + 1]
        run_values = _runs(values)
        if (
            all(values)
            and len(set(values)) > 1
            and values[0] == values[-1]
            and len(run_values) >= 3
            and len(run_values) % 2 == 1
            and run_values == list(reversed(run_values))
        ):
            candidates.append(values)
    return candidates


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be nonempty"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return {"errors": ["grid must be rectangular"], "facts": None}
    height, width = len(grid), next(iter(widths))
    if not (8 <= height <= 30 and 8 <= width <= 30):
        errors.append("grid dimensions must be 8..30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": errors + ["cells must be ARC integers 0..9"], "facts": None}

    components = _components(grid)
    templates = [component for component in components if _has_inner(grid, component)]
    plains = [component for component in components if not _has_inner(grid, component)]
    nested_matches = []
    for template in templates:
        matching = [
            plain
            for plain in plains
            if plain["color"] == template["color"]
            and len(plain["cells"]) >= 25
        ]
        if matching:
            nested_matches.append((template, matching))

    branch = None
    target_count = 0
    template = None
    if nested_matches:
        template, targets = max(
            nested_matches,
            key=lambda item: len(item[0]["cells"]),
        )
        target_count = len(targets)
        top, bottom, left, right = _border_depths(grid, template)
        zero_sides = [
            name
            for name, value in (
                ("top", top),
                ("bottom", bottom),
                ("left", left),
                ("right", right),
            )
            if value == 0
        ]
        if not zero_sides:
            branch = "proportional"
        elif zero_sides == ["bottom"]:
            branch = "top_align"
        elif zero_sides == ["top"]:
            branch = "bottom_align"
        elif zero_sides == ["right"]:
            branch = "left_align"
        elif zero_sides == ["left"]:
            branch = "right_align"
        else:
            errors.append("template must omit at most one border side")
        if min(top + bottom, left + right) < 2:
            errors.append("template border depths are too weak")
    else:
        stripes = _stripe_candidates(grid)
        valid_targets = []
        for values in stripes:
            color = values[0]
            fixed_width = sum(
                count
                for index, (_, count) in enumerate(_runs(values))
                if index != len(_runs(values)) // 2
            )
            valid_targets.extend(
                component
                for component in plains
                if component["color"] == color
                and component["bbox"][2] > component["bbox"][0]
                and component["bbox"][3] - component["bbox"][1] + 1
                > fixed_width
            )
        if stripes and valid_targets:
            branch = "stripe"
            target_count = len(valid_targets)
        else:
            errors.append("need a nested template/target or stripe/target lesson")

    return {
        "errors": errors,
        "facts": {
            "branch": branch,
            "height": height,
            "width": width,
            "component_count": len(components),
            "template_count": len(templates),
            "target_count": target_count,
            "template": template,
        },
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"rule_branch": analysis["facts"]["branch"]}


def lesson_identifiable(demos, query):
    """Require demonstration support for the query's observable rule branch.

    This necessary coverage check does not prove full rule identification.
    The caller validates labels through Racket; this hook reads input grids
    only, so it neither predicts outputs nor needs a hidden query answer.
    Unsupported random lessons are rejected rather than rescheduled.
    """
    if not isinstance(demos, (list, tuple)):
        return ["branch support: demonstrations must be a sequence of pairs"]
    query_input = query.get("input") if isinstance(query, dict) else None
    query_analysis = _analyze(query_input)
    if query_analysis["errors"]:
        return ["branch support: invalid query input: " + "; ".join(query_analysis["errors"])]

    reasons = []
    demonstrated = set()
    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        analysis = _analyze(demo_input)
        if analysis["errors"]:
            reasons.append(
                f"branch support: invalid demonstration {index} input: "
                + "; ".join(analysis["errors"])
            )
        else:
            demonstrated.add(analysis["facts"]["branch"])

    branch = query_analysis["facts"]["branch"]
    if branch not in demonstrated:
        reasons.append(
            f"branch support missing: query uses {branch!r}, "
            "but no demonstration input has that branch"
        )
    return reasons


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    return (
        "invalid"
        if analysis["errors"]
        else analysis["facts"]["branch"]
    )


def _dimensions(ctx, difficulty):
    if difficulty == "easy":
        return ctx.draw_int("height", 20, 23), ctx.draw_int("width", 24, 27)
    if difficulty == "hard":
        return ctx.draw_int("height", 28, 30), ctx.draw_int("width", 29, 30)
    return ctx.draw_int("height", 24, 28), ctx.draw_int("width", 26, 30)


def _paint_nested(grid, box, edge, payload, depths):
    row1, col1, row2, col2 = box
    top, bottom, left, right = depths
    for row in range(row1, row2 + 1):
        for col in range(col1, col2 + 1):
            if (
                row < row1 + top
                or row > row2 - bottom
                or col < col1 + left
                or col > col2 - right
            ):
                grid[row][col] = edge
            else:
                local_row = row - (row1 + top)
                local_col = col - (col1 + left)
                grid[row][col] = payload[
                    (local_row + 2 * local_col) % len(payload)
                ]


def _build_nested(ctx, rng, difficulty, branch):
    height, width = _dimensions(ctx, difficulty)
    edge, payload1, payload2 = ctx.draw_distinct_colors(
        "colors", n=3, exclude={0}
    )
    if branch == "proportional":
        depths = (2, 2, 2, 2)
    elif branch == "top_align":
        depths = (2, 0, 2, 2)
    elif branch == "bottom_align":
        depths = (0, 2, 2, 2)
    elif branch == "left_align":
        depths = (2, 2, 2, 0)
    elif branch == "right_align":
        depths = (2, 2, 0, 2)
    else:
        raise ValueError(f"unknown nested branch: {branch}")

    template_height = rng.randint(8, min(11, height - 11))
    template_width = rng.randint(9, min(15, width - 2))
    target_height = rng.randint(7, min(12, height - template_height - 4))
    target_width = rng.randint(10, min(17, width - 2))
    target_height = max(target_height, depths[0] + depths[1] + 2)
    target_width = max(target_width, depths[2] + depths[3] + 2)

    template_col = rng.randint(1, width - template_width - 1)
    target_col = rng.randint(1, width - target_width - 1)
    template_box = (
        1,
        template_col,
        template_height,
        template_col + template_width - 1,
    )
    target_row1 = height - target_height - 1
    target_box = (
        target_row1,
        target_col,
        target_row1 + target_height - 1,
        target_col + target_width - 1,
    )
    grid = full_grid(height, width, 0)
    _paint_nested(
        grid,
        template_box,
        edge,
        (payload1, payload2),
        depths,
    )
    for row in range(target_box[0], target_box[2] + 1):
        for col in range(target_box[1], target_box[3] + 1):
            grid[row][col] = edge
    return grid


def _build_stripe(ctx, rng, difficulty):
    height, width = _dimensions(ctx, difficulty)
    outer, inner, center = ctx.draw_distinct_colors(
        "colors", n=3, exclude={0}
    )
    outer_run = rng.randint(1, 2)
    inner_run = rng.randint(1, 3)
    center_run = rng.randint(2, 4)
    values = (
        [outer] * outer_run
        + [inner] * inner_run
        + [center] * center_run
        + [inner] * inner_run
        + [outer] * outer_run
    )
    grid = full_grid(height, width, 0)
    stripe_row = rng.randint(1, 3)
    stripe_col = rng.randint(1, width - len(values) - 1)
    for offset, value in enumerate(values):
        grid[stripe_row][stripe_col + offset] = value

    fixed_width = 2 * (outer_run + inner_run)
    target_width = rng.randint(
        fixed_width + 2,
        min(17, width - 2),
    )
    target_height = rng.randint(7, min(12, height - stripe_row - 4))
    target_row = height - target_height - 1
    target_col = rng.randint(1, width - target_width - 1)
    for row in range(target_row, target_row + target_height):
        for col in range(target_col, target_col + target_width):
            grid[row][col] = outer
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
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
    branch = ctx.draw_choice("rule_branch", BRANCHES)
    rng = ctx.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        _build_stripe(ctx, rng, band)
        if branch == "stripe"
        else _build_nested(ctx, rng, band, branch)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["branch"] != branch:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {branch}, observed "
                    f"{analysis['facts']['branch']}"
                ]
            )
        )
    return grid
