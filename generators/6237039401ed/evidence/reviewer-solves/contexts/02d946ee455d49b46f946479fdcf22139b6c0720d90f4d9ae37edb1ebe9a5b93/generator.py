"""Generator for additional_scaffolded:E5 (Solid Square Recolor).

The task recolors every gray cell that belongs to at least one complete 2x2
all-gray window.  Ordinary lessons include both complete target rectangles and
a gray near-miss in the same scene, so "replace every gray cell" and
"recolor only connected components of size four" are both invalid shortcuts.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "6237039401ed"
VERSION = "3.0.0"
TASK_ID = "6237039401ed"
RULE_HASH = "cb03ad6318a1"

SUMMARY = (
    "On a 0-background grid, find every color-5 cell that belongs to at "
    "least one completely filled 2x2 color-5 window and recolor that cell "
    "to color 1. Other cells, including gray L-trominoes, dominoes, and "
    "diagonal singleton pairs that complete no 2x2 window, stay unchanged. "
    "Generated targets include isolated 2x2 squares and overlapping-window "
    "rectangles (2x3, 3x2, and 3x3)."
)

INVARIANTS = [
    "background is 0 and the only foreground input color is 5",
    "ordinary draws contain 2..3 disconnected target components",
    "each target is a solid 2x2, 2x3, 3x2, or 3x3 rectangle",
    "every target cell belongs to at least one complete 2x2 color-5 window",
    "ordinary draws contain one gray distractor pattern with no complete 2x2",
    "targets and distractors are disconnected",
]

TARGET_SHAPES = (
    "isolated_2x2",
    "wide_2x3",
    "tall_3x2",
    "solid_3x3",
)
DISTRACTOR_SHAPES = (
    "l_tromino",
    "horizontal_domino",
    "vertical_domino",
    "diagonal_pair",
)
_TARGET_DIMS = {
    "isolated_2x2": (2, 2),
    "wide_2x3": (2, 3),
    "tall_3x2": (3, 2),
    "solid_3x3": (3, 3),
}
_PROFILE_FROM_DIMS = {value: key for key, value in _TARGET_DIMS.items()}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty draw 8..18", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "difficulty draw 8..18", "valid": "8..18"},
    "n_targets": {"type": "int", "default": "difficulty draw 2..3", "valid": "2..3"},
    "target_shape": {
        "type": "enum",
        "default": "sample_index schedule",
        "valid": "isolated_2x2|wide_2x3|tall_3x2|solid_3x3",
    },
    "distractor_shape": {
        "type": "enum",
        "default": "sample_index schedule",
        "valid": "l_tromino|horizontal_domino|vertical_domino|diagonal_pair",
    },
}


def _scheduled_choice(ctx, label, options, sample_index, offset=0):
    """Record a deterministic lesson schedule while still honoring overrides."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    scheduled = options[(sample_index + offset) % len(options)]
    return ctx.draw_choice(label, (scheduled,))


def _corner_anchor_ranges(h, w, shape_h, shape_w, slot):
    """Return inclusive anchor ranges in one corner around a two-cell moat."""
    mid_r, mid_c = h // 2, w // 2
    top = (0, mid_r - shape_h - 1)
    bottom = (mid_r + 1, h - shape_h)
    left = (0, mid_c - shape_w - 1)
    right = (mid_c + 1, w - shape_w)
    row_range = top if slot.startswith("top") else bottom
    col_range = left if slot.endswith("left") else right
    if row_range[1] < row_range[0] or col_range[1] < col_range[0]:
        raise ValueError(
            f"grid {h}x{w} cannot fit {shape_h}x{shape_w} target in {slot}"
        )
    return row_range, col_range


def _draw_distractor(grid, shape, slot, rng):
    h, w = len(grid), len(grid[0])
    row_range, col_range = _corner_anchor_ranges(h, w, 2, 2, slot)
    r0 = rng.randint(*row_range)
    c0 = rng.randint(*col_range)
    square = ((r0, c0), (r0, c0 + 1), (r0 + 1, c0), (r0 + 1, c0 + 1))
    if shape == "l_tromino":
        missing = rng.randrange(4)
        cells = [cell for index, cell in enumerate(square) if index != missing]
    elif shape == "horizontal_domino":
        row = rng.randrange(2)
        cells = [(r0 + row, c0), (r0 + row, c0 + 1)]
    elif shape == "vertical_domino":
        col = rng.randrange(2)
        cells = [(r0, c0 + col), (r0 + 1, c0 + col)]
    elif shape == "diagonal_pair":
        cells = [square[0], square[3]] if rng.randrange(2) == 0 else [square[1], square[2]]
    else:
        raise ValueError(f"unknown distractor_shape {shape!r}")
    for r, c in cells:
        if grid[r][c] != 0:
            raise ValueError("reserved distractor region overlaps a target")
        grid[r][c] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 8, 18)
    w = ctx.draw_int_diff("grid_w", 8, 18)
    n_targets = ctx.draw_int_diff("n_targets", 2, 3)
    target_shape = _scheduled_choice(
        ctx, "target_shape", TARGET_SHAPES, sample_index
    )
    distractor_shape = _scheduled_choice(
        ctx, "distractor_shape", DISTRACTOR_SHAPES, sample_index, offset=1
    )

    target_h, target_w = _TARGET_DIMS[target_shape]
    grid = full_grid(h, w, 0)
    placement_rng = ctx.draw_rng("target_placement")
    slots = ["top_left", "top_right", "bottom_left", "bottom_right"]
    placement_rng.shuffle(slots)
    distractor_slot = slots[0]
    for slot in slots[1 : 1 + n_targets]:
        row_range, col_range = _corner_anchor_ranges(
            h, w, target_h, target_w, slot
        )
        r = placement_rng.randint(*row_range)
        c = placement_rng.randint(*col_range)
        draw_rect(grid, r, c, target_h, target_w, 5)

    _draw_distractor(
        grid,
        distractor_shape,
        distractor_slot,
        ctx.draw_rng("distractor_placement_and_orientation"),
    )
    return grid


def _color5_components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] != 5 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            component = set()
            while stack:
                r, c = stack.pop()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (r + dr, c + dc)
                    if (
                        0 <= neighbor[0] < h
                        and 0 <= neighbor[1] < w
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == 5
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(component)
    return components


def _target_cells(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    cells = set()
    for r in range(h - 1):
        for c in range(w - 1):
            square = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
            if all(grid[rr][cc] == 5 for rr, cc in square):
                cells.update(square)
    return cells


def _solid_rectangle_profile(component):
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
    }
    if component != expected:
        return None
    return _PROFILE_FROM_DIMS.get((r1 - r0 + 1, c1 - c0 + 1))


def _classify_distractors(components):
    if not components:
        return None
    if len(components) == 1:
        component = components[0]
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        if len(component) == 3 and max(rows) - min(rows) == 1 and max(cols) - min(cols) == 1:
            return "l_tromino"
        if len(component) == 2 and len(set(rows)) == 1:
            return "horizontal_domino"
        if len(component) == 2 and len(set(cols)) == 1:
            return "vertical_domino"
        return "unknown"
    if len(components) == 2 and all(len(component) == 1 for component in components):
        cells = [next(iter(component)) for component in components]
        if abs(cells[0][0] - cells[1][0]) == 1 and abs(cells[0][1] - cells[1][1]) == 1:
            return "diagonal_pair"
    return "unknown"


def observe_overrides(grid):
    target_cells = _target_cells(grid)
    target_components = []
    distractor_components = []
    for component in _color5_components(grid):
        if component & target_cells:
            target_components.append(component)
        else:
            distractor_components.append(component)
    profiles = {_solid_rectangle_profile(component) for component in target_components}
    target_shape = next(iter(profiles)) if len(profiles) == 1 and None not in profiles else "unknown"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_targets": len(target_components),
        "target_shape": target_shape,
        "distractor_shape": _classify_distractors(distractor_components),
    }


def rule_mirror(grid):
    """Independent Python mirror used only for tests; Racket remains authority."""
    target_cells = _target_cells(grid)
    output = deepcopy(grid)
    for r, c in target_cells:
        output[r][c] = 1
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is not a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged or has zero width"]
    if any(value not in (0, 5) for row in grid for value in row):
        return ["input palette must be exactly a subset of {0, 5}"]

    errors = []
    target_cells = _target_cells(grid)
    components = _color5_components(grid)
    targets = [component for component in components if component & target_cells]
    distractors = [component for component in components if not component & target_cells]

    if not 2 <= len(targets) <= 3:
        errors.append(f"expected 2..3 target components, found {len(targets)}")
    profiles = []
    for component in targets:
        profile = _solid_rectangle_profile(component)
        if profile is None:
            errors.append(f"target component is not an allowed solid rectangle: {sorted(component)}")
            continue
        if not component <= target_cells:
            errors.append("target component has a gray tail outside every complete 2x2")
        profiles.append(profile)
    if profiles and len(set(profiles)) != 1:
        errors.append(f"target components use mixed profiles: {sorted(set(profiles))}")

    distractor_shape = _classify_distractors(distractors)
    if distractors and distractor_shape not in DISTRACTOR_SHAPES:
        errors.append(f"distractor grammar is malformed: {distractor_shape}")

    requested = (meta or {}).get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in AXES and observed.get(axis) != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, observed {observed.get(axis)!r}"
                )
    return errors


def mutation_fixtures():
    """Task-semantic impostors that self_check must reject."""
    no_target = full_grid(8, 8, 0)
    no_target[3][3] = no_target[3][4] = no_target[4][3] = 5

    single_target = full_grid(8, 8, 0)
    draw_rect(single_target, 0, 0, 2, 2, 5)

    target_with_tail = full_grid(8, 8, 0)
    draw_rect(target_with_tail, 0, 0, 2, 2, 5)
    draw_rect(target_with_tail, 5, 5, 2, 2, 5)
    target_with_tail[0][2] = 5

    mixed_target_profiles = full_grid(8, 8, 0)
    draw_rect(mixed_target_profiles, 0, 0, 2, 2, 5)
    draw_rect(mixed_target_profiles, 5, 5, 3, 3, 5)

    illegal_color = full_grid(8, 8, 0)
    draw_rect(illegal_color, 0, 0, 2, 2, 5)
    draw_rect(illegal_color, 6, 6, 2, 2, 5)
    illegal_color[3][3] = 7

    return [
        ("distractor_only_no_target", no_target),
        ("single_target_count_shortcut", single_target),
        ("target_with_nonparticipating_tail", target_with_tail),
        ("mixed_target_profiles", mixed_target_profiles),
        ("illegal_input_color", illegal_color),
    ]
