"""Generator for 529bd4803bcc — flood only single-seed compartments.

Color 5 is an impermeable wall.  Every 4-connected non-wall component is a
compartment.  A compartment containing exactly one seed cell (color 1, 2, or
3) is flooded with that seed's color; compartments with zero or multiple seed
cells are cleared to background by the unchanged Racket authority.

The sampler keeps a dense canonical-like component (full horizontal/vertical
wall bands) and alternates it with a local separator that forces connected-
component reasoning beyond the canonical rectangular-grid shortcut.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "529bd4803bcc"
TASK_ID = GENERATOR_ID
RULE_HASH = "222cee10aaec"
VERSION = "3.0.0"
SUMMARY = (
    "Gray walls partition an unframed 0-background grid into 4-connected "
    "compartments. Flood a compartment with its seed color exactly when it "
    "contains one seed cell from {1,2,3}; clear zero-seed and multi-seed "
    "compartments. Canonical full-row/full-column dividers alternate with "
    "local separators, and default lessons include a three-seed negative."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "colors are limited to background 0, seeds 1..3, and walls 5",
    "walls create at least four non-wall compartments without an outer frame",
    "exactly n_single compartments contain one seed and one compartment contains multi_seed_count seeds",
    "default three-seed negatives refute parity/count-cap shortcuts",
    "local_split layouts add a separator confined to one canonical rectangle",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-biased 10..18", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "canonical-biased 10..18", "valid": "10..18"},
    "row_dividers": {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "col_dividers": {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "wall_thickness": {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "layout_kind": {
        "type": "str",
        "default": "alternating local_split|regular",
        "valid": "regular|local_split",
    },
    "n_single": {"type": "int", "default": "scheduled 0..3", "valid": "0..3"},
    "multi_seed_count": {"type": "int", "default": "3", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("local_split", "regular")
MIN_STRICT_FRAC = 0.20

_SEEDS = frozenset((1, 2, 3))
_ALLOWED = frozenset((0, 1, 2, 3, 5))


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    integer_ranges = {
        "grid_h": (10, 18),
        "grid_w": (10, 18),
        "row_dividers": (1, 2),
        "col_dividers": (1, 2),
        "wall_thickness": (1, 2),
        "n_single": (0, 3),
        "multi_seed_count": (2, 4),
    }
    for name, (low, high) in integer_ranges.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")

    if "layout_kind" in overrides:
        value = overrides["layout_kind"]
        if type(value) is not str:
            raise TypeError(f"layout_kind must be a string, not {type(value).__name__}")
        if value not in ("regular", "local_split"):
            raise ValueError("layout_kind must be regular or local_split")


def _draw_choice_or_default(ctx, overrides, name, default, domain):
    """Consume exact overrides through gen_ctx while permitting a fixed schedule."""
    choices = list(domain) if name in overrides else [default]
    return ctx.draw_choice(name, choices)


def _draw_size(ctx, overrides, name, sample_index, difficulty):
    if name in overrides:
        return ctx.draw_choice(name, list(range(10, 19)))
    # One regular-layout slot in every four is an explicit 11x11 canonical
    # profile anchor.  Because odd slots also use a three-color multi-seed
    # negative, the returned palette is exactly {0,1,2,3,5} in every band.
    if sample_index % 4 == 1:
        choices = [11]
    # The remaining common slots stay near canonical scale; the fourth spans
    # the full documented domain so dimensions do not collapse to the anchor.
    elif sample_index % 4 != 3:
        choices = [10, 10, 11, 11]
    else:
        choices = list(range(10, 19))
        if difficulty == "easy":
            choices += [10, 11, 12] * 3
        elif difficulty == "hard":
            choices += [16, 17, 18] * 3
        else:
            choices += [12, 13, 14, 15]
    return ctx.draw_choice(name, choices)


def _positive_lengths(total, parts, rng):
    """Construct varied positive segment lengths with two useful large pieces."""
    if parts == 3:
        lengths = [3, 2, 1]
    elif parts == 2:
        lengths = [4, 4]
    else:  # Defensive; public axes only produce two or three segments.
        lengths = [1] * parts
    remaining = total - sum(lengths)
    if remaining < 0:
        raise ValueError(f"cannot partition {total} open cells into {parts} segments")
    for _ in range(remaining):
        lengths[rng.randrange(parts)] += 1
    rng.shuffle(lengths)
    return lengths


def _segments(lengths, thickness):
    """Return open ranges and full divider indices for a one-dimensional layout."""
    open_ranges = []
    dividers = []
    cursor = 0
    for index, length in enumerate(lengths):
        open_ranges.append(tuple(range(cursor, cursor + length)))
        cursor += length
        if index + 1 < len(lengths):
            dividers.extend(range(cursor, cursor + thickness))
            cursor += thickness
    return open_ranges, tuple(dividers)


def _connected_components(grid):
    height, width = len(grid), len(grid[0])
    pending = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 5
    }
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        component = {start}
        todo = [start]
        while todo:
            row, col = todo.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in pending:
                    pending.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        result.append(component)
    return sorted(result, key=lambda comp: min(comp))


def _build_layout(
    height,
    width,
    row_dividers,
    col_dividers,
    wall_thickness,
    layout_kind,
    multi_seed_count,
    rng,
):
    row_open = height - row_dividers * wall_thickness
    col_open = width - col_dividers * wall_thickness
    row_lengths = _positive_lengths(row_open, row_dividers + 1, rng)
    col_lengths = _positive_lengths(col_open, col_dividers + 1, rng)
    row_ranges, wall_rows = _segments(row_lengths, wall_thickness)
    col_ranges, wall_cols = _segments(col_lengths, wall_thickness)

    grid = full_grid(height, width, 0)
    for row in wall_rows:
        for col in range(width):
            grid[row][col] = 5
    for col in wall_cols:
        for row in range(height):
            grid[row][col] = 5

    split_parent = None
    if layout_kind == "local_split":
        base_rectangles = [
            (row_index, col_index, rows, cols)
            for row_index, rows in enumerate(row_ranges)
            for col_index, cols in enumerate(col_ranges)
        ]
        candidates = []
        for row_index, col_index, rows, cols in base_rectangles:
            outside_areas = [
                len(other_rows) * len(other_cols)
                for other_row, other_col, other_rows, other_cols in base_rectangles
                if (other_row, other_col) != (row_index, col_index)
            ]
            if not outside_areas or max(outside_areas) < multi_seed_count:
                continue
            if len(cols) >= 3:
                for offset in range(1, len(cols) - 1):
                    candidates.append((rows, cols, "vertical", offset))
            if len(rows) >= 3:
                for offset in range(1, len(rows) - 1):
                    candidates.append((rows, cols, "horizontal", offset))
        if not candidates:
            raise RuntimeError("constructive local split unexpectedly has no feasible chamber")
        rows, cols, orientation, offset = rng.choice(candidates)
        split_parent = frozenset((row, col) for row in rows for col in cols)
        if orientation == "vertical":
            split_col = cols[offset]
            for row in rows:
                grid[row][split_col] = 5
        else:
            split_row = rows[offset]
            for col in cols:
                grid[split_row][col] = 5

    return grid, split_parent


def _place_seeds(grid, split_parent, n_single, multi_seed_count, rng, sample_index):
    components = _connected_components(grid)
    split_children = []
    if split_parent is not None:
        split_children = [comp for comp in components if comp <= split_parent]
        if len(split_children) != 2:
            raise RuntimeError(f"local separator produced {len(split_children)} children, expected 2")

    outside = [
        comp
        for comp in components
        if split_parent is None or not comp <= split_parent
    ]
    multi_candidates = [comp for comp in outside if len(comp) >= multi_seed_count]
    if not multi_candidates:
        raise RuntimeError("no compartment can hold the requested multi-seed negative")
    multi = rng.choice(multi_candidates)

    reserved_empty = None
    singles = []
    if split_children and n_single:
        forced = rng.choice(split_children)
        reserved_empty = split_children[1] if forced is split_children[0] else split_children[0]
        singles.append(forced)

    candidates = [
        comp
        for comp in components
        if comp is not multi and comp is not reserved_empty and comp not in singles
    ]
    rng.shuffle(candidates)
    needed = n_single - len(singles)
    if needed > len(candidates):
        raise RuntimeError("not enough compartments for requested single-seed count")
    singles.extend(candidates[:needed])

    color_order = [1, 2, 3]
    rng.shuffle(color_order)
    for index, component in enumerate(singles):
        row, col = rng.choice(sorted(component))
        grid[row][col] = color_order[index % len(color_order)]

    positions = rng.sample(sorted(multi), multi_seed_count)
    if sample_index % 2 == 0:
        colors = [rng.choice((1, 2, 3))] * multi_seed_count
    else:
        start = rng.randrange(3)
        colors = [1 + ((start + index) % 3) for index in range(multi_seed_count)]
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return "local_split" if sample_index % 2 == 0 else "regular"


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

    height = _draw_size(ctx, overrides, "grid_h", sample_index, difficulty)
    width = _draw_size(ctx, overrides, "grid_w", sample_index, difficulty)
    row_dividers = ctx.draw_int("row_dividers", 1, 2)
    col_dividers = ctx.draw_int("col_dividers", 1, 2)
    wall_thickness = ctx.draw_int("wall_thickness", 1, 2)
    layout_kind = _draw_choice_or_default(
        ctx,
        overrides,
        "layout_kind",
        schedule_profile(seed, sample_index, difficulty),
        ("regular", "local_split"),
    )
    default_single = 1 + ((sample_index // 2) % 3) if layout_kind == "local_split" else sample_index % 4
    n_single = _draw_choice_or_default(
        ctx, overrides, "n_single", default_single, range(0, 4)
    )
    multi_seed_count = _draw_choice_or_default(
        ctx, overrides, "multi_seed_count", 3, range(2, 5)
    )

    layout_rng = ctx.draw_rng("layout_geometry")
    grid, split_parent = _build_layout(
        height,
        width,
        row_dividers,
        col_dividers,
        wall_thickness,
        layout_kind,
        multi_seed_count,
        layout_rng,
    )
    _place_seeds(
        grid,
        split_parent,
        n_single,
        multi_seed_count,
        ctx.draw_rng("seed_placement"),
        sample_index,
    )
    return grid


def _runs(indices):
    result = []
    for value in indices:
        if not result or value != result[-1][-1] + 1:
            result.append([value])
        else:
            result[-1].append(value)
    return result


def _full_wall_rows_cols(grid):
    height, width = len(grid), len(grid[0])
    rows = [row for row in range(height) if all(value == 5 for value in grid[row])]
    cols = [col for col in range(width) if all(grid[row][col] == 5 for row in range(height))]
    return rows, cols


def observe_overrides(grid):
    rows, cols = _full_wall_rows_cols(grid)
    row_runs, col_runs = _runs(rows), _runs(cols)
    thicknesses = {len(run) for run in row_runs + col_runs}
    if len(thicknesses) != 1:
        raise ValueError(f"inconsistent divider thicknesses: {sorted(thicknesses)}")
    extra_wall = any(
        value == 5 and row not in rows and col not in cols
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )
    counts = [
        sum(grid[row][col] in _SEEDS for row, col in component)
        for component in _connected_components(grid)
    ]
    multi = [count for count in counts if count >= 2]
    if len(multi) != 1:
        raise ValueError(f"expected one multi-seed compartment, found {len(multi)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "row_dividers": len(row_runs),
        "col_dividers": len(col_runs),
        "wall_thickness": next(iter(thicknesses)),
        "layout_kind": "local_split" if extra_wall else "regular",
        "n_single": counts.count(1),
        "multi_seed_count": multi[0],
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    bad = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or value not in _ALLOWED
    ]
    if bad:
        row, col, value = bad[0]
        return [f"cell ({row},{col}) has unsupported value {value!r}"]
    if not any(value == 5 for row in grid for value in row):
        return ["expected at least one color-5 wall"]
    if not any(value in _SEEDS for row in grid for value in row):
        return ["expected at least one seed color from {1,2,3}"]
    components = _connected_components(grid)
    if len(components) < 2:
        return [f"walls must create at least two compartments, got {len(components)}"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    rows, cols = _full_wall_rows_cols(grid)
    reasons = []
    if not rows or not cols:
        reasons.append("canonical manifold requires full wall rows and columns")
    if any(
        value == 5 and row not in rows and col not in cols
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    ):
        reasons.append("canonical manifold has no local-only wall segment")
    return reasons


def _solve_by_seed_count(grid, accepts):
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for component in _connected_components(grid):
        seeds = [
            grid[row][col]
            for row, col in component
            if grid[row][col] in _SEEDS
        ]
        if seeds and accepts(len(seeds)):
            for row, col in component:
                out[row][col] = seeds[0]
    return out


def _intended_python(grid):
    return _solve_by_seed_count(grid, lambda count: count == 1)


def _odd_seed_count(grid):
    """Plausible canonical shortcut: fill every odd-count compartment."""
    return _solve_by_seed_count(grid, lambda count: count % 2 == 1)


def _global_dividers_only(grid):
    """Plausible canonical shortcut: only full gray rows/columns partition cells."""
    height, width = len(grid), len(grid[0])
    wall_rows, wall_cols = _full_wall_rows_cols(grid)
    row_parts = []
    start = 0
    for run in _runs(wall_rows):
        if start < run[0]:
            row_parts.append(range(start, run[0]))
        start = run[-1] + 1
    if start < height:
        row_parts.append(range(start, height))
    col_parts = []
    start = 0
    for run in _runs(wall_cols):
        if start < run[0]:
            col_parts.append(range(start, run[0]))
        start = run[-1] + 1
    if start < width:
        col_parts.append(range(start, width))

    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for rows in row_parts:
        for cols in col_parts:
            cells = [
                (row, col)
                for row in rows
                for col in cols
                if grid[row][col] != 5
            ]
            seeds = [grid[row][col] for row, col in cells if grid[row][col] in _SEEDS]
            if len(seeds) == 1:
                for row, col in cells:
                    out[row][col] = seeds[0]
    return out


def _has_triple_seed_counterexample(grid):
    return any(
        sum(grid[row][col] in _SEEDS for row, col in component) == 3
        for component in _connected_components(grid)
    ) and _odd_seed_count(grid) != _intended_python(grid)


def _has_local_separator_counterexample(grid):
    rows, cols = _full_wall_rows_cols(grid)
    has_local_wall = any(
        value == 5 and row not in rows and col not in cols
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )
    return has_local_wall and _global_dividers_only(grid) != _intended_python(grid)


def _has_single_branch(grid):
    return any(
        sum(grid[row][col] in _SEEDS for row, col in component) == 1
        for component in _connected_components(grid)
    )


def _has_non_single_branch(grid):
    return any(
        sum(grid[row][col] in _SEEDS for row, col in component) != 1
        for component in _connected_components(grid)
    )


SEMANTIC_WITNESSES = {
    "triple_seed_compartment": _has_triple_seed_counterexample,
    "local_separator": _has_local_separator_counterexample,
    "single_seed_branch": _has_single_branch,
    "non_single_branch": _has_non_single_branch,
}
SEMANTIC_RIVALS = {
    "odd_seed_count": _odd_seed_count,
    "global_dividers_only": _global_dividers_only,
}
WITNESS_RIVALS = {
    "triple_seed_compartment": ["odd_seed_count"],
    "local_separator": ["global_dividers_only"],
}
BRANCH_WITNESSES = {"single_seed_branch", "non_single_branch"}
CANONICAL_SHORTCUTS = {
    "odd_seed_count": _odd_seed_count,
    "global_dividers_only": _global_dividers_only,
}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
