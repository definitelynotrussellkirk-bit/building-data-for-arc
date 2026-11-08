"""Input sampler for task 75422b6b0a4d: flood each walled chamber.

The selected Racket authority treats every color 1..4 cell as a seed.  From
that seed it flood-fills through cells whose original value is either 0 or the
seed color; every other color is a barrier.  This sampler constructs 2..4
wall-separated chambers with exactly one seed and at least one zero per
chamber.  A three-slot schedule retains canonical rectangular examples while
also teaching partial and stepped wall boundaries that refute the strongest
complete-wall-line shortcut fitting the public examples.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75422b6b0a4d"
TASK_ID = GENERATOR_ID
RULE_HASH = "c8f68c67587f"
VERSION = "3.1.0"
SUMMARY = (
    "A closed wall of one color 5..9 partitions a 7..18 by 8..20 grid into "
    "2..4 connected chambers. Each chamber contains exactly one seed color "
    "1..4 and at least one zero. The selected rule floods every zero reachable "
    "from a seed without crossing another color. Scheduled examples mix "
    "canonical straight partitions with stepped and partial dividers; the "
    "shortcut-witness and broad slots both carry those decisive contrasts so "
    "any query rotation of a four-pair lesson remains identifiable."
)

INVARIANTS = [
    "one connected wall network of a single color 5..9 includes the full border",
    "the non-wall cells form exactly 2..4 four-connected chambers",
    "each chamber contains exactly one seed color 1..4 and at least one zero",
    "every advertised override is exact, pixel-observable, and constructive in every band",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-slot canonical/shortcut/broad schedule",
        "valid": "7..18",
    },
    "grid_w": {
        "type": "int",
        "default": "three-slot canonical/shortcut/broad schedule",
        "valid": "8..20",
    },
    "wall_color": {
        "type": "color",
        "default": "canonical 5; shortcut slot cycles 6..9; broad cycles 5..9",
        "valid": "5..9",
    },
    "n_rooms": {
        "type": "int",
        "default": "canonical 4; shortcut 3; broad cycles 2..4",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical_anchor", "shortcut_witness", "broad")
MIN_STRICT_FRAC = 0.20

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_INT_DOMAINS = {
    "grid_h": range(7, 19),
    "grid_w": range(8, 21),
    "wall_color": range(5, 10),
    "n_rooms": range(2, 5),
}
_CANONICAL_PROFILES = {(7, 8, 6), (7, 9, 6), (7, 10, 6)}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in _INT_DOMAINS[name]:
            legal = _INT_DOMAINS[name]
            raise ValueError(f"{name}={value!r} outside [{min(legal)}, {max(legal)}]")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every three consecutive defaults contain one example of each profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _draw_axis(ctx, name, *, default=None, favored=()):
    legal = _INT_DOMAINS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, min(legal), max(legal))
    if default is not None:
        return ctx.draw_choice(name, (default,))
    options = list(legal) + list(favored) * 4
    return ctx.draw_choice(name, options)


def _neighbors(point, height, width):
    row, col = point
    for dr, dc in _DIR4:
        nr, nc = row + dr, col + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield nr, nc


def _components_where(grid, predicate):
    height = len(grid)
    width = len(grid[0])
    pending = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if predicate(grid[row][col])
    }
    components = []
    while pending:
        start = min(pending)
        pending.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            point = queue.popleft()
            for nxt in _neighbors(point, height, width):
                if nxt in pending:
                    pending.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    components.sort(key=min)
    return components


def _open_components(grid, wall_color):
    return _components_where(grid, lambda value: value != wall_color)


def _draw_border(grid, wall_color):
    height = len(grid)
    width = len(grid[0])
    for col in range(width):
        grid[0][col] = wall_color
        grid[height - 1][col] = wall_color
    for row in range(height):
        grid[row][0] = wall_color
        grid[row][width - 1] = wall_color


def _vertical_partition(height, width, wall_color, n_rooms, *, irregular, rng):
    """Draw a top-to-bottom primary divider and optional secondary split."""
    grid = full_grid(height, width, 0)
    _draw_border(grid, wall_color)

    if irregular:
        # Both columns retain at least two floor columns on each side at the
        # minimum 8-wide canvas.  The horizontal bridge makes a gap-free step.
        low = rng.choice(tuple(range(3, width - 4)))
        pair = (low, low + 1)
        if rng.choice((False, True)):
            pair = pair[::-1]
        top_col, bottom_col = pair
        pivot = rng.choice(tuple(range(2, height - 2)))
        primary = set()
        for row in range(0, pivot + 1):
            primary.add((row, top_col))
        for col in range(min(pair), max(pair) + 1):
            primary.add((pivot, col))
        for row in range(pivot, height):
            primary.add((row, bottom_col))
    else:
        divider_col = rng.choice(tuple(range(3, width - 3)))
        primary = {(row, divider_col) for row in range(height)}

    for row, col in primary:
        grid[row][col] = wall_color

    if n_rooms >= 3:
        split_row = rng.choice(tuple(range(3, height - 3)))
        if n_rooms == 4:
            for col in range(width):
                grid[split_row][col] = wall_color
        else:
            path_cols = sorted(col for row, col in primary if row == split_row)
            if not path_cols:
                raise RuntimeError("primary divider unexpectedly misses split row")
            if rng.choice(("left", "right")) == "left":
                for col in range(0, max(path_cols) + 1):
                    grid[split_row][col] = wall_color
            else:
                for col in range(min(path_cols), width):
                    grid[split_row][col] = wall_color

    components = _open_components(grid, wall_color)
    if len(components) != n_rooms or any(len(component) < 2 for component in components):
        raise RuntimeError(
            f"constructive partition failed: wanted {n_rooms} rooms, got "
            f"{[len(component) for component in components]}"
        )
    return grid


def _partition_grid(height, width, wall_color, n_rooms, *, irregular, orientation, rng):
    if orientation == "vertical":
        return _vertical_partition(
            height, width, wall_color, n_rooms, irregular=irregular, rng=rng
        )
    transposed = _vertical_partition(
        width, height, wall_color, n_rooms, irregular=irregular, rng=rng
    )
    return [list(row) for row in zip(*transposed)]


def _place_seeds(grid, wall_color, rng, *, canonical_positions=False):
    components = _open_components(grid, wall_color)
    colors = list(range(1, len(components) + 1))
    if not canonical_positions:
        rng.shuffle(colors)
    for component, color in zip(components, colors):
        cells = sorted(component)
        position = cells[0] if canonical_positions else rng.choice(cells)
        grid[position[0]][position[1]] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    cycle = int(sample_index) // EXAMPLES_NEEDED

    if profile == "canonical_anchor":
        height = _draw_axis(ctx, "grid_h", default=7)
        width = _draw_axis(ctx, "grid_w", default=8 + cycle % 3)
        wall_color = _draw_axis(ctx, "wall_color", default=5)
        n_rooms = _draw_axis(ctx, "n_rooms", default=4)
        irregular = False
        orientation = "vertical"
        canonical_positions = False
    elif profile == "shortcut_witness":
        height_default = 8 + cycle % 5
        width_default = 9 + cycle % 7
        height = _draw_axis(ctx, "grid_h", default=min(height_default, 18))
        width = _draw_axis(ctx, "grid_w", default=min(width_default, 20))
        wall_color = _draw_axis(ctx, "wall_color", default=6 + cycle % 4)
        n_rooms = _draw_axis(ctx, "n_rooms", default=3)
        irregular = True
        orientation = "vertical"
        canonical_positions = False
    else:
        if difficulty == "easy":
            favored_h, favored_w = range(7, 11), range(8, 13)
        elif difficulty == "hard":
            favored_h, favored_w = range(14, 19), range(16, 21)
        else:
            favored_h, favored_w = range(9, 16), range(11, 18)
        height = _draw_axis(ctx, "grid_h", favored=favored_h)
        width = _draw_axis(ctx, "grid_w", favored=favored_w)
        # Broad examples deliberately duplicate both shortcut-killing cues.
        # A four-pair lesson then contains at least two decisive examples, so
        # moving either one to the query cannot leave only canonical-compatible
        # demonstrations. Explicit overrides remain exact.
        wall_color = _draw_axis(ctx, "wall_color", default=6 + cycle % 4)
        n_rooms = _draw_axis(ctx, "n_rooms", default=2 + cycle % 3)
        irregular = True
        orientation = (
            "horizontal"
            if height >= 8 and ctx.draw_rng("orientation").choice((False, True))
            else "vertical"
        )
        canonical_positions = False

    # A horizontal stepped divider needs the original height to become the
    # transposed width.  Width 7 has no two-column safe step, so use vertical.
    if irregular and orientation == "horizontal" and height < 8:
        orientation = "vertical"

    grid = _partition_grid(
        height,
        width,
        wall_color,
        n_rooms,
        irregular=irregular,
        orientation=orientation,
        rng=ctx.draw_rng("partition_geometry"),
    )
    return _place_seeds(
        grid,
        wall_color,
        ctx.draw_rng("seed_placement"),
        canonical_positions=canonical_positions,
    )


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer colors 0..9"
    return None


def _wall_color(grid):
    colors = sorted({value for row in grid for value in row if value >= 5})
    if len(colors) != 1:
        raise ValueError(f"expected exactly one wall color 5..9, found {colors}")
    return colors[0]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    error = _grid_error(grid)
    if error:
        return [error]
    height = len(grid)
    width = len(grid[0])
    errors = []
    if not (7 <= height <= 18 and 8 <= width <= 20):
        errors.append(f"grid dimensions {height}x{width} outside 7..18 by 8..20")
    try:
        wall_color = _wall_color(grid)
    except ValueError as exc:
        return errors + [str(exc)]

    border = (
        list(grid[0])
        + list(grid[-1])
        + [row[0] for row in grid[1:-1]]
        + [row[-1] for row in grid[1:-1]]
    )
    if any(value != wall_color for value in border):
        errors.append("the full outer border must be wall color")

    wall_components = _components_where(grid, lambda value: value == wall_color)
    if len(wall_components) != 1:
        errors.append(f"wall cells must form one connected network, found {len(wall_components)}")

    chambers = _open_components(grid, wall_color)
    if not 2 <= len(chambers) <= 4:
        errors.append(f"expected 2..4 non-wall chambers, found {len(chambers)}")
    for index, chamber in enumerate(chambers):
        seeds = [point for point in chamber if grid[point[0]][point[1]] in (1, 2, 3, 4)]
        zeros = [point for point in chamber if grid[point[0]][point[1]] == 0]
        if len(seeds) != 1:
            errors.append(f"chamber {index} must contain exactly one seed, found {len(seeds)}")
        if not zeros:
            errors.append(f"chamber {index} must contain at least one zero to fill")
    return errors


def observe_overrides(grid):
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe invalid grid: " + "; ".join(findings))
    wall_color = _wall_color(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "wall_color": wall_color,
        "n_rooms": len(_open_components(grid, wall_color)),
    }


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket authority."""
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    source = deepcopy(grid)
    output = deepcopy(grid)
    height = len(source)
    width = len(source[0])
    for row in range(height):
        for col in range(width):
            color = source[row][col]
            if color not in (1, 2, 3, 4):
                continue
            queue = deque([(row, col)])
            seen = {(row, col)}
            while queue:
                point = queue.popleft()
                for nxt in _neighbors(point, height, width):
                    if nxt in seen:
                        continue
                    value = source[nxt[0]][nxt[1]]
                    if value not in (0, color):
                        continue
                    seen.add(nxt)
                    queue.append(nxt)
            for rr, cc in seen:
                if source[rr][cc] == 0:
                    output[rr][cc] = color
    return output


def strict_canonical_like(grid):
    findings = self_check(grid)
    if findings:
        return findings
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    reasons = []
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is not one of {sorted(_CANONICAL_PROFILES)}")
    if _wall_color(grid) != 5:
        reasons.append("canonical wall color is 5")
    if len(_open_components(grid, 5)) != 4:
        reasons.append("canonical examples contain four chambers")
    if _complete_wall_lines_only(grid) != rule_mirror(grid):
        reasons.append("canonical chamber boundaries are complete wall rows/columns")
    return reasons


def _complete_wall_lines_only(grid):
    """Rival: fill only rectangles bounded by complete wall rows/columns."""
    source = deepcopy(grid)
    output = deepcopy(grid)
    try:
        wall_color = _wall_color(source)
    except ValueError:
        return output
    height = len(source)
    width = len(source[0])
    rows = [row for row in range(height) if all(value == wall_color for value in source[row])]
    cols = [
        col
        for col in range(width)
        if all(source[row][col] == wall_color for row in range(height))
    ]
    for top, bottom in zip(rows, rows[1:]):
        if bottom - top <= 1:
            continue
        for left, right in zip(cols, cols[1:]):
            if right - left <= 1:
                continue
            cells = [
                (row, col)
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
                if source[row][col] != wall_color
            ]
            seeds = [(row, col) for row, col in cells if source[row][col] in (1, 2, 3, 4)]
            if len(seeds) != 1:
                continue
            color = source[seeds[0][0]][seeds[0][1]]
            for row, col in cells:
                if source[row][col] == 0:
                    output[row][col] = color
    return output


def _gray_walls_only(grid):
    """Rival: the canonical gray 5 is the only meaningful wall cue."""
    try:
        if _wall_color(grid) != 5:
            return deepcopy(grid)
    except ValueError:
        return deepcopy(grid)
    return rule_mirror(grid)


def _non_rectangular_chambers(grid):
    return _complete_wall_lines_only(grid) != rule_mirror(grid)


def _non_gray_wall(grid):
    try:
        return _wall_color(grid) != 5
    except ValueError:
        return False


SEMANTIC_WITNESSES = {
    "non_rectangular_chambers": _non_rectangular_chambers,
    "non_gray_wall": _non_gray_wall,
}
SEMANTIC_RIVALS = {
    "complete_wall_lines_only": _complete_wall_lines_only,
    "gray_walls_only": _gray_walls_only,
}
WITNESS_RIVALS = {
    "non_rectangular_chambers": ["complete_wall_lines_only"],
    "non_gray_wall": ["gray_walls_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
