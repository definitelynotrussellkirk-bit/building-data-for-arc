"""Generator for ARC task b527c5c6.

Each solid green rectangle contains one non-corner red marker on its rim.  The
marker fires away from the rectangle to the grid boundary: the centre ray is
red and the green side wings have half-width equal to the rectangle depth
behind the marker.  Every scene contains multiple separated rectangles so the
lesson demonstrates per-marker processing rather than a one-object shortcut.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "038f266f3acf"
TASK_ID = GENERATOR_ID
RULE_HASH = "3d0748ee02cc"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains two or three separated solid green(3) "
    "rectangles. Each rectangle has exactly one red(2) non-corner rim cell. "
    "For every red marker independently, project a red centre ray away from "
    "its rectangle to the grid edge and paint green side wings whose "
    "half-width equals the distance from the marker to the opposite rectangle "
    "edge."
)

INVARIANTS = [
    "the palette is exactly background 0, marker 2, and rectangle color 3",
    "there are two or three separated solid rectangles",
    "each rectangle contains exactly one red non-corner boundary marker",
    "the marker has at least one outward cell before the grid boundary",
    "ordinary lessons include both horizontal and vertical launches",
    "ordinary lessons vary rectangle depth and include non-central markers",
]

# One exact, fully observable profile axis is preferable to the old six-axis
# contract whose difficulty-specific clamping made thousands of declared
# boundary combinations false.  The profiles retain both official 10x10 and
# 20x20 scales while adding a three-object generalization.
AXES = {
    "profile": {
        "type": "str",
        "default": "four-slot sample_index schedule",
        "valid": "small_pair|mid_trio|large_pair|large_trio",
        "doc": "Exact (height, width, rectangle-count) curriculum profile.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "small_pair",
    "mid_trio",
    "large_pair",
    "large_trio",
)

# (height, width, rectangle specs).  Each rectangle spec is
# (row choices, col choices, rect_h, rect_w, launch edge).  The layouts leave
# one-cell moats and disjoint outward beam corridors before global reflection.
_PROFILE_SPECS: dict[str, tuple[int, int, tuple[tuple[Any, ...], ...]]] = {
    "small_pair": (
        10,
        10,
        (
            ((1, 2), (2, 3), 6, 2, "left"),
            ((4,), (6,), 3, 4, "bottom"),
        ),
    ),
    "mid_trio": (
        14,
        16,
        (
            ((2, 3), (2,), 7, 3, "left"),
            ((2,), (8, 9), 4, 6, "top"),
            ((10,), (8, 9), 3, 6, "bottom"),
        ),
    ),
    "large_pair": (
        20,
        20,
        (
            ((3, 4), (1, 2, 3), 3, 14, "top"),
            ((8, 9), (14,), 11, 5, "left"),
        ),
    ),
    "large_trio": (
        20,
        20,
        (
            ((2, 3), (1, 2), 4, 8, "top"),
            ((2, 3), (14,), 8, 5, "right"),
            ((15,), (6, 7), 4, 8, "bottom"),
        ),
    ),
}

_PROFILE_SIGNATURES = {
    name: (height, width, len(specs))
    for name, (height, width, specs) in _PROFILE_SPECS.items()
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EDGE_DIR = {
    "top": (-1, 0),
    "bottom": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose a residue-complete schedule with a visible band phase shift."""
    del seed
    phase = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return SCHEDULE_PROFILES[(int(sample_index) + phase) % len(SCHEDULE_PROFILES)]


def _scheduled_profile(ctx, default: str) -> str:
    if "profile" in ctx.overrides and ctx.overrides["profile"] is not None:
        return str(ctx.draw_choice("profile", list(SCHEDULE_PROFILES)))
    return str(ctx.draw_choice("profile", [default]))


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(not isinstance(value, int) for row in grid for value in row):
        return ["grid cells must be integers"]
    return []


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in _DIRS4:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "rectangles": []}

    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    palette = {value for row in normalized for value in row}
    if palette != {0, 2, 3}:
        errors.append(f"palette must be exactly {{0,2,3}}, found {sorted(palette)}")

    rectangles: list[dict[str, Any]] = []
    for component_index, cells in enumerate(_components(normalized)):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        rect_h, rect_w = r2 - r1 + 1, c2 - c1 + 1
        expected = {
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
        }
        if cells != expected:
            errors.append(
                f"component {component_index} must fill its {rect_h}x{rect_w} bbox"
            )
            continue
        if rect_h < 2 or rect_w < 2:
            errors.append(
                f"component {component_index} rectangle is too thin: {rect_h}x{rect_w}"
            )

        red = sorted((row, col) for row, col in cells if normalized[row][col] == 2)
        non_red_bad = [
            (row, col)
            for row, col in cells
            if normalized[row][col] not in (2, 3)
        ]
        if non_red_bad:
            errors.append(f"component {component_index} contains non 2/3 cells")
        if len(red) != 1:
            errors.append(
                f"component {component_index} must contain exactly one red marker, found {len(red)}"
            )
            continue

        marker = red[0]
        mr, mc = marker
        edges = []
        if mr == r1:
            edges.append("top")
        if mr == r2:
            edges.append("bottom")
        if mc == c1:
            edges.append("left")
        if mc == c2:
            edges.append("right")
        if len(edges) != 1:
            errors.append(
                f"component {component_index} marker must be on exactly one non-corner edge"
            )
            continue
        edge = edges[0]
        if edge in ("top", "bottom") and rect_w < 3:
            errors.append(
                f"component {component_index} horizontal marker edge needs width >=3"
            )
        if edge in ("left", "right") and rect_h < 3:
            errors.append(
                f"component {component_index} vertical marker edge needs height >=3"
            )

        dr, dc = _EDGE_DIR[edge]
        if not (0 <= mr + dr < height and 0 <= mc + dc < width):
            errors.append(
                f"component {component_index} marker has no outward beam cell"
            )

        half_width = rect_h - 1 if edge in ("top", "bottom") else rect_w - 1
        offset = mc - c1 if edge in ("top", "bottom") else mr - r1
        span = rect_w if edge in ("top", "bottom") else rect_h
        beam_length = (
            mr if edge == "top" else
            height - 1 - mr if edge == "bottom" else
            mc if edge == "left" else
            width - 1 - mc
        )
        rectangles.append(
            {
                "bbox": (r1, c1, r2, c2),
                "rect_h": rect_h,
                "rect_w": rect_w,
                "marker": marker,
                "edge": edge,
                "direction": (dr, dc),
                "half_width": half_width,
                "offset": offset,
                "span": span,
                "beam_length": beam_length,
            }
        )

    if not (2 <= len(rectangles) <= 4):
        errors.append(f"expected 2..4 lawful rectangles, found {len(rectangles)}")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "rectangles": sorted(rectangles, key=lambda item: item["marker"]),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid: Any) -> dict[str, str]:
    """Recover the exact declared profile from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    signature = (
        analysis["height"],
        analysis["width"],
        len(analysis["rectangles"]),
    )
    for name, expected in _PROFILE_SIGNATURES.items():
        if signature == expected:
            return {"profile": name}
    return {}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural authority grammar; accepts every canonical input."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Generated grids stay inside the same solid-rectangle task manifold."""
    return self_check(grid)


def _launch(
    output: list[list[int]],
    rect: dict[str, Any],
    *,
    half_width: int | None = None,
    direction: tuple[int, int] | None = None,
    max_steps: int | None = None,
    centered: bool = False,
) -> None:
    height, width = len(output), len(output[0])
    r1, c1, r2, c2 = rect["bbox"]
    marker_r, marker_c = rect["marker"]
    edge = rect["edge"]
    if centered:
        if edge in ("top", "bottom"):
            marker_c = (c1 + c2) // 2
        else:
            marker_r = (r1 + r2) // 2
    dr, dc = direction if direction is not None else rect["direction"]
    half = rect["half_width"] if half_width is None else half_width

    row, col = marker_r + dr, marker_c + dc
    steps = 0
    while 0 <= row < height and 0 <= col < width:
        if max_steps is not None and steps >= max_steps:
            break
        output[row][col] = 2
        for offset in range(1, half + 1):
            if dr == 0:
                side_cells = ((row - offset, col), (row + offset, col))
            else:
                side_cells = ((row, col - offset), (row, col + offset))
            for side_r, side_c in side_cells:
                if 0 <= side_r < height and 0 <= side_c < width:
                    output[side_r][side_c] = 3
        row += dr
        col += dc
        steps += 1


def _apply_variant(
    grid: list[list[int]],
    *,
    only_first: bool = False,
    fixed_half: int | None = None,
    half_width_cap: int | None = None,
    reverse_direction: bool = False,
    max_steps_from_half: bool = False,
    centered: bool = False,
) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    rectangles = analysis["rectangles"][:1] if only_first else analysis["rectangles"]
    for rect in rectangles:
        direction = rect["direction"]
        if reverse_direction:
            direction = (-direction[0], -direction[1])
        half_width = fixed_half
        if half_width_cap is not None:
            half_width = min(rect["half_width"], half_width_cap)
        _launch(
            output,
            rect,
            half_width=half_width,
            direction=direction,
            max_steps=rect["half_width"] if max_steps_from_half else None,
            centered=centered,
        )
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    return _apply_variant(grid)


def _rival_first_marker_only(grid):
    return _apply_variant(grid, only_first=True)


def _rival_fixed_three_cell_width(grid):
    return _apply_variant(grid, fixed_half=1)


def _rival_launch_toward_rectangle(grid):
    return _apply_variant(grid, reverse_direction=True)


def _rival_stop_after_rectangle_depth(grid):
    return _apply_variant(grid, max_steps_from_half=True)


def _rival_assume_centered_marker(grid):
    return _apply_variant(grid, centered=True)


def _rival_red_ray_without_green_wings(grid):
    return _apply_variant(grid, fixed_half=0)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "process_only_first_marker": _rival_first_marker_only,
    "use_fixed_three_cell_beam_width": _rival_fixed_three_cell_width,
    "launch_toward_the_rectangle": _rival_launch_toward_rectangle,
    "stop_after_one_rectangle_depth": _rival_stop_after_rectangle_depth,
    "assume_marker_is_edge_center": _rival_assume_centered_marker,
    "paint_red_ray_without_green_wings": _rival_red_ray_without_green_wings,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_rectangles(grid: Any) -> list[dict[str, Any]]:
    analysis = _analysis(grid)
    return [] if analysis["errors"] else analysis["rectangles"]


def _multiple_rectangles(grid: Any) -> bool:
    return len(_valid_rectangles(grid)) >= 2


def _different_depths(grid: Any) -> bool:
    rects = _valid_rectangles(grid)
    return len({rect["half_width"] for rect in rects}) >= 2


def _noncentral_marker(grid: Any) -> bool:
    return any(
        rect["offset"] != (rect["span"] - 1) // 2
        for rect in _valid_rectangles(grid)
    )


def _both_launch_axes(grid: Any) -> bool:
    edges = {rect["edge"] for rect in _valid_rectangles(grid)}
    return bool(edges & {"top", "bottom"}) and bool(edges & {"left", "right"})


def _long_beam(grid: Any) -> bool:
    return any(rect["beam_length"] >= 4 for rect in _valid_rectangles(grid))


def _canonical_dimension_anchor(grid: Any) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and (
        analysis["height"], analysis["width"]
    ) in {(10, 10), (20, 20)}


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "multiple_rectangles_are_processed": _multiple_rectangles,
    "rectangle_depth_controls_beam_width": _different_depths,
    "marker_position_not_edge_center": _noncentral_marker,
    "horizontal_and_vertical_launches": _both_launch_axes,
    "beam_continues_to_grid_boundary": _long_beam,
    "canonical_10_or_20_dimension_anchor": _canonical_dimension_anchor,
}
WITNESS_RIVALS = {
    "multiple_rectangles_are_processed": ["process_only_first_marker"],
    "rectangle_depth_controls_beam_width": ["use_fixed_three_cell_beam_width"],
    "marker_position_not_edge_center": ["assume_marker_is_edge_center"],
    "horizontal_and_vertical_launches": ["launch_toward_the_rectangle"],
    "beam_continues_to_grid_boundary": ["stop_after_one_rectangle_depth"],
    "canonical_10_or_20_dimension_anchor": ["paint_red_ray_without_green_wings"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check named rivals and query-relevant integer half-width caps.

    These finite rival checks are not a universal identifiability guarantee.
    Only the query input is read; its held-out output is never consulted.
    """
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_valid = not self_check(query["input"])
    if not query_valid:
        reasons.append("query input is outside the teaching grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        check_errors = self_check(demo["input"])
        if check_errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the beam rule")
            continue
        valid_demos.append(demo)
    if len(valid_demos) != len(demos):
        return reasons

    for name, predicate in SEMANTIC_WITNESSES.items():
        if not any(predicate(demo["input"]) for demo in valid_demos):
            reasons.append(f"demonstrations never show witness: {name}")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"named competitor survives every demonstration: {name}")

    if query_valid:
        expected_query = rule_mirror(query["input"])
        max_query_depth = max(rect["half_width"]
                              for rect in _valid_rectangles(query["input"]))
        # Larger caps cannot change this query. Compare rendered predictions so
        # clipping and beam overwrites can make smaller caps equivalent too.
        for cap in range(max_query_depth):
            if _apply_variant(query["input"], half_width_cap=cap) == expected_query:
                continue
            if all(_apply_variant(demo["input"], half_width_cap=cap) == demo["output"]
                   for demo in valid_demos):
                reasons.append(
                    f"half-width cap {cap} survives every demonstration "
                    "and changes the query prediction")
    return reasons


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _allowed_marker_offsets(
    *,
    row: int,
    col: int,
    rect_h: int,
    rect_w: int,
    edge: str,
    grid_h: int,
    grid_w: int,
) -> list[int]:
    span = rect_w if edge in ("top", "bottom") else rect_h
    half = rect_h - 1 if edge in ("top", "bottom") else rect_w - 1
    allowed = []
    for offset in range(1, span - 1):
        center = col + offset if edge in ("top", "bottom") else row + offset
        limit = grid_w if edge in ("top", "bottom") else grid_h
        if center - half >= 0 and center + half < limit:
            allowed.append(offset)
    return allowed


def _paint_rectangle(
    grid: list[list[int]],
    *,
    row: int,
    col: int,
    rect_h: int,
    rect_w: int,
    edge: str,
    marker_offset: int,
) -> None:
    for r in range(row, row + rect_h):
        for c in range(col, col + rect_w):
            if grid[r][c] != 0:
                raise ValueError("rectangle placement overlap")
            grid[r][c] = 3
    if edge == "top":
        marker = (row, col + marker_offset)
    elif edge == "bottom":
        marker = (row + rect_h - 1, col + marker_offset)
    elif edge == "left":
        marker = (row + marker_offset, col)
    else:
        marker = (row + marker_offset, col + rect_w - 1)
    grid[marker[0]][marker[1]] = 2


def _beam_corridors_are_clean(grid: list[list[int]]) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    occupied = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0
    }
    for rect in analysis["rectangles"]:
        probe = full_grid(len(grid), len(grid[0]), 0)
        _launch(probe, rect)
        cells = {
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if probe[row][col] != 0
        }
        if cells & occupied:
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic input grid; canonical Racket owns the output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_profile = schedule_profile(seed, sample_index, difficulty)
    profile = _scheduled_profile(ctx, default_profile)
    height, width, specs = _PROFILE_SPECS[profile]
    rng = ctx.draw_rng(f"layout:{profile}")

    grid = full_grid(height, width, 0)
    for index, (row_choices, col_choices, rect_h, rect_w, edge) in enumerate(specs):
        row = int(rng.choice(row_choices))
        col = int(rng.choice(col_choices))
        offsets = _allowed_marker_offsets(
            row=row,
            col=col,
            rect_h=rect_h,
            rect_w=rect_w,
            edge=edge,
            grid_h=height,
            grid_w=width,
        )
        if not offsets:
            raise ValueError(f"profile {profile} rectangle {index} has no lawful marker")
        # The first rectangle in every profile is forced off the floor-centre
        # when possible, so every four-demo lesson refutes the centered-marker
        # shortcut independently of random luck.
        if index == 0:
            span = rect_w if edge in ("top", "bottom") else rect_h
            central_offsets = {(span - 1) // 2, span // 2}
            offcenter = [offset for offset in offsets if offset not in central_offsets]
            if offcenter:
                offsets = offcenter
        marker_offset = int(rng.choice(offsets))
        _paint_rectangle(
            grid,
            row=row,
            col=col,
            rect_h=rect_h,
            rect_w=rect_w,
            edge=edge,
            marker_offset=marker_offset,
        )

    transform = rng.randrange(4)
    if transform & 1:
        grid = _flip_lr(grid)
    if transform & 2:
        grid = _flip_ud(grid)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    curriculum_checks = {
        "multiple rectangles": _multiple_rectangles(grid),
        "different rectangle depths": _different_depths(grid),
        "both launch axes": _both_launch_axes(grid),
        "non-central marker": _noncentral_marker(grid),
    }
    missing = [name for name, present in curriculum_checks.items() if not present]
    if missing:
        raise ValueError("constructed rule-hiding instance: " + ", ".join(missing))
    return [row[:] for row in grid]
