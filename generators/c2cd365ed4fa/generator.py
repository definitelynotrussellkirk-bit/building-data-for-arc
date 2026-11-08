"""Generator for ARC task c2cd365ed4fa (original slug aaecdb9a).

The oracle counts monochromatic 8-connected components on background 7 and
renders those counts as a bottom-aligned five-column histogram.  Histogram
columns are fixed by color: 5, 2, 8, 9, 6 from left to right.

Normal lessons deliberately vary component size independently of component
count and include both ordinary 4-connected shapes and exact diagonal-only
8-connectivity witnesses.  This rules out common shortcuts such as counting
pixels, using 4-connectivity, or inferring the answer from object position.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c2cd365ed4fa"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "281335890ae5"
SUMMARY = (
    "Count each active color's monochromatic 8-connected components on a "
    "7-background grid.  Emit a bottom-aligned histogram whose fixed columns "
    "are colors 5, 2, 8, 9, and 6."
)
INVARIANTS = [
    "the background is 7 and active colors come only from {5,2,8,9,6}",
    "three to five active colors have one to six 8-connected components each",
    "the maximum component count is two to six and at least two colors have different counts",
    "component sizes vary independently of counts; the largest is six to sixteen cells",
    "the diagonal_merge axis exactly controls whether 8-connectivity differs from 4-connectivity",
]

COLORS = (5, 2, 8, 9, 6)
ALLOWED = frozenset((7,) + COLORS)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng",
        "valid": "10..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng",
        "valid": "10..22",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-aware rng",
        "valid": "3..5",
    },
    "peak_count": {
        "type": "int",
        "default": "difficulty-aware rng",
        "valid": "2..6",
    },
    "largest_component_size": {
        "type": "int",
        "default": "difficulty-aware rng",
        "valid": "6..16",
    },
    "diagonal_merge": {
        "type": "bool",
        "default": "rng true|false",
        "valid": "true|false",
    },
}


@dataclass(frozen=True)
class _ComponentSpec:
    color: int
    size: int
    diagonal_only_join: bool = False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, structurally checked input grid."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 10, 22)
    width = ctx.draw_int_diff("grid_w", 10, 22)
    n_colors = ctx.draw_int_diff("n_colors", 3, 5)
    peak_count = ctx.draw_int_diff("peak_count", 2, 6)
    largest_size = ctx.draw_int_diff("largest_component_size", 6, 16)
    diagonal_merge = ctx.draw_choice("diagonal_merge", (False, True))

    color_rng = ctx.draw_rng("active-colors")
    active_colors = tuple(color_rng.sample(list(COLORS), n_colors))
    counts = _count_plan(active_colors, peak_count, ctx.draw_rng("counts"))
    specs = _component_plan(
        active_colors,
        counts,
        largest_size,
        diagonal_merge,
        ctx.draw_rng("component-sizes"),
    )

    # Randomized restarts are deterministic because every attempt has its own
    # keyed RNG.  Placement failure is never silently accepted.
    for attempt in range(96):
        grid = _place_specs(
            height,
            width,
            specs,
            ctx.draw_rng(f"placement-{attempt}"),
        )
        if grid is None:
            continue
        observed = observe_overrides(grid)
        requested = {
            "grid_h": height,
            "grid_w": width,
            "n_colors": n_colors,
            "peak_count": peak_count,
            "largest_component_size": largest_size,
            "diagonal_merge": diagonal_merge,
        }
        if observed != requested:
            raise AssertionError(
                f"internal axis drift: requested={requested}, observed={observed}"
            )
        errors = self_check(grid, difficulty=difficulty)
        if errors:
            raise AssertionError("internal invalid scene: " + "; ".join(errors))
        return grid

    raise ValueError(
        "requested component inventory could not be placed without merging "
        f"same-color components on a {height}x{width} grid"
    )


def _count_plan(colors, peak_count, rng):
    """Assign exact, non-uniform per-color component counts."""
    order = list(colors)
    rng.shuffle(order)
    counts = {color: 1 for color in colors}
    counts[order[0]] = peak_count

    # Intermediate colors vary independently of the peak while staying compact
    # enough for the 10x10 boundary.  The final color remains count one, which
    # also gives the largest shape a guaranteed non-merging home.
    middle = order[1:-1]
    ceiling = min(peak_count, 3)
    for index, color in enumerate(middle):
        if ceiling <= 1:
            counts[color] = 1
        elif index == 0 and peak_count >= 3:
            counts[color] = 2
        else:
            counts[color] = rng.randint(1, ceiling)
    return counts


def _component_plan(colors, counts, largest_size, diagonal_merge, rng):
    """Create exact component sizes, decoupling largest size from peak count."""
    one_count_colors = [color for color in colors if counts[color] == 1]
    if not one_count_colors:
        raise AssertionError("count plan must retain a one-component color")
    largest_color = rng.choice(one_count_colors)

    specs = []
    for color in colors:
        for component_index in range(counts[color]):
            if color == largest_color and component_index == 0:
                specs.append(
                    _ComponentSpec(color, largest_size, diagonal_merge)
                )
                continue

            # Give each repeated color one modest multi-cell object; leave its
            # remaining objects as singletons.  Pixel totals therefore cannot
            # stand in for component counts, and a singleton witness remains.
            if component_index == 0 and counts[color] > 1:
                upper = min(5, largest_size - 1)
                size = rng.randint(2, upper)
            elif component_index == 0 and rng.random() < 0.45:
                upper = min(4, largest_size - 1)
                size = rng.randint(2, upper)
            else:
                size = 1
            specs.append(_ComponentSpec(color, size, False))

    # Larger shapes first greatly reduces fragmentation of available space.
    specs.sort(key=lambda spec: (spec.size, spec.diagonal_only_join), reverse=True)
    return tuple(specs)


def _place_specs(height, width, specs, rng):
    grid = full_grid(height, width, 7)
    occupied_by_color = {color: set() for color in COLORS}

    for spec in specs:
        if spec.diagonal_only_join:
            shape = _diagonal_shape(spec.size, rng)
        else:
            shape = _connected_shape(spec.size, rng)

        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        offsets = [
            (top, left)
            for top in range(height - shape_h + 1)
            for left in range(width - shape_w + 1)
        ]
        rng.shuffle(offsets)

        placed = False
        for top, left in offsets:
            cells = {(top + row, left + col) for row, col in shape}
            if any(grid[row][col] != 7 for row, col in cells):
                continue
            if _touches(cells, occupied_by_color[spec.color]):
                continue
            for row, col in cells:
                grid[row][col] = spec.color
            occupied_by_color[spec.color].update(cells)
            placed = True
            break
        if not placed:
            return None
    return grid


def _touches(cells, existing):
    """Whether a new component would 8-touch an existing same-color one."""
    if not existing:
        return False
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (row + dr, col + dc) in existing:
                    return True
    return False


def _connected_shape(size, rng):
    side = max(2, min(4, ceil(sqrt(size))))
    while side * side < size:
        side += 1
    cells = _grow_polyomino(size, side, rng)
    return _transform(cells, rng)


def _diagonal_shape(size, rng):
    """One 8-component made from two 4-components joined only diagonally."""
    if size < 2:
        raise ValueError("diagonal witness needs at least two cells")
    lobe = _grow_polyomino(size - 1, 4, rng, start=(0, 0))
    cells = {(0, 0)} | {(row + 1, col + 1) for row, col in lobe}
    return _transform(cells, rng)


def _grow_polyomino(size, side, rng, start=None):
    if not (1 <= size <= side * side):
        raise ValueError(f"cannot grow size {size} in {side}x{side} box")
    if start is None:
        start = (rng.randrange(side), rng.randrange(side))
    cells = {start}
    while len(cells) < size:
        frontier = set()
        for row, col in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (row + dr, col + dc)
                if (
                    0 <= point[0] < side
                    and 0 <= point[1] < side
                    and point not in cells
                ):
                    frontier.add(point)
        if not frontier:
            raise AssertionError("connected-shape frontier unexpectedly empty")
        cells.add(rng.choice(sorted(frontier)))
    return cells


def _transform(cells, rng):
    transformed = set(cells)
    if rng.choice((False, True)):
        transformed = {(row, -col) for row, col in transformed}
    for _ in range(rng.randrange(4)):
        transformed = {(col, -row) for row, col in transformed}
    min_row = min(row for row, _ in transformed)
    min_col = min(col for _, col in transformed)
    return {
        (row - min_row, col - min_col)
        for row, col in transformed
    }


def _components(grid, color, *, diagonal):
    neighbors = (
        (
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
        if diagonal
        else iter(((-1, 0), (1, 0), (0, -1), (0, 1)))
    )
    # Materialize because each flood fill reuses the offsets.
    offsets = tuple(neighbors)
    todo = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components = []
    while todo:
        start = todo.pop()
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in offsets:
                point = (row + dr, col + dc)
                if point in todo:
                    todo.remove(point)
                    cells.add(point)
                    stack.append(point)
        components.append(cells)
    return components


def _analysis(grid):
    result = {
        "errors": [],
        "grid_h": None,
        "grid_w": None,
        "n_colors": None,
        "peak_count": None,
        "largest_component_size": None,
        "diagonal_merge": None,
        "counts": {},
        "component_sizes": [],
    }
    errors = result["errors"]
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a nonempty list of rows")
        return result
    if not all(isinstance(row, list) and row for row in grid):
        errors.append("grid rows must be nonempty lists")
        return result
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result

    height = len(grid)
    result["grid_h"] = height
    result["grid_w"] = width
    if not (10 <= height <= 22 and 10 <= width <= 22):
        errors.append("grid dimensions must each be in 10..22")

    flat = [value for row in grid for value in row]
    if any(isinstance(value, bool) or not isinstance(value, int) for value in flat):
        errors.append("grid cells must be integer ARC colors")
        return result
    bad = sorted(set(flat) - ALLOWED)
    if bad:
        errors.append(f"unexpected colors {bad}; expected 7 plus {list(COLORS)}")
    if 7 not in flat:
        errors.append("background color 7 must be present")
    elif flat.count(7) / len(flat) < 0.35:
        errors.append("background 7 must occupy at least 35% of the grid")

    active = [color for color in COLORS if color in flat]
    result["n_colors"] = len(active)
    if not (3 <= len(active) <= 5):
        errors.append("expected three to five active histogram colors")

    counts = {}
    sizes = []
    diagonal_merge = False
    for color in active:
        comps8 = _components(grid, color, diagonal=True)
        counts[color] = len(comps8)
        if not (1 <= len(comps8) <= 6):
            errors.append(
                f"color {color} must form one to six 8-connected components"
            )
        for component in comps8:
            size = len(component)
            sizes.append(size)
            if not (1 <= size <= 16):
                errors.append(
                    f"color {color} has component size {size}; expected 1..16"
                )
            mask = [[7 for _ in range(width)] for _ in range(height)]
            for row, col in component:
                mask[row][col] = color
            if len(_components(mask, color, diagonal=False)) > 1:
                diagonal_merge = True

    result["counts"] = counts
    result["component_sizes"] = sizes
    result["diagonal_merge"] = diagonal_merge
    if counts:
        peak = max(counts.values())
        result["peak_count"] = peak
        if not (2 <= peak <= 6):
            errors.append("at least one color must repeat, with peak count in 2..6")
        if len(set(counts.values())) < 2:
            errors.append("component counts must differ across active colors")
    if sizes:
        largest = max(sizes)
        result["largest_component_size"] = largest
        if len(set(sizes)) < 2:
            errors.append("component sizes must include at least two distinct values")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-friendly lesson inputs."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    """Recover every exact declared axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_colors": analysis["n_colors"],
        "peak_count": analysis["peak_count"],
        "largest_component_size": analysis["largest_component_size"],
        "diagonal_merge": analysis["diagonal_merge"],
    }
