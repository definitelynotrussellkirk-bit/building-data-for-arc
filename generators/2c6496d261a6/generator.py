"""Constructive inputs for the global color-row filter, easy_h04.

Keep a color iff all of its cells occupy one row. Racket remains the output
and label authority. The functions below generate inputs or test explicit WRONG
rivals; they do not supply training labels. See workspace/lesson_probe.py.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c6496d261a6"
TASK_ID = GENERATOR_ID
RULE_HASH = "e0b73d0c2fd9"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Keep nonzero colors confined to one row; erase colors spanning rows. "
    "Collision-free mixed inputs include singleton and horizontal keepers, "
    "a repeated-row color spanning at least three rows, varied distractor "
    "counts and positions, and a canonical-size plus broad-size mixture."
)
INVARIANTS = [
    "background is 0; cells are integer colors 0..9",
    "every selected color is present and its keeper/distractor role is exact",
    "a horizontal keeper and a repeated-row distractor spanning at least three rows are present",
    "placement never overwrites another color and leaves at least one background cell",
    "difficulty changes sampling weights, never an exact override's validity",
]
AXES = {
    "grid_h": {"type": "int", "default": "3..12; mixture favors canonical 5..7", "valid": "3..12"},
    "grid_w": {"type": "int", "default": "7..18; mixture favors canonical 7..10", "valid": "7..18"},
    "kept_colors": {"type": "int", "default": "2..5; 1 for an exact two-color request", "valid": "1..5"},
    "palette_size": {"type": "int", "default": "3..9; mixture favors 3..4", "valid": "2..9",
                     "aliases": ["n_distinct_colors"]},
}
# Compatibility spelling, not an independent axis of variation. Both names
# remain observable and conflicting requests fail before any random draw.
AXIS_ALIASES = {"n_distinct_colors": "palette_size"}
# Rejections are specified by exact exception axes and an explicit condition;
# no broad tuple waiver can turn an unrelated placement bug into a valid case.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_BOUNDS = {"grid_h": (3, 12), "grid_w": (7, 18), "kept_colors": (1, 5),
           "palette_size": (2, 9), "n_distinct_colors": (2, 9)}


def _incompatible(message, *axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - (set(AXES) | set(AXIS_ALIASES))
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    values = {name: value for name, value in overrides.items() if value is not None}
    for name, value in values.items():
        lo, hi = _BOUNDS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if ("palette_size" in values and "n_distinct_colors" in values
            and values["palette_size"] != values["n_distinct_colors"]):
        _incompatible("palette_size and n_distinct_colors must agree",
                      "palette_size", "n_distinct_colors")
    for palette_axis in ("palette_size", "n_distinct_colors"):
        if "kept_colors" in values and palette_axis in values:
            if values["kept_colors"] >= values[palette_axis]:
                _incompatible(f"kept_colors must be smaller than {palette_axis}",
                              "kept_colors", palette_axis)
    return values


def _weighted(ctx, name, lo, hi, favored, weight):
    # The full lawful domain stays in the support in every difficulty band.
    choices = list(range(lo, hi + 1))
    choices += [x for x in favored if lo <= x <= hi] * weight
    return ctx.draw_choice(name, choices)


def _draw_axes(ctx, values, difficulty):
    core = ctx.draw_choice("curriculum_profile", ("core", "broad")) == "core"
    if core:
        heights, widths, palettes, keepers, weight = (5, 6, 7), (7, 8, 9, 10), (3, 4), (2, 3), 16
    elif difficulty == "easy":
        heights, widths, palettes, keepers, weight = (3, 4, 5, 6), (7, 8, 9, 10), (2, 3, 4, 5), (1, 2, 3), 3
    elif difficulty == "hard":
        heights, widths, palettes, keepers, weight = (7, 8, 9, 10, 11, 12), (11, 12, 13, 14, 15, 16, 17, 18), (5, 6, 7, 8, 9), (3, 4, 5), 3
    else:
        heights, widths, palettes, keepers, weight = (5, 6, 7, 8, 9), (8, 9, 10, 11, 12, 13, 14), (3, 4, 5, 6, 7), (2, 3, 4), 3
    h = _weighted(ctx, "grid_h", 3, 12, heights, weight)
    w = _weighted(ctx, "grid_w", 7, 18, widths, weight)
    # Choose the unspecified side of a count constraint from its feasible set.
    # Ordinary draws must show both singleton and multi-cell keepers. Otherwise
    # three legal draws can jointly leave 'erase singletons' indistinguishable.
    # Exact one-keeper/two-color requests remain supported diagnostic cases.
    palette_requested = "palette_size" in values or "n_distinct_colors" in values
    pmin = max(2 if palette_requested else 3, values.get("kept_colors", 1) + 1)
    count = _weighted(ctx, "palette_size", pmin, 9, palettes, weight)
    if "n_distinct_colors" in values:
        ctx.draw_int("n_distinct_colors", 2, 9)  # record the requested alias too
    kmin = 1 if count == 2 or "kept_colors" in values else 2
    kept = _weighted(ctx, "kept_colors", kmin, min(5, count - 1), keepers, weight)
    return h, w, kept, count, core


def _roomiest_rows(free, count, rng):
    # Random ties and a capacity ordering give constructive, distinct row slots.
    available = [r for r in range(len(free)) if free[r]]
    rng.shuffle(available)
    available.sort(key=lambda r: len(free[r]), reverse=True)
    if len(available) < count:
        raise RuntimeError("constructive role reservation exhausted distinct rows")
    return available[:count]


def _put(grid, free, row, color, rng, column=None):
    if column is None:
        column = rng.choice(free[row])
    if column not in free[row] or grid[row][column] != 0:
        raise RuntimeError("refusing to overwrite a reserved cell")
    grid[row][column] = color
    free[row].remove(column)


def _extend_in_rows(grid, free, color, rows, count, rng):
    # Extensions are optional, never exact axes. Keep one background cell.
    for _ in range(count):
        available = [r for r in rows if free[r]]
        if not available or sum(map(len, free)) <= 1:
            return
        _put(grid, free, rng.choice(available), color, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    values = _validate_overrides(overrides)
    # Normalize the compatibility spelling so even alias-only calls record the
    # actual independent palette axis through GenCtx's public draw interface.
    ctx_overrides = dict(values)
    if "n_distinct_colors" in values:
        ctx_overrides.setdefault("palette_size", values["n_distinct_colors"])
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=ctx_overrides)
    h, w, kept, count, core = _draw_axes(ctx, values, difficulty)
    palette = ctx.draw_distinct_colors("role_colors", n=count, exclude=(0,))
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    free = [list(range(w)) for _ in range(h)]

    # Reserve the minimum for EVERY role before placing any optional extension.
    keeper_rows = []
    for index, color in enumerate(palette[:kept]):
        row = _roomiest_rows(free, 1, rng)[0]
        keeper_rows.append(row)
        for _ in range(2 if index == 0 else 1):
            _put(grid, free, row, color, rng)
    primary_rows = _roomiest_rows(free, 3, rng)
    primary = palette[kept]
    for row in primary_rows:
        _put(grid, free, row, primary, rng)
    repeat_row = max(primary_rows, key=lambda r: len(free[r]))
    _put(grid, free, repeat_row, primary, rng)

    other_rows = []
    aligned = []
    for color in palette[kept + 1:]:
        rows = _roomiest_rows(free, 2, rng)
        common = [c for c in free[rows[0]] if c in free[rows[1]]]
        same_column = bool(common) and rng.choice((False, False, True))
        column = rng.choice(common) if same_column else None
        for row in rows:
            _put(grid, free, row, color, rng, column)
        other_rows.append(rows)
        aligned.append(same_column)

    # Maximal minimum occupancy is 20 cells (3x7, one keeper, nine colors).
    # Larger canvases gain varied counts; the 3x7 boundary preserves all minima.
    target_count = rng.choice((3, 4, 4, 5) if core else (4, 5, 6))
    _extend_in_rows(grid, free, palette[0], [keeper_rows[0]], target_count - 2, rng)
    _extend_in_rows(grid, free, primary, list(range(h)), max(0, target_count - 4), rng)
    for index in range(2, kept):
        _extend_in_rows(grid, free, palette[index], [keeper_rows[index]], rng.randint(0, 4), rng)
    # Keeper index 1 stays a singleton. Other two-cell distractors sometimes
    # remain column aligned, so 'keep column-confined colors' is also challenged.
    for index, color in enumerate(palette[kept + 1:]):
        if aligned[index] or rng.choice((True, False)):
            continue
        rows = list(other_rows[index])
        extra_rows = [r for r in range(h) if r not in rows]
        rng.shuffle(extra_rows)
        rows += extra_rows[:rng.randint(0, min(3, len(extra_rows))) ]
        _extend_in_rows(grid, free, color, rows, rng.randint(1, 5), rng)
    return grid


def _cells(grid):
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))
    return positions


def observe_overrides(grid):
    """Measure exact controls from the final pixels, independent of draw intent."""
    positions = _cells(grid)
    kept = sum(len({r for r, _ in cells}) == 1 for cells in positions.values())
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "kept_colors": kept,
            "palette_size": len(positions), "n_distinct_colors": len(positions)}


def _grid_errors(grid):
    """Physical ARC grid domain, including reference-lawful uniform edge cases."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid dimensions must be at most 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    """Generator curriculum: mixed one-row keepers and multi-row distractors.

    The reference rule is also defined on identity and all-erased grids, but
    those provide no keep/erase contrast and are outside this ordinary family.
    Caller metadata cannot bypass this input-domain check.
    """
    errors = _grid_errors(grid)
    if errors:
        return errors
    rows_per_color = [len({r for r, _ in cells}) for cells in _cells(grid).values()]
    if 1 not in rows_per_color:
        errors.append("mixed curriculum needs a color confined to one row")
    if not any(count > 1 for count in rows_per_color):
        errors.append("mixed curriculum needs a color spanning multiple rows")
    return errors


def strict_canonical_like(grid):
    """Mixed teaching domain, including all stored canonical inputs."""
    errors = self_check(grid)
    if errors:
        return errors
    positions = _cells(grid)
    if not any(len(cells) >= 2 and len({r for r, _ in cells}) == 1 for cells in positions.values()):
        errors.append("mixed lesson needs a multi-cell horizontal keeper")
    if not any(len({r for r, _ in cells}) >= 2 for cells in positions.values()):
        errors.append("mixed lesson needs a color spanning rows")
    return errors


def _retain(grid, colors):
    return [[value if value in colors else 0 for value in row] for row in grid]


def _row_repeat_or_singleton(grid):
    # WRONG: a local horizontal repetition cannot override a global row conflict.
    keep = {color for color, cells in _cells(grid).items()
            if len(cells) == 1 or len(cells) > len({r for r, _ in cells})}
    return _retain(grid, keep)


def _erase_two_occurrences(grid):
    # WRONG: only recognizes the old generator's exact two-cell distractors.
    keep = {color for color, cells in _cells(grid).items()
            if len(cells) != 2 or len({r for r, _ in cells}) == 1}
    return _retain(grid, keep)


def _erase_two_rows(grid):
    # WRONG: colors spanning three or more rows must also be erased.
    keep = {color for color, cells in _cells(grid).items()
            if len({r for r, _ in cells}) != 2}
    return _retain(grid, keep)


def _column_confined(grid):
    keep = {color for color, cells in _cells(grid).items()
            if len({c for _, c in cells}) == 1}
    return _retain(grid, keep)


def _drop_singletons(grid):
    keep = {color for color, cells in _cells(grid).items()
            if len(cells) >= 2 and len({r for r, _ in cells}) == 1}
    return _retain(grid, keep)


def _identity(grid):
    return [list(row) for row in grid]


def _erase_all(grid):
    return [[0 for _ in row] for row in grid]


def _global_row_conflict(grid):
    return any(1 < len({r for r, _ in cells}) < len(cells) for cells in _cells(grid).values())


def _three_row_color(grid):
    return any(len({r for r, _ in cells}) >= 3 for cells in _cells(grid).values())


def _horizontal_keeper(grid):
    return any(len(cells) >= 2 and len({r for r, _ in cells}) == 1 for cells in _cells(grid).values())


def _singleton_keeper(grid):
    return any(len(cells) == 1 for cells in _cells(grid).values())


def _same_count_roles(grid):
    positions = _cells(grid)
    kept_counts = {len(cells) for cells in positions.values()
                   if len(cells) >= 3 and len({r for r, _ in cells}) == 1}
    return any(len(cells) in kept_counts and len({r for r, _ in cells}) > 1
               for cells in positions.values())


SEMANTIC_RIVALS = {
    "row_repeat_or_singleton": _row_repeat_or_singleton,
    "erase_two_occurrences": _erase_two_occurrences,
    "erase_two_rows": _erase_two_rows,
    "column_confined": _column_confined,
    "drop_singletons": _drop_singletons,
    "identity": _identity,
    "erase_all": _erase_all,
}
SEMANTIC_WITNESSES = {
    "global_row_conflict": _global_row_conflict,
    "three_row_color": _three_row_color,
    "horizontal_keeper": _horizontal_keeper,
    "singleton_keeper": _singleton_keeper,
    "same_count_roles": _same_count_roles,
}
WITNESS_RIVALS = {
    "global_row_conflict": ["row_repeat_or_singleton", "erase_two_occurrences"],
    "three_row_color": ["erase_two_rows"],
    "horizontal_keeper": ["column_confined"],
    "singleton_keeper": ["drop_singletons"],
    "same_count_roles": ["erase_two_occurrences"],
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("row_repeat_or_singleton", "erase_two_occurrences", "erase_two_rows")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require demo evidence against this finite rival family, not all programs.

    The query OUTPUT is deliberately unused. A surviving competitor is reported
    even if it happens to agree on this query: the lesson still does not teach
    the distinction. Query correctness is scored separately by the Racket probe.
    """
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    observed_outputs = {}
    for pair in demos:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["each demonstration needs input and output grids"]
        errors = _grid_errors(pair["input"]) + _grid_errors(pair["output"])
        if errors:
            return errors
        source, output = pair["input"], pair["output"]
        if len(source) != len(output) or len(source[0]) != len(output[0]):
            return ["row filtering preserves grid dimensions"]
        if any(v not in (0, source[r][c]) for r, row in enumerate(output)
               for c, v in enumerate(row)):
            return ["row filtering only retains or erases an input cell"]
        key = tuple(tuple(row) for row in source)
        target = tuple(tuple(row) for row in output)
        if key in observed_outputs and observed_outputs[key] != target:
            return ["identical demonstration inputs have conflicting outputs"]
        observed_outputs[key] = target
    query_input = query.get("input") if isinstance(query, dict) else query
    errors = _grid_errors(query_input)
    if errors:
        return errors
    return [f"unrefuted rival: {name}" for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
