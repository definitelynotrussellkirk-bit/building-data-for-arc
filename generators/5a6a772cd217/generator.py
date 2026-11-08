"""Input sampler for Frame Interior Gallery (task ``5a6a772cd217``).

The selected Racket authority finds exact hollow color-5 rectangular frames,
orders them by top row then left column, extracts each full interior, pads all
panels to the tallest interior, and concatenates them horizontally.  Interiors
narrower than three columns receive one extra column: trailing for the first
panel, leading for every later panel.

This module samples only inputs.  ``rule_mirror`` and the named rivals are
small independent executable specifications used by focused tests and the
semantic-data gates; the Racket program remains the output authority.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5a6a772cd217"
TASK_ID = GENERATOR_ID
RULE_HASH = "64fd3246321b"
VERSION = "3.0.0"
SUMMARY = (
    "Two or three separated hollow gray (5) rectangular frames contain one "
    "distinct interior color apiece. Read frames in row-major order, preserve "
    "each complete interior rectangle, top-align to the tallest interior, and "
    "concatenate the panels. A panel narrower than three cells gets one zero "
    "column on its outside edge: after the first panel's content but before "
    "the content of every later narrow panel."
)

INVARIANTS = [
    "the canvas/profile determines exactly two or three separate exact color-5 frames",
    "every frame is 4..5 rows by 3..5 columns and has a nonempty one-color interior",
    "interior colors are pairwise distinct and every other nonzero cell belongs to a frame",
    "scheduled lessons alternate row-order conflicts and canonical left-to-right order",
]

# Unique (height, width, frame-count) tuples make the categorical axis exactly
# recoverable from returned pixels.  Four profiles reproduce every canonical
# (height, width, palette-size) profile; the final two widen support modestly.
_CANVAS_SPECS: dict[str, tuple[int, int, int]] = {
    "canonical_8x14_two": (8, 14, 2),
    "canonical_9x15_two": (9, 15, 2),
    "canonical_8x16_two": (8, 16, 2),
    "canonical_9x17_three": (9, 17, 3),
    "broad_10x18_three": (10, 18, 3),
    "broad_10x20_two": (10, 20, 2),
}
CANVAS_PROFILES = tuple(_CANVAS_SPECS)
DENSITIES = ("sparse", "balanced", "dense")

AXES = {
    "canvas_profile": {
        "type": "str",
        "default": "deterministic six-profile cycle",
        "valid": "canonical_8x14_two|canonical_9x15_two|canonical_8x16_two|canonical_9x17_three|broad_10x18_three|broad_10x20_two",
    },
    "density": {
        "type": "str",
        "default": "deterministic sparse/balanced/dense curriculum",
        "valid": "sparse|balanced|dense",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple = ()

SCHEDULE_PROFILES = ("row_order_conflict", "canonical_order")
SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_INTERIOR_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_DENSITY_COUNTS = {"sparse": 1, "balanced": 2, "dense": 4}
_PROFILE_BY_SHAPE = {shape: name for name, shape in _CANVAS_SPECS.items()}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Public deterministic profile cycle used by lesson/rotation audits."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % SCHEDULE_PERIOD]


def _draw_scheduled_axis(ctx, name: str, values: tuple[str, ...], default: str) -> str:
    """Record a deterministic default while preserving the full override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, values)
    return ctx.draw_choice(name, (default,))


def _frame_specs(frame_count: int, layout_profile: str) -> list[tuple[int, int]]:
    # The unique 5x5 frame is also the exact density witness.  Alternating its
    # row-major index exercises both sides of the rule's asymmetric narrow pad.
    if layout_profile == "row_order_conflict":
        specs = [(4, 4), (5, 5), (5, 4)]
    elif layout_profile == "canonical_order":
        specs = [(5, 5), (4, 4), (5, 4)]
    else:  # defensive: schedule_profile is intentionally finite
        raise ValueError(f"unknown layout profile {layout_profile!r}")
    return specs[:frame_count]


def _layout_frames(
    ctx,
    height: int,
    width: int,
    specs: list[tuple[int, int]],
    layout_profile: str,
) -> list[tuple[int, int, int, int]]:
    """Construct non-overlapping frame boxes with no rejection/fallback loop."""
    count = len(specs)
    if layout_profile == "row_order_conflict":
        # Semantic row-major order is 0,1,2; physical left-to-right order is
        # 1,2,0.  Distinct row offsets make the intended order unambiguous.
        physical_order = list(range(1, count)) + [0]
        row_offsets = list(range(count))
    else:
        physical_order = list(range(count))
        row_offsets = [0] * count

    block_width = sum(specs[index][1] for index in physical_order) + count - 1
    block_height = max(row_offsets[index] + specs[index][0] for index in range(count))
    if block_width > width or block_height > height:
        raise ValueError(
            f"profile {height}x{width} cannot fit frame block {block_height}x{block_width}"
        )

    top = ctx.draw_rng("vertical_translation").randint(0, height - block_height)
    left = ctx.draw_rng("horizontal_translation").randint(0, width - block_width)

    columns: dict[int, int] = {}
    cursor = left
    for index in physical_order:
        columns[index] = cursor
        cursor += specs[index][1] + 1  # exactly one guaranteed zero column

    return [
        (top + row_offsets[index], columns[index], specs[index][0], specs[index][1])
        for index in range(count)
    ]


def _draw_frame(grid: list[list[int]], top: int, left: int, height: int, width: int) -> None:
    bottom = top + height - 1
    right = left + width - 1
    for column in range(left, right + 1):
        grid[top][column] = 5
        grid[bottom][column] = 5
    for row in range(top, bottom + 1):
        grid[row][left] = 5
        grid[row][right] = 5


def _paint_interior(
    grid: list[list[int]],
    box: tuple[int, int, int, int],
    color: int,
    density: str,
    rng,
) -> None:
    top, left, height, width = box
    cells = [
        (row, column)
        for row in range(top + 1, top + height - 1)
        for column in range(left + 1, left + width - 1)
    ]
    if height == 5 and width == 5:
        # Keep a guaranteed blank leading row and column.  A tight-crop wrong
        # rule therefore changes the panel even after ordinary output padding.
        candidates = [
            (top + row_offset, left + column_offset)
            for row_offset in (2, 3)
            for column_offset in (2, 3)
        ]
        wanted = _DENSITY_COUNTS[density]
    else:
        candidates = cells
        wanted = {
            "sparse": 1,
            "balanced": min(2, len(cells) - 1),
            "dense": min(4, len(cells) - 1),
        }[density]
    if not 1 <= wanted < len(cells):
        raise RuntimeError("density construction must leave both color and zero cells")
    for row, column in rng.sample(candidates, wanted):
        grid[row][column] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input; every accepted axis is exact and observable."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band_offset = {"easy": 0, "medium": 2, "hard": 4}.get(difficulty, 0)
    default_profile = CANVAS_PROFILES[
        (sample_index + band_offset) % len(CANVAS_PROFILES)
    ]
    # Across eighteen consecutive sample indices every profile/density pair is
    # exercised exactly once; explicit overrides remain independent of band.
    default_density = DENSITIES[(sample_index // len(CANVAS_PROFILES)) % len(DENSITIES)]
    canvas_profile = _draw_scheduled_axis(
        ctx, "canvas_profile", CANVAS_PROFILES, default_profile
    )
    density = _draw_scheduled_axis(ctx, "density", DENSITIES, default_density)

    height, width, frame_count = _CANVAS_SPECS[canvas_profile]
    layout_profile = schedule_profile(seed, sample_index, difficulty)
    specs = _frame_specs(frame_count, layout_profile)
    boxes = _layout_frames(ctx, height, width, specs, layout_profile)

    grid = full_grid(height, width, 0)
    colors = ctx.draw_rng("interior_colors").sample(_INTERIOR_COLORS, frame_count)
    for index, (box, color) in enumerate(zip(boxes, colors)):
        _draw_frame(grid, *box)
        _paint_interior(
            grid,
            box,
            color,
            density,
            ctx.draw_rng(f"interior_pattern_{index}"),
        )
    return grid


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty row sequence")
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        raise ValueError("grid rows must be nonempty sequences")
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid colors must be integers 0..9")
    return len(grid), len(grid[0])


def _five_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 5
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, column = queue.popleft()
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _component_frame(component: set[tuple[int, int]]) -> dict[str, Any]:
    rows = [row for row, _ in component]
    columns = [column for _, column in component]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(columns), max(columns)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    expected = {
        (row, column)
        for row in range(r1, r2 + 1)
        for column in range(c1, c2 + 1)
        if row in (r1, r2) or column in (c1, c2)
    }
    if component != expected:
        raise ValueError(
            f"color-5 component at {(r1, c1, r2, c2)} is not an exact rectangular perimeter"
        )
    if not (4 <= height <= 5 and 3 <= width <= 5):
        raise ValueError(f"frame {height}x{width} is outside the supported 4..5 by 3..5 range")
    return {
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "height": height,
        "width": width,
        "interior_height": height - 2,
        "interior_width": width - 2,
    }


def _analyze(grid: Any) -> dict[str, Any]:
    """Parse and validate the complete input grammar, raising one clear cause."""
    height, width = _validate_grid(grid)
    components = _five_components(grid)
    if len(components) not in (2, 3):
        raise ValueError(f"expected two or three color-5 frames, found {len(components)}")

    frames = sorted(
        (_component_frame(component) for component in components),
        key=lambda frame: (frame["r1"], frame["c1"]),
    )
    shape = (height, width, len(frames))
    if shape not in _PROFILE_BY_SHAPE:
        raise ValueError(f"unsupported canvas/frame profile {shape}")

    owned_interior: dict[tuple[int, int], int] = {}
    interior_colors: list[int] = []
    for index, frame in enumerate(frames):
        interior = [
            [grid[row][column] for column in range(frame["c1"] + 1, frame["c2"])]
            for row in range(frame["r1"] + 1, frame["r2"])
        ]
        values = [value for row in interior for value in row]
        if 5 in values:
            raise ValueError(f"frame {index} contains color 5 inside its perimeter")
        colors = {value for value in values if value != 0}
        if len(colors) != 1:
            raise ValueError(
                f"frame {index} interior must contain exactly one nonzero color, found {sorted(colors)}"
            )
        if 0 not in values:
            raise ValueError(f"frame {index} interior must retain at least one zero cell")
        color = next(iter(colors))
        frame["interior"] = interior
        frame["interior_color"] = color
        frame["colored_count"] = sum(value == color for value in values)
        interior_colors.append(color)
        for row in range(frame["r1"] + 1, frame["r2"]):
            for column in range(frame["c1"] + 1, frame["c2"]):
                point = (row, column)
                if point in owned_interior:
                    raise ValueError("frame interiors overlap")
                owned_interior[point] = index

    if len(set(interior_colors)) != len(interior_colors):
        raise ValueError("frame interior colors must be pairwise distinct")

    for row in range(height):
        for column in range(width):
            value = grid[row][column]
            if value not in (0, 5) and (row, column) not in owned_interior:
                raise ValueError(
                    f"non-frame color {value} at {(row, column)} lies outside every frame interior"
                )

    return {
        "height": height,
        "width": width,
        "profile": _PROFILE_BY_SHAPE[shape],
        "frames": frames,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return complete-grammar violations; canonical and generated inputs pass."""
    del difficulty, meta
    try:
        _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    """The supported grammar is a conservative extension of all canonical inputs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str]:
    """Recover both exact axes from pixels, independent of draw bookkeeping."""
    parsed = _analyze(grid)
    focus = [
        frame
        for frame in parsed["frames"]
        if frame["height"] == 5 and frame["width"] == 5
    ]
    if len(focus) != 1:
        raise ValueError("generated grids must contain exactly one 5x5 density witness frame")
    count_to_density = {count: name for name, count in _DENSITY_COUNTS.items()}
    count = focus[0]["colored_count"]
    if count not in count_to_density:
        raise ValueError(f"5x5 witness has unrecognized colored-cell count {count}")
    return {
        "canvas_profile": parsed["profile"],
        "density": count_to_density[count],
    }


def _crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    points = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]
    if not points:
        return [[0]]
    r1 = min(row for row, _ in points)
    r2 = max(row for row, _ in points)
    c1 = min(column for _, column in points)
    c2 = max(column for _, column in points)
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _gallery(
    grid,
    *,
    frame_order: str = "row_major",
    narrow_padding: str = "canonical",
    crop_interiors: bool = False,
) -> list[list[int]]:
    parsed = _analyze(grid)
    frames = list(parsed["frames"])
    if frame_order == "left_to_right":
        frames.sort(key=lambda frame: (frame["c1"], frame["r1"]))
    elif frame_order != "row_major":
        raise ValueError(f"unknown frame order {frame_order!r}")

    interiors = [deepcopy(frame["interior"]) for frame in frames]
    if crop_interiors:
        interiors = [_crop_nonzero(interior) for interior in interiors]
    target_height = max(len(interior) for interior in interiors)

    panels: list[list[list[int]]] = []
    for index, interior in enumerate(interiors):
        source_height = len(interior)
        source_width = len(interior[0])
        is_narrow = source_width < 3
        if narrow_padding == "none":
            target_width = source_width
            left_pad = 0
        else:
            target_width = source_width + (1 if is_narrow else 0)
            if not is_narrow:
                left_pad = 0
            elif narrow_padding == "canonical":
                left_pad = 1 if index > 0 else 0
            elif narrow_padding == "always_leading":
                left_pad = 1
            elif narrow_padding == "always_trailing":
                left_pad = 0
            else:
                raise ValueError(f"unknown narrow padding policy {narrow_padding!r}")

        panel = full_grid(target_height, target_width, 0)
        for row in range(source_height):
            for column in range(source_width):
                panel[row][column + left_pad] = interior[row][column]
        panels.append(panel)

    return [
        [value for panel in panels for value in panel[row]]
        for row in range(target_height)
    ]


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket rule for contract tests."""
    return _gallery(grid)


def _rival_left_to_right(grid):
    return _gallery(grid, frame_order="left_to_right")


def _rival_raw_concat(grid):
    return _gallery(grid, narrow_padding="none")


def _rival_always_leading(grid):
    return _gallery(grid, narrow_padding="always_leading")


def _rival_always_trailing(grid):
    return _gallery(grid, narrow_padding="always_trailing")


def _rival_tight_crop(grid):
    return _gallery(grid, crop_interiors=True)


def _row_order_conflict(grid) -> bool:
    frames = _analyze(grid)["frames"]
    row_major = [(frame["r1"], frame["c1"]) for frame in frames]
    left_to_right = [
        (frame["r1"], frame["c1"])
        for frame in sorted(frames, key=lambda frame: (frame["c1"], frame["r1"]))
    ]
    return row_major != left_to_right


def _first_panel_is_narrow(grid) -> bool:
    frames = _analyze(grid)["frames"]
    return frames[0]["interior_width"] < 3


def _later_panel_is_narrow(grid) -> bool:
    frames = _analyze(grid)["frames"]
    return any(frame["interior_width"] < 3 for frame in frames[1:])


def _has_narrow_panel(grid) -> bool:
    return any(frame["interior_width"] < 3 for frame in _analyze(grid)["frames"])


def _has_preserved_blank_margin(grid) -> bool:
    for frame in _analyze(grid)["frames"]:
        interior = frame["interior"]
        points = [
            (row, column)
            for row, values in enumerate(interior)
            for column, value in enumerate(values)
            if value != 0
        ]
        if points and (
            min(row for row, _ in points) > 0
            or min(column for _, column in points) > 0
            or max(row for row, _ in points) < len(interior) - 1
            or max(column for _, column in points) < len(interior[0]) - 1
        ):
            return True
    return False


SEMANTIC_RIVALS: dict[str, Callable] = {
    "left_to_right": _rival_left_to_right,
    "raw_concat": _rival_raw_concat,
    "always_leading_narrow_pad": _rival_always_leading,
    "always_trailing_narrow_pad": _rival_always_trailing,
    "tight_crop_interiors": _rival_tight_crop,
}
CANONICAL_SHORTCUTS = {
    # All canonical frames happen to have the same row-major and physical-left
    # order; generated conflict profiles supply the missing counterexample.
    "left_to_right": _rival_left_to_right,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "row_major_not_left_to_right": _row_order_conflict,
    "first_narrow_panel_trails_pad": _first_panel_is_narrow,
    "later_narrow_panel_leads_pad": _later_panel_is_narrow,
    "narrow_panel_adds_column": _has_narrow_panel,
    "full_interior_not_tight_crop": _has_preserved_blank_margin,
}
WITNESS_RIVALS = {
    "row_major_not_left_to_right": ["left_to_right"],
    "first_narrow_panel_trails_pad": ["always_leading_narrow_pad"],
    "later_narrow_panel_leads_pad": ["always_trailing_narrow_pad"],
    "narrow_panel_adds_column": ["raw_concat"],
    "full_interior_not_tight_crop": ["tight_crop_interiors"],
}


def _pair_error(pair: Any, label: str) -> str | None:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return f"{label} must contain input/output grids"
    errors = self_check(pair["input"])
    if errors:
        return f"{label} input is unlawful: {'; '.join(errors)}"
    try:
        expected = rule_mirror(pair["input"])
    except (TypeError, ValueError) as exc:
        return f"{label} rule evaluation failed: {exc}"
    if pair["output"] != expected:
        return f"{label} output disagrees with the selected frame-gallery rule"
    return None


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a labeled lesson only when a named wrong rule remains viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        error = _pair_error(demo, f"demo {index}")
        if error:
            reasons.append(error)
    query_error = _pair_error(query, "query")
    if query_error:
        reasons.append(query_error)
    if reasons:
        return reasons

    truth = query["output"]
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            changes_query = competitor(query["input"]) != truth
        except (TypeError, ValueError) as exc:
            reasons.append(f"competitor {name!r} failed: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"demonstrations remain compatible with competitor {name!r}, "
                "which changes the query answer"
            )
    return reasons
