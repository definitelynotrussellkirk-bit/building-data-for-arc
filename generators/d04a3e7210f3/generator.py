"""Semantic generator for ARC task d04a3e7210f3.

The first singleton color in priority order 2, 3, 4, 6 selects a transform
of the blue template.  The vector from 7 to 9 translates the transformed
shape, which is stamped in cyan on otherwise empty landing cells.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d04a3e7210f3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ddbf085bcc82"
SUMMARY = (
    "Select the first singleton control in priority order 2,3,4,6; apply "
    "identity, clockwise rotation, top-bottom reflection, or 180-degree "
    "rotation to the largest blue component; translate it by vector 7->9; "
    "and stamp its empty in-bounds landing cells cyan."
)
EXAMPLES_NEEDED = 5

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "exact public input or a novel lawful control/template scene",
    },
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
CONTROL_PRIORITY = (2, 3, 4, 6)

INVARIANTS = [
    "one connected color-1 template of at least three cells",
    "exactly one color-7 marker and one color-9 marker",
    "two distinct singleton corner/control colors from 2..6",
    "the first singleton in priority order 2,3,4,6 selects the transform",
    "the complete transformed copy lands in-bounds and overlaps only background or the blue template",
    "every output adds at least three cyan cells",
]

# Public inputs represented compactly as
# (height, width, template cells, singleton (row,col,color) triples).
_PUBLIC_SCENES = (
    (10, 12, ((1, 1), (2, 1), (2, 2)),
     ((0, 10, 2), (9, 0, 5), (7, 8, 7), (8, 10, 9))),
    (12, 13, ((1, 1), (2, 1), (3, 1), (3, 2)),
     ((0, 0, 4), (11, 12, 3), (8, 5, 7), (10, 7, 9))),
    (11, 13, ((2, 2), (2, 3), (2, 4), (3, 3)),
     ((0, 12, 4), (10, 0, 6), (8, 8, 7), (10, 10, 9))),
    (12, 13, ((1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
     ((0, 12, 5), (11, 0, 6), (8, 8, 7), (10, 10, 9))),
    (11, 13, ((2, 2), (2, 4), (3, 2), (3, 3), (3, 4)),
     ((0, 11, 3), (10, 0, 4), (8, 8, 7), (9, 10, 9))),
)


def _public_grid(scene):
    height, width, template, singletons = scene
    grid = full_grid(height, width, 0)
    for row, col in template:
        grid[row][col] = 1
    for row, col, color in singletons:
        grid[row][col] = color
    return grid


_PUBLIC_INPUTS = tuple(_public_grid(scene) for scene in _PUBLIC_SCENES)


def _normalize(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _components_of_color(grid, color):
    remaining = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = [start]
        stack = [start]
        while stack:
            row, col = stack.pop()
            for point in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    component.append(point)
                    stack.append(point)
        result.append(tuple(sorted(component)))
    return tuple(sorted(result, key=lambda cells: (-len(cells), cells[0])))


def _transform(cells, control):
    normalized = _normalize(cells)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1
    if control == 2:
        transformed = normalized
    elif control == 3:
        transformed = tuple((col, height - 1 - row) for row, col in normalized)
    elif control == 4:
        transformed = tuple((height - 1 - row, col) for row, col in normalized)
    else:
        transformed = tuple(
            (height - 1 - row, width - 1 - col)
            for row, col in normalized
        )
    return _normalize(transformed)


def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty sequences"]
    if len({len(row) for row in grid}) != 1:
        return ["grid must be rectangular"]
    errors = []
    if not (8 <= len(grid) <= 30 and 8 <= len(grid[0]) <= 30):
        errors.append("grid dimensions must be 8..30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    return errors


def _analyze(grid):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}
    positions = {
        color: tuple(
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if grid[row][col] == color
        )
        for color in range(10)
    }
    components = _components_of_color(grid, 1)
    if len(components) != 1 or len(components[0]) < 3:
        errors.append("input must contain one connected blue template of size >=3")
    if len(positions[7]) != 1 or len(positions[9]) != 1:
        errors.append("input must contain exactly one marker each of colors 7 and 9")
    controls = tuple(
        color for color in CONTROL_PRIORITY if len(positions[color]) == 1
    )
    singleton_scene_colors = tuple(
        color for color in (2, 3, 4, 5, 6) if len(positions[color]) == 1
    )
    if not controls:
        errors.append("input must expose a singleton control in priority 2,3,4,6")
    if len(singleton_scene_colors) != 2:
        errors.append("input must contain exactly two distinct singleton scene colors")
    if any(
        positions[color] and len(positions[color]) != 1
        for color in (2, 3, 4, 5, 6)
    ):
        errors.append("scene/control colors 2..6 must be absent or singleton")
    facts = None
    if not errors:
        control = controls[0]
        template = components[0]
        top = min(row for row, _ in template)
        left = min(col for _, col in template)
        start, finish = positions[7][0], positions[9][0]
        vector = (finish[0] - start[0], finish[1] - start[1])
        shape = _transform(template, control)
        landing = tuple(
            (top + vector[0] + row, left + vector[1] + col)
            for row, col in shape
        )
        if vector == (0, 0):
            errors.append("marker vector must be nonzero")
        if any(
            not (0 <= row < len(grid) and 0 <= col < len(grid[0]))
            for row, col in landing
        ):
            errors.append("complete transformed template must land in bounds")
        elif any(grid[row][col] not in (0, 1) for row, col in landing):
            errors.append(
                "transformed template may overlap only background or the blue template"
            )
        elif sum(grid[row][col] == 0 for row, col in landing) < 3:
            errors.append("transformed template must add at least three cyan cells")
        if not errors:
            profile = None
            frozen = tuple(map(tuple, grid))
            for index, public in enumerate(_PUBLIC_INPUTS):
                if frozen == tuple(map(tuple, public)):
                    profile = f"public_{index + 1}"
                    break
            facts = {
                "control": control,
                "distractor": next(
                    color for color in singleton_scene_colors if color != control
                ),
                "template": template,
                "template_size": len(template),
                "vector": vector,
                "landing": landing,
                "canonical_profile": profile,
                "scene_family": "linked" if profile else "generalized",
            }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["scene_family"]}


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    return facts["canonical_profile"] or (
        f"generalized:{facts['control']}:{facts['distractor']}:"
        f"{facts['template_size']}:{facts['vector']}"
    )


def rule_mirror(grid):
    """Independent Python mirror for focused parity tests."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = copy.deepcopy(grid)
    for row, col in analysis["facts"]["landing"]:
        if output[row][col] == 0:
            output[row][col] = 8
    return output


def _random_walk(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(sorted(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((row + dr, col + dc))
    return _normalize(tuple(cells))


def _generalized_dimensions(rng, band):
    if band == "easy":
        return rng.randint(10, 13), rng.randint(11, 14)
    if band == "hard":
        return rng.randint(16, 24), rng.randint(16, 24)
    return rng.randint(12, 18), rng.randint(13, 20)


def _distractor_choices(control):
    return {
        2: (3, 4, 5, 6),
        3: (4, 5, 6),
        4: (5, 6),
        6: (5,),
    }[control]


def _build_generalized(rng, band):
    height, width = _generalized_dimensions(rng, band)
    for _attempt in range(120):
        control = rng.choice(CONTROL_PRIORITY)
        distractor = rng.choice(_distractor_choices(control))
        size = rng.randint(3, 4 if band == "easy" else 7)
        template = _random_walk(rng, size)
        shape = _transform(template, control)
        th = max(row for row, _ in template) + 1
        tw = max(col for _, col in template) + 1
        sh = max(row for row, _ in shape) + 1
        sw = max(col for _, col in shape) + 1
        vectors = [
            (dr, dc)
            for dr in range(-5 if band == "hard" else -3, 6 if band == "hard" else 4)
            for dc in range(-5 if band == "hard" else -3, 6 if band == "hard" else 4)
            if (dr, dc) != (0, 0)
        ]
        rng.shuffle(vectors)
        placed = None
        for dr, dc in vectors:
            row_min = max(1, -dr)
            col_min = max(1, -dc)
            row_max = min(height - th - 1, height - sh - dr - 1)
            col_max = min(width - tw - 1, width - sw - dc - 1)
            if row_min <= row_max and col_min <= col_max:
                top = rng.randint(row_min, row_max)
                left = rng.randint(col_min, col_max)
                placed = (top, left, dr, dc)
                break
        if placed is None:
            continue
        top, left, dr, dc = placed
        grid = full_grid(height, width, 0)
        template_cells = {(top + row, left + col) for row, col in template}
        landing = {
            (top + dr + row, left + dc + col) for row, col in shape
        }
        for row, col in template_cells:
            grid[row][col] = 1
        forbidden = template_cells | landing
        marker_pairs = [
            ((row, col), (row + dr, col + dc))
            for row in range(height)
            for col in range(width)
            if 0 <= row + dr < height
            and 0 <= col + dc < width
            and (row, col) not in forbidden
            and (row + dr, col + dc) not in forbidden
        ]
        if not marker_pairs:
            continue
        start, finish = rng.choice(marker_pairs)
        grid[start[0]][start[1]] = 7
        grid[finish[0]][finish[1]] = 9
        forbidden |= {start, finish}
        boundary = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)
            if (row, col) not in forbidden
        ]
        if len(boundary) < 2:
            continue
        first = rng.choice(boundary)
        boundary.remove(first)
        second = rng.choice(boundary)
        grid[first[0]][first[1]] = control
        grid[second[0]][second[1]] = distractor
        analysis = _analyze(grid)
        if not analysis["errors"] and analysis["facts"]["scene_family"] == "generalized":
            return grid
    raise RuntimeError("could not construct generalized transform-vector scene")


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
    family = ctx.draw_choice("scene_family", SCENE_FAMILIES)
    rng = ctx.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        copy.deepcopy(rng.choice(_PUBLIC_INPUTS))
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["scene_family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['scene_family']}"
                ]
            )
        )
    return grid
