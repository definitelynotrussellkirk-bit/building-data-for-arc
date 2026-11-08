"""Generator for 14b:m97 — sort cropped objects by width and pack.

The output rule is deterministic: find the three monochrome 4-connected
objects, crop each to its bounding box, sort the crops by
``(bbox_width, bbox_height, color)``, then pack them left-to-right with one
background column between crops.  Each crop is vertically centered inside the
maximum crop height.

The default distribution keeps a large official-profile prior while adding
procedural witnesses that break position, color-only, width-only-tie, and
top-alignment shortcuts.
"""
from __future__ import annotations

from itertools import permutations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "7b3c2eaee231"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "afe9721b6609"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.30

SUMMARY = (
    "Three separated monochrome objects on background 0. Crop each object, "
    "sort by (bbox width, bbox height, color), and horizontally center-pack "
    "the crops with one-column gaps."
)

INVARIANTS = [
    "background is 0",
    "exactly three 4-connected monochrome objects in distinct colors",
    "objects do not 4-touch",
    "input reading order is not the crop sort order",
    "default draws cover width-primary and width/height/color tie-break lessons",
]

CANVAS_PROFILES = ("9x13", "9x14", "10x15", "10x16")
LESSON_PROFILES = ("width_primary", "tie_breaks")
SHAPE_FAMILIES = ("canonical", "procedural")

# Three consecutive demonstrations must distinguish the real rule from every
# named shortcut.  Every odd slot is an equal-width procedural tie case with a
# >=2-row height gap.  The even slots retain both exact official profile types
# plus the procedural distinct-width branch.  Every length-three sliding
# window therefore contains a decisive procedural tie example, while ordinary
# draws still cover every declared axis combination.
_SCHEDULE = (
    ("width_primary", "canonical"),
    ("tie_breaks", "procedural"),
    ("tie_breaks", "canonical"),
    ("tie_breaks", "procedural"),
    ("width_primary", "procedural"),
    ("tie_breaks", "procedural"),
    ("tie_breaks", "canonical"),
    ("tie_breaks", "procedural"),
)
SCHEDULE_PROFILES = tuple(
    f"slot{index}:{lesson}:{family}"
    for index, (lesson, family) in enumerate(_SCHEDULE)
)

AXES = {
    "canvas": {
        "type": "str",
        "default": "rng official dimension profile",
        "valid": "|".join(CANVAS_PROFILES),
    },
    "lesson_profile": {
        "type": "str",
        "default": "rng width-primary or tie-break witness",
        "valid": "|".join(LESSON_PROFILES),
    },
    "shape_family": {
        "type": "str",
        "default": "rng official-profile or procedural morphology",
        "valid": "|".join(SHAPE_FAMILIES),
    },
}

# Every override combination is supported. Unknown keys are rejected before a
# GenCtx is built so stale or typoed axis names cannot appear to pass.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

Shape = tuple[tuple[int, int], ...]


def _shape(*rows: str) -> Shape:
    return tuple(
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == "1"
    )


# Exact normalized object bitmaps from all five official inputs.  These are a
# prior, not the whole grammar: procedural draws expand morphology while the
# official profiles keep the training distribution anchored to the examples.
_A2 = _shape("11", "11", "10")
_L_BOTTOM = _shape("100", "100", "111")
_S4 = _shape("1100", "0111", "0001")
_T = _shape("111", "010", "010")
_H = _shape("101", "101", "111")
_P4 = _shape("001", "011", "010", "110")
_L_TOP = _shape("111", "100", "100")
_C6 = _shape("111", "100", "110")

_CANONICAL_WIDTH_PROFILES: tuple[tuple[Shape, Shape, Shape], ...] = (
    (_A2, _L_BOTTOM, _S4),
)
_CANONICAL_TIE_PROFILES: tuple[tuple[Shape, Shape, Shape], ...] = (
    (_T, _H, _P4),
    (_A2, _L_TOP, _C6),
    (_H, _T, _S4),
    (_C6, _H, _P4),
)

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_signature(cells: Iterable[tuple[int, int]]) -> Shape:
    return _normalize(cells)


def _profile_signature(shapes: Iterable[Shape]) -> tuple[Shape, ...]:
    return tuple(sorted(_shape_signature(shape) for shape in shapes))


_CANONICAL_SIGNATURES = frozenset(
    _profile_signature(profile)
    for profile in (*_CANONICAL_WIDTH_PROFILES, *_CANONICAL_TIE_PROFILES)
)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _shape_size(shape: Shape) -> tuple[int, int]:
    r1, c1, r2, c2 = _bbox(shape)
    return r2 - r1 + 1, c2 - c1 + 1


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []
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
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1, c1, r2, c2 = _bbox(cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "top": r1,
                    "left": c1,
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                }
            )
    return components


def canonical_profile_signature(
    grid: list[list[int]],
) -> tuple[Shape, ...] | None:
    """Return the linked normalized bitmap profile for a valid 3-object grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    components = _components(grid)
    if len(components) != 3:
        return None
    return tuple(
        sorted(
            _shape_signature(component["cells"])  # type: ignore[arg-type]
            for component in components
        )
    )


def _lesson_from_components(components: list[dict[str, object]]) -> str:
    widths = [int(component["width"]) for component in components]
    return "width_primary" if len(set(widths)) == len(widths) else "tie_breaks"


def observe_overrides(grid: list[list[int]]) -> dict[str, str]:
    """Recover every declared axis directly from the returned grid."""
    components = _components(grid)
    signature = canonical_profile_signature(grid)
    return {
        "canvas": f"{len(grid)}x{len(grid[0])}",
        "lesson_profile": _lesson_from_components(components),
        "shape_family": (
            "canonical" if signature in _CANONICAL_SIGNATURES else "procedural"
        ),
    }


def _validate_override_keys(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis name(s): {', '.join(unknown)}")


def _random_exact_bbox_shape(rng, height: int, width: int) -> Shape:
    """Connected random bitmap that touches all four sides of its bbox."""
    if height < 2 or width < 2:
        raise ValueError("procedural object bboxes must be at least 2x2")

    if rng.choice((False, True)):
        start = (0, 0)
        row_step, col_step = 1, 1
    else:
        start = (0, width - 1)
        row_step, col_step = 1, -1

    steps = [(row_step, 0)] * (height - 1) + [(0, col_step)] * (width - 1)
    rng.shuffle(steps)
    cells = {start}
    r, c = start
    for dr, dc in steps:
        r += dr
        c += dc
        cells.add((r, c))

    area = height * width
    target = rng.randint(len(cells), max(len(cells), area - 1))
    while len(cells) < target:
        frontier = [
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _CARDINAL
            if 0 <= r + dr < height
            and 0 <= c + dc < width
            and (r + dr, c + dc) not in cells
        ]
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return _normalize(cells)


def _procedural_shapes(lesson_profile: str, rng) -> tuple[Shape, Shape, Shape]:
    # Every procedural profile uses a >=2-row height difference.  Official
    # examples leave top alignment answer-equivalent because their heights
    # differ by at most one; these generated rows are the necessary witness
    # for the oracle's vertical-centering policy.
    if lesson_profile == "width_primary":
        specs = ((3, 2), (5, 3), (3, 4))
    else:
        specs = ((2, 3), (2, 3), (5, 3))

    for _ in range(80):
        shapes: list[Shape] = []
        for height, width in specs:
            shape = _random_exact_bbox_shape(rng, height, width)
            while shape in shapes:
                shape = _random_exact_bbox_shape(rng, height, width)
            shapes.append(shape)
        profile = tuple(shapes)
        if _profile_signature(profile) not in _CANONICAL_SIGNATURES:
            return profile  # type: ignore[return-value]
    raise ValueError("could not draw a non-canonical procedural shape profile")


def _select_shapes(
    lesson_profile: str, shape_family: str, rng, *, max_packed_width: int
):
    if shape_family == "procedural":
        return _procedural_shapes(lesson_profile, rng)
    profiles = (
        _CANONICAL_WIDTH_PROFILES
        if lesson_profile == "width_primary"
        else _CANONICAL_TIE_PROFILES
    )
    fitting = [
        profile
        for profile in profiles
        if sum(_shape_size(shape)[1] for shape in profile) + 2 <= max_packed_width
    ]
    if not fitting:
        raise ValueError("no canonical shape profile fits the selected canvas")
    return tuple(rng.choice(fitting))


def _assign_colors(shapes: tuple[Shape, Shape, Shape], rng):
    palette = sorted(random_palette(rng, 3))
    base_keys = []
    for index, shape in enumerate(shapes):
        height, width = _shape_size(shape)
        base_keys.append((width, height, index))
    ordered = [index for _width, _height, index in sorted(base_keys)]

    colors: list[int | None] = [None, None, None]
    widths = [key[0] for key in base_keys]
    if len(set(widths)) == 3:
        # Width order sees high, low, middle colors: color-only sorting fails.
        pattern = (palette[2], palette[0], palette[1])
    else:
        # The largest width/height bucket gets the smallest color, so height
        # must precede color; equal (width,height) objects still require color.
        pattern = (palette[1], palette[2], palette[0])
    for index, color in zip(ordered, pattern):
        colors[index] = color

    items = []
    for shape, color in zip(shapes, colors):
        assert color is not None
        height, width = _shape_size(shape)
        items.append(
            {
                "shape": shape,
                "color": color,
                "height": height,
                "width": width,
                "sort_key": (width, height, color),
            }
        )
    return items


def _reading_order(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return sorted(
        (
            int(component["top"]),
            int(component["left"]),
            int(component["color"]),
        )
        for component in _components(grid)
    )


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _component_crop(component: dict[str, object]) -> list[list[int]]:
    height = int(component["height"])
    width = int(component["width"])
    top = int(component["top"])
    left = int(component["left"])
    color = int(component["color"])
    crop = full_grid(height, width, 0)
    for r, c in component["cells"]:  # type: ignore[assignment]
        crop[r - top][c - left] = color
    return crop


def _render_components(
    grid: list[list[int]],
    *,
    order: str = "official",
    vertical: str = "center",
) -> list[list[int]]:
    """Pure Python audit mirror and deliberately wrong comparison rules."""
    components = sorted(
        _components(grid),
        key=lambda component: (
            int(component["top"]),
            int(component["left"]),
            int(component["color"]),
        ),
    )
    if len(components) != 3:
        return _copy_grid(grid)

    if order == "official":
        components.sort(
            key=lambda component: (
                int(component["width"]),
                int(component["height"]),
                int(component["color"]),
            )
        )
    elif order == "reading":
        pass
    elif order == "color":
        components.sort(key=lambda component: int(component["color"]))
    elif order == "width":
        # Python's stable sort intentionally leaves equal-width crops in input
        # reading order: this is the plausible but wrong width-only shortcut.
        components.sort(key=lambda component: int(component["width"]))
    elif order == "width_color":
        components.sort(
            key=lambda component: (
                int(component["width"]),
                int(component["color"]),
            )
        )
    else:
        raise ValueError(f"unknown crop order: {order}")

    out_h = max(int(component["height"]) for component in components)
    out_w = sum(int(component["width"]) for component in components) + 2
    output = full_grid(out_h, out_w, 0)
    left = 0
    for component in components:
        crop = _component_crop(component)
        top = 0 if vertical == "top" else (out_h - len(crop)) // 2
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                output[top + r][left + c] = value
        left += len(crop[0]) + 1
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for semantic/test auditing."""
    return _render_components(grid)


def _rival_reading_order(grid: list[list[int]]) -> list[list[int]]:
    return _render_components(grid, order="reading")


def _rival_color_order(grid: list[list[int]]) -> list[list[int]]:
    return _render_components(grid, order="color")


def _rival_width_only(grid: list[list[int]]) -> list[list[int]]:
    return _render_components(grid, order="width")


def _rival_width_then_color(grid: list[list[int]]) -> list[list[int]]:
    return _render_components(grid, order="width_color")


def _rival_top_align(grid: list[list[int]]) -> list[list[int]]:
    return _render_components(grid, vertical="top")


def _lawful(grid: list[list[int]]) -> bool:
    return not self_check(grid)


def _width_primary_witness(grid: list[list[int]]) -> bool:
    components = _components(grid)
    return (
        _lawful(grid)
        and len({int(component["width"]) for component in components}) == 3
        and _rival_color_order(grid) != rule_mirror(grid)
    )


def _height_tie_break_witness(grid: list[list[int]]) -> bool:
    components = _components(grid)
    has_height_tie_break = any(
        int(a["width"]) == int(b["width"])
        and int(a["height"]) != int(b["height"])
        for index, a in enumerate(components)
        for b in components[index + 1 :]
    )
    return (
        _lawful(grid)
        and has_height_tie_break
        and _rival_width_then_color(grid) != rule_mirror(grid)
    )


def _color_tie_break_witness(grid: list[list[int]]) -> bool:
    components = _components(grid)
    has_color_tie_break = any(
        int(a["width"]) == int(b["width"])
        and int(a["height"]) == int(b["height"])
        for index, a in enumerate(components)
        for b in components[index + 1 :]
    )
    return (
        _lawful(grid)
        and has_color_tie_break
        and _rival_width_only(grid) != rule_mirror(grid)
    )


def _reading_order_witness(grid: list[list[int]]) -> bool:
    return _lawful(grid) and _rival_reading_order(grid) != rule_mirror(grid)


def _vertical_centering_witness(grid: list[list[int]]) -> bool:
    components = _components(grid)
    heights = [int(component["height"]) for component in components]
    return (
        _lawful(grid)
        and max(heights, default=0) - min(heights, default=0) >= 2
        and _rival_top_align(grid) != rule_mirror(grid)
    )


def strict_canonical_like(grid: list[list[int]]) -> list[str]:
    """Exact task-local official-profile manifold, not a coarse dimension tuple."""
    errors = self_check(grid)
    if errors:
        return errors
    if f"{len(grid)}x{len(grid[0])}" not in CANVAS_PROFILES:
        return ["canvas is outside the official dimension set"]
    if canonical_profile_signature(grid) not in _CANONICAL_SIGNATURES:
        return ["linked normalized object bitmaps are not an official profile"]
    return []


SEMANTIC_RIVALS = {
    "input_reading_order": _rival_reading_order,
    "color_only_order": _rival_color_order,
    "width_only_reading_ties": _rival_width_only,
    "width_then_color_skips_height": _rival_width_then_color,
    "top_align_crops": _rival_top_align,
}

SEMANTIC_WITNESSES = {
    "width_primary_signal": _width_primary_witness,
    "height_tie_break_signal": _height_tie_break_witness,
    "color_tie_break_signal": _color_tie_break_witness,
    "input_reading_order_refuted": _reading_order_witness,
    "vertical_centering_required": _vertical_centering_witness,
}

WITNESS_RIVALS = {
    "width_primary_signal": ["color_only_order"],
    "height_tie_break_signal": ["width_then_color_skips_height"],
    "color_tie_break_signal": ["width_only_reading_ties"],
    "input_reading_order_refuted": ["input_reading_order"],
    "vertical_centering_required": ["top_align_crops"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# All official rows are top-alignment ambiguous: crop heights differ by at
# most one, so floor-centering places every crop at row zero.  Generated
# procedural rows are the required counterexample.
CANONICAL_SHORTCUTS = {"top_align_crops": _rival_top_align}


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic four-slot lesson schedule to the gate."""
    del seed, difficulty
    index = int(sample_index) % len(_SCHEDULE)
    lesson, family = _SCHEDULE[index]
    return f"slot{index}:{lesson}:{family}"


def lesson_identifiable(demos, query) -> list[str]:
    """Verify demos eliminate every named wrong rule for this query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the task grammar: {errors[0]}")
        elif rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} disagrees with the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the task grammar: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the canonical rule")

    if not any(_vertical_centering_witness(demo["input"]) for demo in demos):
        reasons.append("demonstrations lack a vertical-centering counterexample")
    if not any(_height_tie_break_witness(demo["input"]) for demo in demos):
        reasons.append("demonstrations lack a width/height tie-break counterexample")
    if not any(_color_tie_break_witness(demo["input"]) for demo in demos):
        reasons.append("demonstrations lack a final color tie-break counterexample")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons


def _paint_layout(grid, items, rng) -> None:
    h, w = len(grid), len(grid[0])
    sorted_indices = tuple(
        sorted(range(3), key=lambda index: items[index]["sort_key"])
    )
    anti_orders = [order for order in permutations(range(3)) if order != sorted_indices]
    input_order = rng.choice(anti_orders)

    widths = [int(items[index]["width"]) for index in input_order]
    minimum_width = sum(widths) + 2
    slack = (w - 2) - minimum_width
    if slack < 0:
        raise ValueError("object crops do not fit the selected canvas")

    # Split horizontal slack across leading/trailing margins and the two gaps.
    allocations = [0, 0, 0, 0]
    for _ in range(slack):
        allocations[rng.randrange(4)] += 1
    left = 1 + allocations[0]

    top_patterns = ((1, 1, 1), (1, 1, 2), (1, 2, 2), (1, 2, 3))
    valid_patterns = [
        pattern
        for pattern in top_patterns
        if all(
            pattern[position] + int(items[index]["height"]) <= h - 1
            for position, index in enumerate(input_order)
        )
    ]
    tops = rng.choice(valid_patterns or [(1, 1, 1)])

    for position, index in enumerate(input_order):
        obj = items[index]
        paint_at(
            grid,
            tops[position],
            left,
            obj["shape"],
            int(obj["color"]),
        )
        if position < 2:
            left += int(obj["width"]) + 1 + allocations[position + 1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        canvas_options = ("9x13", "9x13", "9x14", "10x15", "10x16")
    elif difficulty == "hard":
        canvas_options = ("9x13", "9x14", "10x15", "10x16", "10x16")
    else:
        canvas_options = CANVAS_PROFILES

    # Every band keeps every canvas reachable; duplicated options only bias
    # dimensions by difficulty and never narrow the override contract.
    canvas = ctx.draw_choice("canvas", canvas_options)
    scheduled_lesson, scheduled_family = _SCHEDULE[
        int(sample_index) % len(_SCHEDULE)
    ]
    lesson_profile = ctx.draw_choice(
        "lesson_profile",
        LESSON_PROFILES
        if overrides.get("lesson_profile") is not None
        else (scheduled_lesson,),
    )
    shape_family = ctx.draw_choice(
        "shape_family",
        SHAPE_FAMILIES
        if overrides.get("shape_family") is not None
        else (scheduled_family,),
    )
    h, w = (int(value) for value in canvas.split("x"))

    shapes = _select_shapes(
        lesson_profile,
        shape_family,
        ctx.draw_rng("shapes"),
        max_packed_width=w - 2,
    )
    items = _assign_colors(shapes, ctx.draw_rng("colors"))
    grid = full_grid(h, w, 0)
    _paint_layout(grid, items, ctx.draw_rng("layout"))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid crop-sort scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "canvas": canvas,
        "lesson_profile": lesson_profile,
        "shape_family": shape_family,
    }
    if observed != requested:
        raise ValueError(f"axis realization mismatch: requested={requested}, observed={observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-local three-object input grammar."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]

    errors: list[str] = []
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC limits: {len(grid)}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three objects, found {len(components)}")
    colors = [int(component["color"]) for component in components]
    if len(colors) != len(set(colors)):
        errors.append("objects must use distinct colors")

    owner: dict[tuple[int, int], int] = {}
    for index, component in enumerate(components):
        for cell in component["cells"]:  # type: ignore[assignment]
            owner[cell] = index
    touching = False
    for (r, c), index in owner.items():
        for dr, dc in _CARDINAL:
            other = owner.get((r + dr, c + dc))
            if other is not None and other != index:
                touching = True
                break
        if touching:
            break
    if touching:
        errors.append("different objects must not 4-touch")

    sort_keys = [
        (
            int(component["width"]),
            int(component["height"]),
            int(component["color"]),
        )
        for component in components
    ]
    if len(sort_keys) != len(set(sort_keys)):
        errors.append("crop sort keys must be deterministic")
    packed_width = sum(int(component["width"]) for component in components) + max(
        0, len(components) - 1
    )
    packed_height = max(
        (int(component["height"]) for component in components),
        default=0,
    )
    if packed_width > 30 or packed_height > 30:
        errors.append(f"packed output would exceed ARC limits: {packed_height}x{packed_width}")
    return errors
