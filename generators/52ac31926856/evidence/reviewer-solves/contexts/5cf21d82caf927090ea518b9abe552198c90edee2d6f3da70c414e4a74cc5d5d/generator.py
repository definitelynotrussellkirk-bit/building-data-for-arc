"""Semantic generator for ARC task db7260a4 / 52ac31926856.

A blue drop sits above one or two red, open-top containers.  Each container may
be divided into adjacent sections by vertical red walls.  The drop falls in its
column, skips a section when any cell of that section's floor is missing, and
fills the first lower section whose complete floor is red.  If no section can
hold it, the blue liquid spreads across the bottom row.

The three-sample schedule is deliberate: first-container landing, second-
container landing after a leak, then bottom spill after all candidates leak.
The first two scenes also carry an adjacent section, so every three-demo lesson
rebuts both "stop at the first frame" and "fill the whole outer container"
shortcuts.  Leaky target floors place their decisive gap away from the drop
column whenever the section is wider than one cell, rebutting a check-only-
under-the-drop shortcut.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "52ac31926856"
VERSION = "3.0.0"
TASK_ID = "52ac31926856"
RULE_HASH = "afd3c4e6c015"

SUMMARY = (
    "Remove the blue (1) drop, follow its column downward through the red (2) "
    "open-top containers, and fill the first bounded section whose entire "
    "floor is solid red. A floor with any gap leaks, so the drop continues to "
    "the next lower container; if every candidate leaks, color the whole "
    "bottom row blue. Adjacent red dividers delimit independent sections."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15
CANONICAL_PROFILES = ((10, 10),)

INVARIANTS = [
    "the palette is exactly black background 0, one blue drop 1, and red walls 2",
    "the single blue drop lies strictly above every red container",
    "each container has at least two full-height red walls and a bottom floor row",
    "the drop column lies strictly between adjacent walls in every container",
    "containers are vertically separated and contain no interior red cells above the floor",
]

LANDINGS = ("first", "second", "bottom")
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# Only exact properties recoverable from the returned grid are public axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware with recurring canonical 10x10 anchors",
        "valid": "10..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware with recurring canonical 10x10 anchors",
        "valid": "10..20",
    },
    "landing": {
        "type": "str",
        "default": "scheduled first|second|bottom",
        "valid": "first|second|bottom",
    },
    "target_width": {
        "type": "int",
        "default": "1..5; leaky scheduled scenes use at least 2",
        "valid": "1..5",
    },
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    source = nested if isinstance(nested, dict) else meta
    return {
        name: value
        for name, value in source.items()
        if name in AXES and value is not None
    }


def _band_ranges(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (10, 13), (10, 13)
    if difficulty == "hard":
        return (16, 20), (16, 20)
    return (12, 17), (12, 17)


def _draw_dimensions(ctx, difficulty: Any, overrides: dict[str, Any], sample_index: int):
    exact_h = overrides.get("grid_h") is not None
    exact_w = overrides.get("grid_w") is not None
    canonical_slot = not exact_h and not exact_w and sample_index % 5 == 0
    if canonical_slot:
        return ctx.draw_int("grid_h", 10, 10), ctx.draw_int("grid_w", 10, 10)

    (h_lo, h_hi), (w_lo, w_hi) = _band_ranges(difficulty)
    height = (
        ctx.draw_int("grid_h", 10, 20)
        if exact_h
        else ctx.draw_int("grid_h", h_lo, h_hi)
    )
    width = (
        ctx.draw_int("grid_w", 10, 20)
        if exact_w
        else ctx.draw_int("grid_w", w_lo, w_hi)
    )
    return height, width


def _draw_landing(ctx, overrides: dict[str, Any], sample_index: int) -> str:
    if overrides.get("landing") is not None:
        return ctx.draw_choice("landing", LANDINGS)
    scheduled = LANDINGS[sample_index % len(LANDINGS)]
    return ctx.draw_choice("landing", (scheduled,))


def _draw_target_width(
    ctx,
    overrides: dict[str, Any],
    landing: str,
    partition_side: str,
) -> int:
    if overrides.get("target_width") is not None:
        return ctx.draw_int("target_width", 1, 5)
    # Ordinary leaky scenes always admit an off-column floor gap.  Partitioned
    # scenes cap at four so the adjacent section still fits in canonical 10x10.
    low = 2 if landing in ("second", "bottom") else 1
    high = 4 if partition_side != "none" else 5
    return ctx.draw_int("target_width", low, high)


def _wall_columns(
    width: int,
    target_width: int,
    requested_partition: str,
    rng,
) -> tuple[list[int], int, str]:
    """Return wall columns, target section index, and realized partition side."""
    side = requested_partition
    extra_width = rng.randint(1, 2)
    required_span = target_width + 2 + extra_width if side != "none" else target_width + 1
    required_cells = required_span + 1
    if required_cells + 2 > width:
        side = "none"
        required_span = target_width + 1
        required_cells = required_span + 1

    margin = width - required_cells
    left_margin = rng.randint(1, margin - 1) if margin >= 2 else rng.randint(0, margin)
    outer_left = left_margin

    if side == "left":
        middle = outer_left + extra_width + 1
        outer_right = middle + target_width + 1
        return [outer_left, middle, outer_right], 1, side
    if side == "right":
        middle = outer_left + target_width + 1
        outer_right = middle + extra_width + 1
        return [outer_left, middle, outer_right], 0, side
    outer_right = outer_left + target_width + 1
    return [outer_left, outer_right], 0, "none"


def _vertical_layout(height: int, count: int, rng) -> tuple[int, list[tuple[int, int]]]:
    """Return blue row and non-overlapping (top, bottom) container spans."""
    if count == 2:
        # h=10 exactly supports: two rows above, 3-row frame, one-row gap,
        # 3-row frame, one row below. Spread all extra height deterministically.
        slack = height - 10
        allocations = [0, 0, 0, 0]
        for _ in range(slack):
            allocations[rng.randrange(len(allocations))] += 1
        top_extra, first_extra, gap_extra, second_extra = allocations
        first_top = 2 + top_extra
        first_bottom = first_top + 2 + first_extra
        second_top = first_bottom + 2 + gap_extra
        second_bottom = second_top + 2 + second_extra
        if second_bottom > height - 2:
            raise RuntimeError("internal two-container layout exceeded grid height")
        blue_row = rng.randint(0, first_top - 1)
        return blue_row, [(first_top, first_bottom), (second_top, second_bottom)]

    max_top = height - 4
    top = rng.randint(2, max_top)
    max_height = min(7, height - top - 1)
    frame_height = rng.randint(3, max_height)
    bottom = top + frame_height - 1
    blue_row = rng.randint(0, top - 1)
    return blue_row, [(top, bottom)]


def _paint_floor_section(
    grid,
    bottom: int,
    left: int,
    right: int,
    *,
    solid: bool,
    blue_col: int,
    rng,
) -> None:
    interior = list(range(left + 1, right))
    if solid:
        for col in interior:
            grid[bottom][col] = 2
        return

    # Keep every cell except one red. Prefer a gap away from the drop column;
    # this is the decisive witness against checking only the cell below blue.
    gap_choices = [col for col in interior if col != blue_col] or interior
    gap = rng.choice(gap_choices)
    for col in interior:
        if col != gap:
            grid[bottom][col] = 2


def _build_container(
    grid,
    top: int,
    bottom: int,
    wall_cols: list[int],
    target_index: int,
    *,
    target_solid: bool,
    blue_col: int,
    rng,
) -> None:
    for col in wall_cols:
        for row in range(top, bottom + 1):
            grid[row][col] = 2

    for section_index, (left, right) in enumerate(zip(wall_cols, wall_cols[1:])):
        if section_index == target_index:
            solid = target_solid
        else:
            # Adjacent sections deliberately disagree with the target floor
            # when possible, making the blue column/nearest-wall relation visible.
            solid = not target_solid
        _paint_floor_section(
            grid,
            bottom,
            left,
            right,
            solid=solid,
            blue_col=blue_col,
            rng=rng,
        )


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
    height, width = _draw_dimensions(ctx, difficulty, overrides, sample_index)
    landing = _draw_landing(ctx, overrides, sample_index)

    requested_partition = ("left", "right", "none")[sample_index % 3]
    target_width = _draw_target_width(
        ctx, overrides, landing, requested_partition
    )
    rng = ctx.draw_rng("layout")
    wall_cols, target_index, _ = _wall_columns(
        width, target_width, requested_partition, rng
    )
    target_left, target_right = wall_cols[target_index : target_index + 2]
    blue_col = rng.randint(target_left + 1, target_right - 1)

    if landing == "second":
        container_count = 2
    else:
        # Vary one versus two candidates without making it another public axis.
        container_count = 1 if sample_index % 4 in (0, 3) else 2
    blue_row, spans = _vertical_layout(height, container_count, rng)
    if (height, width) == (10, 10):
        # The recurring canonical-profile anchor also preserves the public
        # top-row drop relation rather than matching dimensions alone.
        blue_row = 0

    grid = full_grid(height, width, 0)
    grid[blue_row][blue_col] = 1
    for index, (top, bottom) in enumerate(spans):
        if landing == "first":
            target_solid = index == 0 or rng.choice((False, True))
        elif landing == "second":
            target_solid = index == 1
        else:
            target_solid = False
        _build_container(
            grid,
            top,
            bottom,
            wall_cols,
            target_index,
            target_solid=target_solid,
            blue_col=blue_col,
            rng=rng,
        )

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise RuntimeError("internal construction error: " + "; ".join(analysis["errors"]))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "landing": landing,
        "target_width": target_width,
    }
    if observed != expected:
        raise RuntimeError(f"internal axis mismatch: expected {expected}, observed {observed}")
    return grid


def _contiguous_bottom(grid, top: int, col: int) -> int:
    row = top
    while row + 1 < len(grid) and grid[row + 1][col] == 2:
        row += 1
    return row


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular matrix"]}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"]}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {"errors": ["grid must be rectangular and nonempty"]}
    height = len(grid)
    width = next(iter(widths))
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid must fit the ARC 30 by 30 limit")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value not in (0, 1, 2)
        for row in grid
        for value in row
    ):
        return {"errors": errors + ["cells must use only colors 0, 1, and 2"]}

    blues = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    if len(blues) != 1:
        errors.append(f"expected exactly one blue drop, found {len(blues)}")
        return {"errors": errors}
    blue_row, blue_col = blues[0]

    # Parse red open-top containers independently of whether the blue column
    # intersects them. Canonical includes a lawful scene where the drop is to
    # the right of the only frame and therefore spills directly to the bottom.
    containers = []
    seen_tops = set()
    for top in range(height):
        red_cols = [col for col in range(width) if grid[top][col] == 2]
        if len(red_cols) < 2:
            continue
        outer_left, outer_right = red_cols[0], red_cols[-1]
        if (
            top > 0
            and grid[top - 1][outer_left] == 2
            and grid[top - 1][outer_right] == 2
        ):
            continue
        bottoms = [_contiguous_bottom(grid, top, col) for col in red_cols]
        bottom = min(bottoms)
        if bottom - top < 2:
            continue
        if any(value != bottom for value in bottoms):
            errors.append(f"container at row {top} has unequal wall heights")
            continue
        if top in seen_tops:
            continue
        seen_tops.add(top)

        lefts = [col for col in red_cols if col < blue_col]
        rights = [col for col in red_cols if col > blue_col]
        target_left = max(lefts) if lefts else None
        if rights:
            target_right = min(rights)
        elif blue_col in red_cols:
            # This is the canonical program's explicit right-wall fallback:
            # when no red wall lies to the right, a red cell exactly under the
            # drop may serve as the section's right boundary.
            target_right = blue_col
        else:
            target_right = None
        candidate = (
            target_left is not None
            and target_right is not None
            and target_left < target_right
        )
        target_index = None
        if candidate:
            target_index = red_cols.index(target_left)
            if red_cols[target_index + 1] != target_right:
                errors.append(
                    f"container at row {top} has an unparsed wall between target bounds"
                )
                candidate = False

        containers.append(
            {
                "top": top,
                "bottom": bottom,
                "walls": tuple(red_cols),
                "candidate": candidate,
                "target_index": target_index,
                "target_left": target_left if candidate else None,
                "target_right": target_right if candidate else None,
            }
        )

    containers.sort(key=lambda item: item["top"])
    if not 1 <= len(containers) <= 2:
        errors.append(f"expected one or two containers, found {len(containers)}")
    if containers and blue_row >= containers[0]["top"]:
        errors.append("the blue drop must lie strictly above the first container")

    covered_red: set[tuple[int, int]] = set()
    previous_bottom = -1
    for index, container in enumerate(containers):
        top = container["top"]
        bottom = container["bottom"]
        walls = container["walls"]
        if top <= previous_bottom + 1:
            errors.append("containers must be separated by at least one blank row")
        previous_bottom = bottom
        if blue_row >= top:
            errors.append(f"blue drop is not above container {index}")
        if any(right - left < 2 for left, right in zip(walls, walls[1:])):
            errors.append(f"container {index} has a zero-width section")

        for row in range(top, bottom + 1):
            for col in walls:
                if grid[row][col] != 2:
                    errors.append(f"container {index} wall is broken at {(row, col)}")
                covered_red.add((row, col))
        for row in range(top, bottom):
            for col in range(walls[0], walls[-1] + 1):
                if col not in walls and grid[row][col] != 0:
                    errors.append(
                        f"container {index} has interior red above its floor at {(row, col)}"
                    )
        for col in range(walls[0], walls[-1] + 1):
            if grid[bottom][col] == 2:
                covered_red.add((bottom, col))

        if container["candidate"]:
            left = container["target_left"]
            right = container["target_right"]
            container["target_width"] = right - left - 1
            container["floor_solid"] = all(
                grid[bottom][col] == 2 for col in range(left + 1, right)
            )
            container["blue_floor_solid"] = grid[bottom][blue_col] == 2
            container["off_column_gap"] = any(
                col != blue_col and grid[bottom][col] == 0
                for col in range(left + 1, right)
            )
        else:
            container["target_width"] = None
            container["floor_solid"] = False
            container["blue_floor_solid"] = False
            container["off_column_gap"] = False

    all_red = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }
    extra_red = sorted(all_red - covered_red)
    if extra_red:
        errors.append(f"red cells outside parsed containers: {extra_red[:4]}")

    selected_index = next(
        (
            index
            for index, item in enumerate(containers)
            if item.get("candidate") and item.get("floor_solid")
        ),
        None,
    )
    if selected_index == 0:
        landing = "first"
    elif selected_index == 1:
        landing = "second"
    else:
        landing = "bottom"

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": tuple(sorted({value for row in grid for value in row})),
        "blue": (blue_row, blue_col),
        "containers": containers,
        "selected_index": selected_index,
        "landing": landing,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/rule-hiding scenes and verify exact requested axes."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    containers = analysis["containers"]
    target_widths = {
        item["target_width"] for item in containers if item["candidate"]
    }
    if len(target_widths) != 1:
        # Canonical test data lawfully varies widths by depth, but generated
        # exact-axis scenes never do. Omitting the axis makes such archival
        # inputs impossible to misread as exact override witnesses.
        target_width = None
    else:
        target_width = next(iter(target_widths))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "landing": analysis["landing"],
        "target_width": target_width,
    }


def rule_mirror(grid):
    """Exact Python mirror for focused tests; canonical Racket remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = _copy_grid(grid)
    blue_row, blue_col = analysis["blue"]
    output[blue_row][blue_col] = 0
    selected = analysis["selected_index"]
    if selected is None:
        output[-1] = [1 for _ in output[-1]]
        return output
    container = analysis["containers"][selected]
    for row in range(container["top"], container["bottom"]):
        for col in range(container["target_left"] + 1, container["target_right"]):
            if output[row][col] == 0:
                output[row][col] = 1
    return output


def strict_canonical_like(grid) -> list[str]:
    """Linked public manifold: canonical size, palette, drop row, and grammar."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analyze(grid)
    if (analysis["height"], analysis["width"]) != (10, 10):
        reasons.append("canonical inputs are 10 by 10")
    if analysis["palette"] != (0, 1, 2):
        reasons.append("canonical palette is exactly {0,1,2}")
    if analysis["blue"][0] != 0:
        reasons.append("canonical blue drop is on the top row")
    return reasons


def _rival_always_bottom(grid):
    output = _copy_grid(grid)
    blue_row, blue_col = _analyze(grid)["blue"]
    output[blue_row][blue_col] = 0
    output[-1] = [1 for _ in output[-1]]
    return output


def _fill_section(output, container):
    for row in range(container["top"], container["bottom"]):
        for col in range(container["target_left"] + 1, container["target_right"]):
            if output[row][col] == 0:
                output[row][col] = 1
    return output


def _rival_stop_at_first_container(grid):
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    blue_row, blue_col = analysis["blue"]
    output[blue_row][blue_col] = 0
    first_candidate = next(item for item in analysis["containers"] if item["candidate"])
    return _fill_section(output, first_candidate)


def _rival_fill_outer_selected_container(grid):
    analysis = _analyze(grid)
    if analysis["selected_index"] is None:
        return _rival_always_bottom(grid)
    output = _copy_grid(grid)
    blue_row, blue_col = analysis["blue"]
    output[blue_row][blue_col] = 0
    container = analysis["containers"][analysis["selected_index"]]
    for row in range(container["top"], container["bottom"]):
        for col in range(container["walls"][0] + 1, container["walls"][-1]):
            if output[row][col] == 0:
                output[row][col] = 1
    return output


def _rival_check_only_under_drop(grid):
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    blue_row, blue_col = analysis["blue"]
    output[blue_row][blue_col] = 0
    chosen = next(
        (
            item
            for item in analysis["containers"]
            if item["candidate"] and item["blue_floor_solid"]
        ),
        None,
    )
    if chosen is None:
        output[-1] = [1 for _ in output[-1]]
        return output
    return _fill_section(output, chosen)


SEMANTIC_RIVALS = {
    "always spill to bottom": _rival_always_bottom,
    "stop at first container even when its floor leaks": _rival_stop_at_first_container,
    "fill the whole outer selected container": _rival_fill_outer_selected_container,
    "inspect only the floor cell under the drop": _rival_check_only_under_drop,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _witness_first_landing(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["landing"] == "first"


def _witness_second_landing(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["landing"] == "second"


def _witness_bottom_spill(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["landing"] == "bottom"


def _witness_partition(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["selected_index"] is not None
        and len(analysis["containers"][analysis["selected_index"]]["walls"]) >= 3
        and _rival_fill_outer_selected_container(grid) != rule_mirror(grid)
    )


def _witness_off_column_gap(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    return any(
        not item["floor_solid"]
        and item["blue_floor_solid"]
        and item["off_column_gap"]
        for item in analysis["containers"]
    ) and _rival_check_only_under_drop(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "first_solid_section_holds_drop": _witness_first_landing,
    "leaky_upper_section_skips_to_second": _witness_second_landing,
    "all_sections_leak_to_bottom_row": _witness_bottom_spill,
    "adjacent_divider_rebuts_fill_whole_container": _witness_partition,
    "off_column_floor_gap_rebuts_single_cell_check": _witness_off_column_gap,
}

WITNESS_RIVALS = {
    "first_solid_section_holds_drop": ["always spill to bottom"],
    "leaky_upper_section_skips_to_second": [
        "stop at first container even when its floor leaks",
        "always spill to bottom",
    ],
    "all_sections_leak_to_bottom_row": [
        "stop at first container even when its floor leaks"
    ],
    "adjacent_divider_rebuts_fill_whole_container": [
        "fill the whole outer selected container"
    ],
    "off_column_floor_gap_rebuts_single_cell_check": [
        "inspect only the floor cell under the drop"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a plausible rival survives but changes the query."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} consecutive demonstrations"]
    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} does not match the drop/container rule")
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the drop/container rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
